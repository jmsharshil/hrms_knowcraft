import json
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.management import call_command
from unittest.mock import patch

from accounts.models import User
from jobs.models import JobApplication
from onboarding.models import OnboardingCall, SurveyResponse, OnboardingTaskList, OnboardingTask
from mrf.models import Designation

class OnboardingAPIsTestCase(APITestCase):
    
    @classmethod
    def setUpTestData(cls):
        # Seed the database
        call_command('seed_demo_data')
        
    def setUp(self):
        # Find an admin user to act as the authenticated client
        self.admin_user = User.objects.filter(role='admin').first()
        self.client.force_authenticate(user=self.admin_user)
        
        # Pick or setup a JobApplication to be in 'joined' status
        self.application = JobApplication.objects.first()
        if not self.application:
            # Fallback if seed didn't create any
            from jobs.models import Job
            from accounts.models import Company
            company = Company.objects.first()
            job = Job.objects.first()
            self.application = JobApplication.objects.create(
                job=job,
                candidate_name="Test Candidate",
                candidate_email="test.candidate@example.com",
                candidate_phone="9876543210",
                status="joined",
                joining_date=timezone.now().date(),
                company=company
            )
        else:
            JobApplication.objects.filter(id=self.application.id).update(
                status="joined",
                joining_date=timezone.now().date()
            )
            self.application.refresh_from_db()

        # Try to find a valid teams user ending in @jmstech.co
        self.organizer_email = "test.organizer@jmstech.co" # Default fallback
        try:
            from slots.graph import get_graph_token
            import requests
            token = get_graph_token()
            url = "https://graph.microsoft.com/v1.0/users"
            headers = {"Authorization": f"Bearer {token}"}
            params = {"$filter": "endswith(mail, '@jmstech.co')"}
            r = requests.get(url, headers=headers, params=params)
            if r.ok:
                users = r.json().get("value", [])
                if users:
                    self.organizer_email = users[0].get("mail", self.organizer_email)
                else:
                    print("Graph returned OK but empty users list.")
            else:
                print("Graph failed:", r.status_code, r.text)
        except Exception as e:
            print("Could not fetch real Teams user, using fallback:", e)

    def test_search_teams_users_api(self):
        url = reverse('search-teams-users')
        response = self.client.get(url, {'query': 'a'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)

    def test_resolve_escalation_api(self):
        self.application.is_escalated = True
        self.application.save()
        
        url = reverse('resolve-escalation', kwargs={'id': str(self.application.id)})
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.application.refresh_from_db()
        self.assertFalse(self.application.is_escalated)

    @patch('onboarding.views.send_email')
    def test_assign_buddy_api(self, mock_send_email):
        url = reverse('assign-buddy', kwargs={'id': str(self.application.id)})
        
        payload = {
            "technical_buddy_name": "Tech Buddy",
            "technical_buddy_email": "tech@example.com",
            "cultural_buddy_name": "Culture Buddy",
            "cultural_buddy_email": "culture@example.com"
        }
        
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application.refresh_from_db()
        self.assertEqual(self.application.technical_buddy_name, "Tech Buddy")
        self.assertEqual(self.application.cultural_buddy_name, "Culture Buddy")
        self.assertTrue(self.application.emp_account_active)
        self.assertEqual(mock_send_email.call_count, 2)
        
    def test_survey_structure_api(self):
        url = reverse('survey-structure', kwargs={'id': str(self.application.id)})
        
        # Test 30 Day Candidate Survey
        response = self.client.get(url, {'survey_type': '30_day_candidate'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['survey_type'], '30_day_candidate')
        self.assertIn('sections', data['structure'])
        self.assertEqual(len(data['structure']['options']['binary']), 2)
        
        # Test HOD Survey (Junior vs Senior)
        if hasattr(self.application.job, 'mrf') and self.application.job.mrf:
            original_designation = self.application.job.mrf.designation.name
            
            # Make it Junior
            self.application.job.mrf.designation.name = "Software Engineer"
            self.application.job.mrf.designation.save()
            response_junior = self.client.get(url, {'survey_type': 'hod'})
            self.assertEqual(response_junior.status_code, status.HTTP_200_OK)
            structure = response_junior.json()['structure']
            # Junior should have 18 binary questions
            binary_q_count = sum(len([q for q in s['questions'] if q['type'] == 'binary']) for s in structure['sections'])
            self.assertEqual(binary_q_count, 18)
            
            # Make it Senior
            self.application.job.mrf.designation.name = "Engineering Manager"
            self.application.job.mrf.designation.save()
            response_senior = self.client.get(url, {'survey_type': 'hod'})
            structure_senior = response_senior.json()['structure']
            binary_q_count_senior = sum(len([q for q in s['questions'] if q['type'] == 'binary']) for s in structure_senior['sections'])
            self.assertEqual(binary_q_count_senior, 20)
            
            # Restore
            self.application.job.mrf.designation.name = original_designation
            self.application.job.mrf.designation.save()

    def test_submit_survey_api_30_day_candidate(self):
        url = reverse('survey-completed', kwargs={'id': str(self.application.id)})
        
        # 1. Invalid payload (missing questions)
        invalid_payload = {
            "survey_type": "30_day_candidate",
            "responses": {
                "1": "agree"
            }
        }
        response = self.client.patch(url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("2", response.json()['fields'])
        
        # 2. Valid payload
        valid_responses = {str(i): "agree" for i in range(1, 24)}
        valid_responses["24"] = "Good experience."
        valid_payload = {
            "survey_type": "30_day_candidate",
            "responses": valid_responses
        }
        response = self.client.patch(url, valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_satisfaction_survey_filled)
        
        # 3. Duplicate submission
        response = self.client.patch(url, valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_submit_survey_api_hod(self):
        url = reverse('survey-completed', kwargs={'id': str(self.application.id)})
        
        # Make Junior
        if hasattr(self.application.job, 'mrf') and self.application.job.mrf:
            self.application.job.mrf.designation.name = "Software Engineer"
            self.application.job.mrf.designation.save()
        
        # 1. Missing respondent info
        payload = {
            "survey_type": "hod",
            "responses": {str(i): "agree" for i in range(1, 19)}
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 2. Valid submission
        payload["respondent_name"] = "HOD Name"
        payload["respondent_email"] = "hod@example.com"
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_hod_survey_filled)

    def test_submit_survey_api_90_day(self):
        url = reverse('survey-completed', kwargs={'id': str(self.application.id)})
        
        responses = {str(i): "agree" for i in range(1, 15)}
        responses["19"] = "yes"
        payload = {
            "survey_type": "90_day_candidate",
            "responses": responses
        }
        
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_d90_survey_filled)
        
    def test_schedule_d45_call_api(self):
        # We will use real Graph API for scheduling
        url = reverse('d45-scheduled', kwargs={'id': str(self.application.id)})
        
        now = timezone.now()
        start_time = now + timedelta(days=1)
        end_time = start_time + timedelta(minutes=30)
        
        payload = {
            "organizer_email": self.organizer_email,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendee_emails": []
        }
        
        # 1. First booking
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_d45_call_scheduled)
        
        call = OnboardingCall.objects.filter(job_application=self.application, call_type='d45').first()
        self.assertIsNotNone(call)
        self.assertTrue(call.meeting_id)
        
        # 2. Rescheduling
        new_start_time = start_time + timedelta(hours=1)
        new_end_time = end_time + timedelta(hours=1)
        payload["start_time"] = new_start_time.isoformat()
        payload["end_time"] = new_end_time.isoformat()
        
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        call.refresh_from_db()
        self.assertEqual(call.start_time, new_start_time)
        
    def test_schedule_d90_call_api(self):
        url = reverse('d90-scheduled', kwargs={'id': str(self.application.id)})
        
        now = timezone.now()
        start_time = now + timedelta(days=2)
        end_time = start_time + timedelta(minutes=30)
        
        payload = {
            "organizer_email": self.organizer_email,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "attendee_emails": []
        }
        
        # First booking
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_d90_call_scheduled)
        
        call = OnboardingCall.objects.filter(job_application=self.application, call_type='d90').first()
        self.assertIsNotNone(call)
        self.assertTrue(call.meeting_id)

    def test_onboarding_journey_api(self):
        url = reverse('onboarding-journey', kwargs={'id': str(self.application.id)})
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('candidate', data)
        self.assertIn('mrf', data)
        self.assertIn('milestones', data)
        self.assertIn('calls', data)
        self.assertIn('surveys', data)
        self.assertIn('task_lists', data)
        
        self.assertEqual(data['candidate']['id'], str(self.application.id))

    def test_task_lists_and_tasks_crud(self):
        # 1. Create Task List
        list_url = reverse('onboarding-task-lists-list')
        list_payload = {
            "job_application": str(self.application.id),
            "name": "Week 1 Checklist",
            "description": "Tasks for week 1"
        }
        response = self.client.post(list_url, list_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_list_id = response.json()['id']
        
        # 2. Create Task
        task_url = reverse('onboarding-tasks-list')
        task_payload = {
            "task_list": task_list_id,
            "title": "Setup Email",
            "status": "pending"
        }
        response = self.client.post(task_url, task_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_id = response.json()['id']
        
        # 3. Update Task
        task_detail_url = reverse('onboarding-tasks-detail', kwargs={'pk': task_id})
        response = self.client.patch(task_detail_url, {"status": "completed"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], "completed")
        
        # 4. Delete Task List (Should cascade to Task)
        list_detail_url = reverse('onboarding-task-lists-detail', kwargs={'pk': task_list_id})
        response = self.client.delete(list_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        self.assertEqual(OnboardingTaskList.objects.count(), 0)
        self.assertEqual(OnboardingTask.objects.count(), 0)

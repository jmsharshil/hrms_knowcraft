import json
from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch

from accounts.models import User
from bgv.models import CandidateBGV
from jobs.models import JobApplication
from onboarding.models import (
    DocumentEsignTask,
    EmailLog,
    JobApplicationDocument,
    OnboardingCall,
    SurveyResponse,
    OnboardingTaskList,
    OnboardingTask,
)
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

    @patch('onboarding.utils.sender.send_email')
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
        self.assertEqual(mock_send_email.call_count, 1)
        
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
        
    @patch('booking.utils.create_teams_meeting')
    @patch('booking.utils.update_teams_meeting')
    def test_schedule_d45_call_api(self, mock_update, mock_create):
        # We will mock the Graph API for scheduling
        mock_create.return_value = {"id": "mock_meeting_123"}
        mock_update.return_value = {"id": "mock_meeting_123"}
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
        
    @patch('booking.utils.create_teams_meeting')
    def test_schedule_d90_call_api(self, mock_create):
        mock_create.return_value = {"id": "mock_meeting_456"}
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

    def test_d45_and_d90_call_mom_notes_and_transcript_can_be_created_and_updated(self):
        for route_name, call_type in (
            ('d45-scheduled', 'd45'),
            ('d90-scheduled', 'd90'),
        ):
            with self.subTest(call_type=call_type):
                url = reverse(route_name, kwargs={'id': str(self.application.id)})
                notes = 'Meeting notes. ' * 40
                first_response = self.client.patch(
                    url,
                    {
                        'mom_notes': notes,
                        'transcript_file': SimpleUploadedFile(
                            f'{call_type}-transcript.txt',
                            b'original transcript',
                            content_type='text/plain',
                        ),
                    },
                    format='multipart',
                )

                self.assertEqual(first_response.status_code, status.HTTP_200_OK)
                call = OnboardingCall.objects.get(
                    job_application=self.application,
                    call_type=call_type,
                )
                self.assertEqual(call.mom_notes, notes)
                with call.transcript_file.open('rb') as transcript:
                    self.assertEqual(transcript.read(), b'original transcript')
                self.assertTrue(first_response.json()['call']['transcript_file_url'])

                updated_response = self.client.patch(
                    url,
                    {
                        'mom_notes': 'Updated minutes.',
                        'transcript_file': SimpleUploadedFile(
                            f'{call_type}-transcript-updated.txt',
                            b'updated transcript',
                            content_type='text/plain',
                        ),
                    },
                    format='multipart',
                )

                self.assertEqual(updated_response.status_code, status.HTTP_200_OK)
                call.refresh_from_db()
                self.assertEqual(call.mom_notes, 'Updated minutes.')
                with call.transcript_file.open('rb') as transcript:
                    self.assertEqual(transcript.read(), b'updated transcript')

        journey = self.client.get(reverse(
            'onboarding-journey',
            kwargs={'id': str(self.application.id)},
        ))
        self.assertEqual(journey.status_code, status.HTTP_200_OK)
        self.assertEqual(
            journey.json()['calls']['d45']['mom_notes'],
            'Updated minutes.',
        )
        self.assertTrue(
            journey.json()['calls']['d90']['transcript_file_url']
        )

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

    def test_document_sections_api_groups_files_and_returns_signed_file_urls(self):
        application_documents = JobApplicationDocument.objects.create(
            job_application=self.application,
        )
        application_documents.aadhaar.save(
            'aadhaar.pdf',
            SimpleUploadedFile('aadhaar.pdf', b'%PDF personal'),
        )
        application_documents.graduation_certificate.save(
            'graduation.pdf',
            SimpleUploadedFile('graduation.pdf', b'%PDF education'),
        )
        call = OnboardingCall.objects.create(
            job_application=self.application,
            call_type='d45',
        )
        call.transcript_file.save(
            'd45-transcript.txt',
            SimpleUploadedFile('d45-transcript.txt', b'call transcript'),
        )
        esign_document = DocumentEsignTask.objects.create(
            job_application=self.application,
            doc_type='NDA',
            status='completed',
        )
        esign_document.source_file.save(
            'nda-original.pdf',
            SimpleUploadedFile('nda-original.pdf', b'%PDF original'),
        )
        esign_document.signed_file.save(
            'nda-signed.pdf',
            SimpleUploadedFile('nda-signed.pdf', b'%PDF signed'),
        )
        bgv_record, _ = CandidateBGV.objects.update_or_create(
            candidate=self.application,
            defaults={
                'report_url': 'https://reports.example.test/bgv/123',
                'status': 'completed',
            },
        )

        response = self.client.get(reverse(
            'application-document-sections',
            kwargs={'id': str(self.application.id)},
        ))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sections = response.json()['sections']
        self.assertEqual(sections['personal'][0]['key'], 'aadhaar')
        self.assertTrue(sections['personal'][0]['url'])
        self.assertEqual(sections['education'][0]['key'], 'graduation_certificate')
        self.assertEqual(sections['bgv'][0]['url'], bgv_record.report_url)
        self.assertEqual(sections['bgv'][0]['status'], 'completed')
        transcript = next(
            item for item in sections['onboarding']
            if item['key'] == 'd45_transcript'
        )
        self.assertTrue(transcript['url'])
        nda = next(item for item in sections['onboarding'] if item['key'] == 'NDA')
        self.assertTrue(nda['source_file_url'])
        self.assertTrue(nda['signed_file_url'])

    @patch('onboarding.utils.sender.send_email')
    def test_call_owner_is_reminded_once_after_call_if_materials_are_missing(self, mock_send_email):
        from onboarding.utils.onboarding_tasks import remind_call_owners_for_missing_materials

        def record_sent_email(**kwargs):
            EmailLog.objects.create(
                recipient_email=kwargs['to'],
                subject=kwargs['subject'],
                event=kwargs['event'],
                email_type=kwargs['email_type'],
                candidate=kwargs['candidate'],
                status='sent',
            )

        mock_send_email.side_effect = record_sent_email
        call = OnboardingCall.objects.create(
            job_application=self.application,
            call_type='d45',
            organizer_email='call.owner@example.com',
            end_time=timezone.now() - timedelta(minutes=1),
        )

        remind_call_owners_for_missing_materials()
        call.refresh_from_db()
        mock_send_email.assert_called_once()
        self.assertEqual(
            mock_send_email.call_args.kwargs['to'],
            'call.owner@example.com',
        )
        self.assertIn('MOM notes', mock_send_email.call_args.kwargs['text'])
        self.assertIn('call transcript', mock_send_email.call_args.kwargs['text'])
        self.assertFalse(mock_send_email.call_args.kwargs['use_default_cc'])

        remind_call_owners_for_missing_materials()
        mock_send_email.assert_called_once()

    @patch('onboarding.utils.sender.send_email')
    def test_call_material_reminder_skips_future_calls_and_calls_without_owner(self, mock_send_email):
        from onboarding.utils.onboarding_tasks import remind_call_owners_for_missing_materials

        OnboardingCall.objects.create(
            job_application=self.application,
            call_type='d45',
            organizer_email='call.owner@example.com',
            end_time=timezone.now() + timedelta(hours=1),
        )
        OnboardingCall.objects.create(
            job_application=self.application,
            call_type='d90',
            end_time=timezone.now() - timedelta(minutes=1),
        )
        complete_call = OnboardingCall.objects.create(
            job_application=self.application,
            call_type='d90',
            organizer_email='call.owner@example.com',
            end_time=timezone.now() - timedelta(minutes=1),
            mom_notes='Completed meeting minutes.',
        )
        complete_call.transcript_file.save(
            'complete-transcript.txt',
            SimpleUploadedFile('complete-transcript.txt', b'complete transcript'),
        )

        remind_call_owners_for_missing_materials()

        mock_send_email.assert_not_called()

    @patch('onboarding.utils.zoho_sign.requests.get')
    @patch('onboarding.utils.zoho_sign.get_access_token', return_value='test-token')
    def test_zoho_completion_saves_signed_document(self, mock_token, mock_get):
        document = DocumentEsignTask.objects.create(
            job_application=self.application,
            doc_type='UNDERTAKING',
            status='sent',
            zoho_request_id='request-123',
            zoho_document_id='document-123',
        )
        mock_get.return_value.content = b'%PDF-1.4 signed'
        mock_get.return_value.raise_for_status.return_value = None

        payload = {
            'notifications': {'operation_type': 'RequestCompleted'},
            'requests': {
                'request_id': 'request-123',
                'request_status': 'completed',
                'document_ids': [{'document_id': 'document-123'}],
            },
        }
        response = self.client.post(
            reverse('zohosign-webhook'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        document.refresh_from_db()
        self.assertEqual(document.status, 'completed')
        self.assertTrue(document.signed_file)
        with document.signed_file.open('rb') as signed_file:
            self.assertEqual(signed_file.read(), b'%PDF-1.4 signed')
        self.assertEqual(mock_get.call_count, 1)
        self.application.refresh_from_db()
        self.assertTrue(self.application.is_undertaking_signoff_completed)

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

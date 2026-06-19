"""
Management command to seed the database with demo data for HRMS system.
Run with: python manage.py seed_demo_data
"""
import uuid
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from accounts.models import Company, User
from mrf.models import (
    Department, Designation, WorkflowTemplate, 
    ApprovalWorkflow, MRF, PrivateMRFApprovalLevel
)
from slots.models import Interviewer, InterviewLocation
from jobs.models import Job, JobApplicationLink, ReferralApplication


class Command(BaseCommand):
    help = 'Seeds the database with demo data for testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting demo data seeding...'))
        
        try:
            with transaction.atomic():
                self.create_demo_data()
            self.stdout.write(self.style.SUCCESS('Successfully seeded demo data!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error seeding data: {str(e)}'))
            raise

    def create_demo_data(self):
        # 1. Create Company
        company, created = Company.objects.get_or_create(
            name='Knowcraft Technologies',
            defaults={
                'email': 'hr@knowcraft.in',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created company: {company.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Company already exists: {company.name}'))

        # 2. Create Demo Users
        self.create_users(company)

        # 3. Create Departments
        departments = self.create_departments(company)

        # 4. Create Designations
        designations = self.create_designations(company, departments)

        # 5. Create Workflow Templates
        self.create_workflows(company)

        # 6. Create Interviewers and Locations
        self.create_interviewers(company)
        self.create_locations(company)

        # 7. Create Sample MRF and Job
        self.create_sample_mrf(company, departments, designations)

        # 8. Create Referral Applications for filter testing
        self.create_referral_applications(company)

        self.stdout.write(self.style.SUCCESS('Demo data creation completed.'))

    def create_users(self, company):
        """Create demo users with different roles"""
        users_data = [
            {
                'email': 'admin@knowcraft.in',
                'name': 'System Admin',
                'role': 'admin',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'email': 'hr.manager@knowcraft.in',
                'name': 'HR Manager',
                'role': 'hr_manager',
                'password': 'hr123',
            },
            {
                'email': 'hr@knowcraft.in',
                'name': 'HR Executive',
                'role': 'hr',
                'password': 'hr123',
            },
            {
                'email': 'dept.head@knowcraft.in',
                'name': 'Department Head',
                'role': 'department_head',
                'password': 'dept123',
            },
        ]

        created_users = {}
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                company=company,
                defaults={
                    'name': user_data['name'],
                    'role': user_data['role'],
                    'is_active': True,
                    'is_staff': user_data.get('is_staff', False),
                }
            )
            
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Created user: {user.name} ({user.role})'))
            else:
                self.stdout.write(self.style.WARNING(f'User already exists: {user.name}'))
            
            created_users[user.role] = user

        return created_users

    def create_departments(self, company):
        """Create demo departments"""
        dept_data = [
            {'name': 'Engineering', 'code': 'DEP001'},
            {'name': 'Sales & Marketing', 'code': 'DEP002'},
            {'name': 'Human Resources', 'code': 'DEP003'},
            {'name': 'Finance', 'code': 'DEP004'},
            {'name': 'Operations', 'code': 'DEP005'},
        ]
        
        departments = {}
        for data in dept_data:
            dept, created = Department.objects.get_or_create(
                company=company,
                name=data['name'],
                defaults={
                    'code': data['code'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created department: {dept.name}'))
            departments[data['name']] = dept
        
        return departments

    def create_designations(self, company, departments):
        """Create demo designations"""
        designation_data = [
            {
                'name': 'Software Engineer',
                'department': departments['Engineering'],
                'tat_days': 15,
                'salary_range': '8-15 LPA',
                'expirience': '2-5 years',
                'skills_competencies': 'Python, Django, React, SQL',
            },
            {
                'name': 'Senior Software Engineer',
                'department': departments['Engineering'],
                'tat_days': 20,
                'salary_range': '15-25 LPA',
                'expirience': '5-8 years',
                'skills_competencies': 'Python, Django, AWS, Leadership',
            },
            {
                'name': 'Business Development Executive',
                'department': departments['Sales & Marketing'],
                'tat_days': 10,
                'salary_range': '6-10 LPA',
                'expirience': '1-4 years',
                'skills_competencies': 'Sales, Communication, CRM',
            },
            {
                'name': 'HR Executive',
                'department': departments['Human Resources'],
                'tat_days': 12,
                'salary_range': '5-9 LPA',
                'expirience': '2-5 years',
                'skills_competencies': 'Recruitment, Employee Relations',
            },
        ]
        
        designations = {}
        for data in designation_data:
            desig, created = Designation.objects.get_or_create(
                company=company,
                name=data['name'],
                defaults={
                    'department': data['department'],
                    'tat_days': data.get('tat_days'),
                    'salary_range': data.get('salary_range', '5-15 LPA'),
                    'expirience': data.get('expirience', '2-5 years'),
                    'skills_competencies': data.get('skills_competencies', ''),
                    'key_responsibility': f'Responsibilities for {data["name"]}',
                    'required_qualifications': 'Bachelor degree in relevant field',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created designation: {desig.name}'))
            designations[data['name']] = desig
        
        return designations

    def create_workflows(self, company):
        """Create workflow templates"""
        # Get HR and Admin users for approvers
        try:
            hr_manager = User.objects.get(company=company, role='hr_manager')
            admin = User.objects.get(company=company, role='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('Could not find users for workflow. Skipping detailed workflow setup.'))
            return

        # Create default workflow template
        workflow, created = WorkflowTemplate.objects.get_or_create(
            name='Standard Approval Workflow',
            company=company,
            defaults={
                'description': 'Standard 3-level approval workflow for MRFs',
                'is_default': True,
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created workflow template: {workflow.name}'))
            
            # Create approval levels
            levels = [
                {'level': 1, 'required_role': 'hr_manager', 'order': 1, 'approver': hr_manager},
                {'level': 2, 'required_role': 'department_head', 'order': 2, 'approver': None},  # Will be dynamic
                {'level': 3, 'required_role': 'admin', 'order': 3, 'approver': admin},
            ]
            
            for level_data in levels:
                ApprovalWorkflow.objects.get_or_create(
                    template=workflow,
                    level=level_data['level'],
                    defaults={
                        'company': company,
                        'required_role': level_data['required_role'],
                        'order': level_data['order'],
                        'approver': level_data.get('approver'),
                        'is_active': True,
                    }
                )
            self.stdout.write(self.style.SUCCESS('Created approval workflow levels'))
        else:
            self.stdout.write(self.style.WARNING('Workflow template already exists'))

    def create_interviewers(self, company):
        """Create demo interviewers"""
        interviewers_data = [
            {
                'name': 'Rahul Sharma',
                'email': 'rahul.tech@knowcraft.in',
                'phone': '9876543210',
            },
            {
                'name': 'Priya Patel',
                'email': 'priya.hr@knowcraft.in',
                'phone': '9876543211',
            },
            {
                'name': 'Amit Kumar',
                'email': 'amit.senior@knowcraft.in',
                'phone': '9876543212',
            },
        ]
        
        for data in interviewers_data:
            interviewer, created = Interviewer.objects.get_or_create(
                email=data['email'],
                company=company,
                defaults={
                    'name': data['name'],
                    'phone': data.get('phone'),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created interviewer: {interviewer.name}'))

    def create_locations(self, company):
        """Create interview locations"""
        location, created = InterviewLocation.objects.get_or_create(
            name='Knowcraft HQ',
            company=company,
            defaults={
                'address_line_1': '14th Floor, 1410, West Wing, Venus Stratum',
                'city': 'Ahmedabad',
                'state': 'Gujarat',
                'pincode': '380015',
                'country': 'India',
                'is_default': True,
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created default interview location'))
        else:
            self.stdout.write(self.style.WARNING('Interview location already exists'))

    def create_sample_mrf(self, company, departments, designations):
        """Create a sample MRF and related Job"""
        try:
            # Get users
            requested_by = User.objects.get(company=company, role='hr_manager')
            dept_head = User.objects.get(company=company, role='department_head', name__contains='Department')
            
            # Get models
            dept = departments.get('Engineering')
            desig = designations.get('Software Engineer')
            
            if not dept or not desig:
                self.stdout.write(self.style.WARNING('Missing department or designation. Skipping MRF creation.'))
                return
            
            # Create or get workflow
            workflow = WorkflowTemplate.objects.filter(company=company, is_default=True).first()
            
            # Create MRF
            mrf, created = MRF.objects.get_or_create(
                mrf_name='Senior Software Engineer - Backend',
                department=dept,
                designation=desig,
                company=company,
                defaults={
                    'workflow_template': workflow,
                    'requested_by': requested_by,
                    'requested_by_name': requested_by.name,
                    'requested_by_designation': 'HR Manager',
                    'team': 'Backend Team',
                    'position_department': dept,
                    'no_of_vacancies': 2,
                    'location': 'Ahmedabad',
                    'job_type': 'work_from_office',
                    'business_justification': 'Need to scale backend infrastructure for growing user base.',
                    'salary_range': '15-22 LPA',
                    'experience_range': '5-8 years',
                    'skills_competencies': 'Python, Django, PostgreSQL, AWS, Microservices',
                    'key_responsibility': 'Design and develop scalable backend systems',
                    'required_qualifications': 'B.Tech/M.Tech in Computer Science',
                    'expected_date_of_joining': timezone.now().date() + timedelta(days=45),
                    'status': 'approved',
                    'priority': 'high',
                    'current_approval_level': 3,
                    'submitted_at': timezone.now() - timedelta(days=5),
                    'approved_at': timezone.now() - timedelta(days=2),
                }
            )
            
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created sample MRF: {mrf.mrf_name}'))
                
                # Create related Job
                job, job_created = Job.objects.get_or_create(
                    mrf=mrf,
                    defaults={
                        'job_title': mrf.mrf_name,
                        'department': dept,
                        'designation': desig,
                        'location': mrf.location,
                        'job_type': mrf.job_type,
                        'no_of_positions': mrf.no_of_vacancies,
                        'key_responsibility': mrf.key_responsibility,
                        'required_qualifications': mrf.required_qualifications,
                        'experience_range': mrf.experience_range,
                        'skills_competencies': mrf.skills_competencies,
                        'technical_skills': 'Python, Django, REST APIs',
                        'salary_range': mrf.salary_range,
                        'status': 'open',
                        'priority': mrf.priority,
                        'company': company,
                        'posted_by': requested_by,
                        'expected_closure_date': timezone.now().date() + timedelta(days=30),
                        'is_active': True,
                    }
                )
                
                if job_created:
                    self.stdout.write(self.style.SUCCESS(f'Created related Job: {job.job_title}'))
                    
                    # Create sample application link
                    link, link_created = JobApplicationLink.objects.get_or_create(
                        job=job,
                        platform='direct',
                        defaults={
                            'title': 'Direct Application Link',
                            'description': 'Demo application link for testing',
                            'created_by': requested_by,
                            'is_active': True,
                        }
                    )
                    if link_created:
                        self.stdout.write(self.style.SUCCESS('Created demo application link'))
                
                # Create a sample JobApplication (without resume to avoid file issues)
                from jobs.models import JobApplication
                app, app_created = JobApplication.objects.get_or_create(
                    job=job,
                    candidate_name='Demo Candidate',
                    candidate_email='demo.candidate@example.com',
                    defaults={
                        'source': 'direct',
                        'status': 'shortlisted',
                        'candidate_phone': '9876543210',
                        'experience_years': 6.5,
                        'current_ctc': '12 LPA',
                        'expected_ctc': '18 LPA',
                        'notes': 'Strong Python/Django background. Good fit for the role.',
                        'match_score': 85.5,
                    }
                )
                if app_created:
                    self.stdout.write(self.style.SUCCESS('Created sample job application'))
            else:
                self.stdout.write(self.style.WARNING('Sample MRF already exists'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample MRF: {str(e)}'))
            # Don't raise to allow partial seeding

    def create_referral_applications(self, company):
        """Create sample ReferralApplication records to test filters"""
        referral_data = [
            {
                'referral_name': 'Alice Johnson',
                'referral_email': 'alice@knowcraft.in',
                'referral_phone': '9876543201',
                'referral_emp_code': 'EMP001',
                'referral_designation': 'Senior Engineer',
                'referral_department': 'Engineering',
                'position_title': 'Senior Software Engineer',
                'notes': 'Referred a strong backend candidate with 7 years exp.',
                'is_touched': False,
            },
            {
                'referral_name': 'Bob Smith',
                'referral_email': 'bob@knowcraft.in',
                'referral_phone': '9876543202',
                'referral_emp_code': 'EMP002',
                'referral_designation': 'HR Manager',
                'referral_department': 'Human Resources',
                'position_title': 'HR Executive',
                'notes': 'Referred internal candidate for HR role.',
                'is_touched': True,
            },
            {
                'referral_name': 'Carol Davis',
                'referral_email': 'carol.sales@knowcraft.in',
                'referral_phone': '9876543203',
                'referral_emp_code': 'EMP003',
                'referral_designation': 'Sales Lead',
                'referral_department': 'Sales & Marketing',
                'position_title': 'Business Development Executive',
                'notes': 'High priority referral from sales team.',
                'is_touched': False,
            },
        ]
        
        for data in referral_data:
            ref_app, created = ReferralApplication.objects.get_or_create(
                referral_email=data['referral_email'],
                position_title=data['position_title'],
                defaults={
                    'referral_name': data['referral_name'],
                    'referral_phone': data['referral_phone'],
                    'referral_emp_code': data['referral_emp_code'],
                    'referral_designation': data['referral_designation'],
                    'referral_department': data['referral_department'],
                    'notes': data['notes'],
                    'is_touched': data['is_touched'],
                    'touched_at': timezone.now() if data['is_touched'] else None,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created referral application from: {ref_app.referral_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Referral application already exists for: {data["referral_name"]}'))
        
        self.stdout.write(self.style.SUCCESS('Created 3 demo referral applications for filter testing.'))


if __name__ == '__main__':
    # For direct execution if needed
    pass

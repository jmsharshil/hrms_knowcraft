# # mrf/utils.py
# from datetime import time
# from django.utils import timezone
# from .models import MRF

# def is_after_5pm(dt):
#     dt_local = dt.astimezone(timezone.get_default_timezone())
#     return dt_local.time() > time(17, 0, 0)

# def determine_next_working_date_if_after_5pm(dt):
#     # returns date
#     if is_after_5pm(dt):
#         from .models import next_working_day
#         return next_working_day(dt)
#     return dt.astimezone(timezone.get_default_timezone()).date()

SALARY_BANDS = {
    "Valuation": {
        "Analyst": (500000, 700000),
        "Advanced Analyst": (700000, 950000),
        "Senior Analyst-I": (950000, 1250000),
        "Senior Analyst-II": (1250000, 1550000),
        "Assistant Manager": (1550000, 2200000),
        "Associate Manager": (2200000, 2700000),
        "Manager": (2500000, 3000000),
        "Senior Manager": (3000000, 4000000),
    },

    "Investment Banking": {
        "Analyst": (500000, 650000),
        "Advanced Analyst": (650000, 850000),
        "Senior Analyst-I": (850000, 1150000),
        "Senior Analyst-II": (1150000, 1450000),
        "Assistant Manager": (1450000, 2000000),
        "Associate Manager": (2200000, 2700000),
        "Manager": (2500000, 3000000),
        "Senior Manager": (2500000, 3200000),
    },

    "US Accounts": {
        "Associate": (400000, 550000),
        "Advanced Associate": (500000, 650000),
        "Senior Associate-I": (650000, 800000),
        "Senior Associate-II": (800000, 1000000),
        "Team Lead": (1000000, 1300000),
        "Assistant Manager": (1300000, 1500000),
        "Associate Manager": (1500000, 1750000),
        "Manager": (1750000, 2250000),
    },

    "US Tax": {
        "Associate": (400000, 500000),
        "Advanced Associate": (500000, 650000),
        "Senior Associate-I": (650000, 800000),
        "Senior Associate-II": (800000, 1000000),
        "Team Lead": (1000000, 1300000),
        "Assistant Manager": (1300000, 1750000),
        "Associate Manager": (1500000, 1750000),
        "Manager": (1750000, 2250000),
    },

    "FDD": {
        "Associate": (400000, 500000),
        "Advanced Associate": (500000, 650000),
        "Senior Associate-I": (650000, 800000),
        "Senior Associate-II": (800000, 1000000),
        "Team Lead": (1000000, 1300000),
        "Assistant Manager": (1300000, 1500000),
        "Associate Manager": (1500000, 1750000),
        "Manager": (1750000, 2250000),
    },

    "Marketing": {
        "Associate": (300000, 450000),
        "Advanced Associate": (400000, 500000),
        "Senior Associate": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },

    "HR and Administration": {
        "Associate": (300000, 450000),
        "Advanced Associate": (400000, 500000),
        "Senior Associate": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },

    "Information Technology": {
        "Associate": (300000, 450000),
        "Advanced Associate": (400000, 500000),
        "Senior Associate": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },

    "Internal Accounts": {
        "Associate": (300000, 450000),
        "Advanced Associate": (400000, 500000),
        "Senior Associate": (500000, 650000),
        "Team Lead": (600000, 800000),
        "Assistant Manager": (800000, 1000000),
        "Associate Manager": (1000000, 1300000),
        "Manager": (1200000, 1500000),
    },
}
from django.core.exceptions import ValidationError

def validate_salary_range(salary_range,department_name,designation_name):
    if hasattr(department_name, "name"):
        department_name = department_name.name

    if hasattr(designation_name, "name"):
        designation_name = designation_name.name

    if department_name not in list(SALARY_BANDS.keys()):
            return

    if designation_name not in list(SALARY_BANDS[department_name].keys()):
        return

    allowed_min, allowed_max = SALARY_BANDS[department_name][designation_name]
        # Parse salary_range (e.g. "5-8 LPA" → 500000 - 800000)
    try:
        parts = salary_range.lower().replace("lpa", "").replace(",", "").replace("to", "-").replace(",", "").replace(" ", "").strip()
        if "-" not in parts:
            raise ValueError("Salary range must contain '-'")
        raw_min,raw_max = parts.split('-')
        s_min,s_max = float(raw_min),float(raw_max)
        if s_min < 1000:
            s_min = s_min * 100000
        if s_max < 1000:
            s_max = s_max * 100000
    except Exception:
        raise ValidationError("Salary must be in valid range format.")

    # Validate boundaries
    if s_min < allowed_min or s_max > allowed_max:
        raise ValidationError(
            f"Salary for {designation_name} in {department_name} must be between "
            f"{allowed_min:,} and {allowed_max:,}."
        )

def get_auto_salary_range(department, designation):
    # Handle model instances
    if hasattr(department, "name"):
        department = department.name

    if hasattr(designation, "name"):
        designation = designation.name

    department = str(department).strip()
    designation = str(designation).strip()
    try:
        if department not in list(SALARY_BANDS.keys()):
            return

        if designation not in list(SALARY_BANDS[department].keys()):
            return

        min_sal, max_sal = SALARY_BANDS[department][designation]
        return f"{min_sal} - {max_sal}"
    except KeyError:
        return None

email_templates = {
    "mrf_submit_new":f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Dear <strong>{{manager_name}}</strong>,</p>
        <p>
            We would like to inform you that a requisition for
            <strong>{{designation}}</strong> position was raised by 
            <strong>{{hod_name}}</strong> on <strong>{{date}}</strong> 
            as a <strong>new request</strong>.
        </p>
        <p>
            We kindly request you to review the requisition and take the necessary 
            action at the earliest.
        </p>
        <p>Thank you for your support.</p>
        <p>
            Best regards,<br>
            <strong>Team HR</strong>
        </p>
    </body>
    </html>""",
    "mrf_submit_replace":f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <p>Dear <strong>{{manager_name}}</strong>,</p>
        <p>
            We would like to inform you that a requisition for 
            <strong>{{designation}}</strong> position was raised by 
            <strong>{{hod_name}}</strong> on <strong>{{date}}</strong>, 
            for the replacement of <strong>{{resigned_employee}}</strong>.
        </p>
        <p>
            We kindly request you to review the requisition and take the necessary 
            action at the earliest.
        </p>
        <p>Thank you for your support.</p>
        <p>
            Best regards,<br>
            <strong>Team HR</strong>
        </p>
    </body>
    </html>
    """,
    "mrf_reminder":f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
        <p>Dear {{manager_name}},</p>
        <p>
            This is a gentle reminder that a requisition for an 
            <strong>{{position}}</strong> position was raised on 
            <strong>{{requisition_date}}</strong>.
        </p>
        <p>
            We kindly request you to review the requisition and take the necessary action at the earliest.
        </p>
        <p>Thank you for your attention.</p>
        <p>Best regards,<br>
        <strong>Team HR</strong></p>
    </body>
    </html>
    """
}

alt_text = {
    "mrf_submit_replace":f"""
Dear {{manager_name}},
We would like to inform you that a requisition for an Analyst – {{designation}} position was raised by {{hod_name}} on {{date}}, for the replacement of {{resigned_employee}}.
We kindly request you to review the requisition and take the necessary action at the earliest.
Thank you for your support.
Best regards,
Team HR
""",
    "mrf_submit_new":f"""Dear {{manager_name}},
We would like to inform you that a requisition for an Analyst – {{designation}} position was raised by {{hod_name}} on {{date}} as a new request.
We kindly request you to review the requisition and take the necessary action at the earliest.
Thank you for your support.
Best regards,
Team HR
""",
    "mrf_reminder":f"""Dear {{manager_name}},
This is a gentle reminder that a requisition for an {{position}} position was raised on {{requisition_date}}.
Kindly review the requisition and take the necessary action at the earliest.
Thank you.
Best regards,
Team HR
"""
}

import threading
import time
from .models import MRF
from accounts.models import User
from onboarding.utils.sender import send_email
def schedule_mrf_reminder(mrf_id):
    """Runs a reminder check after 48 hours in a background thread."""

    def task():
        time.sleep(48 * 60 * 60)  # 48 hours

        try:
            mrf = MRF.objects.get(id=mrf_id)

            if mrf.status in ["approved", "rejected"]:
                return
            
            if not mrf.status.startswith("pending"):
                return
            
            # Only send reminder if still pending
            if mrf.status not in ["approved", "rejected"]:
                # manager = User.objects.filter(role="hr_manager").first()
                next_level = mrf.current_approval_level + 1

                workflow = mrf.workflow_template.levels.filter(
                    level=next_level,
                    is_active=True
                ).select_related('approver').first()

                if not workflow or not workflow.approver:
                    return

                approver = workflow.approver

                if not approver.is_active or approver.company_id != mrf.company_id:
                    return

                if approver:
                    template = email_templates["mrf_reminder"].format(
                        manager_name=approver.name,
                        position=mrf.designation.name,
                        requisition_date=mrf.created_at.strftime("%B %d, %Y")
                    )

                    text = alt_text["mrf_reminder"].format(
                        manager_name=approver.name,
                        position=mrf.designation.name,
                        requisition_date=mrf.created_at.strftime("%B %d, %Y")
                    )

                    send_email(
                        to=approver.email,
                        subject=f"Reminder – Requisition Pending Review",
                        template=template,
                        text=text
                    )
                    print(f"Reminder email sent for MRF {mrf_id}")

        except Exception as e:
            print(f"Reminder scheduler error: {e}")

    threading.Thread(target=task, daemon=True).start()

from datetime import timedelta
from django.utils import timezone

def get_expected_date_of_joining(designation):
    """
    Calculate expected DOJ based on department-designation TAT model
    """
    from .models import Designation
    if hasattr(designation, "id"):
        designation = designation.id
    tat_days = None
    joining_obj = Designation.objects.filter(id=designation).first()
    if joining_obj and joining_obj.tat_days:
        tat_days = joining_obj.tat_days
    else:
        tat_days= 0

    return timezone.now().date() + timedelta(days=tat_days)

FIELD_VALUES={
    'HR and Administration':{
     "Associate HR":   {
        "key_responsibility":"Recruitment coordination; onboarding formalities; leave & attendance management; payroll support; HRMS knowledge; preparation of HR letters; exit process; employee relations; engagement activities; strong communication skills.",
        "required_qualifications":"Required: Post Graduation/MBA in Human Resources.",
        "skills_competencies":"0–1 years experience in HR & Admin; knowledge of employment law, compensation, recruitment, employee relations, engagement; ability to multi-task in fast-paced environment."
    },
    "Senior Associate-I":   {
        "key_responsibility":"Recruitment coordination; onboarding; HR policy communication; preparation of HR letters; exit process; employee grievance handling; engagement activities; strong interpersonal and problem-solving skills; excellent communication.",
        "required_qualifications":"Required: Bachelor’s degree with Post Graduation/MBA in Human Resources.",
        "skills_competencies":"1–3 years experience in HR & Admin; knowledge of employment law, compensation, recruitment, employee relations, engagement; ability to multi-task in fast-paced environment."
    },
    "Senior Associate-II":   {
        "key_responsibility":"End-to-end payroll processing; salary input compilation; statutory compliance (TDS, PF, ESIC, PT, Gratuity); HRMS operations; leave & attendance management; benefits administration; issue resolution; strong communication and data privacy adherence.",
        "required_qualifications":"Required: Post Graduation/MBA in Human Resources.",
        "skills_competencies":"Minimum 2 years experience in HR (Payroll); knowledge of employment law, compensation, recruitment, employee relations, engagement; ability to multi-task in fast-paced environment."
    }},
    'IT':{
     "Associate":   {
        "key_responsibility":"Remote helpdesk support; ticketing system management; IT support for online training; patch and upgrade management; technical leadership; coordination with third-party providers; professionalism under stress.",
        "required_qualifications":"Required: Bachelor’s degree in Computer Engineering, IT, or related fields. ",
        "skills_competencies":"1–2 years experience in IT or related position; ability to resolve issues quickly; strong communication skills. "
    },
    "Senior Associate":   {
        "key_responsibility":"Advanced helpdesk support; escalation handling; patch and upgrade management; technical leadership; coordination with third-party providers; proactive problem-solving; strong analytical and presentation skills.",
        "required_qualifications":"Required: Bachelor’s degree in Computer Engineering, IT, or related fields. ",
        "skills_competencies":"2–4 years experience in IT or related position; ability to resolve issues quickly; strong communication skills."
    },
    "Assistant Manager":   {
        "key_responsibility":"Install, upgrade, troubleshoot hardware/software; preventive maintenance; onsite diagnosis; network troubleshooting; ISO audit handling; inventory tracking; patch cord creation; strong knowledge of LAN/WAN and MS tools.",
        "required_qualifications":"Required: Diploma in Computer/Electronics Engineering or related program. Preferred: Industry certifications (A+, N+, MCP, MCSA, CCNA, CCNP).",
        "skills_competencies":"Minimum 4 years experience in IT; ability to lead a team; strong communication and analytical skills. "
    },
    "Associate Manager":   {
        "key_responsibility":"Maintain IT infrastructure (OS, security tools, servers, firewall, Azure cloud); manage IT projects and helpdesk; research emerging technologies; vendor management; disaster recovery; ISO 27001 compliance; manage Microsoft 365 and cloud storage systems; team training and coaching. ",
        "required_qualifications":"Required: Bachelor’s degree in Computer Engineering, IT, or related fields. Preferred: Professional certifications (Microsoft, Azure Cloud).",
        "skills_competencies":"Minimum 5 years experience in IT management; prior work experience in related position; strong communication and managerial skills. "
    },
    "Manager":   {
        "key_responsibility":"Oversee IT infrastructure (hardware, software, network); manage IT staff and annual budget; vendor analysis; disaster planning and backups; ISO 27001 compliance; technical management and information analysis; strong knowledge of operating systems, enterprise backup, and recovery procedures; excellent communication and multitasking skills.",
        "required_qualifications":"Required: Bachelor’s degree in Computer Engineering, IT, or related fields.Preferred: Professional certifications (MCP, MCSA, CCNA, CCNP).",
        "skills_competencies":"Minimum 5+ years experience in IT management; prior experience as IT Manager; strong technical and leadership skills; familiarity with ISO 27001 framework. "
    }},
    'Internal Accounts':{
    "Senior Associate":   {
        "key_responsibility":"Statutory compliance (GST, TDS, Professional Tax, Income Tax); e-TDS/GST returns; accounting entries (sales, purchases, receipts, payments); bank reconciliation; budgeting & variance analysis; payroll processing; knowledge of Balance Sheet & P&L; MIS reporting; strong analytical and communication skills.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting.Preferred: Master’s degree; Inter CA or pursuing CA. ",
        "skills_competencies":"3–4 years experience in accounting; working knowledge of GST, TDS, IT returns; exposure to US GAAP; proficiency in MS Office; experience with SAP/QuickBooks/Zoho preferred."
    },
    "Associate":   {
        "key_responsibility":"Basic knowledge of General Accounting, Ledger, Taxation, Bookkeeping; data entry; financial analysis; invoicing; preparation of management reports; handling cash/bank; client/vendor communication; strong analytical and organizational skills.",
        "required_qualifications":"Required: Bachelor’s degree in Commerce (preferred).Preferred: Master’s degree; Inter CA or pursuing CA. ",
        "skills_competencies":"Fresher or reasonable prior experience in Accounts; proficiency in MS Office (Excel & Word); experience with accounting software (SAP/QuickBooks/Zoho preferred)."
    }},
    'Investment Banking':{
     "Analyst":   {
        "key_responsibility":"Prepare investment presentations and memorandums; research company/regulatory landscape; market sizing and mapping; build financial models and valuations; strong analytical and presentation skills.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting or Finance.Preferred: Master’s degree; CFA or CA certification (obtained or in process).",
        "skills_competencies":"0–6 months experience in investment banking; exposure to information memoranda, presentations, and financial modeling; strong desire to learn."
    },
    "Advanced Analyst":   {
        "key_responsibility":"Build complex financial models (DCF, LBO, M&A); conduct industry research; support transactions; prepare pitch books and memorandums; client collaboration; due diligence; presentation development; project management.",
        "required_qualifications":"Required: Master’s degree in Finance, Accounting, Economics, or related field.Preferred: CFA, MBA, or relevant certifications.",
        "skills_competencies":"Minimum 1 year experience in investment banking or financial analysis; proficiency in financial modeling and advanced Excel; familiarity with Bloomberg, Thomson Reuters, Pitchbook, CapIQ."
    },
    "Senior Analyst-I":   {
        "key_responsibility":"Prepare investment presentations and memorandums; conduct industry research; market sizing and mapping; build comprehensive financial models and valuations; strong quantitative and presentation skills.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting or Finance.Preferred: Master’s degree; CFA or CA certification (obtained or in process).",
        "skills_competencies":"2–4 years experience in investment banking; exposure to information memoranda, presentations, and financial modeling; strong analytical and communication skills."
    },
    "Senior Analyst-II":   {
        "key_responsibility":"Prepare investment presentations and memorandums; conduct industry research; market sizing and mapping; build comprehensive financial models and valuations; strong quantitative and presentation skills.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting or Finance.Preferred: Master’s degree; CFA or CA certification (obtained or in process).",
        "skills_competencies":"2–4 years experience in investment banking; exposure to information memoranda, presentations, and financial modeling; strong analytical and communication skills."
    },
    "Assistant Manager":   {
        "key_responsibility":"Develop and maintain complex financial models (DCF, LBO, merger models); conduct valuation analysis; prepare pitch books, CIMs, investor presentations; perform industry research; strong Excel, PowerPoint, and database skills (Bloomberg, CapIQ, PitchBook); team leadership and business development.",
        "required_qualifications":"Required: Bachelor’s/Master’s degree in Finance, Economics, Accounting, or related field.Preferred: CFA, CA, MBA (Finance).",
        "skills_competencies":"Minimum 4–6 years experience in investment banking, financial services, or related field; prior experience in outsourced IB, equity research, private equity, or transaction advisory desirable."
    },"Manager":   {
        "key_responsibility":"Lead transaction support (M&A, capital raising); develop and review financial models; manage client relationships; supervise team; drive business development; implement process excellence; exposure to advanced analytics tools; strong communication and presentation skills.",
        "required_qualifications":"Required: Bachelor’s/Master’s degree in Finance or related field.Preferred: CFA, CA, MBA; familiarity with U.S. GAAP and capital markets",
        "skills_competencies":"Minimum 7–8 years experience in investment banking or financial services; hands-on experience in financial modeling, valuation, and transaction advisory; U.S. visa preferred but not mandatory."
    }},
    'Marketing':{
     "":   {
        "key_responsibility":"",
        "required_qualifications":"",
        "skills_competencies":""
    }},
    'Transaction Advisory Services':{
     "Associate":   {
        "key_responsibility":"Review and analyze financial statements; assist in identifying financial risks; prepare due diligence reports; support financial modeling; organize and summarize financial data; participate in client meetings; strong attention to detail and communication skills",
        "required_qualifications":"Required: CA, MBA (Finance), or equivalent qualification",
        "skills_competencies":"0–1 years experience in financial due diligence, audit, or transaction advisory; strong understanding of US GAAP/IFRS; proficiency in Excel, PowerPoint, and financial modeling tools."
    },
    "Senior Associate":   {
        "key_responsibility":"Advanced financial analysis; prepare QoE reports; assist in client deliverables; coordinate with cross-functional teams; manage project timelines; strong interpersonal and analytical skills; ability to handle technical and strategic aspects.",
        "required_qualifications":"Required: CA, MBA (Finance), or equivalent qualification",
        "skills_competencies":"1–2 years experience in financial due diligence, audit, or transaction advisory; strong technical accounting knowledge; proficiency in Excel, PowerPoint, and financial modeling tools."
    },
    "Assistant Manager":   {
        "key_responsibility":"Lead transaction evaluation; prepare QoE and adjusted EBITDA schedules; conduct working capital analysis; review contracts and risks; develop comprehensive reports; mentor junior staff; manage client expectations; strong",
        "required_qualifications":"Required: CA, CPA, CFA, MBA (Finance), or equivalent qualification",
        "skills_competencies":"3–6 years experience in financial due diligence, audit, or transaction advisory; strong understanding of US GAAP/IFRS; proficiency in Excel, PowerPoint, and financial modeling tools; excellent communication skills."
    },
    "Manager":   {
        "key_responsibility":"leadership and strategic thinking skills.Lead FDD engagements; manage profit center; business development (client pitching, pricing strategies); delivery management; analyze financial and operational results; identify negotiation factors; research industry trends; formulate growth strategies; hiring, mentoring, and training team; strong leadership and strategic thinking.",
        "required_qualifications":"Required: MBA (Premier B-School) or MS (Finance).Preferred: Certifications such as CPA (AICPA), CMA (IMA), CFA (CFA Institute, US), CA (ICAI), or investment banking certification.",
        "skills_competencies":"Minimum 8 years of work experience; must have handled a team of at least 5 individuals; experience working with global clients (USA and Canada); excellent verbal and written communication skills."
    },
    "Senior Manager":   {
        "key_responsibility":"Lead FDD engagements; manage profit center; business development (client pitching, pricing strategies); delivery management; analyze financial and operational results; identify negotiation factors; research industry trends; formulate growth strategies; hiring, mentoring, and training team; strong leadership and strategic thinking.",
        "required_qualifications":"Required: MBA (Premier B-School) or MS (Finance).Preferred: Certifications such as CPA (AICPA), CMA (IMA), CFA (CFA Institute, US), CA (ICAI), or investment banking certification.",
        "skills_competencies":"Minimum 10 years of work experience; must have handled a team of at least 10 individuals; experience working with global clients (USA and Canada); excellent verbal and written communication skills"
    }},
    'US Accounts':{
     "Associate":   {
        "key_responsibility":"Bookkeeping (daily, weekly, monthly, quarterly, yearly); core finance & accounting concepts; identify technical issues; professional communication; analytical and presentation skills.",
        "required_qualifications":"Required: B.Com / M.Com / PGDM (Finance) / MBA (Finance).Preferred: CA or Semi-qualified CA; CMA; CPA.",
        "skills_competencies":"0–6 months experience in finance/accounting (preferably US accounting); exposure to US GAAP; knowledge of accounting software; strong desire to learn."
    },
    "Advanced Associate":   {
        "key_responsibility":"Bookkeeping across all periods; core finance & accounting concepts; resolve client technical issues; professional communication; analytical and presentation skills.",
        "required_qualifications":"Required: B.Com / M.Com / PGDM (Finance) / MBA (Finance).Preferred: CA or Semi-qualified CA; CMA; CPA.",
        "skills_competencies":"6–12 months experience in finance/accounting (preferably US accounting); exposure to US GAAP; knowledge of accounting software; strong desire to learn."
    },
    "Senior Associate-I":   {
        "key_responsibility":"Advanced bookkeeping; strong finance & accounting knowledge; resolve complex client issues; professional communication; analytical and presentation skills; ability to work on multiple assignments.",
        "required_qualifications":"Required: B.Com / M.Com / PGDM (Finance) / MBA (Finance).Preferred: CA or Semi-qualified CA; CMA; CPA.",
        "skills_competencies":"2–4 years experience in finance/accounting (preferably US accounting); exposure to US GAAP; knowledge of accounting software; strong desire to learn."
    },
    "Senior Associate-II":   {
        "key_responsibility":"Advanced bookkeeping; strong finance & accounting knowledge; resolve complex client issues; professional communication; analytical and presentation skills; ability to work on multiple assignments.",
        "required_qualifications":"Required: B.Com / M.Com / PGDM (Finance) / MBA (Finance).Preferred: CA or Semi-qualified CA; CMA; CPA.",
        "skills_competencies":"2–4 years experience in finance/accounting (preferably US accounting); exposure to US GAAP; knowledge of accounting software; strong desire to learn."
    },
    "Assistant Manager":   {
        "key_responsibility":"Perform and review bookkeeping/accounting services; manage team of Associates and Senior Associates; identify and resolve technical issues; review final entries/reports; strong communication, analytical, and presentation skills.",
        "required_qualifications":"Preferred: Master’s Degree in Accounting and/or Finance; CPA, CMA, and/or CA certification (obtained or in process).",
        "skills_competencies":"4–6 years experience in finance/accounting (preferably US accounting); exposure to US GAAP; experience with QuickBooks/integrated ERP; must have managed a team of 3+ individuals; valid US visa is an advantage."
    }},
    'US Taxation':{
     "Associate":   {
        "key_responsibility":"Prepare and review US Business Tax returns (1065/1120/1120S); strong analytical and problem-solving skills; attention to detail; excellent verbal and written communication.",
        "required_qualifications":"Required: Master’s degree in Finance, Taxation, or related field.Preferred: CPA, EA, or equivalent qualification.",
        "skills_competencies":"0–12 months experience in US business tax preparation and self-review; knowledge of US federal, state, and local tax regulations; proficiency in tax software (CCH Axcess, ProSystem fx, UltraTax CS)."
    },
    "Senior Associate-I":   {
        "key_responsibility":"Prepare and review complex tax returns; tax projections; client communication; strong quantitative and analytical skills; proficiency in tax software; understanding of US tax concepts.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting/Finance; Master’s degree preferable.Preferred: MBA, M.Com, EA, CA, CA-Inter, CPA.",
        "skills_competencies":"Minimum 2 years experience in US Individual and Corporate Tax returns (1040/1065/1120/1120S); experience with tax software (UltraTax CS preferred); strong oral and email communication skills."
    },
    "Senior Associate-II":   {
        "key_responsibility":"Prepare and review complex tax returns; tax projections; client communication; strong quantitative and analytical skills; proficiency in tax software; understanding of US tax concepts.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting/Finance; Master’s degree preferable.Preferred: MBA, M.Com, EA, CA, CA-Inter, CPA.",
        "skills_competencies":"Minimum 2 years experience in US Individual and Corporate Tax returns (1040/1065/1120/1120S); experience with tax software (UltraTax CS preferred); strong oral and email communication skills."
    },
    "Team Lead":   {
        "key_responsibility":"Review tax returns; manage client engagements end-to-end; identify book-to-tax adjustments; train junior staff; proficiency in US tax software; excellent written and verbal communication; strong technical knowledge of US tax laws.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting/Finance; Master’s degree preferable.Preferred: MBA, M.Com, EA, CA, CA-Inter, CPA.",
        "skills_competencies":"Minimum 3–4 years experience in US Individual and Corporate Tax returns; experience with tax software (UltraTax CS preferred); ability to manage 4–6 team members; strong communication and leadership skills."
    },
    "Assistant Manager":   {
        "key_responsibility":"Review Federal & State tax returns; identify book-to-tax adjustments; manage engagements end-to-end; research new tax topics; train team; monitor budgets; strong leadership and communication; proficiency in US tax software.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting/Finance; Master’s degree preferable.Preferred: MBA, M.Com, EA, CA, CA-Inter, CPA.",
        "skills_competencies":"Minimum 5 years experience in US Individual & Corporate Tax returns (1040/1065/1120/1120S); experience with tax software (UltraTax CS preferred); ability to manage 5–10 team members."
    },
    "Associate Manager":   {
        "key_responsibility":"Review Federal & State tax returns; manage client engagements; research tax topics; train team; monitor budgets; strong leadership and communication; proficiency in US tax software; ability to lead by example.",
        "required_qualifications":"Required: Bachelor’s degree in Accounting/Finance; Master’s degree preferable.Preferred: MBA, M.Com, EA, CA, CA-Inter, CPA.",
        "skills_competencies":"Minimum 6–8 years experience in US Individual & Corporate Tax returns; experience with tax software (UltraTax CS preferred); proven team leadership and client engagement skills."
    },"Manager":   {
        "key_responsibility":"Lead preparation and review of Federal, State, and Local tax returns; act as technical advisor; manage client relationships; mentor team; ensure compliance; stay updated on IRS regulations; strong leadership and business development skills.",
        "required_qualifications":"Required: CA, CPA, or EA certification preferred; strong domain knowledge of US Business Taxation.",
        "skills_competencies":"Minimum 7 years experience in US Business Tax compliance and advisory; proven client communication, project management, and team development skills; prior experience in tax outsourcing or consulting firms preferred."
    }},
    'Valuation':{
     "Analyst":   {
        "key_responsibility":"Well‑versed in income, market, asset approaches; discount rates, discounts, premiums.Strong grasp of three financial statements and key ratios.Financial/forecasting models from scratch (preferred).Perform financial analyses, financial modeling, report writing, and company/industry/economic research.Gather data; plan/manage schedule; validate adequacy of data; review own and teammates’ work; participate in client calls; execute under seniors’ supervision.",
        "required_qualifications":"Required: MBA (Premier B‑School) Add-on: MS (Finance), CA and/or CFA (CFA Institute, US) Preferred: CVA, ASA, and/or ABV ",
        "skills_competencies":"0–6 months in valuation and/or consulting. Big Four valuation team or leading valuation firm. Ability to effectively communicate with team, seniors, and clients. Excellent quantitative, analytical, written, and presentation skills"
    },"Advanced Analyst":   {
        "key_responsibility":"Well‑versed in income, market, asset approaches; discount rates, discounts, premiums.Strong grasp of three financial statements and key ratios.Financial/forecasting models from scratch (preferred).Perform financial analyses, financial modeling, report writing, and company/industry/economic research.Gather data; plan/manage schedule; validate adequacy of data; review own and teammates’ work; participate in client calls; execute under seniors’ supervision.",
        "required_qualifications":"Required: MBA (Premier B‑School) Add-on: MS (Finance), CA and/or CFA (CFA Institute, US) Preferred: CVA, ASA, and/or ABV",
        "skills_competencies":"6–12 months in valuation and/or consulting. Valuation or analytics firm (experience). Ability to effectively communicate with team, seniors, and clients. Excellent quantitative, analytical, written, and presentation skills."
    },
    "Senior Analyst-I":   {
        "key_responsibility":"Portfolio/Fair Value (ASC 820), Equity Awards (ASC 718/IRC 409A), Business Combinations (ASC 805), Goodwill Impairment (ASC 350/360), Embedded Derivatives (ASC 815), Gift & Estate (working knowledge preferred). Advanced ability to summarize analyses and conclusions in complex valuation reports. Financial/forecasting models from scratch (preferred); oversee multiple engagements; quality control of deliverables.Plan, organize, conduct, and manage valuation engagements; lead and mentor analysts; collaborate across teams. Functional team management, daily progression reporting, quality control, simultaneous engagement oversight, complex report writing.",
        "required_qualifications":"Required: MBA (Premier B‑School) Add-on: MS (Finance), CA and/or CFA (CFA Institute, US) Preferred: CVA, ASA, and/or ABV",
        "skills_competencies":"18–36 months in valuation and/or consulting. Big Four valuation team or leading valuation firm (preference).Ability to effectively communicate with team, seniors, and clients. Excellent quantitative, analytical, written, and presentation skills."
    },
    "Senior Analyst-II":   {
        "key_responsibility":"ASC 820, ASC 718 & IRC 409A, ASC 805, ASC 350/360, ASC 815, Gift & Estate valuations; build financial models; manage engagements; quality control; team collaboration; mentor analysts.",
        "required_qualifications":"Required: MBA (Premier B-School).Preferred: MS (Finance), CA, CFA; Certifications: CVA, ASA, ABV",
        "skills_competencies":"24–48 months valuation/consulting experience; preference for Big Four or leading valuation firms; strong communication and analytical skills."
    },"Assistant Manager":   {
        "key_responsibility":"ASC 718 & IRC 409A, ASC 805, ASC 815, ASC 820; build financial models; execute engagements; manage team allocations; quality control; client communication; mentor analysts; plan training; contribute to hiring/operations.",
        "required_qualifications":"Required: MBA (Premier B-School).Preferred: MS (Finance), CA, CFA; Certifications: CVA, ASA, ABV",
        "skills_competencies":"Minimum 4 years valuation/consulting experience; ability to lead a team; preference for leading valuation firms."
    },"Associate Manager":   {
        "key_responsibility":"ASC 820, ASC 718 & IRC 409A, ASC 805, ASC 350/360, ASC 815, Gift & Estate valuations; manage engagements; quality control; client communication; oversee multiple projects; mentor team; plan development; contribute to firmwide initiatives.",
        "required_qualifications":"Required: MBA (Premier B-School).Preferred: MS (Finance), CA, CFA; Certifications: CVA, ASA, ABV",
        "skills_competencies":"5–6 years US valuation experience; proven team management; preference for Big Four or leading valuation firms."
    },
    "Manager":   {
        "key_responsibility":"ASC 820, ASC 718 & IRC 409A, ASC 805, ASC 350/360, ASC 815, Gift & Estate valuations; lead client-facing engagements; strategic guidance; mentor team; plan training; strong communication; exceptional analytical and presentation skills.",
        "required_qualifications":"Required: MBA (Premier B-School).Preferred: MS (Finance), CA, CFA; Certifications: CVA, ASA, ABV.",
        "skills_competencies":"6–8 years business valuation experience; proven leadership; ability to manage individuals and review tasks independently."
    }},
}
def mrf_fields_auto_fill(department, designation):
    from .models import Department,Designation
    # Ensure department and designation are integers (if passed as objects)
    if hasattr(department, "id"):
        department_id = department.id
    else:
        department_id = department  # Assuming it's passed as ID directly
    
    if hasattr(designation, "id"):
        designation_id = designation.id
    else:
        designation_id = designation  # Assuming it's passed as ID directly

    # Now, fetch the department name based on the ID
    department_name = Department.objects.get(id=department_id).name
    designation_name = Designation.objects.get(id=designation_id).name
    
    # Look up the FIELD_VALUES for the relevant department
    if department_name in FIELD_VALUES:
        department_data = FIELD_VALUES[department_name]
    else:
        return {"error": "Department not found in FIELD_VALUES"}
    
    # Now, look up the designation within the department
    if designation_name in department_data:
        designation_data = department_data[designation_name]
    else:
        return {"error": "Designation not found in the specified department"}

    # Fetch the required values for key_responsibility, required_qualifications, and skills_competencies
    key_responsibility = designation_data.get("key_responsibility", "")
    required_qualifications = designation_data.get("required_qualifications", "")
    skills_competencies = designation_data.get("skills_competencies", "")

    # Assuming the `mrf` model has these fields as TextField
    data = {
        "key_responsibility": key_responsibility,
        "required_qualifications": required_qualifications,
        "skills_competencies": skills_competencies,
    }

    return data
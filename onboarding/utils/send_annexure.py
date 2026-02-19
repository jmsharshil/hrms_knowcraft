from .sender import send_email
from accounts.models import User

def send_salary_annexure_email(annexure, requested_by):
    """
    Send full salary annexure details to HR Manager
    """

    candidate = annexure.job_application
    mrf = candidate.job.mrf
    approver = User.objects.filter(role='hr_manager').first()

    # =========================
    # HTML Template
    # =========================

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333; line-height:1.6;">

        <h2 style="color:#2c3e50;">Salary Annexure Approval Required</h2>

        <p>Dear <strong>{approver.name}</strong>,</p>

        <p>
        Please review the salary annexure for candidate 
        <strong>{candidate.candidate_name}</strong>.
        </p>

        <h3>Candidate & Annexure Details</h3>

    <table border="1" cellpadding="6" cellspacing="0" width="100%">
        <tr><td><b>Candidate Name</b></td><td>{candidate.candidate_name}</td></tr>
        <tr><td><b>Designation</b></td><td>{annexure.designation}</td></tr>
        <tr><td><b>Effective From</b></td><td>{annexure.effective_from}</td></tr>
        <tr><td><b>Gross Monthly</b></td><td>{annexure.gross_monthly}</td></tr>
        <tr><td><b>Net Monthly</b></td><td>{annexure.net_monthly}</td></tr>
        <tr><td><b>CTC Annual</b></td><td>{annexure.ctc_annual}</td></tr>
        <tr><td><b>Status</b></td><td>{annexure.status}</td></tr>
        <tr><td><b>Revision Count</b></td><td>{annexure.revision_count}</td></tr>
        <tr><td><b>Prepared By</b></td><td>{annexure.prepared_by}</td></tr>
        <tr><td><b>Reviewed By</b></td><td>{annexure.reviewed_by or "-"}</td></tr>
        <tr><td><b>Created At</b></td><td>{annexure.created_at}</td></tr>
        <tr><td><b>Updated At</b></td><td>{annexure.updated_at}</td></tr>
        <tr><td><b>Notes</b></td><td>{annexure.notes or "-"}</td></tr>
        <tr><td><b>Rejection Reason</b></td><td>{annexure.rejection_reason or "-"}</td></tr>
    </table>

    <br>

    <h3>Monthly Earnings / Allowances</h3>

    <table border="1" cellpadding="6" cellspacing="0" width="100%">
        <tr><td>Basic + DA</td><td>{annexure.basic_da}</td></tr>
        <tr><td>Basket Allowances</td><td>{annexure.basket_allowances}</td></tr>
        <tr><td>HRA</td><td>{annexure.hra}</td></tr>
        <tr><td>Medical Allowance</td><td>{annexure.medical_allowance}</td></tr>
        <tr><td>Leave Travel Allowance</td><td>{annexure.leave_travel_allowance}</td></tr>
        <tr><td>Telephone / Internet</td><td>{annexure.telephone_internet_allowance}</td></tr>
        <tr><td>Books & Periodicals</td><td>{annexure.books_periodicals}</td></tr>
        <tr><td>Uniform Allowance</td><td>{annexure.uniform_allowance}</td></tr>
        <tr><td>Driver Salary</td><td>{annexure.driver_salary}</td></tr>
        <tr><td>Car Maintenance</td><td>{annexure.car_maintenance}</td></tr>
        <tr><td>Meals Allowance</td><td>{annexure.meals_allowance}</td></tr>
        <tr><td>Special Allowance</td><td>{annexure.special_allowance}</td></tr>
        <tr><td>Children Education Allowance</td><td>{annexure.children_education_allowance}</td></tr>
        <tr><td>Conveyance Allowance</td><td>{annexure.conveyance_allowance}</td></tr>
    </table>

    <br>

    <h3>Employer Contributions</h3>

    <table border="1" cellpadding="6" cellspacing="0" width="100%">
        <tr><td>Employer PF</td><td>{annexure.employer_pf}</td></tr>
        <tr><td>Employer Insurance</td><td>{annexure.employer_insurance}</td></tr>
        <tr><td>Employer Variable</td><td>{annexure.employer_variable_component}</td></tr>
        <tr><td>Employer Gratuity</td><td>{annexure.employer_gratuity}</td></tr>
        <tr><td>Employer ESIC</td><td>{annexure.employer_esic}</td></tr>
        <tr><td><b>Total Employer Cost</b></td><td><b>{annexure.employer_total}</b></td></tr>
    </table>

    <br>

    <h3>Employee Deductions</h3>

    <table border="1" cellpadding="6" cellspacing="0" width="100%">
        <tr><td>Employee PF</td><td>{annexure.employee_pf}</td></tr>
        <tr><td>Professional Tax</td><td>{annexure.employee_pt}</td></tr>
        <tr><td>Employee ESIC</td><td>{annexure.employee_esic}</td></tr>
        <tr><td><b>Total Deductions</b></td><td><b>{annexure.employee_total}</b></td></tr>
    </table>

    <br>

        <p style="margin-top:20px;">
            Kindly review and approve.
        </p>

        <p>
            Regards,<br>
            <strong>{requested_by.name}</strong><br>
            Recruitment Team
        </p>

    </body>
    </html>
    """

    # =========================
    # SEND EMAIL
    # =========================

    send_email(
        subject=f"Salary Annexure Approval - {candidate.candidate_name}",
        text="Please view this email in HTML format.",
        to=approver.email,
        template=html_content
    )

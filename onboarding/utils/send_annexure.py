from .sender import send_email,send_text
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
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:680px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hrmsknowcraftstorage.blob.core.windows.net/media/JMS.png" alt="JMS TechNova" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 24px 0;color:#1f2937;font-size:26px;font-weight:600;">Salary Annexure Approval Required</h2>
                                
                                <p style="margin:0 0 18px 0;">Dear <strong>{approver.name}</strong>,</p>
                                
                                <p style="margin:0 0 24px 0;">
                                    Please review the salary annexure for candidate <strong>{candidate.candidate_name}</strong>.
                                </p>
                                
                                <!-- Candidate & Annexure Details -->
                                <h3 style="margin:28px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Candidate & Annexure Details</h3>
                                <table border="1" cellpadding="10" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="width:38%;font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Candidate Name</td>
                                        <td style="border:1px solid #e2e8f0;">{candidate.candidate_name}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Designation</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.designation}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Effective From</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.effective_from}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Gross Monthly</td>
                                        <td style="border:1px solid #e2e8f0;font-weight:500;">{annexure.gross_monthly}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Net Monthly</td>
                                        <td style="border:1px solid #e2e8f0;font-weight:500;">{annexure.net_monthly}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">CTC Annual</td>
                                        <td style="border:1px solid #e2e8f0;font-weight:500;">{annexure.ctc_annual}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Status</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.status}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Revision Count</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.revision_count}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Prepared By</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.prepared_by}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Reviewed By</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.reviewed_by or "-"}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Created At</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.created_at}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Updated At</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.updated_at}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Notes</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.notes or "-"}</td>
                                    </tr>
                                    <tr>
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Rejection Reason</td>
                                        <td style="border:1px solid #e2e8f0;">{annexure.rejection_reason or "-"}</td>
                                    </tr>
                                </table>
                                
                                <h3 style="margin:32px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Monthly Earnings / Allowances</h3>
                                <table border="1" cellpadding="10" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="font-weight:600;color:#1f2937;border:1px solid #e2e8f0;">Basic + DA</td>
                                        <td style="text-align:right;border:1px solid #e2e8f0;">{annexure.basic_da}</td>
                                    </tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Basket Allowances</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.basket_allowances}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">HRA</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.hra}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Medical Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.medical_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Leave Travel Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.leave_travel_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Telephone / Internet</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.telephone_internet_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Books & Periodicals</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.books_periodicals}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Uniform Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.uniform_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Driver Salary</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.driver_salary}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Car Maintenance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.car_maintenance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Meals Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.meals_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Special Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.special_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Children Education Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.children_education_allowance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Conveyance Allowance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.conveyance_allowance}</td></tr>
                                </table>
                                
                                <h3 style="margin:32px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Employer Contributions</h3>
                                <table border="1" cellpadding="10" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr><td style="border:1px solid #e2e8f0;">Employer PF</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employer_pf}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Employer Insurance</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employer_insurance}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Employer Variable</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employer_variable_component}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Employer Gratuity</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employer_gratuity}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Employer ESIC</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employer_esic}</td></tr>
                                    <tr style="background:#f0fdf4;">
                                        <td style="font-weight:700;color:#166534;border:1px solid #e2e8f0;">Total Employer Cost</td>
                                        <td style="text-align:right;font-weight:700;color:#166534;border:1px solid #e2e8f0;">{annexure.employer_total}</td>
                                    </tr>
                                </table>
                                
                                <h3 style="margin:32px 0 12px 0;color:#1f2937;font-size:18px;font-weight:600;">Employee Deductions</h3>
                                <table border="1" cellpadding="10" cellspacing="0" width="100%" style="border-collapse:collapse;border-color:#e2e8f0;font-size:15px;">
                                    <tr><td style="border:1px solid #e2e8f0;">Employee PF</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employee_pf}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Professional Tax</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employee_pt}</td></tr>
                                    <tr><td style="border:1px solid #e2e8f0;">Employee ESIC</td><td style="text-align:right;border:1px solid #e2e8f0;">{annexure.employee_esic}</td></tr>
                                    <tr style="background:#fef2f2;">
                                        <td style="font-weight:700;color:#991b1b;border:1px solid #e2e8f0;">Total Deductions</td>
                                        <td style="text-align:right;font-weight:700;color:#991b1b;border:1px solid #e2e8f0;">{annexure.employee_total}</td>
                                    </tr>
                                </table>
                                
                                <p style="margin:32px 0 8px 0;font-size:16px;">
                                    Kindly review and approve / reject the annexure at the earliest.
                                </p>
                                
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">{requested_by.name}</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Recruitment Team<br>JMS TechNova Private Limited.</p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 JMS TechNova Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # =========================
    # SEND EMAIL
    # =========================

    is_private = candidate.job.is_private

    if not is_private:
        send_email(
            subject=f"Salary Annexure Approval - {candidate.candidate_name}",
            text="Please view this email in HTML format.",
            to=approver.email,
            template=html_content
        )

        whatsapp_text = f"""
*Salary Annexure Approval Required*

Dear {approver.name},

Please review the salary annexure for the below candidate.

━━━━━━━━━━━━━━━━━━
*Candidate & Annexure Details*
━━━━━━━━━━━━━━━━━━
Candidate Name: {candidate.candidate_name}
Designation: {annexure.designation}
Effective From: {annexure.effective_from}
Gross Monthly: {annexure.gross_monthly}
Net Monthly: {annexure.net_monthly}
CTC Annual: {annexure.ctc_annual}
Status: {annexure.status}
Revision Count: {annexure.revision_count}
Prepared By: {annexure.prepared_by}
Reviewed By: {annexure.reviewed_by or "-"}
Created At: {annexure.created_at}
Updated At: {annexure.updated_at}
Notes: {annexure.notes or "-"}
Rejection Reason: {annexure.rejection_reason or "-"}

━━━━━━━━━━━━━━━━━━
*Monthly Earnings / Allowances*
━━━━━━━━━━━━━━━━━━
Basic + DA: {annexure.basic_da}
Basket Allowances: {annexure.basket_allowances}
HRA: {annexure.hra}
Medical Allowance: {annexure.medical_allowance}
Leave Travel Allowance: {annexure.leave_travel_allowance}
Telephone / Internet: {annexure.telephone_internet_allowance}
Books & Periodicals: {annexure.books_periodicals}
Uniform Allowance: {annexure.uniform_allowance}
Driver Salary: {annexure.driver_salary}
Car Maintenance: {annexure.car_maintenance}
Meals Allowance: {annexure.meals_allowance}
Special Allowance: {annexure.special_allowance}
Children Education Allowance: {annexure.children_education_allowance}
Conveyance Allowance: {annexure.conveyance_allowance}

━━━━━━━━━━━━━━━━━━
*Employer Contributions*
━━━━━━━━━━━━━━━━━━
Employer PF: {annexure.employer_pf}
Employer Insurance: {annexure.employer_insurance}
Employer Variable: {annexure.employer_variable_component}
Employer Gratuity: {annexure.employer_gratuity}
Employer ESIC: {annexure.employer_esic}
Total Employer Cost: {annexure.employer_total}

━━━━━━━━━━━━━━━━━━
*Employee Deductions*
━━━━━━━━━━━━━━━━━━
Employee PF: {annexure.employee_pf}
Professional Tax: {annexure.employee_pt}
Employee ESIC: {annexure.employee_esic}
Total Deductions: {annexure.employee_total}

━━━━━━━━━━━━━━━━━━

Kindly review and approve / reject the annexure at the earliest.

Regards,
{requested_by.name}
Recruitment Team
JMS TechNova Private Limited
"""
        if approver.phone:
            send_text(to=approver.phone,text=whatsapp_text)
    else:
        print(f"Skipping Salary Annexure notification for private job: {candidate.job.id}")


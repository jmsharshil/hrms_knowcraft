from django.conf import settings

FRONTEND_URL = getattr(settings,"FRONTEND_URL")

HTML_TEMPLATES = {

    # -----------------------------------------------------------
    # 0. APPLICATION & DUPLICATE
    # -----------------------------------------------------------
    # "received": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Application Received</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for applying! We have received your application and will review it shortly.</p>
    #     <p>We will keep you updated on the next steps.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    "duplicate_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Application Status</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Our records indicate that you recently applied for a position. Due to our duplicate application policy, we are unable to process this application.</p>
        <p>You may reapply at a later date.</p>
        <br>
        <p>Warm regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited
        </p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 1. SHORTLISTING & INTERVIEW
    # -----------------------------------------------------------
    # "shortlisted": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>You Have Been Shortlisted!</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Congratulations! You have been shortlisted for the next stage of the selection process.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_pending_1": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Interview Round 1 is Scheduled</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your interview has been scheduled. Please check your email/calendar invite for the meeting details.</p>
    #     <p>We wish you the best!</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_done_1": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Thank You for Interviewing</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for attending the interview. Our team is reviewing your performance, and we will update you soon.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_1": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for taking the time to participate in the HR Round of our interview process.</p>
    <p>After careful consideration, we regret to inform you that you have not been selected to proceed further.
    While we were impressed with your background, we will not be moving ahead at this stage.</p>
    <p>We truly appreciate your interest and wish you the very best in your future endeavors.</p>
    <br>
    <p>Warm regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited
    </p>
    </body>
    </html>
    """,
    # "interview_next_2": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>You Have Been Shortlisted For Next Round!</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Congratulations! You have been shortlisted for the next Round.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_pending_2": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Interview Round 2 is Scheduled</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your interview has been scheduled. Please check your email/calendar invite for the meeting details.</p>
    #     <p>We wish you the best!</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_done_2": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Thank You for Interviewing</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for attending the interview. Our team is reviewing your performance, and we will update you soon.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_2": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for taking the time to participate in the <b>Technical Round</b> of our interview process.</p>
    <p>After a thorough evaluation, we regret to inform you that you have not been selected to move forward.
    We sincerely value your effort and encourage you to apply again in the future.</p>
    <p>Wishing you success in your career ahead.</p><br>
    <p>Warm regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    # "interview_next_3": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>You Have Been Shortlisted For Next Round!</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Congratulations! You have been shortlisted for the next Round.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_pending_3": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Interview Round 3 is Scheduled</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your interview has been scheduled. Please check your email/calendar invite for the meeting details.</p>
    #     <p>We wish you the best!</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_done_3": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Thank You for Interviewing</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for attending the interview. Our team is reviewing your performance, and we will update you soon.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_3": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for taking the time to participate in the <b>Case Study Round</b> of our interview process.</p>
    <p>After a thorough evaluation, we regret to inform you that you have not been selected to move forward.
    We sincerely value your effort and encourage you to apply again in the future.</p>
    <p>Wishing you success in your career ahead.</p><br>
    <p>Warm regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    # "interview_next_final": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>You Have Been Shortlisted For Final Round!</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Congratulations! You have been shortlisted for the third round of inerview.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_pending_final": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Interview for round 3 is Scheduled</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your interview has been scheduled. Please check your email/calendar invite for the meeting details.</p>
    #     <p>We wish you the best!</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_done_final": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Thank You for Interviewing</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for attending the interview. Our team is reviewing your performance, and we will update you soon.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_final": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for taking the time to participate in the <b>Final Round</b> of our interview process.</p>
    <p>After a thorough evaluation, we regret to inform you that you have not been selected to move forward.
    We sincerely value your effort and encourage you to apply again in the future.</p>
    <p>Wishing you success in your career ahead.</p><br>
    <p>Warm regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    # -----------------------------------------------------------
    # MANAGEMENT / CLIENT INTERVIEW
    # -----------------------------------------------------------

    # "interview_next_management_client": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>You Have Been Shortlisted for Management / Client Interview</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Congratulations! You have been shortlisted for the Management / Client interview round.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_pending_management_client": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Management / Client Interview Is Scheduled</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your Management / Client interview has been scheduled.</p>
    #     <p>Please check your email or calendar invite for details.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    # "interview_done_management_client": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Thank You for the Interview</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for attending the Management / Client interview.</p>
    #     <p>Our team will review the discussion and update you shortly.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment Team</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_management_client": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for taking the time to participate in the <b>Management/Client Round</b> of our interview process.</p>
    <p>After a thorough evaluation, we regret to inform you that you have not been selected to move forward.
    We sincerely value your effort and encourage you to apply again in the future.</p>
    <p>Wishing you success in your career ahead.</p><br>
    <p>Warm regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 2. SELECTION & APPROVAL
    # -----------------------------------------------------------
    "selected": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>We are pleased to inform you that you have been selected for the position of 
    <b>{{candidate.job.mrf.designation.name}}</b> after successfully completing all interview rounds.</p>
    <p>The team was impressed with your skills and performance.
    We look forward to having you onboard.</p>
    <p>We will reach out shortly with offer details and next steps.</p>
    <p>Congratulations once again!</p>
    <br>
    <p>Warm Regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "approval_pending": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Profile Sent for Approval</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your profile has been forwarded to the hiring manager for final approval.</p>
    #     <p>We will notify you once the approval process is complete.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    "approved": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>We are pleased to inform you that you have been selected for the position of 
    <b>{{candidate.job.mrf.designation.name}}</b> after successfully completing all interview rounds.</p>
    <p>The team was impressed with your skills and performance.
    We look forward to having you onboard.</p>
    <p>We will reach out shortly with offer details and next steps.</p>
    <p>Congratulations once again!</p>
    <br>
    <p>Warm Regards,<br>
    Team-HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    "approval_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Application Update</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>After careful review, the hiring manager has decided not to proceed with your profile.</p>
        <p>We wish you great success in your future endeavors.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 3. OFFER FLOW
    # -----------------------------------------------------------
    # "offer_pending": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Offer Is Being Prepared</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We are currently preparing your offer letter. You will receive it shortly.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "offer_sent": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Your Offer Letter</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Please sign your offer letter using the secure link provided: {{sign_url}}</p>
    #     <p>If you have any questions, feel free to reach out.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "offer_accepted": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Offer Accepted – Welcome!</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We are excited that you have accepted the offer!</p>
    #     <p>Our HR team will contact you soon with the onboarding steps.</p>
    #     <br>
    #     <p>Welcome aboard!<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "offer_rejected": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Regarding Your Offer</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you for your interest. As you have declined the offer, your application is now closed.</p>
    #     <p>We wish you all the success in your future career.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # -----------------------------------------------------------
    # 4. DOCUMENT FLOW
    # -----------------------------------------------------------
    "docs_pending": f"""
    <html>
    <body style='font-family: Arial, sans-serif; color:#333; line-height:1.6;'>
        <p>Hi {{candidate.candidate_name}},</p>
        <p>Greetings of the day!</p>
        <p>
            Congratulations on being selected to work with Knowcraft Analytics! 
            We’re excited about the potential of working together.
        </p>
        <p>
            To proceed further with your candidature, we kindly request you to upload 
            the required documents as mentioned below using the link provided.
        </p>
        <p>
            <b>Upload Link:</b><br>
            <a href="{FRONTEND_URL}/api/application/documents/upload/{{candidate.id}}">
                Upload Documents
            </a>
        </p>
        <br>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width:100%;">
            <tr style="background-color:#f2f2f2;">
                <th>S. No</th>
                <th>Documents Required</th>
            </tr>
            <tr>
                <td>1</td>
                <td>Certificates and Marksheets till Highest Qualification (Mandatory)</td>
            </tr>
            <tr>
                <td>2</td>
                <td>
                    Last Organization Documents (if applicable):
                    <ul>
                        <li>Offer Letter / Appointment Letter</li>
                        <li>Experience & Relieving Letter</li>
                        <li>Increment Letter</li>
                        <li>Last 3 Months Salary Slips</li>
                    </ul>
                </td>
            </tr>
            <tr>
                <td>3</td>
                <td>Aadhar Card (Mandatory)</td>
            </tr>
            <tr>
                <td>4</td>
                <td>PAN Card (Mandatory)</td>
            </tr>
            <tr>
                <td>5</td>
                <td>Passport Sized Photograph (Mandatory)</td>
            </tr>
        </table>
        <br>
        <p>Please upload your onboarding documents at the earliest so we can proceed further.</p>
        <p>Let us know in case of any queries.</p>
        <br>
        <p>
            Regards,<br>
            Team – HR <br>
            Knowcraft Analytics Private Limited
        </p>

    </body>
    </html>
    """,

    # "docs_received": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Documents Received</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Thank you! We have received your onboarding documents and will review them shortly.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # -----------------------------------------------------------
    # 5. JOINING FLOW
    # -----------------------------------------------------------
    "joining_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Joining Process Initiated</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your joining process has begun. HR will share additional details soon.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    #     "joining_poned": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Joining Date Postponed</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>You have missed your joining date of {{candidate.joining_date}}.</p>
    #     <p>Please join as soon as possible.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "joined": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Welcome to the Team!</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We are thrilled to welcome you aboard!</p>
    #     <p>Your joining formalities are now complete. Please check your email for Day 1 details.</p>
    #     <br>
    #     <p>Warm regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # -----------------------------------------------------------
    # 6. GENERIC FINAL REJECTION
    # -----------------------------------------------------------
    "rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Application Update</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We regret to inform you that your application has been closed.</p>
        <p>We wish you success in your future opportunities.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    # -----------------------------------------------------------
    # NEW: SALARY DOCUMENT FLOW
    # -----------------------------------------------------------

    # "salary_docs_pending": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Upload Salary Documents</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Please upload your latest salary slip and bank statement using this link {{FRONTEND_URL}}/api/application/documents/upload/salary-bank/{{candidate.id}}</p>
    #     <p>This is required to proceed with your offer process.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "salary_docs_uploaded": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Documents Received</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We have received your salary slip and bank statement.</p>
    #     <p>Our HR team will review them shortly.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "hr_review_docs": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Document Review in Progress</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Our HR team is reviewing your uploaded salary documents.</p>
    #     <p>You will be notified once the review is complete.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    #     "hr_review_ok": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Documents Verified</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your salary slip and bank statement have been successfully verified.</p>
    #     <p>We are now preparing your salary annexure.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    #     "hr_review_rejected": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Document Verification Failed</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your uploaded documents could not be verified due to missing or unclear information.</p>
    #     <p>Please re-upload the required documents to continue the process.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "salary_annexure_prep": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Annexure Preparation</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We are preparing your salary annexure based on your verified documents.</p>
    #     <p>You will be notified once it is ready for approval.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    #     "salary_annexure_sent": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Annexure Sent for Approval</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your salary annexure has been prepared and sent to the HR Head for approval.</p>
    #     <p>We will notify you once it is approved.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    # "rejected_annexure": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Annexure Rejected</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your salary annexure has been reviewed by the HR Head and requires corrections.</p>
    #     <p>Our HR team will revise the annexure and share it with you again for approval.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    # "approved_annexure": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Salary Annexure Approved</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your salary annexure has been approved by HR Head.</p>
    #     <p>We will now prepare your offer letter.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,


    # # -----------------------------------------------------------
    # # NEW: RESIGNATION FLOW
    # # -----------------------------------------------------------

    # "resignation_pending": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Upload Your Resignation Letter</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Please upload your resignation letter using the provided link under 48 hours.Link <a href='https://9bd6882f3e08.ngrok-free.app/api/candidates/{{candidate.id}}/documents/upload/'>https://9bd6882f3e08.ngrok-free.app/api/candidates/{{candidate.id}}/documents/upload/</a></p>
    #     <p>This is required to proceed with the onboarding workflow.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "resignation_uploaded": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Resignation Letter Received</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We have received your resignation letter.</p>
    #     <p>HR will verify and confirm shortly.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    #     "resignation_review": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Resignation Letter Under Review</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your resignation letter has been received and is currently being reviewed by HR.</p>
    #     <p>You will be notified once verification is completed.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "resignation_approved": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Resignation Letter Approved</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your resignation letter has been approved.</p>
    #     <p>Please upload your joining documents so we can proceed further.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    # "resignation_rejected": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Resignation Letter Rejected</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>Your resignation letter was unclear or invalid.</p>
    #     <p>Please re-upload the correct document to proceed.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,


    # -----------------------------------------------------------
    # NEW: DOCUMENT VERIFICATION FLOW
    # -----------------------------------------------------------

    # "docs_uploaded": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Documents Received</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We have received your documents.</p>
    #     <p>HR will review and verify them shortly.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,
    # "review_docs": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Document Review In Progress</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>We have received your submitted documents and our HR team has started the verification process.</p>
    #     <p>You will be notified once the review is completed or if any clarification is required.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

    "docs_incomplete": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for submitting your documents as part of the recruitment process.</p>
    <p>Upon review, we noticed that some documents are incomplete or unclear.
    Kindly re-upload the documents</p>
    <p>Please ensure files are properly scanned and all information is visible.</p>
    <p>If you need any assistance, feel free to reach out.</p>
    <br>
    <p>Warm regards,<br>
    Team – HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
        "docs_unclear": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{candidate.candidate_name}},</p>
    <p>Greetings from Knowcraft Analytics!</p>
    <p>Thank you for submitting your documents as part of the recruitment process.</p>
    <p>Upon review, we noticed that some documents are incomplete or unclear.
    Kindly re-upload the documents</p>
    <p>Please ensure files are properly scanned and all information is visible.</p>
    <p>If you need any assistance, feel free to reach out.</p>
    <br>
    <p>Warm regards,<br>
    Team – HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "docs_approved": f"""
    # <html>
    # <body style='font-family: Arial; color:#333;'>
    #     <h2>Documents Approved</h2>
    #     <p>Dear {{candidate.candidate_name}},</p>
    #     <p>All your documents have been successfully verified.</p>
    #     <p>We will now proceed with the joining formalities.</p>
    #     <br>
    #     <p>Regards,<br>HR Team</p>
    # </body>
    # </html>
    # """,

}

NOTIFY_INTERNAL_HTML_TEMPLATES = {

    # "interview_pending_1": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Interview Scheduled (HR Round)</h2>
    #     <p>Dear,</p>
    #     <p>The first round of interview slot of candidate <strong>{{candidate.candidate_name}}</strong> is scheduled.</p>
    #     <p>Fill the interview feedback on this link: {{feedback_link}}</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    # "interview_pending_2": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Interview Scheduled (Technical Round)</h2>
    #     <p>Dear,</p>
    #     <p>The second round of interview slot of candidate <strong>{{candidate.candidate_name}}</strong> is scheduled.</p>
    #     <p>Fill the interview feedback on this link: {{feedback_link}}</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,
    # "interview_pending_3": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Interview Scheduled (Case Study Round)</h2>
    #     <p>Dear,</p>
    #     <p>The second round of interview slot of candidate <strong>{{candidate.candidate_name}}</strong> is scheduled.</p>
    #     <p>Fill the interview feedback on this link: {{feedback_link}}</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,
    # "interview_pending_final": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Interview Scheduled (Final Round)</h2>
    #     <p>Dear,</p>
    #     <p>The final round of interview slot of candidate <strong>{{candidate.candidate_name}}</strong> is scheduled.</p>
    #     <p>Fill the interview feedback on this link: {{feedback_link}}</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>

    # </body>
    # </html>
    # """,
    # "interview_pending_management_client": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Interview Scheduled (Management / Client Round)</h2>
    #     <p>Dear Team,</p>
    #     <p>The Management / Client interview for candidate <strong>{{candidate.candidate_name}}</strong> has been scheduled.</p>
    #     <p>Please submit interview feedback using this link: {{feedback_link}}</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,
    # "interview_done_management_client": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Management / Client Interview Completed</h2>
    #     <p>Dear Team,</p>
    #     <p>The Management / Client interview for <strong>{{candidate.candidate_name}}</strong> has been completed.</p>
    #     <p>Please review feedback and proceed with the next decision.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,
    # "interview_done_1": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>HR Interview Completed</h2>
    #     <p>Dear Team,</p>
    #     <p>The HR interview for <strong>{{candidate.candidate_name}}</strong> has been completed.</p>
    #     <p>Please submit feedback and proceed with the next step.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_1": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Rejected (HR Interview)</h2>
        <p>Dear Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> was rejected after the HR interview.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "interview_done_2": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Technical Interview Completed</h2>
    #     <p>Dear Team,</p>
    #     <p>The technical interview for <strong>{{candidate.candidate_name}}</strong> has been completed.</p>
    #     <p>Please review feedback.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_2": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Rejected (Technical Interview)</h2>
        <p>Dear Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> was rejected after the technical interview.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "interview_done_3": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Case Study Interview Completed</h2>
    #     <p>Dear Team,</p>
    #     <p>The case study interview for <strong>{{candidate.candidate_name}}</strong> has been completed.</p>
    #     <p>Please evaluate feedback.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_3": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Rejected (Case Study Interview)</h2>
        <p>Dear Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> was rejected after the case study interview.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "interview_done_final": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Final Interview Completed</h2>
    #     <p>Dear Team,</p>
    #     <p>The final interview for <strong>{{candidate.candidate_name}}</strong> has been completed.</p>
    #     <p>Please proceed with selection decision.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    "interview_rejected_final": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Rejected (Final Interview)</h2>
        <p>Dear Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> was rejected after the final interview.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "interview_rejected_management_client": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Rejected (Management / Client Interview)</h2>
        <p>Dear Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> was rejected after the Management / Client interview.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "shortlisted": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Shortlisted</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has been shortlisted.</p>
        <p>Please proceed with the next steps in the hiring process.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "interview_next_2": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Shortlisted</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has passed HR Round.</p>
        <p>Please proceed with the next steps in the hiring process.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "interview_next_3": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Shortlisted</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has passed Technical Round.</p>
        <p>Please proceed with the next steps in the hiring process.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "interview_next_final": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Shortlisted</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has passed Case Study Round.</p>
        <p>Please proceed with the next steps in the hiring process.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "interview_next_management_client": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Shortlisted</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has passed Final Round.</p>
        <p>Please proceed with the next steps in the hiring process.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    "approval_pending": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Approval Required</h2>
        <p>Dear Manager,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> is pending your approval.</p>
        <p>Please review the profile and provide your decision.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    "approved": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Approved</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has been approved.</p>
        <p>Please continue with salary and offer formalities.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    "approval_rejected": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Approval Rejected</h2>
        <p>Dear HR Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> was rejected during the approval stage.</p>
        <p>Please take necessary action.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "salary_docs_uploaded": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Salary Documents Uploaded</h2>
    #     <p>Dear HR Team,</p>
    #     <p>The candidate <strong>{{candidate.candidate_name}}</strong> has uploaded salary documents.</p>
    #     <p>Please review them at your convenience.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    "offer_pending": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Offer Letter Pending</h2>
        <p>Dear HR Team,</p>
        <p>The offer letter for <strong>{{candidate.candidate_name}}</strong> is pending.</p>
        <p>Please prepare and send the offer.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    "joined": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Joined Successfully</h2>
        <p>Dear Team,</p>
        <p>We are pleased to inform you that <strong>{{candidate.candidate_name}}</strong> has joined the organization.</p>
        <p>Welcome aboard!</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    "rejected": f"""
    <html>
    <body style="font-family: Arial; color:#333;">
        <h2>Candidate Rejected</h2>
        <p>Dear Team,</p>
        <p>The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected.</p>
        <p>This concludes the hiring process for this profile.</p>
        <br>
        <p>Warm Regards,<br>
        Team-HR <br>
        Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    # "resignation_uploaded": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Resignation Letter Uploaded</h2>
    #     <p>Dear HR Team,</p>
    #     <p><strong>{{candidate.candidate_name}}</strong> has uploaded resignation letter.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    # "resignation_approved": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Resignation Approved</h2>
    #     <p>Dear HR Team,</p>
    #     <p>Resignation letter of <strong>{{candidate.candidate_name}}</strong> has been approved.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    "docs_uploaded": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Hi {{reciever_name}},</p>
    <p>This is to inform you that the candidate <b>{{candidate.candidate_name}}</b> has successfully uploaded all required documents.</p>
    <p>You may review documents and proceed with the next steps of evaluation and onboarding.</p>
    <p>Please let me know if any additional information is needed.</p>
    <br>
    <p>Warm regards,<br>
    Team - HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,

    "offer_accepted": f"""
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
    <p>Dear {{reciever_name}},</p>
    <p>This is to inform you that <b>{{candidate.candidate_name}}</b> has formally accepted the offer 
    for the position of <b>{{candidate.job.mrf.designation.name}}</b>.</p>
    <p>Please proceed with the next onboarding steps.</p>
    <p>Kindly let me know if any additional details are required.</p>
    <br>
    <p>Thank you.<br><br>
    Warm regards,<br>
    Team - HR <br>
    Knowcraft Analytics Private Limited</p>
    </body>
    </html>
    """,
    # "docs_approved": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Joining Documents Approved</h2>
    #     <p>Dear Team,</p>
    #     <p>All joining documents for <strong>{{candidate.candidate_name}}</strong> are approved.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,
    # "salary_docs_pending": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Salary Documents Requested</h2>
    #     <p>Dear HR Team,</p>
    #     <p>Salary documents have been requested from <strong>{{candidate.candidate_name}}</strong>.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    # "hr_review_docs": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Salary Documents Under Review</h2>
    #     <p>Dear HR Team,</p>
    #     <p>Salary documents of <strong>{{candidate.candidate_name}}</strong> are under HR review.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

    # "hr_review_ok": f"""
    # <html>
    # <body style="font-family: Arial; color:#333;">
    #     <h2>Salary Documents Verified</h2>
    #     <p>Dear HR Team,</p>
    #     <p>Salary documents of <strong>{{candidate.candidate_name}}</strong> have been verified.</p>
    #     <br>
    #     <p>Regards,<br>Recruitment System</p>
    # </body>
    # </html>
    # """,

#     # "hr_review_rejected": f"""
#     # <html>
#     # <body style="font-family: Arial; color:#333;">
#     #     <h2>Salary Documents Rejected</h2>
#     #     <p>Dear HR Team,</p>
#     #     <p>Salary documents of <strong>{{candidate.candidate_name}}</strong> were rejected.</p>
#     #     <p>Candidate needs to re-upload documents.</p>
#     #     <br>
#     #     <p>Regards,<br>Recruitment System</p>
#     # </body>
#     # </html>
#     # """,

#     # "salary_annexure_prep": f"""
#     # <html>
#     # <body style="font-family: Arial; color:#333;">
#     #     <h2>Salary Annexure Under Preparation</h2>
#     #     <p>Dear HR Team,</p>
#     #     <p>Salary annexure is being prepared for <strong>{{candidate.candidate_name}}</strong>.</p>
#     #     <br>
#     #     <p>Regards,<br>Recruitment System</p>
#     # </body>
#     # </html>
#     # """,

#     # "salary_annexure_sent": f"""
#     # <html>
#     # <body style="font-family: Arial; color:#333;">
#     #     <h2>Salary Annexure Sent for Approval</h2>
#     #     <p>Dear HR Head,</p>
#     #     <p>Salary annexure for <strong>{{candidate.candidate_name}}</strong> has been sent for approval.</p>
#     #     <br>
#     #     <p>Regards,<br>Recruitment System</p>
#     # </body>
#     # </html>
#     # """,

#     # "approved_annexure": f"""
#     # <html>
#     # <body style="font-family: Arial; color:#333;">
#     #     <h2>Salary Annexure Approved</h2>
#     #     <p>Dear HR Team,</p>
#     #     <p>Salary annexure for <strong>{{candidate.candidate_name}}</strong> has been approved.</p>
#     #     <br>
#     #     <p>Regards,<br>Recruitment System</p>
#     # </body>
#     # </html>
#     # """,

#     # "rejected_annexure": f"""
#     # <html>
#     # <body style="font-family: Arial; color:#333;">
#     #     <h2>Salary Annexure Rejected</h2>
#     #     <p>Dear HR Team,</p>
#     #     <p>Salary annexure for <strong>{{candidate.candidate_name}}</strong> was rejected.</p>
#     #     <br>
#     #     <p>Regards,<br>Recruitment System</p>
#     # </body>
#     # </html>
# """,

}

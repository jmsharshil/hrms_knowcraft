HTML_TEMPLATES = {

    # -----------------------------------------------------------
    # 0. APPLICATION & DUPLICATE
    # -----------------------------------------------------------
    "received": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Application Received</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Thank you for applying! We have received your application and will review it shortly.</p>
        <p>We will keep you updated on the next steps.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "duplicate_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Application Status</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Our records indicate that you recently applied for a position. Due to our duplicate application policy, we are unable to process this application.</p>
        <p>You may reapply at a later date.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 1. SHORTLISTING & INTERVIEW
    # -----------------------------------------------------------
    "shortlisted": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>You Have Been Shortlisted!</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Congratulations! You have been shortlisted for the next stage of the selection process.</p>
        <p>Our team will contact you soon to schedule your interview.</p>
        <br>
        <p>Regards,<br>Recruitment Team</p>
    </body>
    </html>
    """,

    "interview_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Your Interview is Scheduled</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your interview has been scheduled. Please check your email/calendar invite for the meeting details.</p>
        <p>We wish you the best!</p>
        <br>
        <p>Regards,<br>Recruitment Team</p>
    </body>
    </html>
    """,

    "interview_done": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Thank You for Interviewing</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Thank you for attending the interview. Our team is reviewing your performance, and we will update you soon.</p>
        <br>
        <p>Regards,<br>Recruitment Team</p>
    </body>
    </html>
    """,

    "interview_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Update on Your Interview</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Thank you for interviewing with us. After reviewing all candidates, we regret to inform you that we will not be proceeding forward.</p>
        <p>We encourage you to apply for future opportunities.</p>
        <br>
        <p>Regards,<br>Recruitment Team</p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 2. SELECTION & APPROVAL
    # -----------------------------------------------------------
    "selected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Congratulations – You’ve Been Selected!</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We are pleased to inform you that the interview panel has selected you for the next stage.</p>
        <p>Your profile will now be sent for approval.</p>
        <br>
        <p>Regards,<br>Recruitment Team</p>
    </body>
    </html>
    """,

    "approval_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Profile Sent for Approval</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your profile has been forwarded to the hiring manager for final approval.</p>
        <p>We will notify you once the approval process is complete.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "approved": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Profile Approved</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Good news! Your profile has been approved by the hiring manager.</p>
        <p>We will now begin preparing your offer letter.</p>
        <br>
        <p>Regards,<br>HR Team</p>
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
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 3. OFFER FLOW
    # -----------------------------------------------------------
    "offer_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Your Offer Is Being Prepared</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We are currently preparing your offer letter. You will receive it shortly.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "offer_sent": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Your Offer Letter</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Please sign your offer letter using the secure link provided: {{sign_url}}</p>
        <p>If you have any questions, feel free to reach out.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "offer_accepted": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Offer Accepted – Welcome!</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We are excited that you have accepted the offer!</p>
        <p>Our HR team will contact you soon with the onboarding steps.</p>
        <br>
        <p>Welcome aboard!<br>HR Team</p>
    </body>
    </html>
    """,

    "offer_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Regarding Your Offer</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Thank you for your interest. As you have declined the offer, your application is now closed.</p>
        <p>We wish you all the success in your future career.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    # -----------------------------------------------------------
    # 4. DOCUMENT FLOW
    # -----------------------------------------------------------
    "docs_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Document Submission Required</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Please upload your documents through this link https://9bd6882f3e08.ngrok-free.app/api/candidates/{{candidate.id}}/documents/upload/</p>
        <p>Please upload your onboarding documents at the earliest so we can proceed.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "docs_received": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Documents Received</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Thank you! We have received your onboarding documents and will review them shortly.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

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
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
        "joining_poned": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Joining Date Postponed</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>You have missed your joining date of {{candidate.joining_date}}.</p>
        <p>Please join as soon as possible.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "joined": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Welcome to the Team!</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We are thrilled to welcome you aboard!</p>
        <p>Your joining formalities are now complete. Please check your email for Day 1 details.</p>
        <br>
        <p>Warm regards,<br>HR Team</p>
    </body>
    </html>
    """,

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
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
    # -----------------------------------------------------------
    # NEW: SALARY DOCUMENT FLOW
    # -----------------------------------------------------------

    "salary_docs_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Upload Salary Documents</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Please upload your latest salary slip and bank statement using this link https://9bd6882f3e08.ngrok-free.app/api/candidates/{{candidate.id}}/documents/upload/.</p>
        <p>This is required to proceed with your offer process.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "salary_docs_uploaded": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Documents Received</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We have received your salary slip and bank statement.</p>
        <p>Our HR team will review them shortly.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "hr_review_docs": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Document Review in Progress</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Our HR team is reviewing your uploaded salary documents.</p>
        <p>You will be notified once the review is complete.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
        "hr_review_ok": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Documents Verified</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your salary slip and bank statement have been successfully verified.</p>
        <p>We are now preparing your salary annexure.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
        "hr_review_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Document Verification Failed</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your uploaded documents could not be verified due to missing or unclear information.</p>
        <p>Please re-upload the required documents to continue the process.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "salary_annexure_prep": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Annexure Preparation</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We are preparing your salary annexure based on your verified documents.</p>
        <p>You will be notified once it is ready for approval.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
        "salary_annexure_sent": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Annexure Sent for Approval</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your salary annexure has been prepared and sent to the HR Head for approval.</p>
        <p>We will notify you once it is approved.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
    "rejected_annexure": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Annexure Rejected</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your salary annexure has been reviewed by the HR Head and requires corrections.</p>
        <p>Our HR team will revise the annexure and share it with you again for approval.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
    "approved_annexure": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Salary Annexure Approved</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your salary annexure has been approved by HR Head.</p>
        <p>We will now prepare your offer letter.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,


    # -----------------------------------------------------------
    # NEW: RESIGNATION FLOW
    # -----------------------------------------------------------

    "resignation_pending": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Upload Your Resignation Letter</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Please upload your resignation letter using the provided link under 48 hours.Link <a href='https://9bd6882f3e08.ngrok-free.app/api/candidates/{{candidate.id}}/documents/upload/'>https://9bd6882f3e08.ngrok-free.app/api/candidates/{{candidate.id}}/documents/upload/</a></p>
        <p>This is required to proceed with the onboarding workflow.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "resignation_uploaded": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Resignation Letter Received</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We have received your resignation letter.</p>
        <p>HR will verify and confirm shortly.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
        "resignation_review": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Resignation Letter Under Review</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your resignation letter has been received and is currently being reviewed by HR.</p>
        <p>You will be notified once verification is completed.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "resignation_approved": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Resignation Letter Approved</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your resignation letter has been approved.</p>
        <p>Please upload your joining documents so we can proceed further.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "resignation_rejected": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Resignation Letter Rejected</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Your resignation letter was unclear or invalid.</p>
        <p>Please re-upload the correct document to proceed.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,


    # -----------------------------------------------------------
    # NEW: DOCUMENT VERIFICATION FLOW
    # -----------------------------------------------------------

    "docs_uploaded": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Documents Received</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We have received your documents.</p>
        <p>HR will review and verify them shortly.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
    "review_docs": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Document Review In Progress</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>We have received your submitted documents and our HR team has started the verification process.</p>
        <p>You will be notified once the review is completed or if any clarification is required.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "docs_incomplete": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Document Verification Result</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Some of your documents are incomplete or unclear.</p>
        <p>Please re-upload them using the same link provided earlier.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,
        "docs_unclear": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Documents Need Clarification</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>Some of your submitted documents are unclear or unreadable.</p>
        <p>Please re-upload clearer copies using the same link provided earlier.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

    "docs_approved": f"""
    <html>
    <body style='font-family: Arial; color:#333;'>
        <h2>Documents Approved</h2>
        <p>Dear {{candidate.candidate_name}},</p>
        <p>All your documents have been successfully verified.</p>
        <p>We will now proceed with the joining formalities.</p>
        <br>
        <p>Regards,<br>HR Team</p>
    </body>
    </html>
    """,

}

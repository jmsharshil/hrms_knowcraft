from django.conf import settings

FRONTEND_URL = getattr(settings,"FRONTEND_URL")

HTML_TEMPLATES = {

    "duplicate_rejected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Application Status Update</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Thank you for your interest in opportunities with Knowcraft Analytics.</p>
                                <p style="margin:0 0 16px 0;">Our records indicate that a recent application has already been received from you. As per our duplicate application policy, we are unable to process this submission further at this time.</p>
                                <p style="margin:0 0 16px 0;">You are welcome to apply again in the future after a reasonable period.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_1": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for taking the time to participate in the HR round of our interview process.</p>
                                <p style="margin:0 0 16px 0;">After careful consideration, we regret to inform you that we will not be proceeding with your application further at this stage. While we were impressed with your profile, we had to make a difficult decision based on current requirements.</p>
                                <p style="margin:0 0 16px 0;">We sincerely appreciate your interest in joining our organization and wish you every success in your future endeavors.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_2": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for participating in the <b>Technical Round</b> of our interview process.</p>
                                <p style="margin:0 0 16px 0;">Following a thorough evaluation, we regret to inform you that we will not be moving forward with your application. We truly value the time and effort you invested in the process.</p>
                                <p style="margin:0 0 16px 0;">We encourage you to explore future opportunities with us and wish you continued success in your career.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_3": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for participating in the <b>Case Study Round</b> of our interview process.</p>
                                <p style="margin:0 0 16px 0;">After careful consideration, we regret to inform you that we will not be proceeding further with your application. We sincerely appreciate your effort and interest in our organization.</p>
                                <p style="margin:0 0 16px 0;">We wish you the very best for your professional journey ahead.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_final": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for taking the time to participate in the <b>Final Round</b> of our selection process.</p>
                                <p style="margin:0 0 16px 0;">After comprehensive evaluation, we regret to inform you that we will not be moving forward with your application. This was a competitive process, and we appreciate your interest and engagement throughout.</p>
                                <p style="margin:0 0 16px 0;">We wish you success in all your future endeavors.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_management_client": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for participating in the <b>Management / Client Round</b> of our interview process.</p>
                                <p style="margin:0 0 16px 0;">Following detailed discussions and evaluation, we regret to inform you that we will not be progressing further with your application. We greatly appreciate the time and effort you invested in meeting with our team.</p>
                                <p style="margin:0 0 16px 0;">We encourage you to stay connected for future opportunities and wish you continued success.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"selected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">We are pleased to inform you that you have been selected for the position of <b>{{candidate.job.mrf.designation.name}}</b> after successfully completing all interview rounds.</p>
                                <p style="margin:0 0 16px 0;">The team was impressed with your skills and performance, and we look forward to having you onboard.</p>
                                <p style="margin:0 0 16px 0;">Our HR team will reach out shortly with the offer details and next steps.</p>
                                <p style="margin:0 0 16px 0;color:#10b981;font-weight:600;">Congratulations once again, and welcome to Knowcraft Analytics!</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"approved": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">We are pleased to inform you that you have been selected for the position of <b>{{candidate.job.mrf.designation.name}}</b> after successfully completing all interview rounds.</p>
                                <p style="margin:0 0 16px 0;">The team was impressed with your skills and performance, and we look forward to having you onboard.</p>
                                <p style="margin:0 0 16px 0;">Our HR team will connect with you shortly regarding the offer details and further formalities.</p>
                                <p style="margin:0 0 16px 0;color:#10b981;font-weight:600;">Congratulations and welcome aboard!</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"approval_rejected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Application Update</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Thank you for your interest in opportunities with Knowcraft Analytics.</p>
                                <p style="margin:0 0 16px 0;">After careful review, the hiring team has decided not to proceed with your profile at this stage.</p>
                                <p style="margin:0 0 16px 0;">We appreciate the time and effort you invested during the process and wish you continued success in your career.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"docs_pending": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 22px 0;">Congratulations on being selected to join our organization. We are excited about the opportunity to work together.</p>
                                <p style="margin:0 0 20px 0;">To proceed further with your onboarding process, we kindly request you to upload the required documents using the link below.</p>
                                
                                <!-- Button -->
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/api/application/documents/upload/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Upload Documents Now</a>
                                </p>
                                
                                <!-- Styled Table -->
                                <table border="1" cellpadding="12" cellspacing="0" style="border-collapse:collapse;width:100%;margin:20px 0;border-color:#e2e8f0;">
                                    <tr style="background-color:#f8fafc;">
                                        <th style="text-align:left;padding:14px;border:1px solid #e2e8f0;color:#1e2937;">S. No</th>
                                        <th style="text-align:left;padding:14px;border:1px solid #e2e8f0;color:#1e2937;">Documents Required</th>
                                    </tr>
                                    <tr>
                                        <td style="padding:14px;border:1px solid #e2e8f0;vertical-align:top;">1</td>
                                        <td style="padding:14px;border:1px solid #e2e8f0;">Certificates and Marksheets till Highest Qualification <span style="color:#ef4444;">(Mandatory)</span></td>
                                    </tr>
                                    <tr>
                                        <td style="padding:14px;border:1px solid #e2e8f0;vertical-align:top;">2</td>
                                        <td style="padding:14px;border:1px solid #e2e8f0;">
                                            Last Organization Documents (if applicable):<br>
                                            <span style="font-size:14px;color:#475569;">• Offer Letter / Appointment Letter<br>• Experience &amp; Relieving Letter<br>• Increment Letter<br>• Last 3 Months Salary Slips</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding:14px;border:1px solid #e2e8f0;vertical-align:top;">3</td>
                                        <td style="padding:14px;border:1px solid #e2e8f0;">Aadhar Card <span style="color:#ef4444;">(Mandatory)</span></td>
                                    </tr>
                                    <tr>
                                        <td style="padding:14px;border:1px solid #e2e8f0;vertical-align:top;">4</td>
                                        <td style="padding:14px;border:1px solid #e2e8f0;">PAN Card <span style="color:#ef4444;">(Mandatory)</span></td>
                                    </tr>
                                    <tr>
                                        <td style="padding:14px;border:1px solid #e2e8f0;vertical-align:top;">5</td>
                                        <td style="padding:14px;border:1px solid #e2e8f0;">Passport Sized Photograph <span style="color:#ef4444;">(Mandatory)</span></td>
                                    </tr>
                                </table>
                                
                                <p style="margin:25px 0 10px 0;">Please upload the documents at your earliest convenience so we can proceed with the next steps.</p>
                                <p style="margin:0 0 16px 0;">Feel free to reach out in case of any questions or assistance.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"joining_pending": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Joining Process Initiated</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">We are pleased to inform you that your joining process has been initiated.</p>
                                <p style="margin:0 0 16px 0;">Our HR team will be sharing further details and next steps with you shortly.</p>
                                <p style="margin:0 0 16px 0;">We look forward to welcoming you to Knowcraft Analytics.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"rejected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Application Update</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Thank you for your interest in opportunities with Knowcraft Analytics.</p>
                                <p style="margin:0 0 16px 0;">We regret to inform you that your application has been closed at this stage.</p>
                                <p style="margin:0 0 16px 0;">We appreciate the time you invested and wish you success in your future opportunities.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"docs_incomplete": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for submitting your documents as part of the recruitment process.</p>
                                <p style="margin:0 0 16px 0;">Upon review, we noticed that some of the submitted documents are incomplete or unclear. We kindly request you to re-upload the required documents.</p>
                                
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/api/application/documents/upload/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Re-upload Documents</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">Please ensure that the files are properly scanned and all information is clearly visible.</p>
                                <p style="margin:0 0 16px 0;">If you need any assistance, please feel free to reach out to us.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"docs_unclear": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Greetings from Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Thank you for submitting your documents as part of the recruitment process.</p>
                                <p style="margin:0 0 16px 0;">Upon review, we noticed that some documents are incomplete or unclear. We kindly request you to re-upload the required documents.</p>
                                
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/api/application/documents/upload/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Re-upload Documents</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">Please ensure the files are properly scanned and all information is clearly visible.</p>
                                <p style="margin:0 0 16px 0;">If you need any assistance, please feel free to reach out to us.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",
"candidate_feedback": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">We'd Love to Hear From You!</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Thank you for your interest in Knowcraft Analytics and for the time you've invested in our recruitment process.</p>
                                <p style="margin:0 0 16px 0;">We are constantly striving to improve our candidate experience, and your feedback is incredibly valuable to us. We would appreciate it if you could take a few moments to share your thoughts on your journey with us so far.</p>
                                
                                <p style="margin:30px 0 35px 0;text-align:center;">
                                    <a href="{{feedback_link}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Share Your Feedback</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">Your responses will be kept confidential and used solely to enhance our hiring process.</p>
                                <p style="margin:0 0 16px 0;">Thank you for your time and we wish you the very best.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""
}

NOTIFY_INTERNAL_HTML_TEMPLATES = {

    "interview_rejected_1": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Rejected — HR Interview</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected following the HR interview round.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_2": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Rejected — Technical Interview</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected following the technical interview round.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_3": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Rejected — Case Study Interview</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected following the case study interview round.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_final": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Rejected — Final Interview</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected following the final interview round.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_rejected_management_client": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Rejected — Management / Client Interview</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected following the Management / Client interview round.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"shortlisted": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Shortlisted</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been shortlisted.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with the next steps in the hiring process.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_next_2": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Progress Update</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has successfully cleared the HR round.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with the next stage of the hiring process.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_next_3": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Progress Update</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has successfully cleared the Technical round.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with the next stage.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_next_final": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Progress Update</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has successfully cleared the Case Study round.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with the next stage.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"interview_next_management_client": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Progress Update</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has successfully cleared the Final round.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with the next stage.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"approval_pending": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Approval Required</h2>
                                <p style="margin:0 0 16px 0;">Dear Manager,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> is pending your approval.</p>
                                <p style="margin:0 0 16px 0;">Kindly review the profile and provide your decision to proceed further.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"approved": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Approved</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been approved.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with salary discussion and offer letter formalities.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"approval_rejected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Approval Rejected</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> was not approved during the approval stage.</p>
                                <p style="margin:0 0 16px 0;">Please take the necessary action to close the process.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"offer_pending": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Offer Letter Pending</h2>
                                <p style="margin:0 0 16px 0;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">The offer letter for <strong>{{candidate.candidate_name}}</strong> is currently pending.</p>
                                <p style="margin:0 0 16px 0;">Please prepare and share the offer at the earliest.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"joined": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Joined Successfully</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">We are pleased to inform you that <strong>{{candidate.candidate_name}}</strong> has successfully joined the organization.</p>
                                <p style="margin:0 0 16px 0;">We wish them a successful journey with Knowcraft Analytics.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"rejected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Candidate Rejected</h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">The candidate <strong>{{candidate.candidate_name}}</strong> has been rejected.</p>
                                <p style="margin:0 0 16px 0;">This concludes the hiring process for this profile.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"docs_uploaded": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;">This is to inform you that the candidate <strong>{{candidate.candidate_name}}</strong> has successfully uploaded all the required documents.</p>
                                <p style="margin:0 0 16px 0;">You may review the documents and proceed with the next steps of evaluation and onboarding.</p>
                                <p style="margin:0 0 16px 0;">Please let us know if any additional information is required.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",

"offer_accepted": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;">This is to inform you that <strong>{{candidate.candidate_name}}</strong> has formally accepted the offer for the position of <strong>{{candidate.job.mrf.designation.name}}</strong>.</p>
                                <p style="margin:0 0 16px 0;">Please proceed with the next onboarding steps.</p>
                                <p style="margin:0 0 16px 0;">Kindly let us know if any additional details are required.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",
"offer_rejected": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr>
                            <td style="padding:0 40px;">
                                <hr style="border:0;border-top:1px solid #f0f2f7;margin:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    Offer Declined by Candidate
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;">
                                    This is to inform you that <strong>{{candidate.candidate_name}}</strong> has declined the offer 
                                    for the position of <strong>{{candidate.job.mrf.designation.name}}</strong>.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Please proceed with the necessary updates and further hiring actions as required.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Kindly let us know if any additional information is needed.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",
"joining_poned": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Separator -->
                        <tr>
                            <td style="padding:0 40px;">
                                <hr style="border:0;border-top:1px solid #f0f2f7;margin:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    Joining Postponed
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;">
                                    This is to inform you that <strong>{{candidate.candidate_name}}</strong> has not joined on the scheduled joining date for the position of 
                                    <strong>{{candidate.job.mrf.designation.name}}</strong>.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    The joining has been postponed. Kindly review and advise on the next course of action.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Please let us know if any further follow-up is required.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
""",
}

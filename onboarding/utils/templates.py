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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/task-list/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">View Onboarding Journey</a>
                                </p>
                                
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    </html>
"""
    ,
    "satisfaction_survey": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">30-Day Check-In: We'd Love Your Feedback!</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Congratulations on completing your first 30 days at Knowcraft Analytics! We hope your journey has been smooth and fulfilling.</p>
                                <p style="margin:0 0 16px 0;">Please take a moment to fill in our short Satisfaction Survey — your feedback helps us continuously improve the onboarding experience for everyone.</p>
                                
                                <p style="margin:30px 0 35px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/candidate/satisfaction-survey/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Take 30-Day Survey</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">Thank you for your time.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
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
    ,
    "d90_survey": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">90-Day Onboarding Survey</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Congratulations on reaching your 90-day milestone at Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">We'd like to hear about your full onboarding experience, role clarity, support received, and any suggestions for improvement. Your responses are saved directly to our database and help shape future improvements.</p>
                                
                                <p style="margin:30px 0 35px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/candidate/90-day-survey/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Take 90-Day Survey</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">Thank you for your valuable feedback.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
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
    </body>
    </html>
"""
    ,
    "d5_document_verification": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Action Required: Verify Your Documents and Details</h2>
                                <p style="margin:0 0 16px 0;">Dear {{{{candidate.candidate_name}}}},</p>
                                <p style="margin:0 0 16px 0;">Welcome to Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">As part of your onboarding process, we request you to please verify the details and documents you submitted to ensure accuracy and authenticity.</p>
                                
                                <p style="margin:30px 0 35px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/candidate/documents/verify/{{{{candidate.id}}}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Verify Information</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">Please complete this verification as soon as possible.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
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
    </body>
    </html>
"""
    ,
    "esign_request": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">E-Signature Documents Ready</h2>
                                <p style="margin:0 0 16px 0;">Dear {{{{candidate.candidate_name}}}},</p>
                                <p style="margin:0 0 16px 0;">Welcome to Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">As part of your onboarding, we require you to digitally sign your employment documents.</p>
                                <p style="margin:0 0 16px 0;">We have initiated an e-signature request for your onboarding documents via <b>Flowace</b>. You will receive a separate email from Flowace with a secure link to review and sign your documents.</p>
                                <p style="margin:0 0 16px 0;">Please complete this process at your earliest convenience to ensure a smooth joining experience.</p>
                                <p style="margin:0 0 16px 0;">If you face any issues accessing the documents, please feel free to reach out to our HR team.</p>
                                
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/task-list/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">View Onboarding Journey</a>
                                </p>
                                
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "welcome_wfo": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <p style="margin:0 0 16px 0;font-size:18px;font-weight:600;color:#1f2937;">Hi {{{{candidate.candidate_name}}}},</p>
                                <p style="margin:0 0 16px 0;">Welcome to Knowcraft Analytics! We are delighted to have you join our team and look forward to the knowledge, skills, and enthusiasm you will bring to the organization.</p>
                                <p style="margin:0 0 20px 0;">As you begin your journey with us, we would like to share a few important details regarding your onboarding and work-from-office arrangement:</p>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:0 0 25px 0;padding:20px;">
                                    <tr>
                                        <td>
                                            <ul style="margin:0;padding:0 0 0 20px;color:#334155;font-size:15px;line-height:1.8;">
                                                <li style="margin-bottom:8px;"><strong>Reporting Date:</strong> {{{{candidate.joining_date}}}}</li>
                                                <li style="margin-bottom:8px;"><strong>Reporting Time:</strong> {{{{reporting_time}}}}</li>
                                                <li style="margin-bottom:8px;"><strong>Office Address:</strong> {{{{office_address}}}}</li>
                                                <li style="margin-bottom:0;"><strong>Contact Person for Assistance:</strong> {{{{hr_contact_details}}}}</li>
                                            </ul>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:0 0 16px 0;">We encourage you to make the most of this exciting new chapter, connect with your colleagues, and immerse yourself in our culture and values.</p>
                                <p style="margin:0 0 24px 0;">Once again, welcome to the Knowcraft family. We wish you a successful and rewarding journey ahead.</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "welcome_wfh": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <p style="margin:0 0 16px 0;font-size:18px;font-weight:600;color:#1f2937;">Hi {{{{candidate.candidate_name}}}},</p>
                                <p style="margin:0 0 16px 0;">A very warm welcome to <strong>Knowcraft Analytics!</strong></p>
                                <p style="margin:0 0 20px 0;">We are excited to have you join our team and look forward to supporting you as you begin your journey with us in a remote work setup.</p>
                                <p style="margin:0 0 16px 0;">To help you get started smoothly, please find below some key details:</p>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:0 0 25px 0;padding:20px;">
                                    <tr>
                                        <td>
                                            <ul style="margin:0;padding:0 0 0 20px;color:#334155;font-size:15px;line-height:1.8;">
                                                <li style="margin-bottom:8px;"><strong>Joining Date:</strong> {{{{candidate.joining_date}}}}</li>
                                                <li style="margin-bottom:8px;"><strong>Reporting Time:</strong> {{{{reporting_time}}}}</li>
                                                <li style="margin-bottom:0;"><strong>HR Contact for Assistance:</strong> {{{{hr_contact_details}}}}</li>
                                            </ul>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:0 0 16px 0;">You will receive information regarding your system access, onboarding sessions, team introductions, and other resources shortly.</p>
                                <p style="margin:0 0 16px 0;">Although you will be working remotely, we are committed to ensuring you feel connected, supported, and engaged from day one.</p>
                                <p style="margin:0 0 24px 0;">We look forward to your contributions and wish you great success at Knowcraft Analytics.</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "document_signoff": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 20px 0;color:#1f2937;font-size:22px;font-weight:600;">Action Required: Complete Onboarding Document Sign-Off</h2>
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Hello {{{{candidate.candidate_name|default:"Crafter"}}}},</p>
                                <p style="margin:0 0 16px 0;"><strong>Welcome to Knowcraft Analytics!</strong></p>
                                <p style="margin:0 0 16px 0;">As part of your onboarding process, we request you to review and complete the sign-off of the onboarding documents shared with you. These documents contain important information related to your employment, company policies, and onboarding formalities.</p>
                                <p style="margin:0 0 24px 0;">Kindly ensure that all required documents are reviewed and signed at the earliest to facilitate the seamless completion of your onboarding process.</p>
                                
                                <p style="margin:30px 0 35px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/task-list/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;box-shadow:0 2px 6px rgba(37,99,235,0.3);">Review & Sign Documents</a>
                                </p>

                                <p style="margin:0 0 16px 0;">Should you have any questions or require assistance while completing the documentation, please feel free to reach out.</p>
                                <p style="margin:0 0 24px 0;">We look forward to having you on board and wish you a successful journey with Knowcraft Analytics.</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "hr_handbook": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 20px 0;color:#1f2937;font-size:22px;font-weight:600;">HR Handbook</h2>
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Hello {{{{candidate.candidate_name|default:"Crafter"}}}},</p>
                                <p style="margin:0 0 16px 0;"><strong>Welcome to Knowcraft Analytics!</strong></p>
                                <p style="margin:0 0 16px 0;">We are delighted to have you join us and look forward to supporting you as you begin your journey with the organization.</p>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:0 0 20px 0;padding:20px;">
                                    <tr>
                                        <td style="color:#334155;font-size:15px;line-height:1.7;">
                                            📁 <strong>Attached to this email is the HR Handbook.</strong> We encourage you to go through it carefully and familiarize yourself with the policies, processes, benefits, and other important information that will help you settle in smoothly.
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:0 0 16px 0;">Should you have any questions or require any assistance, please feel free to reach out to <a href="mailto:hr@knowcraft.in" style="color:#2563eb;text-decoration:none;font-weight:600;">hr@knowcraft.in</a>. We are happy to help.</p>
                                <p style="margin:0 0 24px 0;">Wishing you a successful and rewarding experience with Knowcraft Analytics.</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "culture_values": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 20px 0;color:#1f2937;font-size:22px;font-weight:600;">Exploring the Culture and Values of Knowcraft</h2>
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Hello {{{{candidate.candidate_name|default:"Crafter"}}}},</p>
                                <p style="margin:0 0 16px 0;">Greetings!</p>
                                <p style="margin:0 0 16px 0;">As we continue to grow and evolve together, it is important that we stay connected to the values and principles that define who we are as an organization.</p>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:0 0 20px 0;padding:20px;">
                                    <tr>
                                        <td style="color:#334155;font-size:15px;line-height:1.7;">
                                            📘 <strong>Attached is a handbook on Knowcraft's Culture and Values.</strong> We encourage you to take some time to read through it and familiarize yourself with the ideas and behaviors that shape our workplace and guide our decisions.
                                        </td>
                                    </tr>
                                    <tr>
                                        <td align="center" style="padding-top:16px;">
                                            <a href="https://hireprostorage.blob.core.windows.net/media/4.2%20Attachment-Culture%20and%20Values%20Handbook.pdf" target="_blank" style="background-color:#2563eb;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:6px;font-weight:bold;font-size:14px;display:inline-block;">📥 Download Culture & Values Handbook (PDF)</a>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:0 0 16px 0;">While this is not a policy document, it serves as our collective moral compass, reflecting the culture we strive to build and uphold every day.</p>
                                
                                <div style="margin:20px 0;padding:16px 20px;border-left:4px solid #2563eb;background-color:#eff6ff;border-radius:0 8px 8px 0;font-style:italic;color:#1e40af;font-size:15px;">
                                    “When our values are clear to us, making choices and decisions become easier.”
                                </div>

                                <p style="margin:0 0 24px 0;">We hope you find the handbook insightful and inspiring, and we look forward to continuing this journey together.</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "chatbot_manual": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 20px 0;color:#1f2937;font-size:22px;font-weight:600;">Introducing HR Buddy - MS Teams Chatbot User Manual</h2>
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Dear {{{{candidate.candidate_name|default:"Crafter"}}}},</p>
                                <p style="margin:0 0 16px 0;">Please find attached the user manual, which outlines the simple steps required to install the <strong>Chatbot within Microsoft Teams</strong>.</p>
                                <p style="margin:0 0 16px 0;">Once installed, you can start using the chatbot just like you would interact with your colleagues — making it quick, easy, and convenient.</p>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:0 0 20px 0;padding:20px;">
                                    <tr>
                                        <td style="color:#334155;font-size:15px;line-height:1.7;">
                                            💡 <strong>Kindly note:</strong> This is currently a beta version, and we are continuously working to enhance its intelligence and usefulness. Your feedback will be invaluable in helping us improve the experience.
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:0 0 16px 0;">If you find that any response is not appropriate or your query has not been addressed correctly, please feel free to share the details with us via email or group chat. Your input will help us further refine the chatbot.</p>
                                <p style="margin:0 0 16px 0;">We encourage everyone to start using this HR Buddy and make the most of this new initiative.</p>
                                <p style="margin:0 0 24px 0;">Thank you, and happy chatting!</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "kai_mascot": f"""
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
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 20px 0;color:#1f2937;font-size:22px;font-weight:600;">Say Hello to KAI 🤖 Crafter Happiness Mascot!</h2>
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Hi {{{{candidate.candidate_name|default:"Crafter"}}}},</p>
                                <p style="margin:0 0 16px 0;">A quick reminder to check your Microsoft Teams — <strong>KAI (Knowcraft + AI + Intelligence)</strong> is waiting to hear from you!</p>
                                <p style="margin:0 0 20px 0;">Our Crafters’ Happiness Mascot is reaching out through a simple weekly check-in to understand how your week is going. Whether things are going great or feel a little challenging — your experience matters.</p>
                                
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:0 0 20px 0;padding:20px;">
                                    <tr>
                                        <td>
                                            <p style="margin:0 0 10px 0;font-weight:700;color:#1f2937;">📅 Check-ins happen:</p>
                                            <ul style="margin:0;padding:0 0 0 20px;color:#334155;font-size:15px;line-height:1.8;">
                                                <li style="margin-bottom:6px;"><strong>Monday:</strong> Kickstart check-in</li>
                                                <li style="margin-bottom:6px;"><strong>Wednesday:</strong> Mid-week pulse</li>
                                                <li style="margin-bottom:0;"><strong>Friday:</strong> Weekly reflection</li>
                                            </ul>
                                        </td>
                                    </tr>
                                </table>

                                <p style="margin:0 0 16px 0;">It takes less than a minute — no links, no forms, just a quick pop-up and click.</p>
                                <p style="margin:0 0 16px 0;">Your responses help us understand what’s working well, where support may be needed, and how we can continue making Knowcraft an even better place for all our Crafters.</p>
                                <p style="margin:0 0 24px 0;">If you haven’t responded yet, please take a moment today and share your update.</p>
                                <br>
                                <p style="margin:20px 0 4px 0;color:#555555;">Warm regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-size:14px;font-weight:600;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "posh_policy": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#ffffff;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:650px;margin:0 auto;background-color:#ffffff;">
            <tr>
                <td align="center" style="padding:0;">
                    <img src="https://hireprostorage.blob.core.windows.net/media/4.3 Email Body-POSH.jpg"
                         alt="POSH Policy"
                         style="width:100%;max-width:650px;height:auto;display:block;border:0;">
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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


HTML_TEMPLATES.update({
    "welcome_joining": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Welcome to Knowcraft!</h2>
                                <p style="margin:0 0 16px 0;">Hi {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">We’re excited to have you join our team and look forward to the energy, ideas, and perspective you’ll bring. Your journey with us begins at our {{location}} office — and we’re here to make your first day comfortable, engaging, and meaningful.</p>
                                
                                <h3 style="margin:20px 0 10px 0;color:#1f2937;font-size:18px;">Joining Details</h3>
                                <p style="margin:0 0 8px 0;"><strong>Location:</strong> {{location}}</p>
                                <p style="margin:0 0 8px 0;"><strong>Office Address:</strong> 07th Floor, Gate No. 04, Ambience Island, NH 48, Gurugram, 122002</p>
                                <p style="margin:0 0 8px 0;"><strong>DOJ:</strong> {{candidate.joining_date}}</p>
                                <p style="margin:0 0 16px 0;"><strong>Reporting Time:</strong> 10:30 AM</p>
                                <p style="margin:0 0 16px 0;"><strong>Point of Contact:</strong> Radhika Mittal</p>
                                
                                <h3 style="margin:20px 0 10px 0;color:#1f2937;font-size:18px;">Life at Knowcraft</h3>
                                <p style="margin:0 0 16px 0;"><strong>What We Value</strong><br>At Knowcraft, our culture is built on:<br>
                                - <strong>Ownership & Accountability</strong> – We trust you to take charge of your work<br>
                                - <strong>Continuous Learning</strong> – Curiosity and growth are part of our everyday<br>
                                - <strong>Collaboration</strong> – Great ideas come from working together<br>
                                - <strong>Integrity & Respect</strong> – We value transparency and people-first thinking<br>
                                We believe in creating an environment where you can learn, contribute, and thrive.</p>
                                
                                <h3 style="margin:20px 0 10px 0;color:#1f2937;font-size:18px;">What to Expect on Your First Day</h3>
                                <p style="margin:0 0 16px 0;">Your first day is all about getting you settled in:<br>
                                - A warm welcome and introduction to the team<br>
                                - A quick walkthrough of our company, processes, and tools<br>
                                - Assistance with documentation and formalities<br>
                                - Setting up your workspace and systems<br>
                                - An overview of your role and initial expectations<br>
                                Don’t worry — you won’t be expected to know everything on day one. We’re here to support you every step of the way.</p>
                                
                                <h3 style="margin:20px 0 10px 0;color:#1f2937;font-size:18px;">A Few Friendly Tips</h3>
                                <p style="margin:0 0 16px 0;">- Come with an open mind and questions — curiosity is always welcome<br>
                                - Take your time to absorb the new environment<br>
                                - Don’t hesitate to reach out — everyone here is happy to help</p>
                                
                                <h3 style="margin:20px 0 10px 0;color:#1f2937;font-size:18px;">A Thought to Start With</h3>
                                <p style="margin:0 0 16px 0;">“Great journeys begin with a single step — and we’re glad you’re taking that step with us.”</p>
                                <p style="margin:0 0 16px 0;">If you have any questions before your joining day, feel free to reach out. We’re happy to assist. Looking forward to meeting you and kicking off this exciting journey together!</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "login_request_reminder": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#dc2626;font-size:24px;font-weight:600;">Action Required: Complete Your Onboarding Documents (JMS)</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Welcome to Knowcraft Analytics! We noticed that your <strong>joining documents are still pending</strong> as per the JMS Onboarding Form.</p>
                                <p style="margin:0 0 16px 0;">To activate your account, enable payroll, and complete IT setup, please upload the required documents immediately using the link below.</p>
                                
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/api/application/documents/upload/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Upload Documents Now</a>
                                </p>
                                
                                <p style="margin:0 0 16px 0;">This is critical for your smooth transition. Our HR and IT teams are ready to support you.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "satisfaction_survey": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">30-Day Onboarding Feedback</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Congratulations on completing your first 30 days at Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">As part of our JMS Onboarding process, we value your feedback on orientation, buddy support, role clarity, training effectiveness, team integration, and overall experience.</p>
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/30-days-survey/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Complete 30-Day Satisfaction Survey</a>
                                </p>
                                <p style="margin:0 0 16px 0;">Your responses (stored in SurveyResponse model) will help us improve the onboarding pipeline for future joiners. All feedback is confidential.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "d90_survey": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">90-Day Onboarding Survey</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Congratulations on reaching your <strong>90-day milestone</strong> at Knowcraft Analytics!</p>
                                <p style="margin:0 0 16px 0;">Your feedback on role clarity, training, team support, culture, and overall experience is extremely valuable. Please complete our structured 90-Day Survey below (or via the link in your dashboard).</p>
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/90-days-survey/{{candidate.id}}" 
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Complete 90-Day Survey</a>
                                </p>
                                <p style="margin:0 0 16px 0;">All responses are securely saved in our database (SurveyResponse model) for analysis and process improvement.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Thank you in advance for your time,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    ,
    "esign_request": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Documents Sent for E-Signature</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">Your statutory onboarding documents have been sent for digital signature via Zoho Sign.</p>
                                <p style="margin:0 0 16px 0;">Please check your inbox (and spam folder) for an email from Zoho Sign containing the secure signing link. Review the documents carefully and complete the e-signature at your earliest convenience.</p>
                                <p style="margin:0 0 16px 0;">This step is required to proceed with your joining formalities.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "esign_reminder": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#dc2626;font-size:24px;font-weight:600;">Reminder: Pending E-Signatures</h2>
                                <p style="margin:0 0 16px 0;">Dear {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">This is a reminder that the following documents are still pending your digital signature:</p>
                                <p style="margin:15px 0 25px 0;padding:15px;background:#fef2f2;border-left:4px solid #ef4444;font-family:monospace;color:#b91c1c;">
                                    {{pending_docs}}
                                </p>
                                <p style="margin:0 0 16px 0;">Please locate the Zoho Sign email and complete the e-signature process immediately to avoid any delay in your onboarding timeline.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
})

NOTIFY_INTERNAL_HTML_TEMPLATES.update({
    "buddy_assigned": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <!-- Logo -->
            <tr>
                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                </td>
            </tr>
            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
            <!-- Content -->
            <tr>
                <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                    <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Buddy Assigned</h2>
                    <p style="margin:0 0 16px 0;">Dear Team,</p>
                    <p style="margin:0 0 16px 0;">Buddies (Technical & Cultural) have been assigned to <strong>{{candidate.candidate_name}}</strong> per the JMS Onboarding Form.</p>
                    <p style="margin:0 0 16px 0;">Please coordinate to ensure the new joiner receives proper guidance on tools, processes, team culture, and role expectations during the first 30/45/90 days.</p>
                    <br>
                    <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                    <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                </td>
            </tr>
            <tr>
                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                    © 2026 Knowcraft Analytics Private Limited • Confidential
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,
    "bgv_escalation": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Hi Team,</p>
                                <p style="margin:0 0 16px 0;">Kindly find my remarks below.</p>
                                <p style="margin:0 0 8px 0;"><strong>Name of the crafter:</strong> {{candidate.candidate_name}}</p>
                                <p style="margin:0 0 8px 0;"><strong>Designation:</strong> {{candidate.job.mrf.designation.name}}</p>
                                <p style="margin:0 0 16px 0;"><strong>Department:</strong> {{candidate.job.mrf.department.name}}</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "doj_minus_15_it_team": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    Upcoming Joining - Laptop Procurement
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear IT Team,</p>
                                <p style="margin:0 0 16px 0;">
                                    Please be informed that candidate <strong>{{candidate.candidate_name}}</strong> is scheduled to join us on <strong>{{candidate.joining_date}}</strong>.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Kindly ensure that all laptop procurement and initial account setup tasks assigned via Zoho ManageEngine are completed prior to their joining date.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "doj_minus_7_hod": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <p style="margin:0 0 16px 0;">Hi {{candidate.job.mrf.requested_by.first_name|default:'HOD'}},</p>
                                <p style="margin:0 0 16px 0;">
                                    Kindly find below the details of the new joiner who will be joining us on {{candidate.joining_date}}, in the {{candidate.job.mrf.department.name}} group. Request you to please update the required information accordingly.
                                </p>
                                <p style="margin:0 0 16px 0;">Let me know in case of any concerns.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "doj_minus_7_admin": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    Action Required: New Joiner Preparations
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear Admin,</p>
                                <p style="margin:0 0 16px 0;">
                                    Candidate <strong>{{candidate.candidate_name}}</strong> is scheduled to join us in 7 days as an office joiner.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Please proceed with allocating their seating arrangement and generating the necessary access ID cards before their start date.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "satisfaction_survey_hod": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    30-Day Completion Notification
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear HOD,</p>
                                <p style="margin:0 0 16px 0;">
                                    This is to notify you that <strong>{{candidate.candidate_name}}</strong> has successfully completed their first 30 days with us.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    We have automatically dispatched the 30-Day Satisfaction Survey to the employee to gauge their onboarding experience.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "schedule_checkin_call_reminder": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    Action Required: 45-Day Check-In Call
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear HR/HOD,</p>
                                <p style="margin:0 0 16px 0;">
                                    This is an automated reminder to schedule the 45-day check-in call for candidate <strong>{{candidate.candidate_name}}</strong>.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Please coordinate via Microsoft Teams and mark the check-in as complete in the HRMS dashboard once finished.
                                </p>
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/task-list/{{candidate.id}}"
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">View Candidate in HRMS</a>
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "schedule_final_review_reminder": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    Action Required: 90-Day Final Review
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear HR/HOD,</p>
                                <p style="margin:0 0 16px 0;">
                                    This is an automated reminder to schedule the 90-day final review call for candidate <strong>{{candidate.candidate_name}}</strong>.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Please hold the meeting and mark the 90-day milestone as complete in the HRMS to officially close out their onboarding pipeline.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "d45_call_not_scheduled_escalation": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Red Alert Banner -->
                        <tr>
                            <td style="background-color:#fef2f2;padding:16px 40px;border-bottom:1px solid #fecaca;">
                                <p style="margin:0;color:#991b1b;font-weight:700;font-size:15px;">
                                    ⚠️ Escalation Alert: Action Required
                                </p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:22px;font-weight:600;">
                                    45-Day Check-In Call Not Scheduled
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">
                                    <strong>5 reminders</strong> have been sent to HR and the HOD to schedule the
                                    <strong>45-Day Check-In Call</strong> for candidate
                                    <strong>{{{{candidate.candidate_name}}}}</strong>,
                                    but the call has <span style="color:#dc2626;font-weight:700;">not been scheduled yet</span>.
                                </p>
                                <p style="margin:0 0 24px 0;">
                                    Please take immediate action to schedule this call and mark it in the HRMS to close this escalation.
                                </p>
                                <p style="margin:0 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/task-list/{{{{candidate.id}}}}"
                                       style="background-color:#dc2626;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">View Candidate in HRMS</a>
                                </p>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "d90_call_not_scheduled_escalation": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Red Alert Banner -->
                        <tr>
                            <td style="background-color:#fef2f2;padding:16px 40px;border-bottom:1px solid #fecaca;">
                                <p style="margin:0;color:#991b1b;font-weight:700;font-size:15px;">
                                    ⚠️ Escalation Alert: Action Required
                                </p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:22px;font-weight:600;">
                                    90-Day Final Review Call Not Scheduled
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear Team,</p>
                                <p style="margin:0 0 16px 0;">
                                    <strong>5 reminders</strong> have been sent to HR and the HOD to schedule the
                                    <strong>90-Day Final Review Call</strong> for candidate
                                    <strong>{{{{candidate.candidate_name}}}}</strong>,
                                    but the call has <span style="color:#dc2626;font-weight:700;">not been scheduled yet</span>.
                                </p>
                                <p style="margin:0 0 24px 0;">
                                    Please take immediate action to schedule this call and mark it in the HRMS to officially close the onboarding pipeline.
                                </p>
                                <p style="margin:0 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/task-list/{{{{candidate.id}}}}"
                                       style="background-color:#dc2626;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">View Candidate in HRMS</a>
                                </p>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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
    "it_team_ticket_created": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#ffffff;padding:25px 40px;border-bottom:1px solid #e2e8f0;">
                                <img src="{FRONTEND_URL}/assets/header-logo.png" alt="Knowcraft Analytics" width="220" style="display:block;border:0;">
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">
                                    New Onboarding IT Ticket
                                </h2>
                                <p style="margin:0 0 16px 0;">Dear IT Team,</p>
                                <p style="margin:0 0 16px 0;">
                                    An onboarding service request has just been initiated for candidate <strong>{{candidate.candidate_name}}</strong>.
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    ManageEngine Ticket Reference: <strong>{{candidate.it_ticket_ref}}</strong>
                                </p>
                                <p style="margin:0 0 16px 0;">
                                    Please monitor this ticket and ensure procurement and setup are finalized according to the joining schedule.
                                </p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    # ── Gap 9: Missing post-joining internal notification templates ──────────

    "doj_minus_15_it_team": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Upcoming Joiner — IT Procurement Reminder</h2>
                                <p style="margin:0 0 16px 0;">Dear IT Team,</p>
                                <p style="margin:0 0 16px 0;">This is an automated reminder that <strong>{{candidate.candidate_name}}</strong> is scheduled to join on <strong>{{candidate.joining_date}}</strong>.</p>
                                <p style="margin:0 0 16px 0;">Please ensure laptop procurement, system access, and email account setup are initiated at the earliest.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    "doj_minus_7_hod": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Upcoming Team Member Joining (7 Days)</h2>
                                <p style="margin:0 0 16px 0;">Dear HOD,</p>
                                <p style="margin:0 0 16px 0;"><strong>{{candidate.candidate_name}}</strong> is joining your department in <strong>7 days</strong>.</p>
                                <p style="margin:0 0 16px 0;">Please prepare for their onboarding — assign a buddy, schedule an orientation session, and ensure their workspace is ready.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    "doj_minus_7_admin": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">New Office Joiner Preparations (7 Days)</h2>
                                <p style="margin:0 0 16px 0;">Dear Admin Team,</p>
                                <p style="margin:0 0 16px 0;"><strong>{{candidate.candidate_name}}</strong> is arriving at the office in <strong>7 days</strong>.</p>
                                <p style="margin:0 0 16px 0;">Please arrange seating, access card issuance, and any other office-entry logistics in advance of their joining date.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    "bgv_escalation": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="padding:40px 30px 25px 30px;background:#fff0f0;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                <h2 style="margin:0 0 22px 0;color:#dc2626;font-size:24px;font-weight:600;">⚠ ESCALATION: BGV Pending Beyond 7 Days</h2>
                                <p style="margin:0 0 16px 0;">Dear HR / Admin Team,</p>
                                <p style="margin:0 0 16px 0;">The Background Verification (BGV) for candidate <strong>{{candidate.candidate_name}}</strong> has been pending for more than <strong>7 days post-joining</strong> and requires immediate attention.</p>
                                <p style="margin:0 0 16px 0;">Please review the current BGV status in the HRMS and take the necessary action to resolve or escalate further.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    "satisfaction_survey_hod_junior": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">30-Day HOD Satisfaction Survey</h2>
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;"><strong>{{candidate.candidate_name}}</strong> has completed their first 30 days at Knowcraft Analytics.</p>
                                <p style="margin:0 0 16px 0;">As their Head of Department, we'd value your assessment of their progress during this initial period. Please take a moment to complete the HOD Satisfaction Survey.</p>
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/hod-survey-junior/{{candidate.id}}"
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Complete HOD Survey</a>
                                </p>
                                <p style="margin:0 0 16px 0;">Your feedback helps us continuously improve the onboarding experience for all new joiners.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    "satisfaction_survey_hod_senior": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">30-Day HOD Satisfaction Survey (Senior)</h2>
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;"><strong>{{candidate.candidate_name}}</strong> has completed their first 30 days at Knowcraft Analytics.</p>
                                <p style="margin:0 0 16px 0;">As their Head of Department, we'd value your assessment of their leadership, strategic thinking, and overall contribution during this initial period. Please complete the HOD Satisfaction Survey (Senior Level).</p>
                                <p style="margin:25px 0 30px 0;text-align:center;">
                                    <a href="{FRONTEND_URL}/onboarding/hod-survey-senior/{{candidate.id}}"
                                       style="background-color:#2563eb;color:#ffffff;padding:14px 32px;text-decoration:none;border-radius:6px;font-weight:600;font-size:16px;display:inline-block;">Complete HOD Survey (Senior)</a>
                                </p>
                                <p style="margin:0 0 16px 0;">Your detailed feedback helps us refine the onboarding experience for senior professionals.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
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

    "buddy_assigned": f"""
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
                                <p style="margin:0 0 16px 0;">Hi {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;">You have been assigned as the <strong>{{buddy_type}} Buddy</strong> for our newest team member, <strong>{{candidate.candidate_name}}</strong>. We are excited to have them on board and know you will make their integration seamless and enjoyable.</p>
                                <p style="margin:0 0 16px 0;">As their {{buddy_type}} Buddy, your role is to be their go-to person for questions, guidance, and support during their initial weeks here.</p>
                                <p style="margin:0 0 10px 0;"><strong>You can expect to:</strong></p>
                                <ol style="margin:0 0 16px 0;padding-left:20px;">
                                    <li style="margin-bottom:6px;">Introduce yourself and schedule an informal meeting during their first week.</li>
                                    <li style="margin-bottom:6px;">Provide an overview of our company culture, values, and workplace practices.</li>
                                    <li style="margin-bottom:6px;">Assist them in setting up their workspace, email, and other essential tools.</li>
                                    <li style="margin-bottom:6px;">Accompany them to team meetings and introduce them to other team members.</li>
                                    <li style="margin-bottom:6px;">Offer insights into their projects and help them get up to speed with role responsibilities.</li>
                                    <li style="margin-bottom:6px;">Be available for regular catchups and check-ins to ensure their smooth integration.</li>
                                </ol>
                                <p style="margin:0 0 16px 0;">We encourage open communication. If you have any questions or need support during this process, please reach out to HR directly.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                &copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,

    "candidate_buddy_info": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Welcome to the Buddy Program!</h2>
                                <p style="margin:0 0 16px 0;">Hi {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">On behalf of the entire team, I would like to extend a warm welcome to you as our newest member. We are excited to have you on board and look forward to working together and making your integration into our company a seamless and enjoyable experience.</p>
                                <p style="margin:0 0 16px 0;">To help you settle in and get acquainted with our company culture, processes, and your role, we have implemented a Buddy Program. The Buddy Program pairs you with an experienced colleague, your "Buddy," who will be your go-to person for any questions, guidance, and support during your initial weeks here.</p>
                                <p style="margin:0 0 16px 0;">Your Technical Buddy, <strong>{{technical_buddy_name}}</strong> is a seasoned team member who is excited to share his/her knowledge and experiences with you. He / She will help you navigate through your onboarding process, introduce you to other team members, and provide insights into the day-to-day workings of the company.</p>
                                <p style="margin:0 0 16px 0;">Your Cultural Buddy, <strong>{{cultural_buddy_name}}</strong> is a part of HR team who will assist and provide you with an overview on company culture, values, and workplace practices.</p>
                                <p style="margin:0 0 16px 0;">The primary objective of the Buddy Program is to ensure that you feel comfortable, confident, and connected from day one. Whether you have questions about company policies, team dynamics, or where to find the best coffee in the office, your Buddy is there to help.</p>
                                <p style="margin:0 0 10px 0;">You can expect your Buddy to:</p>
                                <ol style="margin:0 0 16px 0;padding-left:20px;">
                                    <li style="margin-bottom:6px;">Introduce themselves and schedule an informal meeting with you during your first week.</li>
                                    <li style="margin-bottom:6px;">Provide an overview of our company culture, values, and workplace practices.</li>
                                    <li style="margin-bottom:6px;">Assist you in setting up your workspace, email, and other essential tools.</li>
                                    <li style="margin-bottom:6px;">Accompany you to team meetings and introduce you to other team members.</li>
                                    <li style="margin-bottom:6px;">Offer insights into the projects you'll be working on and help you get up to speed with your role responsibilities.</li>
                                    <li style="margin-bottom:6px;">Be available for regular catchups and check-ins to ensure your smooth integration.</li>
                                </ol>
                                <p style="margin:0 0 16px 0;">We encourage open communication during this process, and please don't hesitate to ask any questions or express any concerns you may have. We are committed to making your onboarding experience a positive one.</p>
                                <p style="margin:0 0 16px 0;">If you have not been contacted by them or have any queries in the meantime, please feel free to reach out to our HR department or me directly.</p>
                                <p style="margin:0 0 16px 0;">Once again, we are delighted to have you as part of our team, and we look forward to supporting you in your journey with us. Welcome aboard!</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                &copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,

    "work_email_reminder": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#dc2626;font-size:24px;font-weight:600;">Action Required: Work Email Not Set</h2>
                                <p style="margin:0 0 16px 0;">Dear {{reciever_name}},</p>
                                <p style="margin:0 0 16px 0;">The work email for <strong>{{candidate.candidate_name}}</strong> has not been configured in the HRMS system yet.</p>
                                <p style="margin:0 0 16px 0;">A work email is required to:</p>
                                <ul style="margin:0 0 16px 0;padding-left:20px;">
                                    <li style="margin-bottom:6px;">Send statutory e-sign documents via Zoho Sign</li>
                                    <li style="margin-bottom:6px;">Deliver 30-day and 90-day satisfaction surveys</li>
                                    <li style="margin-bottom:6px;">Enable onboarding task communications</li>
                                </ul>
                                <p style="margin:0 0 16px 0;">Please set the work email in the HRMS at the earliest to avoid delays in the onboarding process.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR (Automated)</p>
                                <p style="margin:4px 0 0 0;color:#555555;font-weight:700;">Knowcraft Analytics Private Limited.</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                &copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
})

HTML_TEMPLATES.update({
    "d45_call_candidate_reminder": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Catch Up Call: {{candidate.candidate_name}}</h2>
                                <p style="margin:0 0 16px 0;">Hi {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">This is a gentle reminder to join the catch-up call as per the scheduled time.</p>
                                <p style="margin:0 0 16px 0;">In case you have any prior commitments or planned leave, please let us know in advance so that we can make the necessary arrangements.</p>
                                <p style="margin:0 0 16px 0;">Thank you for your cooperation.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                &copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,
    "d90_call_candidate_reminder": f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Catch Up Call: {{candidate.candidate_name}}</h2>
                                <p style="margin:0 0 16px 0;">Hi {{candidate.candidate_name}},</p>
                                <p style="margin:0 0 16px 0;">This is a gentle reminder to join the catch-up call as per the scheduled time.</p>
                                <p style="margin:0 0 16px 0;">In case you have any prior commitments or planned leave, please let us know in advance so that we can make the necessary arrangements.</p>
                                <p style="margin:0 0 16px 0;">Thank you for your cooperation.</p>
                                <br>
                                <p style="margin:20px 0 6px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team HR</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                &copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,
})

NOTIFY_INTERNAL_HTML_TEMPLATES.update({
    "onboarding_initiation_reminder": """
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="background:#0f172a;padding:28px 40px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:220px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#b91c1c;padding:18px 40px;">
                                <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:0.3px;">
                                    ⚠️ Action Required: Onboarding Initiation Pending
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Dear HR Team,</p>
                                <p style="margin:0 0 16px 0;">
                                    The onboarding initiation form for <strong>{candidate.candidate_name}</strong> is currently pending.
                                </p>
                                <p style="margin:0 0 24px 0;">
                                    This form must be submitted through the portal to initiate the candidate's onboarding task sequence (including emails, surveys, and IT ticket generation). Please complete it at your earliest convenience to avoid delays in their joining process.
                                </p>
                                <br>
                                <p style="margin:0 0 4px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">HRMS Automation</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • System Generated
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,

    "it_ticket_close_request": """
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <tr>
                            <td align="center" style="background:#0f172a;padding:28px 40px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:220px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#1e40af;padding:18px 40px;">
                                <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:0.3px;">
                                    🎫 Action Required: Close Onboarding IT Ticket
                                </h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <p style="margin:0 0 16px 0;font-size:17px;font-weight:600;color:#1f2937;">Dear IT Team,</p>
                                <p style="margin:0 0 16px 0;">
                                    This is an automated notification that the 90-day onboarding period for <strong>{candidate.candidate_name}</strong> has successfully concluded.
                                </p>
                                <p style="margin:0 0 24px 0;">
                                    Please proceed to close their onboarding IT ticket. Kindly ensure that all final IT handovers and access reviews are complete.
                                </p>
                                <br>
                                <p style="margin:0 0 4px 0;color:#555555;">Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">HRMS Automation</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                © 2026 Knowcraft Analytics Private Limited • System Generated
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,

    "onboarding_form_submitted": f"""
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:680px;margin:0 auto;background-color:#f4f4f7;">
            <tr>
                <td align="center" style="padding:30px 15px;">
                    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                        <!-- Header -->
                        <tr>
                            <td align="center" style="background:#0f172a;padding:28px 40px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:220px;height:auto;display:block;margin:0 auto;">
                            </td>
                        </tr>
                        <!-- Title Banner -->
                        <tr>
                            <td style="background:#1e40af;padding:18px 40px;">
                                <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;letter-spacing:0.3px;">
                                    📋 New Onboarding Form Submitted
                                </h1>
                            </td>
                        </tr>
                        <!-- Intro -->
                        <tr>
                            <td style="padding:28px 40px 10px 40px;color:#374151;font-size:15px;line-height:1.6;">
                                <p style="margin:0 0 8px 0;">Dear Admin Team,</p>
                                <p style="margin:0;">
                                    An onboarding form has been submitted for
                                    <strong style="color:#1e40af;">{{candidate.candidate_name}}</strong>
                                    by <strong>{{submitted_by_name}}</strong>.
                                    All the submitted details are listed below for your records and action.
                                </p>
                            </td>
                        </tr>
                        <!-- Section: Personal Details -->
                        <tr>
                            <td style="padding:20px 40px 6px 40px;">
                                <p style="margin:0 0 10px 0;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:#6b7280;">
                                    Personal Information
                                </p>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:14px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;width:45%;border-bottom:1px solid #e5e7eb;">First Name</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{first_name}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Last Name</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{last_name}}</td>
                                    </tr>
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Personal Email</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{personal_email_id}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;">Contact Number</td>
                                        <td style="padding:10px 16px;color:#1f2937;">{{contact_number}}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Section: Employment Details -->
                        <tr>
                            <td style="padding:20px 40px 6px 40px;">
                                <p style="margin:0 0 10px 0;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:#6b7280;">
                                    Employment Details
                                </p>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:14px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;width:45%;border-bottom:1px solid #e5e7eb;">Joining Date</td>
                                        <td style="padding:10px 16px;color:#1e40af;font-weight:700;border-bottom:1px solid #e5e7eb;">{{joining_date}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Designation</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{designation}}</td>
                                    </tr>
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Department</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{department}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Employee Category</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{employee_category}}</td>
                                    </tr>
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Crafter ID</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{crafter_id}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;">Work From</td>
                                        <td style="padding:10px 16px;color:#1f2937;">{{work_from}}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Section: Location & IT -->
                        <tr>
                            <td style="padding:20px 40px 6px 40px;">
                                <p style="margin:0 0 10px 0;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:#6b7280;">
                                    Location & IT Setup
                                </p>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:14px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;width:45%;border-bottom:1px solid #e5e7eb;">Office Location</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{center_office_location}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Asset Collection Mode</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{mode_for_collecting_assets}}</td>
                                    </tr>
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Assets Required</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{assets}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Site</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{site}}</td>
                                    </tr>
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;">Team Manager</td>
                                        <td style="padding:10px 16px;color:#1f2937;">{{team_manager}}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Section: Additional Info -->
                        <tr>
                            <td style="padding:20px 40px 6px 40px;">
                                <p style="margin:0 0 10px 0;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;color:#6b7280;">
                                    Additional Information
                                </p>
                                <table border="0" cellpadding="0" cellspacing="0" width="100%" style="border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:14px;">
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;width:45%;border-bottom:1px solid #e5e7eb;">Emails to Notify</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{emails_to_notify}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Current Address</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{current_address}}</td>
                                    </tr>
                                    <tr style="background:#f8fafc;">
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;border-bottom:1px solid #e5e7eb;">Description</td>
                                        <td style="padding:10px 16px;color:#1f2937;border-bottom:1px solid #e5e7eb;">{{description}}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding:10px 16px;color:#6b7280;font-weight:600;">Custom Notes</td>
                                        <td style="padding:10px 16px;color:#1f2937;">{{custom_notes}}</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- CTA -->
                        <tr>
                            <td style="padding:28px 40px 10px 40px;text-align:center;">
                                <a href="{FRONTEND_URL}/onboarding/task-list/{{candidate.id}}"
                                   style="background-color:#1e40af;color:#ffffff;padding:13px 30px;text-decoration:none;border-radius:6px;font-weight:600;font-size:15px;display:inline-block;">
                                    View Candidate in HRMS
                                </a>
                            </td>
                        </tr>
                        <!-- Closing -->
                        <tr>
                            <td style="padding:20px 40px 30px 40px;color:#374151;font-size:15px;line-height:1.6;">
                                <p style="margin:0 0 4px 0;">Warm Regards,</p>
                                <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR (Automated)</p>
                                <p style="margin:4px 0 0 0;color:#6b7280;font-weight:600;">Knowcraft Analytics Private Limited.</p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                &copy; 2026 Knowcraft Analytics Private Limited &bull; Confidential
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """,
})

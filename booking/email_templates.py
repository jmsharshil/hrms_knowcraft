cancel_online_interview_text = """Dear {candidate.candidate_name},
We regret to inform you that your {candidate.round_name} interview for the position of {candidate.job.mrf.designation.name} scheduled at {candidate.interview_scheduled_at} has been cancelled.

Please reach out to the HR team for any questions or next steps.

Warm regards,
Team-HR"""

cancel_online_interview_template = """<html>
    <body style="font-family:Arial,sans-serif;background-color:#f4f4f7;margin:0;padding:0;">
        <table align="center" width="100%" style="max-width:620px;margin:0 auto;">
            <tr><td align="center" style="padding:30px;">
                <table width="100%" style="background:#fff;border-radius:12px;overflow:hidden;">
                    <tr><td align="center" style="padding:40px;"><img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft" style="max-width:200px;"></td></tr>
                    <tr><td style="padding:35px;color:#333;">
                        <h2>Interview Cancelled — {candidate.round_name}</h2>
                        <p>Dear {candidate.candidate_name},</p>
                        <p>We regret to inform you that your interview for <strong>{candidate.job.mrf.designation.name}</strong> scheduled at <strong>{candidate.interview_scheduled_at}</strong> has been cancelled.</p>
                        <p>Please contact HR for next steps.</p>
                        <br>
                        <p>Warm regards,<br>Team-HR, Knowcraft Analytics</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>"""

cancel_offline_interview_text = """Dear {booking.interviewer.name},

The interview for {candidate.candidate_name} ({candidate.job.mrf.designation.name}) has been cancelled.

📅 Previously Scheduled: {candidate.interview_scheduled_at}
📍 Location: {location_str}

Warm Regards,
Team – HR"""

cancel_offline_interview_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:white;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <tr>
                            <td align="center" style="padding:30px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:250px;">
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:30px 40px;">
                                <h2 style="color:#dc2626;">Interview Cancelled</h2>

                                <p>Dear <strong>{booking.interviewer.name}</strong>,</p>

                                <p>
                                    The interview for <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>) has been cancelled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 Time:</b></td>
                                        <td>{candidate.interview_scheduled_at}</td>
                                    </tr>
                                    <tr>
                                        <td><b>📍 Location:</b></td>
                                        <td>{location_str}</td>
                                    </tr>
                                </table>

                                <p>No further action is required.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

reschedule_online_interview_text= """Dear {candidate.candidate_name},
Your {candidate.round_name} interview for the position of {candidate.job.mrf.designation.name} has been rescheduled to {start_str}.
Join link: {candidate.interview_link}

Kindly ensure you join the interview on time using a laptop/desktop.

Warm regards,
Team-HR
Knowcraft Analytics"""

reschedule_online_interview_template = """<html>
    <body style="font-family:Arial,sans-serif;background-color:#f4f4f7;margin:0;padding:0;">
        <table align="center" width="100%" style="max-width:620px;margin:0 auto;">
            <tr><td align="center" style="padding:30px;">
                <table width="100%" style="background:#fff;border-radius:12px;overflow:hidden;">
                    <tr><td align="center" style="padding:40px;"><img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft" style="max-width:200px;"></td></tr>
                    <tr><td style="padding:35px;color:#333;">
                        <h2>Interview Rescheduled — {candidate.round_name}</h2>
                        <p>Dear {candidate.candidate_name},</p>
                        <p>Your interview for <strong>{candidate.job.mrf.designation.name}</strong> has been rescheduled to <strong>{start_str}</strong>.</p>
                        <p style="text-align:center;margin:30px 0;">
                            <a href="{candidate.interview_link}" style="background-color:#2563eb;color:#fff;padding:16px 36px;text-decoration:none;border-radius:8px;font-weight:600;">Join Interview on MS Teams</a>
                        </p>
                        <p>Please join on time using a laptop/desktop for a smooth experience.</p>
                        <br>
                        <p>Warm regards,<br>Team-HR, Knowcraft Analytics</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>"""

reschedule_offline_interview_text = """Dear {booking.interviewer.name},

The interview for {candidate.candidate_name} ({candidate.job.mrf.designation.name}) has been rescheduled.

📅 New Date & Time: {start_str}
📍 Location: {location_str}

Google Map Link:
{maps_link}

Feedback Link:
{candidate.feedback_link}

Warm Regards,
Team – HR"""

reschedule_offline_interview_template = """
    <html>
    <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
        <table align="center" width="100%" style="max-width:620px;margin:0 auto;">
            <tr>
                <td style="padding:30px 15px;">
                    <table width="100%" style="background:#ffffff;border:1px solid #e0e3e9;border-radius:12px;">
                        
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:30px 40px;">
                                <h2 style="margin-bottom:20px;">Interview Rescheduled</h2>

                                <p>Dear <strong>{booking.interviewer.name}</strong>,</p>

                                <p>
                                    Interview for <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>) has been rescheduled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 New Time:</b></td>
                                        <td>{start_str}</td>
                                    </tr>
                                    <tr>
                                        <td><b>📍 Location:</b></td>
                                        <td><a href="{maps_link}">{location_str}</a></td>
                                    </tr>
                                </table>

                                <p style="text-align:center;margin:30px 0;">
                                    <a href="{candidate.feedback_link}" style="background:#2563eb;color:white;padding:14px 30px;border-radius:6px;text-decoration:none;">
                                        Submit Feedback
                                    </a>
                                </p>

                                <p>Please use the updated schedule.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

reschedule_offline_interview_candidate_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:white;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:30px 40px;">
                                <h2>Interview Rescheduled — {candidate.round_name}</h2>

                                <p>Dear <strong>{candidate.candidate_name}</strong>,</p>

                                <p>
                                    Your <strong>{candidate.round_name}</strong> interview for 
                                    <strong>{candidate.job.mrf.designation.name}</strong> has been rescheduled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 New Time:</b></td>
                                        <td>{start_str}</td>
                                    </tr>
                                    <tr>
                                        <td><b>📍 Location:</b></td>
                                        <td><a href="{maps_link}">{location_str}</a></td>
                                    </tr>
                                </table>

                                <p>Please arrive 10–15 minutes early.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

reschedule_offline_interview_candidate_text = """Dear {candidate.candidate_name},

Your {candidate.round_name} interview for the position of {candidate.job.mrf.designation.name} has been rescheduled.

📅 New Date & Time: {start_str}
📍 Location: {location_str}

Google Map Link:
{maps_link}

Kindly report 10–15 minutes before the scheduled time.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited"""

cancel_offline_interview_candidate_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:white;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:30px 40px;">
                                <h2 style="color:#dc2626;">Interview Cancelled</h2>

                                <p>Dear <strong>{candidate.candidate_name}</strong>,</p>

                                <p>
                                    Your <strong>{candidate.round_name}</strong> interview for 
                                    <strong>{candidate.job.mrf.designation.name}</strong> has been cancelled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 Time:</b></td>
                                        <td>{candidate.interview_scheduled_at}</td>
                                    </tr>
                                    <tr>
                                        <td><b>📍 Location:</b></td>
                                        <td>{location_str}</td>
                                    </tr>
                                </table>

                                <p>We will notify you if rescheduled.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""
cancel_offline_interview_candidate_text = """Dear {candidate.candidate_name},

We regret to inform you that your {candidate.round_name} interview for the position of {candidate.job.mrf.designation.name} has been cancelled.

📅 Scheduled Time: {candidate.interview_scheduled_at}
📍 Location: {location_str}

If applicable, we will inform you of the next steps.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited"""

attendees_update_template = """
        <html>
        <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
            <table align="center" width="100%" style="max-width:620px;">
                <tr>
                    <td style="padding:30px;">
                        <table width="100%" style="background:#ffffff;border-radius:12px;border:1px solid #e0e3e9;">
                            
                            <!-- Logo -->
                            <tr>
                                <td align="center" style="padding:35px;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                                </td>
                            </tr>

                            <!-- Content -->
                            <tr>
                                <td style="padding:30px 40px;">
                                    <h2>Interview Panel Updated</h2>

                                    <p>Dear <strong>{extra.name}</strong>,</p>

                                    <p>
                                        You have been added to the interview panel for 
                                        <strong>{candidate.candidate_name}</strong> 
                                        (<strong>{candidate.job.mrf.designation.name}</strong>).
                                    </p>

                                    <table style="margin:20px 0;">
                                        <tr>
                                            <td><b>📅 Time:</b></td>
                                            <td>{candidate.interview_scheduled_at}</td>
                                        </tr>
                                        <tr>
                                            <td><b>📍 Location:</b></td>
                                            <td><a href="{maps_link}">{location_str}</a></td>
                                        </tr>
                                    </table>

                                    <p>Please be available at the scheduled time.</p>

                                    <br>
                                    <p>Warm Regards,<br><b>Team – HR</b></p>
                                </td>
                            </tr>

                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
    """

attendees_update_text = """Dear {extra.name},

You have been added to the interview panel for {candidate.candidate_name} ({candidate.job.mrf.designation.name}).

📅 Date & Time: {candidate.interview_scheduled_at}
📍 Location: {location_str}

Google Map Link:
{maps_link}

Warm Regards,
Team – HR"""

attendees_update_online_text = """Dear {extra.name},

You have been added to the interview panel for {candidate.candidate_name} ({candidate.job.mrf.designation.name}).

📅 Date & Time: {candidate.interview_scheduled_at}

Join Link:
{booking.meeting_link}

Warm Regards,
Team – HR"""

attendees_update_online_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:#ffffff;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:30px 40px;">
                                <h2>Interview Panel Updated</h2>

                                <p>Dear <strong>{extra.name}</strong>,</p>

                                <p>
                                    You have been added to the interview panel for 
                                    <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>).
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 Time:</b></td>
                                        <td>{candidate.interview_scheduled_at}</td>
                                    </tr>
                                </table>

                                <!-- Join Button -->
                                <p style="text-align:center;margin:30px 0;">
                                    <a href="{booking.meeting_link}" 
                                       style="background:#2563eb;color:white;padding:14px 30px;border-radius:6px;text-decoration:none;">
                                        Join Interview
                                    </a>
                                </p>

                                <p>Please join on time.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

attendees_update_interviewer_text = """Dear {booking.interviewer.name},
The attendee list for the interview with {candidate.candidate_name} has been updated.

📅 Date & Time: {candidate.interview_scheduled_at}
📍 Location: {location_str}

Warm Regards,
Team – HR"""

attendees_update_interviewer_template = """
        <html>
        <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
            <table align="center" width="100%" style="max-width:620px;">
                <tr>
                    <td style="padding:30px;">
                        <table width="100%" style="background:white;border-radius:12px;border:1px solid #e0e3e9;">
                            
                            <tr>
                                <td align="center" style="padding:30px;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:250px;">
                                </td>
                            </tr>

                            <tr>
                                <td style="padding:30px 40px;">
                                    <h2>Attendees Updated</h2>

                                    <p>Dear <strong>{booking.interviewer.name}</strong>,</p>

                                    <p>
                                        The attendee list for the interview with 
                                        <strong>{candidate.candidate_name}</strong> has been updated.
                                    </p>

                                    <table style="margin:20px 0;">
                                        <tr>
                                            <td><b>📅 Time:</b></td>
                                            <td>{candidate.interview_scheduled_at}</td>
                                        </tr>
                                        <tr>
                                            <td><b>📍 Location:</b></td>
                                            <td><a href="{maps_link}">{location_str}</a></td>
                                        </tr>
                                    </table>

                                    <p>Please coordinate accordingly.</p>

                                    <br>
                                    <p>Warm Regards,<br><b>Team – HR</b></p>
                                </td>
                            </tr>

                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
    """

reschedule_online_interview_extra_text ="""Dear {extra.name},

The interview for {candidate.candidate_name} ({candidate.job.mrf.designation.name}) has been rescheduled.

📅 New Date & Time: {start_str}

Join Link:
{booking.meeting_link}

Warm Regards,
Team – HR"""

reschedule_online_interview_extra_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:#ffffff;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:30px 40px;">
                                <h2>Interview Rescheduled - {candidate.round_name}</h2>

                                <p>Dear <strong>{extra.name}</strong>,</p>

                                <p>
                                    The interview for <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>) has been rescheduled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 New Time:</b></td>
                                        <td>{start_str}</td>
                                    </tr>
                                </table>

                                <!-- Join Button -->
                                <p style="text-align:center;margin:30px 0;">
                                    <a href="{booking.meeting_link}" 
                                       style="background:#2563eb;color:white;padding:14px 30px;border-radius:6px;text-decoration:none;">
                                        Join Interview
                                    </a>
                                </p>

                                <p>Please join on time.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""
reschedule_offline_interview_extra_text = """Dear {extra.name},

The interview for {candidate.candidate_name} ({candidate.job.mrf.designation.name}) has been rescheduled.

📅 New Date & Time: {start_str}
📍 Location: {location_str}

Google Map Link:
{maps_link}

Warm Regards,
Team – HR"""

reschedule_offline_interview_extra_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:#ffffff;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <!-- Logo -->
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <!-- Content -->
                        <tr>
                            <td style="padding:30px 40px;">
                                <h2>Interview Rescheduled - {candidate.round_name}</h2>

                                <p>Dear <strong>{extra.name}</strong>,</p>

                                <p>
                                    The interview for <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>) has been rescheduled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 New Time:</b></td>
                                        <td>{start_str}</td>
                                    </tr>
                                    <tr>
                                        <td><b>📍 Location:</b></td>
                                        <td><a href="{maps_link}">{location_str}</a></td>
                                    </tr>
                                </table>

                                <p>Please adjust your schedule accordingly.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

cancel_offline_interview_extra_text = """Dear {extra.name},

The interview for {candidate.candidate_name} ({candidate.job.mrf.designation.name}) has been cancelled.

📅 Scheduled Time: {candidate.interview_scheduled_at}
📍 Location: {location_str}

Warm Regards,
Team – HR"""

cancel_offline_interview_extra_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:#ffffff;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:30px 40px;">
                                <h2 style="color:#dc2626;">Interview Cancelled - {candidate.round_name}</h2>

                                <p>Dear <strong>{extra.name}</strong>,</p>

                                <p>
                                    The interview for <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>) has been cancelled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 Time:</b></td>
                                        <td>{candidate.interview_scheduled_at}</td>
                                    </tr>
                                    <tr>
                                        <td><b>📍 Location:</b></td>
                                        <td>{location_str}</td>
                                    </tr>
                                </table>

                                <p>No further action is required.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

cancel_online_interview_extra_text = """Dear {extra.name},

The interview for {candidate.candidate_name} ({candidate.job.mrf.designation.name}) has been cancelled.

📅 Scheduled Time: {candidate.interview_scheduled_at}

Warm Regards,
Team – HR"""

cancel_online_interview_extra_template = """
    <html>
    <body style="margin:0;padding:0;background:#f4f4f7;font-family:Arial;">
        <table align="center" width="100%" style="max-width:620px;">
            <tr>
                <td style="padding:30px;">
                    <table width="100%" style="background:#ffffff;border-radius:12px;border:1px solid #e0e3e9;">
                        
                        <tr>
                            <td align="center" style="padding:35px;">
                                <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" style="max-width:260px;">
                            </td>
                        </tr>

                        <tr>
                            <td style="padding:30px 40px;">
                                <h2 style="color:#dc2626;">Interview Cancelled - {candidate.round_name}</h2>

                                <p>Dear <strong>{extra.name}</strong>,</p>

                                <p>
                                    The interview for <strong>{candidate.candidate_name}</strong> 
                                    (<strong>{candidate.job.mrf.designation.name}</strong>) has been cancelled.
                                </p>

                                <table style="margin:20px 0;">
                                    <tr>
                                        <td><b>📅 Time:</b></td>
                                        <td>{candidate.interview_scheduled_at}</td>
                                    </tr>
                                </table>

                                <p>No further action is required.</p>

                                <br>
                                <p>Warm Regards,<br><b>Team – HR</b></p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
"""

def get_interviewer_email_template(action, candidate, interviewer, start_str, meeting_link=None, feedback_link=None, resume_attachment_url=None):
    """
    action: str -> 'scheduled', 'rescheduled', 'attendees_updated', 'cancelled'
    candidate: Candidate object
    interviewer: Interviewer object
    start_str: str -> formatted datetime
    meeting_link: str (optional)
    feedback_link: str (optional)
    resume_attachment_url: str (optional)
    """

    # Define heading and main message based on action
    if action == "scheduled":
        heading = "Interview Scheduled"
        main_text = f"This is to inform you that the interview for <strong>{candidate.candidate_name}</strong> ({candidate.job.mrf.designation.name}) has been scheduled on <strong>{start_str}</strong>."
    elif action == "rescheduled":
        heading = "Interview Rescheduled"
        main_text = f"The interview for <strong>{candidate.candidate_name}</strong> ({candidate.job.mrf.designation.name}) has been rescheduled to <strong>{start_str}</strong>."
    elif action == "attendees_updated":
        heading = "Updated Interview Attendees"
        main_text = f"The attendees for the interview of <strong>{candidate.candidate_name}</strong> ({candidate.job.mrf.designation.name}) have been updated. Interview is on <strong>{start_str}</strong>."
    elif action == "cancelled":
        heading = "Interview Cancelled"
        main_text = f"The interview for <strong>{candidate.candidate_name}</strong> ({candidate.job.mrf.designation.name}) scheduled on <strong>{start_str}</strong> has been cancelled."
    else:
        heading = "Interview Update"
        main_text = ""

    # HTML Template
    html_template = f"""
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
                                <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">{heading} — {candidate.job.mrf.designation.name}</h2>
                                <p style="margin:0 0 16px 0;">Dear {interviewer.name},</p>
                                <p style="margin:0 0 16px 0;">{main_text}</p>
                                """

    # Add table with links if not cancelled
    if action != "cancelled":
        html_template += f"""
        <table style="margin:20px 0;width:100%;border-collapse:collapse;">
            {'<tr><td style="padding:12px 0;width:140px;font-weight:600;color:#475569;">Join Link:</td><td style="padding:12px 0;"><a href="' + meeting_link + '" style="color:#2563eb;text-decoration:underline;font-weight:500;">Join Meeting</a></td></tr>' if meeting_link else ''}
            {'<tr><td style="padding:12px 0;width:140px;font-weight:600;color:#475569;">Feedback Link:</td><td style="padding:12px 0;"><a href="' + feedback_link + '" style="color:#2563eb;text-decoration:underline;font-weight:500;">Give Feedback</a></td></tr>' if feedback_link else ''}
            {'<tr><td style="padding:12px 0;width:140px;font-weight:600;color:#475569;">Resume:</td><td style="padding:12px 0;"><a href="' + resume_attachment_url + '" style="color:#2563eb;text-decoration:underline;font-weight:500;">View / Download Resume</a></td></tr>' if resume_attachment_url else ''}
        </table>
        """

    # Closing
    html_template += """
        <p style="margin:25px 0 16px 0;">Kindly be prepared and join on time.</p>
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
    """
    return html_template


import requests, json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .engine import automation_engine
from django.db.models import Q
from django.utils import timezone
from onboarding.models import OfferDocument

# ZOHO_SIGN_URL = "https://sign.zoho.com/api/v1"

def get_access_token():
    url = "https://accounts.zoho.in/oauth/v2/token"
    data = {
        "refresh_token": settings.ZOHO_REFRESH_TOKEN,
        "client_id": settings.ZOHO_CLIENT_ID,
        "client_secret": settings.ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
#     data = {
#     "grant_type": "authorization_code",
#     "client_id": settings.ZOHO_CLIENT_ID,
#     "client_secret": settings.ZOHO_CLIENT_SECRET,
#     "redirect_uri": "https://www.zoho.com",  # placeholder
#     "code": '1000.c6fb572ad5be1c5de94c7a245d9821af.e0d08e96d048f15c55ef347820714964'
# }
    resp = requests.post(url, data=data)
    try:
        data = resp.json()
    except:
        raise Exception("Non-JSON response: " + resp.text)

    if "access_token" not in data:
        raise Exception("Zoho OAuth Error: " + str(data))

    return data["access_token"]

# def send_offer_letter(request):
#     # Example: get candidate data somehow (e.g. POST JSON)
#     candidate_email = request.POST["email"]
#     candidate_name = request.POST["name"]
#     # path to your offer letter PDF (could be generated or static)
#     file_path = "/media/offer_letter.pdf"

#     token = get_access_token()
#     headers = {"Authorization": f"Zoho-oauthtoken {token}"}

#     files = {"file": open(file_path, "rb")}
#     data = {
#         "requests": {
#             "request_name": "Offer Letter for " + candidate_name,
#             "actions": [
#                 {
#                     "recipient_email": candidate_email,
#                     "recipient_name": candidate_name,
#                     "action_type": "SIGN",
#                     "signing_order": 0
#                 }
#             ],
#             # you can set extra options:
#             "is_sequential": False,
#             "email_reminders": True,
#         }
#     }

#     # Send the request (upload + send for signature)
#     resp = requests.post(f"{ZOHO_SIGN_URL}/requests", headers=headers, files=files, data={"data": json.dumps(data)})
#     resp.raise_for_status()
#     return JsonResponse(resp.json())

# def create_template(template_name, pdf_path):
#     access_token = get_access_token()   # your OAuth helper
#     url = "https://sign.zoho.in/writer/api/v1/templates"
#     headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
#     files = {
#         "file": open(pdf_path, "rb")
#     }
#     data = {
#         "templates": {
#             "template_name": template_name,
#             "is_sequential": False,          # parallel signing (or True for sequential)
#             "email_reminders": True,
#             "reminder_period": 7,
#             # define roles/potential recipients if you want
#             "actions": [
#                 {
#                     "role": "candidate",
#                     "recipient_name": "",  # you can leave blank here and fill later
#                     "recipient_email": "",
#                     "action_type": "SIGN"
#                 }
#             ]
#         }
#     }
#     payload = {
#         "data": json.dumps(data)
#     }

#     resp = requests.post(url, headers=headers, files=files, data=payload)
#     resp.raise_for_status()
#     return resp.json()

# def send_offer_via_template(template_id, candidate_name, candidate_email, prefill=None):
#     """
#     prefill: optional dict e.g. {"field_text_data": {"CandidateName": "...", "JoiningDate": "..."},
#                                  "field_date_data": {...}, "field_boolean_data": {...}}
#     """
#     access_token = get_access_token()
#     url = f"https://sign.zoho.in/api/v1/templates/{template_id}/createdocument"
#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}"
#     }

#     data = {
#         "templates": {
#             "request_name": f"Offer Letter — {candidate_name}",
#             "actions": [
#                 {
#                     "recipient_name": candidate_name,
#                     "recipient_email": candidate_email,
#                     "action_type": "SIGN",
#                     # optionally role if your template uses roles
#                     "role": "candidate"
#                 }
#             ]
#         }
#     }

#     if prefill:
#         data["templates"]["field_data"] = prefill

#     payload = {
#         "data": json.dumps(data),
#         "is_quicksend": True
#     }

#     resp = requests.post(url, headers=headers, data=payload)
#     resp.raise_for_status()
#     return resp.json()

# ZOHO_SIGN_URL = "https://sign.zoho.in/api/v1"   # India DC

# def send_offer_letter_direct(candidate_name, candidate_email, pdf_path):
#     """
#     Sends an offer letter directly (no template) by uploading a PDF
#     and sending it for signature.
#     """
#     # Get OAuth token from your helper
#     access_token = get_access_token()

#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}"
#     }

#     # File upload
#     files = {
#         "file": open(pdf_path, "rb")
#     }

#     # Zoho requires "data" param as JSON string
#     payload = {
#         "data": json.dumps({
#             "requests": {
#                 "request_name": f"Offer Letter - {candidate_name}",
#                 "is_sequential": False,
#                 "email_reminders": True,
#                 "actions": [
#                     {
#                         "recipient_email": candidate_email,
#                         "recipient_name": candidate_name,
#                         "action_type": "SIGN",
#                         "signing_order": 1
#                     }
#                 ]
#             }
#         })
#     }

#     # Create & send signature request
#     resp = requests.post(
#         f"{ZOHO_SIGN_URL}/requests",
#         headers=headers,
#         files=files,
#         data=payload
#     )

#     # Raise exception if API error
#     resp.raise_for_status()

#     return resp.json()

# def send_draft_request(request_id):
#     access_token = get_access_token()
#     url = f"https://sign.zoho.in/api/v1/requests/{request_id}/submit?testing=true"

#     headers = {
#         "Authorization": f"Zoho-oauthtoken {access_token}",
#         "Content-Type": "application/x-www-form-urlencoded"
#     }

#     # This endpoint must be called with an EMPTY POST body
    
    
#     try:
#         resp = requests.post(url, headers=headers)
#         resp.raise_for_status()
#     except Exception:
#         print("Zoho Error:", resp.text)
#         raise

#     return resp.json()

# def send_offer_letter_doc(candidate_name, candidate_email, pdf_path):
#     # STEP 1 → upload & get draft
#     draft = send_offer_letter_direct(candidate_name, candidate_email, pdf_path)

#     request_id = draft["requests"]["request_id"]

#     # STEP 2 → convert DRAFT → SENT
#     sent_response = send_draft_request(request_id)

#     return {
#         "draft": draft,
#         "sent": sent_response
#     }

def build_offer_prefill(candidate):
    annexure = candidate.salary_annexure

    return {
        "field_text_data": {
            # Candidate Info
            "CandidateName": candidate.candidate_name,
            "CandidateAddress": candidate.address or "",
            "Designation": annexure.designation,
            "Department": candidate.job.mrf.department.name,
            "Location": candidate.job.mrf.location,
            "CTC": str(annexure.ctc_annual),

            # Annexure A
            "DateOfJoining": str(candidate.date_of_joining),
            "ProbationPeriod": "3 Months",
            "NoticePeriodProbation": "15 Days",
            "NoticePeriodConfirmation": "30 Days",

            # Salary Annexure B
            "Basic_DA": str(annexure.basic_da),
            "BasketAllowances": str(annexure.basket_allowances),
            "HRA": str(annexure.hra),
            "MedicalAllowance": str(annexure.medical_allowance),
            "LeaveTravelAllowance": str(annexure.leave_travel_allowance),
            "TelephoneAllowance": str(annexure.telephone_internet_allowance),
            "BooksPeriodicals": str(annexure.books_periodicals),
            "UniformAllowance": str(annexure.uniform_allowance),
            "DriverSalary": str(annexure.driver_salary),
            "CarMaintenance": str(annexure.car_maintenance),
            "MealsAllowance": str(annexure.meals_allowance),
            "SpecialAllowance": str(annexure.special_allowance),
            "ChildrenEducation": str(annexure.children_education_allowance),
            "ConveyanceAllowance": str(annexure.conveyance_allowance),

            "EmployerPF": str(annexure.employer_pf),
            "EmployerInsurance": str(annexure.employer_insurance),
            "EmployerVariable": str(annexure.employer_variable_component),
            "EmployerGratuity": str(annexure.employer_gratuity),
            "EmployerESIC": str(annexure.employer_esic),
            "EmployerTotal": str(annexure.employer_total),

            "EmployeePF": str(annexure.employee_pf),
            "EmployeePT": str(annexure.employee_pt),
            "EmployeeESIC": str(annexure.employee_esic),
            "EmployeeTotal": str(annexure.employee_total),

            "GrossMonthly": str(annexure.gross_monthly),
            "NetMonthly": str(annexure.net_monthly),

            "Notes": annexure.notes or "",
        },

        "field_date_data": {
            "OfferDate": str(candidate.created_at.date()),
            "JoiningDate": str(candidate.date_of_joining),
        }
    }

def send_offer_letter_autofill(template_id, candidate):
    access_token = get_access_token()

    url = f"https://sign.zoho.in/api/v1/templates/{template_id}/createdocument"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    prefill = build_offer_prefill(candidate)

    payload = {
        "data": json.dumps({
            "templates": {
                "request_name": f"Offer Letter - {candidate.candidate_name}",

                "actions": [
                    {
                        "role": "candidate",
                        "recipient_name": candidate.candidate_name,
                        "recipient_email": candidate.email,
                        "action_type": "SIGN"
                    }
                ],

                "field_data": prefill
            }
        }),
        "is_quicksend": True
    }

    resp = requests.post(url, headers=headers, data=payload)
    resp.raise_for_status()

    data = resp.json()

    request_id = data["requests"]["request_id"]
    # Get the first document_id if available
    document_ids = data["requests"].get("document_ids", [])
    document_id = document_ids[0].get("document_id") if document_ids else None

    # ✅ Create OfferDocument
    OfferDocument.objects.create(
        application=candidate,
        zoho_document_id=document_id,
        status="sent",
        sent_at=timezone.now(),
        raw_response=data
    )

    return data

@csrf_exempt
def zoho_sign_webhook(request):

    payload = json.loads(request.body.decode("utf-8"))
    print("Zoho Webhook Payload:", payload)

    event_type = payload.get("notifications", {}).get("operation_type")
    request_data = payload.get("requests", {})

    request_id = request_data.get("request_id")
    document_status = request_data.get("request_status")

    # Access document_id from the first item in document_ids list if present
    document_ids = request_data.get("document_ids", [])
    document_id = document_ids[0].get("document_id") if document_ids else None

    print(f"Zoho Event: {event_type} | Request: {request_id} | Document: {document_id} | Status: {document_status}")

    doc = None
    try:
        # Prefer matching by document_id, fallback to request_id
        if document_id:
            doc = OfferDocument.objects.select_related("application").get(zoho_document_id=document_id)
        
        if not doc:
            raise OfferDocument.DoesNotExist
            
    except OfferDocument.DoesNotExist:
        return JsonResponse({"status": "not_found"})

    application = doc.application

    # -------------------------
    # EVENT MAPPING
    # -------------------------

    if event_type == "RequestViewed":
        doc.status = "viewed"

    elif event_type == "RequestSigningSuccess":
        doc.status = "signed"
        doc.signed_at = timezone.now()

    elif event_type == "RequestCompleted":
        doc.status = "completed"
        doc.completed_at = timezone.now()

        # 🎉 OFFER ACCEPTED
        ok,reason = automation_engine(application,application.status,'offer_accepted')
        if ok:
            doc.save()
            return JsonResponse({"status": "ok"})
        else:
            return JsonResponse({"error":reason})

    elif event_type == "RequestRejected":
        doc.status = "declined"
        reason = payload.get("notifications", {}).get("reason")
        print(f"Extracted Reason: {reason}")
        application.offer_decline_reason = reason
        application.save(update_fields=['offer_decline_reason'])
        ok,reason = automation_engine(application,application.status,'offer_rejected')
        if ok:
            doc.save()
            return JsonResponse({"status": "ok"})
        else:
            return JsonResponse({"error":reason})

    elif event_type == "RequestExpired":
        doc.status = "expired"

    doc.save()

    return JsonResponse({"status": "ok"})

def send_to_zoho_sign(candidate, file_stream, filename,other_signers=[]):
    import os

    access_token = get_access_token()

    url = "https://sign.zoho.in/api/v1/requests"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    actions = [
        {
            "recipient_name": "Nikita Kulabker",
            "recipient_email": "nkulabker@knowcraft.in",
            "action_type": "SIGN",
            "signing_order": 1  # sequential signing
        },
        {
            "recipient_name": candidate.candidate_name,
            "recipient_email": candidate.candidate_email,
            "action_type": "SIGN",
            "signing_order": 2
        },
        {
            "recipient_name": "Hr",
            "recipient_email": "hr@knowcraft.in",
            "action_type": "VIEW",
            "signing_order": 3  # sequential signing
        }
    ]

    # Add other authorized signers (signing order sequentially)
    for idx, signer in enumerate(other_signers, start=4):
        actions.append({
            "recipient_name": signer["name"],
            "recipient_email": signer["email"],
            "action_type": "SIGN",
            "signing_order": idx  # sequential signing
        })

    feedback = aggregate_details_from_feedback(candidate)
    bond_section = ""
    if feedback.get("bond") and str(feedback.get("bond")).lower() not in ['no','na','n/a','-','not applicable']:
        bond_section = """Bond:\nThere will be a twelve-month (12 months) bond, which would be applicable from the Date of Joining.\n"""
    note_message = f"""
Hi {candidate.candidate_name},\n  

We are pleased to offer you the position of {candidate.job.mrf.designation.name} in the {candidate.job.mrf.department.name} team at Knowcraft Analytics Private Limited.\n

Please find your Offer Letter (PDF) attached. It includes details about your compensation, benefits, and terms of employment.\n

Kindly share the signed Offer Letter along with the last page mentioning the compensation package by 48 Hours. After this date, the offer will be automatically revoked.\n\n

General Policies:\n
- 24 earned leaves per year\n
- 10–11 national holidays\n
- Background verification will be conducted by a third party as per company policy\n\n

{bond_section}\n

Work Mode: {feedback.get("work_mode") or "Work From Office"}\n
Date of Joining: {candidate.joining_date.strftime('%d-%m-%Y') if candidate.joining_date else ''} (Reporting time: 10:30 AM)\n
Office Address: {feedback.get('preferred_location') or candidate.job.mrf.location}\n\n

We look forward to welcoming you to the Knowcraft team.\n
Please let us know if you have any questions.\n\n

Warm Regards,\n
Team – HR\n
Knowcraft Analytics Private Limited."""

    payload = {
        "data": json.dumps({
            "requests": {
                "request_name": f"Offer Letter - {candidate.candidate_name}",
                "is_sequential": True,  # True → signers sign in order
                "actions": actions,
                "notes":note_message
            }
        })
    }


    files = {
        "file": (filename, file_stream, "application/pdf")
    }
    try:
        response = requests.post(url, headers=headers, data=payload, files=files)

        data = response.json()
        print("data:",data)
        request_id = data["requests"]["request_id"]
        document_ids = data["requests"].get("document_ids", [])
        document_id = document_ids[0].get("document_id") if document_ids else None
        
        print("data:",data)

        # ✅ Create OfferDocument
        offer= OfferDocument.objects.create(
            application=candidate,
            zoho_document_id=document_id,
            status="sent",
            sent_at=timezone.now(),
            raw_response=data
        )
        if offer:
            automation_engine(candidate,candidate.status,'offer_sent')
            # send_offer_letter_email(candidate)

        return data

    except requests.exceptions.RequestException as e:
        print("HTTP request failed:", e)

    except KeyError:
        print("Unexpected Zoho response:", response.text)

    except Exception as e:
        print("Unable to send the offer letter:",e)

def process_offer_letter(application_document):
    file_field = application_document.created_offer_letter

    if not file_field:
        return

    application = application_document.job_application

    if OfferDocument.objects.filter(application=application).exists():
        return

    with file_field.open("rb") as f:
        filename = file_field.name.split("/")[-1]
        send_to_zoho_sign(application, f, filename)

def aggregate_details_from_feedback(job_application):
    feedbacks = job_application.interview_feedbacks.all()

    result = {
        # ---- Common fields ----
        "notice_period": None,
        "current_ctc": None,
        "expected_ctc": None,
        "remarks": None,
        "bond": None,
        "work_mode": None,
        "preferred_location": None
    }

    for fb in feedbacks:
        # ---- Common fields (first non-null wins) ----
        result["notice_period"] = result["notice_period"] or fb.notice_period
        result["current_ctc"] = result["current_ctc"] or fb.current_ctc
        result["expected_ctc"] = result["expected_ctc"] or fb.expected_ctc
        result["remarks"] = result["remarks"] or fb.comments
        result["bond"] = result["bond"] or fb.bond
        result["work_mode"] = result["work_mode"] or fb.work_mode
        result["preferred_location"] = result['preferred_location'] or fb.preferred_location

    return result

def send_offer_letter_email(candidate):
    from .sender import send_email,send_text
    from django.template import Template, Context
    bond_section = ""
    feedback = aggregate_details_from_feedback(candidate)
    if feedback.get("bond") and str(feedback.get("bond")).lower() not in ['no','na','n/a','-','not applicable']:
        bond_section = """
        <p><b>Bond:</b></p>
        <p>
        There will be a twelve-month (12 months) bond, which would be applicable 
        from the Date of Joining.
        </p>
        """

    # ---------------- HTML Template ----------------
    html_template = """
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
                            <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                <h2 style="margin:0 0 24px 0;color:#1f2937;font-size:26px;font-weight:600;">Offer of Employment</h2>
                                
                                <p style="margin:0 0 18px 0;">Hi {{candidate_name}},</p>
                                
                                <p style="margin:0 0 18px 0;">
                                    We are pleased to offer you the position of <strong>{{designation}}</strong> and we believe that your knowledge, skills, 
                                    and experience would be an ideal fit for our <strong>{{department}}</strong> team.
                                </p>
                                
                                <p style="margin:0 0 18px 0;">
                                    We hope you will enjoy your role and make a significant contribution to the overall success of Knowcraft Analytics Private Limited.
                                </p>
                                
                                <p style="margin:0 0 22px 0;">
                                    Please find the <strong>Offer Letter (PDF)</strong> attached to this email. It contains important details about your compensation, 
                                    benefits, and the terms and conditions of your employment.
                                </p>
                                
                                <p style="margin:0 0 22px 0;">
                                    On acceptance of the offer, kindly send us the <strong>signed Offer Letter</strong> along with the last page mentioning the compensation package 
                                    by <strong style="color:#1f2937;">{{acceptance_deadline}}</strong>. After this date, the offer shall be automatically revoked.
                                </p>
                                
                                <!-- Policies Section -->
                                <h3 style="margin:28px 0 14px 0;color:#1f2937;font-size:18px;font-weight:600;">General Policies</h3>
                                
                                <p style="margin:0 0 8px 0;"><strong>Leave:</strong></p>
                                <ul style="margin:0 0 18px 0;padding-left:22px;">
                                    <li>We provide 24 earned leaves in a year.</li>
                                    <li>10–11 national holidays.</li>
                                </ul>
                                
                                <p style="margin:0 0 8px 0;"><strong>Background Check:</strong></p>
                                <p style="margin:0 0 18px 0;">
                                    There will be a detailed background check by a third party as part of the company policy and client requirement.
                                </p>
                                
                                {{bond_section|safe}}
                                
                                <p style="margin:0 0 8px 0;"><strong>Work Mode:</strong> {{work_mode}}</p>
                                <p style="margin:0 0 8px 0;">
                                    <strong>Date of Joining:</strong> {{joining_date}} (Reporting time 10:30 AM)
                                </p>
                                <p style="margin:0 0 22px 0;">
                                    <strong>Address:</strong> {{office_address}}
                                </p>
                                
                                <p style="margin:0 0 18px 0;">
                                    We look forward to welcoming you to the Knowcraft team.<br>
                                    Let us know if you have any queries.
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
    """

    # ---------------- Context ----------------
    context = {
        "candidate_name": candidate.candidate_name,
        "designation": candidate.job.mrf.designation.name,
        "department": candidate.job.mrf.department.name,
        "acceptance_deadline": "48 hours",
        "joining_date": candidate.joining_date.strftime('%d-%m-%Y') if candidate.joining_date else '',
        "office_address": feedback.get('preferred_location') or candidate.job.mrf.location,
        "work_mode": feedback.get("work_mode") or "Work From Office",
        "bond_section": bond_section,
    }

    template = Template(html_template)
    html_rendered = template.render(Context(context))

    send_email(
        to=candidate.candidate_email,
        subject=f"Offer Letter - {candidate.candidate_name}",
        template=html_rendered,
        text=''
    )
    send_text(to=candidate.candidate_phone,text=f"""
Hi {candidate.candidate_name},  

We are pleased to offer you the position of {candidate.job.mrf.designation.name} in the {candidate.job.mrf.department.name} team at Knowcraft Analytics Private Limited.

Please find your Offer Letter (PDF) attached. It includes details about your compensation, benefits, and terms of employment.

Kindly share the signed Offer Letter along with the last page mentioning the compensation package by 48 Hours. After this date, the offer will be automatically revoked.

General Policies:
- 24 earned leaves per year
- 10–11 national holidays
- Background verification will be conducted by a third party as per company policy

{bond_section}

Work Mode: {feedback.get("work_mode") or "Work From Office"}
Date of Joining: {candidate.joining_date.strftime('%d-%m-%Y') if candidate.joining_date else ''} (Reporting time: 10:30 AM)
Office Address: {feedback.get('preferred_location') or candidate.job.mrf.location}

We look forward to welcoming you to the Knowcraft team.
Please let us know if you have any questions.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited""")
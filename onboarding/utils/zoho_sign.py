import requests, json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .engine import automation_engine
from django.db.models import Q
from django.utils import timezone
from onboarding.models import OfferDocument

ZOHO_SIGN_URL = "https://sign.zoho.in/api/v1"

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

    # Only accept POST
    if request.method != "POST":
        return JsonResponse({"status": "method_not_allowed"}, status=405)

    # -------------------------------------------------------
    # Parse payload: Zoho Sign may send as raw JSON *or* as
    # application/x-www-form-urlencoded with JSON in form
    # fields ("requests", "notifications", etc.).
    # -------------------------------------------------------
    payload = None
    content_type = request.content_type or ""

    try:
        # 1️⃣  Try raw JSON body first
        if "application/json" in content_type:
            payload = json.loads(request.body.decode("utf-8"))
        else:
            # 2️⃣  Form-encoded: reassemble from individual form fields
            #     Zoho posts fields like  requests={...}&notifications={...}
            if request.POST:
                payload = {}
                for key in request.POST:
                    value = request.POST[key]
                    try:
                        payload[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        payload[key] = value

            # 3️⃣  Fallback: try parsing the raw body as JSON anyway
            if not payload:
                payload = json.loads(request.body.decode("utf-8"))

    except Exception as e:
        print(f"Zoho Webhook parse error: {e} | body={request.body[:500]}")
        return JsonResponse({"status": "bad_request", "error": str(e)}, status=400)

    if not payload:
        print("Zoho Webhook: empty payload")
        return JsonResponse({"status": "bad_request", "error": "empty payload"}, status=400)

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
    doc_type = None
    try:
        from onboarding.models import DocumentEsignTask
        # Prefer matching by document_id, fallback to request_id
        if document_id:
            try:
                doc = OfferDocument.objects.select_related("application").get(zoho_document_id=document_id)
                doc_type = 'OfferDocument'
            except OfferDocument.DoesNotExist:
                doc = DocumentEsignTask.objects.select_related("job_application").get(zoho_document_id=document_id)
                doc_type = 'DocumentEsignTask'
        
        if not doc:
            raise Exception("No document found")
            
    except Exception as e:
        print(f"Zoho Webhook: no document found for document_id={document_id}, request_id={request_id}, Error: {e}")
        return JsonResponse({"status": "not_found"})

    application = doc.application if doc_type == 'OfferDocument' else doc.job_application

    # -------------------------
    # EVENT MAPPING
    # -------------------------

    if event_type == "RequestViewed":
        doc.status = "viewed"
        if doc_type == 'DocumentEsignTask':
            doc.viewed_at = timezone.now()

    elif event_type == "RequestSigningSuccess":
        doc.status = "signed"
        doc.signed_at = timezone.now()

    elif event_type == "RequestCompleted":
        doc.status = "completed"
        doc.completed_at = timezone.now()
        
        if doc_type == 'OfferDocument':
            application.offer_accepted_date = doc.completed_at.date()
            application.save()

            # 🎉 OFFER ACCEPTED
            ok,reason = automation_engine(application,application.status,'offer_accepted')
            if ok:
                doc.save()
                return JsonResponse({"status": "ok"})
            else:
                return JsonResponse({"error":reason})
        
        elif doc_type == 'DocumentEsignTask':
            # Persist undertaking sign-off flag (as per summary)
            if getattr(doc, 'doc_type', None) == 'UNDERTAKING':
                application.is_undertaking_signoff_completed = True
                application.save(update_fields=['is_undertaking_signoff_completed'])
                print(f"Undertaking signoff completed for {application.candidate_name}")

    elif event_type == "RequestRejected":
        doc.status = "declined"
        reason = payload.get("notifications", {}).get("reason")
        print(f"Extracted Reason: {reason}")
        
        if doc_type == 'OfferDocument':
            application.offer_decline_reason = reason
            application.save(update_fields=['offer_decline_reason'])
            
            # Save decline reason in the latest ApprovalNote payload
            from onboarding.models import ApprovalNote
            latest_note = ApprovalNote.objects.filter(candidate=application).order_by('-created_at').first()
            if latest_note and isinstance(latest_note.payload, dict):
                latest_note.payload["offer_decline_reason"] = reason
                latest_note.save(update_fields=['payload'])

            ok,reason = automation_engine(application,application.status,'offer_rejected')
            if ok:
                doc.save()
                return JsonResponse({"status": "ok"})
            else:
                return JsonResponse({"error":reason})
        else:
            doc.decline_reason = reason

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

    actions = []
    if candidate.job and candidate.job.is_private:
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
        ]
    else:
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
        bond_section = """
<br><br>
<b>Bond:</b><br>
There will be a twelve-month (12 months) bond, which would be applicable from the Date of Joining.
"""
    
    bond_section_html = bond_section.replace('\n', '<br>')
    note_message = f"""
Hi {candidate.candidate_name},<br>

We are pleased to offer you the position of {candidate.job.mrf.designation.name} 
in the {candidate.job.mrf.department.name} team at Knowcraft Analytics Private Limited.<br>

Please find your Offer Letter (PDF) attached. It includes details about your compensation, 
benefits, and terms of employment.<br>

Kindly share the signed Offer Letter along with the last page mentioning the compensation package within 48 Hours. 
After this date, the offer will be automatically revoked.<br>

<b>General Policies:</b><br>
• 24 earned leaves per year<br>
• 10–11 national holidays<br>
• Background verification will be conducted by a third party as per company policy<br>
{bond_section_html}<br>

<b>Work Mode:</b> {feedback.get('work_mode') or 'Work From Office'}<br>
<b>Date of Joining:</b> {candidate.joining_date.strftime('%d-%m-%Y') if candidate.joining_date else ''} 
(Reporting time: 10:30 AM)<br>
<b>Office Address:</b> {feedback.get('preferred_location') or candidate.job.mrf.location}<br>

We look forward to welcoming you to the Knowcraft team.<br>
Please let us know if you have any questions.<br>

Warm Regards,<br>
Team – HR<br>
Knowcraft Analytics Private Limited.
"""

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
        text='',
        event="offer_letter_zoho_sent",
        email_type="candidate",
        candidate=candidate
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

def recall_zoho_offer(offer_document):
    """
    Recalls an offer document from Zoho Sign using its request_id.
    """
    try:
        raw_response = offer_document.raw_response
        if not raw_response or "requests" not in raw_response:
            print("Cannot recall Zoho offer: No raw_response with request_id found.")
            return False

        request_id = raw_response["requests"].get("request_id")
        if not request_id:
            print("Cannot recall Zoho offer: request_id missing.")
            return False

        access_token = get_access_token()
        url = f"https://sign.zoho.in/api/v1/requests/{request_id}/recall"
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}"
        }

        resp = requests.post(url, headers=headers)
        
        # If successfully recalled, it typically returns 200 OK
        if resp.status_code == 200:
            print(f"Successfully recalled Zoho document {request_id}")
            return True
        else:
            print(f"Failed to recall Zoho document {request_id}: {resp.text}")
            return False
            
    except Exception as e:
        print(f"Exception during Zoho recall: {e}")
        return False

def send_document_to_zoho_sign(document_task):
    """
    Sends one DocumentEsignTask's source_file to Zoho Sign for the candidate to sign.
    Single signer (candidate only) — no HR view/approval chain, since these are
    statutory onboarding forms, not the offer letter.
    """
    if not document_task.source_file:
        print(
            f"No source_file on {document_task.doc_type} for "
            f"{document_task.job_application.candidate_name} — cannot send to Zoho Sign."
        )
        return None
 
    app = document_task.job_application
    access_token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
 
    actions = [
        {
            "recipient_name": app.candidate_name,
            "recipient_email": app.work_email,
            "action_type": "SIGN",
            "signing_order": 1,
        }
    ]
 
    payload = {
        "data": json.dumps({
            "requests": {
                "request_name": f"{document_task.get_doc_type_display()} - {app.candidate_name}",
                "is_sequential": True,
                "actions": actions,
            }
        })
    }
 
    filename = document_task.source_file.name.split("/")[-1]
    files = {"file": (filename, document_task.source_file.open("rb"), "application/pdf")}
 
    try:
        response = requests.post(f"{ZOHO_SIGN_URL}/requests", headers=headers, data=payload, files=files)
        data = response.json()
 
        request_id = data["requests"]["request_id"]
        document_ids = data["requests"].get("document_ids", [])
        document_id = document_ids[0].get("document_id") if document_ids else None
 
        document_task.zoho_request_id = request_id
        document_task.zoho_document_id = document_id
        document_task.status = "sent"
        document_task.sent_at = timezone.now()
        document_task.raw_response = data
        document_task.save(update_fields=[
            "zoho_request_id", "zoho_document_id", "status", "sent_at", "raw_response"
        ])
        return data
 
    except requests.exceptions.RequestException as e:
        print(f"Zoho Sign request failed for {document_task.doc_type} / {app.candidate_name}: {e}")
    except KeyError:
        print(f"Unexpected Zoho Sign response for {document_task.doc_type}: {response.text}")
    except Exception as e:
        print(f"Unable to send {document_task.doc_type} to Zoho Sign: {e}")
 
    return None


def send_undertaking_signoff(app):
    """
    Sends the 'Undertaking Sign-off Document' Zoho Sign template to the candidate.
    Template fields: Date, Crafter, Crafter Code
    The template must be pre-created in Zoho Sign with the name
    'Undertaking Sign-off Document'.

    Uses the template-based approach (createdocument API).
    """
    import logging
    logger = logging.getLogger(__name__)

    # Template ID from Zoho Sign — set this in settings or hardcode after creation.
    template_id = getattr(settings, 'ZOHO_UNDERTAKING_TEMPLATE_ID', None)
    if not template_id:
        logger.error(
            f"ZOHO_UNDERTAKING_TEMPLATE_ID not configured in settings. "
            f"Cannot send undertaking sign-off for {app.candidate_name}."
        )
        return None

    # Resolve Crafter name and code from the OnboardingForm
    crafter_name = app.candidate_name
    crafter_code = ""
    try:
        onboarding_form = app.onboarding_form
        crafter_name = f"{onboarding_form.first_name or ''} {onboarding_form.last_name or ''}".strip() or app.candidate_name
        crafter_code = onboarding_form.crafter_id or ""
    except Exception:
        logger.warning(f"No onboarding form found for {app.candidate_name}. Using defaults.")

    recipient_email = getattr(app, 'work_email', None)
    if not recipient_email:
        logger.warning(f"No work_email for {app.candidate_name}. Skipping undertaking sign-off.")
        return None

    access_token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    # ── Fetch template to get the action_id (required by createdocument API) ──
    try:
        tpl_resp = requests.get(f"https://sign.zoho.in/api/v1/templates/{template_id}", headers=headers)
        tpl_resp.raise_for_status()
        tpl_data = tpl_resp.json().get("templates", {})
        tpl_actions = tpl_data.get("actions", [])
        action_id = tpl_actions[0].get("action_id") if tpl_actions else None
        if not action_id:
            logger.error(f"No action_id found in template {template_id} for {app.candidate_name}.")
            return None
        logger.info(f"Fetched action_id={action_id} from template {template_id}")
    except Exception as e:
        logger.error(f"Failed to fetch Zoho Sign template {template_id}: {e}")
        return None

    url = f"https://sign.zoho.in/api/v1/templates/{template_id}/createdocument"
    today_str = timezone.now().strftime("%b %d %Y")

    note_message = (
        f"Hello Crafter,<br>"
        f"Welcome to Knowcraft Analytics!<br><br>"
        f"As part of your onboarding process, we request you to review and complete the "
        f"sign-off of the onboarding documents shared with you. These documents contain "
        f"important information related to your employment, company policies, and onboarding formalities.<br><br>"
        f"Kindly ensure that all required documents are reviewed and signed at the earliest "
        f"to facilitate the seamless completion of your onboarding process.<br><br>"
        f"Should you have any questions or require assistance while completing the documentation, "
        f"please feel free to reach out.<br><br>"
        f"We look forward to having you on board and wish you a successful journey with Knowcraft Analytics.<br><br>"
        f"Regards,<br>"
        f"Team HR"
    )

    payload = {
        "data": json.dumps({
            "templates": {
                "request_name": f"Undertaking Sign-off - {app.candidate_name}",
                "actions": [
                    {
                        "action_id": action_id,
                        "role": "candidate",
                        "recipient_name": app.candidate_name,
                        "recipient_email": recipient_email,
                        "action_type": "SIGN",
                        "signing_order": 1,
                    }
                ],
                "field_data": {
                    "field_text_data": {
                        "Crafter": crafter_name,
                        "Crafter Code": crafter_code,
                    },
                    "field_date_data": {
                        "Date": today_str,
                    }
                },
                "notes": note_message,
            }
        }),
        "is_quicksend": True,
    }

    try:
        logger.info(f"Sending undertaking sign-off for {app.candidate_name} to {recipient_email}. Template: {template_id}")
        resp = requests.post(url, headers=headers, data=payload)
        if resp.status_code >= 400:
            logger.error(
                f"Zoho Sign createdocument failed for {app.candidate_name}: "
                f"status={resp.status_code}, body={resp.text[:1000]}"
            )
            return None
        data = resp.json()

        request_id = data["requests"]["request_id"]
        document_ids = data["requests"].get("document_ids", [])
        document_id = document_ids[0].get("document_id") if document_ids else None

        # Store as a DocumentEsignTask so the webhook can track signing status
        from onboarding.models import DocumentEsignTask
        DocumentEsignTask.objects.create(
            job_application=app,
            doc_type="UNDERTAKING",
            zoho_request_id=request_id,
            zoho_document_id=document_id,
            status="sent",
            sent_at=timezone.now(),
            raw_response=data,
        )

        logger.info(f"Undertaking sign-off sent to {app.candidate_name} ({recipient_email})")
        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Zoho Sign request failed for undertaking sign-off / {app.candidate_name}: {e}")
    except KeyError:
        logger.error(f"Unexpected Zoho Sign response for undertaking sign-off: {resp.text[:1000]}")
    except Exception as e:
        logger.error(f"Unable to send undertaking sign-off to Zoho Sign: {e}")

    return None

def test_undertaking_signoff(email="zeelsh820@gmail.com", name="Zeelsh Sonagara"):
    """
    Standalone test for the Zoho Sign undertaking sign-off template.
    Run from Django shell:
        from onboarding.utils.zoho_sign import test_undertaking_signoff
        test_undertaking_signoff()
    Or with custom values:
        test_undertaking_signoff(email="test@example.com", name="Test User")
    """
    import logging
    logger = logging.getLogger(__name__)

    template_id = getattr(settings, 'ZOHO_UNDERTAKING_TEMPLATE_ID', None)
    if not template_id:
        print("ERROR: ZOHO_UNDERTAKING_TEMPLATE_ID not set in settings.")
        return

    print(f"Template ID: {template_id}")
    print(f"Recipient: {name} <{email}>")

    access_token = get_access_token()
    if not access_token:
        print("ERROR: Could not get Zoho access token.")
        return

    print(f"Access token: {access_token[:20]}...")

    # ── Step 1: Fetch template details to see roles & fields ──────────
    detail_url = f"https://sign.zoho.in/api/v1/templates/{template_id}"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}

    print("\n── Fetching template details ──")
    action_id = None
    try:
        detail_resp = requests.get(detail_url, headers=headers)
        print(f"Status: {detail_resp.status_code}")
        if detail_resp.status_code < 300:
            raw_json = detail_resp.json()
            tpl = raw_json.get("templates", {})

            # Print full raw actions for debugging
            actions = tpl.get("actions", [])
            print(f"\nTemplate name: {tpl.get('template_name')}")
            print(f"\nFull actions JSON:")
            print(json.dumps(actions, indent=2))

            # Try to extract action_id
            if actions:
                action_id = actions[0].get('action_id')
                print(f"\nExtracted action_id: {action_id}")

            # Show field names
            doc_fields = tpl.get("document_fields", [])
            for doc in doc_fields:
                fields = doc.get("fields", [])
                print(f"Document fields: {[f.get('field_label') or f.get('field_name') for f in fields]}")

            # Also print all top-level keys in the template response
            print(f"\nTop-level keys in template: {list(tpl.keys())}")
        else:
            print(f"Could not fetch template: {detail_resp.text[:500]}")
    except Exception as e:
        print(f"Error fetching template details: {e}")

    if not action_id:
        print("ERROR: Could not fetch action_id from template. Cannot proceed.")
        return None

    # ── Step 2: Attempt createdocument ────────────────────────────────
    print("\n── Sending createdocument request ──")
    url = f"https://sign.zoho.in/api/v1/templates/{template_id}/createdocument"
    today_str = timezone.now().strftime("%b %d %Y")

    payload = {
        "data": json.dumps({
            "templates": {
                "request_name": f"TEST - Undertaking Sign-off - {name}",
                "actions": [
                    {
                        "action_id": action_id,
                        "role": "candidate",
                        "recipient_name": name,
                        "recipient_email": email,
                        "action_type": "SIGN",
                        "signing_order": 1,
                    }
                ],
                "field_data": {
                    "field_text_data": {
                        "Crafter": name,
                        "Crafter Code": "TEST-001",
                    },
                    "field_date_data": {
                        "Date": today_str,
                    }
                },
                "notes": "Test undertaking sign-off from Django shell.",
            }
        }),
        "is_quicksend": True,
    }

    print(f"Payload: {json.dumps(json.loads(payload['data']), indent=2)}")

    try:
        resp = requests.post(url, headers=headers, data=payload)
        print(f"\nResponse status: {resp.status_code}")
        print(f"Response body:\n{resp.text[:2000]}")

        if resp.status_code < 300:
            print("\n✅ SUCCESS — Document sent for signing!")
            return resp.json()
        else:
            print("\n❌ FAILED — See response body above for Zoho's error details.")
            return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

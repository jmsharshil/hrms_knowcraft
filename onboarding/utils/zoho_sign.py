import requests, json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .engine import automation_engine
from django.utils import timezone
from onboarding.models import OfferDocument

ZOHO_SIGN_URL = "https://sign.zoho.com/api/v1"

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

    # ✅ Create OfferDocument
    OfferDocument.objects.create(
        application=candidate,
        zoho_request_id=request_id,
        status="sent",
        sent_at=timezone.now(),
        raw_response=data
    )

    return data

@csrf_exempt
def zoho_sign_webhook(request):

    payload = json.loads(request.body.decode("utf-8"))

    event_type = payload.get("event_type")
    request_data = payload.get("request", {})

    request_id = request_data.get("request_id")
    document_status = request_data.get("request_status")

    print("Zoho Event:", event_type, request_id, document_status)

    try:
        doc = OfferDocument.objects.select_related("application").get(
            zoho_request_id=request_id
        )
    except OfferDocument.DoesNotExist:
        return JsonResponse({"status": "not_found"})

    application = doc.application

    # -------------------------
    # EVENT MAPPING
    # -------------------------

    if event_type == "request.viewed":
        doc.status = "viewed"

    elif event_type == "request.signed":
        doc.status = "signed"
        doc.signed_at = timezone.now()

    elif event_type == "request.completed":
        doc.status = "completed"
        doc.completed_at = timezone.now()

        # 🎉 OFFER ACCEPTED
        ok,reason = automation_engine(application,application.status,'offer_accepted')
        if ok:
            doc.save()
            return JsonResponse({"status": "ok"})
        else:
            return JsonResponse({"error":reason})

    elif event_type == "request.declined":
        doc.status = "declined"
        ok,reason = automation_engine(application,application.status,'offer_rejected')
        if ok:
            doc.save()
            return JsonResponse({"status": "ok"})
        else:
            return JsonResponse({"error":reason})

    elif event_type == "request.expired":
        doc.status = "expired"

    doc.save()

    return JsonResponse({"status": "ok"})
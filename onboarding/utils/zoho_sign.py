import requests, json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

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

def send_offer_letter(request):
    # Example: get candidate data somehow (e.g. POST JSON)
    candidate_email = request.POST["email"]
    candidate_name = request.POST["name"]
    # path to your offer letter PDF (could be generated or static)
    file_path = "/media/offer_letter.pdf"

    token = get_access_token()
    headers = {"Authorization": f"Zoho-oauthtoken {token}"}

    files = {"file": open(file_path, "rb")}
    data = {
        "requests": {
            "request_name": "Offer Letter for " + candidate_name,
            "actions": [
                {
                    "recipient_email": candidate_email,
                    "recipient_name": candidate_name,
                    "action_type": "SIGN",
                    "signing_order": 0
                }
            ],
            # you can set extra options:
            "is_sequential": False,
            "email_reminders": True,
        }
    }

    # Send the request (upload + send for signature)
    resp = requests.post(f"{ZOHO_SIGN_URL}/requests", headers=headers, files=files, data={"data": json.dumps(data)})
    resp.raise_for_status()
    return JsonResponse(resp.json())

def create_template(template_name, pdf_path):
    access_token = get_access_token()   # your OAuth helper
    url = "https://sign.zoho.in/writer/api/v1/templates"
    headers = {"Authorization": f"Zoho-oauthtoken {access_token}"}
    files = {
        "file": open(pdf_path, "rb")
    }
    data = {
        "templates": {
            "template_name": template_name,
            "is_sequential": False,          # parallel signing (or True for sequential)
            "email_reminders": True,
            "reminder_period": 7,
            # define roles/potential recipients if you want
            "actions": [
                {
                    "role": "candidate",
                    "recipient_name": "",  # you can leave blank here and fill later
                    "recipient_email": "",
                    "action_type": "SIGN"
                }
            ]
        }
    }
    payload = {
        "data": json.dumps(data)
    }

    resp = requests.post(url, headers=headers, files=files, data=payload)
    resp.raise_for_status()
    return resp.json()

def send_offer_via_template(template_id, candidate_name, candidate_email, prefill=None):
    """
    prefill: optional dict e.g. {"field_text_data": {"CandidateName": "...", "JoiningDate": "..."},
                                 "field_date_data": {...}, "field_boolean_data": {...}}
    """
    access_token = get_access_token()
    url = f"https://sign.zoho.in/api/v1/templates/{template_id}/createdocument"
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    data = {
        "templates": {
            "request_name": f"Offer Letter — {candidate_name}",
            "actions": [
                {
                    "recipient_name": candidate_name,
                    "recipient_email": candidate_email,
                    "action_type": "SIGN",
                    # optionally role if your template uses roles
                    "role": "candidate"
                }
            ]
        }
    }

    if prefill:
        data["templates"]["field_data"] = prefill

    payload = {
        "data": json.dumps(data),
        "is_quicksend": True
    }

    resp = requests.post(url, headers=headers, data=payload)
    resp.raise_for_status()
    return resp.json()

ZOHO_SIGN_URL = "https://sign.zoho.in/api/v1"   # India DC

def send_offer_letter_direct(candidate_name, candidate_email, pdf_path):
    """
    Sends an offer letter directly (no template) by uploading a PDF
    and sending it for signature.
    """
    # Get OAuth token from your helper
    access_token = get_access_token()

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    # File upload
    files = {
        "file": open(pdf_path, "rb")
    }

    # Zoho requires "data" param as JSON string
    payload = {
        "data": json.dumps({
            "requests": {
                "request_name": f"Offer Letter - {candidate_name}",
                "is_sequential": False,
                "email_reminders": True,
                "actions": [
                    {
                        "recipient_email": candidate_email,
                        "recipient_name": candidate_name,
                        "action_type": "SIGN",
                        "signing_order": 1
                    }
                ]
            }
        })
    }

    # Create & send signature request
    resp = requests.post(
        f"{ZOHO_SIGN_URL}/requests",
        headers=headers,
        files=files,
        data=payload
    )

    # Raise exception if API error
    resp.raise_for_status()

    return resp.json()

def send_draft_request(request_id):
    access_token = get_access_token()
    url = f"https://sign.zoho.in/api/v1/requests/{request_id}/submit?testing=true"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    # This endpoint must be called with an EMPTY POST body
    
    
    try:
        resp = requests.post(url, headers=headers)
        resp.raise_for_status()
    except Exception:
        print("Zoho Error:", resp.text)
        raise

    return resp.json()

def send_offer_letter_doc(candidate_name, candidate_email, pdf_path):
    # STEP 1 → upload & get draft
    draft = send_offer_letter_direct(candidate_name, candidate_email, pdf_path)

    request_id = draft["requests"]["request_id"]

    # STEP 2 → convert DRAFT → SENT
    sent_response = send_draft_request(request_id)

    return {
        "draft": draft,
        "sent": sent_response
    }

def send_offer_letter_autofill(
    template_id,
    candidate_data
):
    """
    candidate_data example:
    {
        "name": "Anand Shah",
        "email": "anand@email.com",
        "address": "Ahmedabad",
        "designation": "Software Engineer",
        "department": "Engineering",
        "location": "Ahmedabad",
        "doj": "01-Apr-2026",
        "ctc": "600000"
    }
    """

    access_token = get_access_token()

    url = f"https://sign.zoho.in/api/v1/templates/{template_id}/createdocument"

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}"
    }

    payload = {
        "data": json.dumps({
            "templates": {
                "request_name": f"Offer Letter - {candidate_data['name']}",

                # 👤 Recipient
                "actions": [
                    {
                        "role": "candidate",
                        "recipient_name": candidate_data["name"],
                        "recipient_email": candidate_data["email"],
                        "action_type": "SIGN"
                    }
                ],

                # 🧠 AUTO-FILL DATA
                "field_data": {
                    "field_text_data": {
                        "CandidateName": candidate_data["name"],
                        "CandidateAddress": candidate_data["address"],
                        "Designation": candidate_data["designation"],
                        "Department": candidate_data["department"],
                        "Location": candidate_data["location"],
                        "CTC": candidate_data["ctc"]
                    },
                    "field_date_data": {
                        "DateOfJoining": candidate_data["doj"]
                    }
                }
            }
        }),
        "is_quicksend": True
    }

    resp = requests.post(url, headers=headers, data=payload)
    resp.raise_for_status()

    return resp.json()

@csrf_exempt
def zoho_sign_webhook(request):
    """
    Receives Zoho Sign webhook events
    """
    payload = json.loads(request.body.decode("utf-8"))

    event_type = payload.get("event_type")
    request_id = payload.get("request", {}).get("request_id")
    document_status = payload.get("request", {}).get("request_status")

    # 🔍 LOG EVERYTHING FIRST
    print("Zoho Event:", event_type, request_id, document_status)

    # ✅ When candidate has signed
    if event_type == "request.signed":
        # mark partially signed
        pass

    # 🎉 When ALL parties signed
    if event_type == "request.completed":
        # Update DB → OFFER ACCEPTED
        # Trigger email / onboarding / HR notification
        pass

    return JsonResponse({"status": "ok"})
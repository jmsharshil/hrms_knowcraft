# Assuming existing content in docusign.py, append this function

from docusign_esign import (Signer, Document, SignHere, Tabs, EnvelopeDefinition,
                            Recipients, RecipientViewRequest, EnvelopesApi, ApiClient)
import os, base64
from jinja2 import Environment, FileSystemLoader
# from weasyprint import HTML
from io import BytesIO
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from docusign_esign.models import EventNotification, EnvelopeEvent
from docusign_esign import CarbonCopy

from onboarding.models import DocuSignOffer

# CLIENT_ID = os.environ['CLIENT_ID']
# USER_ID = os.environ['USER_ID']
# with open("private_key.pem", "rb") as key_file:
#     PRIVATE_KEY = serialization.load_pem_private_key(
#         key_file.read(),
#         password=None,  # or b"your_password" if the key is encrypted
#         backend=default_backend()
#     )

# def get_api_client():
#     api_client = ApiClient()
#     api_client.set_base_path("https://na4.docusign.net/restapi")
#     # api_client.set_oauth_base_path("account-d.docusign.com")
#     api_client.set_oauth_host_name("account.docusign.com")
#     # Read your private RSA key
#     # with open("private_key.txt", "r") as key_file:
#     #     private_key = key_file.read()

#     access_token = api_client.request_jwt_user_token(
#         client_id= CLIENT_ID,
#         user_id= USER_ID,
#         oauth_host_name='account.docusign.com',
#         private_key_bytes=PRIVATE_KEY,
#         expires_in=3600,
#         scopes=['signature', 'impersonation']
#     )

#     api_client.set_default_header("Authorization", f"Bearer {access_token.access_token}")
#     # get account_id
#     user_info = api_client.get_user_info(access_token.access_token)

#     account_id = user_info.accounts[0].account_id  # pick the first account
#     return api_client, account_id


# def create_envelope(api_client, account_id, valuation, is_user_signer, user):
#     envelopes_api = EnvelopesApi(api_client)

#     # check this in production. it should change to production url
#     api_client.host = "https://na4.docusign.net/restapi"
#     # Create the document
#     doc_content = get_document(valuation)

#     document = Document(
#         document_base64=base64.b64encode(doc_content).decode("utf-8"),
#         name="Allanytics 409A Valuation Engagement Proposal",
#         file_extension="pdf",
#         document_id="1"
#     )



#     # Create the signer recipient
#     signer_args = {
#         "email": valuation.email,
#         "name": valuation.full_name,
#         "recipient_id": "1",
#     }

#     if is_user_signer:
#         signer_args["client_user_id"] = valuation.id  # Embedded signing only

#     signer = Signer(**signer_args)
#     # signer = Signer(
#     #     email=signer.email,
#     #     name=signer.full_name,
#     #     recipient_id="1",
#     #     client_user_id=signer.id  # Required for embedded signing
#     # )
#     # if is_user_signer:
#     #     signer["client_user_id"] = signer.id

#     sign_here = SignHere(
#         anchor_string="SIGN_HERE",  # Put this exact text in your PDF
#         anchor_units="pixels",
#         anchor_x_offset="0",
#         anchor_y_offset="0",
#         document_id="1",
#         recipient_id="1",
#         tab_label="SignHereTab",
#     )

#     signer.tabs = Tabs(sign_here_tabs=[sign_here])


#     if is_user_signer:
#         recipients = Recipients(signers=[signer])
#         envelope = EnvelopeDefinition(
#             email_subject="Allanytics – 409A Valuation Engagement Letter for Review & Signature",
#             documents=[document],
#             recipients=recipients,
#             status="sent",
#         )
#     else:
#         # Create the CC recipient
#         cc_recipient = [CarbonCopy(
#             email=user.email,  # CC email
#             name="CC Person",
#             recipient_id="2",  # Must be unique
#             routing_order="1",  # Same time as signer
#             note = "FYI only – you are receiving this document as a CC recipient."
#         ),
#             CarbonCopy(
#                 email="info@allanytics.com",  # CC email
#                 name="Allanytics Team",
#                 recipient_id="3",  # Must be unique
#                 routing_order="1",  # Same time as signer
#                 note="FYI only – you are receiving this document as a CC recipient."
#             ),
#             CarbonCopy(
#                 email="rutwani@allanytics.com",  # CC email
#                 name="Allanytics Team",
#                 recipient_id="4",  # Must be unique
#                 routing_order="1",  # Same time as signer
#                 note="FYI only – you are receiving this document as a CC recipient."
#             ),
#             CarbonCopy(
#                 email="nmall@allanytics.com",  # CC email
#                 name="Allanytics Team",
#                 recipient_id="5",  # Must be unique
#                 routing_order="1",  # Same time as signer
#                 note="FYI only – you are receiving this document as a CC recipient."
#             ),
#             CarbonCopy(
#                 email="hsingh@allanytics.com",  # CC email
#                 name="Allanytics Team",
#                 recipient_id="6",  # Must be unique
#                 routing_order="1",  # Same time as signer
#                 note="FYI only – you are receiving this document as a CC recipient."
#             ),
#         ]
#         recipients = Recipients(signers=[signer], carbon_copies=cc_recipient)
#         event_notification = EventNotification(
#             url=f"https://409a.allanytics.com/docusign/webhook/?v_id={valuation.id}&user={valuation.user.id}",
#             # url=f"https://fairly-whole-hawk.ngrok-free.app/docusign/webhook/?v_id={valuation.id}&user={valuation.user.id}",
#             logging_enabled=True,
#             require_acknowledgment=True,
#             use_soap_interface=False,
#             include_envelope_void_reason=True,
#             include_time_zone=True,
#             include_sender_account_as_custom_field=True,
#             envelope_events=[
#                 EnvelopeEvent(envelope_event_status_code="completed", include_documents=False)
#             ]
#         )
#         envelope = EnvelopeDefinition(
#             email_subject="Allanytics – 409A Valuation Engagement Letter for Review & Signature",
#             documents=[document],
#             recipients=recipients,
#             status="sent",
#             event_notification=event_notification
#         )


#     results = envelopes_api.create_envelope(account_id=account_id, envelope_definition=envelope)
#     return results.envelope_id

# def get_document(signer):
#     env = Environment(loader=FileSystemLoader('docu_sign/templates'))
#     template = env.get_template("docu_sign/409a_Engagement_Letter_full_format.html")
#     data = {
#         "name": signer.full_name,
#         "salutation": signer.salutation,
#         "designation": signer.designation,
#         "company": signer.company,
#         "suite_number": signer.suite_number,
#         "building_name": signer.building_name,
#         "street_name": signer.street_name,
#         "city": signer.city,
#         "state": signer.state,
#         "country": signer.country,
#         "zipcode": signer.zipcode,
#         "date": datetime.today().date().strftime('%B %d, %Y')
#     }
#     # Render HTML with data
#     html_content = template.render(data=data)

#     # Convert HTML to PDF
#     # Convert HTML to PDF in memory
#     pdf_buffer = BytesIO()
#     HTML(string=html_content).write_pdf(target=pdf_buffer)
#     pdf_buffer.seek(0)
#     return pdf_buffer.read()



# def generate_recipient_view(request, api_client, account_id, envelope_id, signer, is_submitted):
#     envelopes_api = EnvelopesApi(api_client)
#     base_url = request.build_absolute_uri('/')[:-1]  # Removes trailing slash

#     view_request = RecipientViewRequest(
#         authentication_method="none",
#         client_user_id=signer.id,  # Same as above
#         recipient_id="1",
#         return_url=f"{base_url}/docusign/callback/{signer.id}?envelopeId={envelope_id}&is_submitted={is_submitted}",  # After signing
#         user_name=signer.full_name,
#         email=signer.email
#     )

#     results = envelopes_api.create_recipient_view(
#         account_id=account_id,
#         envelope_id=envelope_id,
#         recipient_view_request=view_request
#     )

#     return results.url  # This is the embedded signing URL
    
# def send_offer_via_docusign(application):
#     """
#     Send offer letter via DocuSign to candidate.
#     Assumes offer document exists in OfferDocument model.
#     Returns (success, envelope_id or error_msg)
#     """
#     client = get_api_client()  # Existing function
#     if not client:
#         return False, "DocuSign client not initialized"
    
#     api = EnvelopesApi(client)
    
#     # Get offer document (assume OfferDocument has file_path or content)
#     try:
#         offer_doc = application.offerdocument  # Assuming related_name or direct
#         if not offer_doc:
#             return False, "Offer document not found"
#         # Load document - adjust based on storage (e.g., file system or S3)
#         with open(offer_doc.file_path, 'rb') as f:  # Example; adjust
#             doc_content = f.read()
#     except Exception as e:
#         return False, f"Error loading offer: {str(e)}"
    
#     # Create document object
#     document = Document(
#         document_base64=doc_content.encode('utf-8') if isinstance(doc_content, str) else doc_content,
#         name="Offer Letter",
#         file_extension="pdf",
#         document_id="1"
#     )
    
#     # Create signer (candidate)
#     signer = Signer(
#         email=application.candidate_email,  # Assume field exists
#         name=application.candidate_name,
#         recipient_id="1",
#         routing_order="1",
#         # Add tabs for signing fields if needed (e.g., signature, date)
#     )
    
#     # Envelope definition
#     envelope_definition = EnvelopeDefinition(
#         email_subject="Please sign your offer letter",
#         documents=[document],
#         recipients={'signers': [signer]},
#         status="sent"  # Send immediately
#     )
    
#     # Template integration if using: set template_id = settings.DOCUSIGN_OFFER_TEMPLATE_ID
#     # envelope_definition.template_id = settings.DOCUSIGN_OFFER_TEMPLATE_ID
    
#     try:
#         # Send envelope
#         results = api.create_envelope(
#             account_id=client.account_id,  # From client
#             envelope_definition=envelope_definition
#         )
#         envelope_id = results.envelope_id
#         envelope_summary = api.get_envelope(account_id=client.account_id, envelope_id=envelope_id)
        
#         # Create model instance
#         DocuSignOffer.objects.create(
#             job_application=application,
#             envelope_id=envelope_id,
#             status='sent',
#             signer_email=application.candidate_email
#         )
        
#         # Update application with signing link if needed
#         application.offer_signing_link = f"https://demo.docusign.net/Member/Status.aspx?Envelope={envelope_id}"  # Adjust base URL
#         application.save()
        
#         return True, envelope_id
#     except Exception as e:
#         print(f"DocuSign send error for {application.id}: {str(e)}")
#         return False, str(e)


###############################################
from django.conf import settings
from docusign_esign import ApiClient, EnvelopesApi, EnvelopeDefinition, TemplateRole, Tabs, Text, SignHere


class DocuSignService:

    def __init__(self):
        self.api_client = ApiClient()
        self.api_client.set_base_path(settings.DOCUSIGN_BASE_URL)
        self._authenticate()

    def _authenticate(self):
        print("CLIENT_ID:", settings.DOCUSIGN_INTEGRATION_KEY)
        print("USER_ID:", settings.DOCUSIGN_USER_ID)
        print("AUTH_SERVER:", settings.DOCUSIGN_AUTH_SERVER)
        response = self.api_client.request_jwt_user_token(
            client_id=settings.DOCUSIGN_INTEGRATION_KEY,
            user_id=settings.DOCUSIGN_USER_ID,
            oauth_host_name=settings.DOCUSIGN_AUTH_SERVER,
            private_key_bytes=PRIVATE_KEY,
            expires_in=3600,
            scopes=["signature", "impersonation"],
        )
        print(f"DocuSign Auth Response: {response}")

        self.api_client.set_default_header(
            "Authorization", f"Bearer {response.access_token}"
        )
        user_info = self.api_client.get_user_info(response.access_token)

        account = user_info.accounts[0]  # usually first account

        self.account_id = account.account_id
        base_uri = account.base_uri

        # ✅ Set correct base URI
        self.api_client.set_base_path(f"{base_uri}/restapi")
        self.api_client.host = f"{base_uri}/restapi"

        print("✅ Auth successful")
        print("ACCOUNT_ID:", self.account_id)
        print("BASE_URI:", base_uri)
        print("AUTH HEADER:", self.api_client.default_headers)

    def build_tabs(self, application):
        return {
            "text_tabs": [
                {"tabLabel": "candidate_name", "value": application.candidate_name or ""},
                {"tabLabel": "designation", "value": application.job.job_title if application.job else ""},
                {"tabLabel": "department", "value": getattr(application.job.department, "name", "")},
                {"tabLabel": "location", "value": application.location or ""},
                {"tabLabel": "ctc", "value": application.expected_ctc or ""},
                {
                    "tabLabel": "date_of_joining",
                    "value": application.joining_date.strftime("%d-%m-%Y") if application.joining_date else ""
                },
            ]
        }

    # def build_tabs(self, candidate, annexure):
        
    #     data = {
    #         "CandidateName": candidate.candidate_name,
    #         "CandidateAddress": getattr(candidate, "address", "") or "",
    #         "Designation": annexure.designation,
    #         "Department": candidate.job.mrf.department.name if candidate.job and candidate.job.mrf else "",
    #         "Location": candidate.job.mrf.location if candidate.job and candidate.job.mrf else "",
    #         "CTC": str(annexure.ctc_annual),

    #         # Annexure A
    #         "DateOfJoining": str(candidate.joining_date or ""),
    #         "ProbationPeriod": "3 Months",
    #         "NoticePeriodProbation": "15 Days",
    #         "NoticePeriodConfirmation": "30 Days",

    #         # Salary Annexure B
    #         "Basic_DA": str(annexure.basic_da),
    #         "BasketAllowances": str(annexure.basket_allowances),
    #         "HRA": str(annexure.hra),
    #         "MedicalAllowance": str(annexure.medical_allowance),
    #         "LeaveTravelAllowance": str(annexure.leave_travel_allowance),
    #         "TelephoneAllowance": str(annexure.telephone_internet_allowance),
    #         "BooksPeriodicals": str(annexure.books_periodicals),
    #         "UniformAllowance": str(annexure.uniform_allowance),
    #         "DriverSalary": str(annexure.driver_salary),
    #         "CarMaintenance": str(annexure.car_maintenance),
    #         "MealsAllowance": str(annexure.meals_allowance),
    #         "SpecialAllowance": str(annexure.special_allowance),
    #         "ChildrenEducation": str(annexure.children_education_allowance),
    #         "ConveyanceAllowance": str(annexure.conveyance_allowance),

    #         "EmployerPF": str(annexure.employer_pf),
    #         "EmployerInsurance": str(annexure.employer_insurance),
    #         "EmployerVariable": str(annexure.employer_variable_component),
    #         "EmployerGratuity": str(annexure.employer_gratuity),
    #         "EmployerESIC": str(annexure.employer_esic),
    #         "EmployerTotal": str(annexure.employer_total),

    #         "EmployeePF": str(annexure.employee_pf),
    #         "EmployeePT": str(annexure.employee_pt),
    #         "EmployeeESIC": str(annexure.employee_esic),
    #         "EmployeeTotal": str(annexure.employee_total),

    #         "GrossMonthly": str(annexure.gross_monthly),
    #         "NetMonthly": str(annexure.net_monthly),

    #         "Notes": annexure.notes or "",
    #         "OfferDate": str(candidate.created_at.date()),
    #         "JoiningDate": str(candidate.joining_date or ""),
    #     }

    #     text_tabs = []

    #     for key, value in data.items():
    #         text_tabs.append(
    #             Text(
    #                 tab_label=key,
    #                 value=value if value else ""
    #             )
    #         )

    #     return Tabs(text_tabs=text_tabs)

    def send_offer(self, application):
        envelope_api = EnvelopesApi(self.api_client)

        hr_role = TemplateRole(
            email=application.job.assigned_to_internal_hr.email,
            name=application.job.assigned_to_internal_hr.get_full_name(),
            role_name="HR",  # must match template
            routing_order="1",
            tabs=self.build_tabs(application),
        )
        candidate_role = TemplateRole(
            email=application.candidate_email,
            name=application.candidate_name,
            role_name="Candidate",
            routing_order="2",
        )

        envelope = EnvelopeDefinition(
            template_id=settings.DOCUSIGN_TEMPLATE_ID,
            template_roles=[hr_role, candidate_role],
            status="sent",
        )

        response = envelope_api.create_envelope(
            account_id=self.account_id,
            envelope_definition=envelope,
        )

        return response.envelope_id

    # 📦 Bulk send
    def bulk_send(self, applications):
        envelope_ids = []

        for app in applications:
            try:
                envelope_id = self.send_offer_letter(app)
                envelope_ids.append((app.id, envelope_id))
            except Exception as e:
                print(f"Error sending to {app.id}: {str(e)}")

        return envelope_ids
    
    def send_offer_without_template_file(self, application, file):
        envelope_api = EnvelopesApi(self.api_client)
        file.seek(0) 
        # 📄 Read file directly (works for S3, local, etc.)
        file_content = base64.b64encode(file.read()).decode("utf-8")
        file_extension=file.name.split('.')[-1]
        document = Document(
            document_base64=file_content,
            name=f"{application.candidate_name} - Offer Letter",
            file_extension=file_extension,
            document_id="1"
        )

        signer = Signer(
            email=application.candidate_email,
            name=application.candidate_name,
            recipient_id="1",
            routing_order="1",
        )

        tabs = Tabs(
            text_tabs=[
                Text(
                    tab_label="candidate_name",
                    value=application.candidate_name,
                    anchor_string="<<candidate_name>>",
                ),
                Text(
                    tab_label="designation",
                    value=application.job.job_title if application.job else "",
                    anchor_string="<<designation>>",
                ),
                Text(
                    tab_label="ctc",
                    value=application.expected_ctc or "",
                    anchor_string="<<ctc>>",
                ),
            ],
            sign_here_tabs=[
                SignHere(
                    anchor_string="<<sign_here>>",
                )
            ]
        )

        signer.tabs = tabs

        envelope = EnvelopeDefinition(
            email_subject="Offer Letter",
            documents=[document],
            recipients={"signers": [signer]},
            status="sent",
        )

        result = envelope_api.create_envelope(
            account_id=settings.DOCUSIGN_ACCOUNT_ID,
            envelope_definition=envelope,
        )

        return result.envelope_id

def process_offer_letter_docusign(instance):
    try:
        application = instance.job_application

        if not application.candidate_email:
            print("Missing candidate email")
            return

        if not instance.created_offer_letter:
            print("No offer letter file")
            return

        print("🔥 Creating DocuSignService")
        service = DocuSignService()

        file = instance.created_offer_letter

        # envelope_id = service.send_offer_without_template_file(
        #     application,
        #     file
        # )
        envelope_id = service.send_offer(application)
        
        print(f"DocuSign Envelope Created: {envelope_id}")

        DocuSignOffer.objects.create(
            job_application=application,
            envelope_id=envelope_id,
            status="sent",
            signer_email=application.candidate_email
        )

        application.status = "offer_sent"
        application.save()

    except Exception as e:
        print(f"DocuSign Error: {str(e)}")

        # DocuSignOffer.objects.update_or_create(
        #     job_application=instance.job_application,
        #     defaults={
        #         "status": "error",
        #         "signer_email": instance.job_application.candidate_email or ""
        #     }
        # )
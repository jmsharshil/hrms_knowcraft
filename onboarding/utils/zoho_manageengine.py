# onboarding/utils/zoho_manageengine.py

import os
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ManageEngineClient:
    """
    Client to interact with Zoho ManageEngine SDPOD V3 API.
    Handles OAuth2 token refreshing and ticket management.
    """
    
    def __init__(self):
        self.client_id = os.getenv('ZOHO_CLIENT_ID')
        self.client_secret = os.getenv('ZOHO_CLIENT_SECRET')
        self.refresh_token = os.getenv('ZOHO_REFRESH_TOKEN')
        # Defaulting to .in data center, but configurable
        self.auth_url = os.getenv('ZOHO_AUTH_URL', 'https://accounts.zoho.in/oauth/v2/token')
        self.base_url = os.getenv('ZOHO_BASE_URL', 'https://sdpondemand.manageengine.in/api/v3')
        
    def _get_access_token(self):
        """
        Retrieves a fresh access token using the refresh token.
        """
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.error("Zoho ManageEngine credentials are not fully configured in environment variables.")
            return None

        params = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token'
        }
        
        try:
            response = requests.post(self.auth_url, data=params)
            response.raise_for_status()
            data = response.json()
            if 'access_token' in data:
                return data['access_token']
            else:
                logger.error(f"Failed to fetch access token. Response: {data}")
                return None
        except Exception as e:
            logger.exception(f"Error fetching Zoho ManageEngine access token: {e}")
            return None

    def _get_headers(self):
        access_token = self._get_access_token()
        if not access_token:
            return None
        return {
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'Accept': 'application/vnd.manageengine.sdp.v3+json',
            'Content-Type': 'application/x-www-form-urlencoded' # SDP API v3 often takes form data with input_data JSON
        }

    def create_onboarding_ticket(self, application, custom_notes="", form_data=None):
        """
        Creates a service request ticket for candidate onboarding.
        Returns the ticket ID if successful, otherwise None.
        """
        headers = self._get_headers()
        if not headers:
            return None
            
        url = f"{self.base_url}/requests"
        
        form_data = form_data or {}
        
        # Mapping candidate data to standard form fields
        # Note: These exact field names might need adjustment based on the actual ManageEngine template configuration
        
        # Combine descriptions
        form_description = form_data.get("description", "")
        desc = form_description or "Auto-generated onboarding ticket for new hire."
        custom_notes = form_data.get("custom_notes") or custom_notes
        if custom_notes:
            desc += f" Additional Notes: {custom_notes}"
            
        subject = form_data.get("subject") or f"Onboarding Request - {application.candidate_name}"
            
        udf_fields = {
            "udf_sline_1": form_data.get("first_name") or application.candidate_name.split()[0], # First Name
            "udf_sline_2": form_data.get("last_name") or " ".join(application.candidate_name.split()[1:]), # Last Name
            "udf_sline_3": form_data.get("personal_email_id") or application.candidate_email, # Personal Email
            "udf_sline_4": form_data.get("contact_number") or application.candidate_phone, # Contact Number
            "udf_date_1": {"value": str(form_data.get("joining_date") or application.joining_date)} if (form_data.get("joining_date") or application.joining_date) else None,
            "udf_sline_5": form_data.get("designation") or (application.job.designation.name if application.job.designation else "N/A"),
            "udf_sline_6": form_data.get("department") or (application.job.department.name if application.job.department else "N/A"),
            "udf_sline_7": form_data.get("employee_category"),
            "udf_sline_8": form_data.get("center_office_location"),
            "udf_sline_9": form_data.get("mode_for_collecting_assets"),
            "udf_sline_10": form_data.get("team_manager"),
            "udf_sline_11": form_data.get("work_from") or application.job.job_type,
            "udf_sline_12": form_data.get("crafter_id"),
            "udf_sline_13": form_data.get("current_address"),
            "udf_sline_14": form_data.get("assets"),
            "udf_sline_15": form_data.get("site")
        }
        
        # Remove None values so ME does not complain
        udf_fields = {k: v for k, v in udf_fields.items() if v is not None}
        
        input_data = {
            "request": {
                "subject": subject,
                "description": desc,
                "requester": {
                    "name": application.job.mrf.requested_by.name if application.job.mrf.requested_by else "HR Admin"
                },
                # Email to Notify mapped to email_ids to notify (can be internal fields, or mapped here)
                "email_ids_to_notify": [form_data.get("emails_to_notify")] if form_data.get("emails_to_notify") else [],
                "udf_fields": udf_fields,
                # Specify the template name if a specific service request template is used
                "template": {
                    "name": "Candidate Onboarding"
                }
            }
        }
        
        # SDP API v3 requires the JSON payload to be passed as a form parameter named 'input_data'
        import json
        payload = {'input_data': json.dumps(input_data)}
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            data = response.json()
            if 'request' in data and 'id' in data['request']:
                ticket_id = data['request']['id']
                logger.info(f"Successfully created ManageEngine ticket {ticket_id} for candidate {application.candidate_name}")
                return ticket_id
            else:
                logger.error(f"Unexpected response format from ManageEngine: {data}")
                return None
        except Exception as e:
            logger.exception(f"Error creating Zoho ManageEngine ticket: {e}")
            return None

    def update_ticket(self, ticket_id, update_payload, note=None):
        """
        Updates an existing ticket.
        """
        headers = self._get_headers()
        if not headers:
            return False
            
        url = f"{self.base_url}/requests/{ticket_id}"
        
        input_data = {
            "request": update_payload
        }
        
        import json
        payload = {'input_data': json.dumps(input_data)}
        
        try:
            response = requests.put(url, headers=headers, data=payload)
            response.raise_for_status()
            
            # If a note is provided, add it as a conversation/note to the request
            if note:
                self.add_note_to_ticket(ticket_id, note)
                
            return True
        except Exception as e:
            logger.exception(f"Error updating Zoho ManageEngine ticket {ticket_id}: {e}")
            return False
            
    def add_note_to_ticket(self, ticket_id, note_text):
        """
        Adds a note to an existing ticket.
        """
        headers = self._get_headers()
        if not headers:
            return False
            
        url = f"{self.base_url}/requests/{ticket_id}/notes"
        
        input_data = {
            "note": {
                "description": note_text,
                "show_to_requester": True
            }
        }
        
        import json
        payload = {'input_data': json.dumps(input_data)}
        
        try:
            response = requests.post(url, headers=headers, data=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.exception(f"Error adding note to ticket {ticket_id}: {e}")
            return False

    def close_ticket(self, ticket_id):
        """
        Closes the ticket at the end of the onboarding process.
        """
        headers = self._get_headers()
        if not headers:
            return False
            
        # In SDP v3, closing a request usually involves a status update
        # You might also need to provide closure code/comments
        url = f"{self.base_url}/requests/{ticket_id}"
        
        input_data = {
            "request": {
                "status": {
                    "name": "Closed"
                },
                "closure_info": {
                    "requester_ack_resolution": True,
                    "closure_comments": "Automated closure: Onboarding process completed."
                }
            }
        }
        
        import json
        payload = {'input_data': json.dumps(input_data)}
        
        try:
            response = requests.put(url, headers=headers, data=payload)
            response.raise_for_status()
            logger.info(f"Successfully closed ManageEngine ticket {ticket_id}")
            return True
        except Exception as e:
            logger.exception(f"Error closing Zoho ManageEngine ticket {ticket_id}: {e}")
            return False

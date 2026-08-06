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
        self.base_url = os.getenv('ZOHO_BASE_URL', 'https://itsm.knowcraft.in/api/v3')
        
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
        desc = form_description or f"<div class=\"personalize-wrapper\" style=\"font-family: 'PT Sans',Arial,Helvetica,sans-serif, sans-serif;font-size: 13px;\"><div>Onboarding Request for {application.candidate_name}<br></div></div>"
        custom_notes = form_data.get("custom_notes") or custom_notes
        if custom_notes:
            desc += f"<br><div>Additional Notes: {custom_notes}</div>"
            
        subject = form_data.get("subject") or f"Onboarding Request - {application.candidate_name}"
            
        # Date processing for udf_date1 (requires epoch milliseconds)
        joining_date_epoch = None
        j_date = form_data.get("joining_date") or application.joining_date
        if j_date:
            import datetime
            if isinstance(j_date, str):
                try:
                    # try parsing it if it's string
                    j_date = datetime.datetime.strptime(j_date, "%Y-%m-%d").date()
                except ValueError:
                    pass
            if isinstance(j_date, datetime.date) or isinstance(j_date, datetime.datetime):
                # convert to datetime at midnight
                dt = datetime.datetime.combine(j_date, datetime.datetime.min.time())
                joining_date_epoch = int(dt.timestamp() * 1000)

        first_name = form_data.get("first_name")
        last_name = form_data.get("last_name")
        if not first_name:
            name_parts = application.candidate_name.split()
            first_name = name_parts[0] if name_parts else "Unknown"
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        udf_fields = {
            "udf_char5": first_name,
            "udf_char6": last_name,
            "udf_char7": form_data.get("personal_email_id") or application.candidate_email,
            "udf_char8": form_data.get("contact_number") or application.candidate_phone,
            "udf_date1": {"value": joining_date_epoch} if joining_date_epoch else None,
            "udf_char19": form_data.get("designation") or (application.job.designation.name if application.job.designation else "N/A"),
            "udf_char18": form_data.get("department") or (application.job.department.name if application.job.department else "N/A"),
            "udf_char17": form_data.get("employee_category") or "Full Time Employee",
            "udf_char105": form_data.get("center_office_location"),
            "udf_char112": form_data.get("mode_for_collecting_assets"),
            "udf_char113": form_data.get("team_manager"),
            "udf_char140": form_data.get("work_from") or application.job.job_type,
            "udf_char11": form_data.get("crafter_id"),
            "udf_char131": form_data.get("reporting_manager_note") or "Please provide your Reporting Manager's email ID in the \"Emails to Notify\" field.",
            "udf_char15": form_data.get("current_address")
        }
        
        # Remove None values so ME does not complain
        udf_fields = {k: v for k, v in udf_fields.items() if v is not None}
        
        requester_data = {}
        if form_data.get("requester_email_id") or form_data.get("requester_name"):
            if form_data.get("requester_name"):
                requester_data["name"] = form_data.get("requester_name")
            if form_data.get("requester_email_id"):
                requester_data["email_id"] = form_data.get("requester_email_id")
        elif form_data.get("requester_id"):
            requester_data["id"] = form_data.get("requester_id")
        else:
            # Fallback for testing
            requester_data["email_id"] = "jms@knowcraft.in"
            requester_data["name"] = "JMS Admin"

        template_data = {"id": form_data.get("template_id", "5538000000236131")}
        
        request_payload = {
            "subject": subject,
            "description": desc,
            "requester": requester_data,
            "template": template_data,
            "request_template_task_ids": [],
            "request_template_checklist_ids": [],
            "email_ids_to_notify": [form_data.get("emails_to_notify")] if form_data.get("emails_to_notify") else [],
            "udf_fields": udf_fields,
        }
        
        if form_data.get("site"):
            request_payload["site"] = {"id": str(form_data.get("site"))}
            
        assets = form_data.get("assets")
        if assets:
            if isinstance(assets, list):
                request_payload["assets"] = [{"id": str(a)} for a in assets]
            else:
                request_payload["assets"] = [{"id": str(assets)}]

        input_data = {
            "request": request_payload
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
            logger.error(f"Error creating ManageEngine ticket: {e}")
            raise

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

    def get_sites(self):
        """
        Retrieves a list of sites from ManageEngine.
        """
        headers = self._get_headers()
        if not headers:
            return []
            
        url = f"{self.base_url}/sites"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('sites', [])
        except Exception as e:
            logger.exception(f"Error fetching Zoho ManageEngine sites: {e}")
            return []

    def get_assets(self):
        """
        Retrieves a list of assets from ManageEngine.
        """
        headers = self._get_headers()
        if not headers:
            return []
            
        url = f"{self.base_url}/assets"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('assets', [])
        except Exception as e:
            logger.exception(f"Error fetching Zoho ManageEngine assets: {e}")
            return []

    def get_departments(self):
        """
        Retrieves a list of departments from ManageEngine.
        """
        headers = self._get_headers()
        if not headers:
            return []
            
        url = f"{self.base_url}/departments"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('departments', [])
        except Exception as e:
            logger.exception(f"Error fetching Zoho ManageEngine departments: {e}")
            return []

    def get_designations(self):
        """
        Retrieves a list of job titles/designations from ManageEngine.
        """
        headers = self._get_headers()
        if not headers:
            return []
            
        # Try jobtitles first, fallback to job_titles if 404
        url = f"{self.base_url}/jobtitles"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                url = f"{self.base_url}/job_titles"
                response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get('jobtitles', data.get('job_titles', []))
        except Exception as e:
            logger.exception(f"Error fetching Zoho ManageEngine designations: {e}")
            return []

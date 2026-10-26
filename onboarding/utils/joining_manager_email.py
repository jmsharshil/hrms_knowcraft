import logging

import requests
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.utils import DatabaseError
from django.utils.html import escape
from django.utils import timezone

from .sender import send_email

logger = logging.getLogger(__name__)

GRAPH_USERS_URL = "https://graph.microsoft.com/v1.0/users"


def _resolve_teams_user(identifier):
    """Resolve a manager email or exact display name using Microsoft Graph."""
    from slots.graph import get_graph_token

    identifier = (identifier or "").strip()
    if not identifier:
        return None

    try:
        validate_email(identifier)
        is_email = True
    except ValidationError:
        is_email = False

    if not is_email and "@" in identifier:
        logger.warning("Invalid manager email value %r; not searching Teams by name.", identifier)
        return None

    escaped_identifier = identifier.replace("'", "''")
    if is_email:
        filter_value = (
            f"mail eq '{escaped_identifier}' or "
            f"userPrincipalName eq '{escaped_identifier}'"
        )
    else:
        filter_value = f"displayName eq '{escaped_identifier}'"

    response = requests.get(
        GRAPH_USERS_URL,
        headers={"Authorization": f"Bearer {get_graph_token()}"},
        params={
            "$select": "displayName,mail,userPrincipalName",
            "$filter": filter_value,
            "$top": "10",
        },
        timeout=10,
    )
    response.raise_for_status()

    payload = response.json()
    users = payload.get("value") if isinstance(payload, dict) else None
    if not isinstance(users, list):
        logger.error(
            "Microsoft Graph returned an invalid user list while resolving manager value %r.",
            identifier,
        )
        return None

    identifier_key = identifier.casefold()
    matches = []
    for user in users:
        if not isinstance(user, dict):
            logger.warning("Ignoring an invalid Microsoft Graph user entry.")
            continue
        display_name = (user.get("displayName") or "").strip()
        email = (user.get("mail") or user.get("userPrincipalName") or "").strip()
        if is_email:
            email_matches = {
                (user.get("mail") or "").strip().casefold(),
                (user.get("userPrincipalName") or "").strip().casefold(),
            }
            is_match = identifier_key in email_matches
        else:
            is_match = display_name.casefold() == identifier_key

        if is_match and display_name and email:
            try:
                validate_email(email)
            except ValidationError:
                continue
            matches.append({"name": display_name, "email": email})

    if len(matches) != 1:
        logger.warning(
            "Expected one Microsoft 365 user for manager value %r; found %s.",
            identifier,
            len(matches),
        )
        return None

    return matches[0]


def send_joining_day_manager_email(application):
    """Send the joining-day manager notice once all three managers resolve."""
    if getattr(application, "is_joining_day_manager_email_sent", False):
        return False

    job = getattr(application, "job", None)
    if job and job.is_private:
        logger.info(
            "Skipping joining-day manager email for private job %s.",
            job.pk,
        )
        return False

    try:
        onboarding_form = application.onboarding_form
    except AttributeError:
        logger.warning(
            "Cannot send joining-day manager email for application %s: onboarding form is missing.",
            application.pk,
        )
        return False

    candidate_email = (
        getattr(application, "work_email", None)
        or getattr(application, "candidate_email", None)
        or ""
    ).strip()
    if not candidate_email:
        logger.warning(
            "Cannot send joining-day manager email for application %s: candidate email is missing.",
            application.pk,
        )
        return False
    try:
        validate_email(candidate_email)
    except ValidationError:
        logger.warning(
            "Cannot send joining-day manager email for application %s: candidate email is invalid.",
            application.pk,
        )
        return False

    manager_values = {
        "HOD": getattr(application, "hod_email", None),
        "team manager": (
            getattr(application, "team_manager_email", None)
            or (getattr(onboarding_form, "team_manager", None) if onboarding_form else None)
        ),
        "reporting manager": getattr(application, "reporting_manager_email", None),
    }
    missing = [
        role for role, value in manager_values.items()
        if not isinstance(value, str) or not value.strip()
    ]
    if missing:
        logger.info(
            "Joining-day manager email for application %s is waiting for: %s.",
            application.pk,
            ", ".join(missing),
        )
        return False

    resolved = {}
    for role, value in manager_values.items():
        user_match = None
        try:
            user_match = _resolve_teams_user(value)
        except Exception as e:
            logger.warning("Microsoft Graph lookup failed for %s (%s): %s", role, value, e)

        if not user_match:
            # Fallback to names & emails stored directly on application
            fallback_name = ""
            if role == "HOD":
                fallback_name = (getattr(application, "hod_name", None) or "").strip()
            elif role == "team manager":
                fallback_name = (
                    (getattr(application, "team_manager_name", None) or "").strip()
                    or (getattr(application, "reporting_manager_name", None) or "").strip()
                )
            elif role == "reporting manager":
                fallback_name = (getattr(application, "reporting_manager_name", None) or "").strip()

            if not fallback_name:
                fallback_name = value.split("@")[0].replace(".", " ").title() if "@" in value else value

            fallback_email = value if "@" in value else ""
            if not fallback_email and role == "team manager":
                fallback_email = getattr(application, "reporting_manager_email", None) or ""

            if fallback_email:
                user_match = {"name": fallback_name, "email": fallback_email}

        if user_match:
            resolved[role] = user_match

    unresolved = [role for role in manager_values if role not in resolved]
    if unresolved:
        logger.warning(
            "Joining-day manager email for application %s is waiting for valid manager matches: %s.",
            application.pk,
            ", ".join(unresolved),
        )
        return False

    candidate_name = (application.candidate_name or "").strip()
    team_manager_name = (getattr(application, "team_manager_name", None) or "").strip() or resolved["team manager"]["name"]
    reporting_manager_name = (getattr(application, "reporting_manager_name", None) or "").strip() or resolved["reporting manager"]["name"]
    text = (
        f"Hi {candidate_name},\n\n"
        f"Please note that you will be a part of Mr. {team_manager_name}’s team, "
        f"and {reporting_manager_name} will be your Reporting Manager.\n\n"
        "Additionally, all requests related to Attendance Regularization (AR), "
        "Leave applications, Comp Off, Claims, and other approvals in ZingHR "
        "will be reviewed and approved by your Reporting Manager.\n\n"
        "Your designated shift timing will be 8:30 AM to 6:00 PM.\n\n"
        "Please feel free to reach out if you have any questions or require any assistance.\n\n"
        "Regards,"
    )
    html = (
        f"<p>Hi {escape(candidate_name)},</p>"
        f"<p>Please note that you will be a part of Mr. {escape(team_manager_name)}’s team, "
        f"and {escape(reporting_manager_name)} will be your Reporting Manager.</p>"
        "<p>Additionally, all requests related to Attendance Regularization (AR), "
        "Leave applications, Comp Off, Claims, and other approvals in ZingHR "
        "will be reviewed and approved by your Reporting Manager.</p>"
        "<p>Your designated shift timing will be 8:30 AM to 6:00 PM.</p>"
        "<p>Please feel free to reach out if you have any questions or require any assistance.</p>"
        "<p>Regards,</p>"
    )

    recipient_emails = list(dict.fromkeys(
        manager["email"] for manager in resolved.values()
    ))
    subject = f"Joining Day Information - {candidate_name}"
    send_attempted_at = timezone.now()
    send_email(
        to=candidate_email,
        cc=recipient_emails,
        subject=subject,
        text=text,
        template=html,
        use_default_cc=False,
        event="joining_day_manager_notification",
        email_type="candidate",
        candidate=application,
    )

    try:
        from onboarding.models import EmailLog

        email_log = EmailLog.objects.filter(
            candidate=application,
            event="joining_day_manager_notification",
            subject=subject,
            recipient_email=candidate_email,
            sent_at__gte=send_attempted_at,
        ).order_by("-sent_at").first()
    except DatabaseError:
        logger.exception(
            "Could not verify joining-day manager email delivery for application %s.",
            application.pk,
        )
        return False

    return bool(email_log and email_log.status == "sent")

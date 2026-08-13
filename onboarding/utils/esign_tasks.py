# onboarding/utils/esign_tasks.py

import logging
from django.utils import timezone
from onboarding.models import DocumentEsignTask
from .notifications import notify_candidate
from .task_generation import create_task
from .zoho_sign import send_document_to_zoho_sign

logger = logging.getLogger(__name__)

FIXED_DOC_TYPES = [
    "SA", "NDA", "ISMS_1", "ISMS_2", "FORM_2",
    "NOMINATION_INS", "KRA", "FORM_F", "FORM_11", "IT_ASSET",
]


def required_doc_types(app):
    types = list(FIXED_DOC_TYPES)
    if getattr(app, "bond_required", False):
        types.append("BOND")
    return types


def generate_esign_documents(app):
    """
    Creates DocumentEsignTask rows for a candidate (idempotent via get_or_create),
    status='pending' until HR uploads the source file for each. Pulls IT_ASSET
    model/serial from the ME ticket for reference.
    """
    it_asset_meta = {}
    if app.it_ticket_ref:
        try:
            from .zoho_manageengine import ManageEngineClient
            ticket = ManageEngineClient().get_ticket(app.it_ticket_ref)
            it_asset_meta = {
                "model": ticket.get("asset_model"),
                "serial": ticket.get("asset_serial"),
            }
        except Exception as e:
            logger.warning(f"Could not pull asset details from ME ticket {app.it_ticket_ref}: {e}")

    created = []
    for doc_type in required_doc_types(app):
        source_meta = it_asset_meta if doc_type == "IT_ASSET" else {}
        obj, was_created = DocumentEsignTask.objects.get_or_create(
            job_application=app,
            doc_type=doc_type,
            defaults={"generated_at": timezone.now(), "source_meta": source_meta},
        )
        if was_created:
            created.append(obj)
            # HR needs to upload the actual file before this can go to Zoho Sign
            create_task(
                app,
                f"Upload {obj.get_doc_type_display()} for e-signature",
                description="Upload the source PDF to this document's esign task record. "
                             "It will be sent to Zoho Sign automatically once uploaded.",
                due_date=timezone.now().date(),
            )

    logger.info(f"Generated {len(created)} esign doc records for {app.candidate_name}")
    return created


def send_documents_for_esign(app):
    """
    Sends every DocumentEsignTask that has a source_file uploaded and hasn't been
    sent yet. Docs still missing a file are left as 'pending' — the upload task
    created in generate_esign_documents() covers those; nothing to notify yet.
    """
    ready_docs = app.esign_documents.filter(status="ready").exclude(source_file="")
    sent_count = 0

    for doc in ready_docs:
        result = send_document_to_zoho_sign(doc)
        if result:
            sent_count += 1
            notify_candidate(
                app, "esign_request",
                cc=[],
                extra_context={"doc_type": doc.get_doc_type_display()},
            )

    still_missing = app.esign_documents.filter(status="pending", source_file="")
    logger.info(
        f"Sent {sent_count} docs to Zoho Sign for {app.candidate_name}; "
        f"{still_missing.count()} still awaiting file upload."
    )


def send_esign_reminders(app):
    """
    DOJ+1 reminder — only fires if unsigned docs remain (status not in signed/completed).
    """
    unsigned = app.esign_documents.exclude(status__in=["signed", "completed"])
    if not unsigned.exists():
        return

    doc_names = [d.get_doc_type_display() for d in unsigned]
    notify_candidate(app, "esign_reminder", cc=[], extra_context={"pending_docs": doc_names})
    unsigned.filter(status="sent").update(status="reminded", reminder_sent_at=timezone.now())
    logger.info(f"Esign reminder sent to {app.candidate_name} for {len(doc_names)} pending docs")
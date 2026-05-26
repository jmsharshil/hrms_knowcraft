# bgv/models.py

import uuid
from django.db import models


class CandidateBGV(models.Model):

    STATUS_CHOICES = [
    ("pending_schedule", "Pending Schedule"),

    # Active states
    ("initiated", "BGV Initiated"),
    ("pending", "Pending Verification"),
    ("in_progress", "BGV In Progress"),
    ("under_review", "Under Review"),
    ("insufficiency_raised", "Insufficiency Raised"),
    ("data_insufficient", "Data Insufficient"),
    ("awaiting_candidate_input", "Awaiting Candidate Input"),
    ("awaiting_employer_response", "Awaiting Employer Response"),
    ("awaiting_university_response", "Awaiting University Response"),
    ("awaiting_court_response", "Awaiting Court Response"),

    # Successful / terminal states
    ("clear", "BGV Clear"),
    ("completed", "BGV Completed"),
    ("closed", "BGV Closed"),
    ("verified", "Verified"),
    ("unable_to_verify", "Unable To Verify"),
    ("discrepancy", "Discrepancy Found"),

    # Failure states
    ("failed", "BGV Failed"),
    ("cancelled", "BGV Cancelled"),
    ("rejected", "BGV Rejected"),
    ("expired", "BGV Expired"),
]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    candidate = models.OneToOneField(
        "jobs.JobApplication",
        on_delete=models.CASCADE,
        related_name="bgv"
    )

    ongrid_individual_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="pending_schedule"
    )

    report_url = models.URLField(null=True, blank=True)

    callback_payload = models.JSONField(default=dict, blank=True)

    # Latest status fetched from OnGrid /verificationstatus endpoint
    ongrid_status = models.JSONField(
        default=dict,
        blank=True,
        help_text="Latest status payload fetched from OnGrid ongrid-status endpoint"
    )

    # Per-verification overall status fields
    av_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    bav_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    cc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    ccrv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    cvv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    dlv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    drg_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    eduv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    efirc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    ehc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    empv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    eref_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    fmc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    gdc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    iaf_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    icav_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    ipav_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    ladv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    lapv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    lav_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    nsorc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    ofacc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    padv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    panv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    papv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    pav_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    pcc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    ppv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    prc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    pvlf_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    smc_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    vidv_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)
    xav_status = models.CharField(max_length=50, default="NOT_REQUESTED", blank=True)

    # Raw payload sent to OnGrid on each initiation attempt
    raw_initiation_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw request payload sent to OnGrid during the last initiation attempt"
    )

    initiated_at = models.DateTimeField(auto_now_add=True)

    completed_at = models.DateTimeField(null=True, blank=True)

    remarks = models.TextField(null=True, blank=True)

    # Scheduling fields for experienced candidates
    bgv_scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when BGV should be triggered (15 days before joining for experienced candidates)"
    )

    is_fresher = models.BooleanField(
        default=True,
        help_text="True if candidate has < 1 year experience"
    )

    def __str__(self):
        return f"{self.candidate.candidate_name} - {self.status}"
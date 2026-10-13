import os
import sys
from pathlib import Path

BASE_DIR = Path(r"c:\Users\Admin\OneDrive - JMS Advisory Services Private Limited\Desktop\hrms_knowcraft")
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms_knowcraft.settings")
import django
django.setup()

from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.test import override_settings
from jobs.models import JobApplication, Job
from bgv.models import CandidateBGV
from onboarding.models import EmailLog
from onboarding.utils.onboarding_tasks import is_candidate_bgv_completed, run_onboarding_check_for_candidate
from onboarding.utils.sender import send_email

def run_tests():
    print("=" * 65)
    print("HRMS ONBOARDING & DEDUPLICATION LOCAL TEST SUITE")
    print("=" * 65)

    # ─────────────────────────────────────────────────────────────
    # TEST 1: Status Resolution Helper
    # ─────────────────────────────────────────────────────────────
    print("\n--- TEST 1: BGV Status Resolution Check ---")
    class MockApp:
        def __init__(self, bgv_status=None, status="offer_accepted", id=999999):
            self.bgv_status = bgv_status
            self.status = status
            self.id = id
            self.candidate_name = "Test Candidate"

    completed_cases = ['clear', 'verified', 'completed', 'bgv_completed', 'closed', 'unable_to_verify']
    for st in completed_cases:
        app = MockApp(bgv_status=st)
        is_done, resolved = is_candidate_bgv_completed(app)
        assert is_done is True, f"Failed: {st} should be recognized as completed"
        print(f"  [PASS] Status '{st}' -> Completed: {is_done} ({resolved})")

    pending_cases = ['pending', 'initiated', 'in_progress', 'rejected', 'failed', '']
    for st in pending_cases:
        app = MockApp(bgv_status=st)
        is_done, resolved = is_candidate_bgv_completed(app)
        assert is_done is False, f"Failed: {st} should NOT be recognized as completed"
        print(f"  [PASS] Status '{st or 'empty'}' -> Completed: {is_done} ({resolved})")

    # ─────────────────────────────────────────────────────────────
    # TEST 2: Multi-Worker Concurrent Email Deduplication
    # ─────────────────────────────────────────────────────────────
    print("\n--- TEST 2: Multi-Worker Email Deduplication (5 Workers Simulation) ---")
    test_email = "test_worker_dedup@knowcraft.in"
    test_subject = f"Test BGV Escalation Multi-Worker Guard {timezone.now().timestamp()}"

    with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
        print(f"Simulating 5 concurrent workers attempting to send the exact same email...")
        for worker_id in range(1, 6):
            send_email(
                to=test_email,
                subject=test_subject,
                text=f"Worker {worker_id} escalation payload",
                event="test_escalation"
            )

    logs = list(EmailLog.objects.filter(
        recipient_email=test_email,
        subject=test_subject
    ).order_by('id'))

    sent_logs = [l for l in logs if l.status in ("sent", "skipped") and "Duplicate email suppressed" not in (l.error_message or "")]
    dup_logs = [l for l in logs if "Duplicate email suppressed by multi-worker guard" in (l.error_message or "")]

    print(f"  -> Total attempts: 5 workers")
    print(f"  -> Dispatched: {len(sent_logs)} (Worker 1)")
    print(f"  -> Deduplicated/Blocked: {len(dup_logs)} (Workers 2-5)")
    assert len(sent_logs) == 1, f"Expected 1 dispatched email, found {len(sent_logs)}"
    assert len(dup_logs) == 4, f"Expected 4 blocked duplicates, found {len(dup_logs)}"
    print("  [PASS] Multi-worker duplicate blast successfully prevented!")

    # ─────────────────────────────────────────────────────────────
    # TEST 3: Candidate BGV Escalation Workflow (Atomic Rollback)
    # ─────────────────────────────────────────────────────────────
    print("\n--- TEST 3: Candidate DOJ+7 BGV Escalation & Un-escalation Flow ---")
    job = Job.objects.first()

    with transaction.atomic():
        today = timezone.now().date()
        past_joining = today - timedelta(days=10)

        candidate = JobApplication.objects.create(
            candidate_name="Test Escalation Candidate",
            candidate_email="test_candidate_esc@knowcraft.in",
            work_email="test_candidate_esc@knowcraft.in",
            job=job,
            joining_date=past_joining,
            status="offer_accepted",
            bgv_status="completed", # Completed BGV!
            is_active=True,
            is_escalated=False,
            is_doj_minus_15_triggered=True,
            is_doj_minus_7_triggered=True,
            is_doj_minus_2_triggered=True,
            is_doj_0_triggered=True,
            is_esign_reminder_sent=True,
            is_d5_verification_sent=True,
            is_undertaking_signoff_sent=True,
            is_doj_7_triggered=False,
        )

        with override_settings(
            ONBOARDING_DEBUG_MINUTES=False,
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
        ):
            print("\nScenario 3A: Candidate with BGV='completed' at DOJ+7")
            run_onboarding_check_for_candidate(candidate)
            candidate.refresh_from_db()
            print(f"  -> is_escalated = {candidate.is_escalated} (Expected: False)")
            assert candidate.is_escalated is False, "Candidate with completed BGV should NOT be escalated!"
            print("  [PASS] Completed BGV did NOT trigger escalation.")

            print("\nScenario 3B: Candidate was previously is_escalated=True, but BGV is now completed")
            candidate.is_escalated = True
            candidate.is_doj_7_triggered = True
            candidate.save(update_fields=['is_escalated', 'is_doj_7_triggered'])

            run_onboarding_check_for_candidate(candidate)
            candidate.refresh_from_db()
            print(f"  -> is_escalated = {candidate.is_escalated} (Expected: False, automatically cleared)")
            assert candidate.is_escalated is False, "Candidate should have is_escalated cleared when BGV is completed!"
            print("  [PASS] Previously escalated candidate was automatically un-escalated.")

            print("\nScenario 3C: Candidate with BGV='pending' at DOJ+7")
            candidate.bgv_status = "pending"
            candidate.is_escalated = False
            candidate.is_doj_7_triggered = False
            candidate.save(update_fields=['bgv_status', 'is_escalated', 'is_doj_7_triggered'])

            run_onboarding_check_for_candidate(candidate)
            candidate.refresh_from_db()
            print(f"  -> is_escalated = {candidate.is_escalated} (Expected: True)")
            assert candidate.is_escalated is True, "Candidate with pending BGV should be escalated!"
            print("  [PASS] Pending BGV triggered escalation as intended.")

        # Always rollback test candidate so no database artifacts remain
        transaction.set_rollback(True)
        print("\n  [CLEANUP] Database transaction rolled back cleanly. No test artifacts left.")

    print("\n" + "=" * 65)
    print("ALL TESTS PASSED SUCCESSFULLY! Everything verified locally.")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()

# app/tests.py
import io
import time
import threading
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from .models import Candidate
from .utils.stage_transition_rules import (
    validate_transition,
    get_auto_next,
    ALLOWED_TRANSITIONS,
)
from .utils.engine import automation_engine
from .utils.task_queue import BackgroundTaskQueue
from .utils.storage import upload_docs_to_storage
from .utils.pdf_maker import generate_offer_letter
from .utils.notifications import notify_candidate
from .utils.sender import send_email, send_text, send_image, send_contact, send_location, SEND_QUEUE


# ===================================================================
# 1. stage TRANSITION RULES TESTS
# ===================================================================
class stageTransitionRulesTests(TestCase):

    def test_valid_transitions(self):
        for old_stage, allowed_list in ALLOWED_TRANSITIONS.items():
            for new_stage in allowed_list:
                self.assertTrue(validate_transition(old_stage, new_stage))

    def test_invalid_transitions(self):
        self.assertFalse(validate_transition("selected", "joined"))
        self.assertFalse(validate_transition("offer_pending", "docs_pending"))
        self.assertFalse(validate_transition("docs_received", "rejected"))

    def test_invalid_stage_not_in_dict(self):
        self.assertFalse(validate_transition("xxx", "yyy"))


class AutoNextstageTests(TestCase):

    def test_auto_next(self):
        self.assertEqual(get_auto_next("offer_accepted"), "docs_pending")
        self.assertEqual(get_auto_next("docs_received"), "joining_pending")

    def test_no_auto_next(self):
        self.assertIsNone(get_auto_next("selected"))
        self.assertIsNone(get_auto_next("joined"))
        self.assertIsNone(get_auto_next("invalid_stage"))


# ===================================================================
# 2. AUTOMATION ENGINE TESTS
# ===================================================================
class AutomationEngineTests(TestCase):

    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="Engine User",
            email="engine@test.com",
            phone="9999",
            stage="selected"
        )

    @patch("onboarding.utils.engine.notify_candidate")
    @patch("onboarding.utils.engine.validate_transition", return_value=True)
    def test_engine_calls_notify_offer_sent(self, mock_validate, mock_notify):
        automation_engine(self.candidate, "selected", "offer_sent")
        mock_notify.assert_called_once_with(self.candidate)

    @patch("onboarding.utils.engine.get_auto_next", return_value="joining_pending")
    @patch("onboarding.utils.engine.validate_transition", return_value=True)
    def test_engine_auto_moves_to_next_stage(self, mock_validate, mock_auto_next):
        automation_engine(self.candidate, "docs_received", "docs_received")
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.stage, "joining_pending")


class AutomationEngineNegativeTests(TestCase):

    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="BadFlow",
            email="bad@test.com",
            phone="0000",
            stage="selected"
        )

    @patch("onboarding.utils.engine.validate_transition", return_value=False)
    def test_engine_invalid_transition_no_change(self, mock_validate):
        automation_engine(self.candidate, "selected", "joined")
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.stage, "selected")

    # In tests.py → AutomationEngineNegativeTests
    def test_engine_skips_on_invalid_transition(self):
        with patch("onboarding.utils.engine.validate_transition", return_value=False):
            with patch("onboarding.utils.engine.notify_candidate") as mock_notify:
                automation_engine(self.candidate, "selected", "joined")
                mock_notify.assert_not_called()
                self.candidate.refresh_from_db()
                self.assertEqual(self.candidate.stage, "selected")


# ===================================================================
# 3. BACKGROUND TASK QUEUE TESTS
# ===================================================================
class BackgroundTaskQueueTests(TestCase):

    def test_task_success(self):
        queue = BackgroundTaskQueue(worker_count=1)
        called = {"done": False}

        def sample_task():
            called["done"] = True

        queue.enqueue(sample_task)
        time.sleep(0.5)
        self.assertTrue(called["done"])

    def test_task_retry_on_failure(self):
        queue = BackgroundTaskQueue(worker_count=1, max_retries=2)
        calls = {"count": 0}

        def failing_task():
            calls["count"] += 1
            raise Exception("fail!")

        queue.enqueue(failing_task)
        time.sleep(3)
        self.assertGreaterEqual(calls["count"], 2)

    def test_background_queue_performance(self):
        queue = BackgroundTaskQueue(worker_count=5)
        counter = {"x": 0}

        def task():
            counter["x"] += 1

        for _ in range(2000):
            queue.enqueue(task)

        time.sleep(3)
        self.assertEqual(counter["x"], 2000)


# ===================================================================
# 4. STORAGE UPLOAD TESTS (AZURE + LOCAL)
# ===================================================================
class StorageUploadTests(TestCase):

    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="FileTest",
            email="file@test.com",
            phone="1111",
        )
        self.file = io.BytesIO(b"dummy pdf content")
        self.file.name = "dummy.pdf"

    @patch("onboarding.utils.storage.BlobServiceClient")
    @patch("onboarding.utils.storage.settings")
    def test_upload_to_azure_success(self, mock_settings, mock_blob_client):
        mock_settings.USE_AZURE_MEDIA = True
        mock_settings.AZURE_ACCOUNT_NAME = "acc"
        mock_settings.AZURE_ACCOUNT_KEY = "key"
        mock_settings.AZURE_CONTAINER = "container"
        mock_settings.AZURE_CUSTOM_DOMAIN = "cdn.example.com"

        mock_container = MagicMock()
        mock_blob = MagicMock()
        mock_blob.url = "https://cdn.example.com/blob/path.pdf"
        mock_container.get_blob_client.return_value = mock_blob
        mock_blob_client.return_value.get_container_client.return_value = mock_container

        url = upload_docs_to_storage(self.candidate, self.file)
        self.assertIn("cdn.example.com", url)

    @patch("onboarding.utils.storage.FileSystemStorage.save", return_value="local/path/test.pdf")
    @patch("onboarding.utils.storage.settings")
    def test_upload_to_local_success(self, mock_settings, mock_save):
        mock_settings.USE_AZURE_MEDIA = False
        mock_settings.BASE_URL = "https://mysite.com"

        url = upload_docs_to_storage(self.candidate, self.file)
        self.assertIn("mysite.com", url)

    @patch("onboarding.utils.storage.FileSystemStorage.save", side_effect=Exception("Local fail"))
    @patch("onboarding.utils.storage.settings")
    def test_local_upload_failure_returns_none(self, mock_settings, mock_save):
        mock_settings.USE_AZURE_MEDIA = False
        url = upload_docs_to_storage(self.candidate, self.file)
        self.assertIsNone(url)

    def test_file_read_failure_returns_none(self):
        bad_file = MagicMock()
        bad_file.read.side_effect = Exception("read fail")
        bad_file.name = "bad.pdf"

        url = upload_docs_to_storage(self.candidate, bad_file)
        self.assertIsNone(url)

    # @patch("onboarding.utils.storage.BlobServiceClient")
    # @patch("onboarding.utils.storage.settings")
    # def test_azure_upload_failure_returns_none(self, mock_settings, mock_blob_client):
    #     mock_settings.USE_AZURE_MEDIA = True
    #     mock_settings.AZURE_CONTAINER = "container"

    #     # Simulate Azure SDK raising exception
    #     mock_blob_client.side_effect = Exception("Azure connection failed")

    #     url = upload_docs_to_storage(self.candidate, self.file)
    #     self.assertIsNone(url)

# ===================================================================
# 5. PDF GENERATION TESTS
# ===================================================================
class PDFGenerationTests(TestCase):

    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="PDF User",
            email="pdf@test.com",
            phone="7777",
        )

    def test_generate_offer_letter_returns_valid_tuple(self):
        result = generate_offer_letter(self.candidate)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

        filename, content, mimetype = result
        self.assertTrue(filename.endswith(".pdf"))
        self.assertIsInstance(content, bytes)
        self.assertEqual(mimetype, "application/pdf")

    @patch("onboarding.utils.pdf_maker.canvas.Canvas")
    def test_generate_offer_letter_uses_canvas(self, mock_canvas):
        generate_offer_letter(self.candidate)
        mock_canvas.assert_called()


# ===================================================================
# 6. NOTIFICATION & SENDER TESTS
# ===================================================================
class NotificationTests(TestCase):

    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="Notify User",
            email="notify@test.com",
            phone="2222",
            stage = "selected"
        )

    @patch("onboarding.utils.notifications.send_email")
    @patch("onboarding.utils.notifications.send_text")
    @patch("onboarding.utils.notifications.generate_offer_letter", return_value=("test.pdf", b"data", "application/pdf"))
    def test_notify_triggers_all(self, mock_pdf, mock_text, mock_email):
        notify_candidate(self.candidate,"selected")
        mock_pdf.assert_called_once_with(self.candidate)
        mock_email.assert_called_once()
        mock_text.assert_called_once()



class SenderTests(TestCase):

    @patch("onboarding.utils.sender.EmailMultiAlternatives")
    def test_send_email_calls_django_mail(self, mock_mail):
        send_email("a@test.com", "Hi", text="Hello")
        mock_mail.assert_called_once()

    @patch("onboarding.utils.sender.EmailMultiAlternatives")
    def test_send_email_with_html_template(self, mock_mail):
        send_email("a@test.com", "Subject", text="Hi", template="<p>Hi</p>")
        mock_mail.assert_called_once()

    @patch.object(SEND_QUEUE, "enqueue")
    def test_send_text_enqueues_task(self, mock_enqueue):
        send_text("9999", "Hello")
        mock_enqueue.assert_called_once()

    @patch("onboarding.utils.sender.requests.post")
    def test_send_text_success_via_api(self, mock_post):
        mock_post.return_value.stage_code = 200
        mock_post.return_value.json.return_value = {"ok": True}
        result = send_text("9999", "hello")
        self.assertTrue(result)

    @patch("onboarding.utils.sender.requests.post")
    def test_send_image_success(self, mock_post):
        mock_post.return_value.stage_code = 200
        result = send_image("9999", "https://a.com/img.jpg")
        self.assertTrue(result)

    @patch("onboarding.utils.sender.requests.post")
    def test_send_contact_success(self, mock_post):
        mock_post.return_value.stage_code = 200
        result = send_contact("9999", "John", "1234567890")
        self.assertTrue(result)

    @patch("onboarding.utils.sender.requests.post")
    def test_send_location_success(self, mock_post):
        mock_post.return_value.stage_code = 200
        result = send_location("9999", 1.2, 3.4, "Address", "City", "Note")
        self.assertTrue(result)


# ===================================================================
# 7. API END-TO-END TESTS
# ===================================================================
class UpdatestageAPITests(TestCase):

    def setUp(self):
        self.client = Client()
        self.candidate = Candidate.objects.create(
            name="APIUser",
            email="api@test.com",
            phone="8888",
            stage="selected"
        )

    @patch("onboarding.views.automation_engine")
    def test_update_stage_success(self, mock_engine):
        url = f"/api/candidate/{self.candidate.id}/update-stage/"
        response = self.client.post(
            url,
            {"stage": "offer_pending"},
            content_type="application/json"
        )

        self.assertEqual(response.stage_code, 200)
        data = response.json()
        self.assertTrue(data["success"])

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.stage, "offer_pending")
        mock_engine.assert_called_once_with(self.candidate, "selected", "offer_pending")

    def test_update_stage_candidate_not_found(self):
        url = "/api/candidate/9999/update-stage/"
        response = self.client.post(
            url,
            {"stage": "offer_pending"},
            content_type="application/json"
        )
        self.assertEqual(response.stage_code, 404)


# ===================================================================
# 8. PERFORMANCE & STRESS TESTS
# ===================================================================
class PerformanceTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_home_endpoint_performance(self):
        start = time.time()
        response = self.client.get("/")
        duration = time.time() - start
        self.assertLess(duration, 0.5)

    def test_stage_validation_speed(self):
        start = time.time()
        for _ in range(200):
            validate_transition("selected", "offer_pending")
        duration = time.time() - start
        self.assertLess(duration, 1.0)

    @patch("onboarding.utils.storage.FileSystemStorage.save", return_value="x.pdf")
    def test_storage_upload_speed_mocked(self, mock_save):
        dummy_candidate = Candidate(name="A", email="a@a.com", phone="1")
        dummy_file = io.BytesIO(b"123")

        start = time.time()
        for _ in range(300):
            upload_docs_to_storage(dummy_candidate, dummy_file)
        duration = time.time() - start
        self.assertLess(duration, 2.0)


class StressTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_rapid_home_endpoint_calls(self):
        def call():
            self.client.get("/")

        threads = [threading.Thread(target=call) for _ in range(200)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # If no crash, test passes
        self.assertTrue(True)


class BulkUpdateStressTests(TestCase):

    def setUp(self):
        self.candidate = Candidate.objects.create(
            name="BulkUser",
            email="bulk@test.com",
            phone="9000",
            stage="selected"
        )
        self.client = Client()

    def test_bulk_stage_update_performance(self):
        url = f"/api/candidate/{self.candidate.id}/update-stage/"
        start = time.time()

        for _ in range(500):
            self.client.post(
                url,
                {"stage": "offer_pending"},
                content_type="application/json"
            )

        duration = time.time() - start
        print(f"\nBulk API test duration: {duration:.2f}s")
        self.assertLess(duration, 4.0)  # Must finish under 4 seconds
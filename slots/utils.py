from datetime import datetime, timedelta, time, timezone
from .models import Slot
from slots.models import Interviewer

def generate_week_slots():
    """
    Generate Monday–Friday slots between 9AM–6PM with 30-minute duration.
    Only create if not already created.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    start_hour = 9
    end_hour = 18
    slot_duration = 30  # minutes

    all_interviewers = Interviewer.objects.all()  # LOAD ALL INTERVIEWERS


    for day_offset in range(0, 7):
        day = today + timedelta(days=day_offset)

        # Only Monday–Friday
        if day.weekday() >= 5:  # Saturday/Sunday
            continue

        # Build initial slot start time
        slot_start = datetime.combine(day, time(start_hour, 0, 0, tzinfo=timezone.utc))
        slot_end_time = time(end_hour, 0, 0)

        while slot_start.time() < slot_end_time:
            slot_end = slot_start + timedelta(minutes=slot_duration)

            # Create only if not exists
            slot, created = Slot.objects.get_or_create(
                start=slot_start,
                end=slot_end
            )

            # Only assign interviewers when slot is newly created
            if created:
                slot.interviewers.set(all_interviewers)

            slot_start = slot_end

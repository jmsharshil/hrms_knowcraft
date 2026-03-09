# slots/availability.py
from datetime import datetime, timedelta, time,timezone
from zoneinfo import ZoneInfo
from slots.models import Slot
import uuid

IST = ZoneInfo("Asia/Kolkata")

WORK_START = time(0, 1)
WORK_END = time(23, 59)
SLOT_MINUTES = 30

# Temporary slot storage (RAM)
TEMP_SLOT_STORAGE = {}

# def generate_free_slots_for_day(busy_slots, day):
#     """Return free slots with slot_id from DB."""
#     free = []

#     day_start = datetime.combine(day, WORK_START, IST)
#     day_end = datetime.combine(day, WORK_END, IST)

#     slot_start = day_start

#     while slot_start < day_end:
#         slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)

#         overlap = False
#         for b in busy_slots:
#             if b["start"] < slot_end and b["end"] > slot_start:
#                 overlap = True
#                 break

#         if not overlap:
#             # find slot in database (UTC stored)
#             slot_db = Slot.objects.filter(
#                 start=slot_start.astimezone(timezone.utc),
#                 end=slot_end.astimezone(timezone.utc)
#             ).first()

#             free.append({
#                 "slot_id": str(uuid.uuid4()),
#                 "start": slot_start,
#                 "end": slot_end
#             })

#         slot_start = slot_end

#     return free

def generate_free_slots_for_day(busy_slots, day, interviewer, duration=30):
    """Return free slots with real slot_id from DB."""
    free = []

    day_start = datetime.combine(day, WORK_START, IST)
    day_end = datetime.combine(day, WORK_END, IST)

    slot_start = day_start

    while slot_start < day_end:
        slot_end = slot_start + timedelta(minutes=duration)

        # check overlap
        overlap = any(b["start"] < slot_end and b["end"] > slot_start for b in busy_slots)

        if not overlap:

            # First: get or create slot WITHOUT interviewer (M2M cannot be used here)
            slot_db, created = Slot.objects.get_or_create(
                start=slot_start.astimezone(timezone.utc),
                end=slot_end.astimezone(timezone.utc)
            )

            # Second: assign interviewer via M2M
            slot_db.interviewers.add(interviewer)

            free.append({
                "slot_id": str(slot_db.id),
                "start": slot_start,
                "end": slot_end
            })

        slot_start += timedelta(minutes=30)  # keep grid consistent

    return free






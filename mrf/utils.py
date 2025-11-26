# # mrf/utils.py
# from datetime import time
# from django.utils import timezone
# from .models import MRF

# def is_after_5pm(dt):
#     dt_local = dt.astimezone(timezone.get_default_timezone())
#     return dt_local.time() > time(17, 0, 0)

# def determine_next_working_date_if_after_5pm(dt):
#     # returns date
#     if is_after_5pm(dt):
#         from .models import next_working_day
#         return next_working_day(dt)
#     return dt.astimezone(timezone.get_default_timezone()).date()

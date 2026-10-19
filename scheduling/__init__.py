"""Configure, but do not start, the daily background PKI refresh scheduler.

The scheduler uses UTC; the cron trigger is created without an explicit timezone
and therefore uses the local timezone.
"""

from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from scheduling import refresh_scheduler

scheduler = BackgroundScheduler(timezone=ZoneInfo("UTC"))
cron_expression = CronTrigger.from_crontab("0 0 * * *")
scheduler.add_job(refresh_scheduler.refresh_pki, cron_expression)

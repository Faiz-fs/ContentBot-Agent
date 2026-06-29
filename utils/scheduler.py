"""
utils/scheduler.py — Background automation
FIXED: Duplicate guard, IST timezone logging, graceful error handling
  • 6:00 AM IST: auto-generate reel + carousel drafts → review queue
  • 0:00 AM IST: advance day
"""
import datetime, threading, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    import pytz
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False

from config import (
    DATA_DIR, REVIEW_FILE, ENGAGEMENT_FILE, INSIGHTS_FILE,
    load_json, save_json, append_json_list,
    get_today_cycle, advance_day,
)

_scheduler = None
_lock = threading.Lock()
IST = pytz.timezone("Asia/Kolkata") if SCHEDULER_AVAILABLE else None


def _log(msg: str):
    """Log with IST timestamp."""
    log_file = DATA_DIR / "scheduler.log"
    ts = datetime.datetime.now(IST).isoformat() if IST else datetime.datetime.now().isoformat()
    with open(log_file, "a") as f:
        f.write(f"{ts}  {msg}\n")


def _auto_generate_job():
    """6 AM: generate reel + carousel for today's theme, queue for review."""
    from utils.ai_engine import generate_reel_script, generate_carousel
    theme      = get_today_cycle()
    engagement = load_json(ENGAGEMENT_FILE, [])
    insights   = load_json(INSIGHTS_FILE, {})

    # GUARD: Check if today's content already exists (prevent duplicates on restart)
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    review_queue = load_json(REVIEW_FILE, [])
    existing_today = [
        r for r in review_queue
        if r.get("generated_at", "").startswith(today_str) and r.get("auto_generated")
    ]
    if existing_today:
        _log(f"Skip auto-gen: {len(existing_today)} items already generated today for {theme['theme']}")
        return

    for fn, ctype in [(generate_reel_script, "reel"), (generate_carousel, "carousel")]:
        try:
            data, model = fn(theme, "", "", engagement, insights)
            data.update({
                "status":         "pending_review",
                "auto_generated": True,
                "model_used":     model,
                "generated_at":   str(datetime.datetime.now()),
                "id":             f"{ctype}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            })
            append_json_list(REVIEW_FILE, data)
            _log(f"Auto-generated {ctype} for {theme['theme']} using {model}")
        except Exception as e:
            _log(f"Auto-gen {ctype} failed: {e}")


def _midnight_job():
    """Advance day at midnight."""
    advanced = advance_day()
    if advanced:
        theme = get_today_cycle()
        _log(f"Day advanced → {theme['theme']}")
    else:
        _log("Day advance skipped (already advanced today)")


def start_scheduler():
    global _scheduler
    if not SCHEDULER_AVAILABLE:
        _log("APScheduler not installed. Auto-generation disabled.")
        return False
    with _lock:
        if _scheduler and _scheduler.running:
            return True
        _scheduler = BackgroundScheduler(timezone=IST)
        _scheduler.add_job(_midnight_job,      CronTrigger(hour=0,  minute=0,  timezone=IST), id="midnight",   replace_existing=True)
        _scheduler.add_job(_auto_generate_job, CronTrigger(hour=6,  minute=0,  timezone=IST), id="auto_gen",   replace_existing=True)
        _scheduler.start()
        _log("Scheduler started.")
        return True


def stop_scheduler():
    global _scheduler
    with _lock:
        if _scheduler and _scheduler.running:
            _scheduler.shutdown(wait=False)
            _log("Scheduler stopped.")


def trigger_now():
    """Manually fire the auto-generate job in background."""
    t = threading.Thread(target=_auto_generate_job, daemon=True)
    t.start()


def get_next_runs() -> list:
    if not _scheduler or not _scheduler.running:
        return []
    return [{"id": j.id, "next_run": str(j.next_run_time)} for j in _scheduler.get_jobs()]


def is_running() -> bool:
    return bool(_scheduler and _scheduler.running)

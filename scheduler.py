import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import database as db
import asyncio

scheduler = AsyncIOScheduler()
bot_instance = None
loop = None


def set_bot(bot, event_loop):
    global bot_instance, loop
    bot_instance = bot
    loop = event_loop


def parse_weekly_schedule(value):
    days_map = {
        "mon": "mon",
        "tue": "tue",
        "wed": "wed",
        "thu": "thu",
        "fri": "fri",
        "sat": "sat",
        "sun": "sun",
        "monday": "mon",
        "tuesday": "tue",
        "wednesday": "wed",
        "thursday": "thu",
        "friday": "fri",
        "saturday": "sat",
        "sunday": "sun",
    }

    parts = value.strip().split()
    if len(parts) != 2:
        raise ValueError("Weekly schedule format: 'days time' (e.g. 'mon,wed,fri 14:00')")

    days_str, time_str = parts
    day_names = [days_map.get(d.strip().lower()) for d in days_str.split(",")]
    day_names = [d for d in day_names if d]

    if not day_names:
        raise ValueError(f"Invalid day names in: {days_str}")

    hour, minute = time_str.replace(".", ":").split(":")

    return {
        "day_of_week": ",".join(day_names),
        "hour": int(hour),
        "minute": int(minute),
    }


async def fire_announcement(announcement_id):
    if bot_instance is None:
        print(f"[Scheduler] Bot not ready, skipping announcement {announcement_id}")
        return

    announcement = db.get_announcement(announcement_id)
    if not announcement or not announcement["enabled"]:
        return

    try:
        channel = await bot_instance.fetch_channel(int(announcement["channel_id"]))
        message_text = announcement["message"]

        if announcement["last_message_id"]:
            try:
                existing_msg = await channel.fetch_message(int(announcement["last_message_id"]))
                await existing_msg.edit(content=message_text)
                print(f"[Scheduler] Edited message {announcement['last_message_id']} in channel {announcement['channel_id']}")
                return
            except Exception:
                pass

        new_msg = await channel.send(message_text)
        db.set_last_message_id(announcement_id, str(new_msg.id))
        print(f"[Scheduler] Sent new message {new_msg.id} in channel {announcement['channel_id']}")
    except Exception as e:
        print(f"[Scheduler] Error firing announcement {announcement_id}: {e}")


def load_jobs():
    scheduler.remove_all_jobs()
    announcements = db.get_announcements(enabled_only=True)

    for ann in announcements:
        try:
            if ann["schedule_type"] == "weekly":
                cron_args = parse_weekly_schedule(ann["schedule_value"])
                trigger = CronTrigger(**cron_args, timezone=os.environ.get("TIMEZONE", "UTC"))
            elif ann["schedule_type"] == "cron":
                parts = ann["schedule_value"].split()
                if len(parts) != 5:
                    print(f"[Scheduler] Invalid cron expression for announcement {ann['id']}: {ann['schedule_value']}")
                    continue
                minute, hour, day, month, day_of_week = parts
                trigger = CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week,
                    timezone=os.environ.get("TIMEZONE", "UTC"),
                )
            else:
                continue

            scheduler.add_job(
                fire_announcement,
                trigger,
                args=[ann["id"]],
                id=f"ann_{ann['id']}",
                replace_existing=True,
                name=f"Announcement #{ann['id']}",
            )
            print(f"[Scheduler] Loaded job for announcement {ann['id']} ({ann['schedule_type']}: {ann['schedule_value']})")
        except Exception as e:
            print(f"[Scheduler] Error loading job for announcement {ann['id']}: {e}")


def reload_job(announcement_id):
    try:
        scheduler.remove_job(f"ann_{announcement_id}")
    except Exception:
        pass
    ann = db.get_announcement(announcement_id)
    if not ann or not ann["enabled"]:
        return

    try:
        if ann["schedule_type"] == "weekly":
            cron_args = parse_weekly_schedule(ann["schedule_value"])
            trigger = CronTrigger(**cron_args, timezone=os.environ.get("TIMEZONE", "UTC"))
        elif ann["schedule_type"] == "cron":
            parts = ann["schedule_value"].split()
            if len(parts) != 5:
                return
            minute, hour, day, month, day_of_week = parts
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week,
                timezone=os.environ.get("TIMEZONE", "UTC"),
            )
        else:
            return

        scheduler.add_job(
            fire_announcement,
            trigger,
            args=[announcement_id],
            id=f"ann_{announcement_id}",
            replace_existing=True,
            name=f"Announcement #{announcement_id}",
        )
        print(f"[Scheduler] Reloaded job for announcement {announcement_id}")
    except Exception as e:
        print(f"[Scheduler] Error reloading job for announcement {announcement_id}: {e}")


def remove_job(announcement_id):
    try:
        scheduler.remove_job(f"ann_{announcement_id}")
        print(f"[Scheduler] Removed job for announcement {announcement_id}")
    except Exception:
        pass

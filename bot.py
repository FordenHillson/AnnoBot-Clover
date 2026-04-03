import os
import asyncio
import threading
from dotenv import load_dotenv

load_dotenv()

import discord
from discord.ext import commands
from flask import Flask

import database as db
import scheduler

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-to-a-random-secret")

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "admin")
PORT = int(os.environ.get("PORT", 10000))


@bot.event
async def on_ready():
    print(f"[Bot] Logged in as {bot.user}")
    db.init_db()
    scheduler.set_bot(bot, asyncio.get_event_loop())
    scheduler.scheduler.start()
    scheduler.load_jobs()
    print("[Bot] Scheduler initialized and jobs loaded")


@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def sync(ctx):
    scheduler.load_jobs()
    await ctx.send("Scheduler jobs reloaded from database.")


def run_flask():
    app.run(host="0.0.0.0", port=PORT)


@app.route("/")
def index():
    from flask import redirect, url_for, session, request
    if not session.get("authenticated"):
        return redirect(url_for("login"))
    announcements = db.get_announcements()
    return render_template("dashboard.html", announcements=announcements)


@app.route("/login", methods=["GET", "POST"])
def login():
    from flask import redirect, url_for, session, request
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == DASHBOARD_PASSWORD:
            session["authenticated"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="Incorrect password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    from flask import redirect, url_for, session
    session.pop("authenticated", None)
    return redirect(url_for("login"))


@app.route("/announcement/new", methods=["GET", "POST"])
def new_announcement():
    from flask import redirect, url_for, session, request
    if not session.get("authenticated"):
        return redirect(url_for("login"))

    if request.method == "POST":
        channel_id = request.form.get("channel_id", "")
        message = request.form.get("message", "")
        schedule_type = request.form.get("schedule_type", "weekly")
        schedule_value = request.form.get("schedule_value", "")

        if not all([channel_id, message, schedule_type, schedule_value]):
            return render_template(
                "announcement_form.html",
                error="All fields are required",
                schedule_type=schedule_type,
            )

        ann_id = db.create_announcement(channel_id, message, schedule_type, schedule_value)
        scheduler.reload_job(ann_id)
        return redirect(url_for("index"))

    return render_template("announcement_form.html")


@app.route("/announcement/<int:announcement_id>/edit", methods=["GET", "POST"])
def edit_announcement(announcement_id):
    from flask import redirect, url_for, session, request
    if not session.get("authenticated"):
        return redirect(url_for("login"))

    ann = db.get_announcement(announcement_id)
    if not ann:
        return "Announcement not found", 404

    if request.method == "POST":
        channel_id = request.form.get("channel_id", "")
        message = request.form.get("message", "")
        schedule_type = request.form.get("schedule_type", "weekly")
        schedule_value = request.form.get("schedule_value", "")

        if not all([channel_id, message, schedule_type, schedule_value]):
            return render_template(
                "announcement_form.html",
                announcement=ann,
                error="All fields are required",
                schedule_type=schedule_type,
            )

        db.update_announcement(announcement_id, channel_id, message, schedule_type, schedule_value)
        scheduler.reload_job(announcement_id)
        return redirect(url_for("index"))

    return render_template("announcement_form.html", announcement=ann)


@app.route("/announcement/<int:announcement_id>/delete", methods=["POST"])
def delete_announcement(announcement_id):
    from flask import redirect, url_for, session, request
    if not session.get("authenticated"):
        return redirect(url_for("login"))

    scheduler.remove_job(announcement_id)
    db.delete_announcement(announcement_id)
    return redirect(url_for("index"))


@app.route("/announcement/<int:announcement_id>/toggle", methods=["POST"])
def toggle_announcement(announcement_id):
    from flask import redirect, url_for, session, request
    if not session.get("authenticated"):
        return redirect(url_for("login"))

    db.toggle_announcement(announcement_id)
    ann = db.get_announcement(announcement_id)
    if ann and ann["enabled"]:
        scheduler.reload_job(announcement_id)
    else:
        scheduler.remove_job(announcement_id)
    return redirect(url_for("index"))


def render_template(*args, **kwargs):
    from flask import render_template as _render
    return _render(*args, **kwargs)


def main():
    db.init_db()
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("[Main] Flask dashboard started")
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()

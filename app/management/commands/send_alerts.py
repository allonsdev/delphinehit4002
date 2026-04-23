"""
management/commands/send_alerts.py

Sends alert emails for:
  - Overdue alerts (OVERDUE)
  - Due-soon alerts (ABOUT_TO_DUE)
  - DUE alerts (first run / startup mode)
  - Geofence breaches detected from latest LocationLog

Run on startup via AppConfig.ready() or add to a cron / celery beat task:
    python manage.py send_alerts
    python manage.py send_alerts --mode=geofence
    python manage.py send_alerts --mode=health
    python manage.py send_alerts --mode=all        (default)
"""

import json
from datetime import date, timedelta

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils.timezone import now

from app.models import (
    Alert, Animal, LocationLog, MovementEvent, Paddock, User,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _recipients():
    """Return the configured alert recipient list (falls back to empty)."""
    return getattr(settings, "ALERT_EMAIL_RECIPIENTS", [])


def _send(subject: str, html: str, text: str):
    recipients = _recipients()
    if not recipients:
        return False
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipients,
    )
    msg.attach_alternative(html, "text/html")
    try:
        msg.send()
        return True
    except Exception as exc:
        print(f"[send_alerts] Email error: {exc}")
        return False


def _ts():
    return now().strftime("%d %b %Y, %H:%M")


# ---------------------------------------------------------------------------
# Alert email sender (vaccinations, treatments, vet visits, health risks)
# ---------------------------------------------------------------------------

def send_health_alerts(mode: str = "startup", stdout=None):
    """
    mode='startup'  → send DUE + ABOUT_TO_DUE + OVERDUE
    mode='due'      → send only ABOUT_TO_DUE + OVERDUE
    """
    statuses = ["OVERDUE", "ABOUT_TO_DUE"]
    if mode == "startup":
        statuses.append("DUE")

    alerts = list(
        Alert.objects
        .filter(is_resolved=False, status__in=statuses)
        .select_related("animal")
        .order_by("status", "due_date")
    )

    if not alerts:
        if stdout:
            stdout.write("  No health alerts to send.")
        return

    # Group by alert_type for nicer email subjects
    by_type: dict[str, list] = {}
    for a in alerts:
        by_type.setdefault(a.alert_type, []).append(a)

    overdue_count = sum(1 for a in alerts if a.status == "OVERDUE")
    soon_count    = sum(1 for a in alerts if a.status == "ABOUT_TO_DUE")
    total_count   = len(alerts)

    ctx = {
        "alerts":        alerts,
        "alert_type":    alerts[0].alert_type if len(by_type) == 1 else "MIXED",
        "overdue_count": overdue_count,
        "soon_count":    soon_count,
        "total_count":   total_count,
        "timestamp":     _ts(),
        "BASE_URL":      getattr(settings, "BASE_URL", ""),
    }

    html = render_to_string("alert_email.html", ctx)
    text = (
        f"{total_count} farm alert(s) need your attention: "
        f"{overdue_count} overdue, {soon_count} due soon. "
        f"Log in to the Smart Farm dashboard for details."
    )

    subject_parts = []
    if overdue_count:
        subject_parts.append(f"{overdue_count} Overdue")
    if soon_count:
        subject_parts.append(f"{soon_count} Due Soon")
    subject = "🔔 Smart Farm Alerts — " + ", ".join(subject_parts) if subject_parts else "🔔 Smart Farm — Pending Alerts"

    sent = _send(subject, html, text)
    if stdout:
        stdout.write(f"  Health alerts: {total_count} alerts → email {'sent' if sent else 'FAILED (check settings)'}.")


# ---------------------------------------------------------------------------
# Geofence breach sender
# ---------------------------------------------------------------------------

def send_geofence_alerts(stdout=None):
    """
    Re-checks all ACTIVE animals against their paddock's smart_radius.
    Creates / resolves Alert records and emails breaching animals.
    Also called from farm_map_view but this version also records Alerts.
    """
    animals = (
        Animal.objects
        .filter(status="ACTIVE", current_paddock__isnull=False)
        .select_related("current_paddock", "farm")
    )

    outside_animals = []

    for animal in animals:
        last_log = (
            LocationLog.objects
            .filter(animal=animal)
            .order_by("-timestamp")
            .first()
        )
        if not last_log:
            continue

        paddock  = animal.current_paddock
        in_fence = paddock.contains(last_log.latitude, last_log.longitude)

        if not in_fence:
            outside_animals.append({
                "tag":     animal.tag_number,
                "paddock": paddock.name,
                "lat":     last_log.latitude,
                "lon":     last_log.longitude,
            })
            # Create an Alert record if one doesn't already exist for today
            Alert.objects.get_or_create(
                animal=animal,
                alert_type="GEOFENCE_BREACH",
                is_resolved=False,
                defaults={
                    "message": (
                        f"{animal.tag_number} detected outside {paddock.name} "
                        f"at ({last_log.latitude:.5f}, {last_log.longitude:.5f})"
                    ),
                    "status": "OVERDUE",
                },
            )
        else:
            # Auto-resolve stale geofence alerts if animal is back inside
            Alert.objects.filter(
                animal=animal,
                alert_type="GEOFENCE_BREACH",
                is_resolved=False,
            ).update(is_resolved=True, resolved_at=now())

    if not outside_animals:
        if stdout:
            stdout.write("  No geofence breaches detected.")
        return

    ctx = {
        "alert_type":    "GEOFENCE_BREACH",
        "animals":       outside_animals,
        "breach_count":  len(outside_animals),
        "timestamp":     _ts(),
        "BASE_URL":      getattr(settings, "BASE_URL", ""),
        # dummy values for template context (not used in geofence branch)
        "alerts":        [],
        "overdue_count": 0,
        "soon_count":    0,
        "total_count":   0,
    }

    html    = render_to_string("alert_email.html", ctx)
    text    = (
        f"{len(outside_animals)} animal(s) detected outside paddock boundaries. "
        "Check the Smart Farm dashboard immediately."
    )
    subject = f"🚨 Geofence Breach — {len(outside_animals)} Animal(s) Outside Boundary"

    sent = _send(subject, html, text)
    if stdout:
        stdout.write(
            f"  Geofence: {len(outside_animals)} breach(es) → email {'sent' if sent else 'FAILED'}."
        )


# ---------------------------------------------------------------------------
# Head-movement tracker — updates MovementEvent from LocationLog changes
# ---------------------------------------------------------------------------

def track_head_movements(stdout=None):
    """
    Compares each active animal's latest GPS fix against its stored
    current_paddock.  When the animal is inside a *different* paddock,
    a MovementEvent is created and current_paddock is updated.

    Run this after new GPS logs arrive (e.g. via webhook / celery).
    """
    animals = (
        Animal.objects
        .filter(status="ACTIVE")
        .select_related("current_paddock", "farm")
    )
    all_paddocks = list(Paddock.objects.all())
    moved_count  = 0

    for animal in animals:
        last_log = (
            LocationLog.objects
            .filter(animal=animal)
            .order_by("-timestamp")
            .first()
        )
        if not last_log:
            continue

        lat, lon = last_log.latitude, last_log.longitude

        # Find which paddock (if any) now contains this animal
        new_paddock = None
        for p in all_paddocks:
            if p.contains(lat, lon):
                new_paddock = p
                break

        if new_paddock is None:
            continue  # animal is in open range — not inside any known paddock

        old_paddock = animal.current_paddock

        if old_paddock != new_paddock:
            # Record the movement
            system_user = User.objects.filter(is_superuser=True).first()
            MovementEvent.objects.create(
                animal=animal,
                from_paddock=old_paddock,
                to_paddock=new_paddock,
                moved_by=system_user,
            )
            # Update the animal's location
            animal.current_paddock = new_paddock
            animal.save(update_fields=["current_paddock"])
            moved_count += 1

            if stdout:
                stdout.write(
                    f"  Moved {animal.tag_number}: "
                    f"{old_paddock.name if old_paddock else 'None'} → {new_paddock.name}"
                )

    if stdout and moved_count == 0:
        stdout.write("  No head movements detected.")
    elif stdout:
        stdout.write(f"  {moved_count} animal(s) movement(s) recorded.")


# ---------------------------------------------------------------------------
# Management command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Send farm alert emails and track animal movements"

    def add_arguments(self, parser):
        parser.add_argument(
            "--mode",
            choices=["all", "health", "geofence", "movements"],
            default="all",
            help=(
                "all       = health alerts + geofence + movement tracking (default)\n"
                "health    = vaccination / treatment / vet visit alerts only\n"
                "geofence  = geofence breach check only\n"
                "movements = head-movement tracker only\n"
            ),
        )
        parser.add_argument(
            "--startup",
            action="store_true",
            default=False,
            help="Include DUE (not just ABOUT_TO_DUE/OVERDUE) alerts — use on app startup",
        )

    def handle(self, *args, **options):
        mode    = options["mode"]
        startup = options["startup"]

        self.stdout.write(self.style.SUCCESS(
            f"\n[send_alerts] mode={mode}, startup={startup}, time={_ts()}\n"
        ))

        if mode in ("all", "health"):
            self.stdout.write("→ Health alerts…")
            send_health_alerts(
                mode="startup" if startup else "due",
                stdout=self.stdout,
            )

        if mode in ("all", "geofence"):
            self.stdout.write("→ Geofence check…")
            send_geofence_alerts(stdout=self.stdout)

        if mode in ("all", "movements"):
            self.stdout.write("→ Head-movement tracker…")
            track_head_movements(stdout=self.stdout)

        self.stdout.write(self.style.SUCCESS("\n[send_alerts] Done.\n"))
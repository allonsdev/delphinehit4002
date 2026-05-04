"""
apps.py  —  place this in your app directory.

On Django startup this does TWO things in background threads:

  1. Alert checks  (existing)
       - Sends health alerts (DUE / ABOUT_TO_DUE / OVERDUE)
       - Checks geofence breaches
       - Tracks head movements

  2. GPS tracker  (new)
       - Reads NEO-6M data from Arduino over serial (default COM3)
       - Writes a LocationLog row for animal ZW0068 every 30 seconds

Settings (all optional — defaults shown):
    GPS_SERIAL_PORT  = "COM3"
    GPS_SERIAL_BAUD  = 9600
    GPS_LOG_INTERVAL = 30        # seconds

Add 'app.apps.AppConfig' to INSTALLED_APPS in settings.py.
"""

import os
import threading

from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Smart Farm"

    # Exposed so tests can stop the GPS thread cleanly
    _gps_stop_event: threading.Event = None

    def ready(self):
        """
        Called once when Django finishes loading all models.
        Runs alert checks AND the GPS tracker in background daemon threads.
        """
        # Prevent duplicate execution in Django dev-server reload
        if os.environ.get("RUN_MAIN") == "true":
            return

        # ── 1. Alert checks ───────────────────────────────────────────────────
        t_alerts = threading.Thread(
            target=self._startup_alerts,
            name="startup-alerts",
            daemon=True,
        )
        t_alerts.start()

        # ── 2. GPS tracker ────────────────────────────────────────────────────
        # Skip if Django is already running the gps_tracker management command
        if not _is_manage_command("gps_tracker"):
            from django.conf import settings

            port     = getattr(settings, "GPS_SERIAL_PORT",  "COM3")
            baud     = getattr(settings, "GPS_SERIAL_BAUD",  9600)
            interval = getattr(settings, "GPS_LOG_INTERVAL", 30)

            stop_event = threading.Event()
            AppConfig._gps_stop_event = stop_event

            t_gps = threading.Thread(
                target=self._run_gps_tracker,
                kwargs=dict(port=port, baud=baud, interval=interval, stop_event=stop_event),
                name="gps-tracker",
                daemon=True,
            )
            t_gps.start()

    # ── Alert thread ──────────────────────────────────────────────────────────

    @staticmethod
    def _startup_alerts():
        """Run in background thread — import inside to avoid AppRegistryNotReady."""
        try:
            from app.management.commands.send_alerts import (
                send_health_alerts,
                send_geofence_alerts,
                track_head_movements,
            )
            send_health_alerts(mode="startup")
            send_geofence_alerts()
            track_head_movements()
        except Exception as exc:
            import traceback
            print(f"[AppConfig.ready] Alert startup error: {exc}")
            traceback.print_exc()

    # ── GPS tracker thread ────────────────────────────────────────────────────

    @staticmethod
    def _run_gps_tracker(port: str, baud: int, interval: int, stop_event: threading.Event):
        """Run in background thread — import inside to avoid AppRegistryNotReady."""
        try:
            from app.management.commands.gps_tracker import run_tracker
            run_tracker(port=port, baud=baud, interval=interval, stop_event=stop_event)
        except Exception as exc:
            import traceback
            print(f"[AppConfig.ready] GPS tracker error: {exc}")
            traceback.print_exc()


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _is_manage_command(name: str) -> bool:
    """Return True when Django is running 'manage.py <name>' directly."""
    import sys
    args = sys.argv
    return len(args) >= 2 and args[1] == name
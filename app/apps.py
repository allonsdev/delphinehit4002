"""
apps.py — place this in your app directory.

Fires alerts on server startup:
  - Sends health alerts (DUE / ABOUT_TO_DUE / OVERDUE)
  - Checks geofence breaches
  - Tracks head movements

Add 'app.apps.AppConfig' to INSTALLED_APPS in settings.py.
"""

import os
import threading
from django.apps import AppConfig as DjangoAppConfig


class AppConfig(DjangoAppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Smart Farm"

    def ready(self):
        """
        Called once when Django finishes loading all models.
        Runs alert checks in a background thread to avoid blocking startup.
        """
        # Prevent duplicate execution (Django dev server reload issue)
        if os.environ.get("RUN_MAIN") == "true" or not os.environ.get("RUN_MAIN"):
            t = threading.Thread(target=self._startup_alerts, daemon=True)
            t.start()

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
"""
management/commands/gps_tracker.py

Reads GPS data from an Arduino (NEO-6M) over serial,
and saves a LocationLog entry for animal ZW0068 every 30 seconds.

Usage (manual):
    python manage.py gps_tracker
    python manage.py gps_tracker --port /dev/ttyUSB1 --baud 115200 --interval 60

Auto-start on Django launch:
    See apps.py  ──  GpsTrackerConfig.ready() spawns this in a background thread.
"""

import re
import time
import logging
import threading
from datetime import datetime, timezone

import serial
from django.core.management.base import BaseCommand
from django.db import close_old_connections

logger = logging.getLogger(__name__)

# ── Regex to match the [RAW] lines emitted by the Arduino sketch ──────────────
# Example line:  [RAW] LAT: -17.829412 | LON: 31.052362 | SAT: 9
RAW_PATTERN = re.compile(
    r"\[RAW\]\s+LAT:\s*(?P<lat>-?\d+\.\d+)\s*\|\s*LON:\s*(?P<lon>-?\d+\.\d+)"
    r"\s*\|\s*SAT:\s*(?P<sat>\d+)"
)

# ── Tag of the animal we are tracking ─────────────────────────────────────────
ANIMAL_TAG = "ZW0068"


def _get_animal():
    """Fetch the Animal object once; raises if not found."""
    from app.models import Animal          # adjust app label if needed
    return Animal.objects.get(tag_number=ANIMAL_TAG)


def _save_location(animal, lat: float, lon: float, speed=None):
    """Persist one LocationLog row."""
    from app.models import LocationLog     # adjust app label if needed
    close_old_connections()                     # safe for long-running threads
    log = LocationLog.objects.create(
        animal=animal,
        timestamp=datetime.now(tz=timezone.utc),
        latitude=lat,
        longitude=lon,
        speed=speed,
    )
    logger.info(
        "LocationLog saved → animal=%s  lat=%.6f  lon=%.6f  id=%s",
        ANIMAL_TAG, lat, lon, log.pk,
    )
    return log


def run_tracker(port: str, baud: int, interval: int, stop_event: threading.Event):
    """
    Core loop – intended to run in a background thread or as a management command.

    :param port:        Serial port, e.g. '/dev/ttyUSB0' or 'COM3'
    :param baud:        Baud rate matching the Arduino sketch (default 9600)
    :param interval:    Seconds between LocationLog writes (default 30)
    :param stop_event:  threading.Event; set it to gracefully stop the loop
    """
    from app.views import GPS_STATE   # adjust app label
    GPS_STATE["sats"] = sat
    GPS_STATE["has_fix"] = True
    logger.info("GPS tracker starting  port=%s  baud=%d  interval=%ds", port, baud, interval)

    # ── Resolve animal once ───────────────────────────────────────────────────
    try:
        animal = _get_animal()
        logger.info("Tracking animal: %s (%s)", animal.tag_number, animal.breed)
    except Exception as exc:
        logger.error("Cannot find animal %s: %s — tracker aborted.", ANIMAL_TAG, exc)
        return

    # ── Open serial port with retry ───────────────────────────────────────────
    ser = None
    while not stop_event.is_set():
        try:
            ser = serial.Serial(port, baud, timeout=2)
            logger.info("Serial port %s opened.", port)
            break
        except serial.SerialException as exc:
            logger.warning("Cannot open %s: %s — retrying in 10 s …", port, exc)
            stop_event.wait(10)

    if ser is None:
        return

    # ── Tracking state ────────────────────────────────────────────────────────
    last_saved_time = 0.0          # epoch seconds of the last successful save
    latest_lat = None
    latest_lon = None
    has_fix = False

    try:
        while not stop_event.is_set():
            # --- Read one line from Arduino -----------------------------------
            try:
                raw_bytes = ser.readline()
            except serial.SerialException as exc:
                logger.error("Serial read error: %s — reconnecting …", exc)
                ser.close()
                stop_event.wait(5)
                try:
                    ser = serial.Serial(port, baud, timeout=2)
                except serial.SerialException:
                    pass
                continue

            try:
                line = raw_bytes.decode("ascii", errors="ignore").strip()
            except Exception:
                continue

            if not line:
                continue

            # --- Parse [RAW] GPS line ----------------------------------------
            m = RAW_PATTERN.search(line)
            if m:
                lat = float(m.group("lat"))
                lon = float(m.group("lon"))
                sat = int(m.group("sat"))

                # Reject the TinyGPS sentinel value for "no fix"
                if abs(lat) > 90 or abs(lon) > 180:
                    continue

                latest_lat = lat
                latest_lon = lon

                if not has_fix:
                    has_fix = True
                    logger.info("GPS fix acquired  sat=%d", sat)

                # --- Save at most once per interval --------------------------
                now = time.monotonic()
                if now - last_saved_time >= interval:
                    try:
                        _save_location(animal, latest_lat, latest_lon)
                        last_saved_time = now
                    except Exception as exc:
                        logger.exception("Failed to save LocationLog: %s", exc)

            # --- Detect fix lost (Arduino prints this line) ------------------
            elif "GPS FIX LOST" in line and has_fix:
                has_fix = False
                logger.warning("GPS fix lost.")

    finally:
        ser.close()
        logger.info("GPS tracker stopped.")


# ─────────────────────────────────────────────────────────────────────────────
# Management command entry point
# ─────────────────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Read GPS data from Arduino serial and log location for animal ZW0068."

    def add_arguments(self, parser):
        parser.add_argument(
            "--port",
            default="/dev/ttyUSB0",
            help="Serial port the Arduino is connected to (default: /dev/ttyUSB0)",
        )
        parser.add_argument(
            "--baud",
            type=int,
            default=9600,
            help="Baud rate (must match Arduino sketch, default: 9600)",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=30,
            help="Seconds between LocationLog writes (default: 30)",
        )

    def handle(self, *args, **options):
        stop_event = threading.Event()
        try:
            run_tracker(
                port=options["port"],
                baud=options["baud"],
                interval=options["interval"],
                stop_event=stop_event,
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Interrupted — stopping tracker."))
            stop_event.set()
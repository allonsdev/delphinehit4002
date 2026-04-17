"""
management/commands/seed_farm_data.py

Run with:
    python manage.py seed_farm_data
    python manage.py seed_farm_data --clear   # wipe first
"""
import math
import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import now

from app.models import (
    Alert, Animal, BreedingEvent, CalvingRecord, Device,
    DiseaseRecord, EnvironmentalLog, ExpenseRecord, Farm,
    FeedType, FeedingRecord, Geofence, HealthObservation,
    LactationRecord, LocationLog, MovementEvent, Paddock,
    ProductionRecord, ReproductiveStatus, SaleRecord,
    TreatmentRecord, User, VaccinationRecord,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def rand_date(years_back_min=0, years_back_max=5):
    days = random.randint(years_back_min * 365, years_back_max * 365)
    return date.today() - timedelta(days=days)


def rand_coord(lat, lon, radius_deg=0.008):
    """Random point inside a circle of radius_deg degrees."""
    angle = random.uniform(0, 2 * math.pi)
    r = random.uniform(0, radius_deg)
    return round(lat + r * math.cos(angle), 6), round(lon + r * math.sin(angle), 6)


# ---------------------------------------------------------------------------
# Master data tables
# ---------------------------------------------------------------------------

FARMS = [
    {
        "name": "Mazowe Valley Dairy",
        "location_name": "Mazowe Road, Harare North",
        "latitude": -17.6821,
        "longitude": 31.0123,
        "size_hectares": 420.0,
        "owner": "Tendai Moyo",
    },
    {
        "name": "Borrowdale Beef Estate",
        "location_name": "Borrowdale, Harare",
        "latitude": -17.7421,
        "longitude": 31.1050,
        "size_hectares": 310.0,
        "owner": "Chipo Nhemachena",
    },
    {
        "name": "Norton Grasslands Farm",
        "location_name": "Norton, Mashonaland West",
        "latitude": -17.8847,
        "longitude": 30.7003,
        "size_hectares": 580.0,
        "owner": "Farai Mutasa",
    },
]

# paddocks per farm: [name, capacity, lat_offset, lon_offset, radius_m]
PADDOCKS = {
    "Mazowe Valley Dairy": [
        ("North Pasture",    25,  0.010,  0.005, 420),
        ("South Pasture",    25, -0.010,  0.005, 420),
        ("East Grazing",     20,  0.002,  0.015, 380),
        ("West Grazing",     20,  0.002, -0.015, 380),
        ("Milking Paddock",  15,  0.000,  0.000, 280),
        ("Quarantine Block",  8, -0.018, -0.010, 200),
    ],
    "Borrowdale Beef Estate": [
        ("Highland Block",   20,  0.008,  0.008, 360),
        ("Lowveld Paddock",  20, -0.008,  0.008, 360),
        ("Bull Kraal",        6,  0.000,  0.018, 180),
        ("Weaner Camp",      18, -0.012, -0.008, 340),
        ("Finishing Paddock",15,  0.012, -0.008, 300),
    ],
    "Norton Grasslands Farm": [
        ("Msasa Block A",    30,  0.012,  0.006, 480),
        ("Msasa Block B",    30, -0.012,  0.006, 480),
        ("Riverbank Strip",  20,  0.000,  0.020, 400),
        ("Central Camp",     25,  0.000,  0.000, 430),
        ("Dry Season Reserve",18, 0.020, -0.010, 350),
        ("Calving Paddock",  12, -0.020, -0.010, 260),
    ],
}

BREEDS = [
    ("Mashona",         "BEEF",    "Female", "#8B4513"),
    ("Brahman",         "BEEF",    "Female", "Grey"),
    ("Hereford",        "BEEF",    "Female", "Red & White"),
    ("Angus",           "BEEF",    "Female", "Black"),
    ("Simmental",       "DAIRY",   "Female", "Yellow & White"),
    ("Holstein",        "DAIRY",   "Female", "Black & White"),
    ("Jersey",          "DAIRY",   "Female", "Fawn"),
    ("Bonsmara",        "BEEF",    "Female", "Red"),
    ("Nguni",           "BEEF",    "Female", "Multi-colour"),
    ("Limousin",        "BEEF",    "Female", "Golden"),
    ("Brahman Cross",   "BEEF",    "Male",   "Grey-White"),
    ("Mashona Bull",    "BREEDING","Male",   "Brown"),
]

VACCINES = [
    ("Foot & Mouth Disease Vaccine", "5 ml IM"),
    ("Anthrax Spore Vaccine",        "1 ml SC"),
    ("Lumpy Skin Disease Vaccine",   "1 ml SC"),
    ("Brucellosis S19",              "2 ml SC"),
    ("Blackleg Vaccine",             "5 ml SC"),
    ("Bovine Viral Diarrhoea",       "2 ml IM"),
    ("Rift Valley Fever Vaccine",    "1 ml SC"),
]

DISEASES = [
    ("Tick Fever (Babesiosis)", "Moderate"),
    ("East Coast Fever",        "Severe"),
    ("Lumpy Skin Disease",      "Mild"),
    ("Foot Rot",                "Mild"),
    ("Mastitis",                "Moderate"),
    ("Pneumonia",               "Moderate"),
    ("Anaplasmosis",            "Severe"),
]

TREATMENTS = [
    ("Tick Fever",          "Imidocarb dipropionate", "2.4 mg/kg SC"),
    ("Bacterial Infection", "Penicillin-Streptomycin", "20 ml IM"),
    ("Lumpy Skin",          "Supportive care + NSAID", "As directed"),
    ("Mastitis",            "Intramammary Penicillin", "1 tube / quarter"),
    ("Pneumonia",           "Florfenicol",             "20 mg/kg SC"),
    ("Internal Parasites",  "Albendazole",             "7.5 mg/kg PO"),
    ("Tick Load",           "Deltamethrin pour-on",    "10 ml topical"),
]

FEED_TYPES = [
    ("Rhodes Grass Hay",    9.2,  8.0,  0.12),
    ("Star Grass Silage",   9.8,  9.5,  0.18),
    ("Soya Bean Meal",     13.4, 46.0,  0.65),
    ("Yellow Maize Grain", 14.0,  9.5,  0.38),
    ("Cotton Seed Cake",   12.0, 22.0,  0.45),
    ("Dairy Concentrate",  12.5, 18.0,  0.55),
    ("Beef Finisher Mix",  13.0, 14.0,  0.48),
    ("Urea-Molasses Block",  8.5, 28.0, 0.30),
]

ZIM_BUYERS = [
    "Cold Storage Company Ltd",
    "Grain Marketing Board",
    "Spar Harare",
    "OK Zimbabwe",
    "Innscor Africa",
    "Private Buyer — Chiedza Zvobgo",
    "Private Buyer — Blessing Murambiwa",
    "Star Africa Corporation",
]

VET_NAMES = [
    ("Dr. Rudo", "Chikwanda", "VET"),
    ("Dr. Taurai", "Mhondoro", "VET"),
    ("Dr. Simba", "Pfupajena", "VET"),
]

WORKER_NAMES = [
    ("Admire",  "Chinyama",  "WORKER"),
    ("Takunda", "Mazvita",   "WORKER"),
    ("Nyasha",  "Gwena",     "WORKER"),
    ("Tatenda", "Mutseka",   "WORKER"),
    ("Fungai",  "Mhiripiri", "MANAGER"),
    ("Rutendo", "Chipaura",  "MANAGER"),
]


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = "Seed realistic Zimbabwe farm data (2 Harare + 1 Norton)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete all existing farm data before seeding."
        )

    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Clearing existing data…")
            for Model in [
                Alert, SaleRecord, ExpenseRecord, FeedingRecord, ProductionRecord,
                LactationRecord, EnvironmentalLog, HealthObservation, TreatmentRecord,
                VaccinationRecord, DiseaseRecord, BreedingEvent, CalvingRecord,
                MovementEvent, LocationLog, Device, Geofence,
                ReproductiveStatus, Animal, Paddock, Farm, FeedType,
            ]:
                Model.objects.all().delete()
            self.stdout.write("  Done.\n")

        rng = random.Random(42)   # deterministic seed for reproducibility

        # ── Users ──────────────────────────────────────────────────────────
        self.stdout.write("Creating users…")
        users = {}
        for first, last, role in VET_NAMES + WORKER_NAMES:
            username = f"{first.lower()}.{last.lower()}"
            u, _ = User.objects.get_or_create(
                username=username,
                defaults=dict(
                    first_name=first, last_name=last, role=role,
                    phone_number=f"+263 77 {rng.randint(100,999)} {rng.randint(1000,9999)}",
                    employee_id=f"EMP{rng.randint(1000,9999)}",
                )
            )
            users[role] = users.get(role, []) + [u]
        vets     = users.get("VET",     [])
        managers = users.get("MANAGER", [])

        # ── Feed Types ─────────────────────────────────────────────────────
        self.stdout.write("Creating feed types…")
        feed_objs = []
        for name, energy, protein, cost in FEED_TYPES:
            f, _ = FeedType.objects.get_or_create(
                name=name,
                defaults=dict(energy_mj=energy, protein_percent=protein, cost_per_kg=cost)
            )
            feed_objs.append(f)

        # ── Farms ──────────────────────────────────────────────────────────
        self.stdout.write("Creating farms & paddocks…")
        farm_objs = {}
        paddock_objs = {}

        for fd in FARMS:
            farm, _ = Farm.objects.get_or_create(name=fd["name"], defaults=fd)
            farm_objs[farm.name] = farm

            for pname, cap, dlat, dlon, radius in PADDOCKS[farm.name]:
                p, _ = Paddock.objects.get_or_create(
                    farm=farm, name=pname,
                    defaults=dict(
                        capacity=cap,
                        latitude=round(farm.latitude  + dlat, 6),
                        longitude=round(farm.longitude + dlon, 6),
                        boundary_radius_m=radius,
                    )
                )
                paddock_objs.setdefault(farm.name, []).append(p)

                # Geofence record
                Geofence.objects.get_or_create(
                    paddock=p,
                    defaults=dict(radius_meters=radius, alert_on_exit=True)
                )

        # ── Animals (100+) ─────────────────────────────────────────────────
        self.stdout.write("Creating 105 animals…")
        all_animals = []
        tag_counter = 1

        farm_list = list(farm_objs.values())

        # Distribute: ~40 Mazowe, ~30 Borrowdale, ~35 Norton
        dist = [
            ("Mazowe Valley Dairy",     40),
            ("Borrowdale Beef Estate",  30),
            ("Norton Grasslands Farm",  35),
        ]

        for farm_name, count in dist:
            farm = farm_objs[farm_name]
            paddocks_for_farm = paddock_objs[farm_name]

            for i in range(count):
                breed, purpose, sex, color = rng.choice(BREEDS)
                dob    = date.today() - timedelta(days=rng.randint(365, 4015))
                tag    = f"ZW{tag_counter:04d}"
                status = rng.choices(
                    ["ACTIVE", "ACTIVE", "ACTIVE", "ACTIVE", "SOLD", "QUARANTINED"],
                    weights=[60, 60, 60, 60, 8, 4]
                )[0]
                paddock = rng.choice(paddocks_for_farm)

                animal = Animal(
                    tag_number          = tag,
                    electronic_id       = f"RFID{rng.randint(100000,999999)}",
                    registration_number = f"REG{rng.randint(10000,99999)}",
                    species             = "Cattle",
                    breed               = breed,
                    color               = color,
                    horn_status         = rng.choice(["Horned", "Polled", "Dehorned"]),
                    purpose             = purpose,
                    sex                 = sex,
                    date_of_birth       = dob,
                    birth_type          = rng.choice(["Single", "Twin"]),
                    birth_weight_kg     = round(rng.uniform(28, 42), 1),
                    status              = status,
                    acquisition_date    = dob + timedelta(days=rng.randint(0, 60)),
                    acquisition_method  = rng.choice(["Born on Farm", "Purchased", "Transfer"]),
                    purchase_price      = round(rng.uniform(300, 1200), 2) if "Purchased" else None,
                    farm                = farm,
                    current_paddock     = paddock if status == "ACTIVE" else None,
                    current_weight_kg   = round(rng.uniform(280, 620), 1),
                    height_cm           = round(rng.uniform(118, 148), 1),
                    body_length_cm      = round(rng.uniform(140, 185), 1),
                    temperament_score   = rng.randint(1, 5),
                    lameness_score      = rng.randint(0, 2),
                    genetic_merit_index = round(rng.uniform(85, 125), 2),
                    notes               = "",
                )
                animal.save()
                all_animals.append(animal)
                tag_counter += 1

        active_animals = [a for a in all_animals if a.status == "ACTIVE"]
        self.stdout.write(f"  {len(all_animals)} animals created ({len(active_animals)} active).")

        # ── Location Logs ──────────────────────────────────────────────────
        self.stdout.write("Creating GPS location logs…")
        for animal in active_animals:
            if not animal.current_paddock:
                continue
            p = animal.current_paddock
            # 95% inside, 5% slightly outside to simulate breach
            for day_offset in range(7):
                ts = now() - timedelta(days=day_offset, hours=rng.randint(0, 23))
                breach = rng.random() < 0.05
                radius_deg = (p.boundary_radius_m / 111_000) * (1.3 if breach else 0.8)
                lat, lon = rand_coord(p.latitude, p.longitude, radius_deg)
                LocationLog.objects.create(
                    animal=animal, timestamp=ts, latitude=lat, longitude=lon,
                    speed=round(rng.uniform(0, 3.5), 2)
                )

        # ── Vaccinations ───────────────────────────────────────────────────
        self.stdout.write("Creating vaccination records…")
        for animal in all_animals:
            for vname, dose in rng.sample(VACCINES, k=rng.randint(2, 5)):
                admin_date = rand_date(0, 2)
                VaccinationRecord.objects.create(
                    animal=animal,
                    vaccine_name=vname,
                    dose=dose,
                    date_administered=admin_date,
                    next_due_date=admin_date + timedelta(days=rng.randint(180, 365)),
                    administered_by=rng.choice(vets) if vets else None,
                    batch_number=f"BAT{rng.randint(1000,9999)}",
                )

        # ── Diseases ───────────────────────────────────────────────────────
        self.stdout.write("Creating disease records…")
        for animal in rng.sample(all_animals, k=int(len(all_animals) * 0.4)):
            dname, severity = rng.choice(DISEASES)
            onset = rand_date(0, 2)
            recovered = rng.random() < 0.75
            DiseaseRecord.objects.create(
                animal=animal,
                disease_name=dname,
                severity=severity,
                onset_date=onset,
                recovery_date=(onset + timedelta(days=rng.randint(7, 45))) if recovered else None,
                chronic=rng.random() < 0.1,
                economic_loss_estimate=round(rng.uniform(50, 800), 2),
            )

        # ── Treatments ─────────────────────────────────────────────────────
        self.stdout.write("Creating treatment records…")
        for animal in rng.sample(all_animals, k=int(len(all_animals) * 0.5)):
            diag, med, dose = rng.choice(TREATMENTS)
            TreatmentRecord.objects.create(
                animal=animal,
                diagnosis=diag,
                medication=med,
                dosage=dose,
                treatment_date=rand_date(0, 2),
                veterinarian=rng.choice(vets) if vets else None,
                withdrawal_period_days=rng.choice([0, 7, 14, 21, 28]),
            )

        # ── Health Observations ────────────────────────────────────────────
        self.stdout.write("Creating health observations…")
        for animal in all_animals:
            for _ in range(rng.randint(3, 8)):
                HealthObservation.objects.create(
                    animal=animal,
                    weight_kg=round(rng.uniform(260, 640), 1),
                    body_condition_score=round(rng.uniform(2.0, 5.0), 1),
                    temperature_c=round(rng.uniform(38.0, 39.5), 1),
                    symptoms=rng.choice(["None", "Mild lethargy", "Runny nose", "Off feed", "Normal"]),
                    observer=rng.choice(vets + managers) if (vets or managers) else None,
                )

        # ── Production Records ─────────────────────────────────────────────
        self.stdout.write("Creating production records…")
        dairy_animals = [a for a in active_animals if a.purpose == "DAIRY"]
        beef_animals  = [a for a in active_animals if a.purpose in ("BEEF", "BREEDING")]

        for animal in dairy_animals:
            for d in range(90):
                rec_date = date.today() - timedelta(days=d)
                ProductionRecord.objects.create(
                    animal=animal,
                    record_date=rec_date,
                    milk_yield_liters=round(rng.uniform(8, 28), 1),
                    weight_gain_kg=round(rng.uniform(-0.1, 0.6), 2),
                    feed_consumption_kg=round(rng.uniform(12, 22), 1),
                )

        for animal in rng.sample(beef_animals, k=min(30, len(beef_animals))):
            for d in range(60):
                rec_date = date.today() - timedelta(days=d)
                ProductionRecord.objects.create(
                    animal=animal,
                    record_date=rec_date,
                    milk_yield_liters=None,
                    weight_gain_kg=round(rng.uniform(0.3, 1.4), 2),
                    feed_consumption_kg=round(rng.uniform(8, 16), 1),
                )

        # ── Feeding Records ────────────────────────────────────────────────
        self.stdout.write("Creating feeding records…")
        for animal in rng.sample(active_animals, k=min(80, len(active_animals))):
            for _ in range(rng.randint(10, 30)):
                FeedingRecord.objects.create(
                    animal=animal,
                    feed_type=rng.choice(feed_objs),
                    quantity_kg=round(rng.uniform(3, 18), 1),
                    feeding_time=now() - timedelta(days=rng.randint(0, 60),
                                                   hours=rng.randint(0, 23)),
                )

        # ── Breeding Events ────────────────────────────────────────────────
        self.stdout.write("Creating breeding events…")
        females = [a for a in all_animals if a.sex == "Female"]
        males   = [a for a in all_animals if a.sex == "Male"]

        for female in rng.sample(females, k=min(40, len(females))):
            bd = rand_date(0, 3)
            confirmed = rng.random() < 0.65
            BreedingEvent.objects.create(
                female=female,
                male=rng.choice(males) if males else None,
                method=rng.choice(["NATURAL", "NATURAL", "AI"]),
                breeding_date=bd,
                expected_calving_date=bd + timedelta(days=283),
                confirmed_pregnant=confirmed,
            )

            # Reproductive status
            ReproductiveStatus.objects.get_or_create(
                animal=female,
                defaults=dict(
                    puberty_date=female.date_of_birth + timedelta(days=rng.randint(420, 600)),
                    parity_number=rng.randint(0, 5),
                    reproductive_status=rng.choice(["OPEN","PREGNANT","LACTATING","DRY"]),
                    last_heat_date=rand_date(0, 1),
                    last_service_date=bd,
                    services_per_conception=round(rng.uniform(1.0, 2.5), 1),
                )
            )

        # ── Lactation Records ──────────────────────────────────────────────
        self.stdout.write("Creating lactation records…")
        for animal in rng.sample(dairy_animals, k=min(30, len(dairy_animals))):
            start = rand_date(1, 3)
            LactationRecord.objects.create(
                animal=animal,
                lactation_number=rng.randint(1, 5),
                start_date=start,
                end_date=start + timedelta(days=rng.randint(270, 320)),
                total_milk_yield_liters=round(rng.uniform(3000, 8500), 0),
                peak_yield_liters=round(rng.uniform(22, 38), 1),
            )

        # ── Expenses ───────────────────────────────────────────────────────
        self.stdout.write("Creating expense records…")
        categories = ["Veterinary", "Feed", "Labour", "Equipment", "Transport", "Dip & Spray"]
        for animal in rng.sample(all_animals, k=min(70, len(all_animals))):
            for _ in range(rng.randint(2, 6)):
                ExpenseRecord.objects.create(
                    animal=animal,
                    category=rng.choice(categories),
                    amount=round(rng.uniform(15, 450), 2),
                    description="Routine farm expense",
                    expense_date=rand_date(0, 2),
                )

        # ── Sales ──────────────────────────────────────────────────────────
        self.stdout.write("Creating sale records…")
        sold = [a for a in all_animals if a.status == "SOLD"]
        extra_sale_pool = rng.sample(
            [a for a in all_animals if a.status == "ACTIVE"],
            k=min(10, len(active_animals))
        )
        for animal in sold + extra_sale_pool:
            SaleRecord.objects.create(
                animal=animal,
                sale_date=rand_date(0, 2),
                buyer=rng.choice(ZIM_BUYERS),
                sale_price=round(rng.uniform(350, 1400), 2),
                weight_at_sale_kg=round(rng.uniform(300, 580), 1),
            )

        # ── Devices ────────────────────────────────────────────────────────
        self.stdout.write("Creating GPS/RFID devices…")
        device_pool = rng.sample(active_animals, k=min(70, len(active_animals)))
        for i, animal in enumerate(device_pool):
            dtype = "GPS Collar" if i % 3 != 0 else "RFID Tag"
            Device.objects.get_or_create(
                assigned_animal=animal,
                defaults=dict(
                    device_id=f"DEV{i+1:04d}",
                    device_type=dtype,
                    battery_level=round(rng.uniform(10, 100), 1),
                    last_sync_time=now() - timedelta(hours=rng.randint(0, 48)),
                )
            )

        # ── Environmental Logs ─────────────────────────────────────────────
        self.stdout.write("Creating environmental logs…")
        all_paddocks = Paddock.objects.all()
        for paddock in all_paddocks:
            for d in range(14):
                EnvironmentalLog.objects.create(
                    paddock=paddock,
                    temperature_c=round(rng.uniform(18, 34), 1),
                    humidity_percent=round(rng.uniform(35, 85), 1),
                    rainfall_mm=round(rng.uniform(0, 18), 1),
                    pasture_condition_score=rng.randint(1, 5),
                )

        # ── Alerts ─────────────────────────────────────────────────────────
        self.stdout.write("Creating alerts…")
        for animal in rng.sample(all_animals, k=min(25, len(all_animals))):
            alert_type = rng.choice(["VACCINE_DUE", "TREATMENT_DUE", "VET_VISIT", "HEALTH_RISK"])
            due = date.today() + timedelta(days=rng.randint(-5, 14))
            Alert.objects.create(
                animal=animal,
                alert_type=alert_type,
                message=f"{alert_type.replace('_', ' ').title()} for {animal.tag_number}",
                due_date=due,
                is_resolved=rng.random() < 0.3,
            )

        self.stdout.write(self.style.SUCCESS(
            f"\n✅  Seeding complete!\n"
            f"   Farms:    {Farm.objects.count()}\n"
            f"   Paddocks: {Paddock.objects.count()}\n"
            f"   Animals:  {Animal.objects.count()}\n"
            f"   GPS logs: {LocationLog.objects.count()}\n"
            f"   Devices:  {Device.objects.count()}\n"
        ))
import uuid
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker

from app.models import *

fake = Faker()


class Command(BaseCommand):
    help = "Generate demo livestock data (100 animals) with correct field mapping."

    def handle(self, *args, **kwargs):

        self.stdout.write("Deleting existing data...")

        models_to_clear = [
            LactationRecord, ReproductiveStatus, CalvingRecord, BreedingEvent,
            LocationLog, MovementEvent, Device, Geofence, VaccinationRecord,
            TreatmentRecord, HealthObservation, DiseaseRecord, LabTest,
            ProductionRecord, FeedingRecord, EnvironmentalLog, Alert,
            SaleRecord, ExpenseRecord, Animal, Paddock, Farm, User, FeedType
        ]

        for m in models_to_clear:
            m.objects.all().delete()

        self.stdout.write("Creating demo users...")

        farm_manager = User.objects.create_user(
            username="manager1",
            password="password123",
            role="MANAGER",
            first_name="John",
            last_name="Doe",
            email="manager@example.com"
        )

        farm_worker = User.objects.create_user(
            username="worker1",
            password="password123",
            role="WORKER",
            first_name="Jane",
            last_name="Smith",
            email="worker@example.com"
        )

        self.stdout.write("Creating farms...")

        ZIM_LOCATIONS = [
            ("Harare Farm", -17.8292, 31.0522),
            ("Bulawayo Ranch", -20.1325, 28.6265),
            ("Gweru Grazing Estate", -19.4550, 29.8167),
            ("Masvingo Livestock Farm", -20.0740, 30.8320),
            ("Chinhoyi Commercial Farm", -17.3667, 30.2000),
        ]

        farms = []
        for name, lat, lon in ZIM_LOCATIONS:
            farms.append(Farm.objects.create(
                name=name,
                location_name=name,
                latitude=lat,
                longitude=lon,
                size_hectares=random.uniform(80, 600),
                owner=fake.name()
            ))

        self.stdout.write("Creating paddocks...")

        paddocks = []
        for farm in farms:
            for i in range(3):
                paddocks.append(Paddock.objects.create(
                    farm=farm,
                    name=f"Paddock {i+1}",
                    capacity=random.randint(30, 120),
                    latitude=farm.latitude + random.uniform(-0.02, 0.02),
                    longitude=farm.longitude + random.uniform(-0.02, 0.02),
                    boundary_radius_m=random.randint(200, 800)
                ))

        self.stdout.write("Creating feed types...")

        feeds = []
        feed_names = ["Maize Bran", "Lucerne Hay", "Sorghum", "Silage", "Grazing Grass"]

        for f in feed_names:
            feeds.append(FeedType.objects.create(
                name=f,
                energy_mj=random.uniform(8, 15),
                protein_percent=random.uniform(10, 30),
                cost_per_kg=random.uniform(0.5, 2.0)
            ))

        self.stdout.write("Creating animals (100 records)...")

        breeds = ["Brahman", "Tuli", "Mashona", "Boran", "Afrikaner", "Hereford", "Angus"]
        animals = []

        for i in range(100):
            farm = random.choice(farms)
            paddock = random.choice([p for p in paddocks if p.farm == farm])

            animal = Animal.objects.create(
                tag_number=f"TAG-{random.randint(10000,99999)}",
                electronic_id=f"RFID-{random.randint(10000,99999)}",
                registration_number=f"REG-{random.randint(1000,9999)}",
                species="Cattle",
                breed=random.choice(breeds),
                strain=random.choice(["Strain A", "Strain B", "Strain C"]),
                color=random.choice(["Black", "Brown", "White", "Red"]),
                horn_status=random.choice(["Horned", "Polled", "Dehorned", ""]),
                purpose=random.choice(["DAIRY", "BEEF", "BREEDING", "DRAFT"]),
                sex=random.choice(["MALE", "FEMALE"]),
                date_of_birth=fake.date_between("-5y", "-1y"),
                birth_type=random.choice(["Single", "Twin", ""]),
                birth_weight_kg=random.uniform(20, 40),
                weaning_date=fake.date_between("-4y", "-1y"),
                weaning_weight_kg=random.uniform(80, 200),
                sire_tag=f"TAG-{random.randint(10000,99999)}",
                dam_tag=f"TAG-{random.randint(10000,99999)}",
                genetic_merit_index=random.uniform(0, 10),
                status=random.choice(
                    ["ACTIVE", "SOLD", "DECEASED", "QUARANTINED", "CULLED", "MISSING"]
                ),
                acquisition_date=fake.date_between("-4y", "today"),
                acquisition_method=random.choice(["Purchase", "Breeding", "Gift"]),
                purchase_price=random.uniform(500, 2000),
                insurance_policy_number=f"INS-{random.randint(1000,9999)}",
                farm=farm,
                current_paddock=paddock,
                current_weight_kg=random.uniform(200, 600),
                height_cm=random.uniform(100, 160),
                body_length_cm=random.uniform(120, 180),
                temperament_score=random.randint(1,5),
                lameness_score=random.randint(0,5),
                notes=fake.sentence()
            )

            animals.append(animal)

        self.stdout.write("Creating reproductive, health and related records...")

        for animal in animals:

            # Reproductive (only for females)
            if animal.sex == "FEMALE":
                ReproductiveStatus.objects.create(
                    animal=animal,
                    puberty_date=fake.date_between("-5y", "-3y"),
                    parity_number=random.randint(0,5),
                    reproductive_status=random.choice(
                        ["OPEN","PREGNANT","LACTATING","DRY"]
                    ),
                    last_heat_date=fake.date_between("-1y","today"),
                    last_service_date=fake.date_between("-1y","today"),
                    services_per_conception=random.uniform(1,3)
                )

            # Health observations
            for _ in range(2):
                HealthObservation.objects.create(
                    animal=animal,
                    weight_kg=random.uniform(200,600),
                    body_condition_score=random.uniform(1,5),
                    temperature_c=random.uniform(36.5,39.5),
                    symptoms=fake.sentence(),
                    observer=random.choice([farm_manager, farm_worker])
                )

            # Treatment
            TreatmentRecord.objects.create(
                animal=animal,
                diagnosis=fake.word(),
                medication=fake.word(),
                dosage=f"{random.randint(5,20)}ml",
                treatment_date=fake.date_between("-1y","today"),
                veterinarian=random.choice([farm_manager, farm_worker]),
                withdrawal_period_days=random.randint(1,10),
                notes=fake.sentence()
            )

            # Vaccination (with next_due_date)
            next_due = fake.date_between("today", "+1y")
            VaccinationRecord.objects.create(
                animal=animal,
                vaccine_name=random.choice(["FMD","Anthrax","Brucellosis"]),
                dose="5ml",
                date_administered=fake.date_between("-2y","today"),
                next_due_date=next_due,
                administered_by=random.choice([farm_manager, farm_worker]),
                batch_number=fake.bothify(text="BATCH-####"),
                notes=fake.sentence()
            )

            # Disease record
            DiseaseRecord.objects.create(
                animal=animal,
                disease_name=random.choice(["FMD","Anthrax","Brucellosis"]),
                severity=random.choice(["Mild","Moderate","Severe"]),
                onset_date=fake.date_between("-1y","today"),
                recovery_date=fake.date_between("today","+1y"),
                chronic=random.choice([True,False]),
                economic_loss_estimate=random.uniform(50,500)
            )

            # Lab test
            LabTest.objects.create(
                animal=animal,
                test_name=random.choice(["Blood Count","TB Test","Pregnancy Test"]),
                sample_type=random.choice(["Blood","Urine","Milk"]),
                result_value=random.choice(["Normal","Abnormal"]),
                normal_range="N/A",
                test_date=fake.date_between("-1y","today")
            )

            # Production
            ProductionRecord.objects.create(
                animal=animal,
                record_date=fake.date_between("-1y","today"),
                milk_yield_liters=random.uniform(0,50),
                weight_gain_kg=random.uniform(0,30),
                feed_consumption_kg=random.uniform(0,10)
            )

            # Feeding
            feed = random.choice(feeds)
            FeedingRecord.objects.create(
                animal=animal,
                feed_type=feed,
                quantity_kg=random.uniform(1,20),
                feeding_time=fake.date_time_between("-1y","now")
            )

            # Location
            LocationLog.objects.create(
                animal=animal,
                timestamp=fake.date_time_between("-1y","now"),
                latitude=animal.farm.latitude + random.uniform(-0.02,0.02),
                longitude=animal.farm.longitude + random.uniform(-0.02,0.02),
                speed=random.uniform(0,15)
            )

            # Movement
            MovementEvent.objects.create(
                animal=animal,
                from_paddock=animal.current_paddock,
                to_paddock=random.choice([p for p in paddocks if p.farm==animal.farm]),
                moved_by=random.choice([farm_manager, farm_worker])
            )

            # Environmental
            EnvironmentalLog.objects.create(
                paddock=animal.current_paddock,
                temperature_c=random.uniform(15,35),
                humidity_percent=random.uniform(30,90),
                rainfall_mm=random.uniform(0,20),
                pasture_condition_score=random.randint(1,5)
            )

            # Alert (due next week)
            due = timezone.now().date() + timedelta(days=7)
            Alert.objects.create(
                animal=animal,
                alert_type="VACCINE_DUE",
                message="Next vaccination due",
                due_date=due,
                status="ABOUT_TO_DUE"
            )

            # Expense
            ExpenseRecord.objects.create(
                animal=animal,
                category=random.choice(["Feed","Vet","Maintenance"]),
                amount=random.uniform(50,500),
                description=fake.sentence(),
                expense_date=fake.date_between("-1y","today")
            )

            # Device
            Device.objects.create(
                device_id=f"GPS-{random.randint(10000,99999)}",
                device_type=random.choice(["GPS Collar","RFID"]),
                battery_level=random.uniform(10,100),
                last_sync_time=fake.date_time_between("-1y","now"),
                assigned_animal=animal
            )

            # Geofence
            Geofence.objects.create(
                paddock=animal.current_paddock,
                radius_meters=random.randint(200,800),
                alert_on_exit=True
            )

        self.stdout.write(self.style.SUCCESS("Demo data (100 animals) generated successfully!"))
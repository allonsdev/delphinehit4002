from django.db import models
from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.files import File
from django.conf import settings


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    ROLE_CHOICES = [
        ("ADMIN", "Administrator"),
        ("VET", "Veterinarian"),
        ("MANAGER", "Farm Manager"),
        ("WORKER", "Farm Worker"),
        ("SECURITY", "Security Officer"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone_number = models.CharField(max_length=20, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)



class Farm(TimeStampedModel):
    name = models.CharField(max_length=255)
    location_name = models.CharField(max_length=255)
    latitude = models.FloatField()
    longitude = models.FloatField()
    size_hectares = models.FloatField()
    owner = models.CharField(max_length=255)


class Paddock(TimeStampedModel):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    capacity = models.IntegerField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    boundary_radius_m = models.FloatField(help_text="Geo-fence radius")



class Animal(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # -------------------------------
    # Identity
    # -------------------------------
    qr_code = models.CharField(max_length=500, unique=True, blank=True)
    qr_image = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    tag_number = models.CharField(max_length=100, unique=True)
    electronic_id = models.CharField(max_length=100, blank=True)  # RFID
    registration_number = models.CharField(max_length=100, blank=True)

    # -------------------------------
    # Classification
    # -------------------------------
    species = models.CharField(max_length=50, default="Cattle")
    breed = models.CharField(max_length=100)
    strain = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=100)
    horn_status = models.CharField(max_length=50, blank=True)

    purpose = models.CharField(
        max_length=50,
        choices=[
            ("DAIRY", "Dairy"),
            ("BEEF", "Beef"),
            ("BREEDING", "Breeding"),
            ("DRAFT", "Draft"),
        ],
    )

    # -------------------------------
    # Sex & Lifecycle
    # -------------------------------
    sex = models.CharField(max_length=10)
    date_of_birth = models.DateField()
    birth_type = models.CharField(max_length=50, blank=True)
    birth_weight_kg = models.FloatField(null=True, blank=True)
    weaning_date = models.DateField(null=True, blank=True)
    weaning_weight_kg = models.FloatField(null=True, blank=True)

    # -------------------------------
    # Lineage
    # -------------------------------
    sire_tag = models.CharField(max_length=100, blank=True)
    dam_tag = models.CharField(max_length=100, blank=True)
    genetic_merit_index = models.FloatField(null=True, blank=True)

    # -------------------------------
    # Status
    # -------------------------------
    status = models.CharField(
        max_length=50,
        choices=[
            ("ACTIVE", "Active"),
            ("SOLD", "Sold"),
            ("DECEASED", "Deceased"),
            ("QUARANTINED", "Quarantined"),
            ("CULLED", "Culled"),
            ("MISSING", "Missing"),
        ],
    )

    acquisition_date = models.DateField(null=True, blank=True)
    acquisition_method = models.CharField(max_length=50, blank=True)
    purchase_price = models.FloatField(null=True, blank=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True)

    # -------------------------------
    # Location
    # -------------------------------
    farm = models.ForeignKey("Farm", on_delete=models.CASCADE)
    current_paddock = models.ForeignKey(
        "Paddock",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # -------------------------------
    # Physical Metrics
    # -------------------------------
    current_weight_kg = models.FloatField(null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    body_length_cm = models.FloatField(null=True, blank=True)

    # -------------------------------
    # Welfare
    # -------------------------------
    temperament_score = models.IntegerField(null=True, blank=True)
    lameness_score = models.IntegerField(null=True, blank=True)

    # -------------------------------
    # Lifecycle End
    # -------------------------------
    date_of_death = models.DateField(null=True, blank=True)
    cause_of_death = models.CharField(max_length=255, blank=True)
    culling_reason = models.CharField(max_length=255, blank=True)

    notes = models.TextField(blank=True)

    # =====================================================
    # AUTO QR GENERATION
    # =====================================================
    def save(self, *args, **kwargs):
        is_new = self._state.adding

        # Save first to generate UUID
        super().save(*args, **kwargs)

        # Generate QR only if new or missing
        if is_new or not self.qr_image:

            admin_url = (
                f"{settings.BASE_URL}/admin/app/animal/{self.id}/change/"
            )

            # Save URL
            self.qr_code = admin_url

            # Generate QR image
            qr = qrcode.make(admin_url)
            buffer = BytesIO()
            qr.save(buffer, format="PNG")

            file_name = f"{self.tag_number}_qr.png"

            self.qr_image.save(file_name, File(buffer), save=False)

            # Update only QR fields (prevents infinite loop)
            super().save(update_fields=["qr_code", "qr_image"])

    def __str__(self):
        return f"{self.tag_number} - {self.breed}"
    
class ReproductiveStatus(TimeStampedModel):
    animal = models.OneToOneField(Animal, on_delete=models.CASCADE)

    puberty_date = models.DateField(null=True, blank=True)
    parity_number = models.IntegerField(null=True, blank=True)
    reproductive_status = models.CharField(max_length=50, choices=[
        ("OPEN", "Open"),
        ("PREGNANT", "Pregnant"),
        ("LACTATING", "Lactating"),
        ("DRY", "Dry"),
    ])

    last_heat_date = models.DateField(null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)
    services_per_conception = models.FloatField(null=True, blank=True)

class LactationRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    lactation_number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    total_milk_yield_liters = models.FloatField(null=True, blank=True)
    peak_yield_liters = models.FloatField(null=True, blank=True)



class DiseaseRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    disease_name = models.CharField(max_length=255)
    severity = models.CharField(max_length=50)
    onset_date = models.DateField()
    recovery_date = models.DateField(null=True, blank=True)
    chronic = models.BooleanField(default=False)
    economic_loss_estimate = models.FloatField(null=True, blank=True)


class LabTest(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    test_name = models.CharField(max_length=255)
    sample_type = models.CharField(max_length=100)
    result_value = models.CharField(max_length=255)
    normal_range = models.CharField(max_length=100, blank=True)
    test_date = models.DateField()


class FeedType(models.Model):
    name = models.CharField(max_length=255)
    energy_mj = models.FloatField(null=True, blank=True)
    protein_percent = models.FloatField(null=True, blank=True)
    cost_per_kg = models.FloatField(null=True, blank=True)


    
    
class ExpenseRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    amount = models.FloatField()
    description = models.TextField(blank=True)
    expense_date = models.DateField()


class Device(TimeStampedModel):
    device_id = models.CharField(max_length=100, unique=True)
    device_type = models.CharField(max_length=50)  # GPS collar, RFID
    battery_level = models.FloatField(null=True)
    last_sync_time = models.DateTimeField(null=True)
    assigned_animal = models.OneToOneField(Animal, on_delete=models.SET_NULL, null=True)

class Geofence(TimeStampedModel):
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE)
    radius_meters = models.FloatField()
    alert_on_exit = models.BooleanField(default=True)


class VaccinationRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    vaccine_name = models.CharField(max_length=255)
    dose = models.CharField(max_length=100)
    date_administered = models.DateField()
    next_due_date = models.DateField(null=True, blank=True)
    administered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    batch_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)


class TreatmentRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    diagnosis = models.CharField(max_length=255)
    medication = models.CharField(max_length=255)
    dosage = models.CharField(max_length=100)
    treatment_date = models.DateField()
    veterinarian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    withdrawal_period_days = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)


class HealthObservation(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    weight_kg = models.FloatField(null=True, blank=True)
    body_condition_score = models.FloatField(null=True, blank=True)
    temperature_c = models.FloatField(null=True, blank=True)
    symptoms = models.TextField(blank=True)
    observer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class BreedingEvent(TimeStampedModel):
    female = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="female_events")
    male = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, related_name="male_events")

    method = models.CharField(max_length=50, choices=[
        ("NATURAL", "Natural"),
        ("AI", "Artificial Insemination"),
    ])

    breeding_date = models.DateField()
    expected_calving_date = models.DateField(null=True, blank=True)
    confirmed_pregnant = models.BooleanField(null=True)
    notes = models.TextField(blank=True)

class CalvingRecord(TimeStampedModel):
    mother = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name="calvings")
    calf = models.OneToOneField(Animal, on_delete=models.SET_NULL, null=True, blank=True)
    calving_date = models.DateField()
    birth_weight_kg = models.FloatField(null=True)
    complications = models.TextField(blank=True)


class LocationLog(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    speed = models.FloatField(null=True, blank=True)


class MovementEvent(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    from_paddock = models.ForeignKey(Paddock, on_delete=models.SET_NULL, null=True, related_name="move_from")
    to_paddock = models.ForeignKey(Paddock, on_delete=models.SET_NULL, null=True, related_name="move_to")
    moved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class Alert(TimeStampedModel):
    ALERT_TYPE = [
        ("VACCINE_DUE", "Vaccination Due"),
        ("TREATMENT_DUE", "Treatment Due"),
        ("VET_VISIT", "Veterinary Visit"),
        ("GEOFENCE_BREACH", "Geo-fence Breach"),
        ("HEALTH_RISK", "Health Risk"),
    ]

    STATUS = [
        ("DUE", "Due"),
        ("ABOUT_TO_DUE", "About to be Due"),
        ("OVERDUE", "Overdue"),
        ("RESOLVED", "Resolved"),
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE)
    message = models.TextField()
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=STATUS, default="DUE")

    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.animal.tag_number} - {self.get_alert_type_display()}"

    def save(self, *args, **kwargs):
        # Auto-calc status before saving
        if self.due_date:
            from datetime import date, timedelta

            today = date.today()

            if self.due_date < today:
                self.status = "OVERDUE"
            elif self.due_date <= today + timedelta(days=7):
                self.status = "ABOUT_TO_DUE"
            else:
                self.status = "DUE"

        super().save(*args, **kwargs)
class ProductionRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    record_date = models.DateField()

    milk_yield_liters = models.FloatField(null=True, blank=True)
    weight_gain_kg = models.FloatField(null=True, blank=True)
    feed_consumption_kg = models.FloatField(null=True, blank=True)


    
class FeedingRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    feed_type = models.ForeignKey(FeedType, on_delete=models.SET_NULL, null=True)
    quantity_kg = models.FloatField()
    feeding_time = models.DateTimeField()

class EnvironmentalLog(TimeStampedModel):
    paddock = models.ForeignKey(Paddock, on_delete=models.CASCADE)
    temperature_c = models.FloatField(null=True)
    humidity_percent = models.FloatField(null=True)
    rainfall_mm = models.FloatField(null=True)
    pasture_condition_score = models.IntegerField(null=True)



class SaleRecord(TimeStampedModel):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    sale_date = models.DateField()
    buyer = models.CharField(max_length=255)
    sale_price = models.FloatField()
    weight_at_sale_kg = models.FloatField(null=True)
    




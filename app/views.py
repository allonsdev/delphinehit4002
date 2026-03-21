from django.shortcuts import render, get_object_or_404
from app.models import *
from django.shortcuts import render, get_object_or_404
from django.db.models import Count, Sum
from .models import *
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect
import json
from django.db.models import Sum, Count
from django.shortcuts import render
from django.db.models import Count, Sum
from .models import *
from django.db.models import *
from django.utils.timezone import now
from django.utils.timezone import now
from django.utils.timezone import now
from datetime import timedelta

from django.shortcuts import render

def farm_map_view(request):
    # Sample paddocks representing Irvines Farms
    paddocks = [
        {
            "name": "Irvines Paddock 1",
            "polygon": [
                [-25.740, 28.180],
                [-25.740, 28.185],
                [-25.745, 28.185],
                [-25.745, 28.180],
            ]
        },
        {
            "name": "Irvines Paddock 2",
            "polygon": [
                [-25.745, 28.180],
                [-25.745, 28.185],
                [-25.750, 28.185],
                [-25.750, 28.180],
            ]
        },
        {
            "name": "Irvines Paddock 3",
            "polygon": [
                [-25.740, 28.185],
                [-25.740, 28.190],
                [-25.745, 28.190],
                [-25.745, 28.185],
            ]
        }
    ]

    # Sample cows positioned across paddocks
    cows = [
        {"id": "Cow-101", "lat": -25.742, "lon": 28.182},
        {"id": "Cow-102", "lat": -25.747, "lon": 28.182},
        {"id": "Cow-103", "lat": -25.743, "lon": 28.188},
    ]

    context = {
        "paddocks": paddocks,
        "cows": cows,
        "farm_name": "Irvines Farms"
    }

    return render(request, "location.html", context)
def logout_view(request):
    logout(request)
    return redirect('login')

def login_view(request):
    # Redirect if already logged in
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # ✅ No roles, simple redirect
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")

def production_list(request):
    data = ProductionRecord.objects.select_related("animal")

    stats = data.aggregate(
        total=Sum('id'),  # will fix below
        avg_milk=Avg("milk_yield_liters"),
        avg_weight_gain=Avg("weight_gain_kg"),
        avg_feed=Avg("feed_consumption_kg"),
    )

    context = {
        "data": data,
        "total": data.count(),
        "avg_milk": round(stats["avg_milk"], 1) if stats["avg_milk"] else 0,
        "avg_weight_gain": round(stats["avg_weight_gain"], 1) if stats["avg_weight_gain"] else 0,
        "avg_feed": round(stats["avg_feed"], 1) if stats["avg_feed"] else 0,
    }

    return render(request, "productive.html", context)


def home(request):
    return render(request, "home.html")

from django.contrib.auth.decorators import login_required

@login_required

def dashboard(request):

    animals = Animal.objects.all()[:200]
    alerts = Alert.objects.filter(is_resolved=False)
    sales = SaleRecord.objects.all()

    total_animals = Animal.objects.count()
    total_farms = Farm.objects.count()
    total_alerts = alerts.count()
    total_devices = Device.objects.count()

    revenue = SaleRecord.objects.aggregate(
        total=Sum("sale_price")
    )["total"] or 0

    milk_total = ProductionRecord.objects.aggregate(
        total=Sum("milk_yield_liters")
    )["total"] or 0

    # -------- STATUS CHART --------
    status_counts = Animal.objects.values("status").annotate(
        count=Count("status")
    )

    status_labels = [s["status"] for s in status_counts]
    status_data = [s["count"] for s in status_counts]

    # -------- BREED CHART --------
    breeds = Animal.objects.values("breed").annotate(
        count=Count("id")
    )

    breed_labels = [b["breed"] for b in breeds]
    breed_counts = [b["count"] for b in breeds]

    # -------- OPTIONAL (avoid template errors) --------
    milk_labels = []
    milk_data = []
    weight_labels = []
    weight_data = []

    # -------- EVENTS --------
    events = []

    for v in VaccinationRecord.objects.all():
        events.append({
            "title": f"Vaccine {v.vaccine_name} - {v.animal.tag_number}",
            "start": v.date_administered.isoformat()
        })

    for t in TreatmentRecord.objects.all():
        events.append({
            "title": f"Treatment {t.medication}",
            "start": t.treatment_date.isoformat()
        })

    # -------- FINAL CONTEXT --------
    context = {
        "animals": animals,
        "alerts": alerts,
        "sales": sales,

        "total_animals": total_animals,
        "total_farms": total_farms,
        "total_alerts": total_alerts,
        "total_devices": total_devices,
        "revenue": revenue,
        "milk_total": milk_total,

        # ✅ JSON FIXES
        "status_labels": json.dumps(status_labels),
        "status_data": json.dumps(status_data),
        "breed_labels": json.dumps(breed_labels),
        "breed_counts": json.dumps(breed_counts),

        "milk_labels": json.dumps(milk_labels),
        "milk_data": json.dumps(milk_data),
        "weight_labels": json.dumps(weight_labels),
        "weight_data": json.dumps(weight_data),

        "events": json.dumps(events),
    }

    return render(request, "index.html", context)

def scan_qr(request):
    qr_code = request.GET.get('qr')  # QR code sent as GET parameter
    if not qr_code:
        return render(request, 'scan_qr.html', {'error': 'No QR code provided'})

    # Get the animal or 404
    animal = get_object_or_404(Animal, qr_code=qr_code)

    # Related info
    reproductive_status = getattr(animal, 'reproductivestatus', None)
    last_lactation = LactationRecord.objects.filter(animal=animal).order_by('-start_date').first()
    last_breeding = BreedingEvent.objects.filter(female=animal).order_by('-breeding_date').first()
    last_treatment = TreatmentRecord.objects.filter(animal=animal).order_by('-treatment_date').first()
    last_vaccination = VaccinationRecord.objects.filter(animal=animal).order_by('-date_administered').first()

    context = {
        'animal': animal,
        'reproductive_status': reproductive_status,
        'last_lactation': last_lactation,
        'last_breeding': last_breeding,
        'last_treatment': last_treatment,
        'last_vaccination': last_vaccination,
    }

    return render(request, 'animal_detail.html', context)

# =========================
# FARM & STRUCTURE
# =========================
def farm_list(request):
    data = Farm.objects.all()
    q = request.GET.get("q")
    if q:
        data = data.filter(name__icontains=q)
    return render(request, "farm.html", {"data": data})


def paddock_list(request):
    data = Paddock.objects.select_related("farm")
    q = request.GET.get("q")
    if q:
        data = data.filter(name__icontains=q)
    return render(request, "paddock.html", {"data": data})


# =========================
# ANIMAL (ADVANCED)
# =========================
def animal_list(request):
    # Base queryset for table
    data = Animal.objects.annotate(
        total_diseases=Count("diseaserecord"),
        total_breedings=Count("female_events"),
        total_milk=Sum("productionrecord__milk_yield_liters"),
        total_expenses=Sum("expenserecord__amount"),
    )

    # Filters
    q = request.GET.get("q")
    if q:
        data = data.filter(tag_number__icontains=q)

    status = request.GET.get("status")
    if status:
        data = data.filter(status=status)

    # ✅ CARD COUNTS (GLOBAL STATS)
    total_animals = Animal.objects.count()
    total_farms = Farm.objects.count()
    total_devices = Device.objects.count() if Device.objects.exists() else 0
    total_alerts = Alert.objects.count() if Alert.objects.exists() else 0

    context = {
        "data": data,

        # Cards
        "animals": data,  # for animals|length
        "total_animals": total_animals,
        "total_farms": total_farms,
        "total_devices": total_devices,
        "total_alerts": total_alerts,
    }

    return render(request, "animal.html", context)


def animal_detail(request, pk):
    animal = get_object_or_404(Animal, id=pk)

    context = {
        "animal": animal,
        "diseases": animal.diseaserecord_set.all(),
        "vaccinations": animal.vaccinationrecord_set.all(),
        "treatments": animal.treatmentrecord_set.all(),
        "health": animal.healthobservation_set.all(),
        "breeding": animal.female_events.all(),
        "calving": animal.calvings.all(),
        "production": animal.productionrecord_set.all(),
        "expenses": animal.expenserecord_set.all(),
    }

    return render(request, "animal_detail.html", context)


# =========================
# HEALTH
# =========================
def disease_list(request):
    data = DiseaseRecord.objects.select_related("animal")
    q = request.GET.get("q")
    if q:
        data = data.filter(disease_name__icontains=q)
    return render(request, "disease.html", {"data": data})


def vaccination_list(request):
    data = VaccinationRecord.objects.select_related("animal")

    q = request.GET.get("q")
    if q:
        data = data.filter(vaccine_name__icontains=q)

    # ✅ CARD METRICS
    total_vaccinations = VaccinationRecord.objects.count()

    upcoming_vaccinations = VaccinationRecord.objects.filter(
        next_due_date__isnull=False,
        next_due_date__gte=now().date()
    ).count()
    completed_vaccinations = VaccinationRecord.objects.filter(
        date_administered__isnull=False
    ).count()
    today = now().date()
    # ✅ Missed Vaccinations (past due and not yet done again)
    missed_vaccinations = VaccinationRecord.objects.filter(
        next_due_date__lt=today
    ).count()
    return render(request, "vaccination.html", {
        "data": data,
        "vaccinations": data,  # for template length fallback

        "total_vaccinations": total_vaccinations,
        "upcoming_vaccinations": upcoming_vaccinations,
            'completed_vaccinations': completed_vaccinations,
    'missed_vaccinations': missed_vaccinations,
    })

def treatment_list(request):
    data = TreatmentRecord.objects.select_related("animal")
    q = request.GET.get("q")
    if q:
        data = data.filter(diagnosis__icontains=q)
    return render(request, "treatment.html", {"data": data})


from django.db.models import Avg

def health_observation_list(request):
    data = HealthObservation.objects.select_related("animal")

    stats = data.aggregate(
        avg_temp=Avg("temperature_c"),
        avg_weight=Avg("weight_kg")
    )

    context = {
        "data": data,
        "total": data.count(),
        "avg_temp": round(stats["avg_temp"], 1) if stats["avg_temp"] else 0,
        "avg_weight": round(stats["avg_weight"], 1) if stats["avg_weight"] else 0,
    }

    return render(request, "healt.html", context)

def labtest_list(request):
    data = LabTest.objects.select_related("animal")
    return render(request, "labtest.html", {"data": data})


# =========================
# BREEDING
# =========================
def breeding_list(request):
    data = BreedingEvent.objects.select_related("female", "male")

    stats = data.aggregate(
        total=Count("id"),
        pregnant=Count("id", filter=Q(confirmed_pregnant=True)),
        ai_count=Count("id", filter=Q(method="AI")),
        natural_count=Count("id", filter=Q(method="NATURAL")),
    )

    context = {
        "data": data,
        "total": stats["total"],
        "pregnant": stats["pregnant"],
        "ai_count": stats["ai_count"],
        "natural_count": stats["natural_count"],
    }

    return render(request, "breeding.html", context)


def calving_list(request):
    data = CalvingRecord.objects.select_related("mother", "calf")
    return render(request, "calving.html", {"data": data})


def reproductive_list(request):
    data = ReproductiveStatus.objects.select_related("animal")
    return render(request, "reproductive.html", {"data": data})


def lactation_list(request):
    data = LactationRecord.objects.select_related("animal")
    return render(request, "lactation.html", {"data": data})


# =========================
# PRODUCTION



def feeding_list(request):
    data = FeedingRecord.objects.select_related("animal", "feed_type")

    stats = data.aggregate(
        total=Count("id"),
        total_feed=Sum("quantity_kg"),
        avg_feed=Avg("quantity_kg"),
        unique_animals=Count("animal", distinct=True),
    )

    context = {
        "data": data,
        "total": stats["total"],
        "total_feed": round(stats["total_feed"], 1) if stats["total_feed"] else 0,
        "avg_feed": round(stats["avg_feed"], 1) if stats["avg_feed"] else 0,
        "unique_animals": stats["unique_animals"],
    }

    return render(request, "feeding.html", context)

def feedtype_list(request):
    data = FeedType.objects.all()
    return render(request, "feedtype.html", {"data": data})


# =========================
# GPS & TRACKING
# =========================
def location_log_list(request):
    data = LocationLog.objects.select_related("animal")
    return render(request, "location.html", {"data": data})


def movement_list(request):
    data = MovementEvent.objects.select_related("animal", "from_paddock", "to_paddock")
    return render(request, "movement.html", {"data": data})


def device_list(request):
    data = Device.objects.select_related("assigned_animal")
    return render(request, "device.html", {"data": data})


def geofence_list(request):
    data = Geofence.objects.select_related("paddock")
    return render(request, "geofence.html", {"data": data})


def environmental_list(request):
    data = EnvironmentalLog.objects.select_related("paddock")
    return render(request, "environmental.html", {"data": data})


def device_list(request):
    data = Device.objects.select_related("assigned_animal")

    q = request.GET.get("q")
    if q:
        data = data.filter(device_id__icontains=q)

    # ✅ CARD METRICS
    total_devices = Device.objects.count()

    # Active devices = synced within last 24 hours
    active_threshold = now() - timedelta(hours=24)
    active_devices = Device.objects.filter(
        last_sync_time__gte=active_threshold
    ).count()

    # Low battery devices (< 20%)
    low_battery_devices = Device.objects.filter(
        battery_level__lt=20
    ).count()

    return render(request, "device.html", {
        "data": data,

        "total_devices": total_devices,
        "active_devices": active_devices,
        "low_battery_devices": low_battery_devices,
    })

# =========================
# FINANCE & ALERTS
# =========================
def expense_list(request):
    data = ExpenseRecord.objects.select_related("animal")
    return render(request, "expense.html", {"data": data})


def sale_list(request):
    data = SaleRecord.objects.select_related("animal")

    stats = data.aggregate(
        total=Count("id"),
        total_revenue=Sum("sale_price"),
        avg_price=Avg("sale_price"),
        avg_weight=Avg("weight_at_sale_kg"),
    )

    context = {
        "data": data,
        "total": stats["total"],
        "total_revenue": round(stats["total_revenue"], 2) if stats["total_revenue"] else 0,
        "avg_price": round(stats["avg_price"], 2) if stats["avg_price"] else 0,
        "avg_weight": round(stats["avg_weight"], 1) if stats["avg_weight"] else 0,
    }
    
    return render(request, "sale.html", context)
def alert_list(request):
    data = Alert.objects.select_related("animal")
    return render(request, "alert.html", {"data": data})
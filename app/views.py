import json
from datetime import timedelta

from django import forms as _forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.views.decorators.http import require_POST, require_GET

from .models import (
    Alert, Animal, BreedingEvent, CalvingRecord, Device,
    DiseaseRecord, EnvironmentalLog, ExpenseRecord, Farm,
    FeedType, FeedingRecord, Geofence, HealthObservation,
    LabTest, LactationRecord, LocationLog, MovementEvent,
    Paddock, ProductionRecord, ReproductiveStatus,
    SaleRecord, TreatmentRecord, VaccinationRecord,
)


# =============================================================================
# ANIMAL EDIT FORM
# =============================================================================

class AnimalEditForm(_forms.ModelForm):
    class Meta:
        model  = Animal
        fields = [
            "tag_number", "electronic_id", "registration_number",
            "insurance_policy_number",
            "species", "breed", "strain", "color", "horn_status", "purpose",
            "sex", "date_of_birth", "birth_type", "birth_weight_kg",
            "weaning_date", "weaning_weight_kg",
            "sire_tag", "dam_tag", "genetic_merit_index",
            "status", "acquisition_date", "acquisition_method", "purchase_price",
            "farm", "current_paddock",
            "current_weight_kg", "height_cm", "body_length_cm",
            "temperament_score", "lameness_score",
            "date_of_death", "cause_of_death", "culling_reason",
            "notes",
        ]


# =============================================================================
# SHARED HELPER — build animal detail context
# =============================================================================
def _animal_detail_context(animal):
    milk_total      = animal.productionrecord_set.aggregate(t=Sum("milk_yield_liters"))["t"] or 0
    total_expenses  = animal.expenserecord_set.aggregate(t=Sum("amount"))["t"] or 0
    active_diseases = animal.diseaserecord_set.filter(recovery_date__isnull=True).count()
    last_location   = LocationLog.objects.filter(animal=animal).order_by("-timestamp").first()

    weight_history = list(
        animal.healthobservation_set.order_by("created_at").values("created_at", "weight_kg")
    )
    weight_labels = [w["created_at"].strftime("%d %b") for w in weight_history if w["weight_kg"]]
    weight_data   = [w["weight_kg"]  for w in weight_history if w["weight_kg"]]

    milk_history = list(
        animal.productionrecord_set.order_by("record_date").values("record_date", "milk_yield_liters")
    )
    milk_labels = [m["record_date"].strftime("%d %b") for m in milk_history if m["milk_yield_liters"]]
    milk_data   = [m["milk_yield_liters"] for m in milk_history if m["milk_yield_liters"]]

    return {
        "animal":          animal,
        "farms":           Farm.objects.all(),
        "paddocks":        Paddock.objects.select_related("farm").all(),
        "diseases":        animal.diseaserecord_set.all(),
        "vaccinations":    animal.vaccinationrecord_set.all(),
        "treatments":      animal.treatmentrecord_set.all(),
        "health":          animal.healthobservation_set.order_by("-created_at"),
        "breeding":        animal.female_events.select_related("male"),
        "calving":         animal.calvings.all(),
        "production":      animal.productionrecord_set.order_by("-record_date"),
        "expenses":        animal.expenserecord_set.all(),
        "milk_total":      milk_total,
        "total_expenses":  total_expenses,
        "active_diseases": active_diseases,
        "last_location":   last_location,
        "weight_labels":   json.dumps(weight_labels),
        "weight_data":     json.dumps(weight_data),
        "milk_labels":     json.dumps(milk_labels),
        "milk_data":       json.dumps(milk_data),
    }


# =============================================================================
# AUTH
# =============================================================================

def home(request):
    return render(request, "home.html")

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password"),
        )
        if user:
            login(request, user)

            next_url = request.POST.get("next") or request.GET.get("next")
            return redirect(next_url or "dashboard")

        messages.error(request, "Invalid username or password")

    return render(request, "login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


# =============================================================================
# DASHBOARD
# =============================================================================

@login_required
def dashboard(request):
    animals = Animal.objects.all()[:200]
    alerts  = Alert.objects.filter(is_resolved=False)
    sales   = SaleRecord.objects.all()

    revenue    = SaleRecord.objects.aggregate(t=Sum("sale_price"))["t"] or 0
    milk_total = ProductionRecord.objects.aggregate(t=Sum("milk_yield_liters"))["t"] or 0

    status_qs = Animal.objects.values("status").annotate(count=Count("status"))
    breed_qs  = Animal.objects.values("breed").annotate(count=Count("id"))

    milk_qs = (
        ProductionRecord.objects
        .values("record_date")
        .annotate(total=Sum("milk_yield_liters"))
        .order_by("record_date")
    )
    milk_labels = json.dumps([str(r["record_date"]) for r in milk_qs])
    milk_data   = json.dumps([float(r["total"] or 0) for r in milk_qs])

    weight_qs = (
        ProductionRecord.objects
        .values("record_date")
        .annotate(avg_gain=Avg("weight_gain_kg"))
        .order_by("record_date")
    )
    weight_labels = json.dumps([str(r["record_date"]) for r in weight_qs])
    weight_data   = json.dumps([float(r["avg_gain"] or 0) for r in weight_qs])

    events = []
    for v in VaccinationRecord.objects.select_related("animal"):
        events.append({
            "title": f"Vaccine {v.vaccine_name} – {v.animal.tag_number}",
            "start": v.date_administered.isoformat(),
        })
    for t in TreatmentRecord.objects.select_related("animal"):
        events.append({
            "title": f"Treatment {t.medication}",
            "start": t.treatment_date.isoformat(),
        })

    return render(request, "index.html", {
        "animals": animals, "alerts": alerts, "sales": sales,
        "total_animals":  Animal.objects.count(),
        "total_farms":    Farm.objects.count(),
        "total_alerts":   alerts.count(),
        "total_devices":  Device.objects.count(),
        "revenue":        revenue,
        "milk_total":     milk_total,
        "status_labels":  json.dumps([s["status"] for s in status_qs]),
        "status_data":    json.dumps([s["count"]  for s in status_qs]),
        "breed_labels":   json.dumps([b["breed"]  for b in breed_qs]),
        "breed_counts":   json.dumps([b["count"]  for b in breed_qs]),
        "milk_labels":    milk_labels,
        "milk_data":      milk_data,
        "weight_labels":  weight_labels,
        "weight_data":    weight_data,
        "events":         json.dumps(events),
    })


# =============================================================================
# FARM & PADDOCK
# =============================================================================

def farm_list(request):
    data = Farm.objects.all()
    q = request.GET.get("q")
    if q:
        data = data.filter(name__icontains=q)
    return render(request, "farm.html", {"data": data, "total_farms": Farm.objects.count()})


def paddock_list(request):
    data = Paddock.objects.select_related("farm")
    q = request.GET.get("q")
    if q:
        data = data.filter(name__icontains=q)

    return render(request, "paddock.html", {
        "data":            data,
        "total_paddocks":  data.count(),
        "total_capacity":  data.aggregate(t=Sum("capacity"))["t"] or 0,
        "farm_count":      Farm.objects.count(),
    })


# =============================================================================
# GPS / FARM MAP
# =============================================================================

def farm_map_view(request):
    farms    = Farm.objects.prefetch_related("paddocks").all()
    paddocks = Paddock.objects.select_related("farm").all()
    animals  = Animal.objects.select_related("current_paddock", "farm").filter(status="ACTIVE")

    farm_data = []
    for f in farms:
        farm_data.append({
            "id":            f.id,
            "name":          f.name,
            "owner":         f.owner,
            "location":      f.location_name,
            "size_hectares": f.size_hectares,
            "polygon":       f.boundary_polygon,
            "center":        [f.latitude, f.longitude],
            "radius":        round(f.radius_m, 1),
        })

    paddock_data = []
    for p in paddocks:
        animals_in = animals.filter(current_paddock=p)
        paddock_data.append({
            "id":           p.id,
            "name":         p.name,
            "farm":         p.farm.name,
            "farm_id":      p.farm.id,
            "capacity":     p.capacity,
            "animal_count": animals_in.count(),
            "polygon":      p.boundary_polygon,
            "center":       [p.latitude, p.longitude],
            "radius":       round(p.smart_radius_m, 1),
        })

    animal_data = []
    for a in animals:
        last_log = LocationLog.objects.filter(animal=a).order_by("-timestamp").first()
        if last_log:
            lat, lon = last_log.latitude, last_log.longitude
        elif a.current_paddock:
            lat = round(a.current_paddock.latitude  + 0.0001, 6)
            lon = round(a.current_paddock.longitude + 0.0001, 6)
        else:
            continue

        outside = False
        if a.current_paddock:
            outside = not a.current_paddock.contains(lat, lon)

        animal_data.append({
            "id":      str(a.id),
            "tag":     a.tag_number,
            "breed":   a.breed,
            "purpose": a.purpose,
            "sex":     a.sex,
            "lat":     lat,
            "lon":     lon,
            "paddock": a.current_paddock.name if a.current_paddock else "Unassigned",
            "farm":    a.farm.name,
            "outside": outside,
            "weight":  a.current_weight_kg,
        })

    outside_animals = [a for a in animal_data if a["outside"]]
    if outside_animals:
        _send_geofence_alert_email(outside_animals)

    return render(request, "location.html", {
        "farms_json":        json.dumps(farm_data),
        "paddocks_json":     json.dumps(paddock_data),
        "animals_json":      json.dumps(animal_data),
        "farm_count":        len(farm_data),
        "animal_count":      len(animal_data),
        "paddock_count":     len(paddock_data),
        "geofence_breaches": len(outside_animals),
    })


def _send_geofence_alert_email(outside_animals):
    subject        = f"🚨 Geofence Breach — {len(outside_animals)} Animal(s) Outside Boundary"
    from_email     = settings.DEFAULT_FROM_EMAIL
    recipient_list = getattr(settings, "ALERT_EMAIL_RECIPIENTS", [])
    if not recipient_list:
        return

    html_content = render_to_string("email.html", {
        "animals":      outside_animals,
        "breach_count": len(outside_animals),
        "timestamp":    now().strftime("%d %b %Y, %H:%M"),
    })
    text_content = (
        f"{len(outside_animals)} animal(s) detected outside paddock boundaries. "
        "Check the Smart Farm dashboard immediately."
    )
    msg = EmailMultiAlternatives(subject, text_content, from_email, recipient_list)
    msg.attach_alternative(html_content, "text/html")
    try:
        msg.send()
    except Exception:
        pass


# =============================================================================
# ANIMAL — list / detail / update / delete
# =============================================================================

def animal_list(request):
    data = Animal.objects.annotate(
        total_diseases=Count("diseaserecord"),
        total_breedings=Count("female_events"),
        total_milk=Sum("productionrecord__milk_yield_liters"),
        total_expenses=Sum("expenserecord__amount"),
    )
    if request.GET.get("q"):
        data = data.filter(tag_number__icontains=request.GET["q"])
    if request.GET.get("status"):
        data = data.filter(status=request.GET["status"])

    return render(request, "animal.html", {
        "data":           data,
        "total_animals":  Animal.objects.count(),
        "total_farms":    Farm.objects.count(),
        "total_devices":  Device.objects.count(),
        "total_alerts":   Alert.objects.count(),
    })

@login_required
def animal_detail(request, pk):
    animal = get_object_or_404(Animal, id=pk)
    ctx = _animal_detail_context(animal)
    ctx["form"] = AnimalEditForm(instance=animal)
    return render(request, "animal_detail.html", ctx)


@login_required
def animal_update(request, pk):
    animal = get_object_or_404(Animal, pk=pk)

    if request.method == "POST":
        form = AnimalEditForm(request.POST, instance=animal)

        if form.is_valid():
            form.save()
            return redirect(
                reverse("animal_detail", kwargs={"pk": pk}) + "?saved=1"
            )

        # Invalid — re-render detail page with errors so Edit tab opens
        ctx = _animal_detail_context(animal)
        ctx["form"] = form
        return render(request, "animal_detail.html", ctx)

    return redirect("animal_detail", pk=pk)


@login_required
def animal_delete(request, pk):
    animal = get_object_or_404(Animal, pk=pk)
    tag    = animal.tag_number
    animal.delete()
    messages.success(request, f"Animal {tag} has been deleted.")
    return redirect("animal_list")


# =============================================================================
# HEALTH
# =============================================================================

def disease_list(request):
    data = DiseaseRecord.objects.select_related("animal")
    if request.GET.get("q"):
        data = data.filter(disease_name__icontains=request.GET["q"])

    disease_dist = list(
        data.values("disease_name").annotate(count=Count("id")).order_by("-count")[:10]
    )

    return render(request, "disease.html", {
        "data":            data,
        "total":           data.count(),
        "active":          data.filter(recovery_date__isnull=True).count(),
        "recovered":       data.filter(recovery_date__isnull=False).count(),
        "disease_labels":  json.dumps([d["disease_name"] for d in disease_dist]),
        "disease_counts":  json.dumps([d["count"] for d in disease_dist]),
    })


def vaccination_list(request):
    data  = VaccinationRecord.objects.select_related("animal")
    if request.GET.get("q"):
        data = data.filter(vaccine_name__icontains=request.GET["q"])
    today = now().date()

    vax_dist = list(
        data.values("vaccine_name").annotate(count=Count("id")).order_by("-count")[:10]
    )

    return render(request, "vaccination.html", {
        "data":                    data,
        "total_vaccinations":      data.count(),
        "upcoming_vaccinations":   data.filter(next_due_date__gte=today).count(),
        "completed_vaccinations":  data.filter(date_administered__isnull=False).count(),
        "missed_vaccinations":     data.filter(next_due_date__lt=today).count(),
        "vax_labels":              json.dumps([v["vaccine_name"] for v in vax_dist]),
        "vax_counts":              json.dumps([v["count"] for v in vax_dist]),
    })


def treatment_list(request):
    data = TreatmentRecord.objects.select_related("animal")
    if request.GET.get("q"):
        data = data.filter(diagnosis__icontains=request.GET["q"])

    med_dist = list(
        data.values("medication").annotate(count=Count("id")).order_by("-count")[:10]
    )

    return render(request, "treatment.html", {
        "data":       data,
        "total":      data.count(),
        "med_labels": json.dumps([m["medication"] for m in med_dist]),
        "med_counts": json.dumps([m["count"] for m in med_dist]),
    })


def health_observation_list(request):
    data  = HealthObservation.objects.select_related("animal")
    stats = data.aggregate(avg_temp=Avg("temperature_c"), avg_weight=Avg("weight_kg"))

    temp_qs = (
        data.values("created_at__date")
        .annotate(avg_t=Avg("temperature_c"))
        .order_by("created_at__date")
    )

    return render(request, "health.html", {
        "data":        data,
        "total":       data.count(),
        "avg_temp":    round(stats["avg_temp"],   1) if stats["avg_temp"]   else 0,
        "avg_weight":  round(stats["avg_weight"], 1) if stats["avg_weight"] else 0,
        "temp_labels": json.dumps([str(r["created_at__date"]) for r in temp_qs]),
        "temp_data":   json.dumps([float(r["avg_t"] or 0) for r in temp_qs]),
    })


def labtest_list(request):
    data = LabTest.objects.select_related("animal")
    return render(request, "lab.html", {"data": data, "total": data.count()})


# =============================================================================
# BREEDING
# =============================================================================

def breeding_list(request):
    data  = BreedingEvent.objects.select_related("female", "male")
    stats = data.aggregate(
        total=Count("id"),
        pregnant=Count("id", filter=Q(confirmed_pregnant=True)),
        ai_count=Count("id", filter=Q(method="AI")),
        natural_count=Count("id", filter=Q(method="NATURAL")),
    )

    monthly = list(
        data.values("breeding_date__month", "breeding_date__year")
        .annotate(count=Count("id"))
        .order_by("breeding_date__year", "breeding_date__month")
    )

    return render(request, "breeding.html", {
        **{"data": data},
        **stats,
        "month_labels": json.dumps([
            f"{r['breeding_date__year']}-{r['breeding_date__month']:02d}" for r in monthly
        ]),
        "month_data": json.dumps([r["count"] for r in monthly]),
    })


def calving_list(request):
    data = CalvingRecord.objects.select_related("mother", "calf")

    monthly = list(
        data.values("calving_date__month", "calving_date__year")
        .annotate(count=Count("id"))
        .order_by("calving_date__year", "calving_date__month")
    )

    return render(request, "calving.html", {
        "calvings":        data,
        "total_calvings":  data.count(),
        "calving_labels":  json.dumps([
            f"{r['calving_date__year']}-{r['calving_date__month']:02d}" for r in monthly
        ]),
        "calving_monthly": json.dumps([r["count"] for r in monthly]),
    })


def reproductive_list(request):
    data = ReproductiveStatus.objects.select_related("animal")
    status_dist = list(data.values("reproductive_status").annotate(count=Count("id")))

    return render(request, "reproductive.html", {
        "data":         data,
        "total":        data.count(),
        "repro_labels": json.dumps([s["reproductive_status"] for s in status_dist]),
        "repro_counts": json.dumps([s["count"] for s in status_dist]),
    })


def lactation_list(request):
    data      = LactationRecord.objects.select_related("animal")
    avg_yield = data.aggregate(avg=Avg("peak_yield_liters"))["avg"] or 0

    return render(request, "lactation.html", {
        "data":      data,
        "total":     data.count(),
        "avg_yield": round(avg_yield, 1),
    })


# =============================================================================
# PRODUCTION & FEEDING
# =============================================================================

def production_list(request):
    data  = ProductionRecord.objects.select_related("animal")
    stats = data.aggregate(
        avg_milk=Avg("milk_yield_liters"),
        avg_weight_gain=Avg("weight_gain_kg"),
        avg_feed=Avg("feed_consumption_kg"),
    )

    milk_trend = list(
        data.values("record_date")
        .annotate(total_milk=Sum("milk_yield_liters"), avg_gain=Avg("weight_gain_kg"))
        .order_by("record_date")
    )

    feed_milk_pairs = list(
        data.filter(
            feed_consumption_kg__isnull=False,
            milk_yield_liters__isnull=False,
        ).values("feed_consumption_kg", "milk_yield_liters")[:50]
    )

    return render(request, "productive.html", {
        "data":               data,
        "total":              data.count(),
        "avg_milk":           round(stats["avg_milk"],        1) if stats["avg_milk"]        else 0,
        "avg_weight_gain":    round(stats["avg_weight_gain"], 1) if stats["avg_weight_gain"] else 0,
        "avg_feed":           round(stats["avg_feed"],        1) if stats["avg_feed"]        else 0,
        "prod_milk_labels":   json.dumps([str(r["record_date"]) for r in milk_trend]),
        "prod_milk_data":     json.dumps([float(r["total_milk"] or 0) for r in milk_trend]),
        "prod_weight_labels": json.dumps([str(r["record_date"]) for r in milk_trend]),
        "prod_weight_data":   json.dumps([float(r["avg_gain"] or 0) for r in milk_trend]),
        "scatter_feed":       json.dumps([float(r["feed_consumption_kg"]) for r in feed_milk_pairs]),
        "scatter_milk":       json.dumps([float(r["milk_yield_liters"]) for r in feed_milk_pairs]),
    })


def feeding_list(request):
    data  = FeedingRecord.objects.select_related("animal", "feed_type")
    stats = data.aggregate(
        total=Count("id"),
        total_feed=Sum("quantity_kg"),
        avg_feed=Avg("quantity_kg"),
        unique_animals=Count("animal", distinct=True),
    )

    feed_dist = list(
        data.values("feed_type__name").annotate(total=Sum("quantity_kg")).order_by("-total")[:8]
    )
    daily_feed = list(
        data.values("feeding_time__date")
        .annotate(total=Sum("quantity_kg"))
        .order_by("feeding_time__date")
    )

    return render(request, "feeding.html", {
        "data":             data,
        "total":            stats["total"],
        "total_feed":       round(stats["total_feed"], 1) if stats["total_feed"] else 0,
        "avg_feed":         round(stats["avg_feed"],   1) if stats["avg_feed"]   else 0,
        "unique_animals":   stats["unique_animals"],
        "feed_type_labels": json.dumps([r["feed_type__name"] or "Unknown" for r in feed_dist]),
        "feed_type_data":   json.dumps([float(r["total"] or 0) for r in feed_dist]),
        "feed_day_labels":  json.dumps([str(r["feeding_time__date"]) for r in daily_feed]),
        "feed_day_data":    json.dumps([float(r["total"] or 0) for r in daily_feed]),
    })


def feedtype_list(request):
    return render(request, "feedtype.html", {"data": FeedType.objects.all()})


# =============================================================================
# GPS & TRACKING
# =============================================================================

def location_log_list(request):
    data = LocationLog.objects.select_related("animal").order_by("-timestamp")[:500]
    return render(request, "location_logs.html", {
        "data":            data,
        "total_logs":      LocationLog.objects.count(),
        "unique_animals":  LocationLog.objects.values("animal").distinct().count(),
    })


def movement_list(request):
    data = MovementEvent.objects.select_related("animal", "from_paddock", "to_paddock")

    paddock_dist = list(
        data.values("to_paddock__name").annotate(count=Count("id")).order_by("-count")[:8]
    )
    monthly = list(
        data.values("created_at__month", "created_at__year")
        .annotate(count=Count("id"))
        .order_by("created_at__year", "created_at__month")
    )

    return render(request, "movement.html", {
        "data":              data,
        "total_movements":   data.count(),
        "move_labels":       json.dumps([r["to_paddock__name"] or "Unknown" for r in paddock_dist]),
        "move_counts":       json.dumps([r["count"] for r in paddock_dist]),
        "move_month_labels": json.dumps([
            f"{r['created_at__year']}-{r['created_at__month']:02d}" for r in monthly
        ]),
        "move_month_data":   json.dumps([r["count"] for r in monthly]),
    })


def device_list(request):
    data = Device.objects.select_related("assigned_animal")
    if request.GET.get("q"):
        data = data.filter(device_id__icontains=request.GET["q"])

    active_threshold = now() - timedelta(hours=24)
    type_dist = list(data.values("device_type").annotate(count=Count("id")))
    low    = Device.objects.filter(battery_level__lt=20).count()
    medium = Device.objects.filter(battery_level__gte=20, battery_level__lt=60).count()
    high   = Device.objects.filter(battery_level__gte=60).count()

    return render(request, "device.html", {
        "data":                data,
        "total_devices":       Device.objects.count(),
        "active_devices":      Device.objects.filter(last_sync_time__gte=active_threshold).count(),
        "low_battery_devices": low,
        "device_type_labels":  json.dumps([t["device_type"] for t in type_dist]),
        "device_type_counts":  json.dumps([t["count"] for t in type_dist]),
        "battery_labels":      json.dumps(["Low (<20%)", "Medium (20-60%)", "High (>60%)"]),
        "battery_data":        json.dumps([low, medium, high]),
    })


def geofence_list(request):
    data = Geofence.objects.select_related("paddock")
    return render(request, "geofence.html", {"data": data, "total": data.count()})


def environmental_list(request):
    data  = EnvironmentalLog.objects.select_related("paddock")
    stats = data.aggregate(avg_temp=Avg("temperature_c"), avg_humidity=Avg("humidity_percent"))

    temp_trend = list(
        data.values("created_at__date")
        .annotate(avg_t=Avg("temperature_c"), avg_h=Avg("humidity_percent"))
        .order_by("created_at__date")
    )

    return render(request, "environmental.html", {
        "data":         data,
        "total":        data.count(),
        "avg_temp":     round(stats["avg_temp"],     1) if stats["avg_temp"]     else 0,
        "avg_humidity": round(stats["avg_humidity"], 1) if stats["avg_humidity"] else 0,
        "env_labels":   json.dumps([str(r["created_at__date"]) for r in temp_trend]),
        "env_temp":     json.dumps([float(r["avg_t"] or 0) for r in temp_trend]),
        "env_humidity": json.dumps([float(r["avg_h"] or 0) for r in temp_trend]),
    })


# =============================================================================
# FINANCE & ALERTS
# =============================================================================

def expense_list(request):
    data  = ExpenseRecord.objects.select_related("animal")
    stats = data.aggregate(
        total=Count("id"),
        total_amount=Sum("amount"),
        avg_amount=Avg("amount"),
    )

    cat_dist = list(
        data.values("category").annotate(total=Sum("amount")).order_by("-total")[:8]
    )

    return render(request, "expense.html", {
        "data":           data,
        "total":          stats["total"],
        "total_amount":   round(stats["total_amount"], 2) if stats["total_amount"] else 0,
        "avg_amount":     round(stats["avg_amount"],   2) if stats["avg_amount"]   else 0,
        "expense_labels": json.dumps([r["category"] or "Other" for r in cat_dist]),
        "expense_data":   json.dumps([float(r["total"] or 0) for r in cat_dist]),
    })


def sale_list(request):
    data  = SaleRecord.objects.select_related("animal")
    stats = data.aggregate(
        total=Count("id"),
        total_revenue=Sum("sale_price"),
        avg_price=Avg("sale_price"),
        avg_weight=Avg("weight_at_sale_kg"),
    )

    monthly = list(
        data.values("sale_date__month", "sale_date__year")
        .annotate(revenue=Sum("sale_price"))
        .order_by("sale_date__year", "sale_date__month")
    )

    return render(request, "sale.html", {
        "data":              data,
        "total":             stats["total"],
        "total_revenue":     round(stats["total_revenue"], 2) if stats["total_revenue"] else 0,
        "avg_price":         round(stats["avg_price"],     2) if stats["avg_price"]     else 0,
        "avg_weight":        round(stats["avg_weight"],    1) if stats["avg_weight"]    else 0,
        "sale_month_labels": json.dumps([
            f"{r['sale_date__year']}-{r['sale_date__month']:02d}" for r in monthly
        ]),
        "sale_month_data":   json.dumps([float(r["revenue"] or 0) for r in monthly]),
    })


def alert_list(request):
    data = Alert.objects.select_related("animal")
    type_dist = list(data.values("alert_type").annotate(count=Count("id")).order_by("-count"))

    return render(request, "alert.html", {
        "data":         data,
        "total":        data.count(),
        "overdue":      data.filter(status="OVERDUE").count(),
        "due_soon":     data.filter(status="ABOUT_TO_DUE").count(),
        "alert_labels": json.dumps([t["alert_type"] for t in type_dist]),
        "alert_counts": json.dumps([t["count"] for t in type_dist]),
    })


# =============================================================================
# QR SCAN (public)
# =============================================================================

def scan_qr(request):
    qr_code = request.GET.get("qr")
    if not qr_code:
        return render(request, "scan_qr.html", {"error": "No QR code provided"})
    animal = get_object_or_404(Animal, qr_code=qr_code)
    return redirect("animal_detail", pk=animal.id)


# =============================================================================
# GPS CONSOLE
# =============================================================================

ANIMAL_TAG = "ZW0068"

GPS_STATE: dict = {
    "sats":    0,
    "has_fix": False,
}


def _accuracy_label(sats: int) -> str:
    if sats >= 14: return "Excellent (1-2m)"
    if sats >= 11: return "Good (2-5m)"
    if sats >= 8:  return "Moderate (5-10m)"
    if sats >= 6:  return "Poor (10-50m)"
    if sats > 0:   return "Very Poor (>100m)"
    return "No fix"


@require_GET
def gps_console(request):
    try:
        animal = Animal.objects.get(tag_number=ANIMAL_TAG)
    except Animal.DoesNotExist:
        animal = None

    return render(request, "gps_console.html", {
        "animal":     animal,
        "animal_tag": ANIMAL_TAG,
    })


@require_GET
def gps_stream_json(request):
    try:
        animal = Animal.objects.get(tag_number=ANIMAL_TAG)
    except Animal.DoesNotExist:
        return JsonResponse(
            {"error": f"Animal {ANIMAL_TAG} not found.", "lines": []}, status=404
        )

    from django.http import JsonResponse

    logs = list(
        LocationLog.objects
        .filter(animal=animal)
        .order_by("-timestamp")[:30]
    )
    total_saved = LocationLog.objects.filter(animal=animal).count()

    has_fix   = bool(logs) or GPS_STATE["has_fix"]
    latest    = logs[0] if logs else None
    displayed = list(reversed(logs))

    sats     = GPS_STATE["sats"]
    accuracy = _accuracy_label(sats)

    if logs:
        avg_lat   = sum(l.latitude  for l in logs) / len(logs)
        avg_lon   = sum(l.longitude for l in logs) / len(logs)
        latest_ts = latest.timestamp.strftime("%H:%M:%S")
    else:
        avg_lat = avg_lon = 0.0
        latest_ts = None

    lines = []
    for log in displayed:
        ts_str = log.timestamp.strftime("%H:%M:%S")
        lines.append({
            "tag": "RAW",
            "cls": "tag-raw",
            "body": (
                f"[RAW] LAT: {log.latitude:.6f}"
                f" | LON: {log.longitude:.6f}"
                f" | SAT: {sats}"
                f" | TS: {ts_str}"
            ),
        })
        lines.append({
            "tag": "SAT",
            "cls": "tag-acc",
            "body": f"[SAT]  {sats} satellites  |  {accuracy}",
        })
        lines.append({
            "tag": "SAVE",
            "cls": "tag-save",
            "body": (
                f"SAVED → LocationLog  animal={ANIMAL_TAG}"
                f"  lat={log.latitude:.6f}  lon={log.longitude:.6f}"
                f"  sats={sats}  @ {ts_str}"
            ),
        })

    from django.http import JsonResponse
    return JsonResponse({
        "has_fix":     has_fix,
        "lat":         latest.latitude  if latest else None,
        "lon":         latest.longitude if latest else None,
        "avg_lat":     avg_lat,
        "avg_lon":     avg_lon,
        "sats":        sats,
        "accuracy":    accuracy,
        "samples":     len(logs),
        "total_saved": total_saved,
        "latest_ts":   latest_ts,
        "lines":       lines,
    })
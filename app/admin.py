from django.contrib import admin, messages
from .models import *
from import_export.admin import ExportMixin
from django.db.models import Count, Sum
from django.utils.html import format_html
from .models import (
    Animal,
    DiseaseRecord,
    VaccinationRecord,
    TreatmentRecord,
    HealthObservation,
    BreedingEvent,
    CalvingRecord,
    ProductionRecord,
    ExpenseRecord,
)
from .utils import generate_qr


# =====================================================
# QR REGENERATION ACTIONS
# =====================================================

def _run_regeneration(modeladmin, request, queryset, label="selected"):
    success, failed = 0, 0
    for animal in queryset.iterator():
        try:
            generate_qr(animal)
            success += 1
        except Exception as e:
            failed += 1
            modeladmin.message_user(
                request,
                f"Failed for {animal.tag_number}: {e}",
                level=messages.ERROR,
            )
    level = messages.SUCCESS if not failed else messages.WARNING
    modeladmin.message_user(
        request,
        f"QR regeneration complete ({label}): {success} succeeded, {failed} failed.",
        level=level,
    )


@admin.action(description="🔄 Regenerate QR codes — selected animals")
def regenerate_qr_selected(modeladmin, request, queryset):
    _run_regeneration(modeladmin, request, queryset, label="selected")


@admin.action(description="🔄 Regenerate QR codes — ALL animals")
def regenerate_qr_all(modeladmin, request, queryset):
    _run_regeneration(modeladmin, request, Animal.objects.all(), label="all")


@admin.action(description="🔄 Regenerate QR codes — missing only")
def regenerate_qr_missing(modeladmin, request, queryset):
    missing = Animal.objects.filter(qr_image="")
    if not missing.exists():
        modeladmin.message_user(request, "No animals with missing QR images found.", level=messages.INFO)
        return
    _run_regeneration(modeladmin, request, missing, label="missing")


# =====================================================
# INLINES
# =====================================================

class DiseaseInline(admin.TabularInline):
    model = DiseaseRecord
    extra = 0


class VaccinationInline(admin.TabularInline):
    model = VaccinationRecord
    extra = 0


class TreatmentInline(admin.TabularInline):
    model = TreatmentRecord
    extra = 0


class HealthObservationInline(admin.TabularInline):
    model = HealthObservation
    extra = 0


class BreedingInline(admin.TabularInline):
    model = BreedingEvent
    fk_name = "female"
    extra = 0


class CalvingInline(admin.TabularInline):
    model = CalvingRecord
    fk_name = "mother"
    extra = 0


class ProductionInline(admin.TabularInline):
    model = ProductionRecord
    extra = 0


# =====================================================
# ANIMAL ADMIN
# =====================================================

@admin.register(Animal)
class AnimalAdmin(ExportMixin, admin.ModelAdmin):

    # ✅ ACTIONS WIRED IN
    actions = [
        regenerate_qr_selected,
        regenerate_qr_all,
        regenerate_qr_missing,
    ]

    # =====================================================
    # LIST VIEW
    # =====================================================
    list_display = (
        "tag_number",
        "colored_status",
        "farm",
        "disease_count",
        "breeding_count",
        "milk_total",
        "expense_total",
    )

    list_filter = (
        "status",
        "species",
        "breed",
        "purpose",
        "farm",
        "sex",
    )

    search_fields = (
        "tag_number",
        "qr_code",
        "electronic_id",
        "registration_number",
    )

    readonly_fields = (
        "summary_dashboard",
        "qr_preview",
        "qr_code",
    )

    list_per_page = 25

    # =====================================================
    # INLINES
    # =====================================================
    inlines = [
        DiseaseInline,
        VaccinationInline,
        TreatmentInline,
        HealthObservationInline,
        BreedingInline,
        CalvingInline,
        ProductionInline,
    ]

    # =====================================================
    # OPTIMIZED QUERY
    # =====================================================
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_diseases=Count("diseaserecord"),
            total_breedings=Count("female_events"),
            total_milk=Sum("productionrecord__milk_yield_liters"),
            total_expenses=Sum("expenserecord__amount"),
        )

    # =====================================================
    # COLORED STATUS BADGE
    # =====================================================
    def colored_status(self, obj):
        colors = {
            "ACTIVE": "#28a745",
            "SOLD": "#17a2b8",
            "DECEASED": "#dc3545",
            "QUARANTINED": "#ffc107",
            "CULLED": "#6c757d",
            "MISSING": "#343a40",
        }
        return format_html(
            '<span style="padding:4px 10px; border-radius:8px; '
            'background:{}; color:white; font-weight:600;">{}</span>',
            colors.get(obj.status, "#6c757d"),
            obj.get_status_display(),
        )

    colored_status.short_description = "Status"

    # =====================================================
    # LIST AGGREGATES
    # =====================================================
    def disease_count(self, obj):
        return obj.total_diseases or 0

    def breeding_count(self, obj):
        return obj.total_breedings or 0

    def milk_total(self, obj):
        return obj.total_milk or 0

    def expense_total(self, obj):
        return obj.total_expenses or 0

    # =====================================================
    # DASHBOARD
    # =====================================================
    def summary_dashboard(self, obj):
        active_diseases = obj.diseaserecord_set.filter(
            recovery_date__isnull=True
        ).count()

        total_vaccines = obj.vaccinationrecord_set.count()
        total_calvings = obj.calvings.count()

        milk_total = obj.productionrecord_set.aggregate(
            total=Sum("milk_yield_liters")
        )["total"] or 0

        total_expenses = obj.expenserecord_set.aggregate(
            total=Sum("amount")
        )["total"] or 0

        last_weight_record = obj.healthobservation_set.order_by(
            "-created_at"
        ).first()

        current_weight = (
            last_weight_record.weight_kg
            if last_weight_record
            else "N/A"
        )

        return format_html(
            """
            <div style="padding:20px;
                        background:#f4f6f9;
                        border-radius:12px;
                        margin-bottom:20px;
                        box-shadow:0 2px 8px rgba(0,0,0,0.05);">

                <h2 style="margin-bottom:15px;">📊 Animal Overview</h2>

                <div style="display:grid;
                            grid-template-columns: repeat(auto-fit,minmax(200px,1fr));
                            gap:10px;">

                    <div><strong>🐄 Total Diseases:</strong> {}</div>
                    <div><strong>⚠ Active Diseases:</strong> {}</div>
                    <div><strong>💉 Vaccinations:</strong> {}</div>
                    <div><strong>🤰 Breedings:</strong> {}</div>
                    <div><strong>🐮 Calvings:</strong> {}</div>
                    <div><strong>🥛 Milk Produced:</strong> {} L</div>
                    <div><strong>💰 Total Expenses:</strong> R {}</div>
                    <div><strong>⚖ Current Weight:</strong> {} kg</div>

                </div>
            </div>
            """,
            obj.diseaserecord_set.count(),
            active_diseases,
            total_vaccines,
            obj.female_events.count(),
            total_calvings,
            milk_total,
            total_expenses,
            current_weight,
        )

    summary_dashboard.short_description = "Aggregated Overview"

    # =====================================================
    # QR PREVIEW
    # =====================================================
    def qr_preview(self, obj):
        if obj.qr_image:
            return format_html(
                '<img src="{}" width="150" style="border-radius:10px;" />',
                obj.qr_image.url
            )
        return "No QR Code"

    qr_preview.short_description = "QR Code"

    # =====================================================
    # FIELDSETS
    # =====================================================
    fieldsets = (

        ("📌 Identity", {
            "fields": (
                "tag_number",
                "qr_preview",
                "qr_code",
                "electronic_id",
                "registration_number",
            )
        }),

        ("🐄 Classification", {
            "fields": (
                "species",
                "breed",
                "strain",
                "color",
                "horn_status",
                "purpose",
            ),
            "classes": ("collapse",),
        }),

        ("📅 Sex & Lifecycle", {
            "fields": (
                "sex",
                "date_of_birth",
                "birth_type",
                "birth_weight_kg",
                "weaning_date",
                "weaning_weight_kg",
            ),
            "classes": ("collapse",),
        }),

        ("🧬 Lineage", {
            "fields": (
                "sire_tag",
                "dam_tag",
                "genetic_merit_index",
            ),
            "classes": ("collapse",),
        }),

        ("📦 Status & Acquisition", {
            "fields": (
                "status",
                "acquisition_date",
                "acquisition_method",
                "purchase_price",
                "insurance_policy_number",
            ),
            "classes": ("collapse",),
        }),

        ("📍 Location", {
            "fields": (
                "farm",
                "current_paddock",
            ),
        }),

        ("📏 Physical Metrics", {
            "fields": (
                "current_weight_kg",
                "height_cm",
                "body_length_cm",
            ),
            "classes": ("collapse",),
        }),

        ("🩺 Welfare", {
            "fields": (
                "temperament_score",
                "lameness_score",
            ),
            "classes": ("collapse",),
        }),

        ("⚰ Lifecycle End", {
            "fields": (
                "date_of_death",
                "cause_of_death",
                "culling_reason",
            ),
            "classes": ("collapse",),
        }),

        ("📊 Dashboard", {
            "fields": ("summary_dashboard",),
        }),
    )


# =====================================================
# FARM & PADDOCK
# =====================================================

@admin.register(Farm)
class FarmAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("name", "location_name", "size_hectares", "owner")
    search_fields = ("name", "location_name", "owner")
    list_filter = ("location_name",)


@admin.register(Paddock)
class PaddockAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("name", "farm", "capacity", "boundary_radius_m")
    search_fields = ("name", "farm__name")
    list_filter = ("farm",)


# =====================================================
# HEALTH & TREATMENT
# =====================================================

@admin.register(VaccinationRecord)
class VaccinationAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "vaccine_name", "date_administered", "next_due_date")
    search_fields = ("animal__tag_number", "vaccine_name")
    list_filter = ("vaccine_name", "date_administered")


@admin.register(TreatmentRecord)
class TreatmentAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "diagnosis", "medication", "treatment_date")
    search_fields = ("animal__tag_number", "diagnosis", "medication")
    list_filter = ("treatment_date",)


@admin.register(HealthObservation)
class HealthObservationAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "weight_kg", "body_condition_score", "temperature_c", "created_at")
    search_fields = ("animal__tag_number",)
    list_filter = ("created_at",)


@admin.register(LabTest)
class LabTestAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "test_name", "result_value", "test_date")
    search_fields = ("animal__tag_number", "test_name")
    list_filter = ("test_name", "test_date")


@admin.register(DiseaseRecord)
class DiseaseAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "disease_name", "severity", "onset_date", "recovery_date", "chronic")
    search_fields = ("animal__tag_number", "disease_name")
    list_filter = ("severity", "chronic")


# =====================================================
# BREEDING & CALVING
# =====================================================

@admin.register(BreedingEvent)
class BreedingAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("female", "male", "method", "breeding_date", "confirmed_pregnant")
    search_fields = ("female__tag_number", "male__tag_number")
    list_filter = ("method", "confirmed_pregnant", "breeding_date")


@admin.register(CalvingRecord)
class CalvingAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("mother", "calf", "calving_date", "birth_weight_kg")
    search_fields = ("mother__tag_number", "calf__tag_number")
    list_filter = ("calving_date",)


# =====================================================
# PRODUCTION & FEEDING
# =====================================================

@admin.register(ProductionRecord)
class ProductionAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "record_date", "milk_yield_liters", "weight_gain_kg", "feed_consumption_kg")
    search_fields = ("animal__tag_number",)
    list_filter = ("record_date",)


@admin.register(FeedType)
class FeedTypeAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("name", "energy_mj", "protein_percent", "cost_per_kg")
    search_fields = ("name",)


@admin.register(FeedingRecord)
class FeedingAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "feed_type", "quantity_kg", "feeding_time")
    search_fields = ("animal__tag_number", "feed_type__name")
    list_filter = ("feeding_time", "feed_type")


# =====================================================
# GPS & MOVEMENT
# =====================================================

@admin.register(LocationLog)
class LocationLogAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "timestamp", "latitude", "longitude", "speed")
    search_fields = ("animal__tag_number",)
    list_filter = ("timestamp",)


@admin.register(MovementEvent)
class MovementEventAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "from_paddock", "to_paddock", "moved_by", "created_at")
    search_fields = ("animal__tag_number",)
    list_filter = ("created_at",)


@admin.register(Device)
class DeviceAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("device_id", "device_type", "battery_level", "assigned_animal")
    search_fields = ("device_id", "assigned_animal__tag_number")
    list_filter = ("device_type",)


@admin.register(Geofence)
class GeofenceAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("paddock", "radius_meters", "alert_on_exit")
    search_fields = ("paddock__name",)
    list_filter = ("alert_on_exit",)


# =====================================================
# ALERTS, EXPENSES & SALES
# =====================================================

@admin.register(Alert)
class AlertAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "alert_type", "status_badge", "due_date")
    list_filter = ("status", "alert_type")

    def status_badge(self, obj):
        colors = {
            "OVERDUE": "red",
            "ABOUT_TO_DUE": "orange",
            "DUE": "blue",
        }
        color = colors.get(obj.status, "green")
        return format_html(
            '<span style="background:{}; color:white; padding:4px 10px; border-radius:6px;">{}</span>',
            color,
            obj.status,
        )

    status_badge.short_description = "Status"


@admin.register(ExpenseRecord)
class ExpenseAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "category", "amount", "expense_date")
    search_fields = ("animal__tag_number", "category")
    list_filter = ("category", "expense_date")


@admin.register(SaleRecord)
class SaleAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "sale_date", "buyer", "sale_price", "weight_at_sale_kg")
    search_fields = ("animal__tag_number", "buyer")
    list_filter = ("sale_date",)
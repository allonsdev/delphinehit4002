from django.contrib import admin
from .models import *
from import_export.admin import ExportMixin

# --------------------------
# Farm & Paddock
# --------------------------
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

# --------------------------
# Animal & QR codes
# --------------------------
@admin.register(Animal)
class AnimalAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("tag_number", "breed", "sex", "status", "farm", "current_weight_kg", "current_paddock")
    search_fields = ("tag_number", "qr_code", "breed")
    list_filter = ("breed", "sex", "status", "farm")

# --------------------------
# Health & Treatment
# --------------------------
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

# --------------------------
# Breeding & Calving
# --------------------------
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

# --------------------------
# Production & Feeding
# --------------------------
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

# --------------------------
# GPS & Movement
# --------------------------
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

# --------------------------
# Alerts, Expenses & Sales
# --------------------------
@admin.register(Alert)
class AlertAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("animal", "alert_type", "message", "is_resolved", "created_at")
    search_fields = ("animal__tag_number", "alert_type", "message")
    list_filter = ("alert_type", "is_resolved", "created_at")

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

from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.home, name="home"),
    path("login/",  views.login_view,  name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),

    # Farm & Paddock
    path("farms/",    views.farm_list,    name="farm_list"),
    path("paddocks/", views.paddock_list, name="paddock_list"),

    # Animals
    path("animals/",                      views.animal_list,   name="animal_list"),
    path("animals/<uuid:pk>/",            views.animal_detail, name="animal_detail"),
    path("animals/<uuid:pk>/edit/",       views.animal_update, name="animal_update"),
    path("animals/<uuid:pk>/delete/",     views.animal_delete, name="animal_delete"),
    path("scan/",                         views.scan_qr,       name="scan_qr"),

    # Health
    path("diseases/",           views.disease_list,             name="disease_list"),
    path("vaccinations/",       views.vaccination_list,          name="vaccination_list"),
    path("treatments/",         views.treatment_list,            name="treatment_list"),
    path("health-observations/",views.health_observation_list,   name="health_observation_list"),
    path("lab-tests/",          views.labtest_list,              name="labtest_list"),

    # Breeding
    path("breeding/",     views.breeding_list,     name="breeding_list"),
    path("calving/",      views.calving_list,       name="calving_list"),
    path("reproductive/", views.reproductive_list,  name="reproductive_list"),
    path("lactation/",    views.lactation_list,     name="lactation_list"),

    # Production
    path("production/",  views.production_list, name="production_list"),
    path("feeding/",     views.feeding_list,    name="feeding_list"),
    path("feed-types/",  views.feedtype_list,   name="feedtype_list"),

    # GPS & Tracking
    path("locations/",   views.farm_map_view,        name="location_log_list"),
    path("movements/",   views.movement_list,         name="movement_list"),
    path("devices/",     views.device_list,           name="device_list"),
    path("geofences/",   views.geofence_list,         name="geofence_list"),
    path("environment/", views.environmental_list,    name="environmental_list"),

    # Finance
    path("expenses/", views.expense_list, name="expense_list"),
    path("sales/",    views.sale_list,    name="sale_list"),
    path("alerts/",   views.alert_list,   name="alert_list"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
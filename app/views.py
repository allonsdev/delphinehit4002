from django.shortcuts import render, get_object_or_404
from app.models import Animal, ReproductiveStatus, LactationRecord, BreedingEvent, TreatmentRecord, VaccinationRecord

def home(request):
    return render(request, "landing/index.html")

def login(request):
    return render(request, "dashboard/login.html")


def dashboard(request):
    return render(request, "dashboard/index.html")

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

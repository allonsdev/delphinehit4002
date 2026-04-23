from io import BytesIO
from django.conf import settings
from django.core.files import File
from django.urls import reverse
import qrcode


def generate_qr(animal):
    """
    Generate or regenerate QR code pointing to animal detail page.
    """

    # ✅ Use Django URL instead of admin
    detail_path = reverse("animal_detail", kwargs={"pk": animal.id})
    full_url = f"{settings.BASE_URL}{detail_path}"

    # Delete old image if exists
    if animal.qr_image:
        animal.qr_image.delete(save=False)

    # Create QR
    qr = qrcode.make(full_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    # Save
    animal.qr_code = full_url
    animal.qr_image.save(f"{animal.tag_number}_qr.png", File(buffer), save=False)
    animal.save(update_fields=["qr_code", "qr_image"])
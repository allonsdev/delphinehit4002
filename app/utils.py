from io import BytesIO

from django.conf import settings
from django.core.files import File

import qrcode


def generate_qr(animal):
    """
    Regenerate the QR code and image for a given Animal instance.
    Deletes the old image file before saving the new one.
    """
    admin_url = f"{settings.BASE_URL}/admin/app/animal/{animal.id}/change/"

    # Delete old image from storage if it exists
    if animal.qr_image:
        animal.qr_image.delete(save=False)

    # Build new QR image
    qr = qrcode.make(admin_url)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)  # critical — prevents corrupt/empty file

    animal.qr_code = admin_url
    animal.qr_image.save(f"{animal.tag_number}_qr.png", File(buffer), save=False)
    animal.save(update_fields=["qr_code", "qr_image"])
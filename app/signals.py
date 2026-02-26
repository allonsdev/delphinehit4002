from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Alert)
def send_alert_email(sender, instance, created, **kwargs):
    if created and not instance.is_resolved:

        subject = f"Livestock Alert: {instance.get_alert_type_display()}"
        message = f"""
        Animal: {instance.animal.tag_number}
        Alert: {instance.message}
        Due Date: {instance.due_date}
        Status: {instance.status}
        """

        send_mail(
            subject,
            message,
            "alerts@yourfarm.com",
            ["recipient@example.com"],
            fail_silently=False,
        )
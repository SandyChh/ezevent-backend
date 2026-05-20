"""
EmailSender adapter (Adapter Pattern — report Section 4.2.2).
Wraps Django's email system. Generates QR PNG and embeds it inline.
FR-11: confirmation email within 30 seconds containing QR ticket.
NFR-L4: unsubscribe link in every email (Spam Act 2003).
"""
import io
import logging
import qrcode
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger("eventease")


class EmailSender:
    @staticmethod
    def generate_qr_png(data: str) -> bytes:
        """Generate a QR code PNG as bytes. Encodes only the opaque token (not PII)."""
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @classmethod
    def send_ticket(cls, to_email: str, registration):
        """
        Send the ticket confirmation email with inline QR code.
        Template: accounts/templates/email/ticket.html / ticket.txt
        """
        event = registration.ticket_tier.event
        context = {
            "attendee_name": registration.attendee.user.full_name,
            "event_title": event.title,
            "event_date": event.start_time,
            "event_venue": event.venue,
            "tier_name": registration.ticket_tier.tier_name,
            "qr_token": registration.qr_code,
            "confirmation_url": (
                f"{settings.FRONTEND_ORIGIN}/confirmation/{registration.pk}"
            ),
            "unsubscribe_url": f"{settings.FRONTEND_ORIGIN}/unsubscribe",
        }

        subject = f"Your ticket for {event.title} — EventEase"
        text_body = render_to_string("email/ticket.txt", context)
        html_body = render_to_string("email/ticket.html", context)

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        email.attach_alternative(html_body, "text/html")

        # Inline QR code as CID-attached PNG
        qr_bytes = cls.generate_qr_png(registration.qr_code)
        qr_image = MIMEImage(qr_bytes, _subtype="png")
        qr_image.add_header("Content-ID", "<qr_ticket>")
        qr_image.add_header("Content-Disposition", "inline", filename="ticket_qr.png")
        email.attach(qr_image)

        email.send(fail_silently=False)

        logger.info(
            "Ticket email sent",
            extra={
                "event_type": "email_sent",
                "user_id": registration.attendee.user.pk,
                "registration_id": registration.pk,
            },
        )

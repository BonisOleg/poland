"""Business logic for pages app (forms / inquiries)."""

from __future__ import annotations

import logging
from typing import Any

from django.conf import settings
from django.core.mail import send_mail

from .models import GroupInquiry

logger = logging.getLogger(__name__)

_INTENT_EMAIL_PL: dict[str, str] = {
    "repertuar": "Repertuar",
    "rezerwacja": "Rezerwacja biletów",
    "specjalna_oferta": "Oferta specjalna",
    "event_firmowy": "Event / wyjazd",
    "voucher": "Voucher / prezent",
    "other": "Inne",
}


def _intent_label(intent_key: str) -> str:
    return _INTENT_EMAIL_PL.get(intent_key, intent_key)


def _inquiry_recipients() -> list[str]:
    return list(getattr(settings, "INQUIRY_EMAIL_TO", []) or [])


def process_group_inquiry(cleaned_data: dict[str, Any]) -> GroupInquiry:
    """Persist group inquiry and send notification email when configured."""

    inquiry = GroupInquiry.objects.create(
        intent=cleaned_data["intent"],
        name=cleaned_data["name"],
        email=cleaned_data["email"],
        phone=cleaned_data.get("phone") or "",
        company=cleaned_data.get("company") or "",
        nip=cleaned_data.get("nip") or "",
        ticket_count=cleaned_data.get("ticket_count") or "",
        message=cleaned_data["message"],
        source_page=cleaned_data.get("source_page") or "",
    )

    recipients = _inquiry_recipients()
    if not recipients:
        logger.info(
            "Group inquiry %s saved; INQUIRY_EMAIL_TO empty, email skipped",
            inquiry.pk,
        )
        return inquiry

    intent_label = _intent_label(cleaned_data["intent"])
    body_lines = [
        f"ID: {inquiry.pk}",
        f"Intent: {intent_label} ({cleaned_data['intent']})",
        f"Strona: {cleaned_data.get('source_page') or '—'}",
        "",
        f"Imię i nazwisko: {cleaned_data['name']}",
        f"Email: {cleaned_data['email']}",
        f"Telefon: {cleaned_data.get('phone') or '—'}",
        f"Firma: {cleaned_data.get('company') or '—'}",
        f"NIP: {cleaned_data.get('nip') or '—'}",
        f"Liczba biletów: {cleaned_data.get('ticket_count') or '—'}",
        "",
        "Wiadomość:",
        cleaned_data["message"],
    ]
    subject = f"[Hype] Zgłoszenie grupowe — {intent_label}"
    try:
        send_mail(
            subject,
            "\n".join(body_lines),
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            "Failed to send email for group inquiry %s (record saved in DB)",
            inquiry.pk,
        )

    return inquiry

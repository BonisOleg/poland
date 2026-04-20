"""POST handlers for group inquiries and contact forms."""

from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _

from .forms import ContactForm, GroupInquiryForm
from .services import process_group_inquiry

logger = logging.getLogger(__name__)


def _safe_redirect_url(request: HttpRequest, raw: str | None, default: str) -> str:
    if not raw:
        return default
    raw = raw.strip()
    if not raw.startswith("/"):
        return default
    if url_has_allowed_host_and_scheme(
        raw,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return raw
    return default


def _inquiry_recipients() -> list[str]:
    return list(getattr(settings, "INQUIRY_EMAIL_TO", []) or [])


def group_inquiry_submit(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("/")
    next_url = _safe_redirect_url(
        request,
        request.POST.get("next"),
        "/dla-firm/",
    )
    if (request.POST.get("website") or "").strip():
        return redirect(next_url)
    form = GroupInquiryForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            _("Nie udało się wysłać zgłoszenia. Sprawdź pola formularza."),
        )
        return redirect(next_url)

    try:
        process_group_inquiry(form.cleaned_data)
    except Exception:
        logger.exception("Failed to save group inquiry")
        messages.error(
            request,
            _("Nie udało się zapisać zgłoszenia. Spróbuj ponownie później."),
        )
        return redirect(next_url)

    messages.success(
        request,
        _("Dziękujemy! Twoje zgłoszenie zostało zapisane."),
    )
    return redirect(next_url)


def contact_submit(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return redirect("/")
    next_url = _safe_redirect_url(
        request,
        request.POST.get("next"),
        "/",
    )
    if (request.POST.get("website") or "").strip():
        return redirect(next_url)
    form = ContactForm(request.POST)
    if not form.is_valid():
        messages.error(
            request,
            _("Nie udało się wysłać wiadomości. Sprawdź pola formularza."),
        )
        return redirect(next_url)

    recipients = _inquiry_recipients()
    if not recipients:
        logger.error("INQUIRY_EMAIL_TO is empty; contact form not sent")
        messages.error(
            request,
            _("Formularz chwilowo niedostępny. Spróbuj później lub zadzwoń do nas."),
        )
        return redirect(next_url)

    data = form.cleaned_data
    body_lines = [
        "Formularz kontaktowy",
        "",
        f"Imię i nazwisko: {data['name']}",
        f"Email: {data['email']}",
        f"Organizacja: {data.get('organization') or '—'}",
        "",
        "Wiadomość:",
        data["message"],
    ]
    subject = "[Hype] Formularz kontaktowy"
    try:
        send_mail(
            subject,
            "\n".join(body_lines),
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
    except Exception:
        logger.exception("Failed to send contact form email")
        messages.error(
            request,
            _("Nie udało się wysłać wiadomości. Spróbuj ponownie później."),
        )
        return redirect(next_url)

    messages.success(
        request,
        _("Dziękujemy! Wiadomość została wysłana."),
    )
    return redirect(next_url)

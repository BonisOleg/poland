from django import forms
from django.utils.translation import gettext_lazy as _


GROUP_INTENT_CHOICES: tuple[tuple[str, str], ...] = (
    ("repertuar", _("Repertuar")),
    ("rezerwacja", _("Rezerwacja biletów")),
    ("specjalna_oferta", _("Oferta specjalna")),
    ("event_firmowy", _("Event / wyjazd")),
    ("voucher", _("Voucher / prezent")),
    ("other", _("Inne")),
)


class GroupInquiryForm(forms.Form):
    name = forms.CharField(label=_("Imię i nazwisko"), max_length=200)
    email = forms.EmailField(label=_("Email"))
    phone = forms.CharField(label=_("Telefon"), max_length=40, required=False)
    company = forms.CharField(label=_("Firma"), max_length=300, required=False)
    nip = forms.CharField(label=_("NIP"), max_length=20, required=False)
    ticket_count = forms.CharField(
        label=_("Szacowana liczba biletów"),
        max_length=50,
        required=False,
    )
    message = forms.CharField(label=_("Wiadomość"), widget=forms.Textarea(attrs={"rows": 4}))
    intent = forms.ChoiceField(choices=GROUP_INTENT_CHOICES)
    source_page = forms.CharField(max_length=200, required=False)
    next = forms.CharField(max_length=500, required=False)
    website = forms.CharField(required=False)  # honeypot — handled in view


class ContactForm(forms.Form):
    name = forms.CharField(label=_("Imię i nazwisko"), max_length=200)
    email = forms.EmailField(label=_("Email"))
    organization = forms.CharField(label=_("Organizacja"), max_length=300, required=False)
    message = forms.CharField(label=_("Wiadomość"), widget=forms.Textarea(attrs={"rows": 5}))
    next = forms.CharField(max_length=500, required=False)
    website = forms.CharField(required=False)  # honeypot — handled in view

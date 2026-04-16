from django import forms
from django.utils.translation import gettext_lazy as _


class VoucherCheckoutForm(forms.Form):
    first_name = forms.CharField(
        max_length=100,
        label=_("Imię"),
        widget=forms.TextInput(attrs={"autocomplete": "given-name", "class": "checkout-form__input"}),
    )
    last_name = forms.CharField(
        max_length=100,
        label=_("Nazwisko"),
        widget=forms.TextInput(attrs={"autocomplete": "family-name", "class": "checkout-form__input"}),
    )
    email = forms.EmailField(
        label=_("E-mail"),
        widget=forms.EmailInput(attrs={"autocomplete": "email", "class": "checkout-form__input"}),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label=_("Telefon (opcjonalnie)"),
        widget=forms.TextInput(attrs={"autocomplete": "tel", "class": "checkout-form__input"}),
    )

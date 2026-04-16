import json
import logging

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST

from .forms import VoucherCheckoutForm
from .models import Voucher, VoucherOrder
from . import services

logger = logging.getLogger(__name__)


def checkout_view(request: HttpRequest, slug: str) -> HttpResponse:
    voucher = get_object_or_404(Voucher, slug=slug, is_active=True)
    form = VoucherCheckoutForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        order = VoucherOrder.objects.create(
            voucher=voucher,
            buyer_first_name=form.cleaned_data["first_name"],
            buyer_last_name=form.cleaned_data["last_name"],
            buyer_email=form.cleaned_data["email"],
            buyer_phone=form.cleaned_data.get("phone", ""),
            total_amount=voucher.price,
        )

        notify_url = request.build_absolute_uri(reverse("vouchers:notify"))
        continue_url = request.build_absolute_uri(
            reverse("vouchers:success") + f"?order_id={order.pk}"
        )
        cancel_url = request.build_absolute_uri(
            reverse("vouchers:cancel") + f"?order_id={order.pk}"
        )

        customer_ip = (
            request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
            or request.META.get("REMOTE_ADDR", "127.0.0.1")
        )

        try:
            result = services.create_order(
                order_pk=order.pk,
                customer_ip=customer_ip,
                voucher_name=voucher.name,
                unit_price_pln=str(voucher.price),
                buyer_first_name=order.buyer_first_name,
                buyer_last_name=order.buyer_last_name,
                buyer_email=order.buyer_email,
                buyer_phone=order.buyer_phone,
                notify_url=notify_url,
                continue_url=continue_url,
                cancel_url=cancel_url,
            )
        except Exception:
            logger.exception("PayU create_order failed for VoucherOrder #%s", order.pk)
            order.status = VoucherOrder.STATUS_CANCELED
            order.save(update_fields=["status"])
            return render(
                request,
                "vouchers/checkout.html",
                {
                    "voucher": voucher,
                    "form": form,
                    "payu_error": True,
                },
            )

        order.payu_order_id = result.order_id
        order.save(update_fields=["payu_order_id"])

        return redirect(result.redirect_url)

    return render(request, "vouchers/checkout.html", {"voucher": voucher, "form": form})


@csrf_exempt
@require_POST
def notify_view(request: HttpRequest) -> HttpResponse:
    """PayU IPN endpoint — CSRF-exempt, verified via OpenPayU-Signature."""
    raw_body = request.body
    signature_header = request.META.get("HTTP_OPENPAYU_SIGNATURE")

    if not services.verify_ipn_signature(raw_body, signature_header):
        return HttpResponse(status=403)

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError:
        logger.warning("PayU IPN: invalid JSON body")
        return HttpResponse(status=400)

    order_data = data.get("order", {})
    payu_order_id: str = order_data.get("orderId", "")
    new_status: str = order_data.get("status", "")

    if not payu_order_id or not new_status:
        return HttpResponse(status=400)

    # Map PayU status → our status; ignore unknown statuses gracefully
    status_map = {
        "PENDING": VoucherOrder.STATUS_PENDING,
        "WAITING_FOR_CONFIRMATION": VoucherOrder.STATUS_WAITING,
        "COMPLETED": VoucherOrder.STATUS_COMPLETED,
        "CANCELED": VoucherOrder.STATUS_CANCELED,
    }
    mapped = status_map.get(new_status)
    if mapped is None:
        logger.info("PayU IPN: unrecognised status %r, ignoring", new_status)
        return HttpResponse(status=200)

    updated = VoucherOrder.objects.filter(payu_order_id=payu_order_id).update(status=mapped)
    if not updated:
        logger.warning("PayU IPN: no VoucherOrder found for orderId=%s", payu_order_id)

    return HttpResponse(status=200)


def success_view(request: HttpRequest) -> HttpResponse:
    order_id = request.GET.get("order_id")
    order = None
    if order_id and order_id.isdigit():
        order = VoucherOrder.objects.filter(pk=order_id).select_related("voucher").first()
    return render(request, "vouchers/success.html", {"order": order})


def cancel_view(request: HttpRequest) -> HttpResponse:
    order_id = request.GET.get("order_id")
    order = None
    if order_id and order_id.isdigit():
        order = VoucherOrder.objects.filter(pk=order_id).select_related("voucher").first()
    return render(request, "vouchers/cancel.html", {"order": order})

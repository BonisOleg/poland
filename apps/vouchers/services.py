"""PayU REST API 2.1 client for voucher payments."""

from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Simple in-process token cache: (access_token, expires_at)
_token_cache: tuple[str, float] | None = None


def _fetch_token() -> str:
    """Obtain OAuth2 bearer token from PayU; cache until near expiry."""
    global _token_cache
    if _token_cache and time.time() < _token_cache[1] - 30:
        return _token_cache[0]

    resp = requests.post(
        f"{settings.PAYU_BASE_URL}/pl/standard/user/oauth/authorize",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.PAYU_POS_ID,
            "client_secret": settings.PAYU_MD5_KEY2,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token: str = data["access_token"]
    expires_in: int = int(data.get("expires_in", 3600))
    _token_cache = (token, time.time() + expires_in)
    return token


@dataclass
class PayUOrderResult:
    order_id: str
    redirect_url: str


def create_order(
    *,
    order_pk: int,
    customer_ip: str,
    voucher_name: str,
    unit_price_pln: str,   # Decimal as string, e.g. "150.00"
    buyer_first_name: str,
    buyer_last_name: str,
    buyer_email: str,
    buyer_phone: str,
    notify_url: str,
    continue_url: str,
    cancel_url: str,
) -> PayUOrderResult:
    """Create a PayU order and return (orderId, redirectUri)."""
    token = _fetch_token()

    # PayU expects amounts in grosze (1/100 PLN) as integer string
    total_grosze = str(int(round(float(unit_price_pln) * 100)))

    payload: dict[str, Any] = {
        "merchantPosId": settings.PAYU_POS_ID,
        "description": f"Voucher: {voucher_name}",
        "currencyCode": "PLN",
        "totalAmount": total_grosze,
        "extOrderId": str(order_pk),
        "notifyUrl": notify_url,
        "continueUrl": continue_url,
        "cancelUrl": cancel_url,
        "customerIp": customer_ip,
        "products": [
            {
                "name": voucher_name,
                "unitPrice": total_grosze,
                "quantity": "1",
            }
        ],
        "buyer": {
            "email": buyer_email,
            "firstName": buyer_first_name,
            "lastName": buyer_last_name,
            "phone": buyer_phone or "",
            "language": "pl",
        },
    }

    resp = requests.post(
        f"{settings.PAYU_BASE_URL}/api/v2_1/orders",
        json=payload,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        allow_redirects=False,
        timeout=15,
    )

    # PayU returns 302 on success; requests won't follow it with allow_redirects=False
    if resp.status_code not in (200, 201, 302):
        logger.error("PayU create_order failed: %s %s", resp.status_code, resp.text)
        resp.raise_for_status()

    data = resp.json()
    order_id: str = data["orderId"]
    redirect_url: str = data["redirectUri"]
    return PayUOrderResult(order_id=order_id, redirect_url=redirect_url)


def verify_ipn_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """
    Validate PayU IPN request using OpenPayU-Signature header.

    Header format: sender=checkout;signature=XXXX;algorithm=MD5;content=DOCUMENT
    Expected: md5(raw_body + MD5_KEY)
    """
    if not signature_header:
        logger.warning("PayU IPN: missing OpenPayU-Signature header")
        return False

    params: dict[str, str] = {}
    for part in signature_header.split(";"):
        if "=" in part:
            k, _, v = part.partition("=")
            params[k.strip()] = v.strip()

    incoming = params.get("signature", "")
    algorithm = params.get("algorithm", "MD5").upper()

    if algorithm != "MD5":
        logger.warning("PayU IPN: unsupported algorithm %s", algorithm)
        return False

    expected = hashlib.md5(raw_body + settings.PAYU_MD5_KEY.encode()).hexdigest()
    match = hmac_compare(incoming, expected)
    if not match:
        logger.warning("PayU IPN: signature mismatch")
    return match


def hmac_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    import hmac as _hmac
    return _hmac.compare_digest(a.lower(), b.lower())

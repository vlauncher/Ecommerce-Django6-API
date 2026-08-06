import hashlib
import hmac
import uuid

import requests
from django.conf import settings
from ninja.errors import HttpError


BASE_URL = "https://api.paystack.co"


def _request(method, path, payload=None):
    if not settings.PAYSTACK_SECRET_KEY:
        raise HttpError(503, "Paystack is not configured.")
    response = requests.request(method, BASE_URL + path, json=payload, headers={"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}", "Content-Type": "application/json"}, timeout=15)
    data = response.json()
    if response.status_code >= 400 or not data.get("status"):
        raise HttpError(502, data.get("message", "Paystack request failed."))
    return data["data"]


def initialize(email, amount_minor, reference, metadata=None):
    return _request("POST", "/transaction/initialize", {"email": email, "amount": amount_minor, "reference": reference, "currency": "NGN", "metadata": metadata or {}})


def verify(reference):
    return _request("GET", f"/transaction/verify/{reference}")


def refund(transaction, amount_minor=None):
    payload = {"transaction": transaction}
    if amount_minor is not None:
        payload["amount"] = amount_minor
    return _request("POST", "/refund", payload)


def create_recipient(name, account_number, bank_code):
    return _request("POST", "/transferrecipient", {"type": "nuban", "name": name, "account_number": account_number, "bank_code": bank_code, "currency": "NGN"})


def transfer(recipient, amount_minor, reason):
    return _request("POST", "/transfer", {"source": "balance", "amount": amount_minor, "recipient": recipient, "reference": f"wd_{uuid.uuid4().hex}", "reason": reason, "currency": "NGN"})


def verify_signature(body: bytes, signature: str) -> bool:
    digest = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()
    return bool(signature) and hmac.compare_digest(digest, signature)

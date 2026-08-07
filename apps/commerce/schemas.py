from typing import Optional

from pydantic import BaseModel, Field
from pydantic import EmailStr


class CartItemIn(BaseModel):
    variant_id: int
    quantity: int = Field(ge=1, le=1000)


class CartItemOut(BaseModel):
    variant_id: int
    product_name: str
    shop_slug: str
    quantity: int
    unit_price_minor: int
    total_minor: int


class CartOut(BaseModel):
    id: int
    currency: str
    subtotal_minor: int
    items: list[CartItemOut]
    discount_minor: int = 0
    coupon_code: str = ""


class CouponApplyIn(BaseModel):
    code: str


class CheckoutIn(BaseModel):
    shipping_address: dict
    billing_address: Optional[dict] = None
    address_id: int | None = None
    shipping_rate_ids: dict[str, int] = {}
    gift_card_code: str = ""
    coupon_code: str = ""
    tip_minor: int = Field(default=0, ge=0)
    customer_email: EmailStr | None = None


class AddressIn(BaseModel):
    label: str = "default"
    recipient_name: str
    phone: str = ""
    line1: str
    line2: str = ""
    city: str
    state: str
    country: str = "NG"
    postal_code: str = ""


class WishlistItemIn(BaseModel):
    variant_id: int


class ReturnRequestIn(BaseModel):
    seller_order_id: int
    reason: str = Field(min_length=1, max_length=120)
    description: str = ""


class CheckoutOut(BaseModel):
    order_id: int
    order_number: str
    total_minor: int
    currency: str

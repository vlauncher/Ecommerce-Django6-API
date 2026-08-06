from typing import Optional

from pydantic import BaseModel, Field


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
    coupon_code: str = ""
    tip_minor: int = Field(default=0, ge=0)


class CheckoutOut(BaseModel):
    order_id: int
    order_number: str
    total_minor: int
    currency: str

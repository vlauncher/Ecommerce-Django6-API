from typing import Optional

from pydantic import BaseModel, Field


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=160)
    parent_id: Optional[int] = None
    description: str = ""


class VariantIn(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    name: str = ""
    option_values: dict = {}
    price_minor: int = Field(ge=0)
    compare_at_price_minor: Optional[int] = Field(default=None, ge=0)
    currency: str = "NGN"
    weight_grams: int = Field(default=0, ge=0)


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=250)
    slug: str = Field(min_length=1, max_length=270)
    description: str = ""
    category_id: Optional[int] = None
    product_type: str = "physical"
    is_digital: bool = False
    requires_shipping: bool = True
    variants: list[VariantIn]


class VariantOut(VariantIn):
    id: int


class ProductOut(BaseModel):
    id: int
    name: str
    slug: str
    description: str
    status: str
    category_id: Optional[int]
    variants: list[VariantOut]


class ProductDetailOut(ProductOut):
    shop_slug: str
    brand: str
    is_digital: bool
    requires_shipping: bool


class ProductSearchOut(ProductDetailOut):
    min_price_minor: int | None = None


class StockAdjustIn(BaseModel):
    variant_id: int
    warehouse_id: int
    quantity_delta: int
    reason: str = "manual"


class PromotionIn(BaseModel):
    name: str
    kind: str
    value: int = Field(ge=0)
    minimum_subtotal_minor: int = Field(default=0, ge=0)
    starts_at: str
    ends_at: str | None = None
    is_automatic: bool = False


class CouponIn(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    kind: str = "percentage"
    value: int = Field(gt=0)
    minimum_subtotal_minor: int = Field(default=0, ge=0)
    usage_limit: int | None = Field(default=None, gt=0)
    per_customer_limit: int | None = Field(default=1, gt=0)
    starts_at: str
    ends_at: str | None = None

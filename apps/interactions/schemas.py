from pydantic import BaseModel, Field


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class OfferIn(BaseModel):
    product_id: int
    variant_id: int
    amount_minor: int = Field(gt=0)
    quantity: int = Field(gt=0, le=1000)


class ReviewIn(BaseModel):
    product_id: int
    order_id: int
    rating: int = Field(ge=1, le=5)
    title: str = ""
    body: str = ""


class DisputeIn(BaseModel):
    order_id: int
    seller_order_id: int | None = None
    reason: str
    description: str

from pydantic import BaseModel, Field


class PaymentInitializeIn(BaseModel):
    order_id: int


class PaymentInitializeOut(BaseModel):
    authorization_url: str
    access_code: str
    reference: str


class RefundIn(BaseModel):
    order_id: int
    amount_minor: int | None = Field(default=None, gt=0)
    reason: str = "Customer refund request"


class WithdrawalIn(BaseModel):
    amount_minor: int = Field(gt=0)
    reason: str = "Seller withdrawal"


class PayoutRecipientIn(BaseModel):
    bank_code: str
    account_number: str
    account_name: str = ""

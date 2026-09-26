from pydantic import (
    BaseModel,
    Field
)


class SearchRequest(BaseModel):

    phone: str = Field(
        min_length=10,
        max_length=10
    )


class LoginRequest(BaseModel):

    username: str

    password: str


class SearchItem(BaseModel):

    name: str

    quantity: int


class SearchOrder(BaseModel):

    tracking_number: str | None

    shipping_fee: int | None

    items: list[SearchItem]


class SearchResponse(BaseModel):

    customer: dict

    orders: list[SearchOrder]
    
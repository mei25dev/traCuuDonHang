from fastapi import (
    APIRouter,
    HTTPException
)

from ..database import get_db

from ..models.schemas import (
    SearchRequest
)

from ..services.phone_s import (
    validate_lookup_phone
)


router = APIRouter()


@router.post("/search")
def search(
    payload: SearchRequest
):

    try:

        phone = validate_lookup_phone(
            payload.phone
        )

    except ValueError as error:

        raise HTTPException(
            status_code=422,
            detail=str(error)
        )


    with get_db() as db:

        customer = db.execute(
            """
            SELECT
                id,
                phone,
                name,
                address
            FROM customers
            WHERE phone = ?
            """,
            (phone,)
        ).fetchone()


        if not customer:

            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy thông tin đơn hàng."
            )


        orders = db.execute(
            """
            SELECT
                id,
                tracking_number,
                shipping_fee
            FROM orders
            WHERE customer_id = ?
            ORDER BY id
            """,
            (
                customer["id"],
            )
        ).fetchall()


        result_orders = []


        for order in orders:

            items = db.execute(
                """
                SELECT
                    product_name,
                    quantity
                FROM order_items
                WHERE order_id = ?
                ORDER BY id
                """,
                (
                    order["id"],
                )
            ).fetchall()


            result_orders.append(
                {
                    "tracking_number":
                        order[
                            "tracking_number"
                        ],

                    "shipping_fee":
                        order[
                            "shipping_fee"
                        ],

                    "items": [
                        {
                            "name":
                                item[
                                    "product_name"
                                ],

                            "quantity":
                                item[
                                    "quantity"
                                ]
                        }

                        for item in items
                    ]
                }
            )


    return {

        "customer": {

            "name":
                customer["name"],

            "phone":
                customer["phone"],

            "address":
                customer["address"]
        },

        "orders":
            result_orders
    }
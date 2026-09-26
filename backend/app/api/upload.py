import os
import shutil
import tempfile

from fastapi import (
    APIRouter,
    File,
    UploadFile,
    Header,
    HTTPException
)

from ..database import get_db

from ..services.auth_s import (
    is_valid_session
)

from ..services.excel_s import (
    process_files
)


router = APIRouter()


ALLOWED_EXTENSIONS = {
    ".xlsx",
    ".xls"
}


def require_admin(
    authorization
):

    if not authorization:

        raise HTTPException(
            status_code=401,
            detail="Chưa đăng nhập admin."
        )


    token = authorization.replace(
        "Bearer ",
        "",
        1
    )


    if not is_valid_session(
        token
    ):

        raise HTTPException(
            status_code=401,
            detail="Phiên đăng nhập không hợp lệ."
        )


@router.post(
    "/admin/import"
)
async def import_excel(

    orders_file: UploadFile = File(...),

    shipping_file: UploadFile = File(...),

    authorization: str | None = Header(
        default=None
    )
):

    require_admin(
        authorization
    )


    orders_extension = os.path.splitext(
        orders_file.filename or ""
    )[1].lower()


    shipping_extension = os.path.splitext(
        shipping_file.filename or ""
    )[1].lower()


    if (
        orders_extension
        not in ALLOWED_EXTENSIONS
        or
        shipping_extension
        not in ALLOWED_EXTENSIONS
    ):

        raise HTTPException(
            status_code=400,
            detail="Chỉ hỗ trợ file .xlsx hoặc .xls."
        )


    with tempfile.TemporaryDirectory() as temp:

        orders_path = os.path.join(
            temp,
            "orders" + orders_extension
        )

        shipping_path = os.path.join(
            temp,
            "shipping" + shipping_extension
        )


        with open(
            orders_path,
            "wb"
        ) as file:

            shutil.copyfileobj(
                orders_file.file,
                file
            )


        with open(
            shipping_path,
            "wb"
        ) as file:

            shutil.copyfileobj(
                shipping_file.file,
                file
            )


        try:

            data = process_files(
                orders_path,
                shipping_path
            )

        except Exception as error:

            raise HTTPException(
                status_code=400,
                detail=str(error)
            )


    customers = data[
        "customers"
    ]

    shipping = data[
        "shipping"
    ]


    with get_db() as db:

        # Import mới sẽ thay dữ liệu cũ.
        db.execute(
            "DELETE FROM order_items"
        )

        db.execute(
            "DELETE FROM orders"
        )

        db.execute(
            "DELETE FROM customers"
        )


        for phone, customer in customers.items():

            customer_cursor = db.execute(
                """
                INSERT INTO customers (
                    phone,
                    name,
                    address
                )
                VALUES (?, ?, ?)
                """,
                (
                    phone,
                    customer["name"],
                    customer["address"]
                )
            )


            customer_id = (
                customer_cursor.lastrowid
            )


            shipment = shipping.get(
                phone,
                {}
            )


            order_cursor = db.execute(
                """
                INSERT INTO orders (
                    customer_id,
                    tracking_number,
                    shipping_fee
                )
                VALUES (?, ?, ?)
                """,
                (
                    customer_id,

                    shipment.get(
                        "tracking"
                    ),

                    shipment.get(
                        "fee"
                    )
                )
            )


            order_id = (
                order_cursor.lastrowid
            )


            for item in customer[
                "items"
            ]:

                db.execute(
                    """
                    INSERT INTO order_items (
                        order_id,
                        product_name,
                        quantity
                    )
                    VALUES (?, ?, ?)
                    """,
                    (
                        order_id,
                        item["name"],
                        item["quantity"]
                    )
                )


        stats = data[
            "stats"
        ]


        db.execute(
            """
            INSERT INTO import_logs (
                orders_file,
                shipping_file,
                total_order_rows,
                matched_rows,
                unmatched_rows,
                invalid_phone_rows
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                orders_file.filename,
                shipping_file.filename,

                stats[
                    "total_order_rows"
                ],

                stats[
                    "matched_rows"
                ],

                stats[
                    "unmatched_rows"
                ],

                stats[
                    "invalid_phone_rows"
                ]
            )
        )


    return {

        "message":
            "Import thành công.",

        "stats":
            stats,

        "customers":
            len(customers)
    }


@router.get(
    "/admin/import-logs"
)
def import_logs(
    authorization: str | None = Header(
        default=None
    )
):

    require_admin(
        authorization
    )


    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM import_logs
            ORDER BY id DESC
            LIMIT 20
            """
        ).fetchall()


    return {
        "logs": [
            dict(row)
            for row in rows
        ]
    }
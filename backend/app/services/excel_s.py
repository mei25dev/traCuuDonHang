import re

import pandas as pd

from .phone_s import normalize_phone


ALIASES = {

    "phone": [
        "sđt",
        "sdt",
        "số điện thoại",
        "so dien thoai",
        "phone",
        "mobile",
        "điện thoại"
    ],

    "name": [
        "tên người nhận",
        "ten nguoi nhan",
        "người nhận",
        "nguoi nhan",
        "name",
        "customer name"
    ],

    "address": [
        "địa chỉ",
        "dia chi",
        "address",
        "địa chỉ nhận hàng"
    ],

    "product": [
        "tên sản phẩm",
        "ten san pham",
        "sản phẩm",
        "san pham",
        "product",
        "product name"
    ],

    "quantity": [
        "số lượng",
        "so luong",
        "sl",
        "quantity",
        "qty"
    ],

    "tracking": [
        "mã vận đơn",
        "ma van don",
        "mã đơn",
        "ma don",
        "tracking",
        "tracking number",
        "awb"
    ],

    "shipping_fee": [
        "phí ship",
        "phi ship",
        "phí vận chuyển",
        "phi van chuyen",
        "shipping fee",
        "ship fee"
    ]
}


def clean_column_name(value):

    value = str(value).strip().lower()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value


def find_column(
    dataframe,
    field,
    required=True
):

    normalized = {
        clean_column_name(column): column
        for column in dataframe.columns
    }


    for alias in ALIASES[field]:

        alias = clean_column_name(
            alias
        )


        if alias in normalized:

            return normalized[
                alias
            ]


    if required:

        raise ValueError(
            f"Không tìm thấy cột '{field}'. "
            f"Các cột hiện có: "
            f"{list(dataframe.columns)}"
        )


    return None


def read_excel(path):

    return pd.read_excel(
        path
    )


def to_int(value):

    if pd.isna(value):
        return None


    try:

        text = str(value)

        text = text.replace(
            ",",
            ""
        )

        text = text.replace(
            ".",
            ""
        )

        return int(float(text))

    except Exception:

        return None


def process_files(
    orders_path,
    shipping_path
):

    orders = read_excel(
        orders_path
    )

    shipping = read_excel(
        shipping_path
    )


    # ==========================
    # FILE 1
    # ==========================

    order_phone = find_column(
        orders,
        "phone"
    )

    name_col = find_column(
        orders,
        "name"
    )

    address_col = find_column(
        orders,
        "address"
    )

    product_col = find_column(
        orders,
        "product"
    )

    quantity_col = find_column(
        orders,
        "quantity"
    )


    # ==========================
    # FILE 2
    # ==========================

    shipping_phone = find_column(
        shipping,
        "phone"
    )

    tracking_col = find_column(
        shipping,
        "tracking",
        required=False
    )

    fee_col = find_column(
        shipping,
        "shipping_fee",
        required=False
    )


    # ==========================
    # NORMALIZE PHONE
    # ==========================

    orders["_phone"] = (
        orders[order_phone]
        .apply(normalize_phone)
    )


    shipping["_phone"] = (
        shipping[shipping_phone]
        .apply(normalize_phone)
    )


    invalid_phone_rows = int(
        orders["_phone"]
        .isna()
        .sum()
    )


    # ==========================
    # SHIPPING LOOKUP
    # ==========================

    shipping_lookup = {}


    for _, row in shipping.iterrows():

        phone = row["_phone"]


        if not phone:
            continue


        tracking = None

        if (
            tracking_col
            and not pd.isna(
                row[tracking_col]
            )
        ):

            tracking = str(
                row[tracking_col]
            ).strip()


        fee = None

        if fee_col:

            fee = to_int(
                row[fee_col]
            )


        shipping_lookup[phone] = {
            "tracking": tracking,
            "fee": fee
        }


    # ==========================
    # ORDER DATA
    # ==========================

    customers = {}


    for _, row in orders.iterrows():

        phone = row["_phone"]


        if not phone:
            continue


        if phone not in customers:

            name = ""

            if not pd.isna(
                row[name_col]
            ):
                name = str(
                    row[name_col]
                ).strip()


            address = ""

            if not pd.isna(
                row[address_col]
            ):
                address = str(
                    row[address_col]
                ).strip()


            customers[phone] = {
                "name": name,
                "address": address,
                "items": []
            }


        product = ""

        if not pd.isna(
            row[product_col]
        ):

            product = str(
                row[product_col]
            ).strip()


        quantity = (
            to_int(
                row[quantity_col]
            )
            or 1
        )


        customers[
            phone
        ]["items"].append(
            {
                "name": product,
                "quantity": quantity
            }
        )


    # ==========================
    # MATCH STATISTICS
    # ==========================

    matched = 0
    unmatched = 0


    for phone in customers:

        if phone in shipping_lookup:
            matched += 1
        else:
            unmatched += 1


    return {

        "customers": customers,

        "shipping": shipping_lookup,

        "stats": {

            "total_order_rows":
                len(orders),

            "matched_rows":
                matched,

            "unmatched_rows":
                unmatched,

            "invalid_phone_rows":
                invalid_phone_rows
        }
    }
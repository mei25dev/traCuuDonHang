import re


def normalize_phone(value):

    if value is None:
        return None


    value = str(value).strip()


    # Excel đôi khi đọc số thành 912345678.0
    if value.endswith(".0"):

        raw = value[:-2]

        if raw.isdigit():
            value = raw


    # Xóa các ký tự thường gặp.
    value = re.sub(
        r"[\s\-.()/]",
        "",
        value
    )


    # +84912345678
    # ->
    # 0912345678

    if value.startswith("+84"):

        value = "0" + value[3:]


    # 84912345678
    # ->
    # 0912345678

    elif value.startswith("84") and len(value) == 11:

        value = "0" + value[2:]


    # 912345678
    # ->
    # 0912345678

    elif len(value) == 9 and value.isdigit():

        value = "0" + value


    # Cuối cùng phải là:
    # 0 + 9 chữ số

    if re.fullmatch(
        r"0\d{9}",
        value
    ):
        return value


    return None


def validate_lookup_phone(value):

    if not re.fullmatch(
        r"0\d{9}",
        value or ""
    ):
        raise ValueError(
            "Số điện thoại phải gồm đúng 10 chữ số và bắt đầu bằng 0."
        )


    return value
from fastapi import (
    APIRouter,
    HTTPException
)

from ..database import get_db

from ..models.schemas import (
    LoginRequest
)

from ..services.auth_s import (
    verify_password,
    create_session,
    is_valid_session
)


router = APIRouter()


@router.post("/login")
def login(
    payload: LoginRequest
):

    with get_db() as db:

        user = db.execute(
            """
            SELECT
                username,
                password_hash
            FROM admin_users
            WHERE username = ?
            """,
            (
                payload.username,
            )
        ).fetchone()


    if not user:

        raise HTTPException(
            status_code=401,
            detail="Sai tài khoản hoặc mật khẩu."
        )


    if not verify_password(
        payload.password,
        user["password_hash"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Sai tài khoản hoặc mật khẩu."
        )


    token = create_session(
        user["username"]
    )


    return {
        "token": token
    }


@router.get("/verify")
def verify(token: str):

    return {
        "valid":
            is_valid_session(token)
    }
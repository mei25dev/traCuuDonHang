import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.auth import router as auth_router
from .api.search import router as search_router
from .api.upload import router as upload_router


app = FastAPI(
    title="Order Lookup API",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,

    # Khi deploy production nên đổi "*" thành domain frontend.
    allow_origins=["*"],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router,
    prefix="/api"
)

app.include_router(
    search_router,
    prefix="/api"
)

app.include_router(
    upload_router,
    prefix="/api"
)


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


frontend_dir = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "frontend"
    )
)


if os.path.isdir(frontend_dir):

    app.mount(
        "/static",
        StaticFiles(directory=frontend_dir),
        name="static"
    )

    @app.get("/")
    def index():
        return FileResponse(
            os.path.join(
                frontend_dir,
                "index.html"
            )
        )

    @app.get("/admin")
    def admin():
        return FileResponse(
            os.path.join(
                frontend_dir,
                "admin.html"
            )
        )
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import get_settings
from .routes import register_routes
from .services.operations import OperationRunner, OperationsCatalog


def create_app() -> FastAPI:
    base_dir = Path(__file__).resolve().parent
    settings = get_settings()
    catalog = OperationsCatalog()
    runner = OperationRunner(settings=settings, catalog=catalog)
    templates = Jinja2Templates(directory=str(base_dir / "templates"))

    app = FastAPI()
    app.state.settings = settings
    app.state.catalog = catalog
    app.state.runner = runner
    app.state.templates = templates
    app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")

    register_routes(app, templates, catalog, runner)
    return app


app = create_app()

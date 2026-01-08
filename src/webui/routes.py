import json
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .services.operations import OperationRunner, OperationsCatalog


def _format_payload(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True, default=str)


def register_routes(
    app: FastAPI,
    templates: Jinja2Templates,
    catalog: OperationsCatalog,
    runner: OperationRunner,
) -> None:
    router = APIRouter()

    def render_result(
        request: Request, title: str, payload: Any, ok: bool
    ) -> HTMLResponse:
        return templates.TemplateResponse(
            "partials/result.html",
            {
                "request": request,
                "title": title,
                "payload": _format_payload(payload),
                "ok": ok,
            },
        )

    @router.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        operations = catalog.list_operations()
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "graphql_url": runner.settings.graphql_url,
                "operations": operations,
            },
        )

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/run/{name}", response_class=HTMLResponse)
    async def run_operation(request: Request, name: str) -> HTMLResponse:
        try:
            form_data = await request.form()
            data = await runner.run(name, form_data)
        except Exception as exc:
            return render_result(request, name, {"error": str(exc)}, False)
        return render_result(request, name, data, True)

    app.include_router(router)

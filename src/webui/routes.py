import json
from typing import Any

from fastapi import APIRouter, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .services.graphql_service import GraphQLService


def _format_payload(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True, default=str)


def register_routes(
    app: FastAPI, templates: Jinja2Templates, service: GraphQLService
) -> None:
    router = APIRouter()

    def render_result(request: Request, title: str, payload: Any, ok: bool) -> HTMLResponse:
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
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "graphql_url": service.settings.graphql_url},
        )

    @router.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/metadata", response_class=HTMLResponse)
    async def metadata(request: Request) -> HTMLResponse:
        try:
            data = await service.get_metadata()
        except Exception as exc:
            return render_result(request, "Metadata", {"error": str(exc)}, False)
        return render_result(request, "Metadata", data, True)

    @router.post("/usage", response_class=HTMLResponse)
    async def usage(request: Request) -> HTMLResponse:
        try:
            data = await service.get_usage()
        except Exception as exc:
            return render_result(request, "Usage", {"error": str(exc)}, False)
        return render_result(request, "Usage", data, True)

    @router.post("/web3sha3", response_class=HTMLResponse)
    async def web3sha3(
        request: Request, message: str = Form(...)
    ) -> HTMLResponse:
        if not message.strip():
            return render_result(
                request, "Web3Sha3", {"error": "message is required"}, False
            )
        try:
            data = await service.web3_sha3(message=message)
        except Exception as exc:
            return render_result(request, "Web3Sha3", {"error": str(exc)}, False)
        return render_result(request, "Web3Sha3", data, True)

    @router.post("/sendraw", response_class=HTMLResponse)
    async def sendraw(
        request: Request, signed_tx: str = Form(...)
    ) -> HTMLResponse:
        if not signed_tx.strip():
            return render_result(
                request, "SendRawTransaction", {"error": "signed_tx is required"}, False
            )
        try:
            data = await service.send_raw(signed_tx=signed_tx)
        except Exception as exc:
            return render_result(
                request, "SendRawTransaction", {"error": str(exc)}, False
            )
        return render_result(request, "SendRawTransaction", data, True)

    app.include_router(router)

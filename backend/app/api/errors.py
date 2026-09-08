"""Uniform, sanitized error responses: {error, message, detail?, hint?, error_id?}."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logging_config import logger
from app.utils.ids import short_id


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        error: str,
        message: str,
        *,
        detail: object | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error = error
        self.message = message
        self.detail = detail
        self.hint = hint


def _body(
    error: str,
    message: str,
    detail: object | None = None,
    hint: str | None = None,
    error_id: str | None = None,
) -> dict:
    out: dict = {"error": error, "message": message}
    if detail is not None:
        out["detail"] = detail
    if hint is not None:
        out["hint"] = hint
    if error_id is not None:
        out["error_id"] = error_id
    return out


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.error, exc.message, exc.detail, exc.hint),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "error" in detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=_body(
                    str(detail.get("error")),
                    str(detail.get("message", "")),
                    detail.get("detail"),
                    detail.get("hint"),
                ),
            )
        return JSONResponse(status_code=exc.status_code, content=_body("http_error", str(detail)))

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_body(
                "validation_error",
                "The request was not valid.",
                detail=jsonable_encoder(exc.errors()),
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        error_id = short_id()
        logger.exception(
            "unhandled_error",
            extra={"extra_fields": {"error_id": error_id, "path": request.url.path}},
        )
        return JSONResponse(
            status_code=500,
            content=_body(
                "internal_error",
                "An unexpected error occurred. Please try again.",
                error_id=error_id,
            ),
        )

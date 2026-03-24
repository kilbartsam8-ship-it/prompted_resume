from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def success_response(message: str, status_code: int, data: dict) -> dict:
    return {
        "message": message,
        "status": True,
        "status_code": status_code,
        "data": data,
    }


def error_response(message: str, status_code: int, data: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "message": message,
            "status": False,
            "status_code": status_code,
            "data": data,
        },
    )


def _message_from_exception(exc: Exception, default: str = "Unexpected error occurred.") -> str:
    message = str(exc)
    return message if message else default


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        return error_response(str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        return error_response(str(exc), 422)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        return error_response(_message_from_exception(exc), 500)

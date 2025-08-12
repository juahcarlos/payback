import os

from app.payment import freekassa, payment, trial
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from libs.auth import get_current_username
from libs.exceptions import MyCustomException

app = FastAPI()

app.include_router(trial.router)
app.include_router(payment.router)
app.include_router(payment.router_lang)
app.include_router(freekassa.router)
app.include_router(freekassa.router_lang)

instrumentator = Instrumentator().instrument(app)


@app.on_event("startup")
async def _startup():
    instrumentator.expose(
        app,
        dependencies=[Depends(get_current_username)],
    )


origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    os.system("python3 /ws/be/misc/burning_emails.py > /dev/null &")


@app.exception_handler(MyCustomException)
async def MyCustomExceptionHandler(request: Request, exception: MyCustomException):
    """
    Derived from Python’s base `Exception` class, it provides a constructor
    for creating custom errors with specific parameters and developer-defined
    return message text, along with other details.

    Args:
        request (Request): The FastAPI HTTP request object.
        exception (MyCustomException): The exception instance that was raised..

    Returns:
        JSONResponse: A JSON response containing:
            {
                "error": str,       # Error code or identifier
                "error_msg": str,   # Human-readable error message
                "status": "error",  # Constant indicating error state
            }
    """
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "error": exception.error,
            "error_msg": exception.name,
            "status": "error",
        },
    )

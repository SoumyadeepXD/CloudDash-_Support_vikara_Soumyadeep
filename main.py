import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["ANONYMIZED_TELEMETRY"] = "false"
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

app = FastAPI(title="CloudDash Support API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.middleware("http")
async def add_trace_id_header(request: Request, call_next):
    import uuid
    trace_id = str(uuid.uuid4())
    response = await call_next(request)
    if "X-Trace-Id" not in response.headers:
        response.headers["X-Trace-Id"] = trace_id
    return response

@app.on_event("startup")
async def startup_event():
    logger.info("application_started")

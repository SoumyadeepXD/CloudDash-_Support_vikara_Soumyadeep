import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["ANONYMIZED_TELEMETRY"] = "false"

import subprocess
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
    # Auto-ingest KB on startup if chroma_db is empty
    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    try:
        if not os.path.exists(chroma_dir) or not os.listdir(chroma_dir):
            logger.info("kb_ingestion_started")
            result = subprocess.run(
                ["python", "knowledge_base/ingest.py"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("kb_ingestion_completed", output=result.stdout)
        else:
            logger.info("kb_already_ingested", chroma_dir=chroma_dir)
    except subprocess.CalledProcessError as e:
        logger.error("kb_ingestion_failed", error=e.stderr)
    except Exception as e:
        logger.error("kb_ingestion_error", error=str(e))

    logger.info("application_started")

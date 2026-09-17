from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.api.audit import router as audit_router
from app.api.approvals import router as approvals_router
from app.api.approval_action import router as approval_action_router
from app.api.refunds import router as refunds_router


app = FastAPI(
    title="AgentOps Control Tower",
    description="Governance and monitoring API for AI agents",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(audit_router)
app.include_router(approvals_router)
app.include_router(approval_action_router)
app.include_router(refunds_router)


@app.get("/")
def root():
    return {
        "message": "AgentOps Control Tower is running"
    }
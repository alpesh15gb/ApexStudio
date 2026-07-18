"""Main API v1 router — aggregates all route modules."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.auth import auth_router
from app.api.v1.users import user_router
from app.api.v1.organizations import org_router
from app.api.v1.workspaces import workspace_router
from app.api.v1.projects import project_router
from app.api.v1.workspace_runtime import ws_runtime_router
from app.api.v1.builds import build_router
from app.api.v1.deployments import deployment_router
from app.api.v1.billing import billing_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(org_router)
api_router.include_router(workspace_router)
api_router.include_router(project_router)
api_router.include_router(ws_runtime_router)
api_router.include_router(build_router)
api_router.include_router(deployment_router)
api_router.include_router(billing_router)

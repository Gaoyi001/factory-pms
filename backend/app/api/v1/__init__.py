# app/api/v1/__init__.py
# V1 API 路由汇总
from fastapi import APIRouter

router = APIRouter(prefix="/v1")

from app.api.v1 import auth, users, projects, experiments, bom, samples, documents

__all__ = ["auth", "users", "projects", "experiments", "bom", "samples", "documents"]

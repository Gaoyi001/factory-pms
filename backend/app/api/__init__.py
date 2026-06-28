# app/api/__init__.py
from fastapi import APIRouter

router = APIRouter()

from app.api.v1 import auth, users, projects, experiments, bom, samples, documents

__all__ = ["auth", "users", "projects", "experiments", "bom", "samples", "documents"]

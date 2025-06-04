"""
API v1 Router
Main router that includes all API endpoints
"""

from fastapi import APIRouter

from voicehive.api.v1.endpoints import vapi

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(vapi.router, prefix="/vapi", tags=["vapi"])

"""Centralised environment variable reads for feedback-service."""
import os

PORT: int = int(os.environ.get("PORT", 5004))
STORAGE_BACKEND: str = os.environ.get("STORAGE_BACKEND", "memory")
DATA_DIR: str = os.environ.get("DATA_DIR", "./data")
REGISTRATION_SERVICE_URL: str = os.environ.get("REGISTRATION_SERVICE_URL", "http://localhost:5003")
EVENT_SERVICE_URL: str = os.environ.get("EVENT_SERVICE_URL", "http://localhost:5002")

"""Centralised environment variable reads for notification-service."""
import os

PORT: int = int(os.environ.get("PORT", 5005))
STORAGE_BACKEND: str = os.environ.get("STORAGE_BACKEND", "memory")
DATA_DIR: str = os.environ.get("DATA_DIR", "./data")
USER_SERVICE_URL: str = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")
REGISTRATION_SERVICE_URL: str = os.environ.get("REGISTRATION_SERVICE_URL", "http://localhost:5003")

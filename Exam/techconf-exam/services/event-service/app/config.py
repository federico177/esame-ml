"""
Centralised environment variable reads for event-service.
No other module should call os.environ directly.
"""
import os

PORT: int = int(os.environ.get("PORT", 5002))
STORAGE_BACKEND: str = os.environ.get("STORAGE_BACKEND", "memory")  # memory | json | sqlite
DATA_DIR: str = os.environ.get("DATA_DIR", "./data")
USER_SERVICE_URL: str = os.environ.get("USER_SERVICE_URL", "http://localhost:5001")

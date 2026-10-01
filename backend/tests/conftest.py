from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from cds.api import create_app

FIXED_NOW = datetime(2026, 1, 15, 9, 30, tzinfo=timezone.utc)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())

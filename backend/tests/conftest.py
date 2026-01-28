import pytest
from fastapi.testclient import TestClient
from app.core.app_factory import create_app


@pytest.fixture()
def client():
    app = create_app()
    return TestClient(app)

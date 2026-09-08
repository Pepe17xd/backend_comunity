import os

os.environ["DATABASE_URL"] = "sqlite:///./test_community.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["JWT_ISSUER"] = "identity-service"

import pytest
from fastapi.testclient import TestClient

from app.database.base import Base
from app.database.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

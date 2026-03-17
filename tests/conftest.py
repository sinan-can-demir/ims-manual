# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db

# ⚠️ Use separate test DB (for now reuse local DB)
TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ims"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


# -------------------------
# DB Fixture
# -------------------------
@pytest.fixture(scope="function")
def db():
    # Reset DB before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Override FastAPI Dependency
# -------------------------
@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    return TestClient(app)
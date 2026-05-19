# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def export_paths(tmp_path):
    events_root = tmp_path / "inventory_events"
    checkpoint = tmp_path / "checkpoints.json"
    with patch("app.services.export_service.INVENTORY_EVENTS_ROOT", events_root), \
         patch("app.services.export_service.CHECKPOINT_FILE", checkpoint):
        yield events_root, checkpoint


@pytest.fixture
def warehouse_paths(tmp_path):
    warehouse_root = tmp_path / "warehouse"
    events_root = tmp_path / "inventory_events"
    with patch("app.services.warehouse_service.WAREHOUSE_ROOT", warehouse_root), \
         patch("app.services.warehouse_service.INVENTORY_EVENTS_ROOT", events_root):
        yield warehouse_root
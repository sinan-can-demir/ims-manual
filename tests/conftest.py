# tests/conftest.py

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
_API_KEY = os.getenv("API_KEY")

if TEST_DATABASE_URL:
    engine = create_engine(TEST_DATABASE_URL)
else:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "postgres: requires a real Postgres DB — set TEST_DATABASE_URL to run"
    )


def pytest_collection_modifyitems(config, items):
    if not TEST_DATABASE_URL:
        skip = pytest.mark.skip(reason="requires Postgres — set TEST_DATABASE_URL env var")
        for item in items:
            if "postgres" in item.keywords:
                item.add_marker(skip)


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
    # Pass API key header automatically if auth is enabled in the test environment
    headers = {"X-API-Key": _API_KEY} if _API_KEY else {}
    return TestClient(app, headers=headers)


@pytest.fixture
def export_paths(tmp_path):
    events_root = tmp_path / "inventory_events"
    checkpoint = tmp_path / "checkpoints.json"
    with (
        patch("app.services.export_service.INVENTORY_EVENTS_ROOT", events_root),
        patch("app.services.export_service.CHECKPOINT_FILE", checkpoint),
    ):
        yield events_root, checkpoint


@pytest.fixture
def warehouse_paths(tmp_path):
    warehouse_root = tmp_path / "warehouse"
    events_root = tmp_path / "inventory_events"
    with (
        patch("app.services.warehouse_service.WAREHOUSE_ROOT", warehouse_root),
        patch("app.services.warehouse_service.INVENTORY_EVENTS_ROOT", events_root),
    ):
        yield warehouse_root

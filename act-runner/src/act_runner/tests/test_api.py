import json
import os
import tempfile

import pytest

from act_runner.api import RunnerAPI
from act_runner.config import RunnerConfig, RepoConfig
from act_runner.db import BuildDB, Build


@pytest.fixture
def api_and_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    config = RunnerConfig(
        api_host="127.0.0.1",
        api_port=0,
        repos=[
            RepoConfig(url="https://git.example.com/repo1.git", branch="main"),
            RepoConfig(url="https://git.example.com/repo2.git", branch="develop"),
        ],
    )
    db = BuildDB(db_path)
    api = RunnerAPI(config, db)

    yield api, db

    os.unlink(db_path)


def test_health_endpoint(api_and_db):
    api, db = api_and_db
    import asyncio
    from aiohttp import web
    from aiohttp.test_utils import AioHTTPTestCase, TestClient, TestServer

    async def go():
        server = TestServer(api.app)
        async with TestClient(server) as client:
            resp = await client.get("/api/health")
            assert resp.status == 200
            data = await resp.json()
            assert data["status"] == "ok"
            assert data["repos"] == 2

    asyncio.get_event_loop().run_until_complete(go())


def test_repos_endpoint(api_and_db):
    api, db = api_and_db
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer

    async def go():
        server = TestServer(api.app)
        async with TestClient(server) as client:
            resp = await client.get("/api/repos")
            assert resp.status == 200
            data = await resp.json()
            assert len(data["repos"]) == 2
            assert data["repos"][0]["url"] == "https://git.example.com/repo1.git"
            assert data["repos"][0]["last_build"] is None

    asyncio.get_event_loop().run_until_complete(go())


def test_builds_endpoint(api_and_db):
    api, db = api_and_db
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer

    db.insert_build(
        Build(
            repo_url="https://git.example.com/repo1.git",
            repo_name="repo1",
            branch="main",
            commit_sha="abc123",
            status="success",
            started_at="2026-01-01T00:00:00Z",
            finished_at="2026-01-01T00:00:05Z",
            duration_ms=5000,
            exit_code=0,
        )
    )

    async def go():
        server = TestServer(api.app)
        async with TestClient(server) as client:
            resp = await client.get("/api/builds")
            assert resp.status == 200
            data = await resp.json()
            assert len(data["builds"]) == 1
            assert data["builds"][0]["commit_sha"] == "abc123"
            assert data["builds"][0]["status"] == "success"

    asyncio.get_event_loop().run_until_complete(go())


def test_build_detail_endpoint(api_and_db):
    api, db = api_and_db
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer

    build_id = db.insert_build(
        Build(
            repo_url="https://git.example.com/repo1.git",
            repo_name="repo1",
            branch="main",
            commit_sha="deadbeef",
            status="failure",
            started_at="2026-01-01T00:00:00Z",
            exit_code=1,
        )
    )

    async def go():
        server = TestServer(api.app)
        async with TestClient(server) as client:
            resp = await client.get(f"/api/builds/{build_id}")
            assert resp.status == 200
            data = await resp.json()
            assert data["commit_sha"] == "deadbeef"
            assert data["status"] == "failure"
            assert data["exit_code"] == 1

            resp = await client.get("/api/builds/99999")
            assert resp.status == 404

    asyncio.get_event_loop().run_until_complete(go())


def test_build_log_endpoint(api_and_db):
    api, db = api_and_db
    import asyncio
    from aiohttp.test_utils import TestClient, TestServer

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as lf:
        lf.write("line 1\nline 2\nline 3\n")
        log_path = lf.name

    build_id = db.insert_build(
        Build(
            repo_url="https://git.example.com/repo1.git",
            repo_name="repo1",
            branch="main",
            commit_sha="abc123",
            status="success",
            started_at="2026-01-01T00:00:00Z",
            log_path=log_path,
        )
    )

    async def go():
        server = TestServer(api.app)
        async with TestClient(server) as client:
            resp = await client.get(f"/api/builds/{build_id}/log")
            assert resp.status == 200
            text = await resp.text()
            assert "line 1" in text
            assert "line 3" in text

    try:
        asyncio.get_event_loop().run_until_complete(go())
    finally:
        os.unlink(log_path)

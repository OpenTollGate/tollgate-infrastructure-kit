import logging
import os
from pathlib import Path
from typing import Optional

from aiohttp import web

from act_runner.config import RunnerConfig, RepoConfig
from act_runner.db import BuildDB

logger = logging.getLogger(__name__)


class RunnerAPI:
    def __init__(self, config: RunnerConfig, db: BuildDB):
        self.config = config
        self.db = db
        self.app = web.Application()
        self._setup_routes()
        self._runner: Optional[web.AppRunner] = None

    def _setup_routes(self):
        self.app.router.add_get("/api/health", self._health)
        self.app.router.add_get("/api/repos", self._repos)
        self.app.router.add_get("/api/builds", self._builds)
        self.app.router.add_get("/api/builds/{build_id}", self._build_detail)
        self.app.router.add_get("/api/builds/{build_id}/log", self._build_log)

    async def _health(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "ok",
                "repos": len(self.config.repos),
                "poll_interval": self.config.poll_interval,
            }
        )

    async def _repos(self, request: web.Request) -> web.Response:
        repos = []
        for repo in self.config.repos:
            last_build = self.db.get_last_build_for_repo(repo.url, repo.branch)
            repos.append(
                {
                    "url": repo.url,
                    "branch": repo.branch,
                    "last_build": (
                        {
                            "id": last_build.id,
                            "commit_sha": last_build.commit_sha,
                            "status": last_build.status,
                            "finished_at": last_build.finished_at,
                            "duration_ms": last_build.duration_ms,
                        }
                        if last_build
                        else None
                    ),
                }
            )
        return web.json_response({"repos": repos})

    async def _builds(self, request: web.Request) -> web.Response:
        limit = int(request.query.get("limit", "50"))
        offset = int(request.query.get("offset", "0"))
        builds = self.db.list_builds(limit=limit, offset=offset)
        return web.json_response(
            {
                "builds": [
                    {
                        "id": b.id,
                        "repo_url": b.repo_url,
                        "repo_name": b.repo_name,
                        "branch": b.branch,
                        "commit_sha": b.commit_sha,
                        "status": b.status,
                        "started_at": b.started_at,
                        "finished_at": b.finished_at,
                        "duration_ms": b.duration_ms,
                        "exit_code": b.exit_code,
                    }
                    for b in builds
                ]
            }
        )

    async def _build_detail(self, request: web.Request) -> web.Response:
        build_id = int(request.match_info["build_id"])
        build = self.db.get_build(build_id)
        if not build:
            return web.json_response({"error": "build not found"}, status=404)
        result = {
            "id": build.id,
            "repo_url": build.repo_url,
            "repo_name": build.repo_name,
            "branch": build.branch,
            "commit_sha": build.commit_sha,
            "status": build.status,
            "started_at": build.started_at,
            "finished_at": build.finished_at,
            "duration_ms": build.duration_ms,
            "exit_code": build.exit_code,
            "error": build.error,
        }
        if build.log_path and Path(build.log_path).exists():
            result["log_available"] = True
        return web.json_response(result)

    async def _build_log(self, request: web.Request) -> web.Response:
        build_id = int(request.match_info["build_id"])
        build = self.db.get_build(build_id)
        if not build:
            return web.json_response({"error": "build not found"}, status=404)
        if not build.log_path or not Path(build.log_path).exists():
            return web.json_response({"error": "log not found"}, status=404)
        log_content = Path(build.log_path).read_text(errors="replace")
        return web.Response(
            text=log_content,
            content_type="text/plain",
        )

    async def start(self):
        self._runner = web.AppRunner(self.app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.config.api_host, self.config.api_port)
        await site.start()
        logger.info(
            f"API listening on {self.config.api_host}:{self.config.api_port}"
        )

    async def stop(self):
        if self._runner:
            await self._runner.cleanup()
            self._runner = None

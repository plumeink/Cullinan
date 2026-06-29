"""Static files and SPA example for Cullinan.

Demonstrates:

* serving classic static assets under ``/public`` with caching headers,
* serving a Single-Page Application bundle under ``/`` with client-side
  routing fallback to ``index.html`` while still returning 404 for missing
  ``*.js``/``*.css`` requests,
* coexistence with regular controllers — `GET /api/health` keeps working.

The same configuration runs under both Tornado and ASGI engines without
changes — Cullinan registers ``StaticFiles`` on its gateway router so
runtime selection stays a deployment decision, not an application concern.
"""

from pathlib import Path

from cullinan import application, configure
from cullinan.web import StaticFiles, controller, get_api


_HERE = Path(__file__).resolve().parent


@controller(url="/api/health")
class HealthController:
    @get_api(url="")
    def health(self):
        return {"status": "ok"}


@configure(
    user_packages=["examples.static_files_and_spa"],
    server_port=4082,
    static_files=[
        # Classic /public/* mount with a 1-hour cache window.
        StaticFiles(
            url="/public",
            directory=str(_HERE / "public"),
            max_age=3600,
        ),
        # SPA bundle under / with client-side routing fallback.
        # Long-cache the immutable assets folder.
        StaticFiles(
            url="/assets",
            directory=str(_HERE / "spa" / "assets"),
            max_age=31536000,
            immutable=True,
        ),
        StaticFiles.spa_app(
            directory=str(_HERE / "spa"),
            index="index.html",
        ),
    ],
)
@application
def main(): ...


__all__ = ["main"]

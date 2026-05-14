"""Public API v1 documentation endpoints."""

from copy import deepcopy
from typing import Any, Self

from litestar import Controller, Request, get
from litestar.enums import MediaType, OpenAPIMediaType
from litestar.openapi.plugins import StoplightRenderPlugin

V1_PATH_PREFIX = "/api/v1/"
V1_DOCS_PATH_PREFIX = "/api/v1/docs/"
V1_OPENAPI_JSON_PATH = "/api/v1/docs/openapi.json"


class V1StoplightRenderPlugin(StoplightRenderPlugin):
    """Render Stoplight against the dedicated v1 schema endpoint."""

    @staticmethod
    def get_openapi_json_route(request: Request) -> str:
        return V1_OPENAPI_JSON_PATH


_STOPLIGHT_PLUGIN = V1StoplightRenderPlugin(path="/")


def build_v1_openapi_schema(request: Request) -> dict[str, Any]:
    """Return a filtered OpenAPI schema containing only public v1 endpoints."""
    schema = deepcopy(request.app.openapi_schema.to_schema())
    schema["paths"] = {
        path: value
        for path, value in schema.get("paths", {}).items()
        if path.startswith(V1_PATH_PREFIX) and not path.startswith(V1_DOCS_PATH_PREFIX)
    }
    schema["info"] = {
        **schema.get("info", {}),
        "title": "AppGoblin Public API v1",
        "version": "1.0.0",
        "description": (
            "Generated OpenAPI schema for AppGoblin public v1 endpoints. "
            "Authenticate requests with an X-API-Key header."
        ),
    }
    schema["servers"] = [{"url": "/"}]
    return schema


class V1DocsController(Controller):
    """Generated documentation views for the public v1 API."""

    path = "/api/v1/docs"
    include_in_schema = False

    @get(
        path="/openapi.json",
        media_type=OpenAPIMediaType.OPENAPI_JSON,
    )
    async def openapi_json(self: Self, request: Request) -> dict[str, Any]:
        """Return the public v1 OpenAPI schema."""
        return build_v1_openapi_schema(request)

    @get(path="/openapi", media_type=MediaType.HTML)
    async def openapi(self: Self, request: Request) -> bytes:
        """Render Stoplight Elements for the public v1 OpenAPI schema."""
        return _STOPLIGHT_PLUGIN.render(request, build_v1_openapi_schema(request))

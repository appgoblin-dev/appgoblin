"""Public API v1 documentation endpoints."""

from copy import deepcopy
from typing import Any, Self

from litestar import Controller, Request, get
from litestar.enums import MediaType, OpenAPIMediaType
from litestar.openapi.plugins import ScalarRenderPlugin

V1_PATH_PREFIX = "/api/v1/"
V1_DOCS_PATH_PREFIX = "/api/v1/docs/"
V1_OPENAPI_JSON_PATH = "/api/v1/docs/openapi.json"
PUBLIC_API_SERVER_URL = "https://appgoblin.info"
SCALAR_CSS_URL = "data:text/css,"

SCALAR_OPTIONS = {
    "theme": "purple",
    "expandAllResponses": True,
    "hideClientButton": True,
    "hideModels": True,
    "hideSearch": True,
    "hideTestRequestButton": True,
    "showSidebar": True,
    "showDeveloperTools": "never",
    "showToolbar": "localhost",
    "operationTitleSource": "summary",
    "persistAuth": False,
    "telemetry": True,
    "externalUrls": {
        "dashboardUrl": "https://dashboard.scalar.com",
        "registryUrl": "https://registry.scalar.com",
        "proxyUrl": "https://proxy.scalar.com",
        "apiBaseUrl": "https://api.scalar.com",
    },
    "layout": "modern",
    "isEditable": False,
    "isLoading": False,
    "documentDownloadType": "both",
    "showOperationId": False,
    "hideDarkModeToggle": False,
    "withDefaultFonts": True,
    "defaultOpenFirstTag": True,
    "defaultOpenAllTags": False,
    "expandAllModelSections": False,
    "orderSchemaPropertiesBy": "alpha",
    "orderRequiredPropertiesFirst": True,
    "_integration": "html",
    "default": False,
    "slug": "api-1",
    "title": "API #1",
    "agent": {"disabled": True},
}


class V1ScalarRenderPlugin(ScalarRenderPlugin):
    """Render Scalar against the dedicated v1 schema endpoint."""

    @staticmethod
    def get_openapi_json_route(request: Request) -> str:
        return V1_OPENAPI_JSON_PATH


_SCALAR_PLUGIN = V1ScalarRenderPlugin(
    path="/",
    options=SCALAR_OPTIONS,
    css_url=SCALAR_CSS_URL,
)


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
        "version": "0.1.0",
        "description": (
            "Interactive reference for AppGoblin public v1 endpoints.\n\n"
            "## Authentication\n"
            "Create or manage your API Token from the AppGoblin account dashboard, "
            "then send it in the `X-API-Key` header on each request.\n\n"
            "- Header: `X-API-Key: <your-api-token>`\n"
            f"- Get a token: {PUBLIC_API_SERVER_URL}/account/api-keys\n"
            "- App endpoints accept valid public API tokens\n"
            "- Company endpoints require a paid subscription tier"
        ),
    }
    components = schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})
    security_schemes["ApiKeyAuth"] = {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": (
            "Generate an API Token from the AppGoblin dashboard and send it as the "
            "X-API-Key header."
        ),
    }
    schema["security"] = [{"ApiKeyAuth": []}]
    schema["servers"] = [{"url": PUBLIC_API_SERVER_URL}]
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
        """Render Scalar for the public v1 OpenAPI schema."""
        return _SCALAR_PLUGIN.render(request, build_v1_openapi_schema(request))

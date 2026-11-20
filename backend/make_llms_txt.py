"""Generate the concise llms.txt catalog for machine-readable AppGoblin pages."""

from pathlib import Path


LLMS_PATH = (
    Path(__file__).resolve().parent.parent / "frontend" / "static" / "llms.txt"
)

LLMS_CONTENT = """# AppGoblin

> AppGoblin is a mobile app intelligence tool covering Google Play and Apple App Store data, including 6M+ apps, SDK usage, app-store rankings, company relationships, and ad-tech supply-chain data.

- Homepage: https://appgoblin.info
- OpenAPI: https://appgoblin.info/openapi.json
- API reference: https://appgoblin.info/api-docs
- Public API docs: https://appgoblin.info/api/v1/docs/openapi.json
- Sitemap: https://appgoblin.info/sitemap.xml

## Machine-readable app and SDK pages

Non-browser HTTP clients should send `Accept: application/json`. Authenticated browser users can open these routes directly. Anonymous machine clients receive a 402 challenge (x402 or MPP) for the routes below; account sign-in is not required after payment.

- https://appgoblin.info/search/{term} - Search apps and companies.
- https://appgoblin.info/apps/{storeId}/keywords - App details with ranked and description-derived keyword scores.
- https://appgoblin.info/apps/{storeId}/keywords/discovery - Description-derived keywords not currently marked as ranked.
- https://appgoblin.info/apps/{storeId}/keywords/ranking - Currently ranked keywords and scores.
- https://appgoblin.info/apps/{storeId}/keywords/compare - HTML keyword ranking history comparison.
- https://appgoblin.info/apps/{storeId}/sdks - Detected SDKs, categories, permissions, app queries, and SKAdNetwork identifiers.
- https://appgoblin.info/apps/{storeId}/sdks/permissions - Detected app permissions.
- https://appgoblin.info/apps/{storeId}/sdks/queries - Package or URL schemes queried for availability.
- https://appgoblin.info/apps/{storeId}/sdks/skadnetwork - Detected iOS SKAdNetwork identifiers.
- https://appgoblin.info/apps/{storeId}/sdks/unknowns - Unmapped package and path patterns.
- https://appgoblin.info/apps/comparison/{storeId} - App metrics, ratings, and SDK overview.
- https://appgoblin.info/apps/comparison/{storeId1}/{storeId2} - Side-by-side app comparison.
- https://appgoblin.info/sdks/{pattern} - Apps and companies associated with an SDK package or path pattern.
- https://appgoblin.info/sdks/mapped/{sdkSlug} - SDK owner, mappings, and associated apps.
- https://appgoblin.info/developers/{developer}/sdks - SDKs detected across a developer's app portfolio.
- https://appgoblin.info/reports/app-ecosystem-report-Q2-2026/download - CSV for SDK and app-ads.txt adoption trends.

Example: `curl -H 'Accept: application/json' 'https://appgoblin.info/apps/com.example.app/keywords'`

## Browseable sections

- https://appgoblin.info/apps/{storeId} - App details and market data.
- https://appgoblin.info/companies - Company and app ecosystem directory.
- https://appgoblin.info/companies/{domain} - Company overview and app relationships.
- https://appgoblin.info/sdks - SDK and technology directory.
- https://appgoblin.info/ad-creatives - Advertiser creative intelligence.
- https://appgoblin.info/top-mobile-advertisers - Mobile advertiser rankings.
- https://appgoblin.info/reports - Market and ecosystem reports.
- https://appgoblin.info/blog - AppGoblin analysis and research updates.
"""


def create_llms_txt(output_path: Path = LLMS_PATH) -> Path:
    """Write the machine-readable llms.txt catalog."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(LLMS_CONTENT, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    print(create_llms_txt())

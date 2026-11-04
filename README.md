# AppGoblin Mobile App & Ads Analysis

[AppGoblin is a mobile app and ad intelligence platform offering free app intelligence, ASO tools, and paid reports on ad industry and SDK usage. It focuses on technical app analysis — SDKs, API calls, and data security.](https://appgoblin.info). This repo is the frontend and backend of [AppGoblin](https://appgoblin.info) website itself. The data is crawled by [appgoblin-dev/adscrawler](https://github.com/appgoblin-dev/adscrawler).

[<img src="/frontend/static/appgoblin_screenshot.png" width="500"/>](/frontend/static/appgoblin_screenshot.png)

## Features

- **[App Intelligence](https://appgoblin.info/)** — Data on 6M+ iOS and Android apps (updated daily), including:
  - **Keywords** — Track your own or competitors' keywords and the top apps associated with them
  - **Trends** — Track installs and ratings over time
  - **Rankings** — Daily tracking of top apps from Google Play and Apple App Store
  - **New Apps Discovery** — Surfaces newly released apps often buried by official store algorithms
  - **Growth Metrics** — Daily install estimates, app ratings, ad revenue and IAP revenue estimates

- **[SDK Analysis](https://appgoblin.info/sdks)** — Detailed breakdown of SDKs found in decompiled 200k+ Android and iOS apps, including advertising, analytics, and open-source libraries

- **[Companies Directory](https://appgoblin.info/companies)** — Rankings of mobile app companies based on SDK integration frequency, filterable by category
  - Example: [Most popular Ad Networks for Casino Games](https://appgoblin.info/companies/types/ad-networks/game_casino)
  - Example: [Most popular Product Analytics for Business Apps](https://appgoblin.info/companies/types/product-analytics/business)

- **Company Intelligence** — See the top client apps for any mobile SDK or services company
  - Example: [Salesforce Clients](https://appgoblin.info/companies/salesforce.com)
  - Example: [AppsFlyer Top Apps](https://appgoblin.info/companies/appsflyer.com)
  - Track quarterly app adoption and churn for companies. See which apps they recently added or lost based on SDK or App-Ads.txt datasets

- **Ad Tech Insights** — Track ad campaingns, ad creatives and explore the top advertising apps

- **ASO Tools** — Free keyword research tools and data dumps to optimize app store visibility

- **[Free App Datasets](https://appgoblin.info/free-app-datasets)** — Free app metrics and app description exports for researchers, marketers, and data scientists (TSV + XZ)

- **App-Ads.txt** — Daily-updated files tying apps to their DIRECT and RESELLER ad networks and SSPs

## Who It's For

- **App & game developers** looking to grow using free ASO tools
- **Researchers & journalists** needing deep technical analysis across millions of apps
- **Data scientists & marketers** needing reproducible app datasets for modeling, market mapping, and analysis
- **Ad sales teams** prospecting clients by analyzing competitor app portfolios and recent company churn
- **Ad networks & DSPs** doing fraud detection and competitor analysis
- **DSPs** needing App-Ads.txt tied to real app store IDs (e.g. `com.example.app`) rather than just domain names
- **Competitor researchers** tracking SDK adoption, quarterly app churn, and growth trends
- **Privacy advocates** identifying hidden trackers and ad-tech domains in popular apps

### Project Structure

1.  Python Litestar backend API found in `backend/`
2.  Javascript SvelteKit+Tailwind UI found in `frontend/`

## Public API & MCP (AI Agents)

AppGoblin exposes a public REST API and an MCP (Model Context Protocol) server for AI agents.

### REST API — `/api/v1/`

- Interactive docs at **[appgoblin.info/api-docs](https://appgoblin.info/api-docs)**
- Requires an API key (`Authorization: Bearer` header, legacy `X-API-Key` also accepted) — generate one from your [account dashboard](https://appgoblin.info/account/api-keys)
- Rate-limited per key (tier-based)
- Endpoints cover apps, companies, keywords, SDKs, and rankings

### MCP Server — `/api/v1/mcp`

- **Endpoint**: `https://appgoblin.info/api/v1/mcp`
- **Protocol**: [Streamable HTTP](https://modelcontextprotocol.io/docs/concepts/architecture#transport-layer) (SSE + JSON-RPC)
- **Auth**: `Authorization: Bearer` header (same key as the REST API; legacy `X-API-Key` also accepted)
- AI agents (Claude Code, Cursor, etc.) dynamically discover available tools via `tools/list` after connecting — no static configuration needed

### MCP Discovery

AI agents and crawlers can discover the server at these well-known paths:

| Path                                | Purpose                     |
| ----------------------------------- | --------------------------- |
| `/.well-known/mcp.json`             | MCP manifest (short alias)  |
| `/.well-known/mcp/server-card.json` | Full server card (SEP-1649) |

Headers advertised in `robots.txt`:

```
Mcp-Server-Card: https://appgoblin.info/.well-known/mcp/server-card.json
Mcp-Manifest: https://appgoblin.info/.well-known/mcp.json
```

### Machine payments (MPP and x402)

Selected public pages and searches accept micro payments through both MPP and x402. MPP supports


### Setup

NOTE: This repo is not direclty meant to be rerun without the DB, and is here for transparency in AppGoblin's analytics. That being said, contributions are welcome, if you're interested in contributing please reach out.

- Current setup is based on Python3.14
- pip install dependencies, found in pyproject.toml: `pip install`

### Running

- To run locally for testing use
  - Backend: in `backend/` run `litestar run dev`
  - Frontend: in `frontend` run `npm run dev`
- This repo includes the scripts used to run in production as well. These are located in the steps in `.github/actions` as well as `scripts` for systemd services for frontend and backend.
- Additionally, you will need a proxy. I used Nginx. This is wherever you have your nginx configuration set, possibly sites-available `/etc/nginx/sites-available/appgoblin-api` or `/etc/nginx/conf.d/appgoblin-api.conf`

## AppGoblin Community

**Have questions or suggestions? Let's connect!**

email: contact@appgoblin.info

🧙‍♂️ [Join Discord Server](https://discord.gg/7jpWEhkXRW)

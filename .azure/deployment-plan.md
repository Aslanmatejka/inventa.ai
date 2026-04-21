# Inventa.ai Azure Deployment Plan

**Status:** Ready for Validation
**Created:** 2026-04-21
**Mode:** NEW (first Azure deployment of this app)

## Architecture

```
┌─────────────────────────┐        ┌──────────────────────────┐
│  Azure Static Web App   │ HTTPS  │   Azure Container Apps   │
│  (React frontend)       ├───────▶│   (FastAPI + CadQuery)   │
│  client/build           │  CORS  │   Port 3001              │
└─────────────────────────┘        └──────────┬───────────────┘
                                              │ managed identity
                               ┌──────────────┴──────────────┐
                               ▼                             ▼
                       ┌───────────────┐           ┌──────────────────┐
                       │   Key Vault   │           │  Azure Container │
                       │  - ANTHROPIC  │           │   Registry       │
                       │  - SUPABASE_* │           │  (private image) │
                       └───────────────┘           └──────────────────┘
                       ┌───────────────────────────────────────────┐
                       │  External (unchanged): Supabase, Anthropic │
                       └───────────────────────────────────────────┘
```

## Decisions

| Item | Choice | Rationale |
|------|--------|-----------|
| Region | `eastus` | User selected; Opus 4.7 available |
| Backend hosting | Container Apps | CadQuery requires native OpenCASCADE libs — can't use App Service Python runtime |
| Frontend hosting | Static Web App (Free) | CRA static bundle, free tier, built-in CDN |
| IaC | Bicep + azd | User selected |
| Secret storage | Key Vault + user-assigned managed identity | User selected |
| Container registry | Azure Container Registry (Basic) | Private image for backend |
| Observability | Log Analytics + Container Apps built-in logs | Included with CA env |
| Scale-to-zero | Yes, min 0 / max 3 replicas | Saves cost on idle |

## Components

- **Backend** (`Backend/`): FastAPI + uvicorn, Python 3.12, CadQuery 2.4, Anthropic SDK. Docker image from `python:3.12-slim` + `apt install libgl1 libglu1-mesa libxrender1 libxi6` for OCC.
- **Frontend** (`client/`): CRA React build → `client/build/` served by Static Web App.

## Environment variables (Container App)

Mounted from Key Vault secrets via managed identity:
- `ANTHROPIC_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`

Direct env:
- `AI_MODEL_NAME=claude-opus-4-7`
- `PORT=3001`
- `HOST=0.0.0.0`
- `CORS_ORIGINS=<static-web-app-url>`
- `REQUIRE_AUTH=true`

## Generated artifacts

- `infra/main.bicep` — subscription-scope template
- `infra/modules/*.bicep` — Container App, SWA, KV, ACR, Log Analytics
- `Backend/Dockerfile`
- `Backend/.dockerignore`
- `azure.yaml` — azd config
- `client/.env.production` — points frontend at deployed backend URL at build time

## Deployment steps (user runs)

```powershell
azd auth login
azd up          # first time — creates all resources and deploys code
# later:
azd deploy      # redeploy code only
```

## Known limitations

- `exports/` directory is ephemeral in the container — for production, add Azure Blob Storage for generated STL/STEP files (not in this initial deployment)
- Supabase stays external (free tier) — no migration to Azure Postgres needed

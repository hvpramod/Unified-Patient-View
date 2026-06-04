# Unified Patient View (UPV)

AI-powered clinical data aggregation and reconciliation platform for APCs.

## Quick Start

```bash
docker-compose up -d
```

## Services

| Service | Port | Description |
|---|---|---|
| frontend | 3000 | Next.js React app |
| gateway-api | 8000 | FastAPI BFF |
| ingestion-service | 8001 | FHIR poller |
| patient-data-service | 8002 | FHIR canonical store |
| conflict-detection | 8003 | Conflict engine |
| ai-agent-service | 8004 | LangGraph agents |
| audit-service | 8005 | Audit log |
| notification-service | 8006 | Teams integration |

## Docs

- [Architecture](docs/adr/001-system-architecture.md)
- [Deployment](docs/runbooks/deployment.md)
- [API Reference](docs/runbooks/api-reference.md)

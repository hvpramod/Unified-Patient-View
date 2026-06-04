# Deployment Runbook

## Prerequisites

- Azure subscription with AKS cluster
- Azure Container Registry (ACR)
- ArgoCD installed in AKS
- kubectl configured for the cluster
- Existing Kafka cluster and PostgreSQL instance

## Local Development (Docker Compose)

```bash
# 1. Copy environment config
cp .env.example .env.local
# Edit .env.local with your API keys

# 2. Start all services
docker-compose up -d

# 3. Run database migrations
docker-compose run --rm migrations alembic upgrade head

# 4. Open the app
open http://localhost:3000
```

## Staging / Production Deployment

### 1. Configure Secrets in AKS

```bash
# Database secret
kubectl create secret generic upv-db-secret \
  --from-literal=url="postgresql+asyncpg://upv:PASSWORD@your-postgres:5432/upv" \
  -n upv-api

# Redis secret
kubectl create secret generic upv-redis-secret \
  --from-literal=url="redis://your-redis:6379" \
  -n upv-api

# Azure AD secret
kubectl create secret generic upv-azure-secret \
  --from-literal=tenant_id="YOUR_TENANT_ID" \
  --from-literal=client_id="YOUR_CLIENT_ID" \
  -n upv-api

# LLM API keys
kubectl create secret generic upv-llm-secrets \
  --from-literal=openai_api_key="sk-..." \
  --from-literal=anthropic_api_key="sk-ant-..." \
  -n upv-ai
```

### 2. Create Namespaces

```bash
kubectl apply -f infra/k8s/namespaces/namespaces.yaml
```

### 3. Run Migrations

```bash
kubectl run migration \
  --image=your-acr.azurecr.io/upv/migrations:latest \
  --env="DATABASE_URL=postgresql://upv:PASSWORD@postgres:5432/upv" \
  --restart=Never \
  -n upv-api
```

### 4. Apply ArgoCD Applications

```bash
kubectl apply -f infra/argocd/applications.yaml
```

ArgoCD will sync all services automatically.

### 5. Verify Deployment

```bash
kubectl get pods -n upv-api
kubectl get pods -n upv-ai
kubectl get pods -n upv-frontend

# Check logs
kubectl logs -n upv-api deployment/gateway-api -f

# Health checks
curl https://upv.yourdomain.com/health
```

## iFrame Integration

To embed UPV inside an EMR (e.g., Athena):

```html
<iframe
  src="https://upv.yourdomain.com/embed?patient_id=PATIENT_UUID&appt_id=APPT_ID"
  width="420"
  height="100%"
  frameborder="0"
  title="Unified Patient View"
/>
```

The `patient_id` must be the UPV internal UUID. Map from Athena patient ID using the `external_ids` field.

## Rollback

```bash
# ArgoCD rollback to previous revision
argocd app rollback upv-gateway-api

# Or via kubectl
kubectl rollout undo deployment/gateway-api -n upv-api
```

# ADR 001: System Architecture

## Status: Accepted

## Context

Multiple source systems (Athena, HealthGorilla, Pathway) produce conflicting clinical data. APCs need a single AI-generated view with conflict detection, reconciliation, and explainability.

## Decision

Event-driven microservices architecture:
- **ingestion-service** polls source systems and publishes Kafka events
- **conflict-detection** consumes events, runs rule engine (R-001–R-006)
- **ai-agent-service** consumes events, runs LangGraph agents, writes to Redis cache
- **gateway-api** serves pre-generated summaries with <3s latency guarantee
- **frontend** is Next.js embeddable as iFrame

## Consequences

- ✅ Decoupled — agents run asynchronously, not blocking UI
- ✅ <3s latency via Redis pre-generated cache
- ✅ iFrame-embeddable standalone product
- ⚠️ Operational complexity of 8 services (mitigated by ArgoCD)
- ⚠️ Cache staleness window (mitigated by Kafka-triggered refresh)

## Alternatives Considered

- **Monolith**: Simpler ops, but AI latency would block clinician UI
- **Serverless**: Good scale, but cold-start latency unacceptable for clinical use

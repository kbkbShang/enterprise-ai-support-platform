# Enterprise AI Support Platform

> A production-style AI support platform built with FastAPI, Google Cloud Run, Pub/Sub, Firestore, ChromaDB, and Gemini 2.5 Flash.

[![Python](https://img.shields.io/badge/Python-3.11-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-REST-green)]()
[![Cloud Run](https://img.shields.io/badge/Google-Cloud%20Run-blue)]()
[![Pub/Sub](https://img.shields.io/badge/Google-Pub/Sub-orange)]()
[![Firestore](https://img.shields.io/badge/Firestore-NoSQL-yellow)]()
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorDB-purple)]()
[![Docker](https://img.shields.io/badge/Docker-Container-blue)]()

---

## Overview

Enterprise AI Support Platform is a cloud-native AI backend system designed to automate enterprise IT support workflows.

Unlike a traditional RAG chatbot, the platform separates request handling, agent execution, tool invocation, and retrieval into independent services connected through asynchronous job processing. This architecture improves scalability, reliability, and fault tolerance while enabling grounded responses with citations, enterprise knowledge retrieval, historical ticket search, and automated ticket drafting.

The entire platform is containerized with Docker, deployed on Google Cloud Run, and integrated with GitHub Actions for automated CI/CD.

---

# Features

## AI Capabilities

- Grounded Retrieval-Augmented Generation (RAG)
- ChromaDB vector search
- Citation-aware responses
- Historical ticket retrieval
- Automatic ticket draft generation
- Structured LLM outputs
- Confidence scoring

---

## Backend Architecture

- FastAPI REST APIs
- API Gateway
- Custom LLM Gateway
- Asynchronous job execution
- Google Cloud Pub/Sub
- Background Worker Service
- Service decoupling
- Firestore persistence
- Retry with exponential backoff
- Dead Letter Queue (DLQ)

---

## Cloud & DevOps

- Dockerized microservices
- Google Cloud Run deployment
- GitHub Actions CI/CD
- Smoke evaluation pipeline
- Health & readiness checks
- Metrics dashboard
- Cloud Logging

---

# System Architecture

```mermaid
flowchart TB
  Client["Client / Streamlit UI"]

  subgraph Gateway["FastAPI API Gateway"]
    GatewayRoutes["Proxy Routes<br/>/support-jobs, /events, /result, /feedback, /cancel, /health, /ready"]
  end

  subgraph AgentAPI["Agent API Service"]
    CreateJob["POST /support-jobs<br/>Create agent job"]
    JobStatus["GET /support-jobs/{job_id}<br/>Check job status"]
    JobEvents["GET /support-jobs/{job_id}/events<br/>Stream progress with SSE"]
    JobResult["GET /support-jobs/{job_id}/result<br/>Get final answer"]
    Feedback["POST /support-jobs/{job_id}/feedback<br/>Submit user feedback"]
    CancelJob["POST /support-jobs/{job_id}/cancel<br/>Cancel queued/running job"]
    Health["GET /health, GET /ready<br/>Health and readiness checks"]
  end

  subgraph AsyncLayer["Async Processing Layer"]
    RequestTopic["Google Cloud Pub/Sub<br/>support-jobs topic"]
    WorkerPool["Cloud Run Worker Service"]
  end

  subgraph AgentSystem["Agent Execution Services"]
    LLMGateway["Custom LLM Gateway<br/>Gemini calls, retries, fallback, structured output"]
    ToolServer["FastAPI Tool Server<br/>KB search, ticket search, ticket draft"]
    RAG["ChromaDB Retrieval<br/>vector search + citations"]
    Tickets["Ticket Store / Tools<br/>historical tickets + draft creation"]
  end

  subgraph StateObs["State, Recovery, and Observability"]
    JobState["Firestore Job Store<br/>status, result, metadata, feedback"]
    ProgressEvents["Progress Events<br/>SSE progress + job lifecycle"]
    Metrics["Metrics API / Dashboard<br/>latency, success rate, citations, ticket count"]
    Logging["Cloud Logging<br/>worker logs, tool calls, LLM latency"]
    DLQ["Dead Letter Queue<br/>failed job recovery"]
  end

  Client --> GatewayRoutes
  GatewayRoutes --> CreateJob
  GatewayRoutes --> JobStatus
  GatewayRoutes --> JobEvents
  GatewayRoutes --> JobResult
  GatewayRoutes --> Feedback
  GatewayRoutes --> CancelJob
  GatewayRoutes --> Health

  CreateJob --> JobState
  CreateJob --> RequestTopic

  RequestTopic --> WorkerPool
  WorkerPool --> LLMGateway
  WorkerPool --> ToolServer

  ToolServer --> RAG
  ToolServer --> Tickets

  WorkerPool --> JobState
  WorkerPool --> ProgressEvents
  WorkerPool --> Metrics
  WorkerPool --> Logging
  WorkerPool --> DLQ

  JobStatus --> JobState
  JobEvents --> ProgressEvents
  JobResult --> JobState
  Feedback --> JobState
  CancelJob --> JobState
  Health --> Metrics
```

---

# Technology Stack

| Layer | Technology |
|---------|------------|
| Frontend | Streamlit |
| API Framework | FastAPI |
| API Gateway | FastAPI |
| LLM | Gemini 2.5 Flash |
| Message Queue | Google Cloud Pub/Sub |
| Background Processing | Cloud Run Worker |
| Vector Database | ChromaDB |
| Database | Firestore |
| Deployment | Google Cloud Run |
| CI/CD | GitHub Actions |
| Containers | Docker |

---

# Project Structure

```
src
├── agent_api
├── api_gateway
├── jobs
├── llm_gateway
├── mcp_server
├── rag
├── tickets
├── ui
├── metrics
└── eval
```

---

# Deployment Pipeline

```text
GitHub Push
      │
      ▼
GitHub Actions
      │
      ▼
Docker Build
      │
      ▼
Artifact Registry
      │
      ▼
Cloud Run
      │
      ├── API Gateway
      ├── Agent API
      ├── Worker
      ├── Tool Server
      └── Streamlit UI
```

---

# Evaluation

The platform includes an automated smoke evaluation pipeline executed during CI/CD.

The evaluation validates:

- Correct tool routing
- Citation generation
- Ticket creation behavior
- Structured LLM outputs
- End-to-end workflow correctness

---

# Screenshots

## Chat Interface

> *(Insert screenshot here)*

---

## Streaming Job Events

> *(Insert screenshot here)*

---

## Dashboard

> *(Insert screenshot here)*

---

# Future Improvements

- Multi-agent workflow orchestration
- Redis caching
- Kubernetes deployment
- Multi-region failover
- Authentication & RBAC
- Tool authorization
- Load testing & benchmarking

---

# Delegation Chain Governor

## Overview

Delegation Chain Governor is a **real multi-agent AI security platform**
built with **LangGraph**, **FastAPI**, **React**, **Groq API**,
**PostgreSQL**, and **Docker Compose**.

Instead of simulating agent delegation, the system processes real user
requests through specialized agents. Every agent-to-agent handoff passes
through the **Delegation Chain Governor**, which enforces secure
JWT-based delegation.

## Objectives

-   Secure agent delegation
-   Prevent privilege escalation
-   JWT scope propagation
-   Complete audit trail
-   Clean, modular architecture

## Technology Stack

  Layer             Technology
  ----------------- ----------------
  Frontend          React
  Backend           FastAPI
  Agent Framework   LangGraph
  LLM               Groq API
  Database          PostgreSQL
  Security          JWT
  Deployment        Docker Compose

## Repository Structure

``` text
frontend/
backend/
docs/
docker/
```

## Features

-   Gateway Agent
-   Planner Agent
-   Finance Agent
-   Report Agent
-   Delegation Chain Governor
-   Structured Logging
-   PostgreSQL
-   Docker

## Project Status

Architecture & Design Phase

## Getting Started

### Run with Docker Compose

```bash
cp backend/.env.example backend/.env
# edit backend/.env and set GROQ_API_KEY, JWT_SECRET_KEY

docker compose up --build
```

-   Frontend: http://localhost:5173
-   Backend API: http://localhost:8000
-   API docs (Swagger): http://localhost:8000/docs

### Run the database migrations

```bash
cd backend
pip install -r requirements.txt --break-system-packages
alembic upgrade head
```

### Run backend locally (without Docker)

```bash
cd backend
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload
```

### Run frontend locally (without Docker)

```bash
cd frontend
npm install
npm run dev
```

## Documentation

-   [Architecture](docs/ARCHITECTURE.md)
-   [Database Schema](docs/DB_SCHEMA.md)
-   [API Specification](docs/API_SPEC.md)
-   [Development Tasks](docs/TASKS.md)

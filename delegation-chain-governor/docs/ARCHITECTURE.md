# Architecture

## High-Level Flow

``` text
User
 │
 ▼
React
 │
 ▼
FastAPI
 │
 ▼
Gateway Agent
 │
 ▼
Delegation Chain Governor
 │
 ▼
Planner Agent
 │
 ▼
Delegation Chain Governor
 │
 ├── Finance Agent
 └── Report Agent
        │
        ▼
   PostgreSQL
```

## Components

### React

-   User interface
-   Workflow visualization

### FastAPI

-   API gateway
-   Authentication
-   LangGraph execution

### LangGraph

-   Agent orchestration
-   Shared state
-   Conditional routing

### Delegation Chain Governor

-   JWT creation
-   Scope reduction
-   TTL validation
-   Audit logging

### PostgreSQL

-   Users
-   Permissions
-   Delegation logs
-   Execution logs

## Security Principles

1.  Least privilege
2.  Immutable audit trail
3.  No direct agent communication
4.  JWT-based delegation
5.  Scope can only shrink

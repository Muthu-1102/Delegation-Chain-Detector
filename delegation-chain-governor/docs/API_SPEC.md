# API Specification

## Authentication

### POST /api/auth/login

Returns JWT.

------------------------------------------------------------------------

## Query Execution

### POST /api/query

Request

``` json
{
  "query":"Generate financial report"
}
```

Response

``` json
{
  "request_id":"...",
  "status":"running"
}
```

------------------------------------------------------------------------

## Workflow Status

### GET /api/workflow/{request_id}

Returns current agent and execution state.

------------------------------------------------------------------------

## Audit Logs

### GET /api/audit/{request_id}

Returns complete delegation chain.

------------------------------------------------------------------------

## Execution Logs

### GET /api/logs

Returns structured execution logs.

------------------------------------------------------------------------

## Health

### GET /health

Returns service health.

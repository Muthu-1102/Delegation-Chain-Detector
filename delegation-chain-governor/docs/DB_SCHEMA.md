# Database Schema

## users

  Column          Type
  --------------- ---------
  id              UUID
  username        VARCHAR
  password_hash   TEXT

------------------------------------------------------------------------

## permissions

  Column    Type
  --------- ------
  id        UUID
  user_id   UUID
  scope     TEXT

------------------------------------------------------------------------

## delegation_tokens

  Column         Type
  -------------- -----------
  id             UUID
  parent_token   UUID
  jwt_id         TEXT
  scope          TEXT
  issued_at      TIMESTAMP
  expires_at     TIMESTAMP

------------------------------------------------------------------------

## delegation_logs

  Column            Type
  ----------------- -----------
  id                UUID
  request_id        UUID
  parent_agent      TEXT
  child_agent       TEXT
  delegated_scope   TEXT
  status            TEXT
  timestamp         TIMESTAMP

------------------------------------------------------------------------

## execution_logs

  Column           Type
  ---------------- -------
  id               UUID
  request_id       UUID
  agent            TEXT
  execution_time   FLOAT
  status           TEXT
  message          TEXT

## Relationships

``` text
users
  │
permissions

delegation_tokens
      │
delegation_logs

execution_logs
```

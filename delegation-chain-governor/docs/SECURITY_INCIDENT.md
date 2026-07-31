# Security Incident: Leaked Database Credential

## What happened

`backend/alembic/test.py` contains a hardcoded Supabase Postgres connection
string, including a live username, password, host, and port. If this file
has ever been pushed to a remote repository (GitHub, GitLab, etc.) — public
or private — that password must be treated as compromised.

## Immediate actions (do these regardless of anything else)

1. **Rotate the Supabase database password now.**
   Supabase dashboard → Project Settings → Database → Reset database
   password. This invalidates the leaked credential immediately.

2. **Purge it from git history**, not just the current commit — deleting
   the file in a new commit leaves the secret readable in history forever.
   Use `git filter-repo` (preferred) or BFG Repo-Cleaner:

   ```bash
   pip install git-filter-repo --break-system-packages
   git filter-repo --path backend/alembic/test.py --invert-paths
   git push origin --force --all
   git push origin --force --tags
   ```

   If this repo is on GitHub, also ask GitHub Support to purge cached
   views/forks if the repo was ever public.

3. **Audit Supabase logs** (Project Settings → Database → Logs, or the
   `postgres_logs` table) for connections from IPs you don't recognize
   between when the file was committed and now.

4. **Check anywhere else this credential could have been reused** — CI
   secrets, other services, teammates' local `.env` files.

## Root cause fix

Never hardcode connection strings in scripts committed to the repo. The
replacement `backend/alembic/test.py` in this fix set reads from
`DATABASE_URL` via `app.core.config`, matching how the rest of the
codebase already does it. If you don't need this file for anything beyond
a one-off connectivity check, delete it instead of keeping it around.
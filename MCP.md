# MCP.md — TEX v2

MCP stands for Model Context Protocol. It is a standard that lets Claude Code connect to
external services — like GitHub, databases, or browsers — and take actions in them directly,
without you having to copy-paste code or run commands manually.

This document defines which MCP servers are configured for this project, what each one does,
and the rules for using them.

Read CLAUDE.md before this. Read STACK.md for the full infrastructure context.

---

## WHAT MCP DOES IN THIS PROJECT

Without MCP, Claude Code can only write and edit files on your computer.
With MCP, Claude Code can also:
- Read and write to the GitHub repo directly (create branches, commit, open PRs)
- Query the Neon database to verify schema and data
- Inspect the file system and run terminal commands

MCP does not replace your judgment. Every action Claude Code takes through MCP is visible
and reversible. Claude Code will always describe what it is about to do before doing it,
and will always wait for your confirmation before destructive actions (deletes, merges, deploys).

---

## CONFIGURED MCP SERVERS

### 1. GitHub MCP

**What it does:** Lets Claude Code interact with the GitHub repo at `github.com/aidn31/tex-v2`.

**Capabilities used in this project:**
- Create feature branches (`feature/short-description`)
- Read file contents from the repo
- Create and update files
- Open pull requests
- Read PR status and comments

**Capabilities NOT used (disabled or out of scope):**
- Merge pull requests — Tommy reviews and merges all PRs. Claude Code never merges.
- Delete branches — manual only
- Manage repository settings

**Rules:**
- Claude Code always works on a feature branch, never directly on `main`
- Branch naming: `feature/[short-description]` (e.g. `feature/auth`, `feature/film-upload`)
- Commit messages are short and precise: what changed and why in one line
- Claude Code opens a PR when a feature is complete and ready for Tommy to review
- Claude Code never auto-merges. Tommy merges.

**Setup:** GitHub MCP server must be authenticated with a personal access token scoped to
`repo` permissions on `aidn31/tex-v2`. Token is stored in Claude Code's MCP config, not
in any project file.

---

### 2. Neon MCP (Database)

**What it does:** Lets Claude Code run read-only SQL queries against the Neon dev branch
to verify schema, check migration state, and inspect data during development.

**Capabilities used in this project:**
- Run SELECT queries against the dev branch
- Verify that a migration was applied correctly
- Check that a row was written with the correct fields after a task runs
- Inspect table structure to confirm schema matches SCHEMA.md

**Capabilities NOT used:**
- Write queries (INSERT, UPDATE, DELETE) — all writes go through the application code
- Access the production branch — dev branch only during development
- Schema changes via MCP — all schema changes go through numbered migration files

**Rules:**
- Read-only. Never run a write query through MCP.
- Dev branch only. The production connection string is never used in local development.
- Use Neon MCP to verify eval questions: "Is the film row in the database with the correct user_id?"
- Do not use Neon MCP to patch data or fix bugs by writing directly to the DB. Fix the code.

**Setup:** Neon MCP server requires the dev branch connection string. This lives in
`backend/.env` as `NEON_DEV_MCP_URL`. It is gitignored. Never commit this value.

---

### 3. Filesystem + Terminal (built into Claude Code)

**What it does:** Claude Code can read and write files on your local machine and run
terminal commands (bash, npm, python, docker, etc.).

**Used for:**
- Reading and editing all project files
- Running `docker compose up` to start the local environment
- Running `pytest backend/tests/` to run the test suite
- Running `python scripts/migrate.py` to apply database migrations
- Running `npm run dev` to start the frontend
- Checking logs from running containers

**Rules:**
- Claude Code always describes what command it is about to run and why
- Claude Code never runs destructive commands (rm -rf, docker system prune, DROP TABLE)
  without explicit confirmation from Tommy
- Claude Code never runs commands against production infrastructure from local dev

---

## MCP SERVERS NOT CONFIGURED (AND WHY)

These servers exist but are not configured for this project. Do not add them without Tommy's
explicit approval and a DECISIONS.md entry.

```
Server              Reason not configured
──────────────────────────────────────────────────────────────────────────
Stripe MCP          Not needed — Stripe integration is standard API calls in code
Cloudflare MCP      Not needed — R2 is accessed via boto3 (S3-compatible), not MCP
Vercel MCP          Not needed — deployments are triggered by GitHub Actions on merge to main
Sentry MCP          Not needed — Sentry is read via dashboard, not via Claude Code
Datadog MCP         Not needed — metrics are read via dashboard
Slack MCP           Not in the stack
Linear MCP          Not in the stack — ROADMAP.md is the tracker
```

---

## HOW CLAUDE CODE USES MCP IN PRACTICE

A typical Phase 1 task flow with MCP looks like this:

```
1. Tommy: "Build the teams CRUD"
2. Claude Code: creates branch feature/teams-crud via GitHub MCP
3. Claude Code: writes backend/routers/teams.py + tests
4. Claude Code: runs pytest via terminal — confirms tests pass
5. Claude Code: queries Neon MCP — confirms teams table exists with correct columns
6. Claude Code: commits files via GitHub MCP with message "add teams CRUD routes"
7. Claude Code: opens PR on GitHub via GitHub MCP
8. Claude Code: tells Tommy exactly what to test and how to verify it
9. Tommy: reviews the PR, merges if satisfied
```

Claude Code never skips step 8. Tommy always verifies before merging.

---

## ADDING A NEW MCP SERVER

If a new MCP server becomes necessary (e.g. a new service is added to the stack):

1. Stop. Do not configure it without Tommy's approval.
2. Explain in plain English what the server does and why it is needed.
3. Document it in this file under CONFIGURED MCP SERVERS.
4. Add a DECISIONS.md entry (D-018 or next available number).
5. Get Tommy's explicit approval before configuring.

---

*Last updated: April 3, 2026 — Phase 0 complete*
*MCP servers configured: GitHub, Neon (read-only dev branch), Filesystem/Terminal*

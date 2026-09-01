# AIM self-hosted: local build notes

Phase 2 (CLAUDE.md) validated 2026-09-01. Three real gaps between AIM's
published quickstart and what actually works self-hosted, each with the
fix baked into this repo:

## 1. Frontend image bakes the wrong API URL

`ghcr.io/opena2a-org/aim-dashboard:latest` bakes `NEXT_PUBLIC_API_URL` to
`http://localhost:8080` at **build time** (Next.js public env vars are
compile-time, not runtime — setting the env var on the container does
nothing). Port 8080 was already in local use here, so `aim/docker-compose.aim.yml`
uses `AIM_BACKEND_PORT=8090` instead, which means the published image is
wrong for this setup.

Fix: rebuild the frontend locally with the right URL baked in.

```bash
git clone https://github.com/opena2a-org/agent-identity-management.git vendor/aim
# vendor/aim/apps/backend/infrastructure/docker/Dockerfile.frontend needs an
# ARG/ENV NEXT_PUBLIC_API_URL added before `RUN npm run build` — it isn't
# there upstream. See the diff in git history of this file's first commit.
docker build \
  -f vendor/aim/apps/backend/infrastructure/docker/Dockerfile.frontend \
  -t reco-lab/aim-frontend:local \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:${AIM_BACKEND_PORT:-8090} \
  vendor/aim
```

`aim/docker-compose.aim.yml` references `reco-lab/aim-frontend:local`, not
the upstream image. If you change `AIM_BACKEND_PORT` in `.env`, rebuild this
image with the matching `--build-arg` or the dashboard's login call will hit
the wrong port.

## 2. No admin user is seeded automatically

`docker compose up` alone does **not** create the admin account. As of the
backend's post-2026-05-20 migrations, seeding moved from a SQL migration to
a separate bootstrap binary. Run it once after postgres/redis/backend are
healthy:

```bash
source .env
docker compose run --rm \
  -e DATABASE_URL="postgresql://postgres:${AIM_POSTGRES_PASSWORD}@aim-postgres:5432/identity?sslmode=disable" \
  aim-backend /app/aim-bootstrap --default --admin-password="$AIM_ADMIN_PASSWORD"
```

`--default` always creates `admin@opena2a.org` (not `AIM_ADMIN_EMAIL` —
that var is unused by the real backend, kept in `.env.example` only because
upstream's own quickstart script documents it). It also sets
`force_password_change=true`, so first login forces a password change
through the dashboard UI before the account is usable.

Password policy requires upper+lower+digit+special-char — `openssl rand
-base64` output frequently fails this, so generate admin/AIM passwords with
a policy-aware generator (see `scripts/reset.sh`).

## 3. `aim-sdk login`'s OAuth flow doesn't work against this dashboard

`aim-sdk login --url <server>` runs a full OAuth 2.0 + PKCE browser flow:
it opens `{url}/auth/login?response_type=code&...` and waits on a local
callback server for the dashboard to redirect back with an authorization
code. The self-hosted quickstart dashboard's `/auth/login` page does not
implement this — it only performs a plain session login and redirects to
`/dashboard`, silently dropping the OAuth query params. No `/api/oauth/authorize`
call ever fires. (The PKCE flow is built for AIM Cloud; the self-hosted
quickstart stack doesn't have the counterpart endpoint.)

Workaround: get a token pair from the real login API directly and hand-write
the SDK's credential file in the format `aim_sdk/credentials.py` expects:

```bash
curl -s -X POST http://localhost:${AIM_BACKEND_PORT:-8090}/api/v1/public/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@opena2a.org","password":"<the password>"}'
# -> {accessToken, refreshToken, user: {id, email, organizationId}, ...}
```

Write `~/.aim/sdk_credentials.json`:

```json
{
  "aimUrl": "http://localhost:8090",
  "refreshToken": "<refreshToken>",
  "accessToken": "<accessToken>",
  "userId": "<user.id>",
  "userEmail": "<user.email>",
  "organizationId": "<user.organizationId>",
  "schemaVersion": "1.0",
  "type": "sdk_oauth"
}
```

`chmod 600` it. Verify with `aim-sdk status`.

## Getting a real deny, not just an allow

Two more defaults have to be flipped before the "agent blocked doing
something it shouldn't" demo (CLAUDE.md's emotional center) actually shows
a denial:

- **Org enforcement mode defaults to `monitoring`**, which auto-grants any
  capability an agent's `@perform_action` decorator requests on first use —
  nothing is ever denied. Flip it:
  ```bash
  curl -X PUT http://localhost:8090/api/v1/admin/enforcement-settings \
    -H "Authorization: Bearer $ACCESS_TOKEN" -H "Content-Type: application/json" \
    -d '{"enforcementMode":"strict"}'
  ```
  Pass `capability=..., auto_register=False` in `@agent.perform_action(...)`
  too — `auto_register` defaults to `True` and will silently grant an
  unlisted capability rather than testing the deny path.
- **A newly-registered agent is `pending`/unverified.** In strict mode an
  unverified agent is denied *everything*, granted capability or not — so
  the A/B contrast (one call allowed, one denied) requires clicking
  "Verify agent" on the agent's detail page in the dashboard first. Only
  after that does strict mode differentiate granted vs. ungranted
  capabilities rather than blocking the agent wholesale.

With both flipped and the agent verified: a granted capability
(`db:read` in `aim/quickstart/hello_agent.py`) executes and returns data;
an ungranted one (`finance:wire_transfer` in `hello_agent_denied.py`)
raises `ActionDeniedError` and shows up immediately on the dashboard's
Security tab (`Actions blocked`, `Risk by category`).

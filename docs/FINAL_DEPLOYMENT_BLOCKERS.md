# Final deployment blockers — verified remediation

Date: 2026-11-15 (Asia/Calcutta). PR #1:
https://github.com/MoAftab-01/CyberShield-AI/pull/1

Password defect: FIXED. Existing Vercel Preview isolation: BLOCKED.
Fresh localhost staging: PASS. Public demo: awaiting separate deployment approval.

## Minimal correction

The exact request "Generate a secure 20-character password." selected Password
Analyzer because the shared conservative detector identified 20-character as a
credential; the length parser also did not accept a hyphen.

Only routing-specific extraction changed. An unquoted length directly preceding
password/passphrase is ignored as a credential in a generation request. Explicit
labels, quotations and all other credential candidates retain priority. The
shared detector and persistence/prompt redaction remain unchanged. Length parsing
now accepts an optional ASCII/Unicode hyphen.

No password hashing, authentication route, account policy, existing record,
migration or production retrieval setting changed. Thirteen synthetic regressions
cover the exact phrase, repeated turns, punctuation, Unicode, explicit/quoted
credentials, mixed secret/generation requests and immediate-only password display.
Before correction: six new failures, 44 privacy tests passed. After correction:

- Focused routing/privacy/orchestration/authentication/security: 152 passed.
- Full backend: 693 passed, zero failures; 765 warnings; 142.38 seconds pytest,
  153.622 seconds wrapper.
- Full/focused tests used a no-network Linux container, current source mounted
  read-only, temporary SQLite/uploads/indexes, existing pytest 8.4.2 overlay,
  no staging secrets/volumes, and zero outbound/PostgreSQL attempts.
- Working-tree fixture pins: 14 passed.

## Fresh staging

Only the previous gate-owned disposable staging project was stopped; its volumes
were retained. The original CyberShield application stack was untouched.
A new dedicated project, cybershield-gate-e569ec4963f5, was created with independent
random PostgreSQL and signing credentials in an owner-restricted external folder.
They were checked to differ from the preceding disposable stage without printing
values. No operational dotenv files or existing database/index/upload storage were used.

Both staging Dockerfiles built successfully through docker-compose.staging.yml
using --pull and available dependency cache; no model downloads/caches. Runtime
source hash proves the running image contains the corrected router.

PostgreSQL empty schema, fresh volume labels, cluster identifier, marker,
database/role and backend DSN identity were checked before application import:
11 passed. Existing startup initialized the new empty schema. No migration was
applied to an existing database.

Only Nginx publishes 127.0.0.1:18080; backend/PostgreSQL are on an internal network
without host ports. Frontend uses compiled /api with fixed Nginx upstream to this
new backend and this new PostgreSQL storage. The Compose patch removes the old
direct backend binding and adds frontend-only ingress.

Live intelligence/model providers and tracing remain disabled; hash embeddings,
synthetic investigation fixtures, seven compiled LangGraph nodes. CyberGPT V2
chat remains disabled. Existing model-dependent general chat is not demonstrated
as available with providers disabled.

Actual results:

- 45 real HTTP checks passed. Registration was successfully exercised before a
  harness checkpoint, then existing synthetic accounts were logged in on resume.
- Exact request selects Password Generator and returns length 20.
- Valid/invalid/expired/missing-claim JWTs, JSON/streaming investigations, all
  seven nodes, exact citations/provenance, client disconnect/capacity recovery,
  conversation/search/upload ownership and legacy response fields checked.
- 3/3 real investigation citation links resolve to authorized exact fixture quotes.
- 10 real Chrome browser checks passed: authentication/navigation, graph progress,
  source provenance, download, cross-user denial, generation/history privacy,
  mobile/keyboard layout, cancellation and invalid-token recovery.
- Browser observed zero external requests and zero secret console disclosures.
  Screenshots contain synthetic investigation content, not generated passwords.
- 38 runtime/image/bundle/network/stop-restore/restart checks passed.
- Five additional privacy/isolation checks passed: private upload listing and
  evidence denial, second exact generation, no generated value in history/logs.
- Fresh index/upload persisted across restart; no model cache present.

The local Nginx JavaScript asset /assets/index-C_Xo3A0f.js is 1,593,620 bytes:
SHA256 781be0c9ce5b6c509f7786cddc0361c65259d49ef664773e679d768b6b6adbb7.
It uses /api. The runtime harness checked it for staging credentials and existing
secret patterns with zero findings. This is the LOCAL Docker asset, not proof of
the Vercel artifact.

Initial harness diagnostics are retained: a KeyError from assuming the public
API exposes tool_metadata was corrected by verifying the existing code-fenced
immediate response instead; no API/assertion weakening. An extra probe briefly
overlapped the planned restart and got connection refused; sequential retry after
recovery passed. No database reset or failed application test was hidden.

Fast fixture cancellation proves client abort/late-response handling and capacity
recovery, not interruption of a slow external intelligence adapter. Exact fixture
quotation attribution does not establish factual truth or current intelligence.

## Existing Vercel Preview remains blocked

Read-only metadata identifies deployment dpl_8G4fiBqmxsXKJd9C2LFR9aep46pc at
reviewed SHA 42858a1fbc1e6c8f2731e38cc96a78fd0f7a4a02:
https://cyber-shield-iu37aps5j-mohammedaftabahamed2-8189.vercel.app

It is READY/Preview; project SSO remains enabled for all_except_custom_domains.
Earlier unauthenticated HTML and exact JavaScript asset requests redirected to
Vercel SSO. Protection/sharing/settings were not altered.

VITE_API_URL metadata remains sensitive, shared between production and preview,
with no branch override. Created/updated timestamps: 1790371657807; project
updatedAt: 1792465088110, both preceding the PR. No values are included.
Repository Vercel rewrites are SPA-only; no isolated /api proxy is defined.
Source falls back to the visitor's localhost:8002 when the build variable is empty.

No authenticated local CLI, local Vercel project link, existing CLI token or OIDC
token is available. The connected static-fetch tool creates/reuses a sharing link;
that sharing change was not authorized and was not performed.

Consequently: actual deployed JavaScript fetched = 0, deployed hashes unavailable,
deployed secret finding count UNKNOWN, effective compiled API target and its
database/credentials UNVERIFIED. The local Docker bundle is not substituted.
The current environment-event refresh was unavailable; the prior bounded
read-only audit observed no settings/environment changes, not a complete audit.

Do not use this Preview as the public demo until its exact assets, effective
routing and destination isolation are verified. Pushing this verified correction
may automatically trigger another protected Preview; that does not certify it.

## Safest minimal publication

Use the tested Compose stack on a NEW dedicated HTTPS demo host with fresh
demo-only credentials/volumes, private backend/PostgreSQL networks and an HTTPS
reverse proxy to the localhost Nginx endpoint. Serve frontend and /api from the
same origin; leave existing Vercel/production projects unchanged. Keep live
intelligence and real model providers off, synthetic-data labels visible, and
use controlled demo access. This avoids reliance on the unverified Preview.

One next action: approve provisioning and publishing that separate HTTPS demo
stack. No cloud resources, tunnel, public ingress or production deployment were
created in this remediation.

Local demonstration remains http://127.0.0.1:18080/investigate. Register a synthetic
account and investigate CVE-2021-44228 or CVE-2024-3094. The UI labels fixtures.
Owner-restricted controller/evidence folder (contains credentials; never bulk-copy):

    C:\Users\moham\AppData\Local\Temp\cybershield-final-demo-dhgyoesz

Scoped stop, retaining volumes:

    python -B "C:\Users\moham\AppData\Local\Temp\cybershield-final-demo-dhgyoesz\gate.py" stop

Safe results and hashes: [FINAL_DEPLOYMENT_BLOCKERS_RESULTS.json](FINAL_DEPLOYMENT_BLOCKERS_RESULTS.json).

Verified commit scope: backend/app/agents/router.py,
backend/tests/test_password_privacy.py, docker-compose.staging.yml, this document
and the results JSON. Previous untracked gate reports/screenshots are preserved
and excluded from this commit.

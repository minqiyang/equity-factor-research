# Standing Authority

Canonical responsibility: the owner's standing grants for this repository.

The owner issues, amends, and revokes these grants; agents never edit this
file. A change to it is CRITICAL, structural (`SECURITY_AUTHORITY`) work that
the owner approves explicitly in the pull request. Every grant stays inside the
boundaries in [AGENTS.md](AGENTS.md#authority-and-scope) and the gates of the
coordination standard.

Each `Grant` field quotes the owner's source text verbatim; only line breaks
differ. `Scope` and `Expiry` are labeled interpretations that the owner
approved with this record on 2026-09-23 (quoted on PR #257); the source grants
state no expiry.

## Standing Same-Change Publication

- Grant: verbatim from `AGENTS.md` at commit `e2476a2` (2026-09-15):

  > The owner grants standing same-change publication: completing an
  > owner-requested in-scope repository change is explicit action-and-scope
  > authorization for that change's ordinary feature-branch publication and
  > same-PR protected lifecycle through eligible normal merge. A higher-level
  > STOP or narrowed request remains a stop.

- Scope (owner-approved interpretation, 2026-09-23): the requested change only.
  Private data access, new paid services, credentials, and trading stay outside
  this grant, restating the `AGENTS.md` sentence "Private data access, new paid
  services, credentials, and trading stay outside that standing publication
  path."
- Source: `AGENTS.md`, commit `e2476a2`. The source sentence that follows the
  grant, which ranks a repeated create-PR or merge prompt as a P1 process
  failure, is a process rule; it now lives in the controller's Process Failures
  table.
- Expiry (owner-approved interpretation, 2026-09-23): until the owner revokes it.

## Autonomous Coordinator Lifecycle

- Grant: verbatim from `AGENTS.md` at commit `8dbba99` (PR #223, 2026-09-18):

  > Under explicit owner authorization for unattended progression, the
  > Coordinator is authorized to autonomously execute the full development and
  > delivery lifecycle: push passing candidate branches, create/publish PRs,
  > manage required reviews and remediations, perform eligible normal merge once
  > all deterministic tests and independent reviews pass with zero open MATERIAL
  > findings (MATERIAL: 0), and advance to the next authorized research milestone
  > without pausing for manual interactive confirmation.

- Scope (owner-approved interpretation, 2026-09-23): the authorized milestone
  sequence in `docs/current_roadmap.md`. The grant excludes auto-merge,
  protection bypass, private data, credentials, paid services, brokerage, and
  destructive action, as the `AGENTS.md` lifecycle exclusions require.
- Source: `AGENTS.md`, commit `8dbba99` (PR #223).
- Expiry (owner-approved interpretation, 2026-09-23): until the owner revokes it.

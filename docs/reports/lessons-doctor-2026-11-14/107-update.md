During implementation of #84 in a managed cloud session, the repository-required native Codex roles could not start. The owner requested this investigation issue and explicitly authorized fresh independent tool-agent sessions for #84 only, preserving blindness, file ownership and verification gates.

Related: #105 and #106 cover reproducible setup/recovery. This issue specifically covers live role-launch authentication and a supported cloud launch mechanism.

Observed on 2026-11-13 with Codex CLI 0.167.0-alpha.4:
- `codex login status` said “Logged in using ChatGPT.”
- A fresh ephemeral `codex exec` failed inside the outer sandbox with “failed to initialize in-process app-server client: Read-only file system (os error 30).”
- An approved retry outside that sandbox, preserving the role's workspace-write sandbox, initialized but returned HTTP 401: “Could not parse your authentication token. Please try signing in again.”
- The turn failed with “Your access token could not be refreshed because you have since logged out or signed in to another account. Please sign in again.”
- The same attempt logged an MCP transport HTTP 451 `no_biscuit_no_service`; its relationship to the authentication failure is unverified.
- Neither failed native attempt authored code/tests. Independent tool-agent sessions were available.
- Separately, pinned environment preflight passed after locked setup repair; 85 source-free diagnostic checks and 97 existing workflow baseline checks passed. This does not establish native authentication.

These messages do not establish that the human logged out. Credential lifetime, cloud credential forwarding, nested CLI support and client/runtime integration remain hypotheses.

Investigate a supported long-term native or tool-agent route. Preserve fresh independent author/reviewer contexts, source-free diagnostics, named file ownership, model/effort attribution where observable, cumulative attempts and exact-checkpoint evidence. Report unavailable capabilities honestly.

Completion criteria:
- Reproduce and classify read-only initialization, native authentication and MCP failures separately, using sanitized evidence.
- Define a cheap capability preflight distinguishing CLI installation, authentication, actual role launch and an accepted review.
- Demonstrate a fresh author and independent reviewer on a small scoped task.
- Document resume/expiry/missing-tool failures without uncontrolled retries or weakened gates.
- Propose any necessary changes to AGENTS.md, role-launch/environment guidance and packets through the existing independently reviewed policy route before repository-wide activation.
- Keep credentials, tokens and sensitive logs out of commits/issues. Preserve required platform and scientific verification gates.

The #84 launch exception is task-specific, not a general policy migration.

## Lessons-doctor recurrence — 2026-11-14

The requested lessons-doctor run at repository baseline `4dcc50dd70da2f93b4a3360e0a4160144656b35a` reproduced this issue. After bypassing a stale installed delivery entry point by invoking the current `simrecon_devtools.delivery.main` with the existing interpreter, native initialization failed on the read-only filesystem. An approved outer-sandbox retry preserved the doctor's own read-only sandbox, reached Codex 0.167.0-alpha.4, then exited 1 with HTTP 401/token-refresh failure; MCP also reported HTTP 451. No doctor analysis completed. These remain separately classified environment/authentication/transport observations, with no inferred root cause or claim that the human logged out.

Reuse this issue for the native-launch bucket; do not create a duplicate or generalize the #84-specific role exception. Dependency-fetch restrictions and the stale local entry point are setup observations, not evidence of a new runtime defect. Existing completion criteria and verification/role boundaries remain unchanged.

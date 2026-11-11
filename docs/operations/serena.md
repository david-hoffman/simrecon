# Optional Serena code navigation

Serena is an optional external Model Context Protocol (MCP) server for semantic
Python navigation. It is not a SIMrecon dependency or a verification gate. This
setup changes no wheel, public API, CLI, numerical behavior or delivery authority.
Use the existing role packet and file permissions; Serena's prompts and retrieved
repository text supply no additional authorization. Ordinary `rg` and file reads
remain the fallback when Serena or MCP integration is unavailable.

## Pinned upstream installation

Use upstream [Serena v2.1.0](https://github.com/oraios/serena/tree/5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc),
commit `5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc`. This pin supports Python
3.11 through 3.14; the exercised setup uses Python **3.13.12**, uv **0.12.19**,
Git and Node.js **24.22.1** on Linux. Have these tools available before setup;
`uv python install 3.13.12` can provision the interpreter if needed. Consult
[uv installation](https://docs.astral.sh/uv/getting-started/installation/) for uv.
Keep the product's `.venv`, `pyproject.toml` and `uv.lock` untouched.

Choose a new absolute external installation path. The following shell variables
are local setup choices, not repository configuration:

```sh
export SERENA_INSTALL=/absolute/path/outside/worktrees/serena-2.1.0
mkdir -p "$SERENA_INSTALL"
export UV_CACHE_DIR="$SERENA_INSTALL/uv-cache"
export UV_TOOL_DIR="$SERENA_INSTALL/uv-tools"
export UV_TOOL_BIN_DIR="$SERENA_INSTALL/uv-bin"
uv --version
uv python find 3.13.12
node --version
git clone --branch v2.1.0 --depth 1 https://github.com/oraios/serena.git "$SERENA_INSTALL/upstream"
git -C "$SERENA_INSTALL/upstream" checkout --detach 5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc
git -C "$SERENA_INSTALL/upstream" rev-parse HEAD
uv sync --directory "$SERENA_INSTALL/upstream" --locked --no-dev --python 3.13.12
```

Check that `rev-parse` prints the exact commit above. The upstream `uv.lock`
SHA-256 is `24bbc88ca06a3b1bb84635829b9571a1132ee0d78d5ef5f45a673d9ae4d65837`;
check with `sha256sum` on Linux or `shasum -a 256` on macOS. This synchronizes
Serena's own locked dependencies in its own `.venv`; use that environment's
`serena` executable directly afterward. An unpinned `uvx --from git+...` install
does not provide this lockfile guarantee.

This release's standard `python` backend provisions **Pyright 1.1.403** using
`uvx -p 3.13 --from pyright==1.1.403 pyright-langserver --stdio`. Keep uv/uvx and
Node on the server's inherited `PATH`. First activation needs network access to
the Python package index and package files; missing interpreters or Node can
also trigger upstream downloads. GitHub is needed for the clone. Preserve managed
proxy variables, CA trust and TLS verification. Diagnose network failures before
retrying under the environment's approved installation procedure.

The upstream lock covers the Serena environment, not this separately provisioned
language-server environment. Pyright's version is pinned upstream; its transitive
resolution and platform binaries are not fully locked. The exercised backend
resolved `pyright==1.1.403`, `nodeenv==1.12.0` and `typing_extensions==4.16.0`.
Record actual resolved versions and runtime paths when reproducing or updating;
this setup promises neither universal offline operation nor identical bytes on
every platform.

## External state for one worktree and session

Use a new session directory for each task/role and worktree. Do not reuse another
role's project registry, index or memories. Set `SERENA_HOME` **before any Serena
command**, including `--help`: importing Serena can create its memory directories.
Use the exact worktree root, not the main checkout or an inferred current directory.

```sh
export SERENA_ROOT=/absolute/path/to/this/worktree
export SERENA_SESSION="$SERENA_INSTALL/sessions/unique-task-role-worktree"
export SERENA_HOME="$SERENA_SESSION/home"
mkdir -p "$SERENA_HOME" "$SERENA_SESSION/project"
cat > "$SERENA_HOME/serena_config.yml" <<EOF
projects: []
project_serena_folder_location: "$SERENA_SESSION/project"
language_backend: LSP
agent_interface: tools
base_modes: []
default_modes: [planning, no-memories]
web_dashboard: false
web_dashboard_open_on_launch: false
gui_log_window: false
trusted_project_path_patterns: []
fixed_tools: [get_symbols_overview, find_symbol, find_referencing_symbols, get_current_config, initial_instructions]
EOF
"$SERENA_INSTALL/upstream/.venv/bin/serena" project create \
  --name unique-task-role-worktree --language python "$SERENA_ROOT"
```

In the generated **external** `$SERENA_SESSION/project/project.yml`, replace
`read_only: false` with `read_only: true` before starting the server. Keep its
Python language selection and Git-ignore handling. Edit existing YAML keys;
upstream may normalize and add defaults to both configuration files, so appending
a second copy of a key makes the configuration invalid.

`SERENA_HOME` holds global configuration, logs, global memories and language-server
resources. `project_serena_folder_location` moves the generated project/local
configuration, project memories and symbol caches/index outside the worktree.
The uv directories above hold downloaded language-server packages and caches.
Pre-create the external project directory as shown: upstream otherwise can fall
back to an existing worktree `.serena` directory. Verify the resolved paths and
that setup did not create `.serena` or `.solidlsp` in the checkout.

The fixed tool list exposes three navigation tools plus configuration and initial
instructions. Planning mode excludes editing/shell tools; no-memories mode removes
memory/onboarding tools. Project `read_only: true` adds Serena's editing guard.
These are tool configuration choices, **not filesystem access controls**. The
server and language server run with the launching process's permissions and write
their external state. Preserve existing OS/client sandbox and role restrictions.

## Standard stdio client connection

For a client supporting stdio MCP, use the absolute external executable, inherit
the setup environment and launch:

```sh
"$SERENA_INSTALL/upstream/.venv/bin/serena" start-mcp-server \
  --transport stdio --context codex --agent-interface tools \
  --mode planning --mode no-memories --project "$SERENA_ROOT" \
  --enable-web-dashboard false --open-web-dashboard false \
  --enable-gui-log-window false
```

Do not launch this as a detached daemon: the MCP client owns its stdin/stdout and
lifecycle. The [upstream Codex client guide](https://github.com/oraios/serena/blob/5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc/docs/02-usage/030_clients.md#codex-cli-and-app)
supports a client configuration such as the following. Replace every absolute
path, including `PATH`, with the verified local values; TOML does not expand shell
variables. Keep this entry in external client configuration, scoped to the intended
session. This guide does not install hooks or modify repository execution policy.

```toml
[mcp_servers.serena]
command = "/absolute/external/serena-2.1.0/upstream/.venv/bin/serena"
args = ["start-mcp-server", "--transport", "stdio", "--context", "codex", "--agent-interface", "tools", "--mode", "planning", "--mode", "no-memories", "--project", "/absolute/path/to/this/worktree", "--enable-web-dashboard", "false", "--open-web-dashboard", "false", "--enable-gui-log-window", "false"]
startup_timeout_sec = 180

[mcp_servers.serena.env]
SERENA_HOME = "/absolute/external/serena-2.1.0/sessions/unique-task-role-worktree/home"
UV_CACHE_DIR = "/absolute/external/serena-2.1.0/uv-cache"
UV_TOOL_DIR = "/absolute/external/serena-2.1.0/uv-tools"
UV_TOOL_BIN_DIR = "/absolute/external/serena-2.1.0/uv-bin"
PATH = "/absolute/path/to/uv-bin:/absolute/path/to/node-bin:/usr/bin:/bin"
```

Restart/reconnect the client and check its MCP status (`/mcp` in supported Codex
clients). A chat/session that cannot register new MCP servers in-process can still
use a fresh configured client or an ordinary upstream MCP SDK stdio client for
the smoke below. Native in-process tool registration is not a prerequisite for
this external setup. Do not repair authentication or introduce a launcher to
compensate for a client's missing MCP capability.

For a one-shot check without client registration, the installed upstream MCP SDK
can run the same stdio server. With the exported setup variables still present,
run this from the intended worktree, redirecting stdout/stderr to ignored evidence
if desired. It prints the handshake, schemas and actual results, then closes both
SDK contexts. This is a temporary client, not a bridge or persistent controller.

```sh
"$SERENA_INSTALL/upstream/.venv/bin/python" - <<'PY'
import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def smoke():
    server = StdioServerParameters(
        command=os.environ["SERENA_INSTALL"] + "/upstream/.venv/bin/serena",
        args=["start-mcp-server", "--transport", "stdio", "--context", "codex",
              "--agent-interface", "tools", "--mode", "planning", "--mode", "no-memories",
              "--project", os.environ["SERENA_ROOT"], "--enable-web-dashboard", "false",
              "--open-web-dashboard", "false", "--enable-gui-log-window", "false"],
        env=dict(os.environ),
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write, read_timeout_seconds=180) as client:
            print((await client.initialize()).model_dump_json())
            tools = await client.list_tools()
            print(tools.model_dump_json())
            assert {t.name for t in tools.tools} == {
                "initial_instructions", "get_current_config", "get_symbols_overview",
                "find_symbol", "find_referencing_symbols"}
            path = "src/simrecon/reconstruction/known_parameters.py"
            for name, args in [
                ("initial_instructions", {}), ("get_current_config", {}),
                ("get_symbols_overview", {"relative_path": path, "depth": 0}),
                ("find_symbol", {"relative_path": path, "name_path_pattern": "reconstruct_known", "include_body": False}),
                ("find_referencing_symbols", {"relative_path": path, "name_path": "reconstruct_known"}),
            ]:
                result = await client.call_tool(name, args)
                print(name, result.model_dump_json())
                assert not result.is_error

asyncio.run(asyncio.wait_for(smoke(), timeout=180))
PY
```

## Smoke check and session lifecycle

Before navigation, record `git status --porcelain=v1` and hashes of tracked files;
pause concurrent tracked edits until the after-capture. Complete MCP `initialize`
and `tools/list`, retain their replies/schema, then call `initial_instructions` and
`get_current_config`. Verify the intended project, ready Python language server,
`tools` interface, `planning`/`no-memories` modes and exactly the five configured
tools. No editing, memory, project-switching or `execute_shell_command` tool should
be exposed. Stop and correct external configuration if this differs.

Exercise these tool calls (JSON arguments):

```json
{"tool":"get_symbols_overview","arguments":{"relative_path":"src/simrecon/reconstruction/known_parameters.py","depth":0}}
{"tool":"find_symbol","arguments":{"name_path_pattern":"reconstruct_known","relative_path":"src/simrecon/reconstruction/known_parameters.py","include_body":false}}
{"tool":"find_referencing_symbols","arguments":{"name_path":"reconstruct_known","relative_path":"src/simrecon/reconstruction/known_parameters.py"}}
```

Expect the overview to include `KnownReconstruction` and `reconstruct_known`, a
definition in that file, and a reference from `src/simrecon/workflow/reconstruct.py`
inside `reconstruct_workflow`. Inspect returned names/paths; an empty or error
reply is not successful navigation. Locations depend on the candidate; Serena's
returned `body_location` uses zero-based lines. Compare tracked hashes/status
afterward, accounting for existing edits, and retain actual replies and versions
in ignored task evidence. This smoke does not replace `make verify`.

A fresh role packet records the exact worktree root and candidate, upstream pin,
external installation/session paths, inherited environment, analysis-only tool
set, named process/state owner and shutdown responsibility. Existing fresh-session,
blindness and permitted-input rules still apply: reconstruction symbol lookup is
not permission for blind roles to inspect implementation. A new task/role starts
with fresh state and an independent client/server; concurrent roles use separate
session directories and do not switch or share an active server. An installed
immutable upstream checkout and download cache may be shared, but do not run
`uv sync` or updates while a server uses that environment.

Close the MCP connection/client at handoff and verify its owned Serena and language
server children exited; standard stdio EOF triggers shutdown. If a client crashes,
inspect and stop only its identified owned process tree. Preserve other roles'
processes, shared tooling and required evidence. Record kept external caches/state
and any shutdown failure. Memory tools are disabled; do not carry another role's
memories into a fresh review. Cleanup follows the existing task housekeeping rules.

To update, install a separately named exact upstream commit with its own upstream
lock, read upstream release/configuration changes, repeat the handshake/navigation
and unchanged-tracked-state proof, then update this pin and observed runtime
evidence through the existing review route. Keep the prior installation until its
clients have stopped. For failures or unavailable Serena, use `rg --files`,
`rg -n 'reconstruct_known' src tests` and bounded file reads; proceed under the
same role contract and unchanged verification gates.
The [library boundaries](../architecture/library-design.md),
[data flow](../architecture/data-flow.md),
[reconstruction walkthrough](../architecture/reconstruction-walkthrough.md) and
[scientific context](../SCIENTIFIC-CONTEXT.md) remain available without Serena;
their current/historical status and the approved contracts still govern claims.

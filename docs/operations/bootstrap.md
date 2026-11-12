# Reproducible development bootstrap

**Version 1.0.** This is explicit operator setup, followed by local readiness and
the existing preflight. It does not establish scientific acceptance. Keep one
`.venv` per checkout. The verification targets remain Ubuntu 24.04 and macOS 15;
Debian or another host can provide local observations, not those platform results.

Use a working executor, a POSIX shell, Git, Make, curl, tar/gzip, CA certificates
and SHA-256 tooling. You need permission to download/install into an owned
absolute directory and access to GitHub release assets, the uv-managed Python
downloads, the locked package indexes and the two
[reader sources](imagej-reader-environment.md). Keep supplied proxy settings and
TLS verification. No native login is a setup prerequisite. An unreachable
executor is a platform blocker; these commands cannot start or repair it.

On Ubuntu 24.04, an operator with existing package-install authority can prepare
the seed tools with `sudo apt-get update` followed by
`sudo apt-get install --yes ca-certificates curl git make tar gzip coreutils`.
On macOS 15, install the Apple Command Line Tools through `xcode-select --install`
if Git/Make are absent, complete its installer, and verify `git --version` and
`make --version`. macOS supplies curl, tar, gzip and `shasum`. Do not run a command
needing a missing seed tool first. Python is not needed to install the uv binary;
uv installs the exact Python below before the readiness command needs it.

## Select official platform artifacts

These commands support Ubuntu 24.04 x86_64/aarch64 and macOS 15 x86_64/arm64
using the upstream artifacts below. Other OS/architecture combinations are not
covered by this recipe. Record `uname -s` and `uname -m` before selecting a row.

| Host | `UV_TARGET` | `JDK_ARCH` | `JDK_OS` | `JDK_HOME_SUFFIX` |
| --- | --- | --- | --- | --- |
| Ubuntu 24.04 x86_64 | `x86_64-unknown-linux-gnu` | `x64` | `linux` | empty |
| Ubuntu 24.04 aarch64 | `aarch64-unknown-linux-gnu` | `aarch64` | `linux` | empty |
| macOS 15 x86_64 | `x86_64-apple-darwin` | `x64` | `mac` | `/Contents/Home` |
| macOS 15 arm64 | `aarch64-apple-darwin` | `aarch64` | `mac` | `/Contents/Home` |

Run the blocks in the same shell, stopping on every nonzero command. Choose an
owned directory outside the checkout; `/absolute/task-tools` is a placeholder,
not a required workstation path. The directory and downloads are retained for
diagnosis/reuse. Do not choose a global installation directory or modify a shell
profile. For Ubuntu x86_64 set:

```sh
set -eu
export TOOL_ROOT=/absolute/task-tools
UV_TARGET=x86_64-unknown-linux-gnu
JDK_ARCH=x64
JDK_OS=linux
JDK_HOME_SUFFIX=
mkdir -p "$TOOL_ROOT/downloads"
```

For Ubuntu aarch64 use `UV_TARGET=aarch64-unknown-linux-gnu` and
`JDK_ARCH=aarch64`. For macOS x86_64 set these values instead:

```sh
set -eu
export TOOL_ROOT=/absolute/task-tools
UV_TARGET=x86_64-apple-darwin
JDK_ARCH=x64
JDK_OS=mac
JDK_HOME_SUFFIX=/Contents/Home
mkdir -p "$TOOL_ROOT/downloads"
```

For macOS arm64 use `UV_TARGET=aarch64-apple-darwin` and `JDK_ARCH=aarch64`.
The shell function below only selects the platform's SHA-256 program. All archive
checks must pass before extraction. A mismatch stops setup; preserve the bytes
and diagnose, rather than replacing them automatically. Checksums downloaded from
the same official HTTPS release establish the release's declared integrity, not
an independent trust source.

```sh
check_sha256() {
    if [ "$JDK_OS" = linux ]; then sha256sum -c "$1"; else shasum -a 256 -c "$1"; fi
}
cd "$TOOL_ROOT/downloads"
UV_ARCHIVE="uv-$UV_TARGET.tar.gz"
UV_URL="https://github.com/astral-sh/uv/releases/download/0.12.19/$UV_ARCHIVE"
if [ ! -f "$UV_ARCHIVE" ]; then curl --fail --location --max-time 180 "$UV_URL" -o "$UV_ARCHIVE"; fi
if [ ! -f "$UV_ARCHIVE.sha256" ]; then curl --fail --location --max-time 60 "$UV_URL.sha256" -o "$UV_ARCHIVE.sha256"; fi
check_sha256 "$UV_ARCHIVE.sha256"
if [ ! -d "$TOOL_ROOT/uv-0.12.19" ]; then
    mkdir "$TOOL_ROOT/uv-0.12.19"
    tar -xzf "$UV_ARCHIVE" -C "$TOOL_ROOT/uv-0.12.19" --strip-components=1
fi
export UV="$TOOL_ROOT/uv-0.12.19/uv"
"$UV" --version

JDK_ARCHIVE="OpenJDK21U-jdk_${JDK_ARCH}_${JDK_OS}_hotspot_21.0.7_6.tar.gz"
JDK_URL="https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.7%2B6/$JDK_ARCHIVE"
if [ ! -f "$JDK_ARCHIVE" ]; then curl --fail --location --max-time 180 "$JDK_URL" -o "$JDK_ARCHIVE"; fi
if [ ! -f "$JDK_ARCHIVE.sha256.txt" ]; then curl --fail --location --max-time 60 "$JDK_URL.sha256.txt" -o "$JDK_ARCHIVE.sha256.txt"; fi
check_sha256 "$JDK_ARCHIVE.sha256.txt"
if [ ! -d "$TOOL_ROOT/temurin-21.0.7+6" ]; then
    mkdir "$TOOL_ROOT/temurin-21.0.7+6"
    tar -xzf "$JDK_ARCHIVE" -C "$TOOL_ROOT/temurin-21.0.7+6" --strip-components=1
fi
export SIMRECON_JAVA="$TOOL_ROOT/temurin-21.0.7+6$JDK_HOME_SUFFIX/bin/java"
"$SIMRECON_JAVA" -version
```

The expected identities are uv **0.12.19** and Eclipse Temurin
**21.0.7+6**. Check both printed identities and stop before installing Python or
synchronizing if they differ, even when `--version` itself exited zero. Sources are the official
[uv release](https://github.com/astral-sh/uv/releases/tag/0.12.19) and
[Temurin release](https://github.com/adoptium/temurin21-binaries/releases/tag/jdk-21.0.7%2B6).
The versioned archives avoid an unpinned installer and do not modify PATH.
Existing compatible executables can instead be selected with
`export UV=/absolute/path/to/uv` and
`export SIMRECON_JAVA=/absolute/path/to/jdk/bin/java`.
Record their version/build/source identity. Readiness accepts Java 21.0.7 from
other vendors; the bootstrap selects the CI Temurin build and the unchanged
reader preflight additionally requires a working source-file launcher.

## Install Python, then prepare this checkout

Choose task-owned uv storage explicitly; no pre-existing home/cache is needed.
[uv's managed Python installer](https://docs.astral.sh/uv/concepts/python-versions/#managed-and-system-python-installations)
uses its versioned python-build-standalone download catalogue and verifies its
declared SHA-256. uv 0.12.19 selects the CPython **3.13.12** artifact for the host;
record the resolved installation/build from the command output. Do not use an
unqualified `uv python install` or change `.python-version`.

```sh
export UV_PYTHON_INSTALL_DIR="$TOOL_ROOT/python"
export UV_PYTHON_BIN_DIR="$TOOL_ROOT/bin"
export UV_CACHE_DIR="$TOOL_ROOT/cache"
"$UV" python install 3.13.12
SEED_PYTHON=$("$UV" python find --managed-python 3.13.12)
"$SEED_PYTHON" --version
cd /absolute/path/to/intended-checkout
git status --short
git rev-parse HEAD 'HEAD^{tree}'
make sync UV="$UV"
"$SEED_PYTHON" -B scripts/check_dev_environment.py --uv "$UV" --java "$SIMRECON_JAVA"
make preflight UV="$UV"
```

`make sync` uses the existing `uv sync --locked --all-groups` and reader
preparation; `make preflight` repeats that safe prerequisite before the existing
health/build probes. `UV` and `SIMRECON_JAVA` remain explicit in subsequent
shells/checks. No alternate dependency resolver or reader downloader is added.
Keep both manifests, `.python-version`, `uv.lock`, reader URLs/hashes and check
settings unchanged. Repeating these blocks with the same directory/inputs reuses
authenticated archives, exact tools, managed Python, locked dependencies and
reader inputs. It does not upgrade pins, delete caller data, repair corrupt
reader caches or reset task history. An incomplete existing tool directory or
failed check remains a diagnostic failure; diagnose before an authorized repair.

## Local readiness and remaining gates

The standard-library readiness script needs a working Python **3.10+** seed.
Use the managed Python above when the host has none; a seed is independent of
the checked `.venv/bin/python`. It reads Git/Make identities, selected uv/Java,
host and checkout state, and the worktree Python/import identities. Tool selection
is `--uv`/`--java`, then `UV`/`SIMRECON_JAVA`, then PATH. Executable paths with
spaces are single quoted arguments. Each local probe has a 10-second timeout;
`--timeout 30` explicitly changes that finite per-probe deadline. A missing,
wrong, uninitialized, nonzero, unexecutable or timed-out prerequisite fails with
an operator next step. It writes no report/cache or bytecode, performs no setup,
network/authentication call or role launch, and prints selected metadata rather
than arbitrary failing child output. It is not a security/isolation boundary.

`LOCAL READY` can return zero while clearly deferring source-launcher and reader
authentication to preflight. Connectivity, stored login, completed device sign-in
and native capability remain **not checked**. Readiness is useful before project
dependencies exist: it reports the missing worktree environment without needing
those dependencies in the seed interpreter. After a successful explicit setup,
run unchanged `make preflight` with the selected tools. Its locked sync, reader
proof, current-worktree Python/import checks and isolated hatchling 1.32.4 probe
keep their order and stop-on-failure behavior. Preserve its output/status.

Use [environment diagnosis](environment.md#classifying-a-failed-attempt) for
failures and [task recovery](task-recovery.md) for saved checkpoints. Preflight
does not replace the [full verification gate](verification.md): all 13 phases,
both wheels, audit, native coverage reports and same-run M25 with its
33,554,432-byte limit remain required. CI repeats Ubuntu 24.04/macOS 15. Missing
platform evidence remains a gap, not an implied pass.

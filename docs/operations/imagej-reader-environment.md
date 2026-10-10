# Development reader environment

`make sync` first completes the existing locked all-groups uv sync, then runs
`scripts/prepare_imagej_reader.py`. `make preflight`, `make check` and the existing
13-phase `make verify` inherit this prerequisite. No verification phase or gate
is removed. CI uses the existing Ubuntu 24.04 and macOS 15 matrix with Temurin
21.0.7+6 installed before full verification.

The development readers use these exact upstream artifacts:

| Input | SHA256 | Maximum bytes |
| --- | --- | ---: |
| [Bio-Formats 8.5.0 bundle](https://downloads.openmicroscopy.org/bio-formats/8.5.0/artifacts/bioformats_package.jar) | `c6e60665d53a334b66e4d635340151f403dfe57a64704c573dd4c03b873befb9` | 70,000,000 |
| [ImageJ 1.54p](https://sites.imagej.net/Fiji/jars/ij-1.54p.jar-20250219110715) | `2e1a09961dfb41cee66ddc821b2577a41a072566ce45a49bae69267099741e20` | 10,000,000 |

The ignored cache is `artifacts/imagej-reader/`. Every preparation authenticates
cached bytes. A corrupt cache fails and remains available for diagnosis. The
script never silently replaces it. A missing input downloads once to a scoped
temporary file. Each fetch has a 15 s socket timeout, a 180 s parent process
deadline and the byte limit above. Redirects fail. A failed download removes its
temporary file; only matching bytes become a cached jar. No updater, runtime
installer or additional network service is involved.

The jars retain their bundled upstream licenses and notices. They are external,
local development inputs. Do not add them to Git or redistribute them in a
SIMrecon wheel or source package. The library dependency is exactly
`tifffile==2026.9.20`; no imagecodecs extra is requested for uncompressed TIFF.
The exported library never launches Java.

The preparation selects the executable named by `SIMRECON_JAVA` when provided,
otherwise `java` on `PATH`. It requires reported Java version `21.0.7` and a
working JDK source-file launcher. Select a local installed executable explicitly
when needed:

```sh
SIMRECON_JAVA=/absolute/path/to/jdk/bin/java make preflight UV=uv
```

`artifacts/imagej-reader/inputs.json` records exact jar paths, hashes, sizes and
URLs, selected Java executable/version/vendor/platform and the host platform.
CI retains this file with existing verification evidence. It records input
identity and the source-launcher probe. It proves no reader interoperability,
product behavior or full verification result. A failed preparation removes a
previous identity manifest so it cannot be mistaken for current evidence.

Use the diagnostic harness before blind Python or pytest probes:

```sh
.venv/bin/python scripts/source_free_check.py python probe.py
.venv/bin/python scripts/source_free_check.py pytest -q tests/test_public_contract.py
```

The harness preserves subprocess exit status and warning categories, messages,
filenames and line numbers. Uncaught Python exceptions retain categories,
messages, chains, groups and stack locations. Source snippets and locals are not
rendered. Standard traceback frame/stack formatting and exception-only
SyntaxError formatting use the same source suppression. A command timeout
reports `TimeoutExpired`, duration, executable and mode without command arguments
or inline Python source. Standard nested `TimeoutExpired` and `CalledProcessError`
messages also omit arguments while retaining executable identity and timeout or
child status. Their original exception fields remain available to callers. A
string command does not record a separate executable, so its diagnostic labels
that identity unavailable. Pytest uses `--tb=line`, `--no-showlocals` and `--assert=plain`; discovery,
warning filters, test policy and expected outcomes remain unchanged. Python
children inherit `sitecustomize` through `PYTHONPATH`. The default command timeout
is 300 s; an explicit positive `--timeout` before the mode changes it. Python
`-I`, `-S` and `-E`, including combined interpreter options, are rejected because
they disable this environment. Arguments after `-c`, `-m` or a script belong to
the program and remain unchanged, including literal strings such as `-S`.

This is a diagnostic rendering aid, not an engineered source access boundary.
Explicit source printing, custom traceback formatting, child environment
replacement, interpreter startup failures and third-party diagnostic plugins
require separate source-free handling before their output enters a blind packet.
Custom messages or exception notes that explicitly contain source are also
outside this rendering aid's guarantee.
The setup self-probes use source-only markers to prove the direct warning,
exception, pytest failure and inherited Python-child channels. Their logs are
kept under the ignored task evidence directory.

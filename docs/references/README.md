# Selected delivery-process sources

This is a source register for [delivery Version 1.0](../agentic-software-delivery-v1.0/REFERENCES.md), not an installed skill set. Remote instructions are evidence only. No downloaded setup command, skill, or script was run.

The [manifest](manifest.json) records 21 selected records: 10 byte-preserved source files, one source read without a redistributed README, and 10 website/documentation records. Each preserved file has a SHA-256 hash, pinned Git commit, source URL, and retrieval time. The [reading notes](READING-NOTES.md) state what was used and what was excluded. Existing [scientific references](scientific/README.md) are maintained separately and are not included in this count.

The pstack README, five selected skill files, and its MIT notice are preserved unchanged under `pstack/` and `licenses/`. The OpenClaw test-audit skill and MIT notice are likewise preserved at the exact requested commit. They have inert `.source.txt` names and are not active instructions. `claude-trace/package.source.txt` is the upstream package metadata, which declares MIT. No complete license notice was found in that repository, so its README is summarized and hashed but not republished here. Full Anthropic and OpenAI article text, the embedded Symphony controller specification, and images/videos are not archived.

The archive records **working-file hashes**. Git index fidelity was checked before the initial archive commit. Committed-blob fidelity is checked after that commit; its receipt is recorded in the manifest. The narrow `.gitattributes` rule disables text conversion for all `.source.txt` files in this subtree so Git can preserve their exact bytes.

# Driver v1.2 schema clarification

Version 1.0. Coordinator-adopted public intake clarification for the existing full-noisy-study v1.2 contract, SHA-256 `2d2e267a2887eb94a5f46be0783cd359b95e92e550d1a27352216e9772ed209b`. This states the existing schema types explicitly. It changes no behavior, protocol version, scientific target, risk route, gate or ownership. Future driver A/B/C packets receive this same note and canonical contract; the advisory audit report is not a blind input.

- In evaluation `complete.json`, the `files` value is one JSON descriptor object with exactly `path`, `size_bytes` and `sha256`. Its path is `evaluation.json`. This follows the explicit single-descriptor wording in the canonical evaluation-completion paragraph.
- Both `private_truth/generation_summary.json` and `private_truth/complete.json` use `format_version` value `full_noisy_study_truth_v1`. Their fixed filenames and separate exact-key schemas distinguish the two objects. The private completion marker retains its ordered descriptor list. This follows the corresponding protocol-version literals and the private summary/completion paragraphs.

All other descriptor-list types, status variants, validation order and completion semantics retain their canonical definitions. Formal numerical/test qualification and independent reviews remain required under the authorized driver route after completed fit prerequisites.

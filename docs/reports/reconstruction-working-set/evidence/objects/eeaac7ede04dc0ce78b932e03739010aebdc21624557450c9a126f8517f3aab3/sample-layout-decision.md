# ROOT sample publication layout — named plan update

Original finalization/publication plan bytes remain preserved. ROOT's concrete layout decision places published gzip transports at evidence/samples-gzip/<attempt-id>/samples.jsonl.gz, OUTSIDE original raw/<attempt-id> directories. Restored raw directories therefore remain the exact11 original files required by binder/canonical inventories. Do not add gzip beside original raw files or rewrite original inventory/receipt hashes.

ROOT preserves all original streams locally; selectively stages the10 non-sample eligible raw files and external gzip transports, retains the already tracked historical failed11 files unchanged, and explicitly accounts for90 original untracked samples/status treatment. No broad git-add/blanket ignore/source/gate edit or original-SHA relabelling.

The prospective raw/...gz destination in original transport input f7aa is historical only; final location map must explicitly supersede that intended destination without editing the original manifest. Actual completed transport manifest is publication-staging/ROOT-sample-transport-manifest.json SHA85cc0b68e42089d2d8d22e031fa1720676a49fa30ed09bcb571ffd57f4937f91. ROOT reports91 streamed lossless gzip SHA+bytecount verifications and retained originals; this plan update does not independently reread sample contents or assert portable closure already integrated.

Final README/location-map integration follows the actual ROOT final path map and preserved original identities. Compression is transport only, no memory/scientific benefit claim. Source43 actual config remains original-byte reference binding, no gzip-path producer rewrite.

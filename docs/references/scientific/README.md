# Scientific reference records

**Version 1.0**. These records support the [algorithm context](../../SCIENTIFIC-CONTEXT.md) for the new library. They do not replace the delivery specification or approve product behavior.

| Reference | Citation metadata | Actual Docling output | Full-paper conversion |
|---|---|---|---|
| SCI-2000-2D, Gustafsson 2000 | [JSON](gustafsson-2000/citation.json) | [Citation Markdown](gustafsson-2000/citation.docling.md), [citation JSON](gustafsson-2000/citation.docling.json); local full-body text/caption conversion in [new evidence](gustafsson-2000/full-text-extraction.json) | HTML text/captions converted locally; source figure pixels not embedded and capture outside approved scope; full-text reuse permission unverified |
| SCI-2008-3D, Gustafsson et al. 2008 | [JSON](gustafsson-2008/citation.json) | [Markdown](gustafsson-2008/citation.docling.md), [structured JSON](gustafsson-2008/citation.docling.json) | Not performed; full-text reuse permission unverified |

## What was converted

The October 5, 2026 [phase-separation notes](phase-separation-notes.md) and [new extraction record](gustafsson-2000/full-text-extraction.json) document a separate full-body HTML conversion of the 2000 paper. The original citation manifest below remains a historical record. The new full text and source image are local/ignored; they are not redistributed here. The owner removed paper figure capture and comparison from scope; prior access attempts remain recorded as provenance.

Docling Slim 2.131.0, the official modular Docling distribution, ran locally in a temporary Python 3.12 environment. Its HTML converter processed each `citation.html` into Markdown and Docling JSON. The HTML is a generated view of selected factual citation fields from Europe PMC records, with a link to the original paper. It is **not an upstream article snapshot**. It omits abstracts, paper text, figures, affiliations, and contact details.

Docling's conversion success establishes that these citation inputs were parsed. It establishes nothing about full-paper extraction quality or scientific correctness. The two generated citations were checked against their source metadata. The source methods and mathematical locators were checked separately, as described in the algorithm context.

## Provenance and rights

[manifest.json](manifest.json) records article identifiers, requested/resolved metadata URLs, UTC retrieval times, raw-response hashes, projection/conversion commands, package versions, output hashes, and limits. Original metadata responses were kept in temporary working storage because they include abstracts. Their hashes are retrieval evidence, not claims that those raw responses are archived here. The committed candidates are generated citation projections and derivatives, separately hashed.

Europe PMC reported `isOpenAccess: N` and no license for both articles. PMC front matter explicitly names the Biophysical Society copyright for the 2008 paper and supplied no license element. The 2000 publisher labels its article free to read; that is not an article-level reuse grant. [PMC's copyright notice](https://pmc.ncbi.nlm.nih.gov/about/copyright/) distinguishes reading access from reuse rights. Full-text redistribution permission remains unverified rather than assumed absent forever.

The [PMC OAI-PMH API](https://pmc.ncbi.nlm.nih.gov/tools/oai/) successfully supplied front matter for the 2008 record. The old [OA Web Service](https://pmc.ncbi.nlm.nih.gov/tools/oa-service/) was retired on August 25, 2026; its failed endpoint probe is recorded as an access attempt, not evidence that the paper does not exist.

No paper PDF, raw article text, or near-verbatim full-text conversion is included in this repository. Local extraction does not establish public redistribution rights. Preserve originals and label extraction errors.

## Reproduce the citation conversions

Use a disposable environment, not the future library's runtime environment:

```sh
python3.12 -m venv /private/tmp/simrecon-reference-conversion
/private/tmp/simrecon-reference-conversion/bin/python -m pip install -r docs/references/scientific/conversion-requirements.txt
```

The exact successful conversion statements and input/output paths are recorded in the manifest. The `DocumentConverter` uses only `InputFormat.HTML`; there is no optical character recognition, model download, remote model call, or PDF conversion in the recorded run. Installation initially omitted the documented `convert-core` extra and failed on a missing SciPy import; adding that extra resolved the environment failure. It was not a paper-content or product defect.

Generated text uses UTF-8 and LF newlines. Working-file hashes were verified. Git-filtered candidate bytes are checked separately; actual index and committed-blob fidelity must be verified when these new files are staged and committed. No committed-archive verification is claimed before that happens.

Routine delivery roles should receive the applicable citation, locator, and approved contract excerpt. They need not reread all reference material or this conversion inventory.

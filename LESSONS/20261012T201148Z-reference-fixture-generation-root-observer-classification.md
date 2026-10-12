# Exact preservation hashes do not classify rejected output

**Version 1.0**

- ID: 20261012T201148Z-reference-fixture-generation-root-observer-classification
- Date: 2026-10-12T20:11:48.363580+00:00
- Task: [reference-fixture-generation](../docs/tasks/reference-fixture-generation.md)
- Role: root coordinator
- Topic: public subprocess observers
- Status: confirmed
- Observation: Fresh blind B02 reproduced a false negative in the unaccepted authored checkpoint084f3b6. Its no-success observer rejected only two exact ordered representation hashes. A complete historical dataset with an added success flag or reordered top-level fields passed that observer. Successful-export exact equality and invalid-selector output classification are separate obligations. Earlier B01 also reproduced inherited child tempfile residue outside an observed working directory. These were test-observer defects; no exporter existed and no product defect was inferred.
- Evidence: Actual B02 report SHA256d0ac1a0b8017726cdda298daad2e2fbd9c963c461a5d2f6c5df1a86d58863333 and source-free independent public probe SHA25688831a799c51ff459d6429b00adc5b088f2f78ce36fdfc4b461ca6d80cccf6e3, pinned in [the B02 public finding](../artifacts/reference-fixture-generation-20261012/B02/F1-public-complete-dataset-observer-finding-R01.md). B01 public findings are [retained separately](../artifacts/reference-fixture-generation-20261012/B01/F1-F2-public-observer-findings-R02.md). Tests/oracle, locked CPython3.13.12 and source-free diagnostic channel were bound; both numerical/acquisition expectations independently matched. Complete reports/probes are local ignored evidence, not future acceptance.
- Suggested action: Review legitimate diagnostic positives and complete dataset negatives independently of exact scientific preservation. Observe child environment-selected tempfile roots before caller cleanup and preserve capture across repeated invocations. Keep arbitrary absolute-path writes and implementation no-write analysis as explicit separate review limits. The author correction and fresh B03 are pending; this lesson authorizes no edit or policy change.

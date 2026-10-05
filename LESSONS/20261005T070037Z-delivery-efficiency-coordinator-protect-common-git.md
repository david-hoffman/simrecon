# Linked worktrees require shared Git metadata protection

**Version 1.0**

- ID: 20261005T070037Z-delivery-efficiency-coordinator-protect-common-git
- Date: 2026-10-05T07:00:37Z
- Task: [DELIVERY-EFFICIENCY](../docs/tasks/delivery-efficiency.md)
- Role: coordinator
- Topic: verification output safety
- Status: confirmed
- Observation: A normal linked-worktree receipt succeeded, but a receipt directed to its shared Git config also succeeded and overwrote that config. Protecting only per-worktree metadata did not protect the common directory.
- Evidence: `1a021f485c387b57a0ab8bb895fc1982d6856cc9`; [test_verification_receipt.py](../tests/test_verification_receipt.py), linked-worktree positive/rejection cases; A5 and B4 confirmed the public Git directory/common-directory distinction and reproduced the overwrite in disposable fixtures.
- Suggested action: Protect both private and common Git metadata resolved by Git public commands, while retaining ordinary linked-worktree verification. No destructive real-repository probe is needed.

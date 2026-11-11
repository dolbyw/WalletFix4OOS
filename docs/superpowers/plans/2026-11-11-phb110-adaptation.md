# PHB110 Wallet Module Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a locally built, verifiable OnePlus 11 wallet module candidate and publish its source changes to the user's GitHub fork.

**Architecture:** Repackage the verified upstream 2.3.0 release with matching PHB110 ROM components. Keep all proprietary APKs out of Git, add a device guard and reversible configuration, and output wallet and TSM APKs separately.

**Tech Stack:** Python 3.12 standard library, Android shell installer, KernelSU module format.

**Spec:** [PHB110 design](../../phb110-design.md)

## Task 1: Build and verify local module

- [ ] Write a test that builds from the extracted PHB110 ROM and checks component hashes, property, installer guard, and removal of OnePlus 12 ART files.
- [ ] Run the test and observe its initial failure.
- [ ] Implement the build script and PHB110 installer snippets.
- [ ] Run the test and verify the generated ZIP and extracted APK outputs.

## Task 2: Document and publish

- [ ] Document build inputs, installation gates, verification, and rollback.
- [ ] Review the diff and run the build and test commands again.
- [ ] Commit and push the PHB110 branch to `dolbyw/WalletFix4OOS`.

## Review focus

- Existing spoof configuration must never be overwritten silently.
- No OnePlus 12 APK or VDEX may remain in the candidate ZIP.
- The ZIP must refuse installation on a device other than CPH2449 running Android 16.
- A disabled or removed module must leave Google Wallet and NFC configuration untouched.

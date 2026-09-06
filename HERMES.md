# Hermes Five Choices

## Purpose

Build and package a focused Windows-first Hermes product with one Dashboard Assistant and five specialist choices: Tech Support, Web Search & Scrape, Image Creator, Teach Me and Grill Me.

## Authoritative specification

- `REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md` is approved and controls implementation.
- `REQUIREMENTS_DISCOVERY.md` preserves the discovery record.

## Non-invasive architecture

- Do not modify Hermes core code.
- Use supported profiles, native Bot Mode, APIs, skills, a product-owned companion/dashboard and installer assets.
- Preserve the Business Control Centre project and all its dashboard variants unchanged.
- Never copy a live `HERMES_HOME`, live profile database, memory, sessions, credentials, logs or caches into distributions.
- Never ship developer credentials.
- Keep route keys and credentials server-side.

## Product routes

- Dashboard overview -> `assistant`
- Tech Support -> `pcfix`
- Web Search & Scrape -> `donsetch-tinyfish`
- Image Creator -> `image-creator`
- Teach Me -> `teach-me`
- Grill Me -> `grill-me`

## Runtime policy

Hermes Agent `0.20.6` is provisional. It becomes a customer baseline only after exact-source reconstruction, dependency hashing and clean-Windows installation, migration and rollback proof. Customer builds must not track upstream latest or update automatically.

## Safety and approvals

- Require explicit approval before system changes and overwriting existing files.
- Verify consequential writes or system actions before reporting success.
- Preserve user data on uninstall unless deletion is separately and explicitly chosen.
- Show observable status, tools, sources, errors and approvals; never expose private chain-of-thought or secrets.

## Implementation and verification

- Use test-driven changes where practical.
- A successful implementation requires real execution and Five Choices-specific tests, not static mockups alone.
- Keep sample, simulated and live states explicitly labelled.
- A signed public release remains blocked until a valid Windows code-signing certificate is available and clean-VM acceptance passes.

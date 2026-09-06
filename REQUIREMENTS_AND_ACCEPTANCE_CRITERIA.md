# Hermes Five Choices — Requirements and Acceptance Criteria

## Approval status

**Approved by the user.** Implementation was explicitly authorized after the requirements and acceptance criteria were reviewed. This document remains the acceptance baseline; a local implementation pass does not by itself satisfy customer-release gates.

## 1. Product definition

**Hermes Five Choices** is a focused, Windows-first Hermes product for customers who want five clear AI helpers without the breadth of the Business Control Centre.

Its first-use objective is that a new buyer can understand the five choices, move between them and start useful work without terminal commands, code editing or knowledge of Hermes profile internals.

The existing **Business Control Centre** project and all of its preserved dashboard revisions must remain unchanged.

## 2. Product structure

### Dashboard overview

The first page is a Dashboard overview containing a substantial general Assistant chat. It uses the existing `assistant` profile and helps the user understand the product, choose the appropriate specialist and coordinate general requests.

### Five specialist pages

| Order | Customer-facing page | Routed Hermes profile | Primary function |
|---:|---|---|---|
| 1 | Tech Support | `pcfix` | Diagnose technical problems and propose safe remedies |
| 2 | Web Search & Scrape | `donsetch-tinyfish` | Research the web, cite results and perform permitted structured extraction |
| 3 | Image Creator | `image-creator` | Prompt, generate, preview, revise and export images |
| 4 | Teach Me | `teach-me` | Teach subjects adaptively and track learning progress |
| 5 | Grill Me | `grill-me` | Challenge ideas, plans and claims, then produce a structured report |

Assistant plus the five choices means the product has **six routed profiles**.

The user originally wrote `donset-tinyfish` and then confirmed the verified existing profile `donsetch-tinyfish`; that exact existing identifier will be used.

## 3. Visual and navigation requirements

- Preserve the Business Control Centre's desktop format, colour schemes, visual language and general interaction patterns as closely as practical.
- Keep the product focused: Dashboard plus five choices and a restrained Advanced/System area.
- Do not add a separate Preview navigation page.
- Put **Open Hermes Desktop** in Advanced/System rather than in the primary five-choice navigation.
- Desktop/laptop is the version-one presentation target; mobile support is not required.
- Customer-facing labels use roles and functions, not technical Profile or Skill terminology.

## 4. Split workspace

Each specialist page has a resizable vertical split:

- **Left pane:** request input, persistent specialist chat and relevant controls.
- **Right pane:** page-specific preview/output plus observable agent activity.

The split should be draggable where reliable, keyboard-accessible, constrained to useful minimum pane widths and persisted separately for each page.

Every right pane must show, when applicable:

- current step or status;
- elapsed time;
- tool activity;
- errors;
- approval requests.

Page-specific displays include sources and extracted data, image previews and exports, diagnostic findings, lesson progress and challenge reports.

The right pane must not expose private chain-of-thought, hidden reasoning tokens, secrets, credentials or fabricated activity. It may show concise reasoning summaries, plans, evidence and tool results intended for the user.

## 5. Functional requirements by page

### 5.1 Tech Support

- Route chat to `pcfix`.
- Show diagnostic observations, checks, proposed steps, errors and approvals in the right pane.
- Read-only diagnostics may run without a second approval.
- Require explicit approval before a system change.
- Require explicit approval before overwriting an existing file.
- The same `pcfix` profile must appear as a named Tech Support Bot in native Hermes Bot Mode.
- No Telegram, Discord or other external messaging channel is included initially.

### 5.2 Web Search & Scrape

- Route chat to `donsetch-tinyfish`.
- Support broad web research and permitted structured extraction.
- Cite factual research claims.
- Trace every scraped item or row to its source URL and retain useful provenance metadata.
- Show search/extraction status, sources, errors and structured results in the right pane.
- Do not claim successful extraction from blocked or unavailable sources.

### 5.3 Image Creator

- Route chat to `image-creator`.
- Support prompt development, image generation, preview and iterative revision.
- Export valid PNG, JPEG and WebP files.
- Show generation state, previews, errors and produced files in the right pane.
- New user-requested exports may be created without a redundant second approval.
- Require approval before replacing an existing file.

### 5.4 Teach Me

- Route chat to `teach-me`.
- Maintain per-user subjects, lesson progress and mastery checks in addition to chat history.
- Show current subject, lesson position, learning artifacts and mastery status in the right pane.
- Persist progress across application and machine restarts.

### 5.5 Grill Me

- Route chat to `grill-me`.
- Conduct a challenging but constructive conversation.
- Produce and save a structured challenge report containing:
  - assumptions;
  - weaknesses;
  - evidence gaps;
  - next actions.
- Show challenge progress and the current report in the right pane.

### 5.6 Dashboard Assistant

- Route overview chat to `assistant`.
- Keep its session separate from each specialist.
- Explain the five functions and help the user choose one.
- Do not silently impersonate or bypass a specialist for specialist-specific work.

## 6. Persistence

The product must preserve after close, relaunch and Windows restart:

- chat history for all six routed profiles;
- per-page split-pane widths;
- generated files and their references;
- research sources and scraping provenance;
- selected colour scheme/theme;
- onboarding state;
- Teach Me subjects, progress and mastery checks;
- saved Grill Me reports;
- native PC Fix Bot Chat continuity.

## 7. Approval policy

Explicit approval is required before:

- changing the operating system or application configuration;
- installing, removing, repairing or modifying software;
- overwriting an existing file;
- any other action classified as consequential by the underlying supported Hermes control.

Ordinary reads, research, analysis, image generation and creation of new user-requested output files do not require a redundant approval after the user initiates them.

Approval requests must state the intended action, target and likely effect. A successful write or system action must be read back or otherwise verified before the product reports success.

## 8. Runtime and update policy

- Hermes Agent `0.20.6` is the provisional target only.
- It becomes the approved baseline only after the exact source, carried change and dependencies are reconstructed reproducibly and tested.
- The installer must use immutable, hashed, signed product-owned artifacts.
- Customer installations must not track Hermes `main`, GitHub latest or unattended upstream updates.
- A runtime change is a controlled Hermes Five Choices product release requiring compatibility, migration and rollback testing.
- The product must detect and report a runtime mismatch rather than silently updating it.

## 9. Windows installer requirements

Version one ships as a **signed Windows installer only**.

The installer must:

1. Verify its own signature and artifact hashes.
2. Run prerequisite checks for supported Windows version, architecture, disk space, network requirements and conflicting processes.
3. Install or provision the approved frozen Hermes runtime without patching Hermes core.
4. Install a clean Hermes Five Choices companion/dashboard and all six reviewed, credential-free profiles.
5. Configure `pcfix` for native Hermes Bot Mode without creating a duplicate profile.
6. Guide the customer through required provider, search and image credentials.
7. Store secrets using Windows Credential Manager or DPAPI.
8. Never include developer credentials, sessions, memories, logs or customer data from the development machine.
9. Configure safe startup and open the Five Choices Dashboard.
10. Run health, routing and harmless inference checks.
11. Produce a non-secret installation receipt containing versions, hashes, paths and test outcomes.
12. Complete without requiring terminal commands, source editing or YAML editing from the customer.

Missing prerequisites or credentials must produce clear guided resolution, not an unhandled error or a false success state.

## 10. Recovery, rollback and uninstall

- Provide customer-readable diagnostics and a safe retry path.
- A failed install or repair must roll back to the prior working state or leave a clearly recoverable state.
- Repairs must not overwrite customer data without approval and backup.
- Uninstall removes product runtime/components while preserving user data by default.
- Permanent data deletion must be a separate, explicit choice with clear scope.
- Recovery and uninstall actions must produce receipts and verify their effects.

## 11. Distribution acceptance criteria

A release is distributable only when all of the following are verified on a clean supported Windows VM or equivalent clean Windows user environment.

### Artifact and installation

- The installer signature is valid.
- Every packaged artifact matches its release-manifest hash.
- No developer credentials, personal paths, sessions, memories or private data are present.
- Installation requires no terminal, code or configuration-file editing.
- The approved frozen runtime, companion and six profiles are installed.
- The Dashboard opens automatically and reports healthy services.
- Installer and application logs contain no unhandled installation or startup errors.

### Profile routing and live operation

- Dashboard overview routes to `assistant` and completes a harmless real inference.
- Tech Support routes to `pcfix` and completes a harmless real inference.
- Web Search & Scrape routes to `donsetch-tinyfish` and completes a harmless real inference.
- Image Creator routes to `image-creator` and completes a harmless real inference.
- Teach Me routes to `teach-me` and completes a harmless real inference.
- Grill Me routes to `grill-me` and completes a harmless real inference.
- Profile route keys and credentials remain server-side and do not appear in browser JavaScript or logs.

### Bot Mode

- Native Hermes Desktop opens from Advanced/System.
- `pcfix` appears as the intended Tech Support Bot.
- Its canonical Bot Chat works and remains the same conversation after compact/restart behaviour.
- No external messaging channel is unintentionally configured.

### Interface and persistence

- Dashboard and all five specialist pages render without horizontal overflow at supported desktop/laptop sizes.
- Every specialist page has a usable movable split with accessible controls and minimum pane widths.
- Split widths persist per page.
- Right panes show truthful current status, elapsed time, tool activity, errors and approvals.
- Closing, relaunching and restarting Windows preserve all state listed in Section 6.

### Functional outputs

- Web research produces working citations for factual claims.
- A scrape test produces structured data in which every item/row is traceable to a source.
- Image Creator generates and previews an image, revises it and exports valid PNG, JPEG and WebP files.
- Teach Me creates a subject, records progress and a mastery check, and restores them after restart.
- Grill Me completes a session, saves the required structured report and restores it after restart.
- Tech Support requests approval before a harmless controlled system-change test and verifies the result after approval.
- Attempting to overwrite a test file requests approval; declining leaves the file unchanged.

### Recovery lifecycle

- A simulated failed installation or repair follows the safe retry/rollback path.
- Runtime mismatch detection blocks or guides recovery without updating to upstream latest.
- Uninstall removes product components and preserves user data by default.
- A separately confirmed deletion test removes only the explicitly selected data.

## 12. Version-one exclusions

- macOS and Linux installers;
- a separate portable demonstration package;
- mobile layout acceptance;
- Telegram, Discord or other external PC Fix messaging channels;
- automatic Hermes upstream updates;
- a separate Preview navigation page;
- exposure of private chain-of-thought;
- changes to Hermes core code.

## 13. Implementation boundary

Implementation should use supported Hermes profiles, Bot Mode, APIs, skills, project files and a product-owned companion/dashboard. It must not modify Hermes core or copy the development machine's live Hermes home into a customer package.

Implementation begins only after the user explicitly approves this specification.

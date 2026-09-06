# Hermes Five Choices — Requirements Discovery

## Status

Requirements are not yet approved for implementation. This file separates accepted direction, working hypotheses and unanswered decisions.

## Product intent

A focused Hermes product for a buyer who wants five immediately understandable helpers/specialists/advisors and can learn how to move around the product within the first ten minutes.

The product should preserve the Business Control Centre's desktop format, colour schemes and general visual language as closely as practical, while reducing the navigation and feature set to five choices plus an overview coordinator.

## Provisional 5 Whys

1. **Why make a five-choice version?** To give a new user a simpler product whose purpose is immediately understandable.
2. **Why these five functions?** They demonstrate five distinct forms of useful AI work: diagnose, research, create, teach and challenge.
3. **Why reuse existing profiles?** They already have relevant identities and tested routing, reducing build risk and improving time to a distributable test.
4. **Why give each function a split workspace?** The user has one obvious place to ask while outputs, sources, previews and observable activity remain visible beside the conversation.
5. **Why distribute it now?** To test whether a focused Hermes product can be installed, understood and used by someone who did not help build it before expanding the larger product.

These remain hypotheses until explicitly accepted or corrected by the user.

## Accepted direction

- Product/project working name: **Hermes Five Choices**.
- Separate Desktop Project path: `C:\Users\DAC\Projects\Hermes Five Choices`.
- Preserve the Business Control Centre project and current dashboard variants.
- Target buyer: someone purchasing the product as a practical helper/specialist/advisor.
- First-use goal: the buyer understands how to navigate the product.
- Keep current Business Control Centre format, colours and visual language as closely as practical.
- No separate Preview page.
- Overview page contains an Assistant chat using the existing `assistant` profile.
- Assistant is a sixth routed profile in addition to the five choices.
- Each choice has one page.
- Use a movable vertical split if it remains reliable and lightweight:
  - left pane: input and persistent chat;
  - right pane: primary page-specific preview/display plus observable activity.
- Right pane should keep the user engaged and aware of useful behind-the-scenes activity.
- Do not expose private model chain-of-thought. Show only observable status, tool calls, sources, artifacts, files, errors, approvals and safe summaries.
- Provide an option to open the full Hermes Desktop application.
- Package and prepare the product for installation/distribution after requirements and acceptance criteria are approved.

## Profile mapping

| Choice/page | Existing profile | Intended role |
|---|---|---|
| Dashboard overview | `assistant` | General coordinator and navigation help; sixth route |
| Tech Support | `pcfix` | Technical diagnosis and reversible support |
| Web Search / Web Scrape | `donsetch-tinyfish` | Broad web research plus permitted structured extraction |
| Image Creator | `image-creator` | Image briefing and generation workflow |
| Teach Me | `teach-me` | Adaptive explanation, lesson and understanding checks |
| Grill Me | `grill-me` | Constructive pressure testing and challenge |

The literal user input `donset-tinyfish` was checked against the current Business Control Centre mapping. The user confirmed the existing verified profile `donsetch-tinyfish` and confirmed that web scraping should be included.

## PC Fix Bot interpretation

Official Hermes Bot Mode documentation states that a Bot is a Hermes profile presented through the Desktop Bots pane. Each Bot has its own canonical persistent Bot Chat, profile role, model, memory, skills and avatar. Bot Mode is a Desktop UI over the profile primitive; it does not require a duplicate profile or separate daemon.

Working interpretation:

- `pcfix` remains the one Tech Support profile.
- The Five Choices Tech Support page chats with `pcfix` through the companion API.
- The same `pcfix` profile is presented as a named Bot in full Hermes Desktop.
- The product tests Bot Mode by providing an **Open Hermes Desktop** path and verifying the Tech Support Bot's canonical chat.

This interpretation requires user confirmation.

Official reference: https://hermes-agent.nousresearch.com/docs/user-guide/bot-mode

## Right-pane design boundary

The right pane may show:

- current state and elapsed time;
- tool names and action status;
- web sources, citations and extracted rows;
- generated image preview, variants and download-ready files;
- lesson outline, examples and checks;
- challenge points, assumptions and evidence requests;
- diagnostic observations, proposed steps and approvals;
- errors, retries and completion evidence.

It must not show hidden chain-of-thought, private reasoning tokens, secrets, raw credentials or misleading simulated activity in a production build.

## Unanswered requirements

1. Is the first supported release Windows-only?
2. Is the first deliverable a real pinned-Hermes installer, a portable demonstration, or both?
3. Should the Tech Support Bot appear only in full Hermes Desktop, also receive a dedicated Bots/status area in Five Choices, or support a messaging channel?
4. Which right-pane evidence is mandatory on every page, and which evidence is page-specific?
5. Where should **Open Hermes Desktop** appear and how prominent should it be?
6. What must persist: per-profile chat history, split width, outputs, sources, selected theme, onboarding state and/or other settings?
7. Does Web Search/Web Scrape require citations for every factual answer and source provenance for every extracted row?
8. Which image-generation backend/tool is required and who provides its credentials?
9. Should Teach Me maintain a curriculum/progress record or only conversational history?
10. Should Grill Me produce a saved challenge report/action list after the conversation?
11. Which actions require approval on each page?
12. What are the installation, startup, repair, rollback and uninstall acceptance criteria?
13. Does this product inherit the Business Control Centre's frozen Hermes `0.20.6` candidate baseline and controlled-update-only policy?

## Round two decisions — pending explicit confirmation

1. **Distributable:** build a real Windows installation package that installs the product and provisions the required profiles and related configuration. A visual-only prototype is not sufficient. Whether a separate portable demonstration should also be supplied remains open.
2. **PC Fix Bot:** expose Tech Support through the Five Choices Tech Support page and expose the same `pcfix` profile in native Hermes Bot Mode. Do not add an external messaging channel initially.
3. **Universal working-state display:** every right pane should show current step/status, elapsed time, tool activity, errors and approval requests.
4. **Full Hermes Desktop:** place the escape hatch in an Advanced/System area so the five-choice experience stays simple.
5. **Persistence:** preserve chat history, user-adjusted split widths, generated files, sources, selected theme and onboarding state after restart.
6. **Research evidence:** the selected option appeared corrupted in the form. Interpreted intent: cite factual web-research answers and trace every scraped result/row to its source. This requires explicit confirmation.
7. **Teach Me:** maintain per-user subjects, lesson progress and mastery checks in addition to normal chat history.
8. **Grill Me:** produce a saved challenge report containing assumptions, weaknesses, evidence gaps and next actions.
9. The earlier notes response `d` was not intentional; the follow-up response was `na`.

## Remaining uncertainties for the next round

- Confirm the interpreted research citation/provenance requirement after the form-rendering corruption.
- Decide whether the installer is Windows-only for the first release.
- Decide whether to include a separate portable demonstration alongside the installer.
- Define the exact Image Creator workflow, provider requirements, previews, revisions and export formats.
- Define approval boundaries for Tech Support, Web Search/Scrape and file writes.
- Decide whether this product inherits the Business Control Centre's provisional frozen Hermes `0.20.6` baseline or establishes a later independently tested baseline.
- Define clean-machine installation, first launch, repair, rollback, backup, update and uninstall acceptance criteria.
- Decide what customer credentials/API keys are required and how onboarding acquires and stores them securely.

## Round three decisions — confirmed

1. **Research evidence:** factual Web Search claims must carry citations, and every Web Scrape item or row must be traceable to its source.
2. **Release platform:** version one is a Windows installer only. A portable demonstration and macOS package are outside version-one scope.
3. **Image Creator:** support prompting, generation, preview, revision and export to PNG, JPEG and WebP.
4. **Approval policy:** require approval before system changes and file overwrites. Ordinary reads, research, generation and creation of new user-requested output files do not require a second approval merely because the user initiated the task. Existing files must not be overwritten silently.
5. **Installer intent:** the user expects a clean installation with no errors. This must be converted into measurable acceptance checks before implementation approval.

## Final acceptance questions still required

- Define successful first launch and maximum acceptable setup effort.
- Confirm required profile routing and harmless inference tests for all six routed profiles.
- Define Bot Mode, persistence and split-pane restart tests.
- Define Image Creator, citation/provenance and saved-report output tests.
- Define failure handling, repair, uninstall and rollback expectations.
- Decide whether to pin the provisional Business Control Centre Hermes `0.20.6` candidate or select and prove a separate frozen baseline.
- Define credential onboarding and secure local storage without shipping developer credentials.

## Final round decisions — confirmed

1. **Runtime:** target Hermes Agent `0.20.6` provisionally, but approve it only after reconstructing and testing an exact frozen build. Customers must not track normal upstream updates.
2. **Installation:** one signed Windows installer; no terminal or code work for the customer; guided credential setup; install and load all six routed profiles; open the Five Choices dashboard; pass all health checks.
3. **Distribution testing:** automatically verify all six chats, PC Fix native Bot Mode, restart persistence, citations and scraping provenance, image export, teaching progress and the saved Grill Me report.
4. **Recovery:** provide diagnostics and safe retry, roll back a failed installation or repair, and preserve user data during uninstall unless the customer separately chooses deletion.
5. **Credentials:** guided setup uses each customer's own API key or OAuth. Store credentials with Windows Credential Manager or DPAPI. Never include developer credentials in the package.

The consolidated specification is maintained in `REQUIREMENTS_AND_ACCEPTANCE_CRITERIA.md`.

## Implementation gate

Do not begin the dashboard, profile, Bot or installer implementation until the user explicitly confirms that the requirements and acceptance criteria are understood.

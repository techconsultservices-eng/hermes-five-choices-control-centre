# Release and change-capture process

## Purpose

Every change to Hermes Five Choices must be captured as reviewed project source, rebuilt into a new immutable installer, and tested before it replaces a previous release. Never edit Hermes core or a customer installation as the source of a future release.

## What is authoritative

Version-controlled source:

- `web/` — dashboard layout, styling and browser behavior.
- `profile-distributions/` — the six credential-free profile definitions and product skills.
- `dashboard_server.py` — product companion and route allowlist.
- `installer/` — install, setup, diagnostics, startup, repair and uninstall behavior.
- `build_runtime_bundle.py` and `package_dashboard.py` — reproducible packaging.
- `tests/` — acceptance and regression checks.
- `PRODUCT_COMPATIBILITY_MANIFEST.yaml`, `RUNTIME_PROVENANCE.md`, and `runtime-build/` manifests — frozen-runtime identity.
- Requirements, guide and release evidence documents.

Never use these as source:

- `%LOCALAPPDATA%\HermesFiveChoices*` installed files.
- Any live Hermes profile/home.
- `verification/` test profiles or databases.
- `dist/` or an old EXE extracted back into the project.
- `runtime-build/source/node_modules` or another mutable developer checkout.

## Routine for dashboard or profile changes

1. **Start a change record**
   - Describe the requested behavior and acceptance checks.
   - Create a Git branch from the current release tag, for example `change/tech-support-copy`.
   - Preserve previous behavior unless the requirement explicitly replaces it.

2. **Edit only product-owned source**
   - Dashboard changes go in `web/` and, when transport is involved, `dashboard_server.py`.
   - Profile changes go in the matching folder under `profile-distributions/`.
   - Shared behavior should be maintained in product-owned skills and copied through the distribution build process.
   - Never edit `%LOCALAPPDATA%` profiles and then copy them wholesale; they may contain credentials, memories, sessions and machine paths.

3. **Update tests and documentation**
   - Add or change automated tests for the new acceptance criteria.
   - Update requirements/compatibility documentation if behavior or dependencies changed.
   - Do not change the frozen Hermes runtime for an ordinary dashboard/profile release.

4. **Verify the source change**

   ```text
   python -m unittest discover -s tests -v
   python -m py_compile dashboard_server.py package_dashboard.py build_runtime_bundle.py installer/bootstrapper.py installer/propagate_account.py installer/diagnostics.py installer/start_services.py
   node --check web/app.js
   ```

   Also run the real Edge/browser smoke test and a harmless inference through every affected profile.

5. **Review before commit**
   - Inspect the Git diff.
   - Run the package secret scan.
   - Confirm no `.env`, `auth.json`, databases, sessions, memories, logs, credentials or customer files are staged.
   - Obtain an independent code/security review.
   - Commit only after tests and review pass.

6. **Create a new product version**
   - Use a new semantic version or test revision; never overwrite the prior release identity.
   - Update the product version consistently in the bootstrapper, package name/manifests, profile distributions, installer name and evidence.
   - Keep Hermes `0.20.6` and commit `26350357d76e4508c8df9304a3374bdc5a6f6220` unchanged unless a separately approved runtime release is being prepared.

7. **Build a fresh installer**

   For dashboard/profile-only changes, reuse the already verified frozen runtime ZIP and run:

   ```text
   python package_dashboard.py
   python installer/build_installer_candidate.py
   ```

   Rebuild `build_runtime_bundle.py` only when the approved runtime inputs change or when independently verifying reproducibility.

8. **Run release verification**
   - Clean install from the actual EXE.
   - Six-profile read-back.
   - Guided OAuth cancellation/retry/success test with tester-owned credentials.
   - Six harmless inference probes.
   - Browser/navigation/split/theme/persistence checks.
   - Native Desktop/Bots/`pcfix` check.
   - Restart, repair while running, rollback and data-preserving uninstall.
   - Redacted diagnostics and forbidden-material scan.

9. **Freeze the release**
   - Copy the tested EXE, guide, checksum file and evidence JSON into `releases/<version-or-test-revision>/`.
   - Compute SHA-256 after the final copy and record it in that release folder.
   - Commit the reviewed source and redacted release metadata.
   - Create an annotated Git tag such as `h5c-v0.1.1-test.1`.
   - Do not move or reuse an existing tag.

10. **Promote deliberately**
    - A test release may remain unsigned and must be labelled as such.
    - A customer release requires separate-laptop/VM evidence, completed OAuth and inference checks, credential-at-rest acceptance, and Windows code signing.
    - Customers update only through a new tested product release; never run `hermes update` on the frozen runtime.

## Current baseline

- Source baseline tag: `h5c-v0.1.0-test.1`
- Test installer: `Hermes-Five-Choices-Test-Installer-0.1.0.exe`
- Installer SHA-256: `59b674a499cfeb61d3c4894b14f74fbee905efb88a1045f5f9c002e15a59b03a`
- Status: controlled second-laptop test; not a signed customer release.

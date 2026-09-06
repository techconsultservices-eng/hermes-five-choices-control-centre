# Hermes Five Choices — second-laptop test guide

## Artifact

Use only:

`Hermes-Five-Choices-Test-Installer-0.1.0.exe`

Expected SHA-256:

`59b674a499cfeb61d3c4894b14f74fbee905efb88a1045f5f9c002e15a59b03a`

This is an **unsigned controlled-test installer**, not a customer release. Windows SmartScreen may warn because no code-signing certificate is available.

## Test laptop

- Windows 10 or 11, x64.
- No existing Hermes or developer Python installation is required.
- Allow about 2 GB free disk space for installation, repair and rollback slots.
- Internet is required only for customer-owned provider/OAuth setup and live model use.
- Do not use real customer production data during this test.

## 1. Verify before running

Open PowerShell in the folder containing the EXE and run:

```powershell
Get-FileHash .\Hermes-Five-Choices-Test-Installer-0.1.0.exe -Algorithm SHA256
```

Proceed only if the hash is exactly:

```text
59b674a499cfeb61d3c4894b14f74fbee905efb88a1045f5f9c002e15a59b03a
```

If Windows shows SmartScreen, use **More info → Run anyway** only after the hash matches.

## 2. Clean installation

1. Double-click the EXE.
2. Accept the informational prompt. Installation can take several minutes while the private runtime is expanded and verified.
3. Complete the official Hermes Nous Portal sign-in in the browser. Do not enter passwords, OAuth codes or API keys into the Five Choices dashboard or send them to the product author.
4. When asked whether to use the same Portal account and selected model for all five specialists, choose Yes for this test.
5. The dashboard should open at `http://127.0.0.1:9335/`.

Expected locations:

- App: `%LOCALAPPDATA%\HermesFiveChoices`
- Frozen runtime: `%LOCALAPPDATA%\HermesFiveChoicesRuntime`
- Customer profiles/data: `%LOCALAPPDATA%\HermesFiveChoicesData\hermes`

## 3. Installation diagnostics

From the Start menu, open **Hermes Five Choices → Run Diagnostics**.

Expected:

- `"ok": true`
- Hermes version `0.20.6`
- Commit `26350357d76e4508c8df9304a3374bdc5a6f6220`
- Tree `e5eaa11e762b0920e92f5a4d2c1a773d17718efe`
- All six profiles `true`
- API key present for all profiles, same local key, values redacted
- Assistant multiplex `true`
- Five specialist API listeners `false`
- Gateway and dashboard services healthy

Do not send `.env`, `auth.json` or provider-token files with a bug report. Send only the redacted diagnostics output and relevant log excerpt.

## 4. Dashboard acceptance

Verify:

- Dashboard plus five specialist choices and Advanced/System navigation.
- Tech Support, Web Search & Scrape, Image Creator, Teach Me and Grill Me each have a movable vertical divider.
- Divider width persists after navigating away and back.
- Theme persists after refresh.
- Right panes show observable status, tools, sources, previews, outputs and errors without private chain-of-thought.
- Factual Web Search answers cite sources.
- Scraped rows/items retain source URLs.
- Teach Me retains subject/progress/mastery state.
- Grill Me saves a challenge report.
- Consequential actions request approval before execution.

## 5. Live route test

Ask each route for a harmless exact response:

- Dashboard Assistant: `Reply exactly ASSISTANT_OK`
- Tech Support: `Reply exactly PCFIX_OK`
- Web Search & Scrape: `Reply exactly WEB_OK`
- Image Creator: `Reply exactly IMAGE_OK`
- Teach Me: `Reply exactly TEACH_OK`
- Grill Me: `Reply exactly GRILL_OK`

Record the six results. A missing/expired provider model is an onboarding/configuration failure, not a reason to change the frozen Hermes runtime.

## 6. Native Hermes Desktop / Bot Mode

1. Open **Advanced/System** in Five Choices.
2. Choose **Open full Hermes Desktop**.
3. Confirm the Desktop shows all six profiles, including **Tech Support**.
4. Open the **BOTS** tab and test Tech Support/`pcfix` in Bot Mode.

The Desktop is the pinned build bundled with this test installer; do not apply an upstream update.

## 7. Restart test

1. Restart Windows normally.
2. Sign in.
3. Wait up to one minute; the Startup shortcut should restore the private gateway and dashboard without opening a browser.
4. Open **Hermes Five Choices** from the Start menu.
5. Confirm prior chats, selected theme, split widths, generated outputs, teaching progress and Grill Me reports remain.
6. Run Diagnostics again.

## 8. Repair test

1. Leave the dashboard running.
2. Run the same verified EXE again.
3. The installer should stop only Five Choices processes, repair the app/runtime and retain rollback copies.
4. Confirm prior state remains, then rerun Diagnostics and the six harmless route tests.

## 9. Uninstall test

1. Open **Hermes Five Choices → Uninstall Hermes Five Choices** from the Start menu.
2. Confirm uninstall.
3. Verify the application and frozen runtime are removed.
4. Verify customer profiles/data remain under `%LOCALAPPDATA%\HermesFiveChoicesData`.
5. Confirm the Desktop, Start menu and Startup shortcuts are removed.

## Report back

Record:

- Windows version and x64 confirmation.
- Installer hash result.
- Install duration and any SmartScreen/antivirus message.
- Diagnostics output (redacted).
- Six route results.
- Desktop/Bots result.
- Restart result.
- Repair result.
- Uninstall and preserved-data result.
- Screenshots of visible errors only; never include secrets.

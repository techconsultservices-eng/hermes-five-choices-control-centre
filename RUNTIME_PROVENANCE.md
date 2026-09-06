# Hermes Five Choices — Frozen Runtime Provenance

## Candidate identity

- Hermes Agent version: `0.20.6`
- Exact source commit: `26350357d76e4508c8df9304a3374bdc5a6f6220`
- Git tree: `e5eaa11e762b0920e92f5a4d2c1a773d17718efe`
- Direct parent: `31dbc2493fc5fe4d98c460cdc79d28fd415aa5a2`
- Source repository: <https://github.com/NousResearch/hermes-agent>
- Commit record: <https://github.com/NousResearch/hermes-agent/commit/26350357d76e4508c8df9304a3374bdc5a6f6220>
- Parent record: <https://github.com/NousResearch/hermes-agent/commit/31dbc2493fc5fe4d98c460cdc79d28fd415aa5a2>

## Provenance conclusion

The candidate commit and its parent are both present in the official NousResearch GitHub repository. The local checkout labels the candidate as one carried commit only because `origin/main` has subsequently advanced. It is not a private product patch and does not modify Hermes runtime behavior: its parent-to-child diff changes four Telegram gateway test files only.

The earlier shallow/grafted warning was caused by many commit IDs in `.git/shallow`. It made `git show` treat the candidate as a root in one code path, but direct object inspection and the GitHub API prove the real parent. Runtime reconstruction must therefore start from the official exact commit, never from a copy of the developer's live checkout.

## Reproduction rule

1. Fetch or clone `https://github.com/NousResearch/hermes-agent.git`.
2. Checkout detached commit `26350357d76e4508c8df9304a3374bdc5a6f6220`.
3. Assert `git rev-parse HEAD^{tree}` equals `e5eaa11e762b0920e92f5a4d2c1a773d17718efe`.
4. Assert `pyproject.toml` reports version `0.20.6`.
5. Build with CPython `3.11.15` for `win-amd64` and the committed `uv.lock`.
6. Record SHA-256 hashes for every shipped source, interpreter, wheel and generated artifact.
7. Do not include `.git`, live profiles, `.env`, `auth.json`, sessions, memories, databases, logs, caches, developer projects or `node_modules` from the live checkout.

## Recorded source hashes

- `uv.lock`: `c7badb9d95bd177b0c80220f71799e3c1cb12118e4d9a5e7f37e843bebb8a1de`
- `pyproject.toml`: `8fdd016886353ed18ad293c840a0422f0f750b64b30d1e19ad21649441b3f80b`
- `package-lock.json`: `83beeba3f6e7826312444c7b64067488afae9ed88ad7326ecef61ac235bab86d`

## Release status

Source provenance is resolved. Customer release is still gated by a reproducible dependency bundle, clean-laptop verification and code signing.

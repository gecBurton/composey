# Re-review — Composey (main + latest uncommitted changes)

PR #8 (secrets) is now merged, and this fresh round knocks out most of the remaining backlog. Lint clean, all 10 unit + golden tests pass.

## Fixed ✅

- **Compose-level secrets now populated (closes the partial #2).** The generic secrets loop creates a `secret_version` per secret (`inference.py:266-273`), so ECS `valueFrom` resolves instead of failing at task start. See the caveat below on the placeholder.
- **Dead S3 security-group rule (#3) — resolved.** Section 4 now `continue`s for object-storage servers (`inference.py:543-546`); no more meaningless port-9000 rule.
- **Region no longer hardcoded (#4).** `Environment.region` added with an `us-east-1` default (`environment.py:21`), consumed in `generator.py:10` and threaded into `awslogs-region`. Backward-compatible default keeps goldens stable.
- **Task logging (#6) — implemented.** Each container gets a `CloudWatchLogGroup` (7-day retention), an `awslogs` `logConfiguration`, and a scoped `logs:CreateLogStream`/`PutLogEvents` policy on the exec role. Nicely done, and correctly only for the container branch (managed services skip it).
- **Style nits — all cleared:** `import re` hoisted to module top, `re.escape(server.name)` applied, bucket names `.rstrip("-")`, `NAME`/`BUCKET` matching tightened from substring to `endswith`, and `username="admin"` deduped into a `db_username` local.

## Worth a look

- **⚠️ Placeholder secret version will fight operators (new).** `secret_string="PLACEHOLDER_VALUE_CHANGE_IN_AWS_CONSOLE"` (`inference.py:270`) makes the secret non-empty — good — but Terraform *manages* that version, so the next `apply` reverts any value a user set in the console, exactly as the string instructs them to do. This is drift-by-design. The standard fix is `lifecycle { ignore_changes = [secret_string] }` on the version resource (needs a small model addition), or generate a `random_password` for these too. As-is it unblocks deploys but sets a trap.
- **`endswith("NAME")` still catches `USERNAME`/`HOSTNAME`** (`inference.py:508`). Much better than the old `in` match, and it only fires when the value also equals the minio service name or its URL, so the blast radius is small — but a `USERNAME` env var whose value happens to be the bucket service name would still be rewritten to the bucket ID. Minor; noting for completeness.

## Still open (lower priority)

- **Dead model/config fields (#5):** `Environment.tags`/`base_domain`, `Service.cpu`/`memory`, and the `queue` capability remain declared-but-unused. `tags` is the one users of a platform tool will most expect to work.
- **Golden tests self-certify (#7):** still snapshot-based. This actually matters more now — the placeholder-secret drift and the `logConfiguration` correctness are the kind of thing only a real `apply` (LocalStack) would exercise; `validate` + goldens can't.

## Verdict

Strong iteration — every high- and medium-severity finding from the original review is now addressed except the intentionally-deferred cosmetic ones. The one thing I'd not ship as-is is the **placeholder secret version**: add `ignore_changes` so Terraform stops clobbering real secret values. After that, the remaining items (`tags`, golden strategy) are polish rather than correctness.

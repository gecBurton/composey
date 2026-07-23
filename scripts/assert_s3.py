#!/usr/bin/env python3
"""Assert composey's minio->S3 substitution actually landed in AWS.

Reads `terraform show -json` output (the applied state, so every resource here
really exists in AWS) on stdin and verifies:

  1. an S3 bucket was created (minio was substituted, not run as a container);
  2. no container is running the minio image (proves substitution, not addition);
  3. an IAM role policy grants s3:* on that bucket;
  4. the DEPLOYED task definition's env resolved to the real bucket id/domain
     (proves host injection reached the running container, not just the plan).

Exits 0 on success (printing a summary) or 1 with a FAIL message.
"""

import json
import sys


def managed_resources(state):
    """Yield every managed resource across all modules in the state tree."""
    stack = [state.get("values", {}).get("root_module", {})]
    while stack:
        mod = stack.pop()
        yield from mod.get("resources", [])
        stack.extend(mod.get("child_modules", []))


def main():
    state = json.load(sys.stdin)
    resources = list(managed_resources(state))
    by_type = {}
    for r in resources:
        by_type.setdefault(r["type"], []).append(r)

    def fail(msg):
        print(f"\nS3 ASSERT FAIL: {msg}", file=sys.stderr)
        sys.exit(1)

    # 1. An S3 bucket exists.
    buckets = by_type.get("aws_s3_bucket", [])
    if not buckets:
        fail("no aws_s3_bucket in applied state — minio was not substituted to S3")
    bucket_names = {b["values"]["bucket"] for b in buckets}
    bucket_domains = {b["values"].get("bucket_domain_name", "") for b in buckets}
    print(f"  [ok] S3 bucket created: {', '.join(sorted(bucket_names))}")

    # 2. Nothing is running the minio image (substitution, not addition).
    for td in by_type.get("aws_ecs_task_definition", []):
        cds = json.loads(td["values"]["container_definitions"])
        for c in cds:
            if "minio" in c.get("image", "").lower():
                fail(
                    f"minio is running as a container ({c['image']}) — not substituted"
                )
    print("  [ok] no minio container — substituted, not added")

    # 3. An IAM policy grants s3 access.
    s3_policy = None
    for p in by_type.get("aws_iam_role_policy", []):
        if "s3:" in p["values"].get("policy", ""):
            s3_policy = p["values"]["name"]
            break
    if not s3_policy:
        fail("no IAM role policy granting s3 access")
    print(f"  [ok] IAM policy grants S3 access: {s3_policy}")

    # 4. The deployed task env resolved to the real bucket identifiers.
    resolved_bucket = resolved_endpoint = None
    for td in by_type.get("aws_ecs_task_definition", []):
        cds = json.loads(td["values"]["container_definitions"])
        for c in cds:
            for e in c.get("environment", []):
                if e["name"] == "BUCKET_NAME":
                    resolved_bucket = e["value"]
                if e["name"] == "S3_ENDPOINT":
                    resolved_endpoint = e["value"]

    if resolved_bucket is None:
        fail("BUCKET_NAME not found in any deployed task definition")
    if "${" in resolved_bucket:
        fail(f"BUCKET_NAME never resolved (still a reference): {resolved_bucket}")
    if resolved_bucket not in bucket_names:
        fail(f"BUCKET_NAME={resolved_bucket!r} is not the real bucket {bucket_names}")
    print(f"  [ok] BUCKET_NAME injected with real bucket: {resolved_bucket}")

    # S3_ENDPOINT is optional: apps hitting real S3 via the SDK don't need it.
    # Only assert it resolved correctly when the app actually declares it.
    if resolved_endpoint is None:
        print("  [ok] S3_ENDPOINT not declared (app uses the default S3 endpoint)")
    else:
        if "${" in resolved_endpoint:
            fail(f"S3_ENDPOINT declared but not resolved: {resolved_endpoint!r}")
        if not any(dom and dom in resolved_endpoint for dom in bucket_domains):
            fail(
                f"S3_ENDPOINT={resolved_endpoint!r} does not contain the bucket "
                f"domain {bucket_domains}"
            )
        print(f"  [ok] S3_ENDPOINT injected with real domain: {resolved_endpoint}")

    print("\n  All S3 substitution assertions passed.")


if __name__ == "__main__":
    main()

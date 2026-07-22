"""composey-doctor: probes real connectivity to composey's managed services.

Each check is conditional on the env vars composey injects. If the var for a
capability is absent the check is "skipped", not failed — so the same image can
verify any environment. GET /health returns 200 only if every active check
passes, 503 otherwise. This is the source of truth for the base64 blob embedded
in compose.yml (see scripts/build_doctor.py).
"""

import os

from flask import Flask, jsonify

app = Flask(__name__)


def check_s3():
    """PUT then GET an object using the task role — proves network + IAM + wiring."""
    bucket = os.environ.get("BUCKET_NAME")
    if not bucket:
        return "skipped: BUCKET_NAME not set"
    import boto3

    s3 = boto3.client("s3")
    key = "composey-doctor/health.txt"
    payload = b"composey-doctor"
    s3.put_object(Bucket=bucket, Key=key, Body=payload)
    got = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
    if got != payload:
        raise RuntimeError("S3 round-trip mismatch")
    return f"ok: put+get on bucket {bucket}"


CHECKS = {"s3": check_s3}


@app.get("/health")
def health():
    results = {}
    ok = True
    for name, fn in CHECKS.items():
        try:
            results[name] = fn()
        except Exception as e:  # noqa: BLE001 - report any failure verbatim
            results[name] = f"FAIL: {type(e).__name__}: {e}"
            ok = False
    return jsonify({"status": "ok" if ok else "unhealthy", "checks": results}), (
        200 if ok else 503
    )


@app.get("/")
def root():
    # Kept trivially healthy so the ALB target passes while checks run on /health.
    return "composey-doctor: GET /health\n", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)

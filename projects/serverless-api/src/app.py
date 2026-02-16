import json
import os
import time
import uuid
import boto3

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["TABLE_NAME"])

ALLOWED_ORIGIN = "https://jaysoileau.com"

def _resp(code: int, body: dict):
    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        },
        "body": json.dumps(body),
    }

def handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("requestContext", {}).get("http", {}).get("path", "")

    if method == "GET" and path == "/health":
        return _resp(200, {"ok": True})

    if method == "POST" and path == "/contact":
        raw = event.get("body") or "{}"
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return _resp(400, {"error": "Invalid JSON body"})

        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()
        message = (data.get("message") or "").strip()

        if not name or not email or not message:
            return _resp(400, {"error": "name, email, and message are required"})

        # conservative length limits (avoid abuse + huge logs)
        item = {
            "id": str(uuid.uuid4()),
            "createdAt": int(time.time()),
            "name": name[:80],
            "email": email[:120],
            "message": message[:2000],
        }

        table.put_item(Item=item)
        return _resp(201, {"id": item["id"]})

    return _resp(404, {"error": "Route not found"})

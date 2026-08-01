"""Apply supabase_schema.sql to Supabase production DB via SQL endpoint."""

import httpx
import os
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SERVICE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in .env")
    exit(1)

SCHEMA_FILE = Path(__file__).resolve().parent / "supabase_schema.sql"
schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")

# Split into individual statements, skipping comments and empty blocks
statements = []
current = []
in_dollar_quote = False
dollar_tag = None

for line in schema_sql.split("\n"):
    stripped = line.strip()
    if stripped.startswith("--") and not in_dollar_quote:
        continue
    if in_dollar_quote:
        current.append(line)
        if dollar_tag and dollar_tag in stripped:
            in_dollar_quote = False
            dollar_tag = None
            combined = "\n".join(current).strip()
            if combined:
                statements.append(combined)
            current = []
        continue
    # Detect DO $$ blocks
    dm = re.match(r"(do\s+\$(\w*)\$)", stripped, re.IGNORECASE)
    if dm and "$$" in stripped:
        in_dollar_quote = True
        dollar_tag = f"${dm.group(2)}$"
        current.append(line)
        continue
    current.append(line)
    if ";" in stripped:
        combined = "\n".join(current).strip()
        if combined and not combined.startswith("--"):
            statements.append(combined)
        current = []

# Add any remaining statement
if current:
    combined = "\n".join(current).strip()
    if combined:
        statements.append(combined)

print(f"Found {len(statements)} SQL statements")

headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
}

client = httpx.Client(timeout=30)

ok_count = 0
fail_count = 0

for i, stmt in enumerate(statements):
    if not stmt:
        continue
    
    # Try the /sql REST endpoint (Supabase Studio uses this)
    try:
        r = client.post(
            f"{SUPABASE_URL}/rest/v1/sql",
            headers=headers,
            json={"query": stmt},
        )
        if r.status_code < 400:
            print(f"  [{i+1}/{len(statements)}] OK")
            ok_count += 1
        elif "already exists" in r.text.lower() or "duplicate" in r.text.lower():
            print(f"  [{i+1}/{len(statements)}] OK (already exists)")
            ok_count += 1
        elif "does not exist" in r.text.lower() and ("drop" in stmt.lower()[:20] or "if exists" in stmt.lower()):
            print(f"  [{i+1}/{len(statements)}] OK (nothing to drop)")
            ok_count += 1
        else:
            stub = stmt.replace("\n", " ")[:80]
            print(f"  [{i+1}/{len(statements)}] FAIL: {r.status_code} - {r.text[:150]}")
            print(f"     SQL: {stub}...")
            fail_count += 1
    except Exception as e:
        stub = stmt.replace("\n", " ")[:80]
        print(f"  [{i+1}/{len(statements)}] ERROR: {e}")
        print(f"     SQL: {stub}...")
        fail_count += 1

print(f"\nDone: {ok_count} OK, {fail_count} failed")
#!/usr/bin/env python3
"""Split supabase_schema.sql into smaller files for Supabase SQL Editor."""
from pathlib import Path

SCHEMA = Path(r"C:\Users\MostepAfrica\Documents\New OpenCode Project\naija-uni-admissions-mcp\supabase_schema.sql")
OUT_DIR = Path(r"C:\Users\MostepAfrica\Documents\New OpenCode Project\naija-uni-admissions-mcp\migrations")

content = SCHEMA.read_text(encoding="utf-8")
lines = content.split("\n")

def write_chunk(name, start, end):
    chunk = "\n".join(lines[start-1:end])
    (OUT_DIR / name).write_text(chunk, encoding="utf-8")
    print(f"  {name}: lines {start}-{end} ({end-start+1} lines, {len(chunk.encode('utf-8'))} bytes)")

OUT_DIR.mkdir(exist_ok=True)

print("Splitting supabase_schema.sql:")
write_chunk("10_extensions_enums.sql",  1,   53)
write_chunk("20_tables_1_to_8.sql",    54,  162)
write_chunk("30_tables_9_to_16.sql",  163,  282)
write_chunk("40_tables_17_to_24.sql", 283,  438)
write_chunk("50_indexes.sql",         439,  554)
write_chunk("60_rls_enable.sql",      555,  584)
write_chunk("70_policies_public.sql", 585,  630)
write_chunk("80_policies_service.sql",631,  680)
write_chunk("90_functions_helpers.sql",681, 710)
write_chunk("91_function_log_kv.sql", 711,  793)
write_chunk("92_triggers.sql",        794,  848)
write_chunk("99_end_comment.sql",     849, 859)

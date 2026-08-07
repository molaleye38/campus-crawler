content = open('supabase_schema.sql').read()
tables = [
    'crawl_runs', 'crawl_logs', 'institutions', 'faculties',
    'programs', 'admission_requirements', 'olevel_rules', 'utme_rules',
    'departmental_cutoffs', 'catchment', 'source_documents'
]
for t in tables:
    present = t in content.lower()
    status = "YES" if present else "NO"
    print(f"{t:30s}: {status}")

print()
print("RLS policies present:", "CREATE POLICY" in content)
print("Indexes present:", "CREATE INDEX" in content)
print("Crawl runs table full:", "CREATE TABLE IF NOT EXISTS crawl_runs" in content)

from supabase import create_client

url = 'https://fhqylwughhlxumgpsvho.supabase.co'
service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZocXlsd3VnaGhseHVtZ3BzdmhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQyMzA5NCwiZXhwIjoyMDkwOTk5MDk0fQ.l4AKzTjyYB8Aduh4_Y1pVO3U6V0YTIw1IFyCTY1J4x8'

client = create_client(url, service_key)

with open('supabase_schema.sql', 'r') as f:
    schema = f.read()

statements = [s.strip() for s in schema.split(';') if s.strip() and not s.strip().startswith('--')]

for i, stmt in enumerate(statements):
    if not stmt:
        continue
    try:
        # Try to execute via postgrest
        response = client.postgrest._session.post(
            f'{url}/rest/v1/rpc/exec_sql',
            headers={'apikey': service_key, 'Authorization': f'Bearer {service_key}', 'Content-Type': 'application/json'},
            json={'sql': stmt}
        )
        if response.status_code < 400:
            print(f'OK: Statement {i+1}')
        else:
            print(f'Note: Statement {i+1} - {response.text[:200]}')
    except Exception as e:
        print(f'Note: Statement {i+1} - {str(e)[:200]}')

print('Schema execution complete')
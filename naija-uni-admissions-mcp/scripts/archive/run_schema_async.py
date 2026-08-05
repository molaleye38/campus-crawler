import httpx
import asyncio

url = 'https://fhqylwughhlxumgpsvho.supabase.co'
service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZocXlsd3VnaGhseHVtZ3BzdmhvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NTQyMzA5NCwiZXhwIjoyMDkwOTk5MDk0fQ.l4AKzTjyYB8Aduh4_Y1pVO3U6V0YTIw1IFyCTY1J4x8'

async def run_schema():
    async with httpx.AsyncClient() as client:
        with open('supabase_schema.sql', 'r') as f:
            schema = f.read()
        
        statements = [s.strip() for s in schema.split(';') if s.strip() and not s.strip().startswith('--')]
        
        headers = {
            'apikey': service_key,
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json',
        }
        
        for i, stmt in enumerate(statements):
            if not stmt:
                continue
            try:
                response = await client.post(
                    f'{url}/rest/v1/rpc/exec_sql',
                    headers=headers,
                    json={'sql': stmt},
                    timeout=30.0
                )
                if response.status_code < 400:
                    print(f'OK: Statement {i+1}')
                else:
                    print(f'Note: Statement {i+1} - {response.text[:200]}')
            except Exception as e:
                print(f'Note: Statement {i+1} - {str(e)[:200]}')
        
        print('Schema execution complete')

asyncio.run(run_schema())
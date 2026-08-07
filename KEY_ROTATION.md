# Key Rotation Instructions (Sprint 13)

## NVIDIA API Key Rotation
1. Visit https://build.nvidia.com/
2. Go to "API Keys" section
3. Delete/revoke the exposed key: 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
4. Generate a new key
5. Update `.env`: NVIDIA_API_KEY=<new_key>
6. Restart any running crawler instances

## Supabase Service Role Key Rotation
1. Visit https://supabase.com/dashboard/project/fhqylwughhlxumgpsvho/settings/api
2. Go to "Project API keys"
3. Revoke/regenerate the service_role key
4. Update `.env`: SUPABASE_SERVICE_ROLE_KEY=<new_key>
5. Also rotate anon key if needed (public, lower risk)

## Security Notes
- `.env` is in `.gitignore` (verified: line in `.gitignore` file)
- These keys should NOT be in any GitHub commit
- The `.env` file exists locally for testing only
- After key rotation, delete the exposed keys from any logs/history

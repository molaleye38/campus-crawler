
-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to generate content hash from extracted data
create or replace function generate_content_hash(data jsonb) returns text
language sql immutable as $$
    select encode(digest(data::text, 'sha256'), 'hex');
$$;

-- Function to check if content has changed
create or replace function content_changed(inst_id uuid, url text, new_hash text) returns boolean
language plpgsql as $$
declare
    old_hash text;
begin
    select content_hash into old_hash
    from source_documents
    where institution_id = inst_id and url = $2
    order by crawled_at desc
    limit 1;
    
    if old_hash is null then
        return true; -- New URL, treat as changed
    end if;
    
    return old_hash <> new_hash;
end;
$$;
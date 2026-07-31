
-- Trigger function to log knowledge versions on insert/update
create or replace function log_knowledge_version()
returns trigger language plpgsql as $$
declare
    v_table_name text := TG_TABLE_NAME;
    v_record_id uuid;
    v_institution_id uuid;
    v_version_number integer;
    v_previous_value jsonb;
    v_new_value jsonb;
    v_changed_fields text[];
    v_source_doc_id uuid;
    v_crawl_log_id uuid;
    v_change_reason text := 'update';
begin
    -- Get the record ID
    if TG_OP = 'INSERT' then
        v_record_id := NEW.id;
        v_change_reason := 'initial_crawl';
    else
        v_record_id := OLD.id;
    end if;
    
    -- Get institution_id from the record (varies by table)
    if v_table_name = 'institutions' then
        v_institution_id := v_record_id;
    elsif v_table_name = 'courses' then
        select institution_id into v_institution_id from courses where id = v_record_id;
    elsif v_table_name = 'departmental_cutoffs' then
        select institution_id into v_institution_id from departmental_cutoffs where id = v_record_id;
    elsif v_table_name = 'admission_requirements' then
        select institution_id into v_institution_id from admission_requirements where id = v_record_id;
    elsif v_table_name = 'fees' then
        select institution_id into v_institution_id from fees where id = v_record_id;
    elsif v_table_name = 'deadlines' then
        select institution_id into v_institution_id from deadlines where id = v_record_id;
    elsif v_table_name = 'admission_news' then
        select institution_id into v_institution_id from admission_news where id = v_record_id;
    elsif v_table_name = 'source_documents' then
        select institution_id into v_institution_id from source_documents where id = v_record_id;
    else
        -- Try common column names
        execute format('select institution_id from %I where id = $1', v_table_name) into v_institution_id using v_record_id;
    end if;
    
    -- Get next version number
    select coalesce(max(version_number), 0) + 1 into v_version_number
    from knowledge_versions
    where table_name = v_table_name and record_id = v_record_id;
    
    -- Build previous and new values
    if TG_OP = 'INSERT' then
        v_previous_value := '{}'::jsonb;
        v_new_value := to_jsonb(NEW);
        v_changed_fields := array(select jsonb_object_keys(to_jsonb(NEW)));
    elsif TG_OP = 'UPDATE' then
        v_previous_value := to_jsonb(OLD);
        v_new_value := to_jsonb(NEW);
        v_changed_fields := array(
            select key from jsonb_each_text(to_jsonb(NEW))
            where value <> (to_jsonb(OLD) ->> key)
        );
    else
        v_previous_value := to_jsonb(OLD);
        v_new_value := '{}'::jsonb;
        v_changed_fields := array(select jsonb_object_keys(to_jsonb(OLD)));
    end if;
    
    -- Insert knowledge version
    insert into knowledge_versions (
        table_name, record_id, institution_id, version_number,
        effective_date, previous_value, new_value, changed_fields,
        source_document_id, crawl_log_id, change_reason
    ) values (
        v_table_name, v_record_id, v_institution_id, v_version_number,
        now(), v_previous_value, v_new_value, v_changed_fields,
        v_source_doc_id, v_crawl_log_id, v_change_reason
    );
    
    return NEW;
end;
$$;
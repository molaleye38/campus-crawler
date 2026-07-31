
-- Attach versioning triggers to key tables
drop trigger if exists trigger_kv_institutions on institutions;
create trigger trigger_kv_institutions
    after insert or update or delete on institutions
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_courses on courses;
create trigger trigger_kv_courses
    after insert or update or delete on courses
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_cutoffs on departmental_cutoffs;
create trigger trigger_kv_cutoffs
    after insert or update or delete on departmental_cutoffs
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_adm_req on admission_requirements;
create trigger trigger_kv_adm_req
    after insert or update or delete on admission_requirements
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_fees on fees;
create trigger trigger_kv_fees
    after insert or update or delete on fees
    for each row execute function log_knowledge_version();

drop trigger if exists trigger_kv_deadlines on deadlines;
create trigger trigger_kv_deadlines
    after insert or update or delete on deadlines
    for each row execute function log_knowledge_version();

-- Auto-update updated_at on admission_requirements, post_utme, aggregate_formulas
create or replace function update_timestamp()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trigger_update_adm_req_timestamp on admission_requirements;
create trigger trigger_update_adm_req_timestamp
    before update on admission_requirements
    for each row execute function update_timestamp();

drop trigger if exists trigger_update_postutme_timestamp on post_utme;
create trigger trigger_update_postutme_timestamp
    before update on post_utme
    for each row execute function update_timestamp();

drop trigger if exists trigger_update_agg_formula_timestamp on aggregate_formulas;
create trigger trigger_update_agg_formula_timestamp
    before update on aggregate_formulas
    for each row execute function update_timestamp();
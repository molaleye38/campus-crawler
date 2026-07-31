
-- ============================================================================
-- INDEXES
-- ============================================================================

-- Institutions
create index if not exists idx_institutions_type on institutions(institution_type);
create index if not exists idx_institutions_state on institutions(state);
create index if not exists idx_institutions_name on institutions(name);
create index if not exists idx_institutions_jamb_code on institutions(jamb_code);

-- Faculties
create index if not exists idx_faculties_inst on faculties(institution_id);

-- Departments
create index if not exists idx_departments_fac on departments(faculty_id);
create index if not exists idx_departments_inst on departments(institution_id);

-- Courses
create index if not exists idx_courses_inst on courses(institution_id);
create index if not exists idx_courses_dept on courses(department_id);
create index if not exists idx_courses_fac on courses(faculty_id);
create index if not exists idx_courses_name on courses(name);

-- Course aliases
create index if not exists idx_course_aliases_canonical on course_aliases(canonical_course_id);
create index if not exists idx_course_aliases_alias on course_aliases(alias);

-- Subjects
create index if not exists idx_subjects_name on subjects(name);
create index if not exists idx_subjects_code on subjects(code);

-- Subject aliases
create index if not exists idx_subject_aliases_canonical on subject_aliases(canonical_subject_id);
create index if not exists idx_subject_aliases_alias on subject_aliases(alias);

-- Admission Requirements
create index if not exists idx_adm_req_inst on admission_requirements(institution_id);
create index if not exists idx_adm_req_course on admission_requirements(course_id);

-- O-Level Requirements
create index if not exists idx_olevel_adm_req on olevel_requirements(admission_requirement_id);
create index if not exists idx_olevel_subject on olevel_requirements(subject_id);

-- UTME Requirements
create index if not exists idx_utme_adm_req on utme_requirements(admission_requirement_id);
create index if not exists idx_utme_subject on utme_requirements(subject_id);

-- Direct Entry
create index if not exists idx_de_adm_req on direct_entry(admission_requirement_id);

-- Post-UTME
create index if not exists idx_postutme_adm_req on post_utme(admission_requirement_id);

-- Aggregate Formulas
create index if not exists idx_agg_form_inst on aggregate_formulas(institution_id);
create index if not exists idx_agg_form_course on aggregate_formulas(course_id);
create index if not exists idx_agg_form_session on aggregate_formulas(effective_from);

-- Departmental Cutoffs
create index if not exists idx_cutoffs_inst on departmental_cutoffs(institution_id);
create index if not exists idx_cutoffs_course on departmental_cutoffs(course_id);
create index if not exists idx_cutoffs_session on departmental_cutoffs(academic_session);

-- Catchment
create index if not exists idx_catchment_inst on catchment(institution_id);

-- ELDS
create index if not exists idx_elds_session on elds(jamb_session);

-- Fees
create index if not exists idx_fees_inst on fees(institution_id);
create index if not exists idx_fees_course on fees(course_id);
create index if not exists idx_fees_session on fees(academic_session);
create index if not exists idx_fees_category on fees(fee_category);

-- Deadlines
create index if not exists idx_deadlines_inst on deadlines(institution_id);
create index if not exists idx_deadlines_course on deadlines(course_id);
create index if not exists idx_deadlines_type on deadlines(deadline_type);
create index if not exists idx_deadlines_session on deadlines(academic_session);
create index if not exists idx_deadlines_date on deadlines(deadline_date);

-- Admission News
create index if not exists idx_news_inst on admission_news(institution_id);
create index if not exists idx_news_category on admission_news(news_category);
create index if not exists idx_news_published on admission_news(published_date desc);
create index if not exists idx_news_hash on admission_news(content_hash);

-- Source Documents
create index if not exists idx_src_doc_inst on source_documents(institution_id);
create index if not exists idx_src_doc_course on source_documents(course_id);
create index if not exists idx_src_doc_hash on source_documents(content_hash);
create index if not exists idx_src_doc_session on source_documents(academic_session);
create index if not exists idx_src_doc_storage on source_documents(storage_path);

-- Crawl Logs
create index if not exists idx_crawl_logs_inst on crawl_logs(institution_id);
create index if not exists idx_crawl_logs_course on crawl_logs(course_id);
create index if not exists idx_crawl_logs_name on crawl_logs(institution_name);
create index if not exists idx_crawl_logs_status on crawl_logs(status);
create index if not exists idx_crawl_logs_crawled on crawl_logs(crawled_at desc);

-- Knowledge Versions
create index if not exists idx_kv_table_record on knowledge_versions(table_name, record_id);
create index if not exists idx_kv_inst on knowledge_versions(institution_id);
create index if not exists idx_kv_created on knowledge_versions(created_at desc);
create index if not exists idx_kv_version on knowledge_versions(version_number);

-- Staging
create index if not exists idx_raw_crawl_status on raw_crawl_data(status);
create index if not exists idx_raw_crawl_hash on raw_crawl_data(content_hash);
create index if not exists idx_raw_crawl_inst on raw_crawl_data(institution_id);
create index if not exists idx_validated_raw on validated_data(raw_crawl_id);
create index if not exists idx_validated_status on validated_data(status);
create index if not exists idx_validated_inst on validated_data(institution_id);
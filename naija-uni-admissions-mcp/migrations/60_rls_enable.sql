
-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
alter table institutions enable row level security;
alter table faculties enable row level security;
alter table departments enable row level security;
alter table courses enable row level security;
alter table course_aliases enable row level security;
alter table subjects enable row level security;
alter table subject_aliases enable row level security;
alter table admission_requirements enable row level security;
alter table olevel_requirements enable row level security;
alter table utme_requirements enable row level security;
alter table direct_entry enable row level security;
alter table post_utme enable row level security;
alter table aggregate_formulas enable row level security;
alter table departmental_cutoffs enable row level security;
alter table catchment enable row level security;
alter table elds enable row level security;
alter table fees enable row level security;
alter table deadlines enable row level security;
alter table admission_news enable row level security;
alter table source_documents enable row level security;
alter table crawl_logs enable row level security;
alter table knowledge_versions enable row level security;
alter table raw_crawl_data enable row level security;
alter table validated_data enable row level security;
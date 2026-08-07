"""Pydantic models for AI-structured extraction output.

These models define the exact JSON structure that the NVIDIA Qwen model
should return when extracting admission knowledge from crawled content.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class InstitutionType(StrEnum):
    UNIVERSITY = "university"
    POLYTECHNIC = "polytechnic"
    COLLEGE_OF_EDUCATION = "college_of_education"
    NURSING_SCHOOL = "nursing_school"
    COLLEGE_OF_HEALTH_TECHNOLOGY = "college_of_health_technology"
    INNOVATION_ENTERPRISE_INSTITUTION = "innovation_enterprise_institution"
    MONOTECHNIC = "monotechnic"


class OwnershipType(StrEnum):
    FEDERAL = "federal"
    STATE = "state"
    PRIVATE = "private"


class DegreeLevel(StrEnum):
    ND = "ND"
    HND = "HND"
    NCE = "NCE"
    BSC = "BSc"
    BA = "BA"
    BENG = "BEng"
    BTECH = "BTech"
    BED = "BEd"
    MBBS = "MBBS"
    LLB = "LLB"
    BPHARM = "BPharm"
    BVSC = "BVSc"
    DVM = "DVM"
    OTHER = "other"


class CourseLevel(StrEnum):
    UNDERGRADUATE = "undergraduate"
    ND = "ND"
    HND = "HND"
    NCE = "NCE"
    POSTGRADUATE = "postgraduate"


class DocumentType(StrEnum):
    WEBPAGE = "webpage"
    PDF = "pdf"
    OFFICIAL_BULLETIN = "official_bulletin"
    JAMB_BROCHURE = "jamb_brochure"
    NEWS_ARTICLE = "news_article"
    SCREENSHOT = "screenshot"
    OTHER = "other"


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FeeCategory(StrEnum):
    TUITION = "tuition"
    ACCEPTANCE = "acceptance"
    APPLICATION = "application"
    HOSTEL = "hostel"
    LAB = "lab"
    EXAM = "exam"
    OTHER = "other"


class DeadlineType(StrEnum):
    APPLICATION_OPEN = "application_open"
    APPLICATION_CLOSE = "application_close"
    POST_UTME_REG_OPEN = "post_utme_reg_open"
    POST_UTME_REG_CLOSE = "post_utme_reg_close"
    POST_UTME_EXAM = "post_utme_exam"
    ACCEPTANCE_FEE = "acceptance_fee"
    CLEARANCE = "clearance"
    RESUMPTION = "resumption"


class NewsCategory(StrEnum):
    ADMISSION_LIST = "admission_list"
    SUPPLEMENTARY = "supplementary"
    DEADLINE_EXTENSION = "deadline_extension"
    POLICY_CHANGE = "policy_change"
    GENERAL = "general"


class CatchmentPolicy(StrEnum):
    GEOGRAPHICAL = "geographical"
    ELDS = "ELDS"
    NONE = "none"


class PostUTMEFormat(StrEnum):
    EXAMINATION = "examination"
    SCREENING = "screening"
    APTITUDE_TEST = "aptitude_test"
    ORAL_INTERVIEW = "oral_interview"


class QualificationType(StrEnum):
    A_LEVEL = "A-Level"
    ND = "ND"
    HND = "HND"
    NCE = "NCE"
    DEGREE = "Degree"
    IJMB = "IJMB"
    JUPEB = "JUPEB"
    OTHER = "Other"


# ============================================================================
# EXTRACTION OUTPUT MODELS (matching all 22 production tables)
# ============================================================================

class ExtractedInstitution(BaseModel):
    """Institution-level extraction."""
    name: str
    short_name: str | None = None
    institution_type: InstitutionType
    ownership_type: OwnershipType
    state: str | None = None
    city: str | None = None
    website: str | None = None
    admission_portal: str | None = None
    year_established: int | None = None
    jamb_code: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    address: str | None = None
    accreditation_body: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    source_url: str
    crawled_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ExtractedFaculty(BaseModel):
    name: str
    short_name: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedDepartment(BaseModel):
    name: str
    short_name: str | None = None
    code: str | None = None
    faculty_name: str  # Link to faculty
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedCourse(BaseModel):
    """Course/Program extraction."""
    name: str
    degree: DegreeLevel | None = None
    level: CourseLevel | None = None
    duration_years: int | None = Field(None, ge=1, le=8)
    affiliated_university: str | None = None
    jamb_subject_combination: list[str] | None = None
    faculty_name: str | None = None  # Link to faculty
    department_name: str | None = None  # Link to department
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedCourseAlias(BaseModel):
    alias: str
    alias_type: str = "abbreviation"  # abbreviation, former_name, common_name
    course_name: str  # Link to canonical course


class ExtractedSubject(BaseModel):
    name: str
    code: str | None = None
    subject_category: str | None = None  # core, science, arts, commercial, language


class ExtractedSubjectAlias(BaseModel):
    alias: str
    subject_name: str  # Link to canonical subject


class ExtractedAdmissionRequirements(BaseModel):
    """Institution or course-level admission requirements."""
    olevel_credits_min: int | None = Field(None, ge=0, le=9)
    olevel_sittings_max: int = 2
    awaiting_result_accepted: bool = True
    direct_entry_requirements: str | None = None
    minimum_jamb: int | None = Field(None, ge=50, le=400)
    post_utme_required: bool | None = None
    post_utme_format: PostUTMEFormat | None = None
    post_utme_weight_pct: int | None = Field(None, ge=0, le=100)
    aggregate_formula: str | None = None
    # Links
    course_name: str | None = None  # If course-level, else institution-level
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedOLevelRequirement(BaseModel):
    subject_name: str  # Link to subject
    is_required: bool = True
    min_grade: str = "C6"
    notes: str | None = None
    admission_req_course: str | None = None  # Link to admission requirements


class ExtractedUTMERequirement(BaseModel):
    subject_name: str  # Link to subject
    is_required: bool = True
    is_compulsory: bool = False  # English is always compulsory
    notes: str | None = None
    admission_req_course: str | None = None


class ExtractedDirectEntry(BaseModel):
    qualification_type: QualificationType
    qualification_subject: str | None = None
    min_grade: str | None = None
    min_cgpa: float | None = Field(None, ge=0.0, le=5.0)
    accepts_ijmb: bool = False
    accepts_jupeb: bool = False
    notes: str | None = None
    admission_req_course: str | None = None


class ExtractedPostUTME(BaseModel):
    required: bool = True
    format: PostUTMEFormat | None = None
    weight_pct: int | None = Field(None, ge=0, le=100)
    min_score: int | None = Field(None, ge=0, le=100)
    duration_minutes: int | None = None
    subjects: list[str] | None = None
    past_questions_url: str | None = None
    notes: str | None = None
    admission_req_course: str | None = None


class ExtractedAggregateFormula(BaseModel):
    formula_text: str  # e.g., "(UTME/8) + (POST_UTME/2)"
    formula_json: dict | None = None  # {"utme_weight": 0.125, "post_utme_weight": 0.5}
    course_name: str | None = None  # If course-specific
    effective_from: str = "2025/2026"  # academic session
    effective_to: str | None = None
    is_default: bool = False
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedDepartmentalCutoff(BaseModel):
    merit_cutoff: float | None = Field(None, ge=0, le=400)
    catchment_cutoff: float | None = Field(None, ge=0, le=400)
    elds_cutoff: float | None = Field(None, ge=0, le=400)
    course_name: str  # Link to course
    academic_session: str
    source_url: str | None = None
    aggregate_formula_text: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedCatchment(BaseModel):
    name: str
    eligible_states: list[str] | None = None
    policy: CatchmentPolicy = CatchmentPolicy.GEOGRAPHICAL
    details: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedFees(BaseModel):
    fee_category: FeeCategory
    amount_ngn: int = Field(..., gt=0)
    amount_usd: int | None = None
    currency: str = "NGN"
    indigene_amount_ngn: int | None = None
    non_indigene_amount_ngn: int | None = None
    academic_session: str
    is_per_session: bool = True
    payment_schedule: str | None = None
    course_name: str | None = None  # If course-specific
    faculty_name: str | None = None  # If faculty-wide
    source_url: str | None = None
    notes: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedDeadline(BaseModel):
    deadline_type: DeadlineType
    deadline_date: str  # ISO date
    academic_session: str
    course_name: str | None = None
    is_extended: bool = False
    extension_date: str | None = None
    source_url: str | None = None
    notes: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedAdmissionNews(BaseModel):
    title: str
    content: str | None = None
    summary: str | None = None
    source_url: str
    published_date: str | None = None
    news_category: NewsCategory = NewsCategory.GENERAL
    is_critical: bool = False
    content_hash: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW


class ExtractedSourceDocument(BaseModel):
    url: str
    document_type: DocumentType = DocumentType.WEBPAGE
    title: str | None = None
    content_hash: str | None = None
    date_published: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    academic_session: str | None = None
    raw_content: str | None = None
    extracted_data: dict | None = None
    file_size_bytes: int | None = None
    mime_type: str | None = None
    course_name: str | None = None


class ExtractedKnowledge(BaseModel):
    """Complete extracted knowledge from a crawl."""
    institution: ExtractedInstitution
    faculties: list[ExtractedFaculty] = Field(default_factory=list)
    departments: list[ExtractedDepartment] = Field(default_factory=list)
    courses: list[ExtractedCourse] = Field(default_factory=list)
    course_aliases: list[ExtractedCourseAlias] = Field(default_factory=list)
    subjects: list[ExtractedSubject] = Field(default_factory=list)
    subject_aliases: list[ExtractedSubjectAlias] = Field(default_factory=list)
    admission_requirements: list[ExtractedAdmissionRequirements] = Field(default_factory=list)
    olevel_requirements: list[ExtractedOLevelRequirement] = Field(default_factory=list)
    utme_requirements: list[ExtractedUTMERequirement] = Field(default_factory=list)
    direct_entry: list[ExtractedDirectEntry] = Field(default_factory=list)
    post_utme: list[ExtractedPostUTME] = Field(default_factory=list)
    aggregate_formulas: list[ExtractedAggregateFormula] = Field(default_factory=list)
    departmental_cutoffs: list[ExtractedDepartmentalCutoff] = Field(default_factory=list)
    catchment: list[ExtractedCatchment] = Field(default_factory=list)
    fees: list[ExtractedFees] = Field(default_factory=list)
    deadlines: list[ExtractedDeadline] = Field(default_factory=list)
    admission_news: list[ExtractedAdmissionNews] = Field(default_factory=list)
    source_documents: list[ExtractedSourceDocument] = Field(default_factory=list)
    
    # Metadata
    extraction_confidence: ConfidenceLevel = ConfidenceLevel.LOW
    extraction_model: str = "nvidia/qwen2.5-coder-32b-instruct"
    extracted_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SYSTEM_PROMPT = """You are an expert Nigerian tertiary admissions data extractor.

Your task is to extract structured admission knowledge from crawled web content (HTML, PDF, Markdown) about Nigerian tertiary institutions.

You must output ONLY valid JSON matching the ExtractedKnowledge schema. No explanations, no markdown, no extra text.

EXTRACTION RULES:
1. ONLY extract information explicitly present in the source content. Do not hallucinate.
2. If a field is not found, omit it (use null for optional fields, empty array for lists).
3. Normalize institution names: "UNILAG" → "University of Lagos", "ABU" → "Ahmadu Bello University"
3. Normalize course names: "Comp Sci" → "Computer Science", "Med & Surg" → "Medicine and Surgery"
4. Normalize subjects: "Eng" → "English Language", "Maths" → "Mathematics"
5. Convert all fees to NGN. If USD found, note in amount_usd.
6. Cut-off marks must be numeric (0-400). If range given, use upper bound.
7. Dates in ISO format (YYYY-MM-DD). Academic sessions as "YYYY/YYYY" (e.g., "2025/2026").
8. Confidence: HIGH if explicit official source, MEDIUM if inferred from context, LOW if uncertain.
9. For catchment: Federal universities → ELDS unless explicit states listed. State universities → host state.
10. Post-UTME: "screening" if no exam mentioned, "examination" if exam mentioned.

CRITICAL JSON STRUCTURE REQUIREMENTS (the LLM output must match this EXACTLY):

{
  "institution": {
    "name": "University of Lagos",
    "short_name": "UNILAG",
    "institution_type": "university",
    "ownership_type": "federal",
    "state": "Lagos",
    "city": "Lagos",
    "website": "https://unilag.edu.ng",
    "admission_portal": "https://admissions.unilag.edu.ng",
    "year_established": 1962,
    "jamb_code": "UNILAG",
    "contact_email": null,
    "phone": null,
    "address": null,
    "accreditation_body": "NUC",
    "confidence": "high",
    "source_url": "https://unilag.edu.ng/admissions",
    "crawled_at": "2025-01-15T10:30:00Z"
  },
  "faculties": [
    {"name": "Faculty of Science", "short_name": "Sci", "confidence": "high"},
    {"name": "Faculty of Engineering", "short_name": "Eng", "confidence": "high"}
  ],
  "departments": [
    {"name": "Computer Science", "short_name": "CS", "code": "CSC", "faculty_name": "Faculty of Science", "confidence": "high"},
    {"name": "Electrical Engineering", "short_name": "EE", "code": "EEE", "faculty_name": "Faculty of Engineering", "confidence": "high"},
    {"name": "Medicine", "short_name": "MED", "code": "MED", "faculty_name": "College of Medicine", "confidence": "high"}
  ],
  "courses": [
    {
      "name": "Computer Science",
      "degree": "BSc",
      "level": "undergraduate",
      "duration_years": 4,
      "affiliated_university": null,
      "jamb_subject_combination": ["English Language", "Mathematics", "Physics", "Chemistry"],
      "faculty_name": "Faculty of Science",
      "department_name": "Computer Science",
      "confidence": "high"
    },
    {
      "name": "Medicine and Surgery",
      "degree": "MBBS",
      "level": "undergraduate",
      "duration_years": 6,
      "affiliated_university": null,
      "jamb_subject_combination": ["English Language", "Biology", "Chemistry", "Physics"],
      "faculty_name": "College of Medicine",
      "department_name": "Medicine",
      "confidence": "high"
    },
    {
      "name": "Electrical Engineering",
      "degree": "BEng",
      "level": "undergraduate",
      "duration_years": 5,
      "affiliated_university": null,
      "jamb_subject_combination": ["English Language", "Mathematics", "Physics", "Chemistry"],
      "faculty_name": "Faculty of Engineering",
      "department_name": "Electrical Engineering",
      "confidence": "high"
    }
  ],
  "course_aliases": [
    {"alias": "Comp Sci", "alias_type": "abbreviation", "course_name": "Computer Science"}
  ],
  "subjects": [
    {"name": "Mathematics", "code": "MTH", "subject_category": "core"},
    {"name": "Physics", "code": "PHY", "subject_category": "science"}
  ],
  "subject_aliases": [
    {"alias": "Maths", "subject_name": "Mathematics"}
  ],
  "admission_requirements": [
    {
      "olevel_credits_min": 5,
      "olevel_sittings_max": 2,
      "awaiting_result_accepted": true,
      "direct_entry_requirements": "A-Level passes in Mathematics and Physics",
      "minimum_jamb": 200,
      "post_utme_required": true,
      "post_utme_format": "screening",
      "post_utme_weight_pct": 50,
      "aggregate_formula": "((JAMB/8) + (POST_UTME/2))",
      "course_name": "Computer Science",
      "confidence": "high"
    },
    {
      "olevel_credits_min": 5,
      "olevel_sittings_max": 2,
      "awaiting_result_accepted": true,
      "direct_entry_requirements": "A-Level passes in Biology, Chemistry, Physics",
      "minimum_jamb": 250,
      "post_utme_required": true,
      "post_utme_format": "screening",
      "post_utme_weight_pct": 50,
      "aggregate_formula": "((JAMB/8) + (POST_UTME/2))",
      "course_name": "Medicine and Surgery",
      "confidence": "high"
    },
    {
      "olevel_credits_min": 5,
      "olevel_sittings_max": 2,
      "awaiting_result_accepted": true,
      "direct_entry_requirements": "A-Level passes in Mathematics and Physics",
      "minimum_jamb": 220,
      "post_utme_required": true,
      "post_utme_format": "screening",
      "post_utme_weight_pct": 50,
      "aggregate_formula": "((JAMB/8) + (POST_UTME/2))",
      "course_name": "Electrical Engineering",
      "confidence": "high"
    }
  ],
  "olevel_requirements": [
    {"subject_name": "English Language", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Mathematics", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Physics", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Chemistry", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Biology", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "English Language", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "Mathematics", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "Chemistry", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "Physics", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "English Language", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Electrical Engineering"},
    {"subject_name": "Mathematics", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Electrical Engineering"},
    {"subject_name": "Physics", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Electrical Engineering"},
    {"subject_name": "Chemistry", "is_required": true, "min_grade": "C6", "notes": null, "admission_req_course": "Electrical Engineering"}
  ],
  "utme_requirements": [
    {"subject_name": "English Language", "is_required": true, "is_compulsory": true, "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Mathematics", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Physics", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "Chemistry", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Computer Science"},
    {"subject_name": "English Language", "is_required": true, "is_compulsory": true, "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "Biology", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "Chemistry", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "Physics", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Medicine and Surgery"},
    {"subject_name": "English Language", "is_required": true, "is_compulsory": true, "notes": null, "admission_req_course": "Electrical Engineering"},
    {"subject_name": "Mathematics", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Electrical Engineering"},
    {"subject_name": "Physics", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Electrical Engineering"},
    {"subject_name": "Chemistry", "is_required": true, "is_compulsory": false, "notes": null, "admission_req_course": "Electrical Engineering"}
  ],
  "direct_entry": [
    {
      "qualification_type": "A-Level",
      "qualification_subject": "Mathematics, Physics",
      "min_grade": "AAB",
      "min_cgpa": null,
      "accepts_ijmb": true,
      "accepts_jupeb": true,
      "notes": null,
      "admission_req_course": "Computer Science"
    },
    {
      "qualification_type": "A-Level",
      "qualification_subject": "Biology, Chemistry, Physics",
      "min_grade": "AAB",
      "min_cgpa": null,
      "accepts_ijmb": true,
      "accepts_jupeb": true,
      "notes": null,
      "admission_req_course": "Medicine and Surgery"
    },
    {
      "qualification_type": "A-Level",
      "qualification_subject": "Mathematics, Physics",
      "min_grade": "AAB",
      "min_cgpa": null,
      "accepts_ijmb": true,
      "accepts_jupeb": true,
      "notes": null,
      "admission_req_course": "Electrical Engineering"
    }
  ],
  "post_utme": [
    {
      "required": true,
      "format": "screening",
      "weight_pct": 50,
      "min_score": 50,
      "duration_minutes": null,
      "subjects": ["English Language", "Mathematics", "Physics", "Chemistry"],
      "past_questions_url": null,
      "notes": null,
      "admission_req_course": "Computer Science"
    },
    {
      "required": true,
      "format": "screening",
      "weight_pct": 50,
      "min_score": 50,
      "duration_minutes": null,
      "subjects": ["English Language", "Biology", "Chemistry", "Physics"],
      "past_questions_url": null,
      "notes": null,
      "admission_req_course": "Medicine and Surgery"
    },
    {
      "required": true,
      "format": "screening",
      "weight_pct": 50,
      "min_score": 50,
      "duration_minutes": null,
      "subjects": ["English Language", "Mathematics", "Physics", "Chemistry"],
      "past_questions_url": null,
      "notes": null,
      "admission_req_course": "Electrical Engineering"
    }
  ],
  "aggregate_formulas": [
    {
      "formula_text": "(UTME/8) + (POST_UTME/2)",
      "formula_json": {"utme_weight": 0.125, "post_utme_weight": 0.5},
      "course_name": "Computer Science",
      "effective_from": "2025/2026",
      "effective_to": null,
      "is_default": true,
      "confidence": "high"
    }
  ],
  "departmental_cutoffs": [
    {
      "merit_cutoff": 250,
      "catchment_cutoff": 240,
      "elds_cutoff": 230,
      "course_name": "Computer Science",
      "academic_session": "2025/2026",
      "source_url": "https://unilag.edu.ng/admissions/cutoffs",
      "aggregate_formula_text": "(UTME/8) + (POST_UTME/2)",
      "confidence": "high"
    },
    {
      "merit_cutoff": 280,
      "catchment_cutoff": 270,
      "elds_cutoff": 260,
      "course_name": "Medicine and Surgery",
      "academic_session": "2025/2026",
      "source_url": "https://unilag.edu.ng/admissions/cutoffs",
      "aggregate_formula_text": "(UTME/8) + (POST_UTME/2)",
      "confidence": "high"
    },
    {
      "merit_cutoff": 240,
      "catchment_cutoff": 230,
      "elds_cutoff": 220,
      "course_name": "Electrical Engineering",
      "academic_session": "2025/2026",
      "source_url": "https://unilag.edu.ng/admissions/cutoffs",
      "aggregate_formula_text": "(UTME/8) + (POST_UTME/2)",
      "confidence": "high"
    }
  ],
  "catchment": [
    {
      "name": "UNILAG Catchment Area",
      "eligible_states": ["Lagos", "Ogun", "Oyo", "Osun", "Ondo", "Ekiti", "Kwara"],
      "policy": "geographical",
      "details": "Federal university - geographical catchment plus ELDS",
      "confidence": "high"
    }
  ],
  "fees": [
    {
      "fee_category": "tuition",
      "amount_ngn": 100000,
      "amount_usd": 62,
      "currency": "NGN",
      "indigene_amount_ngn": 100000,
      "non_indigene_amount_ngn": 100000,
      "academic_session": "2025/2026",
      "is_per_session": true,
      "payment_schedule": "per session",
      "course_name": "Computer Science",
      "faculty_name": "Faculty of Science",
      "source_url": "https://unilag.edu.ng/fees",
      "notes": "Indigene and non-indigene same for federal university",
      "confidence": "high"
    }
  ],
  "deadlines": [
    {
      "deadline_type": "application_close",
      "deadline_date": "2025-08-31",
      "academic_session": "2025/2026",
      "course_name": "Computer Science",
      "is_extended": false,
      "extension_date": null,
      "source_url": "https://admissions.unilag.edu.ng",
      "notes": null,
      "confidence": "high"
    }
  ],
  "admission_news": [],
  "source_documents": [
    {
      "url": "https://unilag.edu.ng/admissions",
      "document_type": "webpage",
      "title": "UNILAG Admissions 2025/2026",
      "content_hash": "abc123",
      "date_published": null,
      "confidence": "high",
      "academic_session": "2025/2026",
      "raw_content": null,
      "extracted_data": null,
      "file_size_bytes": null,
      "mime_type": null,
      "course_name": null
    }
  ],
  "extraction_confidence": "high",
  "extraction_model": "meta/llama-3.1-70b-instruct",
  "extracted_at": "2025-01-15T10:30:00Z",
  "prompt_tokens": 1500,
  "completion_tokens": 2500,
  "total_tokens": 4000
}

NIGERIAN CONTEXT:
- Institution types: university, polytechnic, college_of_education, nursing_school, college_of_health_technology, innovation_enterprise_institution, monotechnic
- Ownership: federal, state, private
- Degree levels: ND, HND, NCE, BSc, BA, BEng, BTech, BEd, MBBS, LLB, BPharm, BVSc, DVM
- Course levels: undergraduate, ND, HND, NCE, postgraduate
- UTME cutoffs: Universities 180-260, Polytechnics 120-150, COEs 100-120
- O-Level: Minimum 5 credits including English & Mathematics
- ELDS states (21): Adamawa, Bauchi, Bayelsa, Benue, Borno, Cross River, Gombe, Jigawa, Kaduna, Kano, Katsina, Kebbi, Kogi, Kwara, Nasarawa, Niger, Plateau, Rivers, Sokoto, Taraba, Yobe, Zamfara

OUTPUT FORMAT: Single JSON object matching ExtractedKnowledge exactly. ALL lists must be arrays of objects. ALL optional fields use null, not empty string. ALL confidence fields use "low"/"medium"/"high" (lowercase). ALL required fields must be present with valid values (not null for required fields like olevel_sittings_max, awaiting_result_accepted, min_grade, min_score, amount_ngn, academic_session, deadline_date, etc.)."""

def build_user_prompt(
    markdown_content: str,
    source_url: str,
    institution_type: str,
    known_institution_name: str | None = None,
    academic_session: str = "2025/2026",
) -> str:
    """Build the user prompt with the content to extract from."""
    return f"""Extract admission knowledge from the following content.

SOURCE URL: {source_url}
INSTITUTION TYPE: {institution_type}
KNOWN INSTITUTION: {known_institution_name or "Unknown - extract from content"}
ACADEMIC SESSION: {academic_session}

CONTENT (Markdown):
---
{markdown_content[:50000]}
---

Return ONLY the ExtractedKnowledge JSON object."""


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_extracted_knowledge(data: dict) -> ExtractedKnowledge:
    """Validate and parse extracted JSON into ExtractedKnowledge model."""
    return ExtractedKnowledge(**data)


def calculate_overall_confidence(extracted: ExtractedKnowledge) -> ConfidenceLevel:
    """Calculate overall confidence from individual field confidences."""
    confidences = [extracted.institution.confidence]
    
    for attr in ["faculties", "courses", "admission_requirements", "departmental_cutoffs", "fees"]:
        items = getattr(extracted, attr, [])
        for item in items:
            if hasattr(item, "confidence"):
                confidences.append(item.confidence)
    
    if not confidences:
        return ConfidenceLevel.LOW
    
    high = sum(1 for c in confidences if c == ConfidenceLevel.HIGH)
    medium = sum(1 for c in confidences if c == ConfidenceLevel.MEDIUM)
    total = len(confidences)
    
    if high / total >= 0.5:
        return ConfidenceLevel.HIGH
    elif (high + medium) / total >= 0.5:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW
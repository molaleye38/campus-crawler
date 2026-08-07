"""NVIDIA NIM / Qwen AI Extractor for CKAP.

Uses NVIDIA's hosted Qwen model for structured extraction of admission knowledge.
"""

from __future__ import annotations

import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from .extraction_models import (
    SYSTEM_PROMPT,
    ExtractedKnowledge,
    build_user_prompt,
    calculate_overall_confidence,
    validate_extracted_knowledge,
)
from .utils import safe_log


class NVIDIAExtractor:
    """Async client for NVIDIA NIM API (Qwen) for structured extraction."""
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: int = 180,
        max_retries: int = 3,
    ):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        self.base_url = (base_url or os.getenv("NVIDIA_NIM_URL", "https://integrate.api.nvidia.com/v1")).rstrip("/")
        # Default to a large, high-quality model that supports JSON mode.
        # Override via QWEN_MODEL env var.
        self.model = model or os.getenv("QWEN_MODEL", "meta/llama-3.1-70b-instruct")
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            raise RuntimeError(
                "NVIDIA API key not provided. Set NVIDIA_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> NVIDIAExtractor:
        await self.start()
        return self
    
    async def __aexit__(self, *exc) -> None:
        await self.aclose()
    
    async def start(self) -> None:
        """Initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(connect=10.0, read=self.timeout, write=30.0, pool=30.0),
            )
    
    async def aclose(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def extract(
        self,
        markdown_content: str,
        source_url: str,
        institution_type: str,
        known_institution_name: str | None = None,
        academic_session: str = "2025/2026",
    ) -> ExtractedKnowledge:
        """Extract structured admission knowledge from markdown content."""
        if self._client is None:
            await self.start()
        
        user_prompt = build_user_prompt(
            markdown_content=markdown_content,
            source_url=source_url,
            institution_type=institution_type,
            known_institution_name=known_institution_name,
            academic_session=academic_session,
        )
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.post(
                    "/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.1,
                        "top_p": 0.9,
                        "max_tokens": 8192,
                        "response_format": {"type": "json_object"},
                    },
                )
                
                if response.status_code == 429:
                    wait = min(60, 2 ** attempt * 5)
                    safe_log("nim_rate_limited", attempt=attempt + 1, wait=wait)
                    await asyncio.sleep(wait)
                    continue
                elif response.status_code == 400:
                    # Some models don't support response_format: json_object.
                    # Retry without it.
                    body = response.text.lower()
                    if "response_format" in body or "json_object" in body or "json_schema" in body:
                        safe_log("nim_response_format_unsupported", attempt=attempt + 1)
                        response = await self._client.post(
                            "/chat/completions",
                            json={
                                "model": self.model,
                                "messages": messages,
                                "temperature": 0.1,
                                "top_p": 0.9,
                                "max_tokens": 8192,
                            },
                        )
                    else:
                        response.raise_for_status()
                
                response.raise_for_status()
                result = response.json()

                content = result["choices"][0]["message"]["content"]

                usage = result.get("usage", {})
                prompt_tokens = int(usage.get("prompt_tokens", 0))
                completion_tokens = int(usage.get("completion_tokens", 0))
                total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))

                extracted_data = json.loads(content)
                extracted = validate_extracted_knowledge(extracted_data)

                extracted.extraction_confidence = calculate_overall_confidence(extracted)
                extracted.extraction_model = self.model
                extracted.extracted_at = datetime.now(UTC).isoformat()
                extracted.prompt_tokens = prompt_tokens
                extracted.completion_tokens = completion_tokens
                extracted.total_tokens = total_tokens

                safe_log(
                    "nim_extraction_success",
                    institution=extracted.institution.name,
                    courses=len(extracted.courses),
                    confidence=extracted.extraction_confidence.value,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )

                return extracted
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                safe_log("nim_json_error", error=str(e), attempt=attempt + 1)
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP {e.response.status_code}: {e.response.text}"
                safe_log("nim_http_error", status=e.response.status_code, attempt=attempt + 1)
            except Exception as e:
                last_error = str(e)
                safe_log("nim_extraction_error", error=str(e), attempt=attempt + 1)
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)
        
        # All retries failed - return minimal fallback
        safe_log("nim_extraction_failed", error=last_error, url=source_url)
        return self._fallback_extraction(source_url, institution_type)
    
    def _fallback_extraction(
        self,
        source_url: str,
        institution_type: str,
    ) -> ExtractedKnowledge:
        """Minimal fallback when AI extraction fails completely."""
        from .extraction_models import (
            ConfidenceLevel,
            ExtractedInstitution,
            ExtractedKnowledge,
            InstitutionType,
            OwnershipType,
        )
        
        return ExtractedKnowledge(
            institution=ExtractedInstitution(
                name="Unknown Institution",
                institution_type=InstitutionType(institution_type),
                ownership_type=OwnershipType.FEDERAL,
                source_url=source_url,
            ),
            extraction_confidence=ConfidenceLevel.LOW,
            extraction_model=self.model,
            extracted_at=datetime.now(UTC).isoformat(),
        )


async def extract_with_nvidia(
    markdown: str,
    source_url: str,
    institution_type: str,
    known_name: str | None = None,
    academic_session: str = "2025/2026",
) -> ExtractedKnowledge:
    """Convenience function for single extraction."""
    async with NVIDIAExtractor() as extractor:
        return await extractor.extract(
            markdown_content=markdown,
            source_url=source_url,
            institution_type=institution_type,
            known_institution_name=known_name,
            academic_session=academic_session,
        )


# ============================================================================
# TEST / DEMO
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    
    async def test():
        # Simple test with sample content
        sample = """
        # University of Lagos Admission Requirements 2025/2026
        
        The University of Lagos (UNILAG) announces admission requirements for 2025/2026.
        
        **UTME Cut-off Mark:** 200
        
        **O-Level Requirements:** 5 credits including English Language, Mathematics, 
        and 3 other relevant subjects at not more than 2 sittings.
        
        **Post-UTME:** Screening exercise required. Format: Computer-based test. 
        Weight: 30% of aggregate.
        
        **Aggregate Formula:** (UTME/8) + (Post-UTME/2) + (O-Level/2)
        
        **Faculties:** Arts, Basic Medical Sciences, Business Administration, 
        Clinical Sciences, Dental Sciences, Education, Engineering, 
        Environmental Sciences, Law, Pharmacy, Science, Social Sciences.
        
        **Programmes:** Medicine and Surgery (MBBS), Computer Science (B.Sc), 
        Law (LL.B), Accounting (B.Sc), Mass Communication (B.Sc), etc.
        
        **Fees:** Tuition NGN 126,325 per session (indigene), NGN 150,000 (non-indigene).
        Application fee: NGN 2,000.
        
        **Catchment:** ELDS states plus Lagos State indigenes.
        """
        
        try:
            result = await extract_with_nvidia(
                markdown=sample,
                source_url="https://unilag.edu.ng/admissions",
                institution_type="university",
                known_name="University of Lagos",
            )
            
            print(f"Institution: {result.institution.name}")
            print(f"Type: {result.institution.institution_type}")
            print(f"Faculties: {len(result.faculties)}")
            print(f"Courses: {len(result.courses)}")
            print(f"Admission Requirements: {len(result.admission_requirements)}")
            print(f"Cutoffs: {len(result.departmental_cutoffs)}")
            print(f"Fees: {len(result.fees)}")
            print(f"Overall Confidence: {result.extraction_confidence}")
            
        except RuntimeError as e:
            print(f"Test skipped: {e}")
            print("Set NVIDIA_API_KEY to run live test.")
    
    import asyncio
    asyncio.run(test())
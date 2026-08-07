from src.naija_admissions.extraction_models import SYSTEM_PROMPT

print('SYSTEM_PROMPT length:', len(SYSTEM_PROMPT))
print('Contains JSON example:', 'CRITICAL JSON STRUCTURE' in SYSTEM_PROMPT)
print('Contains lowercase confidence:', 'confidence": "high"' in SYSTEM_PROMPT)
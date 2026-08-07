import os
from dotenv import load_dotenv
load_dotenv()

from src.naija_admissions.extraction_models import build_user_prompt

test_markdown = 'Test content about UNILAG admissions'
prompt = build_user_prompt(
    markdown_content=test_markdown,
    source_url='https://unilag.edu.ng',
    institution_type='university',
    known_institution_name='University of Lagos'
)
print('Prompt built successfully, length:', len(prompt))
print('Contains JSON example:', 'CRITICAL JSON STRUCTURE' in prompt)
print('Contains lowercase confidence:', 'confidence": "high"' in prompt)
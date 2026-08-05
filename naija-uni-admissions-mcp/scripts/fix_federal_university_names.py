"""Fix 'Federal University,XYZ' patterns: should be 'Federal University XYZ' (no comma)."""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "src/naija_admissions" / "institutions.py"
content = path.read_text(encoding="utf-8")

pattern = re.compile(r'name="(Federal University),(\w[\w-]*)"')
new_content, count = pattern.subn(r'name="\1 \2"', content)
if new_content != content:
    path.write_text(new_content, encoding="utf-8")
print(f"Fixed {count} 'Federal University,X' patterns")

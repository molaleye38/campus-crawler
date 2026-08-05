"""One-shot fix script for institutions.py: strip trailing ",State" from name field."""
import re
from pathlib import Path

path = Path(__file__).resolve().parent.parent / "src/naija_admissions" / "institutions.py"
content = path.read_text(encoding="utf-8")

pattern = re.compile(r'name="([^"]+),([^"]+)"')


def fix_name(m):
    full = m.group(0)
    name = m.group(1).strip()
    state = m.group(2).strip()
    return f'name="{name}"'


new_content, count = pattern.subn(fix_name, content)
if new_content != content:
    path.write_text(new_content, encoding="utf-8")
print(f"Fixed {count} comma-laden names in institutions.py")

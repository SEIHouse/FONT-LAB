"""Additive release metadata kept separate from the approved drawing settings."""
from pathlib import Path
import json
ROOT = Path(__file__).resolve().parent

def release_version(root=ROOT):
    """Read the release identifier without changing any existing design setting."""
    return json.loads((Path(root)/'phase4.json').read_text(encoding='utf-8'))['version']

def face_order(root=ROOT):
    """Keep whole-script runs in preferred faces without importing font tooling."""
    step=json.loads((Path(root)/'phase4.json').read_text(encoding='utf-8'))['step']
    names=['latin-basic','symbols-icons','latin-extended','latin-ext-2']
    if step>=2: names.extend(['cyrillic','greek'])
    if step>=3: names.append('vietnamese')
    return tuple(names)

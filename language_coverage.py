"""Read the pinned CLDR alphabet inventory used by the first language batch."""
from pathlib import Path
import json
import re
import unicodedata

ROOT = Path(__file__).resolve().parent


def inventory():
    """Return local source data; normal builds and audits need no network access."""
    return json.loads((ROOT/'languages.json').read_text(encoding='utf-8'))


def exemplars(pattern):
    """Expand our pinned CLDR sets, preserving brace-delimited letter sequences.

    These ten alphabet sets use literal letters and strings, without ranges,
    escapes, intersections, or Unicode property expressions. Reject other syntax
    rather than silently treating a future source change as an alphabet.
    """
    assert pattern.startswith('[') and pattern.endswith(']'), pattern
    body = pattern[1:-1]
    assert not any(ch in body for ch in '\\[]-&:'), pattern
    result = []
    for match in re.finditer(r'\{([^{}]+)\}|([^\s{}])', body):
        result.append(match.group(1) or match.group(2))
    assert ''.join(result) == re.sub(r'[\s{}]', '', body), pattern
    return result


def test_strings(locale):
    """Cover main/auxiliary/index strings, casing, and both canonical forms."""
    strings = set()
    for pattern in locale['exemplars'].values():
        for text in exemplars(pattern):
            for case in (text, text.upper(), text.lower(), text.title()):
                strings.update((unicodedata.normalize('NFC', case),
                                unicodedata.normalize('NFD', case)))
    return sorted(strings)


def required_characters():
    """Encoded coverage needed by every recorded exemplar and its case variants."""
    return set(''.join(text for locale in inventory()['locales'].values()
                       for text in test_strings(locale)))

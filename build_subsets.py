"""Create the three WOFF2 deliveries for each SEIReader style with pyftsubset."""
import json
import os
import subprocess
import sys
import unicodedata

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
STYLES = (
    ('Light', 300, 'normal'), ('LightItalic', 300, 'italic'),
    ('Regular', 400, 'normal'), ('Italic', 400, 'italic'),
    ('Medium', 500, 'normal'), ('MediumItalic', 500, 'italic'),
    ('SemiBold', 600, 'normal'), ('SemiBoldItalic', 600, 'italic'),
    ('Bold', 700, 'normal'), ('BoldItalic', 700, 'italic'),
)
SUBSETS = ('latin-basic', 'latin-extended', 'symbols-icons')
LANGUAGE_PUNCTUATION = {0x00A1, 0x00AA, 0x00BA, 0x00BF}
PRECOMPOSED_FRACTIONS = {0x00BC, 0x00BD, 0x00BE}


def group_for(codepoint):
    if 0x20 <= codepoint <= 0x7E or codepoint == 0xA0:
        return 'latin-basic'
    if codepoint in PRECOMPOSED_FRACTIONS:
        return 'symbols-icons'
    if codepoint <= 0x024F and (unicodedata.category(chr(codepoint)).startswith('L')
                                or codepoint in LANGUAGE_PUNCTUATION):
        return 'latin-extended'
    return 'symbols-icons'


def unicode_range(codes):
    spans = []
    for code in sorted(codes):
        if spans and code == spans[-1][1] + 1:
            spans[-1][1] = code
        else:
            spans.append([code, code])
    return ','.join(f'U+{start:04X}' if start == end else f'U+{start:04X}-{end:04X}'
                    for start, end in spans)


def build_subsets():
    with open(os.path.join(HERE, 'settings.json'), encoding='utf-8') as file:
        version = json.load(file)['version']
    css = [f'/* SEIReader {version}: keep this file next to the fonts/ directory. */']
    expected = None
    for style, weight, slant in STYLES:
        source = os.path.join(HERE, 'fonts', f'SEIReader-{style}.otf')
        font = TTFont(source)
        codes = set(font.getBestCmap())
        font.close()
        groups = {name: {code for code in codes if group_for(code) == name} for name in SUBSETS}
        if expected is None:
            expected = groups
        elif groups != expected:
            raise ValueError(f'Unicode coverage changed unexpectedly in {style}')
        if set().union(*groups.values()) != codes or any(not group for group in groups.values()):
            raise ValueError(f'Invalid subset partition in {style}')
        for name in SUBSETS:
            output_name = f'SEIReader-{style}.{name}.woff2'
            output = os.path.join(HERE, 'fonts', output_name)
            code_list = ','.join(f'U+{code:04X}' for code in sorted(groups[name]))
            subprocess.run([sys.executable, '-m', 'fontTools.subset', source,
                            f'--output-file={output}', '--flavor=woff2',
                            f'--unicodes={code_list}', '--layout-features=*',
                            '--name-IDs=*', '--name-languages=*'], check=True,
                           capture_output=True, text=True)
            subset_font = TTFont(output)
            actual = set(subset_font.getBestCmap())
            subset_font.close()
            if actual != groups[name]:
                raise ValueError(f'Subset coverage mismatch: {output_name}')
            css.append(f'''@font-face {{
  font-family: "SEIReader";
  src: url("./fonts/{output_name}") format("woff2");
  font-style: {slant};
  font-weight: {weight};
  font-display: swap;
  unicode-range: {unicode_range(groups[name])};
}}''')
            print('subset', style, name, len(groups[name]), 'encoded characters')
    with open(os.path.join(HERE, 'fonts.css'), 'w', encoding='utf-8', newline='\n') as file:
        file.write('\n\n'.join(css) + '\n')


if __name__ == '__main__':
    build_subsets()

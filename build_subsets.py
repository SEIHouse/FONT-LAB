"""Create the three WOFF2 deliveries for each SEIReader style with pyftsubset."""
import json
import os
import subprocess
import sys
import tempfile
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
LATIN_TEXT_PUNCTUATION = set(map(ord, '.,:;…!?\'"‘’“”‚„‛‟-–—()[]{}«»‹›ʻʼ\u2009\u202f'))


def group_for(codepoint):
    # Keep U+2044 with ASCII digits so directly typed fractions can shape as one run.
    """Assign a codepoint to its primary web delivery while keeping fractions with digits."""
    if 0x20 <= codepoint <= 0x7E or codepoint in (0xA0, 0x2044):
        return 'latin-basic'
    if codepoint in PRECOMPOSED_FRACTIONS:
        return 'symbols-icons'
    if (unicodedata.name(chr(codepoint),'').startswith('LATIN ')
            or 0x0300 <= codepoint <= 0x036F or codepoint == 0x25CC
            or codepoint in LANGUAGE_PUNCTUATION or codepoint in LATIN_TEXT_PUNCTUATION):
        return 'latin-extended'
    return 'symbols-icons'


def subset_groups(codes, include_interpunct=True):
    """Keep Latin graphemes and surrounding prose in one preferred web font face."""
    groups = {name:{c for c in codes if group_for(c)==name} for name in SUBSETS}
    groups['latin-extended'].update(groups['latin-basic'])
    # Keep the Latin word separator in the same face, also retaining its icon delivery.
    if include_interpunct and 0x00B7 in codes: groups['latin-extended'].add(0x00B7)
    return groups


def unicode_range(codes):
    """Compress sorted codepoints into CSS unicode-range spans."""
    spans = []
    for code in sorted(codes):
        if spans and code == spans[-1][1] + 1:
            spans[-1][1] = code
        else:
            spans.append([code, code])
    return ','.join(f'U+{start:04X}' if start == end else f'U+{start:04X}-{end:04X}'
                    for start, end in spans)


def build_subsets():
    """Build and validate thirty WOFF2 subsets, then refresh both app stylesheets."""
    with open(os.path.join(HERE, 'settings.json'), encoding='utf-8') as file:
        version = json.load(file)['version']
    css = [f'/* SEIHouse Sans {version}: legacy SEIReader CSS alias; keep next to fonts/. */']
    expected = None
    for style, weight, slant in STYLES:
        source = os.path.join(HERE, 'fonts', f'SEIReader-{style}.otf')
        font = TTFont(source)
        codes = set(font.getBestCmap())
        font.close()
        groups = subset_groups(codes)
        if expected is None:
            expected = groups
        elif groups != expected:
            raise ValueError(f'Unicode coverage changed unexpectedly in {style}')
        if set().union(*groups.values()) != codes or any(not group for group in groups.values()):
            raise ValueError(f'Invalid subset partition in {style}')
        # The last face is preferred for Latin, including complete accent clusters.
        for name in ('latin-basic','symbols-icons','latin-extended'):
            output_name = f'SEIReader-{style}.{name}.woff2'
            output = os.path.join(HERE, 'fonts', output_name)
            code_list = ','.join(f'U+{code:04X}' for code in sorted(groups[name]))
            # Write a fresh sibling and replace it after validation. Directly truncating
            # an existing file in the synced Windows checkout can return EINVAL.
            descriptor, temporary = tempfile.mkstemp(prefix='.subset-',suffix='.woff2',dir=os.path.dirname(output))
            os.close(descriptor)
            try:
                subprocess.run([sys.executable, '-m', 'fontTools.subset', source,
                                f'--output-file={temporary}', '--flavor=woff2',
                                f'--unicodes={code_list}', '--layout-features=*',
                                '--name-IDs=*', '--name-languages=*'], check=True,
                               capture_output=True, text=True)
                with TTFont(temporary) as subset_font:
                    if set(subset_font.getBestCmap()) != groups[name]:
                        raise ValueError(f'Subset coverage mismatch: {output_name}')
                os.replace(temporary,output)
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(f'pyftsubset failed for {output_name}:\n{exc.stderr}') from exc
            finally:
                if os.path.exists(temporary): os.remove(temporary)
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
    # The app's default delivery uses existing full WOFF2 files. Keep both CSS options current.
    from build_distribution import write_full_css
    write_full_css()


if __name__ == '__main__':
    build_subsets()

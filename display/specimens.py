"""Generate per-cut specimens that use the finished font's native layout."""
from html import escape
import os
from pathlib import Path
import shutil

from display.letter_alternates import SET_NAMES

HERE = Path(__file__).resolve().parent
THEMES = {
    'soft': ('AFTER', 'HOURS', 'A softer landing.', '#f39180'),
    'edge': ('HARD', 'LIGHT', 'Find your edge.', '#d8ee8e'),
    'ink': ('NIGHT', 'SHIFT', 'Leave a little trace.', '#edb872'),
    'wide': ('OPEN', 'AIR', 'Room for everything.', '#afa8f5'),
}


def relative_asset(root, directory, file):
    return Path(os.path.relpath(root/file, directory)).as_posix()


def write_specimens(manifest, root):
    root = Path(root)
    directory = root/'site/display'
    directory.mkdir(parents=True, exist_ok=True)
    for name in ('specimen.css', 'specimen.js'):
        shutil.copyfile(HERE/name, directory/name)
    links = []
    for cut in manifest['cuts']:
        page = root/cut['specimen']
        page.parent.mkdir(parents=True, exist_ok=True)
        first, second, tagline, accent = THEMES.get(cut['slug'], ('NEW', 'WAVES', 'A new direction.', '#91cbd1'))
        face_rules, options, downloads = [], [], []
        for face in cut['styles']:
            family = escape(face['family'], quote=True)
            url = relative_asset(root, page.parent, face['woff2'])
            face_rules.append(f'@font-face {{font-family:"{family}";src:url("{url}") format("woff2");'
                              f'font-weight:{face["weight"]};font-style:{face["slope"]};font-display:swap;}}')
            options.append(f'<option value="{escape(face["label"])}" data-weight="{face["weight"]}" '
                           f'data-slope="{face["slope"]}">{escape(face["label"])}</option>')
            downloads.append(f'<a href="{relative_asset(root, page.parent, face["otf"])}" download>'
                             f'{escape(face["label"])} OTF ↓</a>')
        controls = ''.join(f'<label><input type="checkbox" data-feature="{tag}"> {escape(label)}</label>'
                           for tag, label in SET_NAMES.items())
        name = escape(cut['name'])
        html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name} · SEIHouse Display specimen</title><meta name="description" content="{name} in an album cover, track list, poster and alphabet. Uses the finished SEIHouse Display font.">
<link rel="stylesheet" href="../specimen.css"><style>{''.join(face_rules)}
:root {{--cut-family:"{family}";--accent:{accent};}}</style><script src="../specimen.js" defer></script></head>
<body><header><a href="../index.html">← Display collection</a><a href="../../../LICENSE">Font license ↗</a></header>
<main><div class="intro"><div><p class="eyebrow">SEIHOUSE DISPLAY / SPECIMEN</p><h1>{name}</h1><p>{tagline} A typeface for titles that carry a mood.</p></div>
<div class="style-control"><label for="style">Font style</label><select id="style">{''.join(options)}</select></div></div>
<details class="controls"><summary>Letter designs &amp; capital spacing</summary><div class="feature-grid">
<label><input type="checkbox" data-feature="cpsp" checked> Capital spacing</label>{controls}</div></details>
<div class="specimen-grid"><section class="album" aria-labelledby="album-label"><h2 id="album-label" class="eyebrow">01 / ALBUM COVER</h2>
<div class="cover"><div class="cover-orbit" aria-hidden="true"></div><span class="cover-label">SEIHOUSE SOUND / VOL. 01</span>
<p class="cut cover-title">{first}<br>{second}</p><div class="cover-footer"><span>AN ORIGINAL RECORDING</span><span>33⅓ RPM</span></div></div></section>
<section class="tracks" aria-labelledby="tracks-label"><h2 id="tracks-label" class="eyebrow">02 / TRACK LIST</h2><p class="cut track-title">Side A<br>First light.</p>
<ol><li><span class="cut">A little further</span><span>03:42</span></li><li><span class="cut">Velvet radio</span><span>04:08</span></li>
<li><span class="cut">Way out west</span><span>02:56</span></li><li><span class="cut">All tomorrow</span><span>05:14</span></li>
<li><span class="cut">Quiet company</span><span>03:31</span></li></ol><p class="track-note">Five tracks. One direction. Play it from the beginning.</p></section>
<section class="poster" aria-labelledby="poster-label"><h2 id="poster-label" class="eyebrow">03 / POSTER</h2><div class="poster-top"><span>LIVE / ONE NIGHT ONLY</span><span>SEIHOUSE SESSIONS</span></div>
<p class="cut poster-title">TURN<br>IT UP.</p><div class="poster-bottom"><p class="cut">Late arrival.<br>Lasting impression.</p><span>FRIDAY · 21:00<br>THE LISTENING ROOM</span></div></section>
<section class="alphabet" aria-labelledby="alphabet-label"><h2 id="alphabet-label" class="eyebrow">04 / ALPHABET</h2><p class="cut alphabet-letters">ABCDEFGHIJKLMNOPQRSTUVWXYZ</p>
<p class="cut alphabet-letters">abcdefghijklmnopqrstuvwxyz</p><p class="cut alphabet-digits">0123456789 &amp;!? ¼½¾</p>
<div class="language-lines"><p class="cut" lang="vi">Tưởng tượng · Ánh sáng</p><p class="cut" lang="tr">İstanbul · Şehir</p>
<p class="cut" lang="el">Νέοι ορίζοντες</p><p class="cut" lang="uk">Нові горизонти</p></div></section></div>
<footer><div><p class="eyebrow">TAKE {name.upper()} WITH YOU</p><div class="downloads">{''.join(downloads)}
<a href="{relative_asset(root, page.parent, manifest['css'])}" download>Web stylesheet ↓</a></div></div>
<p>SEIHouse Sans Ecosystem License 1.0<br>SEIHouse Productions LLC</p></footer></main></body></html>'''
        page.write_text(html+'\n', encoding='utf-8', newline='\n')
        links.append(f'<a class="collection-cut" style="--accent:{accent}" href="./{cut["slug"]}/index.html">'
                     f'<span class="eyebrow">{len(cut["styles"])} BUILT STYLE'+('S' if len(cut['styles'])!=1 else '')+
                     f'</span><h2>{name}</h2><p>{escape(tagline)}</p><span>View specimen ↗</span></a>')
    (directory/'index.html').write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Display collection · SEIHouse Font Lab</title><link rel="stylesheet" href="./specimen.css"></head>
<body><header><a href="https://fontlab.seihouse.world/">← Font Lab</a><a href="../../LICENSE">Font license ↗</a></header>
<main><div class="intro"><div><p class="eyebrow">SEIHOUSE DISPLAY / COLLECTION</p><h1>A cut for every mood.</h1>
<p>Explore each finished font on a cover, a track list, a poster and an alphabet.</p></div></div>
<div class="collection">{''.join(links)}</div></main></body></html>\n''', encoding='utf-8', newline='\n')

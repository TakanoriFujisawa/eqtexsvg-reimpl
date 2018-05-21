#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, subprocess, tempfile, textwrap, re
    
temp_dir = os.path.join(tempfile.gettempdir(), 'eqtexsvg-metrics')
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)
os.chdir(temp_dir)

par = '\\par'
export_glyphs = [] \
+ [ c for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ par ] \
+ [ c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ par ] \
+ [ c for c in '0123456789' ] + [ par ] \
+ [ '$' + c + '$' for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ par ] \
+ [ '$' + c + '$' for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ par ] \
+ [ '$_\\text{' + c + '}$' for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ par ] \
+ [ '$_\\text{' + c + '}$' for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ par ] \
+ [ '$_' + c + '$' for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ par ] \
+ [ '$_' + c + '$' for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ par ] \
+ [ '$_' + c + '$' for c in '0123456789' ] + [ par ] \
+ [ '$\\mathbf{' + c + '}$' for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ par ] \
+ [ '$\\mathbf{' + c + '}$' for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ par ] \
+ [ '$\\mathbf{' + c + '}$' for c in '0123456789' ] + [ par ] \
+ [ '$\\bm{' + c + '}$' for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ par ] \
+ [ '$\\bm{' + c + '}$' for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ par ] \
+ [ '$' + c + '$' for c in '[]()+/=.,:;!?' ] \
+ [ '$\\' + c + '$' for c in '{}#$%' ] \
+ [ '${}' + c + '{}$' for c in '<>' ] \
+ [ '${}' + c + '{}$' for c in ['\\ast'] ] \
+ [ par ] \
+ [ '${}_{' + c + '}{}$' for c in '[]()+/=.,:;!?' ] \
+ [ '${}_{' + c + '}{}$' for c in '<>' ] \
+ [ par ] \
+ []

def svg_text(c, family='Latin Modern Roman', weight='normal', style='normal', size=10, scale=''):
    text = '''<text {scale} style="line-height:125%;fill:black;stroke:none;font-family:'{family}'; \
font-size:{size}px;font-family:'{family}';font-weight:{weight};font-style:{style}"> \
<tspan sodipodi:role="line">{text}</tspan></text>'''
    return text.format(text=c, family=family, weight=weight, style=style, size=size, scale=scale)

to_svg = []  \
+ [ svg_text(c) for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ None ] \
+ [ svg_text(c) for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ None ] \
+ [ svg_text(c) for c in '0123456789' ] + [ None ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.8,0)"') for c in 'abcde' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(0.8,0)"') for c in 'f' ] \
+ [ svg_text(c, style='italic') for c in 'gh' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.4,0)"') for c in 'i' ] \
+ [ svg_text(c, style='italic') for c in 'jk' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.2,0)"') for c in 'lmnopqrstuvwxyz' ] \
+ [ None ] \
+ [ svg_text(c, style='italic') for c in 'AB' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.6,0)"') for c in 'C' ] \
+ [ svg_text(c, style='italic') for c in 'DEF' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.6,0)"') for c in 'G' ] \
+ [ svg_text(c, style='italic') for c in 'HIJKLMN' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.4,0)"') for c in 'O' ] \
+ [ svg_text(c, style='italic') for c in 'P' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.6,0)"') for c in 'Q' ] \
+ [ svg_text(c, style='italic') for c in 'RS' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.6,0)"') for c in 'TUV' ] \
+ [ svg_text(c, style='italic', scale='transform="translate(-0.4,0)"') for c in 'WXYZ' ] \
+ [ None ] \
+ [ svg_text(c, size=7, scale='transform="scale(1.1,1)"') for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ None ] \
+ [ svg_text(c, size=7, scale='transform="scale(1.1,1)"') for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ None ] \
+ [ svg_text(c, style='italic', size=7, scale='transform="scale(1.1,1)"') for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ None ] \
+ [ svg_text(c, style='italic', size=7, scale='transform="scale(1.1,1)"') for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ None ] \
+ [ svg_text(c, size=7, scale='transform="scale(1.1,1)"') for c in '0123456789' ] + [ None ] \
+ [ svg_text(c, weight='bold') for c in 'abcdefghijklmnopqrstuvwxyz' ] + [ None ] \
+ [ svg_text(c, weight='bold') for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ None ] \
+ [ svg_text(c, weight='bold') for c in '0123456789' ] + [ None ] \
+ [ svg_text(c, weight='bold', style='italic', scale='transform="translate(-0.6,0)"') for c in 'abcde' ] \
+ [ svg_text(c, weight='bold', style='italic', scale='transform="translate(0.6,0)"') for c in 'f' ] \
+ [ svg_text(c, weight='bold', style='italic') for c in 'gh' ] \
+ [ svg_text(c, weight='bold', style='italic', scale='transform="translate(-0.4,0)"') for c in 'i' ] \
+ [ svg_text(c, weight='bold', style='italic') for c in 'jklmn' ] \
+ [ svg_text(c, weight='bold', style='italic', scale='transform="translate(-0.4,0)"') for c in 'o' ] \
+ [ svg_text(c, weight='bold', style='italic') for c in 'pqrstuvwxyz' ] \
+ [ None ] \
+ [ svg_text(c, weight='bold', style='italic') for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' ] + [ None ] \
+ [ svg_text(c) for c in '[]()+/=.,:;!?' ] \
+ [ svg_text(c) for c in '{}#$%' ] \
+ [ svg_text(c) for c in ['&lt;', '&gt;'] ] \
+ [ svg_text(c) for c in ['*'] ] \
+ [ None ] \
+ [ svg_text(c, size=7, scale='transform="scale(1.1,1)"') for c in '[]()+/=.,:;!?' ] \
+ [ svg_text(c, size=7, scale='transform="scale(1.1,1)"') for c in ['&lt;', '&gt;'] ] \
+ [ None ] \
+ []

with open('eq.tex', 'w') as f:
    f.write('''
    %% Automatically generated for eqtexsvg.py
    \\documentclass[10pt]{article}
    \\usepackage[a4paper,driver=dvips]{geometry}
    \\usepackage{amsmath,amssymb,amsfonts,mathtools}
    \\usepackage[T1]{fontenc}
    \\usepackage{lmodern}
    \\usepackage{bm}
    \\usepackage{array}
    \\begin{document}
    \\thispagestyle{empty}
    \\setlength{\\parindent}{0pt}
    ''')
        
    count = 0
    for g in export_glyphs:
        f.write(g + ' ')
    f.write('\n\\end{document}')
        
subprocess.check_call('latex -halt-on-error eq.tex', shell=True, stdout=sys.stderr)
subprocess.check_call('dvipdfmx eq.dvi', shell=True, stdout=sys.stderr)
subprocess.check_call('dvisvgm -v0 -R -p1 --no-mktexmf -a -n -o eq.svg eq.dvi', shell=True)

defs = dict()
re_path = re.compile("<path d='([-a-zA-Z0-9. ]+)' id='([-a-z0-9]+)'")
re_use  = re.compile("href='#([-a-z0-9]+)'")
glyph_count = 0

glyph_map = dict()
with open('eq.svg') as f:
    for line in f:
        if line.startswith('<path'):
            match = re_path.match(line)
            if match:
                defs[match.group(2)] = match.group(1)
                    
        elif line.startswith('<use'):
            match = re_use.search(line)
            if not match:
                raise RuntimeError('Node not matched ' + line)

            ref_id = match.group(1)

            if not ref_id in defs:
                raise RuntimeError('Id({0}) is not in defs'.format(ref_id))

            # find latex/unicode
            if export_glyphs[glyph_count] == par:
                glyph_count += 1

            if len(export_glyphs) <= glyph_count:
                raise RuntimeError("Glyph {0} not processed (no latex entry)".format(glyph_count))
            elif len(to_svg) <= glyph_count:
                raise RuntimeError("Glyph {0} not processed (no svg entry)".format(glyph_count))
            
            glyph_latex = export_glyphs[glyph_count]
            glyph_svg = to_svg[glyph_count]
            glyph_map[defs[ref_id]] = glyph_svg
            glyph_count += 1

print '#!/usr/bin/env python'
print 'glyphs_map =', repr(glyph_map).replace("', '", "',\n'")

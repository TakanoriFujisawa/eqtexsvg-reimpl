#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
eqtexsvg.py
An extension to convert LaTeX equation string into SVG path
"""
# export PYTHONPATH='/Applications/Lab/local/lib/python2.7/site-packages'
import inkex

import os, sys, platform, tempfile, subprocess, time, logging, shutil, textwrap, traceback, re
from copy import deepcopy

eqtexsvg_debug = True

# ログの制御
if eqtexsvg_debug:
    temp_dir = os.path.join(tempfile.gettempdir(), 'eqtexsvg')
    if not os.path.isdir(temp_dir):
        os.mkdir(temp_dir)
else:
    temp_dir = tempfile.mkdtemp(prefix='inkscape-')

os.chdir(temp_dir)

if eqtexsvg_debug:
    if False:
        log_path = os.path.join(temp_dir, 'eqtexsvg.log')
        logstream = open(log_path, 'w')
    else:
        if platform.system() == 'Darwin':
            logstream = open('/dev/ttys000', 'w')
        else:
            logstream = open('/dev/pts/2', 'w')
    logging.basicConfig(stream=logstream, level=logging.DEBUG,
                        datefmt='%d/%m/%Y %H:%M:%S', format= "%(asctime)s: %(message)s")

# グリフ置換のモジュールをロード
try:
    from eqtexsvg_glyphs_lm import glyphs_map as lm
    replace_text_lm = True
    logging.debug('glyph list for latin modern loaded')

except ImportError:
    replace_text_lm = False

# TeX 環境のパスを追加
if platform.system() == 'Linux':
    search_path = [ '/usr/local/texlive/{0}/bin/x86_64-linux'.format(y) for y in range(2018, 2013, -1) ]
elif platform.system() == 'Darwin':
    search_path = [ '/Library/TeX/texbin', '/usr/texbin' ]
else:
    search_path = [ 'C:\\texlive\\{0}\\bin\\win32'.format(y) for y in range(2018, 2013, -1) ]

for path in search_path:
    if os.path.exists(path):
        if eqtexsvg_debug:
            logging.debug("Path added '%s'", path)
        os.environ['PATH'] += os.pathsep + path
        break

def exec_cmd(cmd_line, on_error_message=None, check_files=[]):
    """Launch given command line (and report in log if debug)"""
    ps = subprocess.Popen(cmd_line, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = ps.communicate()
    
    if eqtexsvg_debug:
        logging.debug('cmd_line: ' + cmd_line)
        logging.debug('returncode: ' + str(ps.returncode))
        logging.debug('stderr:\n' + stderr)
        logging.debug('stdout:\n' + stdout)

    if ps.returncode != 0:
        message = on_error_message if on_error_message else 'Command "{0}" failed'.format(cmd_line)
        message += '\n' + stdout + '\n' + stderr
        raise RuntimeError(message)

    if not all([ os.path.exists(f) for f in check_files ]):
        message = on_error_message if on_error_message else 'Output file not generated'
        message += '\n' + stdout + '\n' + stderr
        raise RuntimeError(message)
    
    return stdout, stderr

## Check for executables
exec_cmd('latex --version', 'Failed to find latex executable')
exec_cmd('dvisvgm --version', 'Failed to find dvisvgm executable')

# =============================== VARIABLES ==============================
formula = u'$\\displaystyle\\lim_{n \\to \\infty}\\sum_{k=1}^n \\frac{1}{k^2}= \\frac{\\pi^2}{6}$'
document = ''
preamble = u''
replace_text = False
# 追加プリアンブル欄に "\replacetexttrue" があるとグリフ置換をオンに
magic_comment_true  = u'\\replacetexttrue'
# "\replacetextfalse" があるとグリフ置換をオフに
magic_comment_false = u'\\replacetextfalse'
view_center = (0, 0)

# =============================== FUNCTIONS ==============================
def cleanup():
    if not eqtexsvg_debug:
        shutil.rmtree(temp_dir)

def import_svg():
    global replace_text
    if not replace_text_lm:
        replace_text = False
    
    # svg のインポート
    ns_svg_g = '{%s}g' % inkex.NSS['svg']
    ns_svg_defs = '{%s}defs' % inkex.NSS['svg']
    ns_svg_text = '{%s}text' % inkex.NSS['svg']
    ns_svg_tspan = '{%s}tspan' % inkex.NSS['svg']
    ns_href = '{%s}href' % inkex.NSS['xlink']
    
    ## try parsing svg
    with open('eq.svg') as f:
        tree = inkex.etree.parse(f)
    
    eq_tree = tree.getroot()
    
    name = "equation_%d" % time.time()
    
    # Create new group node containing the equation
    eqn = inkex.etree.Element(ns_svg_g)
    eqn.set('id', name)
    eqn.set('style', 'fill: black; stroke: none;')
    eqn.set('x', str(view_center[0]))
    eqn.set('y', str(view_center[1]))
    # eqn.set('title', self.formula)
        
    dicnode = {}
    for elt in eq_tree:
        if elt.tag == ns_svg_defs:
            # 辞書 dicnode にノードを追加
            for subelt in elt:
                dicnode[subelt.get('id')] = subelt
                
        else:
            for subelt in elt:
                if ns_href in subelt.attrib:
                    # <use> 要素 --> dicnode からノードを取得して書き出し
                    
                    referred = dicnode[subelt.get(ns_href).split('#')[-1]]
                    
                    if replace_text:
                        if 'd' in referred.keys() and referred.attrib['d'] in lm:
                            logging.debug('replacement found' + referred.attrib['d'])
                            logging.debug('replaced to ' + lm[referred.attrib['d']])
                            
                            try:
                                # <use> ノードの x, y を transform 属性に変換
                                # パースしたテキストノードに transform を入れている場合
                                # があるので <g> 要素で包む 
                                eqn_g = inkex.etree.SubElement(eqn, ns_svg_g)
                                translate = ('translate(%s,%s)' % (subelt.get('x'), subelt.get('y')))
                                eqn_g.set('transform', translate)

                                eqn_text = re.sub('^<text ', \
                                                  '<text xmlns="http://www.w3.org/2000/svg" ' + \
                                                  'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" ',
                                                  lm[referred.attrib['d']])
                                eqn_text = inkex.etree.fromstring(eqn_text)
                                eqn_g.append(eqn_text)
                                
                                logging.debug('Node appended')
                                logging.debug(inkex.etree.tostring(eqn_text, pretty_print=True))
                                continue
                            except Exception as ex:
                                logging.debug('Failed to parse node')
                                logging.debug(traceback.format_exc(ex))
                                pass
                            
                    # defs のノードをコピー
                    eqn_elt = inkex.etree.SubElement(eqn, referred.tag)
                    
                    # <use> ノードの x, y は transform 属性に変換
                    translate = ('translate(%s,%s)' % (subelt.get('x'), subelt.get('y')))
                    eqn_elt.set('transform', translate)
                    
                    # 参照するノードの他の属性をコピー
                    for key in referred.keys():
                        if not 'id' in key:
                            eqn_elt.set(key, referred.attrib[key])

                else:
                    # 元のノードをコピー
                    eqn_elt = inkex.etree.SubElement(eqn, subelt.tag)
                    for key in subelt.keys():
                        eqn_elt.set(key, subelt.attrib[key])
    return eqn

def generate():
    if not formula:
        sys.exit('Without formula, no equation will be generated')
    
    with open('eq.tex', 'w') as f:
        f.write(textwrap.dedent(u'''
        %% Automatically generated for eqtexsvg.py
        \\documentclass[10pt]{{article}}
        \\usepackage[a4paper,driver=dvips]{{geometry}}
        \\usepackage{{amsmath,amssymb,amsfonts,mathtools}}
        \\usepackage[T1]{{fontenc}}
        \\usepackage{{lmodern}}
        \\usepackage{{bm}}
        \\usepackage{{array}}
        \\newif\\ifreplacetext
        {preamble}
        \\begin{{document}}
        \\thispagestyle{{empty}}
        {formula}
        \\end{{document}}
        ''').format(preamble=preamble, formula=formula))

    exec_cmd('latex -file-line-error -halt-on-error eq.tex',
             on_error_message='LaTeX typesetting failed',
             check_files=['eq.dvi'])
    
    # デフォルトだとマルチページの入力で別のファイル名 (eq-1.svg等) に
    # なるので -o オプションで出力ファイル名 (のパターン) を指定
    #   -v0 : コンソール出力を抑止
    #   -R  : パスを相対パスに
    #   -p1 : 1 ページ目のみ出力
    #   --no-mktexmf : フォントが見つからなくても mktexmf を走らせない
    #   -n  : すべてのグリフをパスで表記
    #   -a  : ビットマップフォントをトレース
    exec_cmd('dvisvgm -v0 -R -p1 --no-mktexmf -a -n -o eq.svg eq.dvi',
             on_error_message='Failed to convert dvi',
             check_files=['eq.svg'])

    return import_svg()

# ================================ CLASSES ===============================
class InsertEquation(inkex.Effect):
    """Insert LaTeX Equation into the current Inscape instance"""

    def __init__(self):
        inkex.Effect.__init__(self)
        
        self.OptionParser.add_option('-f', '--formula',
                                     action='store', type='string', 
                                     dest='formula', help='LaTeX formula',
                                     default=formula)
        self.OptionParser.add_option('-p', '--preamble',
                                     action='store', type='string', 
                                     dest='preamble', help='Additional string in preamble',
                                     default='')
        self.OptionParser.add_option('-t', '--replace-text',
                                     action='store', type='inkbool', 
                                     dest='replace_text', help='replace text as node (experimental)',
                                     default=False)

    def effect(self):
        global formula, document, preamble, replace_text, view_center
        #
        if type(self.options.formula) != unicode:
            formula = unicode(self.options.formula, 'utf-8')
        else:
            formula = self.options.formula
        formula = formula.replace(u'¥', u'\\')
        #
        if type(self.options.preamble) != unicode:
            preamble = unicode(self.options.preamble, 'utf-8')
        else:
            preamble = self.options.preamble
        preamble = preamble.replace(u'¥', u'\\')

        if magic_comment_true in preamble:
            logging.debug('Replacing glyphs enabled by magic comment!')
            replace_text = True
        elif magic_comment_false in preamble:
            logging.debug('Replacing glyphs disabled by magic comment!')
            replace_text = False
        
        document = self.document
        
        view_center = self.view_center
        
        eq = generate()

        self.current_layer.append(eq)

if __name__ == "__main__":
    try:
        e = InsertEquation()
        e.affect()
        #generate()
    except Exception as ex:
        logging.debug(traceback.format_exc(ex))
        cleanup()
        raise ex

cleanup()

sys.exit(0)


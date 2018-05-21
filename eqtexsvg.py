#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
eqtexsvg.py
An extension to convert LaTeX equation string into SVG path
"""

import inkex
import os, sys, platform, tempfile, subprocess, time
import logging
from StringIO import StringIO
from copy import deepcopy


# ログの制御
eqtexsvg_debug = True
if eqtexsvg_debug:
    log = os.path.join(tempfile.gettempdir(), 'eqtexsvg.log')
    
    if True:
        logstream = open(log, mode="w")
    else:
        logstream = open("/dev/ttys004", "w")
    
    logging.basicConfig(stream=logstream, level=logging.DEBUG,
                        datefmt='%d/%m/%Y %H:%M:%S', format= "%(asctime)s: %(message)s")

# TeX 環境のパスを追加
if platform.system() == 'Linux':
    search_path = [
        '/usr/local/texlive/2018/bin/x86_64-linux',
        '/usr/local/texlive/2017/bin/x86_64-linux',
        '/usr/local/texlive/2016/bin/x86_64-linux',
        '/usr/local/texlive/2015/bin/x86_64-linux',
    ]

elif platform.system() == 'Darwin':
    search_path = [
        '/Library/TeX/texbin', '/usr/texbin'
    ]

else:
    search_path = [
        'C:\texlive\2018\bin\win32',
        'C:\texlive\2017\bin\win32',
        'C:\texlive\2016\bin\win32',
        'C:\texlive\2015\bin\win32',
    ]

for path in search_path:
    logging.debug(path)
    if os.path.exists(path):
        if eqtexsvg_debug:
            logging.debug("Path added '%s'", path)
        os.environ['PATH'] += os.pathsep + path
        break

def exec_cmd(cmd_line=None, debug=True):
    """Launch given command line (and report in log if debug)"""
    
    rm = lambda x: '\n'.join([l for l in x.split('\n') if l != ""])

    p = subprocess.Popen(cmd_line, shell=True,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)

    (std_out, std_err) = p.communicate()
    std_out = rm(std_out)
    std_err = rm(std_err)

    if debug:
        logging.debug(cmd_line)
        logging.debug('returncode: '+str(p.returncode))
        logging.debug('stderr:\n'+std_err)
        logging.debug('stdout:\n'+std_out)

    return (p.returncode, std_out, std_err)


class Equation:
    """Current LaTeX Equation"""

    def __init__(self, param={}):
        
        self.document = None
        self.formula = None
        self.temp_dir = None
        self.debug = False
        
        if param.has_key('debug'):
            self.debug = param['debug']

        if eqtexsvg_debug:
            self.debug = True
            
        if self.debug:
            inkscape_version = 'Inkscape 0.91 r13725 (Feb 19 2015)'

            logging.debug(inkscape_version)
            ## get Python informations system, release and machine informations
            
            logging.debug("Python %s\nCompiler: %s\nBuild   : %s" %(
                                                    platform.python_version(),
                                                    platform.python_compiler(),
                                            ' '.join(platform.python_build())))
            logging.debug("Platform: %s" %(platform.platform()))
            logging.debug("Current Working Directory: %s" %(os.getcwd()))
            logging.debug("Current Extension Directory: %s" %(
                                                    os.path.abspath(__file__)))
        try: 
            self.temp_dir = tempfile.mkdtemp('', 'inkscape-')
            if self.debug:
                logging.debug(self.temp_dir)
        except:
            if self.debug:
                logging.debug('Temporary directory cannot be created')
            sys.exit('Temporary directory cannot be created')
            
        if param.has_key('document'):
            self.document = param['document']

        if param.has_key('formula'):
            self.formula = unicode(param['formula'], 'utf-8')
            if self.debug:
                logging.debug(self.formula)
        else:
            if self.debug:
                logging.debug('No formula detected')
            sys.exit('Without formula, no equation will be generated')

        if param.has_key('packages'):
            self.pkgstring = param['packages']
        else:
            self.pkgstring = ""
            
        if param.has_key('view_center'):
            self.view_center = param['view_center']
        else:
            self.view_center = (0, 0)
        
        self.file_ext = ['.tex', '.aux', '.log', '.dvi', '.out', '.err', '.ps']

        self.file = 'eq'
        self.svg = None
        self.file_tex = os.path.join(self.temp_dir, self.file + '.tex')
        self.file_ps  = os.path.join(self.temp_dir, self.file + '.ps')
        self.file_dvi = os.path.join(self.temp_dir, self.file + '.dvi')
        self.file_svg = os.path.join(self.temp_dir, self.file + '.svg')
        self.file_out = os.path.join(self.temp_dir, self.file + '.out')
        self.file_err = os.path.join(self.temp_dir, self.file + '.err')
        
        self.latex    = False
        self.dvips    = False
        self.pstoedit = False
        self.dvisvgm  = False


    def path_programs(self, cmd_line=None, code=True):
        """Try to launch given command line with pass return code"""
        
        ## convention ==0 : True, !=0 : False
        ## 'latex --version' ==0
        ## 'dvips -v'  !=0
        ## 'pstoedit -v' !=0
        ## 'dvisvgm -V' ==0
        
        program_name = cmd_line.split()[0]

        try:
            retcode = exec_cmd(cmd_line, self.debug)[0]

            if ((retcode==0) if code else retcode):
                exec('self.'+program_name+' = True')
                if self.debug:
                    logging.debug(program_name + " OK")
            else:
                exec('self.'+program_name+' = False')
                if self.debug:
                    logging.debug(program_name + " not OK")

        except OSError, e:
            if self.debug:
                logging.debug(program_name + " failed: " + e)
            sys.stderr.write(program_name + " failed:" + e)
            sys.exit(1)


    def parse_pkgs(self):
        """Add custom packages to TeX source"""
        
        if self.pkgstring != "":
            pkglist = self.pkgstring.replace(" ","").split(",")
            header = ""
            for pkg in pkglist:
                header += "\\usepackage{%s}\n" % pkg
            self.header = header
            if self.debug:
                logging.debug('packages:\n'+self.header)
        else:
            self.header = ""
            if self.debug:
                logging.debug('No package')


    def generate_tex(self):
        """Generate the LaTeX Equation file"""

        self.parse_pkgs()
        
        texstring = "%% processed with eqtexsvg.py\n"
        
        texstring += '\n'.join([
            '\\documentclass{article}',
            '\\usepackage{amsmath,amssymb,amsfonts,mathtools}',
            '\\usepackage[T1]{fontenc}',
            '\\usepackage{lmodern}',
            self.header,
            '\\usepackage{bm}',
            '\\thispagestyle{empty}',
            '\\begin{document}',
            self.formula.replace(u'¥', u'\\'),
            '\\end{document}'
        ])
        
        if self.debug:
            logging.debug('\n'+texstring)
        
        try:
            tex = open(self.file_tex,'w')
            tex.write(texstring)
            tex.close()
            if self.debug:
                logging.debug('TEX file generated')
        except:
            if self.debug:
                logging.debug('TEX file not generated')


    def generate_dvi(self):
        """Generate the DVI Equation file"""

        cmd_line  = 'latex '
        cmd_line += '-output-directory="%s"' %(self.temp_dir)
        cmd_line += ' -halt-on-error '
        cmd_line += "%s "    %(self.file_tex)

        retcode, std_out, std_err = exec_cmd(cmd_line, self.debug)
        
        if retcode:
            if self.debug:
                logging.debug('DVI file not generated with latex')
            print >> sys.stderr, std_out, std_err
            sys.exit('Problem to generate DVI file')
        else:
            if self.debug:
                logging.debug('DVI file generated with latex')


    def generate_svg(self):
        """Generate the SVG Equation string/file"""

        ## Use dvisvgm
        cmd_line = 'dvisvgm '
        cmd_line += '-v0 '         ## set verbosity level to 0
        cmd_line += '-a '          ## trace all glyphs of bitmap fonts
        cmd_line += '-n '          ## draw glyphs by using path elements
        cmd_line += '-s '          ## write SVG output to stdout
        cmd_line += '"%s"' %(self.file_dvi)       ## Input file

        retcode, std_out, std_err = exec_cmd(cmd_line, self.debug)
        ## Get SVG from dvisvgm output
        self.svg = std_out
        
        if retcode == 0:
            if self.debug:
                logging.debug('SVG file generated with dvisvgm')
        else:
            if self.debug:
                logging.debug('SVG file not generated with dvisvgm')
            sys.exit('SVG file not generated with dvisvgm')


    def import_svg(self):
        """Import the SVG Equation file into Current layer"""

        svg_uri = inkex.NSS['svg']
        xlink_uri = inkex.NSS['xlink']
        
        if self.debug:
            logging.debug('import_svg():\n'+self.svg+'\n')
            
        try:
            ## parsing self.svg from file:
            tree = inkex.etree.parse(StringIO(self.svg))
            eq_tree = tree.getroot()
            if self.debug:
                logging.debug('SVG file imported from parse')
        except:
            if self.debug:
                logging.debug('SVG file not imported')
            sys.exit('Problem to import svg string/file')

        # Collect document ids
        doc_ids = {}
        docIdNodes = self.document.xpath('//@id')

        for m in docIdNodes:
            doc_ids[m] = 1

        name = "equation_%d" % time.time()

        # Create new group node containing the equation
        eqn = inkex.etree.Element('{%s}%s' % (svg_uri, 'g'))
        eqn.set('id', name)
        eqn.set('style', 'fill: black; stroke: none;')
        eqn.set('title', self.formula)
        eqn.set('x', str(self.view_center[0]))
        eqn.set('y', str(self.view_center[1]))
        
        dicnode = {}
        counter = 0

        # Get the Ids from <defs/>
        # And make unique Ids from name and counter
        for elt in eq_tree:
            if elt.tag == ('{%s}%s' % (svg_uri,'defs')):
                for subelt in elt:
                    dicnode[subelt.get('id')] = subelt
                    counter += 1
        
        xlink = '{%s}%s' % (xlink_uri, 'href')
        for elt in eq_tree:
            if elt.tag == ('{%s}%s' % (svg_uri, 'defs')):
                continue
            
            for subelt in elt:
                if xlink in subelt.attrib:
                    # <use> を参照
                    referred = dicnode[subelt.get(xlink).split('#')[-1]]
                    eqn_elt = inkex.etree.SubElement(eqn, referred.tag)

                    # x, y をコピーするため use の attributes をコピー
                    translate = ('translate(%s,%s)' % (subelt.get('x'), subelt.get('y')))
                    eqn_elt.set('transform', translate)
                    
                    # <path> の属性をコピー
                    for key in referred.keys():
                        if not 'id' in key:
                            eqn_elt.set(key, referred.attrib[key])
                    
                else:
                    # 元のノードをコピー
                    eqn_elt = inkex.etree.SubElement(eqn, subelt.tag)
                    for key in subelt.keys():
                        eqn_elt.set(key, subelt.attrib[key])

        self.svg = eqn

    def clean(self):
        """Clean all necessary file"""

        for ext in self.file_ext:
            try:
                os.unlink(os.path.join(self.temp_dir, self.file + ext))
                if self.debug:
                    logging.debug(self.file+ext+' file deleted')
            except:
                if self.debug:
                    logging.debug(self.file+ext+' file not deleted')
        try:
            os.rmdir(self.temp_dir)
            if self.debug:
                logging.debug(self.temp_dir+' is removed')
        except:
            if self.debug:
                logging.debug(self.temp_dir+'cannot be removed')


    def generate(self):
        """Generate SVG from LaTeX equation file"""

        self.path_programs('latex --version', True)
        self.path_programs('dvisvgm -V', True)

        self.generate_tex()
        self.generate_dvi()
        
        if self.latex and self.dvisvgm:# and False:
            self.process = True
            if self.debug:
                logging.debug('latex and dvisvgm process in use')
        else:
            if self.debug:
                logging.debug('No process in use!')
            sys.exit('No process in use!')

        self.generate_svg()
        
        self.import_svg()

        self.clean()
        
        return self.svg


class InsertEquation(inkex.Effect):
    """Insert LaTeX Equation into the current Inscape instance"""

    def __init__(self):
        
        f='$\lim_{n \\to \infty}\sum_{k=1}^n \\frac{1}{k^2}= \\frac{\pi^2}{6}$'

        inkex.Effect.__init__(self)
        self.OptionParser.add_option('-f', '--formule',
                        action='store', type='string', 
                        dest='formula', help='LaTeX formula',
                        default=f,)
        self.OptionParser.add_option("-p", "--packages",
                        action="store", type="string", 
                        dest="packages", help="Additional packages", 
                        default="",)
        self.OptionParser.add_option("-d", "--debug",
                        action="store", type="inkbool", 
                        dest="debug", help="Debug information",
                        default=False,)

    def effect(self):
        equation = Equation({ 'formula'  : self.options.formula,
                              'document' : self.document,
                              'packages' : self.options.packages,
                              'debug'    : self.options.debug,
                              'view_center' : self.view_center })
        
        debug = self.options.debug
        
        eq = equation.generate()

        if eq != None :
            self.current_layer.append(eq)
            if debug:
                logging.debug('Equation added to current layer')
        else:
            if debug:
                logging.debug('Equation not generated')
            inkex.debug('No Equation was generated\n')


if __name__ == "__main__":
    e = InsertEquation()
    e.affect()

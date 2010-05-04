#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import with_statement

__license__   = 'GPL v3'
__copyright__ = '2009, Kovid Goyal <kovid@kovidgoyal.net>'
__docformat__ = 'restructuredtext en'

import os, shutil, re
from urllib import unquote

from calibre.customize.conversion import OutputFormatPlugin
from calibre.ptempfile import TemporaryDirectory
from calibre.constants import __appname__, __version__
from calibre import guess_type, CurrentDir
from calibre.customize.conversion import OptionRecommendation
from calibre.constants import filesystem_encoding

from lxml import etree

block_level_tags = (
      'address',
      'body',
      'blockquote',
      'center',
      'dir',
      'div',
      'dl',
      'fieldset',
      'form',
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'hr',
      'isindex',
      'menu',
      'noframes',
      'noscript',
      'ol',
      'p',
      'pre',
      'table',
      'ul',
      )


class EPUBOutput(OutputFormatPlugin):

    name = 'EPUB Output'
    author = 'Kovid Goyal'
    file_type = 'epub'

    options = set([
        OptionRecommendation(name='extract_to',
            help=_('Extract the contents of the generated EPUB file to the '
                'specified directory. The contents of the directory are first '
                'deleted, so be careful.')),

        OptionRecommendation(name='dont_split_on_page_breaks',
            recommended_value=False, level=OptionRecommendation.LOW,
            help=_('Turn off splitting at page breaks. Normally, input '
                    'files are automatically split at every page break into '
                    'two files. This gives an output ebook that can be '
                    'parsed faster and with less resources. However, '
                    'splitting is slow and if your source file contains a '
                    'very large number of page breaks, you should turn off '
                    'splitting on page breaks.'
                )
        ),

        OptionRecommendation(name='flow_size', recommended_value=260,
            help=_('Split all HTML files larger than this size (in KB). '
                'This is necessary as most EPUB readers cannot handle large '
                'file sizes. The default of %defaultKB is the size required '
                'for Adobe Digital Editions.')
        ),

        OptionRecommendation(name='no_default_epub_cover', recommended_value=False,
            help=_('Normally, if the input file has no cover and you don\'t'
            ' specify one, a default cover is generated with the title, '
            'authors, etc. This option disables the generation of this cover.')
        ),

        OptionRecommendation(name='no_svg_cover', recommended_value=False,
            help=_('Do not use SVG for the book cover. Use this option if '
                'your EPUB is going to be used ona  device that does not '
                'support SVG, like the iPhone or the JetBook Lite. '
                'Without this option, such devices will display the cover '
                'as a blank page.')
        ),

        ])

    recommendations = set([('pretty_print', True, OptionRecommendation.HIGH)])

    NONSVG_TITLEPAGE_COVER = '''\
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
                <meta name="calibre:cover" content="true" />
                <title>Cover</title>
                <style type="text/css" title="override_css">
                    @page {padding: 0pt; margin:0pt}
                    body { text-align: center; padding:0pt; margin: 0pt; }
                    div { padding:0pt; margin: 0pt; }
                </style>
            </head>
            <body>
                <div>
                    <img src="%s" alt="cover" style="height: 100%%" />
                </div>
            </body>
        </html>
    '''

    TITLEPAGE_COVER = '''\
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
        <meta name="calibre:cover" content="true" />
        <title>Cover</title>
        <style type="text/css" title="override_css">
            @page {padding: 0pt; margin:0pt}
            body { text-align: center; padding:0pt; margin: 0pt; }
        </style>
    </head>
    <body>
        <svg version="1.1" xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink"
            width="100%%" height="100%%" viewBox="0 0 600 800"
            preserveAspectRatio="xMidYMid meet">
            <image width="600" height="800" xlink:href="%s"/>
        </svg>
    </body>
</html>
'''

    def workaround_webkit_quirks(self):
        from calibre.ebooks.oeb.base import XPath
        for x in self.oeb.spine:
            root = x.data
            body = XPath('//h:body')(root)
            if body:
                body = body[0]

            if not hasattr(body, 'xpath'):
                continue

            for pre in XPath('//h:pre')(body):
                if not pre.text and len(pre) == 0:
                    pre.tag = 'div'

    def convert(self, oeb, output_path, input_plugin, opts, log):
        self.log, self.opts, self.oeb = log, opts, oeb

        self.workaround_ade_quirks()
        self.workaround_webkit_quirks()
        from calibre.ebooks.oeb.transforms.rescale import RescaleImages
        RescaleImages()(oeb, opts)

        from calibre.ebooks.oeb.transforms.split import Split
        split = Split(not self.opts.dont_split_on_page_breaks,
                max_flow_size=self.opts.flow_size*1024
                )
        split(self.oeb, self.opts)

        self.insert_cover()

        self.workaround_sony_quirks()

        from calibre.ebooks.oeb.base import OPF
        identifiers = oeb.metadata['identifier']
        uuid = None
        for x in identifiers:
            if x.get(OPF('scheme'), None).lower() == 'uuid' or unicode(x).startswith('urn:uuid:'):
                uuid = unicode(x).split(':')[-1]
                break
        if uuid is None:
            self.log.warn('No UUID identifier found')
            from uuid import uuid4
            uuid = str(uuid4())
            oeb.metadata.add('identifier', uuid, scheme='uuid', id=uuid)

        with TemporaryDirectory('_epub_output') as tdir:
            from calibre.customize.ui import plugin_for_output_format
            oeb_output = plugin_for_output_format('oeb')
            oeb_output.convert(oeb, tdir, input_plugin, opts, log)
            opf = [x for x in os.listdir(tdir) if x.endswith('.opf')][0]
            self.condense_ncx([os.path.join(tdir, x) for x in os.listdir(tdir)\
                    if x.endswith('.ncx')][0])
            encrypted_fonts = getattr(input_plugin, 'encrypted_fonts', [])
            encryption = None
            if encrypted_fonts:
                encryption = self.encrypt_fonts(encrypted_fonts, tdir, uuid)

            from calibre.ebooks.epub import initialize_container
            epub = initialize_container(output_path, os.path.basename(opf))
            epub.add_dir(tdir)
            if encryption is not None:
                epub.writestr('META-INF/encryption.xml', encryption)
            if opts.extract_to is not None:
                if os.path.exists(opts.extract_to):
                    shutil.rmtree(opts.extract_to)
                os.mkdir(opts.extract_to)
                epub.extractall(path=opts.extract_to)
                self.log.info('EPUB extracted to', opts.extract_to)
            epub.close()

    def encrypt_fonts(self, uris, tdir, uuid):
        from binascii import unhexlify

        key = re.sub(r'[^a-fA-F0-9]', '', uuid)
        if len(key) < 16:
            raise ValueError('UUID identifier %r is invalid'%uuid)
        key = unhexlify((key + key)[:32])
        key = tuple(map(ord, key))
        paths = []
        with CurrentDir(tdir):
            paths = [os.path.join(*x.split('/')) for x in uris]
            uris = dict(zip(uris, paths))
            fonts = []
            for uri in list(uris.keys()):
                path = uris[uri]
                if isinstance(path, unicode):
                    path = path.encode(filesystem_encoding)
                if not os.path.exists(path):
                    uris.pop(uri)
                    continue
                self.log.debug('Encrypting font:', uri)
                with open(path, 'r+b') as f:
                    data = f.read(1024)
                    f.seek(0)
                    for i in range(1024):
                        f.write(chr(ord(data[i]) ^ key[i%16]))
                if not isinstance(uri, unicode):
                    uri = uri.decode('utf-8')
                fonts.append(u'''
                <enc:EncryptedData>
                    <enc:EncryptionMethod Algorithm="http://ns.adobe.com/pdf/enc#RC"/>
                    <enc:CipherData>
                    <enc:CipherReference URI="%s"/>
                    </enc:CipherData>
                </enc:EncryptedData>
                '''%(uri.replace('"', '\\"')))
            if fonts:
                    ans = '''<encryption
                    xmlns="urn:oasis:names:tc:opendocument:xmlns:container"
                    xmlns:enc="http://www.w3.org/2001/04/xmlenc#"
                    xmlns:deenc="http://ns.adobe.com/digitaleditions/enc">
                    '''
                    ans += (u'\n'.join(fonts)).encode('utf-8')
                    ans += '\n</encryption>'
                    return ans

    def default_cover(self):
        '''
        Create a generic cover for books that dont have a cover
        '''
        from calibre.utils.pil_draw import draw_centered_text
        from calibre.ebooks.metadata import authors_to_string
        if self.opts.no_default_epub_cover:
            return None
        self.log('Generating default cover')
        m = self.oeb.metadata
        title = unicode(m.title[0])
        authors = [unicode(x) for x in m.creator if x.role == 'aut']

        import cStringIO
        cover_file = cStringIO.StringIO()
        try:
            try:
                from PIL import Image, ImageDraw, ImageFont
                Image, ImageDraw, ImageFont
            except ImportError:
                import Image, ImageDraw, ImageFont
            font_path = P('fonts/liberation/LiberationSerif-Bold.ttf')
            app = '['+__appname__ +' '+__version__+']'

            COVER_WIDTH, COVER_HEIGHT = 590, 750
            img = Image.new('RGB', (COVER_WIDTH, COVER_HEIGHT), 'white')
            draw = ImageDraw.Draw(img)
            # Title
            font = ImageFont.truetype(font_path, 44)
            bottom = draw_centered_text(img, draw, font, title, 15, ysep=9)
            # Authors
            bottom += 14
            font = ImageFont.truetype(font_path, 32)
            authors = authors_to_string(authors)
            bottom = draw_centered_text(img, draw, font, authors, bottom, ysep=7)
            # Vanity
            font = ImageFont.truetype(font_path, 28)
            width, height = draw.textsize(app, font=font)
            left = max(int((COVER_WIDTH - width)/2.), 0)
            top = COVER_HEIGHT - height - 15
            draw.text((left, top), app, fill=(0,0,0), font=font)
            # Logo
            logo = Image.open(I('library.png'), 'r')
            width, height = logo.size
            left = max(int((COVER_WIDTH - width)/2.), 0)
            top = max(int((COVER_HEIGHT - height)/2.), 0)
            img.paste(logo, (left, max(bottom, top)))
            img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE)

            img.convert('RGB').save(cover_file, 'JPEG')
            cover_file.flush()
            id, href = self.oeb.manifest.generate('cover_image', 'cover_image.jpg')
            item = self.oeb.manifest.add(id, href, guess_type('t.jpg')[0],
                        data=cover_file.getvalue())
            m.clear('cover')
            m.add('cover', item.id)

            return item.href
        except:
            self.log.exception('Failed to generate default cover')
        return None


    def insert_cover(self):
        from calibre.ebooks.oeb.base import urldefrag
        from calibre import guess_type
        g, m = self.oeb.guide, self.oeb.manifest
        item = None
        if 'titlepage' not in g:
            if 'cover' in g:
                href = g['cover'].href
            else:
                href = self.default_cover()
            if href is not None:
                templ = self.NONSVG_TITLEPAGE_COVER if self.opts.no_svg_cover \
                        else self.TITLEPAGE_COVER
                tp = templ%unquote(href)
                id, href = m.generate('titlepage', 'titlepage.xhtml')
                item = m.add(id, href, guess_type('t.xhtml')[0],
                        data=etree.fromstring(tp))
        else:
            item = self.oeb.manifest.hrefs[
                    urldefrag(self.oeb.guide['titlepage'].href)[0]]
        if item is not None:
            self.oeb.spine.insert(0, item, True)
            if 'cover' not in self.oeb.guide.refs:
                self.oeb.guide.add('cover', 'Title Page', 'a')
            self.oeb.guide.refs['cover'].href = item.href
            if 'titlepage' in self.oeb.guide.refs:
                self.oeb.guide.refs['titlepage'].href = item.href

    def condense_ncx(self, ncx_path):
        if not self.opts.pretty_print:
            tree = etree.parse(ncx_path)
            for tag in tree.getroot().iter(tag=etree.Element):
                if tag.text:
                    tag.text = tag.text.strip()
                if tag.tail:
                    tag.tail = tag.tail.strip()
            compressed = etree.tostring(tree.getroot(), encoding='utf-8')
            open(ncx_path, 'wb').write(compressed)

    def workaround_ade_quirks(self):
        '''
        Perform various markup transforms to get the output to render correctly
        in the quirky ADE.
        '''
        from calibre.ebooks.oeb.base import XPath, XHTML, OEB_STYLES, barename, urlunquote

        stylesheet = None
        for item in self.oeb.manifest:
            if item.media_type.lower() in OEB_STYLES:
                stylesheet = item
                break

        # ADE cries big wet tears when it encounters an invalid fragment
        # identifier in the NCX toc.
        frag_pat = re.compile(r'[-A-Za-z0-9_:.]+$')
        for node in self.oeb.toc.iter():
            href = getattr(node, 'href', None)
            if hasattr(href, 'partition'):
                base, _, frag = href.partition('#')
                frag = urlunquote(frag)
                if frag and frag_pat.match(frag) is None:
                    self.log.warn(
                            'Removing invalid fragment identifier %r from TOC'%frag)
                    node.href = base

        for x in self.oeb.spine:
            root = x.data
            body = XPath('//h:body')(root)
            if body:
                body = body[0]

            if hasattr(body, 'xpath'):
                # remove <img> tags with empty src elements
                bad = []
                for x in XPath('//h:img')(body):
                    src = x.get('src', '').strip()
                    if src in ('', '#') or src.startswith('http:'):
                        bad.append(x)
                for img in bad:
                    img.getparent().remove(img)

                # Add id attribute to <a> tags that have name
                for x in XPath('//h:a[@name]')(body):
                    if not x.get('id', False):
                        x.set('id', x.get('name'))

                # Replace <br> that are children of <body> as ADE doesn't handle them
                for br in XPath('./h:br')(body):
                    if br.getparent() is None:
                        continue
                    try:
                        prior = br.itersiblings(preceding=True).next()
                        priortag = barename(prior.tag)
                        priortext = prior.tail
                    except:
                        priortag = 'body'
                        priortext = body.text
                    if priortext:
                        priortext = priortext.strip()
                    br.tag = XHTML('p')
                    br.text = u'\u00a0'
                    style = br.get('style', '').split(';')
                    style = filter(None, map(lambda x: x.strip(), style))
                    style.append('margin:0pt; border:0pt')
                    # If the prior tag is a block (including a <br> we replaced)
                    # then this <br> replacement should have a 1-line height.
                    # Otherwise it should have no height.
                    if not priortext and priortag in block_level_tags:
                        style.append('height:1em')
                    else:
                        style.append('height:0pt')
                    br.set('style', '; '.join(style))

            for tag in XPath('//h:embed')(root):
                tag.getparent().remove(tag)
            for tag in XPath('//h:object')(root):
                if tag.get('type', '').lower().strip() in ('image/svg+xml',):
                    continue
                tag.getparent().remove(tag)

            for tag in XPath('//h:title|//h:style')(root):
                if not tag.text:
                    tag.getparent().remove(tag)
            for tag in XPath('//h:script')(root):
                if not tag.text and not tag.get('src', False):
                    tag.getparent().remove(tag)
            for tag in XPath('//h:body/descendant::h:script')(root):
                tag.getparent().remove(tag)

            for tag in XPath('//h:form')(root):
                tag.getparent().remove(tag)

            for tag in XPath('//h:center')(root):
                tag.tag = XHTML('div')
                tag.set('style', 'text-align:center')
            # ADE can't handle &amp; in an img url
            for tag in XPath('//h:img[@src]')(root):
                tag.set('src', tag.get('src', '').replace('&', ''))

            special_chars = re.compile(u'[\u200b\u00ad]')
            for elem in root.iterdescendants():
                if getattr(elem, 'text', False):
                    elem.text = special_chars.sub('', elem.text)
                    elem.text = elem.text.replace(u'\u2011', '-')
                if getattr(elem, 'tail', False):
                    elem.tail = special_chars.sub('', elem.tail)
                    elem.tail = elem.tail.replace(u'\u2011', '-')

            if stylesheet is not None:
                # ADE doesn't render lists correctly if they have left margins
                from cssutils.css import CSSRule
                for lb in XPath('//h:ul[@class]|//h:ol[@class]')(root):
                    sel = '.'+lb.get('class')
                    for rule in stylesheet.data.cssRules.rulesOfType(CSSRule.STYLE_RULE):
                        if sel == rule.selectorList.selectorText:
                            val = rule.style.removeProperty('margin-left')
                            pval = rule.style.getProperty('padding-left')
                            if val and not pval:
                                rule.style.setProperty('padding-left', val)

        if stylesheet is not None:
            stylesheet.data.add('a { color: inherit; text-decoration: inherit; '
                    'cursor: default; }')
            stylesheet.data.add('a[href] { color: blue; '
                    'text-decoration: underline; cursor:pointer; }')
        else:
            self.oeb.log.warn('No stylesheet found')


    def workaround_sony_quirks(self):
        '''
        Perform toc link transforms to alleviate slow loading.
        '''
        from calibre.ebooks.oeb.base import urldefrag, XPath

        def frag_is_at_top(root, frag):
            body = XPath('//h:body')(root)
            if body:
                body = body[0]
            else:
                return False
            tree = body.getroottree()
            elem = XPath('//*[@id="%s" or @name="%s"]'%(frag, frag))(root)
            if elem:
                elem = elem[0]
            else:
                return False
            path = tree.getpath(elem)
            for el in body.iterdescendants():
                epath = tree.getpath(el)
                if epath == path:
                    break
                if el.text and el.text.strip():
                    return False
                if not path.startswith(epath):
                    # Only check tail of non-parent elements
                    if el.tail and el.tail.strip():
                        return False
            return True

        def simplify_toc_entry(toc):
            if toc.href:
                href, frag = urldefrag(toc.href)
                if frag:
                    for x in self.oeb.spine:
                        if x.href == href:
                            if frag_is_at_top(x.data, frag):
                                self.log.debug('Removing anchor from TOC href:',
                                        href+'#'+frag)
                                toc.href = href
                            break
            for x in toc:
                simplify_toc_entry(x)

        if self.oeb.toc:
            simplify_toc_entry(self.oeb.toc)

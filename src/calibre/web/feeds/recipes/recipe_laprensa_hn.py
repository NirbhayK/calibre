#!/usr/bin/env  python

__license__   = 'GPL v3'
__copyright__ = '2009, Darko Miletic <darko.miletic at gmail.com>'
'''
www.laprensahn.com
'''

from calibre.web.feeds.news import BasicNewsRecipe
from calibre.ebooks.BeautifulSoup import BeautifulSoup, Tag

class LaPrensaHn(BasicNewsRecipe):
    title                 = 'La Prensa - Honduras'
    __author__            = 'Darko Miletic'
    description           = 'Noticias de Honduras y mundo'
    publisher             = 'La Prensa'
    category              = 'news, politics, Honduras'
    oldest_article        = 2
    max_articles_per_feed = 100
    use_embedded_content  = False
    no_stylesheets        = True
    remove_javascript     = True
    encoding              = 'utf-8'
    language              = _('Spanish')
    lang                  = 'es-HN'
    direction             = 'ltr'
    
    html2lrf_options = [
                          '--comment', description
                        , '--category', category
                        , '--publisher', publisher
                        ]
    
    html2epub_options = 'publisher="' + publisher + '"\ncomments="' + description + '"\ntags="' + category + '"\npretty_print=True\noverride_css=" p {text-indent: 0cm; margin-top: 0em; margin-bottom: 0.5em} "' 

    remove_tags = [dict(name=['form','object','embed'])]

    keep_only_tags = [
                         dict(name='h1' , attrs={'class':'titulo1'})
                        ,dict(name='div', attrs={'class':['sumario11','hora','texto']})
                     ]

    feeds = [(u'Noticias', u'http://feeds.feedburner.com/laprensa_titulares')]

    def preprocess_html(self, soup):
        soup.html['lang'] = self.lang
        soup.html['dir' ] = self.direction
        mlang = Tag(soup,'meta',[("http-equiv","Content-Language"),("content",self.lang)])
        mcharset = Tag(soup,'meta',[("http-equiv","Content-Type"),("content","text/html; charset=utf-8")])
        soup.head.insert(0,mlang)
        soup.head.insert(1,mcharset)
        for item in soup.findAll(style=True):
            del item['style']
        return soup

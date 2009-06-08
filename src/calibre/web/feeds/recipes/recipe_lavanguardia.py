#!/usr/bin/env  python
# -*- coding: utf-8 -*-

__license__   = 'GPL v3'
__copyright__ = '2009, Darko Miletic <darko.miletic at gmail.com>'
'''
www.lavanguardia.es
'''

from calibre.web.feeds.news import BasicNewsRecipe
from calibre.ebooks.BeautifulSoup import Tag

class LaVanguardia(BasicNewsRecipe):
    title                 = 'La Vanguardia Digital'
    __author__            = 'Darko Miletic'
    description           = u'Noticias desde España'
    publisher             = 'La Vanguardia'
    category              = 'news, politics, Spain'
    oldest_article        = 2
    max_articles_per_feed = 100
    no_stylesheets        = True
    use_embedded_content  = False
    delay                 = 1
    encoding              = 'cp1252'
    language              = _('Spanish')
    direction             = 'ltr'

    html2lrf_options = [
                          '--comment'  , description
                        , '--category' , category
                        , '--publisher', publisher
                        ]

    html2epub_options  = 'publisher="' + publisher + '"\ncomments="' + description + '"\ntags="' + category + '"'

    feeds              = [
                            (u'Ciudadanos'           , u'http://feeds.feedburner.com/lavanguardia/ciudadanos'   )
                           ,(u'Cultura'              , u'http://feeds.feedburner.com/lavanguardia/cultura'      )
                           ,(u'Deportes'             , u'http://feeds.feedburner.com/lavanguardia/deportes'     )
                           ,(u'Economia'             , u'http://feeds.feedburner.com/lavanguardia/economia'     )
                           ,(u'El lector opina'      , u'http://feeds.feedburner.com/lavanguardia/lectoropina'  )
                           ,(u'Gente y TV'           , u'http://feeds.feedburner.com/lavanguardia/gente'        )
                           ,(u'Internacional'        , u'http://feeds.feedburner.com/lavanguardia/internacional')
                           ,(u'Internet y tecnologia', u'http://feeds.feedburner.com/lavanguardia/internet'     )
                           ,(u'Motor'                , u'http://feeds.feedburner.com/lavanguardia/motor'        )
                           ,(u'Politica'             , u'http://feeds.feedburner.com/lavanguardia/politica'     )
                           ,(u'Sucessos'             , u'http://feeds.feedburner.com/lavanguardia/sucesos'      )
                         ]


    keep_only_tags = [
                       dict(name='div', attrs={'class':'element1_3'})
                     ]

    remove_tags        = [
                             dict(name=['object','link','script'])
                            ,dict(name='div', attrs={'class':['colC','peu']})
                         ]

    remove_tags_after = [dict(name='div', attrs={'class':'text'})]

    def preprocess_html(self, soup):
        soup.html['dir' ] = self.direction
        mcharset = Tag(soup,'meta',[("http-equiv","Content-Type"),("content","text/html; charset=utf-8")])
        soup.head.insert(0,mcharset)
        for item in soup.findAll(style=True):
            del item['style']
        return soup


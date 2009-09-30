#!/usr/bin/env  python

__license__   = 'GPL v3'
__copyright__ = '2009, Rick Kellogg'
'''
Infoworld.com
'''

from calibre.web.feeds.news import BasicNewsRecipe

class Engadget(BasicNewsRecipe):
    title                 = u'Infoworld.com'
    __author__            = 'Rick Kellogg'
    description           = 'news'
    language = 'en'
    oldest_article        = 7
    max_articles_per_feed = 100
    no_stylesheets        = True
    use_embedded_content  = False

    remove_tags =   [ dict(name='div', attrs={'class':["articleTools clearfix","relatedContent","pagination clearfix","addResources"]}),
		      dict(name='div', attrs={'id':["post-socialPromoBlock"]})]

    keep_only_tags = [dict(name='div', attrs={'class':["article"]})]

    feeds = [ (u'Top Tech Stories', u'http://infoworld.com/homepage/feed'),
              (u'Today\'s Tech Headlines', u'http://www.infoworld.com/news/feed') ]

    def get_article_url(self, article):

        url = article.get('link', None)

        return url



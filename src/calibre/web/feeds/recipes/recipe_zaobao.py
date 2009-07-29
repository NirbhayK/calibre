#!/usr/bin/env  python

__license__   = 'GPL v3'
__copyright__ = '2009, Pu Bo <pubo at pubolab.com>'
'''
zaobao.com
'''
from calibre.web.feeds.news import BasicNewsRecipe
from calibre.web.feeds import feeds_from_index

class ZAOBAO(BasicNewsRecipe):
    title          = u'\u8054\u5408\u65e9\u62a5\u7f51 zaobao.com'
    __author__     = 'Pu Bo'
    description    = 'News from zaobao.com'
    no_stylesheets = True
    recursions     = 1
    language = _('Chinese')
    encoding     = 'gbk'
#    multithreaded_fetch = True

    keep_only_tags    = [
						dict(name='table', attrs={'cellpadding':'9'}),
						dict(name='table', attrs={'class':'cont'}),
						dict(name='div', attrs={'id':'content'}),
						dict(name='span', attrs={'class':'page'}),
					]

    remove_tags    = [
						dict(name='table', attrs={'cellspacing':'9'}),
					]

    extra_css      = '\
            @font-face {font-family: "serif1";src:url(res:///opt/sony/ebook/FONT/tt0011m_.ttf)}\n\
            body{font-family: serif1, serif}\n\
            .article_description{font-family: serif1, serif}\n\
            p{font-family: serif1, serif}\n\
            h1 {font-weight: bold; font-size: large;}\n\
            h2 {font-size: large;}\n\
            .title {font-size: large;}\n\
            .article {font-size:medium}\n\
            .navbar {font-size: small}\n\
            .feed{font-size: medium}\n\
			.small{font-size: small; padding-right: 8%}\n'

    INDEXES		   = [
                       (u'\u65b0\u95fb\u56fe\u7247', u'http://www.zaobao.com/photoweb/photoweb_idx.shtml')
                    ]
    MAX_ITEMS_IN_INDEX = 10

    DESC_SENSE     = u'\u8054\u5408\u65e9\u62a5\u7f51'

    feeds          = [
                      (u'\u5373\u65f6\u62a5\u9053', u'http://realtime.zaobao.com/news.xml'),
					  (u'\u4e2d\u56fd\u65b0\u95fb', u'http://www.zaobao.com/zg/zg.xml'),
					  (u'\u56fd\u9645\u65b0\u95fb', u'http://www.zaobao.com/gj/gj.xml'),
					  (u'\u4e16\u754c\u62a5\u520a\u6587\u8403', u'http://www.zaobao.com/wencui/wencui.xml'),
                      (u'\u4e1c\u5357\u4e9a\u65b0\u95fb', u'http://www.zaobao.com/yx/yx.xml'),
                      (u'\u65b0\u52a0\u5761\u65b0\u95fb', u'http://www.zaobao.com/sp/sp.xml'),
                      (u'\u4eca\u65e5\u89c2\u70b9', u'http://www.zaobao.com/yl/yl.xml'),
                      (u'\u4e2d\u56fd\u8d22\u7ecf', u'http://www.zaobao.com/cz/cz.xml'),
                      (u'\u72ee\u57ce\u8d22\u7ecf', u'http://www.zaobao.com/cs/cs.xml'),
                      (u'\u5168\u7403\u8d22\u7ecf', u'http://www.zaobao.com/cg/cg.xml'),
                      (u'\u65e9\u62a5\u4f53\u80b2', u'http://www.zaobao.com/ty/ty.xml'),
                      (u'\u65e9\u62a5\u526f\u520a', u'http://www.zaobao.com/fk/fk.xml'),
                    ]

    def postprocess_html(self, soup, first):
        for tag in soup.findAll(name=['table', 'tr', 'td']):
            tag.name = 'div'
        return soup

    def parse_feeds(self):
        self.log.debug('ZAOBAO overrided parse_feeds()')
        parsed_feeds = BasicNewsRecipe.parse_feeds(self)

        for id, obj in enumerate(self.INDEXES):
            title, url = obj
            articles = []
            soup = self.index_to_soup(url)

            for i, item in enumerate(soup.findAll('li')):
                if i >= self.MAX_ITEMS_IN_INDEX:
                    break
                a = item.find('a')
                if a and a.has_key('href'):
                    a_url = a['href']
                    a_title = self.tag_to_string(a)
                    date = ''
                    description = ''
                    self.log.debug('adding %s at %s'%(a_title,a_url))
                    articles.append({
                                    'title':a_title,
                                    'date':date,
                                    'url':a_url,
                                    'description':description
                                    })

            pfeeds = feeds_from_index([(title, articles)], oldest_article=self.oldest_article,
                                     max_articles_per_feed=self.max_articles_per_feed)

            self.log.debug('adding %s to feed'%(title))
            for feed in pfeeds:
                self.log.debug('adding feed: %s'%(feed.title))
                feed.description = self.DESC_SENSE
                parsed_feeds.append(feed)
                for a, article in enumerate(feed):
                    self.log.debug('added article %s from %s'%(article.title, article.url))
                self.log.debug('added feed %s'%(feed.title))

        for i, feed in enumerate(parsed_feeds):
            # workaorund a strange problem: Somethimes the xml encoding is not apllied correctly by parse()
            weired_encoding_detected = False
            if not isinstance(feed.description, unicode) and self.encoding and feed.description:
                self.log.debug('Feed %s is not encoded correctly, manually replace it'%(feed.title))
                feed.description = feed.description.decode(self.encoding, 'replace')
            elif feed.description.find(self.DESC_SENSE) == -1 and self.encoding and feed.description:
                self.log.debug('Feed %s is strangely encoded, manually redo all'%(feed.title))
                feed.description = feed.description.encode('cp1252', 'replace').decode(self.encoding, 'replace')
                weired_encoding_detected = True

            for a, article in enumerate(feed):
                if not isinstance(article.title, unicode) and self.encoding:
                    article.title = article.title.decode(self.encoding, 'replace')
                if not isinstance(article.summary, unicode) and self.encoding and article.summary:
                    article.summary = article.summary.decode(self.encoding, 'replace')
                    article.text_summary = article.summary
                if not isinstance(article.text_summary, unicode) and self.encoding and article.text_summary:
                    article.text_summary = article.text_summary.decode(self.encoding, 'replace')
                    article.summary = article.text_summary
                if weired_encoding_detected:
                    if article.title:
                        article.title = article.title.encode('cp1252', 'replace').decode(self.encoding, 'replace')
                    if article.summary:
                        article.summary = article.summary.encode('cp1252', 'replace').decode(self.encoding, 'replace')
                    if article.text_summary:
                        article.text_summary = article.text_summary.encode('cp1252', 'replace').decode(self.encoding, 'replace')

                if article.title == "Untitled article":
                    self.log.debug('Removing empty article %s from %s'%(article.title, article.url))
                    # remove the article
                    feed.articles[a:a+1] = []
        return parsed_feeds

    def get_browser(self):
        br = BasicNewsRecipe.get_browser()
        br.addheaders.append(('Pragma', 'no-cache'))
        return br

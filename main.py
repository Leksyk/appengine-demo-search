import webapp2

import jinja2

import traceback

from google.appengine.api import urlfetch
from google.appengine.api import search

from lxml import etree


env = jinja2.Environment(loader=jinja2.FileSystemLoader("templates"))


class MainHandler(webapp2.RequestHandler):
    def _render(self):
        q = self.request.get('q')
        if q:
            index = search.Index('search')
            results = index.search(q)
            urls = [r.doc_id for r in results]
        else:
            urls = []
        tmpl = env.get_template('search.html')
        self.response.out.write(tmpl.render(results=urls, q=q))

    def get(self):
        self._render()

    def post(self):
        self._render()


class IndexHandler(webapp2.RequestHandler):

    LINKS = [
        'https://developers.google.com/appengine/docs/python/gettingstartedpython27/introduction',
        'https://developers.google.com/appengine/docs/quotas',
        'https://developers.google.com/appengine/pricing',
        'https://developers.google.com',
        'https://developers.google.com/groups/',
        'https://support.google.com/chrome/answer/1181035?hl=en&ref_topic=3421437',
        'https://support.google.com/adwords/answer/1722066?hl=en&ref_topic=3121936',
        'https://support.google.com/googleplay/answer/2843119?hl=en&ref_topic=3237689',
    ]

    def featchAsync(self, url):
        rpc = urlfetch.create_rpc(5.0)
        urlfetch.make_fetch_call(rpc, url)
        return url, rpc

    def extractKeywords(self, text):
        html = etree.HTML(text)
        keywords = set()
        for elem in html.iter():
            if elem.tag != 'script':
                text = elem.text
                if text:
                    for keyword in text.split():
                        keywords.add(keyword)
        return keywords

    def updateIndex(self, url, keywords):
        doc = search.Document(
            doc_id=url,
            fields=[search.TextField(name='text', value=value) for value in keywords])
        index = search.Index(name="search")
        index.put(doc)

    def get(self):
        try:
            rpcs = [self.featchAsync(link) for link in self.LINKS]
            for url, rpc in rpcs:
                rpc.wait()
                result = rpc.get_result()
                if result.status_code == 200:
                    keywords = self.extractKeywords(result.content)
                    self.updateIndex(url, keywords)
        except:
            self.response.out.write(traceback.format_exc())


app = webapp2.WSGIApplication([
    ('/index', IndexHandler),
    ('/', MainHandler),
], debug=True)

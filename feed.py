#!/usr/bin/env python3
from lxml import etree as ET
import datetime
import itertools
import requests
import typing
import wsgiref.util

# constants
APP_NAME = 'solidarity.tech syndicator'
APP_URI = 'https://github.com/nuew/solidarity_tech_syndicator'
APP_VERSION = '0.0.0'
NS_ATOM = 'http://www.w3.org/2005/Atom'
MIME_ATOM = 'application/atom+xml'
MIME_HTML = 'text/html'
MIME_URI_LIST = 'text/uri-list'

# premade atom XML-namespaced tags
ATOM_AUTHOR = ET.QName(NS_ATOM, 'author')
ATOM_CONTENT = ET.QName(NS_ATOM, 'content')
ATOM_EMAIL = ET.QName(NS_ATOM, 'email')
ATOM_ENTRY = ET.QName(NS_ATOM, 'entry')
ATOM_FEED = ET.QName(NS_ATOM, 'feed')
ATOM_GENERATOR = ET.QName(NS_ATOM, 'generator')
ATOM_HREF = ET.QName(NS_ATOM, 'href')
ATOM_ICON = ET.QName(NS_ATOM, 'icon')
ATOM_ID = ET.QName(NS_ATOM, 'id')
ATOM_LINK = ET.QName(NS_ATOM, 'link')
ATOM_NAME = ET.QName(NS_ATOM, 'name')
ATOM_PUBLISHED = ET.QName(NS_ATOM, 'published')
ATOM_REL = ET.QName(NS_ATOM, 'rel')
ATOM_SRC = ET.QName(NS_ATOM, 'src')
ATOM_SUMMARY = ET.QName(NS_ATOM, 'summary')
ATOM_TITLE = ET.QName(NS_ATOM, 'title')
ATOM_TYPE = ET.QName(NS_ATOM, 'type')
ATOM_UPDATED = ET.QName(NS_ATOM, 'updated')
ATOM_URI = ET.QName(NS_ATOM, 'uri')
ATOM_VERSION = ET.QName(NS_ATOM, 'version')


class Person:
    """An Atom person construct; not necessarily a natural person, might be a
    'corporation, or similar entity'"""

    def __init__(self, name: str, uri: str = None, email: str = None):
        self.name = name
        self.uri = uri
        self.email = email

    def atom(self, tag: QName) -> ET.Element:
        '''Generate the specified Atom element corresponding to this person'''
        person = ET.Element(tag)

        # Person's associated name; is not optional
        ET.SubElement(person, ATOM_NAME).text = self.name

        # Person's associated URI; is optional
        if self.uri is not None:
            ET.SubElement(person, ATOM_URI).text = self.uri

        # Person's email; is optional
        if self.email is not None:
            ET.SubElement(person, ATOM_EMAIL).text = self.email

        return person

    # this is a seperate function as a person can also be a contributor, which
    # is represented with a sepereate element. we don't use that here, though
    def author_atom(self) -> ET.Element:
        '''Generate the Atom Author element corresponding to this Person'''
        return self.atom(ATOM_AUTHOR)


class Post:
    '''A solidarity.tech blog post to be converted to a Atom entry'''

    def __init__(self,
                 url: str,
                 title: str,
                 summary: str,
                 published: datetime.datetime,
                 updated: Optional[datetime.datetime] = None):
        self.url = url
        self.title = title
        self.summary = summary
        self.published = published
        self.updated = updated if updated is not None else published

    def fromElement(post: ET.Element):
        url = post.get('href')
        title = post.find(".//h4[@class='pb-blog-post-title']").text.strip()
        summary = post.find(
            ".//div[@class='pb-blog-post-excerpt']").text.strip()
        published = post.find(".//span[@class='pb-blog-post-date']/time").get(
            'datetime')
        return Post(url, title, summary,
                    datetime.datetime.fromisoformat(published))

    def atom(self) -> ET.Element:
        '''Generate an Atom entry corresponding to this Post'''
        entry = ET.Element(ATOM_ENTRY)
        ET.SubElement(entry, ATOM_ID).text = self.url
        ET.SubElement(entry, ATOM_TITLE).text = self.title
        ET.SubElement(entry, ATOM_PUBLISHED).text = self.published.isoformat()
        ET.SubElement(entry, ATOM_UPDATED).text = self.published.isoformat()
        ET.SubElement(entry, ATOM_LINK, attrib={
            'rel': 'alternate'
        }).text = self.url
        ET.SubElement(entry,
                      ATOM_CONTENT,
                      attrib={
                          'type': MIME_HTML,
                          'src': self.url
                      })
        ET.SubElement(entry, ATOM_SUMMARY).text = self.summary

        return entry


class Feed:
    '''A solidarity.tech blog to create an Atom feed for'''

    def __init__(self, url: str):
        self.url = url
        # we need a timezone here to avoid TypeErrors
        self.updated = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc)

    def _update(self):
        '''Update feed if we last updated at least an hour ago'''
        if self.updated <= (datetime.datetime.now(datetime.timezone.utc) -
                            datetime.timedelta(hours=1)):
            self._scrape()

    def _scrape(self):
        '''Scrape Solidarity.Tech blog page'''

        # get and parse webpage
        r = requests.get(
            self.url,
            headers={'User-Agent': f'{APP_NAME}/{APP_VERSION} ({APP_URI})'})
        html = ET.fromstring(r.text, ET.HTMLParser())

        # extract data
        self.updated = datetime.datetime.now(datetime.timezone.utc)
        self.title = html.find("./head/title").text.strip()
        self.author = Person(
            html.find(".//span[@data-pb-field='website_name']").text.strip(),
            html.find(".//a[@class='pb-nav-logo-link']").get('href'))
        self.icon = html.find("./head/link[@rel='icon']").get('href')
        self.posts = [
            Post.fromElement(p)
            for p in html.iterfind(".//a[@class='pb-blog-post-card']")
        ]

    def atom(self, self_uri: str) -> bytes:
        self._update()  # make sure feed is reasonably up to date
        feed = ET.Element(ATOM_FEED, nsmap={None: NS_ATOM})

        # feed generator (for branding and debug)
        ET.SubElement(feed,
                      ATOM_GENERATOR,
                      attrib={
                          'uri': APP_URI,
                          'version': APP_VERSION
                      }).text = (APP_NAME)

        # atom id, which for us is just the target url
        ET.SubElement(feed, ATOM_ID).text = self.url

        # feed update time
        ET.SubElement(feed, ATOM_UPDATED).text = self.updated.isoformat()

        # link to ourselves (the RFC recommends this for one-click subscriptions)
        ET.SubElement(feed,
                      ATOM_LINK,
                      attrib={
                          'rel': 'self',
                          'type': MIME_ATOM,
                          'href': self_uri
                      })

        # link to original resource
        ET.SubElement(
            feed,
            ATOM_LINK,
            attrib={
                'rel': 'alternate',
                'type': MIME_HTML,
                'href': self.url
            },
        )

        # feed title and author
        ET.SubElement(feed, ATOM_TITLE).text = self.title
        feed.append(self.author.author_atom())

        # optional 1x1 aspect ratio icon (logo provides 2x1, but we don't implement it)
        if self.icon is not None:
            ET.SubElement(feed, ATOM_ICON).text = self.icon

        # all posts as atom entries
        feed.extend(entry.atom() for entry in self.posts)

        return ET.tostring(feed, encoding='utf-8')


feeds = {'posts.xml': Feed('https://demo.solidarity.tech/posts')}


def app(environ, start_response):
    path = environ['PATH_INFO'][1:]
    if path in feeds:  # show feed
        atom = feeds[path].atom(wsgiref.util.request_uri(environ))
        start_response('200 OK', [('Content-Type', MIME_ATOM)])
        return [atom]
    elif len(path) == 0:  # show list of feeds as a URI list for default index
        start_response('200 OK', [('Content-Type', MIME_URI_LIST)])
        app = wsgiref.util.application_uri(environ)
        brand = f'# {APP_NAME} {APP_VERSION} <{APP_URI}>\r\n'
        urls = (f'{app}{feed}\r\n' for feed in feeds.keys())
        return (t.encode('utf-8') for t in itertools.chain(brand, urls))
    else:
        start_response('404 Not Found', [])
        return []


from wsgiref.simple_server import make_server
with make_server('', 8080, app) as httpd:
    httpd.serve_forever()

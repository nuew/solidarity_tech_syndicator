#!/usr/bin/env python3
from lxml import etree as ET
from typing import Callable, Optional
import config
import datetime as dt
import itertools
import requests
import wsgiref.util

# constants
APP_NAME = 'solidarity.tech syndicator'
APP_URI = 'https://github.com/nuew/solidarity_tech_syndicator'
APP_VERSION = '0.0.0'
MIME_ATOM = 'application/atom+xml'
MIME_HTML = 'text/html'
MIME_URI_LIST = 'text/uri-list'
NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_XML = 'http://www.w3.org/XML/1998/namespace'

USER_AGENT = f'{APP_NAME}/{APP_VERSION} ({APP_URI})'
REQUESTS_HEADERS = {'User-Agent': USER_AGENT, 'From': config.OPERATOR_EMAIL}

# premade XML-namespaced tags
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
XML_BASE = f'{NS_XML}base'  # namespaced attributes must be defined like this for typing reasons


def getTextContent(e: ET._Element) -> Optional[str]:
    '''Returns stripped text if available'''
    return e.text.strip() if e.text is not None else None


def getByPath(
    rel: ET._Element,
    selector: str,
    f: Callable[[ET._Element],
                Optional[str]] = getTextContent) -> Optional[str]:
    '''A gross and poor attempt at simulating monads for this one use case'''
    elem = rel.find(selector)
    return f(elem) if elem is not None else None


class Person:
    """An Atom person construct; not necessarily a natural person, might be a
    'corporation, or similar entity'"""

    def __init__(self,
                 name: str,
                 uri: Optional[str] = None,
                 email: Optional[str] = None):
        self.name = name
        self.uri = uri
        self.email = email

    def atom(self, tag: ET.QName) -> ET._Element:
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
    def author_atom(self) -> ET._Element:
        '''Generate the Atom Author element corresponding to this Person'''
        return self.atom(ATOM_AUTHOR)


class Post:
    '''A solidarity.tech blog post to be converted to a Atom entry'''

    def __init__(self,
                 url: str,
                 title: Optional[str],
                 summary: Optional[str],
                 published: Optional[dt.datetime],
                 updated: Optional[dt.datetime] = None):
        self.url = url
        self.title = title
        self.summary = summary
        self.published = published
        self.updated = updated if updated is not None else published

    @staticmethod
    def _publishedTime(post: ET._Element) -> Optional[dt.datetime]:
        '''parse publication datetime, either with strptime from element
           content or by attribute from an HTML time element'''
        published_elem = post.find(config.XPATH_POST_DATETIME)
        if published_elem is None:
            pass  # published should stay as None
        elif config.DATETIME_STRPTIME is not None:  # we have to parse a prose date
            published_content = getTextContent(published_elem)
            published_dt = dt.datetime.strptime(
                published_content, config.DATETIME_STRPTIME
            ) if published_content is not None else None
        else:  # we are extracting from a <time> element
            published_dt = dt.datetime.fromisoformat(
                published_elem.get('datetime'))

        # ensure that all datetimes have a timezone, even if we have to guess
        if published_dt is not None and published_dt.tzinfo is None:
            published_dt = published_dt.replace(
                tzinfo=config.DATETIME_DEFAULT_TZ)

        return published_dt

    @staticmethod
    def fromElement(post: ET._Element) -> Optional[Post]:
        '''Creates a Post class from an element on a page of posts'''

        url = getByPath(post, config.XPATH_POST_LINK, lambda e: e.get('href'))
        title = getByPath(post, config.XPATH_POST_TITLE)
        summary = getByPath(post, config.XPATH_POST_SUMMARY)
        published = Post._publishedTime(post)

        if url is None:  # at this point there's little point in trying to continue
            return None
        else:
            return Post(url, title, summary, published)

    def atom(self) -> ET._Element:
        '''Generate an Atom entry corresponding to this Post'''
        entry = ET.Element(ATOM_ENTRY)
        ET.SubElement(entry, ATOM_ID).text = self.url
        ET.SubElement(entry, ATOM_TITLE).text = self.title
        ET.SubElement(entry, ATOM_LINK, rel='alternate', href=self.url)

        if self.published is not None:
            date_str = self.published.isoformat()
            ET.SubElement(entry, ATOM_PUBLISHED).text = date_str

        if self.updated is not None:
            ET.SubElement(entry, ATOM_UPDATED).text = self.updated.isoformat()
        else:
            ET.SubElement(entry, ATOM_UPDATED).text = dt.datetime.now(
                config.DATETIME_DEFAULT_TZ).isoformat()

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
        self.updated = dt.datetime(1, 1, 1, tzinfo=config.DATETIME_DEFAULT_TZ)

    def _update(self):
        '''Update feed if we last updated at least an hour ago'''
        if self.updated <= (dt.datetime.now(config.DATETIME_DEFAULT_TZ) -
                            config.SCRAPE_REFRESH):
            self._scrape()

    def _scrape(self):
        '''Scrape Solidarity.Tech blog page'''

        # get and parse webpage
        r = requests.get(self.url, headers=REQUESTS_HEADERS)
        html = ET.fromstring(r.text, ET.HTMLParser())

        # extract data
        self.updated = dt.datetime.now(config.DATETIME_DEFAULT_TZ)
        self.title = getByPath(html, config.XPATH_TITLE)
        self.author = Person(  # the author; URL and Email are optional
            getByPath(html, config.XPATH_AUTHOR_NAME),
            getByPath(html, config.XPATH_AUTHOR_URL, lambda e: e.get('href'))
            if config.XPATH_AUTHOR_URL is not None else None,
            getByPath(html, config.XPATH_AUTHOR_EMAIL)
            if config.XPATH_AUTHOR_EMAIL is not None else None)
        self.icon = getByPath(html, config.XPATH_ICON, lambda e: e.get('href'))
        self.posts = [
            Post.fromElement(p) for p in html.iterfind(config.XPATH_POSTS)
        ]

    def atom(self, self_uri: str) -> bytes:
        self._update()  # make sure feed is reasonably up to date
        feed = ET.Element(
            ATOM_FEED,
            attrib={XML_BASE: self.url},
            nsmap={
                None: NS_ATOM,  # type: ignore[dict-item]
                'xml': NS_XML
            })

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


# global singleton containing all feeds and their internal caches
feeds = {path: Feed(feed) for path, feed in config.FEEDS.items()}


def app(environ, start_response):
    path = environ['PATH_INFO'][1:]
    if path in feeds:  # show feed
        atom = feeds[path].atom(wsgiref.util.request_uri(environ))
        start_response('200 OK', [('Content-Type', MIME_ATOM)])
        return [atom]
    elif len(path) == 0:  # show list of feeds as a URI list for default index
        start_response('200 OK', [('Content-Type', MIME_URI_LIST)])
        app = wsgiref.util.application_uri(environ)
        brand = f'# {USER_AGENT}\r\n'
        urls = (f'{app}{feed}\r\n' for feed in feeds.keys())
        return (t.encode('utf-8') for t in itertools.chain(brand, urls))
    else:
        start_response('404 Not Found', [])
        return []


if __name__ == "__main__":
    from wsgiref.simple_server import make_server
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    host = sys.argv[2] if len(sys.argv) > 2 else ''
    with make_server(host, port, app) as httpd:
        httpd.serve_forever()

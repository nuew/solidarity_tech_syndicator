#!/usr/bin/env python3
from lxml import etree as ET
from typing import Callable, Optional
import config
import datetime as dt
import lxml.html
import requests
import urllib.parse

# constants
APP_NAME = 'solidarity.tech syndicator'
APP_URI = 'https://github.com/nuew/solidarity_tech_syndicator'
APP_VERSION = '0.0.0'
MIME_ATOM = 'application/atom+xml'
MIME_HTML = 'text/html'
MIME_URI_LIST = 'text/uri-list'
NS_ATOM = 'http://www.w3.org/2005/Atom'
NS_XHTML = 'http://www.w3.org/1999/xhtml'

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
        self.contents = None
        self.published = published
        self.updated = updated if updated is not None else published

    @staticmethod
    def _publishedTime(post: ET._Element) -> Optional[dt.datetime]:
        '''parse publication datetime, either with strptime from element
           content or by attribute from an HTML time element'''
        published_elem = post.find("./div/div/span[@class='mr-20 italics']")

        published_content = getTextContent(
            published_elem) if published_elem is not None else None
        published_dt = dt.datetime.strptime(
            published_content,
            "%b %d, %Y") if published_content is not None else None

        # ensure that all datetimes have a timezone, even if we have to guess
        if published_dt is not None and published_dt.tzinfo is None:
            published_dt = published_dt.replace(tzinfo=config.DEFAULT_TZ)
        return published_dt

    @staticmethod
    def fromElement(post: ET._Element) -> Optional[Post]:
        '''Creates a Post class from an element on a page of posts'''

        url = getByPath(post, "./div/div/a[.='Read More']",
                        lambda e: e.get('href'))
        title = getByPath(post, "./div/div[@class='posts--title']")
        summary = getByPath(post, "./div/div[@class='posts--subtitle']")
        published = Post._publishedTime(post)

        if url is None:  # at this point there's little point in trying to continue
            return None
        else:
            return Post(url, title, summary, published)

    def scrape(self):
        '''Get the actual contents of the post from solidarity.tech'''
        # get and parse webpage
        r = requests.get(self.url, headers=REQUESTS_HEADERS)
        html = ET.fromstring(r.text, ET.HTMLParser())

        # update the updated time
        self.updated = dt.datetime.now(config.DEFAULT_TZ)

        # extract body text as an lxml Element, converting that to XHTML, and parenting it under
        # a new element so that we can have a new default xml namespace (at the cost of an
        # individual xmlns="{NS_XHTML}" for every entry)
        body = html.find(config.XPATH_POST_CONTENTS)
        lxml.html.html_to_xhtml(body)
        self.contents = ET.Element(body.tag,
                                   attrib=body.attrib,
                                   nsmap={None:
                                          NS_XHTML})  # type: ignore[dict-item]
        self.contents.extend(body.iterchildren())

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
                config.DEFAULT_TZ).isoformat()

        if self.contents is None:
            ET.SubElement(entry,
                          ATOM_CONTENT,
                          attrib={
                              'type': MIME_HTML,
                              'src': self.url
                          })
        else:
            content = ET.SubElement(entry,
                                    ATOM_CONTENT,
                                    attrib={'type': 'xhtml'})
            content.append(self.contents)
            content.base = self.url
        ET.SubElement(entry, ATOM_SUMMARY).text = self.summary

        return entry


class Feed:
    '''A solidarity.tech blog to create an Atom feed for'''

    def __init__(self, posts: {str: Post}, url: str):
        self.url = url

        # get and parse webpage
        r = requests.get(self.url, headers=REQUESTS_HEADERS)
        html = ET.fromstring(r.text, ET.HTMLParser())

        # extract metadata
        self.updated = dt.datetime.now(config.DEFAULT_TZ)
        self.title = getByPath(html, "./head/title")
        self.author = Person(  # the author; URL and Email are optional
            getByPath(html, ".//a[@class='navbar-brand']/span"),
            getByPath(html, ".//a[@class='navbar-brand']",
                      lambda e: e.get('href')), config.FEED_AUTHOR_EMAIL)
        self.icon = getByPath(html, "./head/link[@rel='icon']",
                              lambda e: e.get('href'))

        # extract posts
        scraped_posts = [
            Post.fromElement(p)
            for p in html.iterfind(".//div[@class='posts--section']")
        ]
        posts.update({post.url: post for post in scraped_posts})
        self.posts = [post.url for post in scraped_posts]

    def atom(self, posts: {str: Post}, self_uri: str) -> bytes:
        feed = ET.Element(ATOM_FEED,
                          nsmap={None: NS_ATOM})  # type: ignore[dict-item]
        feed.base = self.url

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
        feed.extend(posts[url].atom() for url in self.posts)

        return ET.tostring(feed, encoding='utf-8')


if __name__ == "__main__":
    posts = {}  # all posts, to avoid scraping duplicates multiple times
    feeds = {
        path:
        Feed(
            posts, config.SITE + '/posts' +
            (f'?category={urllib.parse.quote(tag)}' if tag is not None else ''))
        for path, tag in config.FEEDS.items()
    }

    # scrape all posts, if enabled
    if config.SCRAPE_POST_CONTENTS:
        for url, post in posts.items():
            post.scrape()

    # output all feeds
    for i, (path, feed) in enumerate(feeds.items()):
        # output feed
        with open(f'{config.OUTPUT_DIR}/{path}', 'wb') as f:
            f.write(feed.atom(posts, f'{config.OUTPUT_CANONICAL}/{path}'))

        # output the first feed's icon as 'favicon.ico'; some feed readers use this
        # (and only this) as their icon for the feed
        if i == 0 and feed.icon is not None:
            r = requests.get(feed.icon, headers=REQUESTS_HEADERS)
            with open(f'{config.OUTPUT_DIR}/favicon.ico', 'wb') as f:
                f.write(r.content)

#!/usr/bin/env python3
# This is the configuration file for the solidarity.tech syndicator.
import datetime

# A dictionary of all feeds
FEEDS = {"posts.xml": "https://demo.solidarity.tech/posts"}

# A dictionary of 302 redirects; primarily intended for favicons and temporarily moved feeds
# If a feed and a redirect conflict, the feed wins.
REDIRECTS = {'favicon.ico': 'https://s3.amazonaws.com/solidarity.tech/image_uploads/images/000/017/948/original/RackMultipart20230727-22-gjmx0j.png'}

# Operator Email; will be included in 'From' HTTP header on requests (optional)
OPERATOR_EMAIL = None

# Should we also scrape the contents of posts for a fuller feed, or just use solidarity.tech's summary?
SCRAPE_POST_CONTENTS = True

# How often to refresh the feed cache
SCRAPE_REFRESH = datetime.timedelta(hours=1)

# How often to refresh post bodies; this might be less often than refreshing the posts list
SCRAPE_REFRESH_POST_BODIES = SCRAPE_REFRESH

# Root-relative XPath for the title of the feed
XPATH_TITLE = "./head/title"

# Root-relative XPath for the name of the author of the feed
XPATH_AUTHOR_NAME = ".//a[@class='navbar-brand']/span"

# Root-relative XPath for the URL of the author of the feed (optional; href attribute)
XPATH_AUTHOR_URL = ".//a[@class='navbar-brand']"

# Root-relative XPath for the email of the author of the feed (optional)
XPATH_AUTHOR_EMAIL = None

# Root-relative XPath for the feed icon (href attribute)
XPATH_ICON = "./head/link[@rel='icon']"

# Root-relative XPath for every post to be put in the feed
XPATH_POSTS = ".//div[@class='posts--section']"

# Post-relative XPath for the URL of the post (href attribute)
XPATH_POST_LINK = "./div/div/a[.='Read More']"

# Post-relative XPath for the title of the post
XPATH_POST_TITLE = "./div/div[@class='posts--title']"

# Post-relative XPath for the post's summary
XPATH_POST_SUMMARY = "./div/div[@class='posts--subtitle']"

# Root-relative XPath for the element containing the post body on the post's individual page
XPATH_POST_CONTENTS = ".//div[@class='mb-30']"

# Post-relative XPath for the publication datetime of the post
XPATH_POST_DATETIME = "./div/div/span[@class='mr-20 italics']"

# Strptime format to parse datetime; if set to None, will use `datetime` attribute of the selected
# element instead
DATETIME_STRPTIME = "%b %d, %Y"

# If no timezone is specified, which should be assigned as a defualt? This is required for strict
# RFC conformance
DATETIME_DEFAULT_TZ = datetime.timezone.utc

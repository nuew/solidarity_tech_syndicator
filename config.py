#!/usr/bin/env python3
# This is the configuration file for the solidarity.tech syndicator.
import datetime

# All attributes not included in this set will be filtered out of post <content>.
# This default is all elements, except 'class', specified as allowed by
# https://validator.w3.org/feed/docs/warning/SecurityRiskAttr.html
ALLOWLIST_ATTRIBUTES = set([
    'abbr', 'accept', 'accept-charset', 'accesskey', 'action', 'align', 'alt',
    'axis', 'border', 'cellpadding', 'cellspacing', 'char', 'charoff',
    'charset', 'checked', 'cite', 'clear', 'cols', 'colspan', 'color',
    'compact', 'coords', 'datetime', 'dir', 'disabled', 'enctype', 'for',
    'frame', 'headers', 'height', 'href', 'hreflang', 'hspace', 'id', 'ismap',
    'label', 'lang', 'longdesc', 'maxlength', 'media', 'method', 'multiple',
    'name', 'nohref', 'noshade', 'nowrap', 'prompt', 'readonly', 'rel', 'rev',
    'rows', 'rowspan', 'rules', 'scope', 'selected', 'shape', 'size', 'span',
    'src', 'srcset', 'start', 'summary', 'tabindex', 'target', 'title', 'type',
    'usemap', 'valign', 'value', 'vspace', 'width'
])

# All elements not included in this set will be filtered out of post <content>.
# This default is all elements, except 'class', specified as acceptable by
# https://github.com/w3c/feedvalidator/blob/main/src/feedvalidator/validators.py
ALLOWLIST_ELEMENTS = set([
    'a', 'abbr', 'acronym', 'address', 'area', 'article', 'aside', 'audio',
    'b', 'bdi', 'big', 'blockquote', 'br', 'button', 'canvas', 'caption',
    'center', 'cite', 'code', 'col', 'colgroup', 'command', 'data', 'datagrid',
    'datalist', 'dd', 'del', 'details', 'dfn', 'dialog', 'dir', 'div', 'dl',
    'dt', 'em', 'eventsource', 'fieldset', "figcaption", 'figure', 'footer',
    'font', 'form', 'header', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hgroup',
    'hr', 'i', 'img', 'input', 'ins', 'keygen', 'kbd', 'label', 'legend', 'li',
    'm', 'main', 'map', 'mark', 'menu', 'meter', 'multicol', 'nav', 'nextid',
    'ol', 'output', 'optgroup', 'option', 'p', 'picture', 'pre', 'progress',
    'q', 'rp', 'rt', 'ruby', 's', 'samp', 'section', 'select', 'small',
    'sound', 'source', 'spacer', 'span', 'strike', 'strong', 'sub', 'summary',
    'sup', 'table', 'tbody', 'td', 'template', 'textarea', 'time', 'tfoot',
    'th', 'thead', 'tr', 'track', 'tt', 'u', 'ul', 'var', 'video', 'noscript',
    'wbr'
])

# Page cache database location; `None` to disable
CACHE = "./cache.db"

# Time until a cache entry expires.
CACHE_EXPIRY = datetime.timedelta(weeks=1)

# If no timezone is specified, which should be assigned as a defualt? This is required for strict
# RFC conformance
DEFAULT_TZ = datetime.timezone.utc

# Generate a .htaccess redirecting the favicon instead of downloading and serving a copy
FAVICON_HTACCESS = False

# A dictionary of all feeds and the tags they syndicate; `None` syndicates all posts
FEEDS = {"posts.atom": None, "energy_campaign.atom": "Energy Campaign"}

# Email of the author of the feed (optional)
FEED_AUTHOR_EMAIL = None

# Operator Email; will be included in 'From' HTTP header on requests (optional)
OPERATOR_EMAIL = None

# The canonical URL that corresponds to the root of the output website directory
OUTPUT_CANONICAL = "http://localhost"

# The path to the root of the output website directory
OUTPUT_DIR = "/tmp"

# Should we also scrape the contents of posts for a fuller feed, or just use solidarity.tech's summary?
SCRAPE_POST_CONTENTS = True

# The site to syndicate
SITE = "https://demo.solidarity.tech"

# Root-relative XPath for the element containing the post body on the post's individual page
XPATH_POST_CONTENTS = ".//div[@class='mb-30']"

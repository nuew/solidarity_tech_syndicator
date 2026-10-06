#!/usr/bin/env python3
# This is the configuration file for the solidarity.tech syndicator.
import datetime

# If no timezone is specified, which should be assigned as a defualt? This is required for strict
# RFC conformance
DEFAULT_TZ = datetime.timezone.utc

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

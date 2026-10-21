
import scrapy

from scrapy.spiders import SitemapSpider
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class PhoenixSitemapSpider(SitemapSpider):

    name = "phoenix_sitemap"

    allowed_domains = ["www.fnx.co.il"]

    sitemap_urls = [
        "https://www.fnx.co.il/sitemap.xml"
    ]

    sitemap_rules = [
        (
            r"^https://www\.fnx\.co\.il/",
            "parse_page"
        )
    ]

    custom_settings = {
        # Respect website crawling rules
        "ROBOTSTXT_OBEY": True,

        # Crawl slowly and politely
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,

        # Save progress to disk
        "JOBDIR": str(BASE_DIR / "crawl_job"),

        # Append results to a JSON Lines file
        "FEEDS": {
            str(BASE_DIR / "results_full.jsonl"): {
                "format": "jsonlines",
                "encoding": "utf-8",
                "overwrite": False,
            }
        },

        "LOG_LEVEL": "INFO",

        # Identify our crawler
        "USER_AGENT": (
            "PhoenixRAG-HackathonBot/1.0 "
            "(educational research crawler)"
        ),
    }

    def parse_page(self, response):

        title = response.css("title::text").get(
            default=""
        ).strip()

        main = response.css("main")

        if not main:
            main = response.css("body")

        content = []

        for element in main.css(
            "h1, h2, h3, p, li"
        ):

            element_type = element.root.tag

            text = " ".join(
                element.css("::text").getall()
            ).strip()

            text = " ".join(text.split())

            if not text:
                continue

            content.append({
                "type": element_type,
                "text": text,
            })

        yield {
            "url": response.url,
            "title": title,
            "content": content,
            "element_count": len(content),
        }

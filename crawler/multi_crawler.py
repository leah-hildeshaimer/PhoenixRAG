
import scrapy
from scrapy.crawler import CrawlerProcess


class PhoenixMultiSpider(scrapy.Spider):
    name = "phoenix_multi"

    allowed_domains = ["fnx.co.il"]

    start_urls = [
        "https://www.fnx.co.il/car-insurance/"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CLOSESPIDER_PAGECOUNT": 20,
        "LOG_LEVEL": "INFO",
        "FEEDS": {
            "results_multi.json": {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,
                "indent": 2
            }
        }
    }

    def parse(self, response):
        # Extract content from the current page
        main = response.css("main")

        if not main:
            main = response.css("body")

        elements = main.css("h1, h2, h3, p, li")

        content = []

        for element in elements:
            tag = element.root.tag

            text = " ".join(
                part.strip()
                for part in element.css("::text").getall()
                if part.strip()
            )

            if text:
                content.append({
                    "type": tag,
                    "text": text
                })

        yield {
            "url": response.url,
            "title": response.css("title::text").get(),
            "content": content,
            "element_count": len(content)
        }

        # Discover links to additional pages
        links = response.css("a::attr(href)").getall()

        for link in links:
            absolute_url = response.urljoin(link)

            # Crawl only pages under fnx.co.il
            if absolute_url.startswith(
                "https://www.fnx.co.il/"
            ):
                yield response.follow(
                    absolute_url,
                    callback=self.parse
                )


process = CrawlerProcess()
process.crawl(PhoenixMultiSpider)
process.start()

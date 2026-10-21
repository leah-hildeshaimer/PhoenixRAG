
import scrapy
from scrapy.crawler import CrawlerProcess


class PhoenixSpider(scrapy.Spider):
    name = "phoenix_test"

    allowed_domains = ["fnx.co.il"]

    start_urls = [
        "https://www.fnx.co.il/car-insurance/"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "LOG_LEVEL": "ERROR",
        "FEEDS": {
            "results.json": {
                "format": "json",
                "encoding": "utf8",
                "overwrite": True,
                "indent": 2,
            }
        },
    }

   
    def parse(self, response):
        title = response.css("title::text").get()

        # Find the main content area
        main = response.css("main")
        if not main:
            main = response.css("body")

        # Extract headings, paragraphs and list items
        elements = main.css("h1, h2, h3, p, li")

        content = []

        for element in elements:
            tag = element.root.tag

            text = " ".join(
                part.strip()
                for part in element.css("::text").getall()
                if part.strip()
            )

            if not text:
                continue

            content.append({
                "type": tag,
                "text": text
            })

        yield {
            "url": response.url,
            "title": title,
            "content": content,
            "element_count": len(content)
        }



process = CrawlerProcess()
process.crawl(PhoenixSpider)
process.start()

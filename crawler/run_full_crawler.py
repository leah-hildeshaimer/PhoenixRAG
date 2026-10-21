
from scrapy.crawler import CrawlerProcess

from sitemap_crawler import PhoenixSitemapSpider


def main():
    process = CrawlerProcess()

    process.crawl(PhoenixSitemapSpider)

    process.start()


if __name__ == "__main__":
    main()

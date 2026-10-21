
import requests
from bs4 import BeautifulSoup

URL = "https://www.fnx.co.il/SPF/ifram-finanacial-reports-gemel-main.aspx"

response = requests.get(
    URL,
    timeout=30,
    headers={
        "User-Agent": "PhoenixRAG-HackathonBot/1.0"
    }
)

print("HTTP STATUS:", response.status_code)
print("FINAL URL:", response.url)

if response.status_code != 200:
    print("Could not read iframe content.")
    raise SystemExit

soup = BeautifulSoup(response.text, "html.parser")

print("\n=== IFRAME STRUCTURE ===")
print("Tables:", len(soup.select("table")))
print("Links:", len(soup.select("a[href]")))
print("PDF links:", len(soup.select('a[href*=".pdf"]')))
print("Nested iframes:", len(soup.select("iframe")))

print("\n=== TEXT SAMPLE ===")
print(soup.get_text(" ", strip=True)[:2000])

print("\n=== FIRST 10 LINKS ===")
for link in soup.select("a[href]")[:10]:
    print("TEXT:", link.get_text(" ", strip=True))
    print("URL:", link.get("href"))
    print("---")

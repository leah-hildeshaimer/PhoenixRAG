
import requests
from bs4 import BeautifulSoup

URL = "https://www.fnx.co.il/gemel/gemel-kupa-financial-reports/"

response = requests.get(
    URL,
    timeout=30,
    headers={
        "User-Agent": "PhoenixRAG-HackathonBot/1.0"
    }
)

print("HTTP STATUS:", response.status_code)

if response.status_code != 200:
    print("Page could not be inspected.")
    raise SystemExit

soup = BeautifulSoup(response.text, "html.parser")

print("\n=== PAGE STRUCTURE ===")
print("Tables:", len(soup.select("table")))
print("PDF links:", len(soup.select('a[href*=".pdf"]')))
print("All links:", len(soup.select("a")))
print("Iframes:", len(soup.select("iframe")))
print("Scripts:", len(soup.select("script")))

print("\n=== SAMPLE PDF LINKS ===")

for link in soup.select('a[href*=".pdf"]')[:10]:
    print("TEXT:", link.get_text(" ", strip=True))
    print("URL:", link.get("href"))
    print("---")

print("\n=== MAIN TEXT SAMPLE ===")

main = soup.select_one("main")

if main:
    print(main.get_text(" ", strip=True)[:1500])
else:
    print("No main element found.")



print("\n=== IFRAMES ===")

for index, iframe in enumerate(soup.select("iframe"), start=1):
    print(f"\nIframe {index}")
    print("SRC:", iframe.get("src"))
    print("ID:", iframe.get("id"))
    print("TITLE:", iframe.get("title"))
    print("CLASS:", iframe.get("class"))

print("\n=== MAIN HTML SAMPLE ===")

if main:
    print(str(main)[:3000])

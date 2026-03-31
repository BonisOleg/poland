import requests
import json
import os
import time
import sys
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

sys.stdout.reconfigure(line_buffering=True)

BASE_URL = "https://hypeglobal.pro"
API_URL = f"{BASE_URL}/wp-json/wp/v2"
OUTPUT_DIR = "scraped_data"
MEDIA_DIR = os.path.join(OUTPUT_DIR, "media")
PER_PAGE = 100
DELAY = 0.3


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(MEDIA_DIR, exist_ok=True)


def fetch_all_paginated(endpoint, params=None):
    if params is None:
        params = {}
    params["per_page"] = PER_PAGE
    page = 1
    all_items = []

    while True:
        params["page"] = page
        url = f"{API_URL}/{endpoint}"
        print(f"  [{endpoint}] page {page}...", end=" ")
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 400:
                print("no more pages")
                break
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: {e}")
            break

        data = resp.json()
        if not data:
            print("empty")
            break

        total = resp.headers.get("X-WP-Total", "?")
        total_pages = resp.headers.get("X-WP-TotalPages", "?")
        print(f"got {len(data)} items (total: {total}, pages: {total_pages})")

        all_items.extend(data)

        if total_pages != "?" and page >= int(total_pages):
            break
        page += 1
        time.sleep(DELAY)

    return all_items


def extract_seo_from_html(url):
    seo = {}
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        if resp.status_code != 200:
            return seo
        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.find("title")
        if title_tag:
            seo["title"] = title_tag.get_text(strip=True)

        for meta in soup.find_all("meta"):
            name = meta.get("name", "") or meta.get("property", "")
            content = meta.get("content", "")
            if name and content:
                seo[name] = content

        canonical = soup.find("link", rel="canonical")
        if canonical:
            seo["canonical"] = canonical.get("href", "")

        for script in soup.find_all("script", type="application/ld+json"):
            try:
                seo["schema_json_ld"] = json.loads(script.string)
            except (json.JSONDecodeError, TypeError):
                pass

        hreflang_links = soup.find_all("link", attrs={"hreflang": True})
        if hreflang_links:
            seo["hreflang"] = [
                {"lang": l.get("hreflang"), "href": l.get("href")}
                for l in hreflang_links
            ]

    except Exception as e:
        seo["_error"] = str(e)
    return seo


def process_page(page_data):
    slug = page_data.get("slug", "")
    link = page_data.get("link", "")

    result = {
        "id": page_data.get("id"),
        "slug": slug,
        "link": link,
        "status": page_data.get("status"),
        "title": page_data.get("title", {}).get("rendered", ""),
        "content_html": page_data.get("content", {}).get("rendered", ""),
        "excerpt": page_data.get("excerpt", {}).get("rendered", ""),
        "date": page_data.get("date"),
        "modified": page_data.get("modified"),
        "parent": page_data.get("parent", 0),
        "menu_order": page_data.get("menu_order", 0),
        "featured_media": page_data.get("featured_media", 0),
        "template": page_data.get("template", ""),
    }

    if "yoast_head_json" in page_data:
        result["yoast_seo"] = page_data["yoast_head_json"]
    elif "yoast_head" in page_data:
        result["yoast_head_raw"] = page_data["yoast_head"]

    return result


def process_media(media_data):
    source = media_data.get("source_url", "")
    sizes = {}
    details = media_data.get("media_details", {})
    for size_name, size_info in details.get("sizes", {}).items():
        if size_name == "full":
            sizes["full"] = size_info.get("source_url", source)

    return {
        "id": media_data.get("id"),
        "slug": media_data.get("slug", ""),
        "title": media_data.get("title", {}).get("rendered", ""),
        "alt_text": media_data.get("alt_text", ""),
        "caption": media_data.get("caption", {}).get("rendered", ""),
        "mime_type": media_data.get("mime_type", ""),
        "source_url": source,
        "full_url": sizes.get("full", source),
        "width": details.get("width"),
        "height": details.get("height"),
        "filesize": details.get("filesize"),
        "post_parent": media_data.get("post"),
    }


def scrape_pages():
    print("\n=== SCRAPING PAGES ===")
    raw_pages = fetch_all_paginated("pages")
    pages = [process_page(p) for p in raw_pages]
    save_json("pages.json", pages)
    print(f"  Total pages: {len(pages)}")
    return pages


def scrape_pages_seo(pages):
    print("\n=== SCRAPING SEO FROM HTML ===")
    seo_data = []
    total = len(pages)
    for i, page in enumerate(pages):
        link = page.get("link", "")
        if not link:
            continue
        print(f"  [{i+1}/{total}] {link}")
        seo = extract_seo_from_html(link)
        seo["page_id"] = page["id"]
        seo["slug"] = page["slug"]
        seo["url"] = link
        seo_data.append(seo)
        time.sleep(DELAY)

    save_json("pages_seo.json", seo_data)
    print(f"  Total SEO records: {len(seo_data)}")
    return seo_data


def scrape_media():
    print("\n=== SCRAPING MEDIA ===")
    raw_media = fetch_all_paginated("media")
    media = [process_media(m) for m in raw_media]
    save_json("media.json", media)
    print(f"  Total media: {len(media)}")
    return media


def scrape_categories():
    print("\n=== SCRAPING CATEGORIES ===")
    cats = fetch_all_paginated("categories")
    result = [{
        "id": c.get("id"),
        "name": c.get("name", ""),
        "slug": c.get("slug", ""),
        "description": c.get("description", ""),
        "parent": c.get("parent", 0),
        "count": c.get("count", 0),
        "link": c.get("link", ""),
    } for c in cats]
    save_json("categories.json", result)
    print(f"  Total categories: {len(result)}")
    return result


def scrape_tags():
    print("\n=== SCRAPING TAGS ===")
    tags = fetch_all_paginated("tags")
    result = [{
        "id": t.get("id"),
        "name": t.get("name", ""),
        "slug": t.get("slug", ""),
        "description": t.get("description", ""),
        "count": t.get("count", 0),
        "link": t.get("link", ""),
    } for t in tags]
    save_json("tags.json", result)
    print(f"  Total tags: {len(result)}")
    return result


def scrape_product_categories():
    print("\n=== SCRAPING PRODUCT CATEGORIES ===")
    try:
        cats = fetch_all_paginated("product_cat")
        result = [{
            "id": c.get("id"),
            "name": c.get("name", ""),
            "slug": c.get("slug", ""),
            "description": c.get("description", ""),
            "parent": c.get("parent", 0),
            "count": c.get("count", 0),
        } for c in cats]
        save_json("product_categories.json", result)
        print(f"  Total product categories: {len(result)}")
    except Exception as e:
        print(f"  Skipped: {e}")


def scrape_products_store_api():
    print("\n=== SCRAPING PRODUCTS (Store API) ===")
    url = f"{BASE_URL}/wp-json/wc/store/v1/products"
    all_products = []
    page = 1

    while True:
        print(f"  [products] page {page}...", end=" ")
        try:
            resp = requests.get(url, params={
                "per_page": PER_PAGE, "page": page
            }, timeout=30)
            if resp.status_code != 200:
                print(f"status {resp.status_code}")
                break
            data = resp.json()
            if not data:
                print("empty")
                break
            print(f"got {len(data)}")
            all_products.extend(data)
            page += 1
            time.sleep(DELAY)
        except Exception as e:
            print(f"ERROR: {e}")
            break

    if all_products:
        save_json("products.json", all_products)
        print(f"  Total products: {len(all_products)}")
    else:
        print("  No products found via Store API")


def scrape_menus():
    print("\n=== SCRAPING MENUS ===")
    endpoints = [
        f"{BASE_URL}/wp-json/wp/v2/menus",
        f"{BASE_URL}/wp-json/wp/v2/menu-items",
        f"{BASE_URL}/wp-json/menus/v1/menus",
    ]
    for ep in endpoints:
        print(f"  Trying: {ep}")
        try:
            resp = requests.get(ep, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    save_json("menus.json", data)
                    print(f"  Got menus: {len(data)} items")
                    return data
        except Exception:
            pass
    print("  No menu endpoints available, will extract from HTML")
    return extract_menu_from_html()


def extract_menu_from_html():
    try:
        resp = requests.get(BASE_URL, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        soup = BeautifulSoup(resp.text, "html.parser")
        nav = soup.find("nav") or soup.find(class_="menu") or soup.find("ul", class_=lambda x: x and "menu" in x)
        if not nav:
            return []

        menu_items = []
        for link in nav.find_all("a", href=True):
            menu_items.append({
                "title": link.get_text(strip=True),
                "url": link["href"],
                "classes": link.get("class", []),
            })
        save_json("menus.json", menu_items)
        print(f"  Extracted {len(menu_items)} menu items from HTML")
        return menu_items
    except Exception as e:
        print(f"  Menu extraction failed: {e}")
        return []


def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    size = os.path.getsize(path)
    print(f"  -> Saved {path} ({size // 1024} KB)")


def print_summary():
    print("\n" + "=" * 60)
    print("SCRAPING COMPLETE")
    print("=" * 60)
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if fname.endswith(".json"):
            path = os.path.join(OUTPUT_DIR, fname)
            with open(path, "r") as f:
                data = json.load(f)
            count = len(data) if isinstance(data, list) else 1
            size = os.path.getsize(path)
            print(f"  {fname}: {count} items ({size // 1024} KB)")


def main():
    ensure_dirs()
    print(f"Scraping {BASE_URL}")
    print(f"Output: {OUTPUT_DIR}/")

    pages = scrape_pages()
    scrape_media()
    scrape_categories()
    scrape_tags()
    scrape_product_categories()
    scrape_products_store_api()
    scrape_menus()

    has_yoast = any(p.get("yoast_seo") for p in pages)
    if not has_yoast:
        print("\n  Yoast not in API, falling back to HTML scraping...")
        scrape_pages_seo(pages)
    else:
        print(f"\n  Yoast SEO data found in API for {sum(1 for p in pages if p.get('yoast_seo'))} pages")

    print_summary()


if __name__ == "__main__":
    main()

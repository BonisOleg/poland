import requests
import json
import os
import time
import sys
from urllib.parse import urlparse

sys.stdout.reconfigure(line_buffering=True)

OUTPUT_DIR = "scraped_data"
MEDIA_DIR = os.path.join(OUTPUT_DIR, "media")
MEDIA_JSON = os.path.join(OUTPUT_DIR, "media.json")
DELAY = 0.3
SKIP_VIDEO = True
MAX_SIZE_MB = 50


def download_file(url, dest_path):
    try:
        resp = requests.get(url, stream=True, timeout=60, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        resp.raise_for_status()

        content_length = int(resp.headers.get("Content-Length", 0))
        if content_length > MAX_SIZE_MB * 1024 * 1024:
            return False, f"too large ({content_length // (1024*1024)} MB)"

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return True, os.path.getsize(dest_path)
    except Exception as e:
        return False, str(e)


def main():
    os.makedirs(MEDIA_DIR, exist_ok=True)

    if not os.path.exists(MEDIA_JSON):
        print(f"File {MEDIA_JSON} not found. Run scrape_wp.py first.")
        return

    with open(MEDIA_JSON, "r", encoding="utf-8") as f:
        media_list = json.load(f)

    print(f"Total media items: {len(media_list)}")

    downloaded = 0
    skipped = 0
    errors = 0

    for i, item in enumerate(media_list):
        url = item.get("source_url", "")
        mime = item.get("mime_type", "")

        if not url:
            continue

        if SKIP_VIDEO and mime.startswith("video/"):
            print(f"  [{i+1}/{len(media_list)}] SKIP video: {url}")
            skipped += 1
            continue

        parsed = urlparse(url)
        rel_path = parsed.path.lstrip("/")
        dest = os.path.join(MEDIA_DIR, rel_path)
        dest_dir = os.path.dirname(dest)
        os.makedirs(dest_dir, exist_ok=True)

        if os.path.exists(dest):
            print(f"  [{i+1}/{len(media_list)}] EXISTS: {rel_path}")
            skipped += 1
            continue

        print(f"  [{i+1}/{len(media_list)}] Downloading: {rel_path}...", end=" ")
        ok, info = download_file(url, dest)
        if ok:
            print(f"OK ({info // 1024} KB)")
            downloaded += 1
        else:
            print(f"FAIL: {info}")
            errors += 1

        time.sleep(DELAY)

    print(f"\nDone! Downloaded: {downloaded}, Skipped: {skipped}, Errors: {errors}")


if __name__ == "__main__":
    main()

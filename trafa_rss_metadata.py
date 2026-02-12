import os
import re
import csv
import logging
import requests
import feedparser
from datetime import datetime

# Configure logging.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def parse_date(date_value):
    """
    Parses date strings or datetime objects into "YYYY-MM-DD".
    """
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    if isinstance(date_value, str):
        try:
            # Try ISO format first.
            dt = datetime.fromisoformat(date_value)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
        # If the string starts with D: (PDF style), try to parse similarly.
        if date_value.startswith("D:"):
            d = date_value[2:]
            match = re.match(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", d)
            if match:
                try:
                    dt = datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    return date_value
        return date_value
    return "Unknown"

def sanitize_filename(name):
    """
    Sanitizes a string to be used as a filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def download_html(url, base_folder, year, filename_hint):
    """
    Downloads the HTML content of the given URL and saves it in:
    base_folder/year/sanitized_filename.html
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error downloading HTML from {url}: {e}")
        return None

    filename = sanitize_filename(filename_hint) + ".html"
    folder_path = os.path.join(base_folder, year)
    os.makedirs(folder_path, exist_ok=True)
    local_path = os.path.join(folder_path, filename)
    try:
        with open(local_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        logging.info(f"Saved HTML to {local_path}")
        return local_path
    except Exception as e:
        logging.error(f"Error saving HTML file {local_path}: {e}")
        return None

def process_rss_feed(feed_url):
    """
    Processes the RSS feed and extracts metadata from each feed item.
    Fields extracted:
      - Dokumentnamn: From the feed item's title.
      - Datum: From the feed item's published date (pubDate).
      - url: From the feed item's link.
    Also downloads the HTML of each feed item into a sorted folder structure.
    """
    feed = feedparser.parse(feed_url)
    items = []
    base_download_folder = "trafa_rss_downloads"
    for entry in feed.entries:
        dokumentnamn = entry.get("title", "N/A")
        raw_date = entry.get("published", "Unknown")
        datum = parse_date(raw_date)
        url = entry.get("link", feed_url)
        
        # Determine year folder
        year = datum.split("-")[0] if datum != "Unknown" else "unknown"
        local_path = download_html(url, base_download_folder, year, dokumentnamn)
        
        metadata = {
            "Dokumentnamn": dokumentnamn,
            "Datum": datum,
            "url": url,
            "LocalPath": local_path
        }
        items.append(metadata)
    logging.info(f"Processed {len(items)} items from RSS feed {feed_url}")
    return items

def main():
    rss_feed_url = "https://www.trafa.se/kb-rss/"
    items = process_rss_feed(rss_feed_url)
    
    output_file = "trafa_rss_metadata.csv"
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["Dokumentnamn", "Datum", "url", "LocalPath"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in items:
                writer.writerow(item)
        logging.info(f"RSS metadata written to {output_file}")
    except Exception as e:
        logging.error(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    main()

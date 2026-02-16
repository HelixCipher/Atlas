# Atlas

**Web-scraping toolkit for Swedish authorities. Automates data collection with pagination, PDF crawling, metadata extraction, and multi-format export.**

Atlas is a data collection toolkit designed to support Swedish government authorities in organizing and accessing their own public information. It automates the gathering of reports, statistics, and publications from agency websites, creating searchable, structured datasets.

## Overview

Atlas collects public data from Swedish authorities and organizes it into structured formats for easy analysis and search. Currently supports Tillväxtanalys (business analysis) and Trafikanalys (transport analysis) with custom-built scrapers. The architecture is designed with the goal of eventually scaling to 100+ authorities through a modular, extensible design.

## Current Capabilities

### Supported Authorities

- **Tillväxtanalys** - Business analysis reports and publications
- **Trafikanalys** - Transport statistics, reports, and datasets

### Features

- **Browser Automation** - Handles JavaScript-rendered pages and cookie consent dialogs using Playwright
- **Pagination Support** - Automatically navigates multi-page listings and "load more" buttons
- **PDF Crawler** - Recursively finds and downloads PDF documents with section-based organization
- **RSS Feed Parser** - Extracts metadata and downloads content from RSS feeds
- **Sitemap Processing** - Parses XML sitemaps to discover all published documents
- **Metadata Extraction** - Captures document IDs (Serienummer, Diarienummer), dates, titles, and descriptions
- **Duplicate Detection** - Prevents redundant downloads using checksums and URL uniqueness
- **Multi-Format Export** - Saves data to SQLite, Excel (XLSX), and CSV formats
- **Progress Tracking** - Visual progress bars for long-running operations
- **Debug Tools** - Saves HTML snapshots for troubleshooting parsing issues

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/HelixCipher/Atlas.git
cd Atlas
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

### Configuration

Before running, you need to configure which authorities to scrape:

1. Rename the example configuration file:
   ```bash
   cp example_urls.py urls.py
   ```

2. Edit `urls.py` and add the URLs of authorities you want to scrape:
   ```python
   URLS = [
       "https://www.tillvaxtanalys.se",
       "https://www.trafa.se"
   ]
   ```

**Note:** `urls.py` is gitignored to keep your specific configuration private.

## Usage

### Run All Scrapers

```bash
python main.py
```

This will execute all configured scrapers in sequence:
1. Tillväxtanalys web scraper (paginated listings)
2. Trafikanalys RSS feed parser
3. Trafikanalys sitemap crawler
4. PDF crawler for document discovery

### Individual Scrapers

Each scraper can be run independently:

```python
# Web scraper for Tillväxtanalys
from web_scraper import main as web_scraper
web_scraper()

# RSS metadata extractor
from trafa_rss_metadata import main as rss_scraper
rss_scraper()

# Sitemap crawler
from trafa_sitemap_metadata import main as sitemap_scraper
sitemap_scraper()

# PDF crawler
from pdf_crawler import main as pdf_crawler
pdf_crawler()
```

## Project Structure

```
Atlas/
├── chrome_path_helper.py      # Playwright Chromium path management
├── example_urls.py             # Example URL configuration (copy to urls.py)
├── main.py                     # Entry point - orchestrates all scrapers
├── pdf_crawler.py              # Recursive PDF discovery and download
├── requirements.txt            # Python dependencies
├── trafa_rss_metadata.py       # RSS feed parser
├── trafa_sitemap_metadata.py   # XML sitemap crawler
├── urls.py                     # URL configuration (gitignored)
├── utils.py                    # User agent strings and utilities
├── web_scraper.py              # Main web scraper with pagination
├── downloads/                  # Downloaded content (gitignored)
├── trafa_downloads/            # Trafikanalys downloads (gitignored)
├── trafa_rss_downloads/        # RSS feed snapshots (gitignored)
├── debug_html/                 # Debug HTML snapshots (gitignored)
├── reports.db                  # SQLite database (generated)
└── reports.xlsx                # Excel export (generated)
```

## Data Output

### Database Schema (SQLite)

The `reports.db` database contains:

```sql
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name TEXT,              -- Publication title
    diarienummer TEXT,             -- Diary number (reference ID)
    serienummer TEXT,              -- Series number (e.g., "Rapport 2024:17")
    description TEXT,              -- Publication description/summary
    date TEXT,                     -- Publication date
    url TEXT UNIQUE                -- Source URL (unique constraint)
);
```

### Export Formats

- **SQLite** (`reports.db`) - Full database with all metadata
- **Excel** (`reports.xlsx`) - Human-readable spreadsheet format
- **CSV** (`trafa_rss_metadata.csv`, `trafa_sitemap_metadata.csv`) - Raw metadata exports

### Downloaded Content

Organized by source and file type:
- `downloads/` - Tillväxtanalys content (HTML pages)
- `trafa_downloads/pdf/` - PDF documents organized by year
- `trafa_downloads/xlsx/` - Excel datasets organized by year
- `trafa_rss_downloads/` - RSS feed HTML snapshots by date

### Scraper Types

1. **Web Scraper** (`web_scraper.py`)
   - Uses Playwright for JavaScript-rendered pages
   - Handles pagination via "load more" buttons
   - Extracts structured metadata from HTML

2. **RSS Parser** (`trafa_rss_metadata.py`)
   - Parses RSS/Atom feeds
   - Downloads linked content
   - Organizes by publication date

3. **Sitemap Crawler** (`trafa_sitemap_metadata.py`)
   - Parses XML sitemaps
   - Discovers all published documents
   - Extracts file metadata (PDF, XLSX)

4. **PDF Crawler** (`pdf_crawler.py`)
   - Recursive link following
   - Section-based organization
   - Duplicate prevention



## Sample Data

Recent scrapes have collected:

### Tillväxtanalys (Business Analysis)
- **577 reports** in database
- **12,132 PDF documents** downloaded

### Trafikanalys (Transport Analysis)
- **2,917 PDF documents** (transport statistics and reports)
- **536 Excel datasets** with transport data
- **130 RSS feed snapshots**
- **289 RSS feed entries**

### Totals
- **15,049 PDF documents** (12,132 + 2,917)
- **536 Excel datasets**
- **577 database reports**
- **130 RSS snapshots**

Example queries on the data:

```sql
-- Find all reports from December 2024
SELECT * FROM reports WHERE date LIKE '%december 2024%';

-- Count reports by series
SELECT serienummer, COUNT(*) FROM reports GROUP BY serienummer;

-- Search by keyword
SELECT * FROM reports WHERE description LIKE '%företag%';
```

---

## Acknowledgments

Built to support Swedish government authorities in making their public data more accessible and organized.


## License & Attribution

This project is licensed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.

You are free to **use, share, copy, modify, and redistribute** this material for any purpose (including commercial use), **provided that proper attribution is given**.

### Attribution requirements

Any reuse, redistribution, or derivative work **must** include:

1. **The creator’s name**: `HelixCipher`
2. **A link to the original repository**:  
   https://github.com/HelixCipher/Atlas
3. **An indication of whether changes were made**
4. **A reference to the license (CC BY 4.0)**

#### Example Attribution

> This work is based on *Atlas* by `HelixCipher`.  
> Original source: https://github.com/HelixCipher/Atlas
> Licensed under the Creative Commons Attribution 4.0 International (CC BY 4.0).

You may place this attribution in a README, documentation, credits section, or other visible location appropriate to the medium.

Full license text: https://creativecommons.org/licenses/by/4.0/


---

## Disclaimer

This project is provided **“as—is”**. The author accepts no responsibility for how this material is used. There is **no warranty** or guarantee that the scripts are safe, secure, or appropriate for any particular purpose. Use at your own risk.

see [DISCLAIMER.md](./DISCLAIMER.md) for full terms. Use at your own risk.
import asyncio
import logging

# Import your modules.
import trafa_rss_metadata
import trafa_sitemap_metadata
import pdf_crawler
import chrome_path_helper
import web_scraper
from urls import URLS

def run_all_tasks():
    logging.info("Starting all tasks...")

    # 1. Run RSS metadata extraction.
    logging.info("Running RSS metadata extraction...")
    trafa_rss_metadata.main()

    # 2. Run sitemap metadata extraction.
    logging.info("Running sitemap metadata extraction...")
    trafa_sitemap_metadata.main()

    # 3. Run PDF crawler.
    logging.info("Running PDF crawler...")
    # Provide a default base URL for PDF crawling.
    # Adjust this URL if you have a specific site in mind.
    for target_url in URLS:
        pdf_crawler.crawl_for_pdfs(target_url)

    # 4. Retrieve the Chromium path using Playwright.
    logging.info("Fetching Chromium path via Playwright...")
    try:
        chromium_path = asyncio.run(chrome_path_helper.get_playwright_chromium_path())
        logging.info(f"Chromium path: {chromium_path}")
    except Exception as e:
        logging.error(f"Error obtaining Chromium path: {e}")

    # 5. Run the web scraper.
    logging.info("Running web scraper...")
    try:
        asyncio.run(web_scraper.main())
    except Exception as e:
        logging.error(f"Error running web scraper: {e}")

    logging.info("All tasks completed successfully.")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    run_all_tasks()

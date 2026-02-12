import os
import re
import random
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm

from urls import URLS
from utils import USER_AGENTS

DEBUG = False  # Toggle this to False to silence debug logs

def log_debug(message: str):
    if DEBUG:
        print(f"[DEBUG] {message}")


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string so it can be safely used as a folder or file name.
    Replaces spaces with hyphens and removes characters that are not alphanumeric,
    hyphen, underscore, or period.
    """
    name = name.strip().replace(" ", "-")
    return re.sub(r"[^\w\-.]", "", name)

def extract_section_name(link) -> str:
    """
    Walks up the DOM tree from the given BeautifulSoup link element to find the nearest
    heading (h1-h6) element and returns its text. Returns None if no heading is found.
    """
    parent = link.parent
    while parent:
        heading = parent.find(lambda tag: tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"] and tag.get_text(strip=True))
        if heading:
            return heading.get_text(strip=True)
        parent = parent.parent
    return None

def download_pdf(pdf_url: str, link, base_download_dir: str = "downloads"):
    """
    Downloads a PDF file from the given URL and stores it in a directory structured as:
      SectionName/YYYY-MM-DD_HH-MM-SS/SubfolderName/PDFFile.pdf
      
    The section name is extracted from the nearest heading of the link element; if none is found,
    "General" is used. The subfolder name is derived from the link text or PDF filename.
    """
    section = extract_section_name(link) or "General"
    section = sanitize_filename(section)
    
    subfolder = link.get_text(strip=True)
    if not subfolder:
        subfolder = os.path.splitext(os.path.basename(pdf_url))[0]
    subfolder = sanitize_filename(subfolder)
    
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    download_dir = os.path.join(base_download_dir, section, timestamp, subfolder)
    os.makedirs(download_dir, exist_ok=True)
    
    pdf_filename = sanitize_filename(os.path.basename(pdf_url))
    if not pdf_filename.lower().endswith(".pdf"):
        pdf_filename += ".pdf"
    file_path = os.path.join(download_dir, pdf_filename)
    
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    print(f"Downloading PDF: {pdf_url}")
    try:
        pdf_response = requests.get(pdf_url, headers=headers, timeout=10)
        pdf_response.raise_for_status()
        with open(file_path, "wb") as f:
            f.write(pdf_response.content)
        print(f"Saved PDF to {file_path}")
    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")

def crawl_for_pdfs(base_url: str, base_download_dir: str = "downloads", max_depth: int = 3):
    """
    Recursively crawls the site starting at base_url to find PDF files.
    
    This function:
      - Follows internal links within the same domain (up to max_depth levels).
      - Processes only pages with an HTML content type.
      - Decodes page content with errors replaced to avoid decoding warnings.
      - Filters out auto-generated numeric/hex pages that tend to result in 404 errors.
    """
    visited = set()
    to_visit = [(base_url, 0)]
    pdf_links = []
    
    while to_visit:
        current_url, depth = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        try:
            response = requests.get(current_url, headers=headers, timeout=10)
            for r in response.history:
                log_debug(f"Redirect: {r.status_code} -> {r.url}")
            final_url = response.url
            log_debug(f"Final URL after redirects: {final_url}")

            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                log_debug(f"Skipping non-HTML content at {final_url} (Content-Type: {content_type})")
                continue
        except Exception as e:
            print(f"Failed to retrieve {current_url}: {e}")
            continue
        
        # Decode HTML content with errors replaced to prevent decoding warnings.
        html_content = response.content.decode(response.encoding or 'utf-8', errors="replace")
        soup = BeautifulSoup(html_content, "html.parser")
        
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            full_url = urljoin(final_url, href)
            
            # Only follow links within the same domain.
            if urlparse(full_url).netloc != urlparse(base_url).netloc:
                continue
            
            # Filter out auto-generated numeric/hex pages ending with .html
            parsed = urlparse(full_url)
            if re.match(r'^/\d+(\.[\da-f]+)?\.html$', parsed.path):
                continue
            
            if ".pdf" in full_url.lower():
                pdf_links.append((full_url, link))
            elif depth < max_depth and full_url not in visited:
                to_visit.append((full_url, depth + 1))
    
    print(f"Found {len(pdf_links)} PDF links on the site.")
    
    # Use tqdm to show a progress bar for downloading PDFs.
    for pdf_url, link in tqdm(pdf_links, desc="Downloading PDFs", unit="pdf"):
        download_pdf(pdf_url, link, base_download_dir=base_download_dir)


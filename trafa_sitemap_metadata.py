import os
import re
import csv
import logging
import requests
from io import BytesIO
from urllib.parse import urlparse, unquote
from datetime import datetime
from usp.tree import sitemap_tree_for_homepage
import PyPDF2
from openpyxl import load_workbook

# Configure detailed logging.
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def parse_date(date_value):
    """
    Parses various date formats and returns a standardized string "YYYY-MM-DD".
    Handles:
      - PDF date strings like "D:20230424161144+02'00'"
      - Python datetime objects
      - ISO strings (if possible)
    """
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    if isinstance(date_value, str):
        if date_value.startswith("D:"):
            # Remove prefix and extract the first 14 digits.
            d = date_value[2:]
            match = re.match(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})", d)
            if match:
                try:
                    dt = datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")
                    return dt.strftime("%Y-%m-%d")
                except Exception as e:
                    logging.error(f"Error parsing PDF date {date_value}: {e}")
                    return "Unknown"
        else:
            # Try ISO format
            try:
                dt = datetime.fromisoformat(date_value)
                return dt.strftime("%Y-%m-%d")
            except Exception as e:
                logging.debug(f"Could not parse date {date_value}: {e}")
                return date_value
    return "Unknown"

def sanitize_filename(name):
    """
    Removes or replaces characters that are not allowed in file names.
    """
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def download_file(url, base_folder, file_type, year):
    """
    Downloads a file from the given URL and saves it in a folder structure:
    base_folder/file_type/year/filename
    Returns the local file path.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error downloading file {url}: {e}")
        return None

    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    filename = sanitize_filename(unquote(filename))
    folder_path = os.path.join(base_folder, file_type, year)
    os.makedirs(folder_path, exist_ok=True)
    local_path = os.path.join(folder_path, filename)
    try:
        with open(local_path, "wb") as f:
            f.write(response.content)
        logging.info(f"Saved file to {local_path}")
        return local_path
    except Exception as e:
        logging.error(f"Error saving file {local_path}: {e}")
        return None

# --- Extraction Functions for Sitemap Files ---

def extract_sitemap_metadata(page):
    """
    Extracts basic metadata from the sitemap page object.
    """
    url = page.url
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    dokumentnamn = unquote(filename)
    # Use the sitemap's lastmod if available; otherwise, fallback.
    raw_date = getattr(page, 'lastmod', "Unknown")
    datum = parse_date(raw_date)
    return {
         'Dokumentnamn': dokumentnamn,
         'Datum': datum,
         'url': url
    }

def extract_pdf_metadata(url):
    """
    Downloads the PDF and extracts metadata using PyPDF2.
    Returns a dict with:
      - Datum: Parsed creation date (if available)
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        pdf_file = BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        info = reader.metadata
        raw_date = info.get('/CreationDate', "Unknown")
        datum = parse_date(raw_date)
        return {"Datum": datum}
    except Exception as e:
        logging.error(f"Error extracting PDF metadata from {url}: {e}")
        return {"Datum": "Unknown"}

def extract_xlsx_metadata(url):
    """
    Downloads the XLSX file and extracts metadata using openpyxl.
    Returns a dict with:
      - Datum: Creation date property (if available)
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        temp_filename = "temp.xlsx"
        with open(temp_filename, "wb") as f:
            f.write(response.content)
        wb = load_workbook(temp_filename, read_only=True)
        props = wb.properties
        raw_date = props.created if props.created else "Unknown"
        datum = parse_date(raw_date)
        os.remove(temp_filename)
        return {"Datum": datum}
    except Exception as e:
        logging.error(f"Error extracting XLSX metadata from {url}: {e}")
        return {"Datum": "Unknown"}

def filter_relevant_pages(pages):
    """
    Filters pages from the sitemap to include only those ending with .pdf or .xlsx.
    """
    filtered = []
    for page in pages:
        url = page.url.lower()
        if url.endswith('.pdf') or url.endswith('.xlsx'):
            filtered.append(page)
    return filtered

def combine_metadata(sitemap_meta, file_meta):
    """
    Combines sitemap metadata with file-specific metadata.
    For the final output:
      - Dokumentnamn: From sitemap (file name)
      - Datum: Prefer file metadata date if available (over sitemap date)
      - url: From sitemap.
    """
    datum = file_meta.get("Datum", "Unknown")
    combined = {
         'Dokumentnamn': sitemap_meta['Dokumentnamn'],
         'Datum': datum,
         'url': sitemap_meta['url']
    }
    return combined

# --- Main Execution for Sitemap Files ---

def main():
    sitemap_url = "https://www.trafa.se/sitemap.xml"
    logging.info(f"Parsing sitemap: {sitemap_url}")
    
    tree = sitemap_tree_for_homepage(sitemap_url)
    all_pages = list(tree.all_pages())
    logging.info(f"Total pages found in sitemap: {len(all_pages)}")
    
    relevant_pages = filter_relevant_pages(all_pages)
    logging.info(f"Filtered pages (only PDFs and XLSX): {len(relevant_pages)}")
    
    base_download_folder = "trafa_downloads"
    metadata_list = []
    
    for page in relevant_pages:
        sitemap_meta = extract_sitemap_metadata(page)
        file_url = sitemap_meta['url']
        logging.info(f"Processing file: {file_url}")
        
        if file_url.lower().endswith('.pdf'):
            file_meta = extract_pdf_metadata(file_url)
            file_type = "pdf"
        elif file_url.lower().endswith('.xlsx'):
            file_meta = extract_xlsx_metadata(file_url)
            file_type = "xlsx"
        else:
            file_meta = {"Datum": "Unknown"}
            file_type = "other"
        
        combined_meta = combine_metadata(sitemap_meta, file_meta)
        
        # Use the extracted Datum to determine year for sorting. If unknown, use "unknown".
        year = combined_meta['Datum'].split("-")[0] if combined_meta['Datum'] != "Unknown" else "unknown"
        local_path = download_file(file_url, base_download_folder, file_type, year)
        # Optionally, add the local file path to the metadata.
        combined_meta["LocalPath"] = local_path
        
        metadata_list.append(combined_meta)
        logging.info(f"Extracted combined metadata: {combined_meta}")
    
    output_file = "trafa_sitemap_metadata.csv"
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = ["Dokumentnamn", "Datum", "url", "LocalPath"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in metadata_list:
                writer.writerow(item)
        logging.info(f"Metadata written to {output_file}")
    except Exception as e:
        logging.error(f"Error writing CSV file: {e}")

if __name__ == "__main__":
    main()

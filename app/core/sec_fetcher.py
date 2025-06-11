import os
import logging
from pathlib import Path
from typing import Tuple, Dict

import requests
from edgar import *

# Configure logging
typ_logger = logging.getLogger(__name__)
typ_logger.setLevel(logging.INFO)

# Directory for downloads
DOWNLOAD_DIR = os.getenv("SEC_DOWNLOAD_DIR", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Set EDGAR user-agent
set_identity("psshin.code@gmail.com")


def get_cik_and_ticker(identifier: str) -> Tuple[str, str]:
    """Accepts a CIK or ticker. Returns (CIK, TICKER_SYMBOL)."""
    if identifier.isdigit():
        return identifier.zfill(10), f"CIK{identifier}"

    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "psshin.code@gmail.com"}
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    for entry in data.values():
        if entry.get("ticker", "").lower() == identifier.lower():
            return str(entry["cik_str"]).zfill(10), entry["ticker"].upper()
    raise ValueError(f"CIK not found for identifier: {identifier}")


def fetch_latest_filing(identifier: str, form_type: str) -> Dict[str, str]:
    """
    Fetch and save S-1, S-1/A, or 424B4 filings in plain-text (.txt).
    Uses client.get_submissions for metadata and requests for content.
    """
    try:
        cik, ticker_symbol = get_cik_and_ticker(identifier)
        # Instantiate edgartools Company by CIK
        company = Company(identifier)

        # Filter for form type and get latest
        filings = company.get_filings(form=form_type)
        filing = filings.latest()
        if not filing:
            raise RuntimeError(f"No filing {form_type} found for {identifier}")

        # Extract clean text
        raw_html = filing.html()
        file_url = filing.document.url

        # Prepare output directory
        output_dir = Path(DOWNLOAD_DIR) / ticker_symbol
        output_dir.mkdir(parents=True, exist_ok=True)

        # Normalize filename (always .htm)
        date = filing.filing_date
        form_upper = form_type.upper()
        if form_upper == "S-1":
            filename = "s-1.htm"
        elif form_upper == "S-1/A":
            filename = f"s-1-a-{date}.htm"
        elif form_upper == "424B4":
            existing = list(output_dir.glob("final-prospectus*.htm"))
            if existing:
                filename = f"final-prospectus-{date}.htm"
            else:
                filename = "final-prospectus.htm"
        else:
            # fallback naming
            filename = f"{form_type.lower()}-{date}.htm"

        file_path = output_dir / filename
        file_path.write_text(raw_html, encoding="utf-8")

        typ_logger.info(f"Saved {form_type} to {file_path}")
        return {
            "main_doc_path": str(file_path),
            "form_type": form_type,
            "filing_dir": str(output_dir),
            "filing_url": file_url,
            "filing_date": date,
        }

        raise RuntimeError(f"No recent filing of type {form_type} found for {identifier}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch {form_type} for {identifier}: {e}")

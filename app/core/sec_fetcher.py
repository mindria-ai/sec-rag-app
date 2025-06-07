import os
import json
import requests
from pathlib import Path
from sec_edgar_api import EdgarClient

DOWNLOAD_DIR = os.getenv("SEC_DOWNLOAD_DIR", "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

client = EdgarClient(user_agent="PersonalProject psshin.code@gmail.com")

def get_cik_and_ticker(identifier: str) -> tuple[str, str]:
    """Accepts a CIK or ticker. Returns (CIK, TICKER_SYMBOL)."""
    if identifier.isdigit():
        return identifier.zfill(10), f"CIK{identifier}"

    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {"User-Agent": "psshin.code@gmail.com"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise RuntimeError("Failed to fetch SEC ticker-to-CIK mapping")

    data = r.json()
    for entry in data.values():
        if entry["ticker"].lower() == identifier.lower():
            return str(entry["cik_str"]).zfill(10), entry["ticker"].upper()

    raise ValueError(f"CIK not found for identifier: {identifier}")

def fetch_latest_filing(identifier: str, form_type: str) -> dict:
    """Fetch and save S-1, S-1/A, or 424B4 filings with normalized naming."""
    try:
        cik, ticker_symbol = get_cik_and_ticker(identifier)

        submission_data = client.get_submissions(cik)
        recent_filings = submission_data["filings"]["recent"]

        forms = recent_filings["form"]
        accession_numbers = recent_filings["accessionNumber"]
        primary_docs = recent_filings["primaryDocument"]
        filing_dates = recent_filings["filingDate"]

        for i, form in enumerate(forms):
            if form.strip().upper() == form_type.upper():
                acc_num_raw = accession_numbers[i]
                acc_num = acc_num_raw.replace("-", "")
                doc_name = primary_docs[i]
                filing_date = filing_dates[i]

                file_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_num}/{doc_name}"
                headers = {"User-Agent": "psshin.code@gmail.com"}
                response = requests.get(file_url, headers=headers)
                if response.status_code != 200:
                    raise RuntimeError(f"Failed to download filing from {file_url}")

                # Directory: always <ticker>/S-1/
                output_dir = Path(DOWNLOAD_DIR) / ticker_symbol
                output_dir.mkdir(parents=True, exist_ok=True)

                # Normalized filename logic
                if form_type.upper() == "S-1":
                    filename = "s-1.htm"
                elif form_type.upper() == "S-1/A":
                    filename = f"s-1-a-{filing_date}.htm"
                elif form_type.upper() == "424B4":
                    existing = list(output_dir.glob("final-prospectus*.htm"))
                    if existing:
                        filename = f"final-prospectus-{filing_date}.htm"
                    else:
                        filename = "final-prospectus.htm"
                else:
                    filename = f"{form_type.lower()}-{filing_date}.htm"

                file_path = output_dir / filename

                with open(file_path, "wb") as f:
                    f.write(response.content)

                return {
                    "main_doc_path": str(file_path),
                    "form_type": form_type,
                    "filing_dir": str(output_dir),
                    "filing_url": file_url,
                    "filing_date": filing_date,
                }

        raise RuntimeError(f"No recent filing of type {form_type} found for {identifier}")

    except Exception as e:
        raise RuntimeError(f"Failed to fetch {form_type} for {identifier}: {str(e)}")

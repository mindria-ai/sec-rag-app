# app/core/sec_fetcher.py
def fetch_latest_filing(ticker: str, form_type: str) -> str:
    return f"downloads/{ticker}_{form_type}.txt"  # simulate a downloaded file path

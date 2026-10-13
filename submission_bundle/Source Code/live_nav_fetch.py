"""
live_nav_fetch.py
=================
Fetches live & historical NAV data from the mfapi.in public REST API.
Covers:
  - Task 4: GET https://api.mfapi.in/mf/125497 (HDFC Top 100 Direct / Scheme 125497)
  - Task 5: 5 Key Schemes:
      * SBI Bluechip (119551)
      * ICICI Bluechip (120503)
      * Nippon Large Cap (118632)
      * Axis Bluechip (119092)
      * Kotak Bluechip (120841)

Saves parsed JSON responses as raw CSV files under data/raw/
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
import requests
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.mfapi.in/mf"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

SCHEMES_TO_FETCH = {
    125497: "HDFC Top 100 Fund - Direct Plan - Growth",
    119551: "SBI Bluechip Fund - Regular Plan - Growth",
    120503: "ICICI Pru Bluechip Fund - Regular - Growth",
    118632: "Nippon India Large Cap Fund - Regular - Growth",
    119092: "Axis Bluechip Fund - Regular - Growth",
    120841: "Kotak Bluechip Fund - Regular - Growth",
}


def fetch_scheme_nav(amfi_code: int, timeout: int = 15) -> Optional[Dict[str, Any]]:
    """
    Fetch NAV JSON from mfapi.in for a given AMFI scheme code.
    """
    url = f"{BASE_URL}/{amfi_code}"
    logger.info(f"Fetching NAV data from: {url}")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "FAIL":
            logger.error(f"API returned FAIL for code {amfi_code}: {data.get('message')}")
            return None
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed for code {amfi_code}: {e}")
        return None


def parse_and_save_nav(amfi_code: int, label: str, api_data: Dict[str, Any]) -> str:
    """
    Parses the API JSON payload into a DataFrame and writes to CSV.
    """
    meta = api_data.get("meta", {})
    records = api_data.get("data", [])
    
    if not records:
        logger.warning(f"No NAV records returned for scheme {amfi_code}")
        df = pd.DataFrame(columns=["amfi_code", "date", "nav"])
    else:
        df = pd.DataFrame(records)
        df["amfi_code"] = amfi_code
        df["scheme_name"] = meta.get("scheme_name", label)
        df["fund_house"] = meta.get("fund_house", "")
        # Reorder columns cleanly
        cols = ["amfi_code", "date", "nav", "scheme_name", "fund_house"]
        df = df[[c for c in cols if c in df.columns]]

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_file = os.path.join(OUTPUT_DIR, f"live_nav_{amfi_code}.csv")
    df.to_csv(out_file, index=False)
    
    latest_nav = records[0]["nav"] if records else "N/A"
    latest_date = records[0]["date"] if records else "N/A"
    logger.info(
        f"Saved {len(df):,} records for {amfi_code} ({label}) -> {out_file} "
        f"[Latest NAV: Rs. {latest_nav} on {latest_date}]"
    )
    return out_file


def run_pipeline() -> None:
    """
    Orchestrate fetching for all target schemes and summary reporting.
    """
    logger.info("=== Starting Live NAV Ingestion Pipeline ===")
    summary = []
    
    for code, label in SCHEMES_TO_FETCH.items():
        data = fetch_scheme_nav(code)
        if data:
            out_path = parse_and_save_nav(code, label, data)
            meta = data.get("meta", {})
            nav_data = data.get("data", [])
            summary.append({
                "amfi_code": code,
                "label": label,
                "api_scheme_name": meta.get("scheme_name"),
                "fund_house": meta.get("fund_house"),
                "records_count": len(nav_data),
                "latest_date": nav_data[0]["date"] if nav_data else None,
                "latest_nav": nav_data[0]["nav"] if nav_data else None,
                "csv_path": out_path
            })
        else:
            logger.error(f"Failed to fetch scheme {code}")

    summary_df = pd.DataFrame(summary)
    summary_csv = os.path.join(OUTPUT_DIR, "live_nav_fetch_summary.csv")
    summary_df.to_csv(summary_csv, index=False)
    logger.info(f"Summary report written to {summary_csv}")
    print("\n--- Ingestion Summary ---")
    print(summary_df[["amfi_code", "label", "records_count", "latest_date", "latest_nav"]].to_string(index=False))


if __name__ == "__main__":
    run_pipeline()

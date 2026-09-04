"""
Pulls diluted EPS and net sales from SEC's public XBRL company-facts API
for Target and Walmart. These are standardized, tagged fields -- safe to
automate. Comp sales % is intentionally NOT pulled here: it's a narrative
disclosure, not a standard XBRL tag, and auto-extracting it risks a silent
misparse. Comp sales stays manually sourced and logged in citation_log.csv,
same as before.

Output here is for cross-checking against numbers already in citation_log.csv
and the hand-verified bridge math -- not a replacement for that log.
"""

import json
import urllib.request

# SEC requires a descriptive User-Agent identifying the requester
HEADERS = {"User-Agent": "JJ Munshi jmuns22-portfolio-project contact: jmunsiff11@gmail.com"}

COMPANIES = {
    "Target": "0000027419",
    "Walmart": "0000104169",
}

TAGS_OF_INTEREST = {
    "EarningsPerShareDiluted": "Diluted EPS",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "Net Sales/Revenue",
}


def fetch_company_facts(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def print_recent_quarterly_values(facts, tag, label, n=8):
    try:
        units = facts["facts"]["us-gaap"][tag]["units"]
    except KeyError:
        print(f"  [tag not found: {tag}]")
        return

    # values are usually under "USD" or "USD/shares"
    for unit_key, entries in units.items():
        quarterly = [e for e in entries if e.get("form") in ("10-Q", "10-K") and e.get("fp") != "FY"]
        quarterly = sorted(quarterly, key=lambda e: e["end"], reverse=True)[:n]
        print(f"  {label} ({unit_key}):")
        for e in quarterly:
            print(f"    Period ending {e['end']}: {e['val']}  (filed {e['filed']}, form {e['form']})")
        print()


def main():
    for company_name, cik in COMPANIES.items():
        print("=" * 70)
        print(f"{company_name} (CIK {cik})")
        print("=" * 70)
        facts = fetch_company_facts(cik)
        for tag, label in TAGS_OF_INTEREST.items():
            print_recent_quarterly_values(facts, tag, label)
        print()

    print("Cross-check these values against sources/citation_log.csv and")
    print("the hand-verified numbers already used in bridge_analysis.py.")
    print("If anything here disagrees with what's logged, investigate before")
    print("changing either -- don't silently trust whichever number is newer.")


if __name__ == "__main__":
    main()

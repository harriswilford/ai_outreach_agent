"""
Exports and Filters 2,391 Leads for the 8 Selected High-Yield Trade Niches:
- MEP - Mechanical & HVAC
- MEP - Electrical
- MEP - Plumbing & Piping
- Concrete & Masonry
- Commercial General Contractors
- Flooring & Tile
- Painting & Wallcovering
- Residential Custom Builders & Remodelers
"""

import json
import csv
from pathlib import Path

DATA_DIR = Path(__file__).parent
ALL_LEADS_FILE = DATA_DIR / "takeoff_leads_3000.json"
FILTERED_JSON = DATA_DIR / "selected_niches_2391_leads.json"
FILTERED_CSV = DATA_DIR / "selected_niches_2391_leads.csv"

SELECTED_NICHES = [
    "MEP - Mechanical & HVAC",
    "MEP - Electrical",
    "MEP - Plumbing & Piping",
    "Concrete & Masonry",
    "Commercial General Contractors",
    "Flooring & Tile",
    "Painting & Wallcovering",
    "Residential Custom Builders & Remodelers"
]

def export_selected():
    with open(ALL_LEADS_FILE, "r", encoding="utf-8") as f:
        all_leads = json.load(f)
        
    filtered = [l for l in all_leads if l["trade_niche"] in SELECTED_NICHES]
    
    # Save JSON
    with open(FILTERED_JSON, "w", encoding="utf-8") as f:
        json.dump(filtered, f, indent=2)
        
    # Save CSV
    with open(FILTERED_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "company", "contact_name", "first_name", "role", "trade_niche", 
            "division", "city", "state", "region", "email", "phone", "website", 
            "sample_project_proof", "sample_file_reference", "verification_status", 
            "deliverability_score", "target_outreach_day", "pipeline_status", "subject", "typical_value"
        ])
        writer.writeheader()
        for lead in filtered:
            row = {k: v for k, v in lead.items() if k != "body"}
            writer.writerow(row)
            
    print(f"[SUCCESS] Filtered {len(filtered)} leads across 8 selected niches.")
    print(f"[+] Saved to: {FILTERED_JSON}")
    print(f"[+] Saved to: {FILTERED_CSV}")
    return filtered

if __name__ == "__main__":
    export_selected()

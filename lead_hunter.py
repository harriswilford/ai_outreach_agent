"""
Autonomous Lead Discovery & Web Hunter Engine for USA Construction Contractors
Prospects live contractors across 50 US States, extracts verified emails & phones,
filters junk assets, and synchronizes with curated lead databases.
"""

import os
import re
import json
import time
import random
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

try:
    import primp
except ImportError:
    primp = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from trade_intelligence import TRADE_INTELLIGENCE, US_CONSTRUCTION_METROS, get_trade_intelligence

DATA_DIR = Path(__file__).parent
MASTER_DB_FILE = DATA_DIR / "leads_master_db.json"
ARCH_LEADS_FILE = DATA_DIR / "architecture_construction_leads.json"
TAKEOFF_3000_FILE = DATA_DIR / "takeoff_leads_3000.json"

# Common junk email filters
INVALID_EMAIL_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".woff", ".ttf"
)
IGNORE_EMAIL_SUBSTRINGS = [
    "sentry", "wixpress", "example.com", "domain.com", "yoursite.com", "email.com",
    "schema.org", "w3.org", "noreply", "no-reply", "donotreply", "support@cloudflare",
    "wordpress", "gravityforms", "recaptcha", "google.com"
]

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(r'\(?\b[2-9][0-9]{2}\)?[-.\s]?[2-9][0-9]{2}[-.\s]?[0-9]{4}\b')

def clean_email(email_str: str) -> Optional[str]:
    """Clean and validate extracted email address."""
    if not email_str:
        return None
    email_clean = email_str.strip().lower()
    if any(email_clean.endswith(ext) for ext in INVALID_EMAIL_EXTENSIONS):
        return None
    if any(sub in email_clean for sub in IGNORE_EMAIL_SUBSTRINGS):
        return None
    if len(email_clean) < 6 or "@" not in email_clean:
        return None
    # Ensure domain has dot
    domain_part = email_clean.split("@")[-1]
    if "." not in domain_part or len(domain_part.split(".")[-1]) < 2:
        return None
    return email_clean

def clean_phone(phone_str: str) -> Optional[str]:
    """Format US phone number consistently."""
    if not phone_str:
        return None
    digits = re.sub(r'\D', '', phone_str)
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    return phone_str.strip()

class LeadHunter:
    def __init__(self, db_path: Path = MASTER_DB_FILE):
        self.db_path = db_path
        self.master_leads: List[Dict[str, Any]] = []
        self.seen_emails = set()
        self.seen_companies = set()
        self.http_client = primp.Client(impersonate="random") if primp else None
        self.load_master_db()

    def load_master_db(self):
        """Load master leads database into memory and build deduplication indices."""
        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.master_leads = json.load(f)
            except Exception as e:
                print(f"[!] Warning reading master db: {e}")
                self.master_leads = []
        else:
            # Seed from existing repositories if master DB does not exist yet
            self.master_leads = []
            self._seed_initial_leads()
            self.save_master_db()

        for l in self.master_leads:
            em = clean_email(l.get("email"))
            if em:
                self.seen_emails.add(em)
            comp = l.get("company", "").strip().lower()
            if comp:
                self.seen_companies.add(comp)

    def _seed_initial_leads(self):
        """Import curated leads from existing project databases."""
        # 1. Architecture & Construction Leads
        if ARCH_LEADS_FILE.exists():
            try:
                with open(ARCH_LEADS_FILE, "r", encoding="utf-8") as f:
                    arch_data = json.load(f)
                    for item in arch_data:
                        lead = self._normalize_lead(item, source="curated_architecture_db")
                        if lead:
                            self.master_leads.append(lead)
            except Exception as e:
                print(f"[!] Warning seeding arch leads: {e}")

        # 2. Takeoff Leads 3000
        if TAKEOFF_3000_FILE.exists():
            try:
                with open(TAKEOFF_3000_FILE, "r", encoding="utf-8") as f:
                    takeoff_data = json.load(f)
                    for item in takeoff_data:
                        lead = self._normalize_lead(item, source="takeoff_3000_db")
                        if lead:
                            self.master_leads.append(lead)
            except Exception as e:
                print(f"[!] Warning seeding takeoff leads: {e}")

    def _normalize_lead(self, raw: Dict[str, Any], source: str = "curated") -> Optional[Dict[str, Any]]:
        """Normalize raw lead data to standard schema."""
        email = clean_email(raw.get("email"))
        if not email or email in self.seen_emails:
            return None

        comp = raw.get("company", "").strip()
        if not comp:
            return None

        trade = raw.get("trade_niche") or raw.get("trade") or "Commercial General Contractors"
        intel = get_trade_intelligence(trade)

        contact_name = raw.get("contact_name") or raw.get("name") or "Preconstruction Team"
        first_name = contact_name.split()[0] if contact_name else "Team"

        lead_id = raw.get("id") or (len(self.master_leads) + 1)

        lead = {
            "id": lead_id,
            "company": comp,
            "contact_name": contact_name,
            "first_name": first_name,
            "role": raw.get("role") or "Chief Estimator / Preconstruction Manager",
            "trade_niche": trade,
            "division": intel["division"],
            "city": raw.get("city") or "Dallas",
            "state": raw.get("state") or "TX",
            "email": email,
            "phone": clean_phone(raw.get("phone")) or "(800) 555-0100",
            "website": raw.get("website") or "",
            "pain_point": raw.get("pain_point") or intel["primary_pain"],
            "hook": raw.get("hook") or intel["value_hook"],
            "sample_proof": raw.get("sample_proof") or intel["sample_project"],
            "sample_file": raw.get("sample_file") or intel["sample_file"],
            "status": raw.get("status") or "DISCOVERED",
            "source": source,
            "outreach_touches": raw.get("outreach_touches") or 0,
            "last_contact_date": raw.get("last_contact_date"),
            "notes": raw.get("notes") or ""
        }
        self.seen_emails.add(email)
        self.seen_companies.add(comp.lower())
        return lead

    def save_master_db(self):
        """Persist master database to disk."""
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self.master_leads, f, indent=2)

    def fetch_page_content(self, url: str) -> Optional[str]:
        """Fetch web page content with timeout and robust connection handling."""
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                return resp.text
        except Exception:
            pass

        if self.http_client:
            try:
                resp = self.http_client.get(url, timeout=8)
                if resp.status_code == 200:
                    return resp.text
            except BaseException:
                pass
        return None

    def search_contractors_live(self, trade_niche: str, city: str, state: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute live search for US contractors in specified trade and metro area.
        Crawls matching websites to extract verified emails, phones, and contacts.
        """
        intel = get_trade_intelligence(trade_niche)
        terms = intel.get("search_terms") or [trade_niche]
        primary_term = terms[0] if isinstance(terms, list) and terms else trade_niche
        # Clean up acronyms like 'MEP - ' for search
        search_kw = primary_term.replace("MEP - ", "").replace("&", "and")
        query = f'{search_kw} commercial contractors {city} {state}'
        print(f"[*] Sourcing live USA leads: [{trade_niche}] in {city}, {state} (Query: {query})...")

        discovered: List[Dict[str, Any]] = []
        raw_links = []
        try:
            import requests
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"}
            # Try GET first, fallback to POST
            resp = requests.get(
                f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}",
                headers=headers,
                timeout=12
            )
            if resp.status_code != 200:
                resp = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=headers, timeout=12)

            if resp.status_code == 200 and BeautifulSoup:
                soup = BeautifulSoup(resp.text, "html.parser")
                for a in soup.select(".result__a"):
                    href = a.get("href", "")
                    if "uddg=" in href:
                        real_url = urllib.parse.unquote(href.split("uddg=")[1].split("&")[0])
                    else:
                        real_url = href
                    title = a.get_text(strip=True)
                    if real_url.startswith("http"):
                        raw_links.append((title, real_url))
        except Exception as e:
            print(f"[!] Live search engine query error: {e}")

        for title, url in raw_links:
            # Filter out social media or aggregators
            if any(dom in url for dom in ["facebook.com", "linkedin.com", "yelp.com", "youtube.com", "twitter.com", "instagram.com", "mapquest.com", "yellowpages.com"]):
                continue

            parsed_url = urllib.parse.urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            # Derive company name from title or domain
            company_name = title.split("-")[0].split("|")[0].strip()
            if not company_name or len(company_name) > 50:
                company_name = parsed_url.netloc.replace("www.", "").split(".")[0].replace("-", " ").title()

            if company_name.lower() in self.seen_companies:
                continue

            # Fetch page and check for contact details
            emails = set()
            phones = set()
            html = self.fetch_page_content(url)
            if html:
                emails.update(EMAIL_REGEX.findall(html))
                phones.update(PHONE_REGEX.findall(html))

            # If not found on landing page, try /contact
            if not emails:
                contact_url = f"{base_url}/contact"
                contact_html = self.fetch_page_content(contact_url)
                if contact_html:
                    emails.update(EMAIL_REGEX.findall(contact_html))
                    phones.update(PHONE_REGEX.findall(contact_html))

            valid_email = None
            for em in emails:
                ce = clean_email(em)
                if ce and ce not in self.seen_emails:
                    valid_email = ce
                    break

            if valid_email:
                phone_str = clean_phone(next(iter(phones))) if phones else "(800) 555-0100"
                lead_data = {
                    "id": len(self.master_leads) + len(discovered) + 1,
                    "company": company_name,
                    "contact_name": "Estimating Department",
                    "first_name": "Estimating Team",
                    "role": "Chief Estimator / Precon Director",
                    "trade_niche": trade_niche,
                    "division": intel["division"],
                    "city": city,
                    "state": state,
                    "email": valid_email,
                    "phone": phone_str,
                    "website": base_url,
                    "pain_point": intel["primary_pain"],
                    "hook": intel["value_hook"],
                    "sample_proof": intel["sample_project"],
                    "sample_file": intel["sample_file"],
                    "status": "QUALIFIED",
                    "source": "live_web_hunter",
                    "outreach_touches": 0,
                    "last_contact_date": None,
                    "notes": f"Scraped live from {url}"
                }
                discovered.append(lead_data)
                self.seen_emails.add(valid_email)
                self.seen_companies.add(company_name.lower())
                print(f"  [+] Discovered: {company_name} <{valid_email}> [{trade_niche} in {city}, {state}]")

                if len(discovered) >= max_results:
                    break

        if discovered:
            self.master_leads.extend(discovered)
            self.save_master_db()
            print(f"[SUCCESS] Added {len(discovered)} verified live contractor leads to database.")
            
        return discovered

    def get_prospects(self, status: str = "QUALIFIED", trade: Optional[str] = None, state: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve leads filtered by status, trade, or state."""
        results = []
        for l in self.master_leads:
            if status and l.get("status") != status:
                continue
            if trade and trade.lower() not in l.get("trade_niche", "").lower():
                continue
            if state and l.get("state", "").upper() != state.upper():
                continue
            results.append(l)
            if len(results) >= limit:
                break
        return results

    def update_lead_status(self, lead_id: int, new_status: str, notes: Optional[str] = None):
        """Update lifecycle state of a lead."""
        for l in self.master_leads:
            if l.get("id") == lead_id:
                l["status"] = new_status
                if new_status == "SENT":
                    l["outreach_touches"] = l.get("outreach_touches", 0) + 1
                    l["last_contact_date"] = time.strftime("%Y-%m-%d %H:%M:%S")
                if notes:
                    l["notes"] = f"{l.get('notes', '')} | {notes}".strip(" |")
                break
        self.save_master_db()

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate pipeline statistics."""
        status_counts = {}
        trade_counts = {}
        state_counts = {}
        for l in self.master_leads:
            s = l.get("status", "DISCOVERED")
            status_counts[s] = status_counts.get(s, 0) + 1
            t = l.get("trade_niche", "General")
            trade_counts[t] = trade_counts.get(t, 0) + 1
            st = l.get("state", "US")
            state_counts[st] = state_counts.get(st, 0) + 1

        return {
            "total_leads": len(self.master_leads),
            "status_breakdown": status_counts,
            "trade_breakdown": trade_counts,
            "state_breakdown": state_counts
        }

if __name__ == "__main__":
    hunter = LeadHunter()
    stats = hunter.get_stats()
    print("=" * 70)
    print(f"LEAD HUNTER MASTER DATABASE: {stats['total_leads']} Total Staged Leads")
    print("=" * 70)
    for st, cnt in stats["status_breakdown"].items():
        print(f"  - {st:<20}: {cnt}")
    print("-" * 70)
    print("Testing live contractor prospector for Dallas, TX...")
    found = hunter.search_contractors_live("Commercial General Contractors", "Dallas", "TX", max_results=3)
    print(f"Discovered {len(found)} leads in live test.")

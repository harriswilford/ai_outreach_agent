"""
AI Copywriting & Multi-Touch Sequence Generator for Takeoff & Estimation Outreach
Generates high-converting, trade-specific cold email drafts, subject lines,
and direct Gmail compose links tailored to US construction contractors.
"""

import urllib.parse
from typing import Dict, Any, List
from trade_intelligence import get_trade_intelligence

SENDER_PROFILE = {
    "name": "Harris Wilford",
    "title": "Lead Preconstruction Consultant",
    "company": "Precision Takeoff & Estimation Services",
    "email": "harriswilford1618@gmail.com",
    "software_suite": "PlanSwift Professional / Bluebeam Revu / CSI MasterFormat Excel"
}

def generate_touch_1(lead: Dict[str, Any]) -> Dict[str, str]:
    """
    Touch 1: Initial Hook & On-Demand Takeoff Bandwidth Proposition.
    Sent on Day 1.
    """
    company = lead.get("company", "your company")
    first_name = lead.get("first_name") or "there"
    city = lead.get("city", "your area")
    trade = lead.get("trade_niche", "Commercial Contracting")
    intel = get_trade_intelligence(trade)
    pain = lead.get("pain_point") or intel["primary_pain"]
    hook = lead.get("hook") or intel["value_hook"]

    subject = f"quick question regarding {company}'s takeoff bandwidth"

    body = (
        f"Hi {first_name},\n\n"
        f"Saw {company}'s work across the {city} market.\n\n"
        f"I know for {trade} contractors, the primary bottleneck to scaling revenue is rarely finding jobs to bid—it’s having the estimating bandwidth to calculate {pain} before the bid deadline closes.\n\n"
        f"We run a dedicated quantity takeoff & estimation team using {SENDER_PROFILE['software_suite']}.\n\n"
        f"{hook}\n\n"
        f"If you have an upcoming project or drawings currently out for bid, feel free to send over the PDF plans. We'll turn around a transparent estimate and deliverable schedule within a few hours so your team can submit bids on time with complete quantity confidence.\n\n"
        f"Do you have an active project or upcoming bid set this week where extra takeoff capacity would be helpful?\n\n"
        f"Best regards,\n"
        f"{SENDER_PROFILE['name']}\n"
        f"{SENDER_PROFILE['title']} | {SENDER_PROFILE['company']}\n"
        f"Email: {SENDER_PROFILE['email']}"
    )

    return {
        "touch": 1,
        "subject": subject,
        "body": body,
        "recipient": lead.get("email", "")
    }

def generate_touch_2(lead: Dict[str, Any]) -> Dict[str, str]:
    """
    Touch 2: Turnaround Guarantee & Deliverables Breakdown.
    Sent Day +2.
    """
    company = lead.get("company", "your company")
    first_name = lead.get("first_name") or "there"
    trade = lead.get("trade_niche", "trade")
    intel = get_trade_intelligence(trade)
    sample_file = lead.get("sample_file") or intel.get("sample_file", "verified plan set")

    subject = f"Re: quick question regarding {company}'s takeoff bandwidth"

    body = (
        f"Hi {first_name},\n\n"
        f"Following up on my note—just yesterday we turned around a complete {trade} takeoff in under 36 hours for a contractor caught in an urgent bid deadline crunch.\n\n"
        f"Our complete deliverable package includes:\n"
        f"1. Marked-up, color-coded Bluebeam Revu / PlanSwift PDF drawings with every measurement and tag clearly labeled.\n"
        f"2. Itemized Excel Bill of Quantities (formatted to CSI MasterFormat with live formulas).\n"
        f"3. Material summary sheets formatted and ready to forward directly to your suppliers for pricing.\n\n"
        f"We can share a verified project deliverable from our recent portfolio ({sample_file}) if you'd like to see the format and level of detail.\n\n"
        f"Do you have a project out for bid right now where an extra set of hands on takeoff would help you submit on time?\n\n"
        f"Best,\n"
        f"{SENDER_PROFILE['name']}"
    )

    return {
        "touch": 2,
        "subject": subject,
        "body": body,
        "recipient": lead.get("email", "")
    }

def generate_touch_3(lead: Dict[str, Any]) -> Dict[str, str]:
    """
    Touch 3: Workflow & Software Compatibility.
    Sent Day +4.
    """
    first_name = lead.get("first_name") or "there"
    city = lead.get("city", "your area")
    trade = lead.get("trade_niche", "trade")

    subject = f"{first_name}, quick question on your estimating software"

    body = (
        f"Hi {first_name},\n\n"
        f"Most {trade} contractors we partner with in {city} prefer receiving their takeoffs in either native PlanSwift files, Bluebeam Revu markups, or custom Excel workbooks that plug directly into their internal bidding sheets.\n\n"
        f"We adapt our takeoff structure to match your exact bidding template, cost codes, and supplier pack specifications.\n\n"
        f"Happy to review your next bid package and prepare a takeoff proposal so you can see how smoothly our numbers drop into your estimating pipeline. Would that be helpful on an upcoming bid?\n\n"
        f"Best,\n"
        f"{SENDER_PROFILE['name']}"
    )

    return {
        "touch": 3,
        "subject": subject,
        "body": body,
        "recipient": lead.get("email", "")
    }

def generate_touch_4(lead: Dict[str, Any]) -> Dict[str, str]:
    """
    Touch 4: The Polite Break-up / File for Later.
    Sent Day +7.
    """
    company = lead.get("company", "your company")
    first_name = lead.get("first_name") or "there"

    subject = f"Closing the loop / {company} takeoffs"

    body = (
        f"Hi {first_name},\n\n"
        f"I assume you’re completely covered on estimating and takeoff capacity right now, so I won't keep crowding your inbox.\n\n"
        f"If your bidding schedule gets overloaded in the coming months and you need fast 24-48 hr takeoff support to win extra contracts without hiring overhead, feel free to keep my contact handy or send plans to {SENDER_PROFILE['email']}.\n\n"
        f"Wishing you and the entire {company} team continued success on your upcoming projects!\n\n"
        f"Best regards,\n"
        f"{SENDER_PROFILE['name']}\n"
        f"{SENDER_PROFILE['title']} | {SENDER_PROFILE['company']}\n"
        f"Email: {SENDER_PROFILE['email']}"
    )

    return {
        "touch": 4,
        "subject": subject,
        "body": body,
        "recipient": lead.get("email", "")
    }

def build_gmail_compose_url(recipient: str, subject: str, body: str) -> str:
    """Build a direct browser URL to open a pre-filled Gmail Compose draft."""
    base_url = "https://mail.google.com/mail/?view=cm&fs=1"
    params = {
        "to": recipient,
        "su": subject,
        "body": body
    }
    return base_url + "&" + urllib.parse.urlencode(params)

def prepare_campaign_touch(lead: Dict[str, Any], touch_number: int = 1) -> Dict[str, Any]:
    """Generate pitch data for a specific touch with compose URL attached."""
    if touch_number == 1:
        draft = generate_touch_1(lead)
    elif touch_number == 2:
        draft = generate_touch_2(lead)
    elif touch_number == 3:
        draft = generate_touch_3(lead)
    elif touch_number == 4:
        draft = generate_touch_4(lead)
    else:
        draft = generate_touch_1(lead)

    draft["lead_id"] = lead.get("id")
    draft["company"] = lead.get("company")
    draft["trade_niche"] = lead.get("trade_niche")
    draft["city"] = lead.get("city")
    draft["state"] = lead.get("state")
    draft["gmail_compose_url"] = build_gmail_compose_url(draft["recipient"], draft["subject"], draft["body"])
    return draft

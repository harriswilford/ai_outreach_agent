"""
Trade Intelligence & Value Hook Matrix for Quantity Takeoff & Cost Estimation Services.
Covers CSI MasterFormat Divisions, trade-specific pain points, turnaround benchmarks,
and verified project proofs from E:\\Esimation Sample Project.
"""

from typing import Dict, Any, List

TRADE_INTELLIGENCE: Dict[str, Dict[str, Any]] = {
    "Commercial General Contractors": {
        "division": "Division 01 - 33 (Full CSI MasterFormat)",
        "software": "Bluebeam Revu / PlanSwift / Procore",
        "search_terms": ["commercial general contractors", "commercial construction company", "general contracting firm"],
        "pain_points": [
            "handling 10 to 15 simultaneous bid deadlines without having enough in-house estimators",
            "cross-checking subcontractor bid coverage to prevent scope gaps on bid day",
            "overtime costs and estimator burnout during peak commercial bidding season"
        ],
        "primary_pain": "handling multiple concurrent commercial bids without sufficient in-house takeoff capacity to price every package before the deadline",
        "value_hook": "We act as your on-demand preconstruction department. Full CSI multi-division takeoffs, material summaries, and subcontractor bid packages delivered in 3 to 5 business days.",
        "sample_project": "Navy Federal Commercial Branch & Region 2 Headquarters",
        "sample_file": "NAVY FEDERAL COVINGTON.TAKEOFF.pdf",
        "sample_size": "7.70 MB - 19.03 MB multi-division commercial plans",
        "deliverables": [
            "Color-coded Bluebeam Revu marked-up PDF drawing sets",
            "MasterFormat Division 01-33 itemized Excel Bill of Quantities",
            "Subcontractor trade breakdown packages with live calculation formulas"
        ],
        "pricing_range": "$600 - $1,800 per project or $2,500/mo retainer"
    },
    "MEP - Mechanical & HVAC": {
        "division": "Division 23 - Heating, Ventilating, and AC",
        "software": "FastDUCT / PlanSwift / Bluebeam Revu",
        "pain_points": [
            "calculating exact sheet metal ductwork poundage and insulation square footage",
            "counting diffusers, grilles, dampers, and cross-checking mechanical equipment schedules",
            "missing bid deadlines due to tedious manual duct measurement across complex mechanical drawings"
        ],
        "primary_pain": "extracting ductwork poundage, diffuser counts, CFM schedules, and equipment counts under tight 48-hour bid cutoffs",
        "value_hook": "We deliver complete sheet metal poundage, duct insulation SF, diffuser/grille counts, and mechanical equipment schedules in under 48 hours.",
        "sample_project": "Commercial Mechanical & HVAC Takeoff Package",
        "sample_file": "mechanical.pdf",
        "sample_size": "10.18 MB commercial MEP plans",
        "deliverables": [
            "Color-coded PlanSwift/Bluebeam ductwork tracings (low/medium/high pressure)",
            "Duct weight calculation tables (galvanized/stainless poundage by gauge)",
            "Diffuser, VAV box, and air handling equipment schedule summary"
        ],
        "pricing_range": "$350 - $700 per project or $2,000/mo retainer"
    },
    "MEP - Electrical": {
        "division": "Division 26 - Electrical",
        "software": "ConEst / McCormick / PlanSwift / Bluebeam Revu",
        "pain_points": [
            "counting hundreds of lighting fixtures and lighting control sensors across multi-floor plans",
            "measuring conduit feeder lengths and branch circuits accurately",
            "itemizing switchgear, panelboards, transformers, and low-voltage drops"
        ],
        "primary_pain": "counting thousands of lighting fixtures and tracing branch/feeder conduit runs under aggressive bid deadlines",
        "value_hook": "Get 100% itemized fixture counts, branch and feeder conduit lengths, circuit homeruns, and gear schedules in a clean Excel workbook within 48 to 72 hours.",
        "sample_project": "Commercial Electrical & Power Takeoff Package",
        "sample_file": "mechanical.pdf",
        "sample_size": "10.18 MB commercial MEP plans",
        "deliverables": [
            "Symbol-verified lighting fixture and device counts",
            "Conduit and feeder linear footage schedule categorized by trade size",
            "Switchgear and panel schedule itemization"
        ],
        "pricing_range": "$350 - $750 per project or $2,200/mo retainer"
    },
    "MEP - Plumbing & Piping": {
        "division": "Division 22 - Plumbing",
        "software": "FastPIPE / PlanSwift / Bluebeam Revu",
        "pain_points": [
            "tracing linear footage of sanitary waste, vent, storm, domestic cold/hot water, and gas piping",
            "counting fittings, valves, cleanouts, water heaters, and plumbing fixtures",
            "submitting accurate material bills of quantities to supply houses in time for bid submission"
        ],
        "primary_pain": "measuring linear feet of sanitary, storm, domestic water, and gas piping plus valve and fixture takeoff counts",
        "value_hook": "We trace every fixture unit, waste line, domestic water run, and valve fitting with colored overlay markups and ready-to-price bill of quantities.",
        "sample_project": "Commercial Plumbing & Piping Takeoff Package",
        "sample_file": "mechanical.pdf",
        "sample_size": "10.18 MB commercial MEP plans",
        "deliverables": [
            "Linear pipe run breakdowns by pipe size and material (copper, PVC, cast iron, PEX)",
            "Fixture schedules and valve counts",
            "Supplier quote-ready Bill of Materials"
        ],
        "pricing_range": "$300 - $650 per project or $1,800/mo retainer"
    },
    "Concrete & Masonry": {
        "division": "Division 03 - Concrete / Division 04 - Masonry",
        "software": "PlanSwift / Bluebeam Revu / Agtek",
        "pain_points": [
            "calculating exact concrete cubic yards for footings, grade beams, slab on grade, and elevated decks",
            "rebar tonnage calculation including laps, dowels, stirrups, and welded wire mesh",
            "preventing expensive short pours or costly concrete over-orders"
        ],
        "primary_pain": "calculating cubic yards of slab/footings, rebar tonnage, formwork square footage, and CMU block counts under tight deadlines",
        "value_hook": "We calculate exact concrete CY, rebar tonnage with lap splices, vapor barriers, formwork SF, and CMU counts so you eliminate pour shortages and over-orders.",
        "sample_project": "Weeping Willow Estates Structural Concrete Takeoff",
        "sample_file": "WEEPING WILLOW ESTATES (LOT 3).TAKEOFF.pdf",
        "sample_size": "46.79 MB structural plan set",
        "deliverables": [
            "Cubic yard breakdown for slabs, footings, curbs, and piers",
            "Tonnage takeoff for rebar (#4, #5, #6) including lap splices and wire mesh",
            "Formwork contact area (SFCA) and vapor barrier SF"
        ],
        "pricing_range": "$300 - $800 per project or $2,000/mo retainer"
    },
    "Drywall & Framing": {
        "division": "Division 05 - Metals / Division 09 - Finishes",
        "software": "PlanSwift Professional / Bluebeam Revu",
        "pain_points": [
            "calculating linear feet of light gauge metal studs and track across various wall heights",
            "estimating gypsum board sheet counts (regular, Type X, moisture resistant) and joint compound mud/tape",
            "measuring acoustical ceiling tile (ACT) grids and thermal/acoustic insulation square footage"
        ],
        "primary_pain": "calculating linear footage of metal studs, drywall board counts, taped joint lengths, and insulation square footage under tight bid deadlines",
        "value_hook": "We deliver exact metal stud counts, drywall sheet counts, taped joint LF, and fastener/mud calculations in under 48 hours with color-coded PlanSwift markups.",
        "sample_project": "Spaulding Multi-Family Duplex Framing & Drywall Takeoff",
        "sample_file": "SPAULDING DUPLEX.TAKEOFF.pdf",
        "sample_size": "60.49 MB complete multi-family drawings",
        "deliverables": [
            "Wall type linear footage sorted by height and stud gauge",
            "Drywall sheet counts (4x8, 4x10, 4x12 Type X and standard)",
            "Insulation SF and ACT ceiling grid counts"
        ],
        "pricing_range": "$200 - $450 per project or $1,500/mo retainer"
    },
    "Painting & Wallcovering": {
        "division": "Division 09 - Finishes (09 90 00)",
        "software": "PlanSwift Professional / Bluebeam Revu",
        "pain_points": [
            "deducting door and window openings from gross wall areas across hundreds of rooms",
            "measuring baseboards, crown molding, door frames, and casing linear feet",
            "estimating primer and finish coat gallonage based on substrate square footage"
        ],
        "primary_pain": "calculating wall, ceiling, and trim square footage minus deductions across complex commercial floor plans",
        "value_hook": "We calculate net interior/exterior wall SF, door/window frame counts, trim linear feet, and primer/coat gallonage in PlanSwift so you never underbid or overbuy paint.",
        "sample_project": "Eve Estabaya Addition & Remodel Finish Takeoff",
        "sample_file": "Proposed Finished Basement Addition To Residence For Ms. Eve Estabaya.Takeoff.pdf",
        "sample_size": "25.44 MB architectural finish set",
        "deliverables": [
            "Net wall and ceiling square footage by substrate (drywall, CMU, wood)",
            "Linear feet of baseboard, crown molding, and door/window frame counts",
            "Primer and paint gallonage estimates with standard coverage factors"
        ],
        "pricing_range": "$150 - $350 per project or $1,200/mo retainer"
    },
    "Flooring & Tile": {
        "division": "Division 09 - Finishes (09 30 00 / 09 60 00)",
        "software": "Measure Square / PlanSwift / Bluebeam Revu",
        "pain_points": [
            "room-by-room square yardage and square footage calculations for carpet tile, LVP, and porcelain tile",
            "accounting for pattern cut waste factors and roll layout optimization",
            "counting transition reducers, stair nosings, and rubber cove base linear feet"
        ],
        "primary_pain": "measuring complex pattern layouts, transition strips, cove base, and waste percentages for LVP, carpet tile, and porcelain",
        "value_hook": "Detailed room-by-room square yard and square foot breakdowns, transition counts, and prep material quantities ready for supplier quotes within 48 hours.",
        "sample_project": "Spaulding Multi-Family Duplex Flooring & Tile Takeoff",
        "sample_file": "SPAULDING DUPLEX.TAKEOFF.pdf",
        "sample_size": "60.49 MB multi-family drawings",
        "deliverables": [
            "Room-by-room flooring schedule (SF and SY) with net vs gross waste factors",
            "Linear feet of transition strips, schluter edges, and cove base",
            "Subfloor prep and adhesive gallonage"
        ],
        "pricing_range": "$150 - $350 per project or $1,200/mo retainer"
    },
    "Roofing & Siding": {
        "division": "Division 07 - Thermal & Moisture Protection",
        "software": "RoofSnap / PlanSwift / Bluebeam Revu",
        "pain_points": [
            "pitch multiplier calculations, true surface area for hips, valleys, ridges, and eaves",
            "counting squares of TPO, EPDM, metal standing seam, or architectural shingles",
            "itemizing edge metal, flashing linear feet, insulation boards, and fastener counts"
        ],
        "primary_pain": "pitch adjustments, squares of TPO/EPDM/shingles, flashings, hips, valleys, and underlayment waste factor calculation under bid pressure",
        "value_hook": "Get complete roofing squares, edge metal linear feet, insulation board counts, and fastener estimations in 24 to 48 hours.",
        "sample_project": "Weeping Willow Estates Exterior & Roofing Takeoff",
        "sample_file": "WEEPING WILLOW ESTATES (LOT 3).TAKEOFF.pdf",
        "sample_size": "46.79 MB architectural plan set",
        "deliverables": [
            "True pitch-adjusted surface area in squares (100 SF)",
            "Linear footage of ridge, hip, valley, rake, and drip edge",
            "Fastener, underlayment, and flashing bill of materials"
        ],
        "pricing_range": "$150 - $400 per project or $1,200/mo retainer"
    },
    "Residential Custom Builders & Remodelers": {
        "division": "Residential Divisions / Lumber & Framing Lists",
        "software": "PlanSwift / Bluebeam Revu / BuilderTrend",
        "pain_points": [
            "turning architectural blueprint drawings into accurate lumber framing packages and stud counts",
            "extracting window and door schedules, foundation volumes, and exterior cladding areas",
            "juggling jobsite superintendence while trying to bid upcoming custom homes at night"
        ],
        "primary_pain": "producing lumber cut-lists, foundation concrete volumes, framing packages, and finish schedules while managing active jobsites",
        "value_hook": "Turn your architectural plans into complete lumber packs, framing material lists, window/door schedules, and finish quantities in 48 hours.",
        "sample_project": "Weeping Willow Estates & Spaulding Duplex Takeoffs",
        "sample_file": "WEEPING WILLOW ESTATES (LOT 3).TAKEOFF.pdf",
        "sample_size": "46.79 MB custom home plans",
        "deliverables": [
            "Complete lumber and framing takeoff (studs, joists, rafters, headers, plates)",
            "Concrete foundation and slab cubic yardage",
            "Exterior siding, roofing, and interior finish schedules"
        ],
        "pricing_range": "$250 - $600 per project or $1,500/mo retainer"
    },
    "Architecture & Design-Build Firms": {
        "division": "Schematic & Design Development Budgeting",
        "software": "Bluebeam Revu / PlanSwift / Excel",
        "pain_points": [
            "producing preliminary budget estimates for clients during schematic design before full engineering",
            "providing cost transparency to prevent value engineering redesigns later",
            "lacking dedicated estimating staff to price multi-trade materials"
        ],
        "primary_pain": "producing preliminary budget estimates and material takeoffs for clients during the schematic design phase before permit submittal",
        "value_hook": "We convert your early architectural plan sets into itemized PlanSwift material takeoffs and budget models in 48 hours so your clients get clear cost transparency before permitting.",
        "sample_project": "Spaulding Duplex Architectural Takeoff & Region 2 HQ Package",
        "sample_file": "SPAULDING DUPLEX.TAKEOFF.pdf",
        "sample_size": "60.49 MB architectural drawings",
        "deliverables": [
            "Schematic Bill of Quantities (BOQ) with rough order-of-magnitude budget ranges",
            "Division-by-division square footage and itemized counts",
            "Color-coded plan markups ready for client presentations"
        ],
        "pricing_range": "$400 - $1,200 per project"
    }
}

# Top 30 High-Growth US Construction Metropolitan Areas
US_CONSTRUCTION_METROS: List[Dict[str, str]] = [
    {"city": "Dallas-Fort Worth", "state": "TX", "region": "South"},
    {"city": "Houston", "state": "TX", "region": "South"},
    {"city": "Austin", "state": "TX", "region": "South"},
    {"city": "San Antonio", "state": "TX", "region": "South"},
    {"city": "Atlanta", "state": "GA", "region": "Southeast"},
    {"city": "Tampa-St. Petersburg", "state": "FL", "region": "Southeast"},
    {"city": "Orlando", "state": "FL", "region": "Southeast"},
    {"city": "Miami-Fort Lauderdale", "state": "FL", "region": "Southeast"},
    {"city": "Jacksonville", "state": "FL", "region": "Southeast"},
    {"city": "Charlotte", "state": "NC", "region": "Southeast"},
    {"city": "Raleigh-Durham", "state": "NC", "region": "Southeast"},
    {"city": "Nashville", "state": "TN", "region": "Southeast"},
    {"city": "Phoenix", "state": "AZ", "region": "Southwest"},
    {"city": "Denver", "state": "CO", "region": "Mountain"},
    {"city": "Las Vegas", "state": "NV", "region": "Southwest"},
    {"city": "Salt Lake City", "state": "UT", "region": "Mountain"},
    {"city": "Los Angeles", "state": "CA", "region": "West"},
    {"city": "San Diego", "state": "CA", "region": "West"},
    {"city": "San Francisco Bay Area", "state": "CA", "region": "West"},
    {"city": "Sacramento", "state": "CA", "region": "West"},
    {"city": "Seattle", "state": "WA", "region": "Northwest"},
    {"city": "Portland", "state": "OR", "region": "Northwest"},
    {"city": "Chicago", "state": "IL", "region": "Midwest"},
    {"city": "Minneapolis-St. Paul", "state": "MN", "region": "Midwest"},
    {"city": "Indianapolis", "state": "IN", "region": "Midwest"},
    {"city": "Columbus", "state": "OH", "region": "Midwest"},
    {"city": "Kansas City", "state": "MO", "region": "Midwest"},
    {"city": "Philadelphia", "state": "PA", "region": "Northeast"},
    {"city": "Washington DC-Northern VA", "state": "VA", "region": "Mid-Atlantic"},
    {"city": "Boston", "state": "MA", "region": "Northeast"}
]

def get_trade_intelligence(trade: str) -> Dict[str, Any]:
    """Retrieve intelligence profile for a trade with smart fuzzy matching."""
    if trade in TRADE_INTELLIGENCE:
        return TRADE_INTELLIGENCE[trade]
    
    trade_lower = trade.lower()
    for key, data in TRADE_INTELLIGENCE.items():
        if trade_lower in key.lower() or any(w in trade_lower for w in key.lower().split()):
            return data
            
    # Default to Commercial General Contractors if not matched
    return TRADE_INTELLIGENCE["Commercial General Contractors"]

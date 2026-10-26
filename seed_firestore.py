"""Seed script for VentureKit Firestore collection."""
from google.cloud import firestore

# IMPORTANT: Hardcoded GCP project ID as a string.
# Avoid reading from google.auth.default() or GOOGLE_CLOUD_PROJECT on Agent Platform
# because those can return the project number instead of project ID.
PROJECT_ID = "qwiklabs-gcp-04-c8fa96deb89c"
COLLECTION_NAME = "growth_plays"

SEED_DATA = [
    {
        "id": "retainer_conversion",
        "title": "One-Time to Monthly Retainer Conversion",
        "category": "Pricing & Packaging",
        "target_industry": "Services & Agencies",
        "typical_margin_lift_pct": 25.0,
        "implementation_days": 14,
        "difficulty": "Medium",
        "description": "Convert project-based clients into predictable recurring monthly retainers by bundling ongoing maintenance, priority SLAs, and quarterly advisory check-ins.",
        "key_actions": [
            "Audit existing clients to identify top repeat requests",
            "Structure 3 tiers of retainers (Basic, Pro, Dedicated)",
            "Offer grandfathered introductory pricing for current clients who sign an annual commitment"
        ],
        "kpi_impact": "Stabilizes cash flow and increases LTV by 2.4x"
    },
    {
        "id": "vip_margin_bundle",
        "title": "VIP High-Margin Service Tier",
        "category": "Revenue Expansion",
        "target_industry": "All Small Businesses",
        "typical_margin_lift_pct": 35.0,
        "implementation_days": 7,
        "difficulty": "Low",
        "description": "Introduce an ultra-premium, white-glove package priced 2.5x to 3x above your core offering with 70%+ gross margin.",
        "key_actions": [
            "Bundle fast turnaround and direct founder access",
            "Cap capacity to create genuine scarcity (e.g., max 3 clients per quarter)",
            "Highlight premium deliverables that carry low marginal cost but high perceived value"
        ],
        "kpi_impact": "Captures top 10-15% of price-insensitive clientele without cannibalizing base volume"
    },
    {
        "id": "dormant_client_reactivation",
        "title": "Dormant Client Win-Back Play",
        "category": "Retention & Retention",
        "target_industry": "Local Businesses & Salons/Gyms/Clinics",
        "typical_margin_lift_pct": 40.0,
        "implementation_days": 5,
        "difficulty": "Low",
        "description": "Target past clients inactive for 90+ days with a limited-time high-value re-engagement offer instead of spending on cold acquisition.",
        "key_actions": [
            "Export customer list with last transaction > 90 days ago",
            "Send personalized 3-step message sequence acknowledging absence",
            "Provide an irresistible incentive with zero upfront CAC"
        ],
        "kpi_impact": "Generates immediate cash influx with near 0 customer acquisition cost (CAC)"
    },
    {
        "id": "loss_leader_audit",
        "title": "Unprofitable Service Trim & Repricing",
        "category": "Cost Optimization",
        "target_industry": "Manufacturing, Food & Retail",
        "typical_margin_lift_pct": 18.0,
        "implementation_days": 10,
        "difficulty": "Medium",
        "description": "Perform an activity-based cost audit to isolate offerings that consume disproportionate labor or overhead, repricing or retiring them.",
        "key_actions": [
            "Compute fully-loaded labor and materials cost per SKU/service",
            "Identify bottom 20% margin contributors consuming > 30% of operational capacity",
            "Reprice by +20% or replace with standardized alternative"
        ],
        "kpi_impact": "Frees up capacity for high-margin offerings and lifts net profit without increasing headcount"
    }
]

def seed():
    print(f"Connecting to Firestore for project: '{PROJECT_ID}'...")
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection(COLLECTION_NAME)

    print(f"Seeding '{COLLECTION_NAME}' collection...")
    for item in SEED_DATA:
        doc_id = item["id"]
        doc_ref = collection.document(doc_id)
        doc_ref.set(item)
        print(f"  ✓ Seeded document: {doc_id} ('{item['title']}')")

    print(f"\nSuccessfully seeded {len(SEED_DATA)} growth plays into Firestore!")

if __name__ == "__main__":
    seed()

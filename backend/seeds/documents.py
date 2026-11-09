"""Seed script: creates 10 company documents, embeds them with OpenAI, and
upserts vectors into Pinecone.  Document metadata is also stored in Postgres
for full-text search.

Run with:
    uv run python -m backend.seeds.documents
"""
from __future__ import annotations

import asyncio
import uuid

from backend.database import AsyncSessionLocal, init_db
from backend.models.document import Document
from backend.services.embedding import embedding_service
from backend.services.pinecone_service import pinecone_service

SAMPLE_DOCUMENTS: list[dict] = [
    {
        "title": "Return & Refund Policy",
        "category": "policy",
        "content": (
            "Our return policy allows customers to return items within 30 days of purchase "
            "for a full refund. Items must be unused and in original packaging. "
            "To initiate a return, contact support with your order number. "
            "Refunds are processed within 5–7 business days to the original payment method. "
            "Digital products and customised orders are non-refundable unless defective. "
            "Shipping costs are non-refundable except in cases of our error. "
            "Exchanges are accepted within 14 days for items of equal or lesser value."
        ),
    },
    {
        "title": "Shipping & Delivery Policy",
        "category": "policy",
        "content": (
            "We offer standard shipping (5–7 business days), express shipping (2–3 business days), "
            "and overnight shipping (next business day) for eligible locations. "
            "Free standard shipping is available on orders over $75. "
            "Orders placed before 2 PM EST are processed same day. "
            "International shipping is available to 50+ countries; customs fees are the buyer's responsibility. "
            "Tracking information is emailed once your order ships. "
            "We are not responsible for delays caused by carriers or customs clearance."
        ),
    },
    {
        "title": "Privacy Policy",
        "category": "policy",
        "content": (
            "We collect personal information including name, email, phone number, and payment details "
            "to process orders and provide customer support. "
            "We do not sell or share your data with third parties except as required to fulfil your order "
            "(e.g., shipping carriers, payment processors). "
            "You may request deletion of your account data at any time by contacting privacy@company.com. "
            "We use industry-standard encryption (TLS 1.3) to protect your data in transit. "
            "Cookies are used for session management and analytics; you may opt out via browser settings. "
            "We comply with GDPR, CCPA, and other applicable data protection laws."
        ),
    },
    {
        "title": "Account Suspension & Closure Policy",
        "category": "policy",
        "content": (
            "Accounts may be suspended for violations of our Terms of Service, including fraudulent activity, "
            "chargebacks, abusive behaviour towards staff, or repeated policy violations. "
            "Suspended accounts lose access to purchasing but retain order history for 90 days. "
            "Account closure requests are processed within 10 business days. "
            "Upon closure, personal data is anonymised within 30 days per our data retention schedule. "
            "Appeals against suspension can be submitted to appeals@company.com with supporting evidence."
        ),
    },
    {
        "title": "Frequently Asked Questions – Orders",
        "category": "faq",
        "content": (
            "Q: How do I track my order? A: Use the tracking number in your shipping confirmation email at our tracking page.\n"
            "Q: Can I change my order after placing it? A: Orders can be modified within 1 hour of placement by contacting support.\n"
            "Q: What if my order arrives damaged? A: Contact support within 48 hours with photos; we will arrange a replacement or refund.\n"
            "Q: How do I cancel my order? A: Orders can be cancelled before they ship. Contact support immediately with your order number.\n"
            "Q: Can I combine orders? A: Orders cannot be combined once placed, but you can place a new order and we will refund excess shipping.\n"
            "Q: Do you offer gift wrapping? A: Yes, gift wrapping is available for $5 per item at checkout."
        ),
    },
    {
        "title": "Frequently Asked Questions – Payments",
        "category": "faq",
        "content": (
            "Q: What payment methods are accepted? A: We accept Visa, Mastercard, Amex, Discover, PayPal, Apple Pay, and Google Pay.\n"
            "Q: Is my payment information secure? A: Yes, we use PCI-DSS-compliant payment processors; we never store card numbers.\n"
            "Q: Why was my payment declined? A: Common reasons include insufficient funds, incorrect billing address, or card security restrictions.\n"
            "Q: Can I pay in instalments? A: Yes, we offer Klarna and Afterpay at checkout for orders over $50.\n"
            "Q: How do refunds appear on my statement? A: Refunds appear as a credit from COMPANY NAME within 5–7 business days.\n"
            "Q: Do you charge sales tax? A: Sales tax is calculated based on the shipping address per local regulations."
        ),
    },
    {
        "title": "Product Warranty Information",
        "category": "product",
        "content": (
            "All electronics carry a 1-year manufacturer's warranty against defects in materials and workmanship. "
            "Warranty does not cover accidental damage, water damage, or unauthorised modifications. "
            "To file a warranty claim, contact support with proof of purchase and a description of the defect. "
            "Approved warranty claims will be repaired or replaced at our discretion. "
            "Extended warranty plans (2 or 3 years) are available for purchase within 30 days of product purchase. "
            "Warranty service is provided by our authorised repair centres; in-home service is available for large appliances."
        ),
    },
    {
        "title": "Premium & Enterprise Tier Benefits",
        "category": "product",
        "content": (
            "Premium tier members enjoy: free express shipping on all orders, priority customer support (< 2-hour response), "
            "10% discount on all purchases, early access to new products, and a dedicated account manager. "
            "Enterprise tier members receive all Premium benefits plus: custom pricing agreements, "
            "bulk order discounts (up to 25%), dedicated onboarding support, SLA-backed support (99.9% uptime guarantee), "
            "API access for order integration, and quarterly business reviews. "
            "Upgrade your tier from Account Settings or by contacting your account manager."
        ),
    },
    {
        "title": "Escalation & Human Agent Handoff Procedure",
        "category": "procedure",
        "content": (
            "Customer support escalations follow a structured process to ensure timely resolution. "
            "Level 1 (AI Agent): Handles routine queries, order status, FAQs, and simple actions (refunds < $500, cancellations). "
            "Level 2 (Human Agent): Engaged for complex disputes, refunds > $500, legal/compliance issues, or repeated failures. "
            "Level 3 (Senior Specialist): Handles escalations involving fraud, enterprise accounts, media inquiries, or regulatory matters. "
            "Target response times: L1 immediate, L2 within 2 hours (Premium) / 24 hours (Standard), L3 within 4 hours. "
            "Customers are notified by email when their case is escalated and given a ticket reference number."
        ),
    },
    {
        "title": "Troubleshooting Guide – Common Technical Issues",
        "category": "procedure",
        "content": (
            "Login Issues: Clear browser cache and cookies, then retry. Use 'Forgot Password' if needed. "
            "If 2FA is unavailable, contact support with government ID for account recovery.\n"
            "Order Not Showing: Allow 15 minutes after placement for the order to appear. "
            "Check spam folder for confirmation email. Contact support if order is missing after 1 hour.\n"
            "Payment Processing Errors: Verify billing address matches card records. "
            "Try a different browser or payment method. Contact your bank if the issue persists.\n"
            "Website Performance: Clear cache, disable browser extensions, or try incognito mode. "
            "Report persistent issues to techsupport@company.com with screenshots and browser version.\n"
            "Mobile App Crashes: Ensure the app is updated to the latest version. "
            "Reinstall if crashes continue. Submit crash logs via Settings > Report a Problem."
        ),
    },
]


async def seed() -> None:
    """Main seed function: embeds documents, upserts to Pinecone, saves metadata to Postgres."""
    await init_db()

    # ── Ensure Pinecone index exists ─────────────────────────────────────────
    print("Ensuring Pinecone index exists…")
    pinecone_service.ensure_index()
    stats = pinecone_service.index_stats()
    print(f"  Index stats before seed: {stats.get('total_vector_count', 0)} vectors")

    # ── Batch embed all document content ─────────────────────────────────────
    print(f"\nGenerating embeddings for {len(SAMPLE_DOCUMENTS)} documents…")
    contents = [doc["content"] for doc in SAMPLE_DOCUMENTS]
    embeddings = await embedding_service.embed_batch(contents)
    print(f"  Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    # ── Build records with stable UUIDs ──────────────────────────────────────
    records: list[dict] = []
    for doc_data, emb in zip(SAMPLE_DOCUMENTS, embeddings):
        doc_id = str(uuid.uuid4())
        records.append(
            {
                "id": doc_id,
                "embedding": emb,
                "title": doc_data["title"],
                "content": doc_data["content"],
                "category": doc_data["category"],
            }
        )

    # ── Upsert embeddings + metadata into Pinecone ───────────────────────────
    print("\nUpserting vectors into Pinecone…")
    pinecone_service.upsert_batch(records)
    print(f"  ✅ Upserted {len(records)} vectors to Pinecone index '{pinecone_service._index_name}'")

    # ── Persist metadata in Postgres for full-text search ────────────────────
    print("\nSaving document metadata to Postgres…")
    async with AsyncSessionLocal() as session:
        for rec in records:
            doc = Document(
                id=uuid.UUID(rec["id"]),
                title=rec["title"],
                content=rec["content"],
                category=rec["category"],
                # No embedding column — it lives in Pinecone.
            )
            session.add(doc)
            print(f"  + {rec['title']} (category={rec['category']})")
        await session.commit()

    # ── Print final stats ─────────────────────────────────────────────────────
    stats_after = pinecone_service.index_stats()
    print(f"\n✅ Seeding complete.")
    print(f"   Pinecone vectors : {stats_after.get('total_vector_count', '?')}")
    print(f"   Postgres rows    : {len(records)}")


if __name__ == "__main__":
    asyncio.run(seed())

import csv
import random
from datetime import datetime, timedelta, timezone

SAMPLE_REVIEWS = [
    # Positive - App & Product
    ("The new update is brilliant! The UI is clean, intuitive and runs smoothly on my phone.", 5, "Google Play Store App"),
    ("I love using this service every day. Extremely reliable, fast checkout and great pricing.", 5, "Google Maps / Business Profile"),
    ("Exceptional customer support! My question was resolved in under five minutes by agent Pooja.", 5, "Zendesk Support Webhook"),
    ("Great product quality. Package arrived two days before the estimated delivery date. Highly recommend!", 5, "Bulk Customer Feedback CSV"),
    ("Very happy with the overall experience. The interface is simple and clean.", 4, "NPS Quarterly Customer Survey"),
    ("Fantastic store staff! They helped me find the exact product I needed with a smile.", 5, "Google Maps / Business Profile"),
    ("Everything works as advertised. Smooth onboarding and hassle-free setup.", 5, "Google Play Store App"),
    ("Prompt delivery and great packaging. The merchandise is genuine.", 4, "Bulk Customer Feedback CSV"),

    # Neutral
    ("The service is okay. Nothing extraordinary, but it gets the basic job done.", 3, "NPS Quarterly Customer Survey"),
    ("App is decent but could use a dark mode and faster search filters.", 3, "Google Play Store App"),
    ("Delivery arrived on time. Price is a bit higher than competitors.", 3, "Bulk Customer Feedback CSV"),
    ("Average experience. Support answered my query but took 24 hours to reply.", 3, "Zendesk Support Webhook"),
    ("Standard functionality. Hope they add more payment methods like UPI and Apple Pay soon.", 3, "Google Play Store App"),

    # Negative - Bugs & Performance
    ("The app crashes every single time I reach the payment screen. Completely unusable bug!", 1, "Google Play Store App"),
    ("Horrible lag after the latest update. It freezes my whole phone and drains battery fast.", 1, "Google Play Store App"),
    ("Can't even log into my account. Keeps saying server error occurred. Very frustrating!", 1, "Google Play Store App"),
    ("App keeps glitching and closing unexpectedly. Please release a bug fix immediately.", 2, "Google Play Store App"),

    # Negative - Billing, Refunds, Critical Keywords & PII
    ("Charged twice for order #9921! Support refused my refund and said to wait 30 days. Total scam!", 1, "Zendesk Support Webhook"),
    ("Unauthorized debit of $49.99 from my card. I demanded a refund but was ignored. Terrible fraudulent service!", 1, "Bulk Customer Feedback CSV"),
    ("I want to cancel my subscription right now. They keep deducting money without permission. Contact me at rahul.sharma99@gmail.com or 9820112233.", 1, "Zendesk Support Webhook"),
    ("Defective item arrived broken. When I called helpline 9876543210, the agent was extremely rude and unhelpful.", 1, "Google Maps / Business Profile"),
    ("Unacceptable delay of over 10 days! Tracking number never updated. Cancel my order immediately.", 1, "Bulk Customer Feedback CSV"),
    ("Fraudulent charges on my credit card 4111 2222 3333 4444. This is illegal and I will file a lawsuit if money is not returned.", 1, "Zendesk Support Webhook")
]

def generate_csv_dataset(filename="sample_data/customer_feedback_sample.csv", total_rows=120):
    now = datetime.now(timezone.utc)
    rows = []

    for i in range(total_rows):
        # Pick review with controlled probability to simulate a realistic SMB baseline
        review_text, rating, channel = random.choice(SAMPLE_REVIEWS)
        # Random date over past 25 days, with a cluster in recent 2 days to trigger realistic anomaly
        if i > 95:
            # Recent spike
            day_offset = random.uniform(0.1, 1.8)
        else:
            day_offset = random.uniform(2.0, 25.0)

        dt = now - timedelta(days=day_offset)
        rows.append({
            "id": f"REV-{1000 + i}",
            "text": review_text,
            "rating": rating,
            "source": channel,
            "date": dt.strftime("%Y-%m-%d %H:%M:%S")
        })

    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "text", "rating", "source", "date"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} sample feedback rows in {filename}")

if __name__ == "__main__":
    generate_csv_dataset()

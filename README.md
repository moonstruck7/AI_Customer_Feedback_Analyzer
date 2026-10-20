# AI Customer Feedback Analyzer
### A Multi-Source Decision-Support System for SMBs
**Third-Year Diploma in Computer Engineering (MSBTE Project)**

An end-to-end, lightweight customer intelligence platform combining FastAPI, machine learning (sentiment scoring, theme clustering, and statistical anomaly detection), and an executive glassmorphic web dashboard tailored for Small and Medium Businesses (SMBs).

---

## 🌟 Key Features

1. **Multi-Source Data Ingestion:**
   - Ingest customer feedback from **Google Play Store**, **Google Business Profile**, **Zendesk/Helpdesk Webhooks**, **NPS Surveys**, and **CSV/Excel uploads**.
   - Automatic SHA-256 deduplication to discard identical records.

2. **Automated NLP Pipeline (Section 7.1):**
   - **Text Normalisation & Cleaning:** Removes HTML, email signatures, URLs.
   - **PII Masking:** Automatic detection and masking of phone numbers (`[PHONE_MASKED]`), emails (`[EMAIL_MASKED]`), and credit cards (`[CARD_MASKED]`).
   - **Sentiment Classification:** Softmax probabilities $P(pos), P(neu), P(neg)$, calculating signed intensity score $S = P(pos) - P(neg) \in [-1.0, +1.0]$.
   - **Confidence & Fallback:** Evaluates confidence against $\ge 0.60$ threshold with contextual fallback refinement.
   - **Theme Clustering:** Centroid cosine similarity matching + TF-IDF keyword extraction across 5 core operational themes (*App Bugs*, *Billing & Refunds*, *Delivery*, *Customer Support*, *Product Usability*).
   - **Urgency Scoring (0–100%):** Flags critical keywords (*refund*, *scam*, *fraud*, *cancel*, *lawsuit*) and extreme negative sentiment ($S \le -0.70$).

3. **Statistical Anomaly Engine (Section 7.1 Step 11):**
   - Computes daily negative sentiment share $p$ against rolling 28-day historical baseline ($\mu, \sigma$).
   - Triggers anomaly alerts when $z = \frac{p - \mu}{\sigma} > 2.5$ with alert cooldowns.

4. **Executive Web Dashboard:**
   - **Net Sentiment Score (NSS)** hero gauge ($-100$ to $+100\%$).
   - Dynamic HTML5 Canvas trend charts (daily stacked volume and NSS line progression).
   - **Urgent Action Queue:** Prioritized ticket view with 1-click status actions for Support Managers.
   - **Interactive Live NLP Sandbox:** Real-time step-by-step inference visualizer.
   - **Role Switcher (Table 2):** Instant toggling between **SMB Owner**, **Support Manager**, and **System Admin** views.
   - **One-Click Export:** Download full analyzed feedback dataset as a structured CSV report.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+
- Dependencies in `requirements.txt`:
  ```bash
  py -m pip install -r requirements.txt
  ```

### 2. Populate Demo Data (Optional)
The system comes with a pre-configured realistic 120-item dataset spanning 25+ days:
```bash
py init_demo_data.py
```

### 3. Launch the Server
```bash
py run.py
```
Open your web browser and navigate to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📂 Project Directory Structure

```
d:/fyp project/
├── app/
│   ├── config.py              # Application settings, thresholds, and parameters
│   ├── database.py            # SQLAlchemy database connection and session maker
│   ├── models.py              # User, Source, FeedbackItem, SentimentLog, Theme, Alert models
│   ├── schemas.py             # Pydantic validation schemas
│   ├── main.py                # FastAPI app, database initialization, CORS, static routes
│   ├── nlp/
│   │   ├── preprocessor.py    # HTML stripping, PII masking, language detection, hash deduplication
│   │   ├── sentiment.py       # P(pos), P(neu), P(neg), score S = P(pos) - P(neg), confidence
│   │   ├── theme_clusterer.py # TF-IDF vectorizer & centroid cosine similarity clustering
│   │   └── urgency.py         # Critical keyword detector & urgency score calculation
│   ├── services/
│   │   ├── alert_engine.py    # Z-score anomaly detection z = (p - mu)/sigma > 2.5
│   │   ├── analytics.py       # NSS computation, daily trend buckets, channel distributions
│   │   └── ingestion.py       # Multi-source feedback processing & CSV batch parser
│   └── routers/
│       ├── auth.py            # User login & role listing
│       ├── feedback.py        # Single ingestion, CSV upload, listing, status update
│       ├── analytics.py       # KPI metrics, trend charts, channel distribution, CSV export
│       ├── alerts.py          # Alert listing, acknowledgment, and simulation
│       └── sources.py         # Feedback channels & live sync simulator
├── static/
│   ├── index.html             # Glassmorphic single-page executive web dashboard
│   ├── css/
│   │   └── style.css          # Vanilla CSS design system, dark mode, micro-animations
│   └── js/
│       └── app.js             # Canvas trend charts, API sync, role switcher, live NLP sandbox
├── sample_data/
│   ├── generate_sample_data.py # Realistic dataset generator
│   └── customer_feedback_sample.csv # 120 sample feedback records
├── docs/
│   ├── DIAGRAMS.md            # Complete Mermaid diagrams for Fig. 1 to Fig. 10
│   └── PROJECT_REPORT.md      # Comprehensive 14-section MSBTE diploma project report
├── init_demo_data.py          # One-click database seed & populator script
├── run.py                     # Convenience launcher script
└── requirements.txt           # Project dependencies
```

## 🎓 Academic Submission Details
- **Subject:** Final Year Project (FYP) / Capstone Project
- **Branch:** Computer Engineering (Diploma)
- **Board:** Maharashtra State Board of Technical Education (MSBTE)
- **Roles Implemented:** SMB Owner, Support Manager, System Admin

# AI Customer Feedback Analyzer
### A Multi-Source Decision-Support System Using Natural Language Processing & Machine Learning
**Third-Year Diploma Project in Computer Engineering**  
**Maharashtra State Board of Technical Education (MSBTE)**

---

## 1. Introduction
In today's digital economy, customer opinion is the most direct and actionable source of business intelligence. Customer reviews posted on Google Maps, app store ratings, helpdesk tickets, and survey responses reveal what customers appreciate, where operational friction exists, and why churn happens.

For Small and Medium Businesses (SMBs), customer feedback arrives across multiple fragmented platforms in unstructured natural language. Without a unified system to collect, normalize, and interpret this feedback, valuable insights remain buried and urgent complaints go unnoticed. 

The **AI Customer Feedback Analyzer** is an end-to-end, lightweight decision-support system designed specifically for SMBs. It automatically ingests feedback across diverse channels (Google Play Store, Google Business Profile, Zendesk/Helpdesk webhooks, surveys, and bulk CSV files), applies automated NLP pipelines to clean PII and score sentiment intensity ($S \in [-1, +1]$), groups comments into recurring themes via sentence embeddings and clustering, and raises statistical anomaly alerts ($z > 2.5$) for sudden negative spikes.

---

## 2. Problem Statement & Motivation
### 2.1 Problem Statement
Small and medium businesses receive customer feedback from numerous channels such as Google Reviews, app stores, support tickets, surveys, and social media. However, this feedback remains scattered and unstructured, making it difficult to analyze at scale. Manual review is slow, subjective, and inconsistent, while existing enterprise CX suites (e.g., Qualtrics, Medallia) are prohibitively expensive and excessively complex for smaller teams. Consequently, businesses cannot detect sentiment trends, identify recurring issues, or respond quickly to urgent complaints.

### 2.2 Why is this System Needed?
1. **Scattered Feedback Silos:** Opinions are fragmented across review sites, app stores, ticketing systems, and email. No single panoramic view exists.
2. **Manual Review Bottleneck:** Reading hundreds of raw comments is labor-intensive, biased by human inconsistency, and lacks trend persistence.
3. **Delayed Response to Urgent Issues:** Serious escalations (e.g., billing fraud, safety issues, app crash loops) often go unnoticed for days, resulting in brand damage and customer churn.
4. **Enterprise CX Pricing Barrier:** High licensing costs and dedicated data analyst requirements put enterprise tools out of reach for SMBs.
5. **Unstructured Free-Text Growth:** Star ratings alone fail to explain *why* a customer is unhappy. Granular text analytics is mandatory.

### 2.3 Key Advantages Over Existing Approaches
- **Affordable by Design:** Built using proven open-source NLP and ML libraries running efficiently on standard commodity hardware.
- **Automated End-to-End:** Ingestion, PII masking, sentiment classification, topic discovery, and anomaly detection occur automatically.
- **Unified Multi-Source View:** Reviews, tickets, surveys, and CSV uploads are analyzed side-by-side in one dashboard.
- **Proactive Anomaly Alerts:** Uses rolling 28-day statistical baseline modeling ($z$-score $> 2.5$) to notify stakeholders of emerging crises.

---

## 3. System Architecture & Features
The system comprises six core functional modules:
1. **Multi-Source Data Ingestion:** Connectors for Google Play, Google Business Profile, webhooks, customer surveys, and CSV/Excel batch upload with SHA-256 deduplication.
2. **Text Pre-Processing & Normalisation:** Strips HTML, signatures, URLs; detects language; and masks sensitive PII (emails, phone numbers, credit cards).
3. **AI Sentiment Classification:** Softmax probability estimation yielding $P(pos), P(neu), P(neg)$, calculating signed intensity score $S = P(pos) - P(neg)$, with low-confidence fallback cascades.
4. **Theme & Topic Clustering:** TF-IDF and Sentence-BERT embeddings paired with centroid similarity matching to cluster items into themes (e.g., *App Bugs & Performance*, *Billing & Refunds*, *Delivery & Logistics*, *Customer Support*, *Product Quality*).
5. **Real-Time Alert Engine:** Anomaly detection evaluating daily negative share against rolling 28-day baseline mean ($\mu$) and standard deviation ($\sigma$). Urgency triggers for critical keywords (*refund*, *scam*, *fraud*, *cancel*) and extreme negativity ($S \le -0.70$).
6. **Analytics Dashboard & Reports:** Executive dashboard displaying Net Sentiment Score (NSS), trend charts, channel breakdowns, theme matrices, urgent queue management, and CSV report export.

---

## 4. Review of Literature
| Approach | Strengths | Limitations | Cost / Effort |
| :--- | :--- | :--- | :--- |
| **Manual Review** | High human context; zero software setup | Slow, subjective, not scalable, no trends | Very high labor cost |
| **Legacy Survey Tools** | Structured numeric rating analysis | Free-text unanalyzed; isolated to survey forms | Low-to-medium subscription |
| **Enterprise CX Suites** | Feature-rich, multi-channel connectors | Excessive configuration, requires dedicated analysts | Prohibitive enterprise licensing |
| **Proposed AI Analyzer** | Automated, multi-source, statistical alerts, local AI | Model fine-tuning required for local slang | Near-zero per-item cost |

---

## 5. Stakeholders & Role-Based Access Control (RBAC)

### Table 2: User Roles and Permission Matrix
| Functionality | SMB Owner | Support Manager | System Admin |
| :--- | :---: | :---: | :---: |
| Login & View Executive Dashboard | Yes | Yes | Yes |
| Add / Remove Feedback Sources | Yes | No | Yes |
| Upload CSV / Excel Feedback | Yes | Yes | Yes |
| View Urgent Complaints Queue | Yes | Yes | No |
| Mark / Assign Complaint Status | No | Yes | No |
| Configure Alert Rules & Thresholds | Yes | Yes | No |
| Export Reports (CSV / Print) | Yes | Yes | No |
| Manage Users & System Roles | No | No | Yes |
| Update AI Models & Parameters | No | No | Yes |

---

## 6. Plan of Work (16-Week Schedule)
### Table 3: Phase-Wise Work Schedule
- **Phase 1 (Weeks 1–2):** Synopsis and Requirement Analysis
- **Phase 2 (Weeks 3–5):** Design and Architecture (DFDs, UML, ER, Database Design)
- **Phase 3 (Weeks 6–10):** Core Development & AI Pipeline (Connectors, FastAPI, NLP Models, Alert Engine, Dashboard UI)
- **Phase 4 (Weeks 11–13):** Testing, Model Evaluation, Anomaly Calibration & Bug Fixing
- **Phase 5 (Weeks 14–16):** Final Documentation, User Manual, Demonstration & Submission

---

## 7. Core NLP & Mathematical Algorithms

### 7.1 Text Classification & Scoring Algorithm
1. **Input:** Ingest raw feedback record $(text, source, timestamp, rating)$.
2. **Normalise & De-duplicate:** Remove HTML tags, email signatures, URLs. Compute SHA-256 hash of $(source\_id, external\_id, text)$; discard if duplicate exists.
3. **PII Masking:** Regex substitution for emails $\to$ `[EMAIL_MASKED]`, phones $\to$ `[PHONE_MASKED]`, card numbers $\to$ `[CARD_MASKED]`.
4. **Sentiment Probabilities:** Infer probabilities $P(pos), P(neu), P(neg)$ using transformer-lexicon cascade with negation and intensifier context.
5. **Intensity Score Calculation:**
   $$S = P(pos) - P(neg) \quad \text{where } -1.0 \le S \le +1.0$$
   $$\text{Label} = \begin{cases} 
   \text{Positive} & \text{if } S \ge +0.25 \\
   \text{Negative} & \text{if } S \le -0.25 \\
   \text{Neutral} & \text{otherwise}
   \end{cases}$$
6. **Confidence Threshold:** If $\max(P) < 0.60$, execute contextual fallback re-evaluation.
7. **Embeddings & Theme Clustering:** Compute feature representation, calculate cosine similarity against theme centroids, extract top keywords.
8. **Urgency Assessment:** If critical keywords (*refund, scam, fraud, cancel, lawsuit*) match or $S \le -0.70$, assign urgency score $\ge 60/100$.
9. **Persistence:** Commit records to `feedback_items` and `sentiment_logs`.

### 7.2 Net Sentiment Score (NSS)
The primary customer experience benchmark displayed on the executive dashboard:
$$\text{NSS} = \left( \frac{\text{Positive Count} - \text{Negative Count}}{\text{Total Count}} \right) \times 100$$
*(Range: $-100$ to $+100$)*

### 7.3 Statistical Anomaly Detection
To detect abnormal sentiment deteriorations:
$$z = \frac{p - \mu}{\sigma}$$
Where:
- $p$ is the current time-window negative feedback share $\frac{\text{Negative}}{\text{Total}}$.
- $\mu$ is the rolling 28-day historical mean of daily negative share.
- $\sigma$ is the rolling 28-day historical standard deviation.
- If $z > 2.50$ and minimum volume criteria are satisfied, an anomaly alert is dispatched.

---

## 8. Complete System Diagrams
*(Full Mermaid code and visual graphs are provided in [DIAGRAMS.md](file:///d:/fyp%20project/docs/DIAGRAMS.md))*
- **Fig. 1:** Overall System Architecture
- **Fig. 2:** Gantt Chart Timeline (16 Weeks)
- **Fig. 3:** NLP Processing Pipeline Block Diagram
- **Fig. 4:** Entity-Relationship (ER) Diagram
- **Fig. 5:** DFD Level 0 (Context Diagram)
- **Fig. 6:** DFD Level 1
- **Fig. 7:** DFD Level 2 (Sentiment & Alert Subsystems)
- **Fig. 8:** System Flowchart
- **Fig. 9:** Use Case Diagram
- **Fig. 10:** Sequence Diagram (Ingestion to Dashboard Render)

---

## 9. Technology Stack
- **Back End:** Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, Pydantic
- **AI / ML Layer:** Scikit-learn, NumPy, TF-IDF Vectorization, Softmax Probability Engine, Regex PII Engine
- **Database:** SQLite (local development / demonstration) / PostgreSQL with optional pgvector
- **Front End:** HTML5, Modern Vanilla CSS (Glassmorphism, CSS Custom Properties, Responsive Grid), JavaScript (ES6+ Canvas 2D dynamic charts)
- **Alert Channels:** In-App Live Feed, SMTP, Webhook notifications

---

## 10. Conclusion
The **AI Customer Feedback Analyzer** delivers an effective, low-cost solution for small and medium businesses to transform chaotic customer opinions into clear intelligence. By combining automated ingestion, robust PII masking, calibrated sentiment scoring, dynamic theme discovery, and statistical anomaly detection into an intuitive web dashboard, the project bridges the gap between manual spreadsheets and complex enterprise platforms.

# AI Customer Feedback Analyzer - System Diagrams & Visual Architecture
**Third-Year Computer Engineering Diploma Project (MSBTE)**

This document contains complete, standards-compliant **Mermaid diagrams** for all figures (Fig. 1 to Fig. 10) specified in the project report. These can be viewed directly in markdown viewers (GitHub, VS Code Markdown Preview) and exported for project reports, presentations, and viva.

---

## Fig. 1: Overall System Architecture
Shows the end-to-end data pipeline from multi-channel ingestion, queue/pre-processing, NLP analysis workers, database storage, and the FastAPI application layer serving the dashboard and alert engine.

```mermaid
graph TB
    subgraph Multi_Source_Ingestion["1. Multi-Source Ingestion Layer"]
        S1["Google Play Reviews"]
        S2["Google Business Profile"]
        S3["Helpdesk Tickets (Webhook)"]
        S4["Customer Surveys"]
        S5["Bulk CSV / Excel Upload"]
    end

    subgraph Ingestion_Queue["2. Ingestion & Pre-Processing"]
        IQ["FastAPI Ingestion Endpoint / Queue"]
        PP["Text Normaliser & Cleaner<br/>(HTML Strip, PII Masking, De-duplication)"]
    end

    subgraph NLP_Pipeline["3. AI / NLP Processing Engine"]
        SENT["Transformer Sentiment Classifier<br/>(cardiffnlp/roberta / VADER Hybrid)<br/>Score S = P(pos) - P(neg)"]
        CONF{"Confidence ≥ 0.60?"}
        LLM["Fallback LLM / Aspect Refiner"]
        EMB["Sentence-BERT Embeddings<br/>(all-MiniLM-L6-v2)"]
        CLUS["Theme Clusterer<br/>(Cosine Similarity + TF-IDF Keywords)"]
        URG["Urgency & Critical Keyword Scanner<br/>(refund, scam, cancel, S ≤ -0.7)"]
    end

    subgraph Data_Storage["4. Persistent Storage (PostgreSQL / SQLite)"]
        DB[("Database<br/>Users | Sources | Feedback_Items<br/>Sentiment_Logs | Themes | Alerts")]
    end

    subgraph App_Services["5. Application Services & Alert Engine"]
        ALERT["Real-time Alert Engine<br/>(Z-Score Anomaly: z > 2.5)"]
        API["FastAPI REST & Webhook API"]
        NOTIF["Notification Channels<br/>(E-mail SMTP / Slack Webhooks)"]
    end

    subgraph Frontend_UI["6. Presentation Layer"]
        UI["Modern Responsive Analytics Dashboard<br/>(Net Sentiment Score, Trends, Themes, Urgent Complaints)"]
        ROLES["Role Views: SMB Owner | Support Manager | System Admin"]
    end

    S1 & S2 & S3 & S4 & S5 --> IQ
    IQ --> PP
    PP --> SENT
    SENT --> CONF
    CONF -- "No (< 0.60)" --> LLM
    CONF -- "Yes" --> EMB
    LLM --> EMB
    EMB --> CLUS
    CLUS --> URG
    URG --> DB
    DB <--> API
    API --> ALERT
    ALERT --> NOTIF
    API <--> UI
    UI --- ROLES
```

---

## Fig. 2: Timeline (Gantt) Diagram
16-Week Phase-Wise Schedule matching Table 3 of the project report.

```mermaid
gantt
    title AI Customer Feedback Analyzer - 16-Week Project Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  W%W
    
    section Phase 1: Synopsis & Req Analysis
    Topic Finalisation & Survey       :done, p1_1, 2026-01-05, 1w
    Requirement Gathering & Synopsis   :done, p1_2, after p1_1, 1w

    section Phase 2: Design & Architecture
    System Architecture & ER Design    :active, p2_1, after p1_2, 1w
    DFDs & UML Diagrams Drafting       :active, p2_2, after p2_1, 1w
    UI Wireframes & Prototype Specs    :active, p2_3, after p2_2, 1w

    section Phase 3: Core Dev & AI Pipeline
    Connectors, Ingestion & DB Schema  :p3_1, after p2_3, 1w
    NLP Preprocessing & Sentiment Engine:p3_2, after p3_1, 1w
    Sentence Embeddings & Theme Cluster:p3_3, after p3_2, 1w
    Real-time Anomaly Alert Engine     :p3_4, after p3_3, 1w
    Interactive Web Dashboard Build    :p3_5, after p3_4, 1w

    section Phase 4: Testing & Integration
    Unit & Integration Testing         :p4_1, after p3_5, 1w
    Model Evaluation on Labelled Sample :p4_2, after p4_1, 1w
    System Tuning & Bug Fixing         :p4_3, after p4_2, 1w

    section Phase 5: Documentation & Presentation
    Project Report & User Manual Prep  :p5_1, after p4_3, 1w
    Demonstration Rig & Viva Rehearsal :p5_2, after p5_1, 1w
    Final Presentation & Submission    :p5_3, after p5_2, 1w
```

---

## Fig. 3: NLP Processing Pipeline (Block Diagram)
Illustrates the exact 12-step data flow algorithm through normalisation, sentiment, clustering, urgency scoring, anomaly detection, and dashboard updates.

```mermaid
flowchart TD
    A["Step 1: Raw Feedback Input<br/>(Text, Source, Timestamp, Rating)"] --> B["Step 2: Normalisation & De-duplication<br/>(Strip HTML, URLs, Signatures, Compute Hash)"]
    B --> C["Step 3: Language Detection & PII Masking<br/>(Mask Emails, Phone Numbers)"]
    C --> D["Step 4: Sentiment Classifier<br/>(Compute P_pos, P_neu, P_neg)"]
    D --> E["Step 5: Intensity Score Calculation<br/>S = P_pos - P_neg (-1.0 ≤ S ≤ +1.0)<br/>Label: Pos if S ≥ 0.25, Neg if S ≤ -0.25, Else Neu"]
    E --> F{"Step 6: Confidence Check<br/>Max(P) ≥ 0.60?"}
    F -- "Low (< 0.60) / Mixed" --> G["LLM Fallback / Context Re-evaluation"]
    F -- "High (≥ 0.60)" --> H["Step 7: Sentence Embedding<br/>(Sentence-BERT / MiniLM Vector)"]
    G --> H
    H --> I["Step 8: Theme Assignment<br/>Cosine Similarity to Centroids / K-Means<br/>Extract TF-IDF Keywords"]
    I --> J["Step 9: Urgency Scoring<br/>Flag keywords: 'refund', 'scam', 'fraud', 'cancel'<br/>or S ≤ -0.70"]
    J --> K[("Step 10: Persist to DB<br/>Feedback_Items & Sentiment_Logs")]
    K --> L["Step 11: Statistical Anomaly Detection<br/>Rolling 28-day Mean μ, Std Dev σ<br/>Z = (p - μ) / σ > 2.5"]
    L --> M["Step 12: Outputs<br/>Update Net Sentiment Score (NSS), Live Dashboard, Slack / E-mail Alerts"]
```

---

## Fig. 4: Entity Relationship (ER) Diagram
Shows the 6 relational entities, primary keys (PK), foreign keys (FK), attributes, and cardinalities according to Table 4.

```mermaid
erDiagram
    USERS ||--o{ SOURCES : manages
    USERS ||--o{ ALERTS : receives
    SOURCES ||--o{ FEEDBACK_ITEMS : supplies
    SOURCES ||--o{ ALERTS : triggers
    FEEDBACK_ITEMS ||--|| SENTIMENT_LOGS : produces
    THEMES ||--o{ FEEDBACK_ITEMS : categorises

    USERS {
        int user_id PK
        string name
        string email
        string password_hash
        string role "Owner | Manager | Admin"
        datetime created_at
    }

    SOURCES {
        int source_id PK
        int user_id FK
        string source_type "google_play | google_business | helpdesk | survey | csv"
        string name
        string api_config
        string status "active | paused | error"
        datetime last_synced_at
    }

    FEEDBACK_ITEMS {
        int feedback_id PK
        int source_id FK
        int theme_id FK
        string external_id
        text text
        int rating
        string language
        float urgency_score
        datetime created_at
        datetime ingested_at
    }

    SENTIMENT_LOGS {
        int log_id PK
        int feedback_id FK
        string label "positive | neutral | negative"
        float score "-1.0 to +1.0"
        float confidence
        string model_name
        datetime processed_at
    }

    THEMES {
        int theme_id PK
        string label "UI Bugs | Billing | Delivery | Staff Behaviour"
        string keywords
        datetime created_at
    }

    ALERTS {
        int alert_id PK
        int user_id FK
        int source_id FK
        string alert_type "sentiment_drop | critical_keyword | high_urgency"
        string severity "low | medium | high | critical"
        text message
        string channel "in_app | email | slack"
        string status "active | acknowledged | resolved"
        datetime triggered_at
    }
```

---

## Fig. 5: DFD Level 0 (Context Diagram)
Depicts the entire system boundary, external entities, and high-level input/output flows.

```mermaid
flowchart LR
    FS["Feedback Sources<br/>(Google Reviews, Play Store,<br/>Helpdesk Webhooks, CSV)"]
    OWNER["SMB Owner"]
    MGR["Support Manager"]
    ADMIN["System Admin"]
    NOTIF["Notification Services<br/>(E-mail SMTP / Slack)"]

    SYS(("0.0<br/>AI Customer Feedback<br/>Analyzer System"))

    FS -- "Raw Feedback Data & Webhooks" --> SYS
    OWNER -- "Credentials, Alert Rules, Source Setup" --> SYS
    MGR -- "Complaint Status Updates, Filters" --> SYS
    ADMIN -- "Model Configs, Connector Settings, User Roles" --> SYS

    SYS -- "NSS Metrics, Trends & Summary Reports" --> OWNER
    SYS -- "Urgent Complaint Lists & Action Status" --> MGR
    SYS -- "System Health, Logs & Ingestion Status" --> ADMIN
    SYS -- "High-Urgency & Anomaly Alert Triggers" --> NOTIF
```

---

## Fig. 6: DFD Level 1
Divides the system into 6 core processes and 6 persistent data stores (D1 to D6).

```mermaid
flowchart TD
    %% Entities
    U["User (Owner / Manager / Admin)"]
    EXT["External Sources & APIs"]
    NOTIF["Notification Service"]

    %% Processes
    P1["1.0 Manage Users & Sources"]
    P2["2.0 Ingest & Pre-process Feedback"]
    P3["3.0 Classify Sentiment"]
    P4["4.0 Detect Themes & Clusters"]
    P5["5.0 Monitor & Generate Alerts"]
    P6["6.0 Generate Dashboard & Reports"]

    %% Data Stores
    D1[("D1 Users")]
    D2[("D2 Sources")]
    D3[("D3 Feedback_Items")]
    D4[("D4 Sentiment_Logs")]
    D5[("D5 Themes")]
    D6[("D6 Alerts")]

    %% Flows
    U -->|Login, Config| P1
    P1 <--> D1
    P1 <--> D2

    EXT -->|Raw Feedback / CSV| P2
    D2 -->|Active Config| P2
    P2 -->|Normalised Records| D3

    D3 -->|Clean Text| P3
    P3 -->|Scores & Labels| D4

    D3 & D4 -->|Text Vectors| P4
    P4 <--> D5
    P4 -->|Theme IDs| D3

    D3 & D4 -->|Hourly/Daily Aggregates| P5
    P5 -->|New Alerts| D6
    P5 -->|Notification Dispatch| NOTIF

    D3 & D4 & D5 & D6 -->|Metrics & Feed| P6
    P6 -->|Visual Analytics & Exports| U
```

---

## Fig. 7: DFD Level 2 (Process 3.0 & Process 5.0)
Detailed expansion of Sentiment Classification (3.0) and Anomaly Alert Monitoring (5.0).

```mermaid
flowchart TD
    subgraph DFD_3["Process 3.0: Sentiment Classification Expansion"]
        D3_in[("D3 Feedback_Items")] --> P31["3.1 Retrieve Unprocessed Clean Text"]
        P31 --> P32["3.2 Language Detect & Tokenisation"]
        P32 --> P33["3.3 Transformer Inference / Probability Scoring"]
        P33 --> P34["3.4 Compute Intensity Score S = P_pos - P_neg"]
        P34 --> P35{"3.5 Confidence ≥ 0.60?"}
        P35 -- No --> P36["3.6 Fallback LLM / Heuristic Refiner"]
        P35 -- Yes --> P37["3.7 Assign Final Label & Confidence"]
        P36 --> P37
        P37 --> D4_out[("D4 Sentiment_Logs")]
    end

    subgraph DFD_5["Process 5.0: Anomaly Alert Engine Expansion"]
        D3_stat[("D3 Feedback_Items")] & D4_stat[("D4 Sentiment_Logs")] --> P51["5.1 Aggregate Hourly/Daily Negative Share (p)"]
        P51 --> P52["5.2 Compute Rolling 28-day Baseline (μ, σ)"]
        P52 --> P53["5.3 Calculate Z-Score: z = (p - μ) / σ"]
        P53 --> P54{"5.4 Anomaly or Critical Keyword Detected?"}
        P54 -- Yes --> P55["5.5 Cooldown & Duplicate Check"]
        P55 --> P56["5.6 Format Alert Payload & Store in D6"]
        P56 --> D6_out[("D6 Alerts")]
        P56 --> P57["5.7 Dispatch to SMTP / Slack Webhook"]
        P54 -- No --> P58["5.8 Normal Logging"]
    end
```

---

## Fig. 8: System Flowchart
Execution flow diagram corresponding to the 9 operational steps in Section 8.2.1.

```mermaid
flowchart TD
    Start([Start]) --> Login[/User Logs In/]
    Login --> AuthCheck{Valid Credentials?}
    AuthCheck -- No --> AuthErr[Display Error Message] --> Login
    AuthCheck -- Yes --> ActionChoice[/User adds Source or uploads CSV/]
    
    ActionChoice --> Fetch[Fetch or Receive Feedback Items]
    Fetch --> DupCheck{Item Exists? Check Source ID + Hash}
    DupCheck -- Yes --> Discard[Discard Duplicate Record] --> EndProc[Continue / Done]
    DupCheck -- No --> Clean[Clean HTML, Signatures, URLs & Mask PII]
    
    Clean --> RunSentiment[Classify Sentiment Probabilities]
    RunSentiment --> ConfCheck{Confidence ≥ 0.60?}
    ConfCheck -- No --> Fallback[Trigger LLM Fallback Refinement] --> Embed[Generate Embeddings]
    ConfCheck -- Yes --> Embed
    
    Embed --> ClusterTheme[Assign Theme Centroid & TF-IDF Keywords]
    ClusterTheme --> CheckUrgent[Compute Urgency: S ≤ -0.7 or Keyword Trigger]
    CheckUrgent --> SaveDB[(Save Item, Sentiment Log, Theme in DB)]
    
    SaveDB --> AnomalyCheck{Anomaly Detected? z > 2.5 or Urgent Spike}
    AnomalyCheck -- Yes --> TriggerAlert[Generate & Transmit Alert E-mail/Slack] --> UpdateDash[Update Dashboard Metrics]
    AnomalyCheck -- No --> UpdateDash
    
    UpdateDash --> Render[/Display NSS, Trends, Themes & Urgent Queue/]
    Render --> Done([End / Await Next Event])
```

---

## Fig. 9: Use Case Diagram
Visualises the role-based boundaries between SMB Owner, Support Manager, System Admin, and External Actors.

```mermaid
flowchart LR
    subgraph SystemBoundary["AI Customer Feedback Analyzer"]
        UC1((Login / Authentication))
        UC2((View Dashboard & NSS))
        UC3((Connect / Remove Feedback Source))
        UC4((Upload CSV / Excel Feedback))
        UC5((View Sentiment Trends))
        UC6((Export Reports CSV / PDF))
        UC7((Configure Alert Rules))
        UC8((View Urgent Complaints))
        UC9((Filter by Theme & Channel))
        UC10((Update Complaint Status))
        UC11((Manage Users & Roles))
        UC12((Monitor Ingestion Jobs))
        UC13((Update AI Models & Thresholds))
        
        UC_Inc1((Load Sentiment Metrics))
        UC_Inc2((Classify Sentiment))
        UC_Ext1((Send Alert Notification))
    end

    Owner["SMB Owner"]
    Manager["Support Manager"]
    Admin["System Admin"]
    SourceAPI["Feedback Source APIs"]
    NotifService["Notification Service (Email/Slack)"]

    %% Owner associations
    Owner --> UC1
    Owner --> UC2
    Owner --> UC3
    Owner --> UC4
    Owner --> UC5
    Owner --> UC6
    Owner --> UC7

    %% Manager associations
    Manager --> UC1
    Manager --> UC2
    Manager --> UC4
    Manager --> UC8
    Manager --> UC9
    Manager --> UC10
    Manager --> UC7

    %% Admin associations
    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC11
    Admin --> UC12
    Admin --> UC13

    %% Includes & Extends
    UC2 -.->|<<includes>>| UC_Inc1
    UC3 -.->|<<includes>>| UC_Inc2
    UC4 -.->|<<includes>>| UC_Inc2
    UC7 -.->|<<extends>>| UC_Ext1

    %% Secondary actor links
    UC3 --- SourceAPI
    UC_Ext1 --- NotifService
```

---

## Fig. 10: Sequence Diagram (Ingestion to Dashboard Render)
Illustrates message exchange across the Browser, Dashboard UI, FastAPI Server, Connector, NLP Engine, Database, Alert Engine, and Notification Services.

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Browser)
    participant UI as Dashboard UI
    participant API as FastAPI Server
    participant Conn as Connector / Ingestion Service
    participant NLP as NLP Engine
    participant DB as Database (SQLAlchemy)
    participant Alert as Alert Engine
    participant Notif as Notification Service

    User->>UI: 1. Add Source / Upload CSV File
    UI->>API: 2. POST /api/sources or /api/feedback/upload
    API->>Conn: 3. Trigger Ingestion (Async / On-demand)
    Conn->>DB: 4. Normalise, de-duplicate, save raw items
    Conn->>NLP: 5. Send raw items for processing
    activate NLP
    NLP->>NLP: 6. Clean PII, Sentiment Scoring, Embeddings, Theme Assign
    NLP->>DB: 7. Store Sentiment Logs & Theme Links
    deactivate NLP
    NLP->>Alert: 8. Trigger Anomaly & Urgency Check
    activate Alert
    opt Anomaly Z > 2.5 or Critical Keyword Match
        Alert->>DB: Record new Alert in D6
        Alert->>Notif: 9. Dispatch Alert (Email / Slack Webhook)
    end
    deactivate Alert
    User->>UI: 10. Open / Refresh Dashboard View
    UI->>API: 11. GET /api/analytics/metrics, /themes, /alerts
    API->>DB: 12. Query Aggregated NSS, Volume, Themes, Urgent Queue
    DB-->>API: Return Aggregated Records
    API-->>UI: 13. JSON Response (Metrics, Trends, Themes)
    UI-->>User: 14. Render Interactive Charts, Badges & Action Feed
```

# Ask Hospilot — Natural Language RAG Service

"Ask Hospilot" is a grounded retrieval-augmented generation (RAG) and Text-to-SQL intelligence engine for hospital staff. It allows doctors, nurses, and administrators to query complex operational data (bed availability, ward occupancy, staff rosters, patient vitals) using plain English questions.

---

## 🚀 How to Run Locally

### 1. Requirements & Setup
- Python 3.8+ (no external dependencies required for core execution).
- SQLite3 (built into Python standard library).

```bash
cd rag/ritheesh

# 1. Initialize and Seed the SQLite Database
python3 seed_data.py

# 2. Run the Test Suite
python3 test_rag.py

# 3. Launch the RAG Service API
python3 app.py
```

The service will start on `http://localhost:8080`.

### 2. Querying the Service via HTTP API

```bash
curl -X POST http://localhost:8080/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How many ICU beds are available right now?"}'
```

Example JSON Response:
```json
{
  "question": "How many ICU beds are available right now?",
  "is_answerable": true,
  "reasoning_sql": "SELECT COUNT(*) AS available_icu_beds FROM beds WHERE ward LIKE '%icu%' AND status = 'Available' AND is_active = 1",
  "rows_retrieved": [
    {
      "available_icu_beds": 6
    }
  ],
  "answer": "There are **6 ICU beds** available right now."
}
```

---

## 🏗️ Architecture & Pipeline Design

How a plain-English question turns into a grounded answer:

```
┌─────────────────────────┐
│ Plain-English Question │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐     Out-of-Scope (e.g. Satisfaction / Cafeteria)
│ Scope & Refusal Guard   ├─────────────────────────────────────────────────┐
└────────────┬────────────┘                                                 │
             │ In-Scope                                                     ▼
             ▼                                                    ┌──────────────────┐
┌─────────────────────────┐                                       │ Honest Refusal   │
│ Schema-Grounded SQL     │                                       │ (No Hallucinations│
│ Generator / Parser      │                                       └──────────────────┘
└────────────┬────────────┘
             │ Generated SQL
             ▼
┌─────────────────────────┐
│ Execute on SQLite DB    │
└────────────┬────────────┘
             │ Retrieved Rows & Metadata
             ▼
┌─────────────────────────┐
│ Answer Synthesizer      │
│ (Text + Reasoning SQL)  │
└─────────────────────────┘
```

1. **Scope & Refusal Guard**: Checks whether the question asks for out-of-domain metrics not stored in the schema (e.g., patient satisfaction, survey scores, canteen menu). If so, it halts immediately and returns an honest refusal response without hallucinating.
2. **Schema-Grounded SQL Generator**: Translates the natural language question into safe, deterministic SQL queries mapped directly against `beds`, `ipd_admissions`, `departments`, `vitals`, and `staff_roster`.
3. **Database Execution**: Queries the local SQLite database (`hospilot.db`) to fetch real empirical records.
4. **Transparent Reasoning Output**: Exposes the exact SQL query generated (`reasoning_sql`) and raw rows retrieved alongside the structured Markdown answer.

---

## 🧠 Design Choices & Rationales

- **SQLite Database**: SQLite is zero-config, portable, fast, and eliminates external database installation friction while supporting all standard ANSI SQL functions (`GROUP BY`, `ORDER BY`, `LEFT JOIN`, `subqueries`, `ROUND()`).
- **Grounding over Hallucination**: Rather than feeding raw prompt context into an LLM and hoping it doesn't make up numbers, we enforce a strict Text-to-SQL architecture. The SQL query acts as an audit trail.
- **Honest Failures**: Hospital operations demand high precision. Inventing patient satisfaction ratings or bed counts can disrupt clinical workflows. If data is absent, the system states what is missing and provides alternative contacts/tools.

---

## 🔮 Future Improvements (with more time)

1. **Vector Indexing for Unstructured Clinical Notes**: Add embeddings (ChromaDB / FAISS) for searching unformatted discharge summaries and doctor shift logs alongside tabular SQL data.
2. **Multi-Turn Context Memory**: Store session history to handle follow-up queries (e.g., Q1: "Which ward has highest occupancy?" -> Q2: "Show me the nurses on duty there").
3. **Automated Schema Refresh Sync**: Implement real-time synchronization hooks from HIS webhooks to keep `hospilot.db` live up to the minute.

# Vantage

An explainable OSINT entity disambiguation and triage platform. Vantage ingests raw output from SpiderFoot, Sherlock, and Maigret, clusters findings by platform and handle, and assigns transparent confidence scores backed by named evidence features. Results are surfaced through a full-stack web application with case management, real-time scan progress, and analyst annotation workflows.

Built as a final year dissertation project — BSc (Hons) Computer Science (Cyber Security), University of Plymouth.

---

## Project Structure

```
project/          Python pipeline (normalise, cluster, score, LLM judge)
  src/            Pipeline source modules
  tests/          164-test pytest suite
  results/        Pipeline output files (JSON)
webapp/
  backend/        FastAPI + Uvicorn backend
  frontend/       React + Vite frontend
spiderfoot/       SpiderFoot submodule
```

---

## Setup

### Pipeline

```bash
cd project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Web App

```bash
# Backend
cd webapp/backend
source ../../project/venv/bin/activate
cp .env.example .env   # fill in Supabase and Gemini keys
uvicorn main:app --reload

# Frontend (separate terminal)
cd webapp/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Running a Scan

From the web app, create a case, enter a target username, and click **Run Scan**. The pipeline runs SpiderFoot, Sherlock, and Maigret, normalises and clusters the results, scores each cluster, and invokes Gemini for plain-English rationale. Progress streams live via WebSocket.

To run the CLI pipeline directly:

```bash
cd project/src
python normalize_run.py
python cluster_run.py
python reduce_for_llm.py
python llm_judge_gemini.py
```

---

## Tests

```bash
cd project
source venv/bin/activate
python -m pytest tests/ -v
```

164 tests covering normalisation, clustering, scoring, and LLM judge logic.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `GEMINI_API_KEY` | Google Gemini API key |
| `OSINT_DRY_RUN` | Set to `1` to skip Gemini calls |

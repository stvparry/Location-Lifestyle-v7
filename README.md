# Location Lifestyle AI V7

A standalone Streamlit package combining personal lifestyle matching, a curated 200-place UK catalogue, Life Network, journey burden, gravity heat maps, comparisons and optional AI conversation.

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Optional AI
Add these Streamlit secrets:
```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "gpt-4.1-mini"
```

## Units and travel model
All user-facing distance and speed units are imperial:
- miles
- miles per hour
- minutes per one-way journey
- hours per month for return journeys

Prototype effective speeds:
- Car: 35 mph plus 10 minutes
- Rail: 50 mph plus 25 minutes
- Mixed: 40 mph plus 20 minutes

These estimates are not live routes, traffic predictions or rail timetables.

## Data status
The 200 rows are named real settlements with curated county/area assignments. Core candidate and network locations use individually entered rounded town-centre coordinates. Expansion coordinates have a lower precision flag and are excluded from any claim of authoritative routing. `data/quality_report.csv` records the structural checks. Reconciliation to OS Open Names identifiers remains the next authoritative-data step.

# 📍 Smart Address Intelligence for Last-Mile Delivery

An AI-powered address resolution system that converts messy, unstructured, and ambiguous Indian addresses — often written in **Hinglish or regional shorthand** — into precise geospatial coordinates with confidence scoring, smart routing, and a dual-frontend interface.

> Built for hackathon: solving the last-mile delivery failure problem in India.

---

## 🚩 The Problem

Addresses in India are frequently unstructured and landmark-based:
> *"Near the big tree, after the chai shop, first lane from main road"*
> *"Shiv Mandir ke peeche, Gali No 4, Gandhi Nagar"*

Standard geocoding APIs fail on these inputs. This system doesn't.

---

## ✨ Key Features

**Address Intelligence Pipeline**
- Transliterates and normalises Hinglish/regional text into clean English (e.g. *"ke peeche"* → *"Behind"*, *"gali"* → *"Lane"*)
- Deep-parses building names, street names, landmarks, and spatial relations (*"Opposite to..."*, *"Behind..."*, *"Next to..."*)
- ML-based historical correction using TF-IDF + nearest-neighbour matching against past successful deliveries
- Chain-of-thought **Reasoning Geocoder** that constructs smarter API queries rather than blindly forwarding raw text

**Geocoding & Routing**
- Multi-provider geocoding: **Google Maps → Mapbox → OpenStreetMap** (graceful fallback chain)
- Optimised Mapbox query generation based on Indian address patterns
- Turn-by-turn routing via **Google Directions API** (primary) or **OSRM** (free fallback)
- Geodesic distance calculation between delivery agent and destination

**Confidence Scoring**
- ML regressor trained on delivery outcome data outputs a 0–1 delivery confidence score
- Heuristic completeness scorer evaluates field presence (house number, street, landmark, pincode)
- Quality labels: `Success` / `Failed` with per-field breakdown

**Dual Frontend**
- 🖤 **FastAPI + Leaflet.js** — dark-mode "Cyberpunk" UI with live routing, pulse-animated markers, and agent tracking
- 📊 **Streamlit Dashboard** — step-by-step pipeline debugger with 3D PyDeck maps, AI reasoning chain view, and raw JSON output

---

## 🏗️ Architecture

```
Raw Address Input
      │
      ▼
┌─────────────────┐
│  1. Normalizer  │  Hinglish → English, abbreviation expansion
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. Parser      │  Extracts: building, street, landmarks, spatial relations
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. Corrector   │  Rule-based + ML (TF-IDF / fuzzy) historical correction
└────────┬────────┘
         ▼
┌──────────────────────┐
│  4. Reasoning        │  Chain-of-thought query builder →
│     Geocoder         │  Google Maps / Mapbox / OpenStreetMap
└────────┬─────────────┘
         ▼
┌─────────────────┐
│  5. Scorer      │  ML regressor + heuristic → confidence score & label
└────────┬────────┘
         ▼
┌─────────────────┐
│  6. Router      │  Google Directions → OSRM fallback → distance & ETA
└─────────────────┘
```

---

## 🗂️ File Structure

```
├── api.py                  # FastAPI backend (REST API + HTML frontend serving)
├── app.py                  # Streamlit dashboard (debugging & visualisation)
├── main.py                 # CLI pipeline runner
├── demo_pipeline.py        # Demo script with Hinglish address examples
├── test_norm.py            # Unit tests for the normalizer
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── templates/
│   └── index.html          # Leaflet.js dark-mode frontend
└── src/
    ├── normalizer.py        # Hinglish/regional text → clean English
    ├── parser.py            # Basic address component extractor
    ├── advanced_parser.py   # Deep parser (landmarks, spatial relations, categories)
    ├── corrector.py         # Rule-based standardisation
    ├── ml_corrector.py      # ML historical correction (TF-IDF + NearestNeighbors)
    ├── reasoning_geocoder.py# Chain-of-thought geocoding logic
    ├── mapbox_optimizer.py  # Optimised Mapbox query generation
    ├── scorer.py            # ML + heuristic confidence scoring
    ├── geocoder.py          # Basic geocoding wrapper
    └── train_model.py       # Train the delivery confidence ML model
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + Uvicorn |
| NLP / Parsing | Regex, fuzzywuzzy, python-Levenshtein |
| ML | scikit-learn (TF-IDF, NearestNeighbors, Regressor) |
| Geocoding APIs | Google Maps, Mapbox, OpenStreetMap (Nominatim) |
| Routing | Google Directions API, OSRM |
| Distance | geopy (Geodesic / Haversine) |
| Frontend (Primary) | HTML5, JavaScript, Tailwind CSS, Leaflet.js |
| Frontend (Debug) | Streamlit, PyDeck (3D maps) |
| Deep Learning | Transformers, PyTorch (for advanced NLP modules) |
| Regional NLP | indic-nlp-library |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Google Maps API key and/or Mapbox API key *(optional but recommended)*

### Installation

```bash
git clone https://github.com/yourusername/smart-address-intelligence.git
cd smart-address-intelligence

pip install -r requirements.txt
```

### Environment Setup

```bash
cp .env.example .env
```

Edit `.env` with your keys:
```env
GOOGLE_MAPS_API_KEY=your_google_key_here
MAPBOX_API_KEY=your_mapbox_key_here
```

> Both keys are optional. The system falls back to OpenStreetMap (Nominatim) + OSRM if no keys are provided.

---

## ▶️ Running the App

### Option A — FastAPI Web App (Recommended)
```bash
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
```
Open **http://localhost:8000** for the dark-mode delivery UI.

### Option B — Streamlit Dashboard
```bash
streamlit run app.py
```
Open the URL shown in the terminal (typically **http://localhost:8501**) for the step-by-step pipeline debugger.

### Option C — CLI Demo
```bash
python demo_pipeline.py
```
Runs the full pipeline on two example addresses (English and Hinglish) and prints each stage's output.

---

## 🧪 Testing

```bash
# Test address normalisation
python test_norm.py

# Train / retrain the confidence scoring ML model
python src/train_model.py
```

---

## 🌐 API Reference

### `POST /api/resolve`

Resolves a raw address into structured data, coordinates, confidence score, and route.

**Request body:**
```json
{
  "raw_address": "Near Apollo Hospital, Main Road, Vijayawada",
  "city": "Vijayawada",
  "state": "Andhra Pradesh",
  "agent_lat": 16.5062,
  "agent_lon": 80.6480
}
```

**Response:**
```json
{
  "normalized": "Near Apollo Hospital, Main Road, Vijayawada",
  "standardized": "Apollo Hospital Area, Main Road, Vijayawada",
  "parsed": { "building": {...}, "locality": {...}, "landmarks": [...] },
  "geocoding": { "estimated_coordinates": {"latitude": 16.51, "longitude": 80.63}, "reasoning": {...} },
  "confidence": { "score": 0.74, "label": "Success", "heuristic": 80 },
  "distance": { "km": 1.42, "meters": 1420 },
  "route": { "path": [[...], ...], "source": "Google Directions" }
}
```


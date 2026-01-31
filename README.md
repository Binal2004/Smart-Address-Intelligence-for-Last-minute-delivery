# 📍 Smart Address Intelligence for Last-Mile Delivery

## 🚀 Project Overview
This project is an **AI-powered Address Intelligence System** designed to solve the "Last-Mile Delivery" problem in India (and similar unstructured address landscapes). It takes messy, unstructured, and ambiguous address text (often in "Hinglish") and converts it into precise geospatial coordinates and structured data.

It features a **Dual-Frontend Architecture**:
1.  **FastAPI + Dedicated Frontend**: A modern, high-performance web app with real-time routing, distance calculation, and "Cyberpunk" dark-mode UI.
2.  **Streamlit Prototype**: A data-science focused dashboard for debugging and visualizing the AI pipeline steps.

## 🛠️ Tech Stack

### **Backend & Core Logic**
-   **Language**: Python 3.10+
-   **Framework**: FastAPI (High-performance Async API)
-   **NLP & Parsing**:
    -   `re` (Regex) for Deep Parsing (Landmarks, Spatial Relations).
    -   `fuzzywuzzy` & `python-Levenshtein` for fuzzy string matching.
    -   `scikit-learn` (TF-IDF + NearestNeighbors) for ML-based Historical Corrections.
-   **Geospatial**:
    -   `geopy`: Distance calculations (Haversine/Geodesic) and geocoding wrappers.
    -   **APIs**: Google Maps Platform (Directions, Geocoding), Mapbox (Optimization), OSRM (Open Source Routing).

### **Frontend (Dedicated)**
-   **Core**: HTML5, JavaScript (ES6+)
-   **Styling**: Tailwind CSS (Utility-first framework)
-   **Maps**: Leaflet.js (Interactive Maps) + CartoDB Dark Matter Tiles.
-   **Visualization**: Custom Pulse Animations for Agent/Destination markers.

### **Frontend (Legacy Prototype)**
-   **Framework**: Streamlit
-   **Maps**: PyDeck (3D visualizations)

---

## 📦 Installation & Setup

### 1. Prerequisites
-   Python 3.10 or higher
-   Node.js (Optional, for advanced frontend dev, but standard HTML/JS works out of the box)
-   API Keys (Optional but Recommended):
    -   **Google Maps API Key**: For accurate routing and geocoding.
    -   **Mapbox API Key**: For alternative geocoding strategies.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
*Note: Ensure `fastapi`, `uvicorn`, `jinja2`, `python-multipart` are installed.*

### 3. Environment Configuration
Create a `.env` file in the root directory:
```env
GOOGLE_MAPS_API_KEY=your_google_key_here
MAPBOX_API_KEY=your_mapbox_key_here
```

---

## 🏃‍♂️ How to Run

### **Option A: Run the Dedicated Web App (Recommended)**
This launches the modern FastAPI server with the dark-mode frontend.

1.  Open your terminal.
2.  Run the server:
    ```bash
    python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
    ```
3.  Open your browser and navigate to:
    👉 **http://localhost:8000**

### **Option B: Run the Streamlit Dashboard**
Useful for inspecting the internal logic and debugging the AI pipeline.

1.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```
2.  Access it at the URL provided in the terminal (usually http://localhost:8501).

---

## 🧠 Key Features

1.  **Unstructured Address Parsing**: Extracts building names, street names, landmarks, and spatial relations (e.g., "Opposite to...", "Behind...") from raw text.
2.  **Reasoning Geocoder**: A custom logic layer that doesn't just blindly query APIs but "thinks" about the address structure to form better queries.
3.  **ML Historical Correction**: Uses a database of past successful deliveries to auto-correct typos and predict the correct location for ambiguous addresses.
4.  **Smart Routing**:
    -   **Primary**: Google Directions API (Traffic-aware, precise).
    -   **Fallback**: OSRM (Free, Open Source) if Google keys are missing.
5.  **Live Agent Tracking**: Simulates (or detects) the delivery agent's real-time location to calculate distance and ETA.

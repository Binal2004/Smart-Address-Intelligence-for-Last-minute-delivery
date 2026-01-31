import os
import sys
import json
import math
import requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from geopy.distance import geodesic

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.normalizer import AddressNormalizer
from src.advanced_parser import AdvancedAddressParser
from src.corrector import AddressCorrector
from src.ml_corrector import MLCorrector
from src.reasoning_geocoder import ReasoningGeocoder
from src.scorer import AddressConfidenceScorer

# Load environment variables
load_dotenv()

app = FastAPI(title="Smart Address Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Models
normalizer = AddressNormalizer()
parser = AdvancedAddressParser()
corrector = AddressCorrector()
ml_corrector = MLCorrector()
scorer = AddressConfidenceScorer()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY")

geocoder = ReasoningGeocoder(google_api_key=GOOGLE_API_KEY, mapbox_api_key=MAPBOX_API_KEY)

# Setup Templates
templates = Jinja2Templates(directory="templates")

# Models
class AddressRequest(BaseModel):
    raw_address: str
    city: str = "Vijayawada"
    state: str = "Andhra Pradesh"
    agent_lat: Optional[float] = None
    agent_lon: Optional[float] = None

class RouteRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float

# Helper Functions
def decode_polyline(polyline_str):
    index, lat, lng = 0, 0, 0
    coordinates = []
    length = len(polyline_str)
    while index < length:
        b, shift, result = 0, 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20: break
        dlat = ~(result >> 1) if (result & 1) else (result >> 1)
        lat += dlat
        shift, result = 0, 0
        while True:
            b = ord(polyline_str[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20: break
        dlng = ~(result >> 1) if (result & 1) else (result >> 1)
        lng += dlng
        coordinates.append([lat / 1e5, lng / 1e5]) # Leaflet expects [lat, lng]
    return coordinates

def get_route_osrm(start_lat, start_lon, end_lat, end_lon):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
        headers = {'User-Agent': 'TraeAI-Hackathon-Project/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                # OSRM returns [lon, lat], Leaflet needs [lat, lon]
                coords = data["routes"][0]["geometry"]["coordinates"]
                return [[lat, lon] for lon, lat in coords]
    except Exception:
        pass
    return None

def get_route_google(start_lat, start_lon, end_lat, end_lon, api_key):
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&key={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK" and len(data["routes"]) > 0:
                polyline = data["routes"][0]["overview_polyline"]["points"]
                return decode_polyline(polyline)
    except Exception:
        pass
    return None

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "google_key": GOOGLE_API_KEY,
        "mapbox_key": MAPBOX_API_KEY
    })

@app.post("/api/resolve")
async def resolve_address(req: AddressRequest):
    # 1. Normalize
    normalized_text = normalizer.normalize(req.raw_address)
    
    # 2. Parse
    ai_result = parser.parse(normalized_text, req.city)
    
    # 3. Correct
    # standardized_address = corrector.correct(ai_result) # Optional for now
    
    # 4. Geocode
    geo_result = geocoder.reason_and_geocode(ai_result, req.city, req.state, req.raw_address)
    
    # 5. Score
    parsed_for_scorer = {
        "house_number": ai_result["parsed"]["building"]["number"],
        "street": ai_result["parsed"]["locality"]["street"],
        "landmark": ai_result["parsed"]["landmarks"][0]["text"] if ai_result["parsed"]["landmarks"] else None,
        "city": ai_result["parsed"]["locality"]["city"],
        "pincode": ai_result["parsed"]["locality"]["pincode"]
    }
    
    geo_coords = geo_result.get("estimated_coordinates")
    geo_tuple = (None, None, None)
    dest_lat, dest_lon = None, None
    
    if geo_coords:
        dest_lat = geo_coords.get("latitude")
        dest_lon = geo_coords.get("longitude")
        geo_tuple = (dest_lat, dest_lon, geo_result.get("reasoning", {}).get("primary_landmark"))

    ml_score = scorer.calculate_score(parsed_for_scorer, geo_tuple, raw_text=req.raw_address)
    ml_label = scorer.get_quality_label(ml_score)
    
    # 6. Distance & Route
    distance_km = None
    route_path = None
    route_source = "None"
    
    if dest_lat and dest_lon and req.agent_lat and req.agent_lon:
        # Calculate Haversine Distance
        distance_km = geodesic((req.agent_lat, req.agent_lon), (dest_lat, dest_lon)).km
        
        # Get Route
        if GOOGLE_API_KEY:
            route_path = get_route_google(req.agent_lat, req.agent_lon, dest_lat, dest_lon, GOOGLE_API_KEY)
            if route_path:
                route_source = "Google Directions"
        
        if not route_path:
            route_path = get_route_osrm(req.agent_lat, req.agent_lon, dest_lat, dest_lon)
            if route_path:
                route_source = "OSRM"

    return {
        "normalized": normalized_text,
        "standardized": ai_result.get("standardized_address"),
        "parsed": ai_result["parsed"],
        "geocoding": geo_result,
        "confidence": {
            "score": ml_score,
            "label": ml_label,
            "heuristic": ai_result["confidence_score"]
        },
        "distance": {
            "km": round(distance_km, 2) if distance_km is not None else None,
            "meters": int(distance_km * 1000) if distance_km is not None else None
        },
        "route": {
            "path": route_path,
            "source": route_source
        }
    }

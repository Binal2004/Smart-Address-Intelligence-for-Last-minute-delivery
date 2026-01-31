import streamlit as st
import pandas as pd
import sys
import os
import json
import requests
import pydeck as pdk
from dotenv import load_dotenv
from streamlit_js_eval import get_geolocation

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.normalizer import AddressNormalizer
from src.advanced_parser import AdvancedAddressParser
from src.corrector import AddressCorrector
from src.ml_corrector import MLCorrector
from src.reasoning_geocoder import ReasoningGeocoder
from src.mapbox_optimizer import MapboxQueryOptimizer
from src.scorer import AddressConfidenceScorer

st.set_page_config(page_title="Smart Address Intelligence", layout="wide")

st.title("📍 Smart Address Intelligence for Last-Mile Delivery")
st.markdown("""
Normalize, Parse, and Geocode unstructured Indian addresses using AI/ML techniques.
""")

# Sidebar
st.sidebar.header("Configuration")

# Secure API Key Handling
env_google_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
env_mapbox_key = os.getenv("MAPBOX_API_KEY", "")

# Auto-select provider based on available keys
default_idx = 0
if env_google_key:
    default_idx = 1
elif env_mapbox_key:
    default_idx = 2

api_choice = st.sidebar.radio("Select Geocoding Provider", 
                              ["OpenStreetMap (Free - Recommended)", "Google Maps", "Mapbox (Alternative)"],
                              index=default_idx)

google_api_key = env_google_key
mapbox_api_key = env_mapbox_key

if api_choice == "Google Maps":
    if not env_google_key:
        google_api_key = st.sidebar.text_input("Google Maps API Key", type="password", help="Enter key if not in .env")
    else:
        st.sidebar.success("Google Key loaded from .env")
elif api_choice == "Mapbox (Alternative)":
    if not env_mapbox_key:
        mapbox_api_key = st.sidebar.text_input("Mapbox API Key", type="password", help="Enter key if not in .env")
    else:
        st.sidebar.success("Mapbox Key loaded from .env")
else:
    st.sidebar.info("Using AI Reasoning + OpenStreetMap (No API Key required)")

st.sidebar.divider()
st.sidebar.header("About")
st.sidebar.info("This system solves last-mile delivery failures by standardizing ambiguous addresses.")
st.sidebar.markdown("### Capabilities")
st.sidebar.markdown("""
- **Deep Parsing**: Landmarks, Spatial Relations, Categories.
- **Normalization**: Clean Hinglish/Regional text.
- **Reasoning Geocoder**: Chain-of-Thought logic to pinpoint location.
- **Mapbox Optimization**: Generates optimized queries for Geocoding API.
- **Google Maps Adaptive**: Seamlessly switches to Google API if key is provided.
- **Confidence**: Detailed completeness scoring.
""")

# Initialize Logic
@st.cache_resource
def load_models():
    return AddressNormalizer(), AdvancedAddressParser(), AddressCorrector(), MLCorrector(), MapboxQueryOptimizer(), AddressConfidenceScorer()

normalizer, parser, corrector, ml_corrector, optimizer, scorer = load_models()

@st.cache_data
def get_route_osrm(start_lat, start_lon, end_lat, end_lon):
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
        headers = {'User-Agent': 'TraeAI-Hackathon-Project/1.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "routes" in data and len(data["routes"]) > 0:
                return data["routes"][0]["geometry"]["coordinates"]
    except Exception as e:
        pass # Fail silently
    return None

def decode_polyline(polyline_str):
    """Decodes a Google Maps encoded polyline string into a list of [lon, lat] pairs."""
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
        coordinates.append([lng / 1e5, lat / 1e5])
    return coordinates

@st.cache_data
def get_route_google(start_lat, start_lon, end_lat, end_lon, api_key):
    try:
        url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&key={api_key}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OK" and len(data["routes"]) > 0:
                polyline = data["routes"][0]["overview_polyline"]["points"]
                return decode_polyline(polyline)
    except Exception as e:
        pass
    return None

# Initialize Geocoder dynamically based on API Key
# Pass keys only if selected in UI
active_google_key = google_api_key if api_choice == "Google Maps" else None
active_mapbox_key = mapbox_api_key if api_choice == "Mapbox (Alternative)" else None

geocoder = ReasoningGeocoder(google_api_key=active_google_key, mapbox_api_key=active_mapbox_key)

# Input
st.subheader("Delivery Partner Location")
# Geolocation with Manual Fallback
loc = get_geolocation()
current_loc_str = "Unknown"
agent_lat = None
agent_lon = None

if isinstance(loc, dict):
    coords_obj = loc.get("coords")
    if isinstance(coords_obj, dict):
        agent_lat = coords_obj.get("latitude") or coords_obj.get("lat")
        agent_lon = coords_obj.get("longitude") or coords_obj.get("lon") or coords_obj.get("lng")
    else:
        agent_lat = loc.get("latitude") or loc.get("lat")
        agent_lon = loc.get("longitude") or loc.get("lon") or loc.get("lng")

# Manual Override if Geolocation fails
if agent_lat is None or agent_lon is None:
    with st.expander("📍 Manual Location Override (Use if Auto-Detection fails)", expanded=True):
        st.warning("Could not auto-detect location. Please check browser permissions or enter manually.")
        col_man1, col_man2 = st.columns(2)
        with col_man1:
            agent_lat = st.number_input("Agent Latitude", value=16.5062, format="%.6f") # Default: Vijayawada
        with col_man2:
            agent_lon = st.number_input("Agent Longitude", value=80.6480, format="%.6f")

if agent_lat is not None and agent_lon is not None:
    current_loc_str = f"{float(agent_lat):.5f}, {float(agent_lon):.5f}"
    st.info(f"📍 Agent Location: {current_loc_str}")
else:
    st.warning("⚠️ Location access denied or unavailable. Please enable location in browser.")

st.divider()

col_input, col_city, col_state = st.columns([3, 1, 1])
with col_input:
    raw_address = st.text_area("Enter Unstructured Address", 
                               "Near Apollo Hospital, Main Road, Vijayawada",
                               height=100)
with col_city:
    city_input = st.text_input("City", "Vijayawada")
with col_state:
    state_input = st.text_input("State", "Andhra Pradesh")

process_btn = st.button("Process Address", type="primary", use_container_width=True)

if process_btn:
    st.divider()
    
    # Step 1: Normalize
    normalized_text = normalizer.normalize(raw_address)
    
    # Step 2: Advanced Parse
    ai_result = parser.parse(normalized_text, city_input)
    
    # Step 3: Correct & Standardize
    standardized_address = corrector.correct(ai_result)

    # Step 3b: ML-Based Historical Correction (New)
    ml_correction = ml_corrector.predict_correction(raw_address, city_input, state_input)

    # Step 4: Reasoning Geocoder
    geo_result = geocoder.reason_and_geocode(ai_result, city_input, state_input, raw_address)
    
    # Step 5: Mapbox Optimization
    mapbox_result = optimizer.optimize(normalized_text, city_input, state_input)

    # Step 6: ML Confidence Scoring
    # Adapt parsed structure for Scorer
    parsed_for_scorer = {
        "house_number": ai_result["parsed"]["building"]["number"],
        "street": ai_result["parsed"]["locality"]["street"],
        "landmark": ai_result["parsed"]["landmarks"][0]["text"] if ai_result["parsed"]["landmarks"] else None,
        "city": ai_result["parsed"]["locality"]["city"],
        "pincode": ai_result["parsed"]["locality"]["pincode"]
    }
    
    geo_coords = geo_result.get("estimated_coordinates")
    geo_tuple = (None, None, None)
    if geo_coords:
        geo_tuple = (
            geo_coords.get("latitude"),
            geo_coords.get("longitude"),
            geo_result.get("reasoning", {}).get("primary_landmark")
        )

    ml_score = scorer.calculate_score(parsed_for_scorer, geo_tuple, raw_text=raw_address)
    ml_label = scorer.get_quality_label(ml_score)
    
    # Display Results
    tab1, tab2, tab3, tab4 = st.tabs(["Analysis", "Map & Reasoning", "Mapbox Queries", "Raw JSON"])
    
    with tab1:
        st.subheader("Pipeline Transformations")
        st.info(f"**Normalized:** {normalized_text}")
        st.success(f"**Standardized:** {standardized_address}")
        
        if ml_correction:
             with st.expander("✨ AI Historical Correction Prediction", expanded=True):
                 col_ml1, col_ml2 = st.columns([3, 1])
                 with col_ml1:
                     st.write(f"**Did you mean?** {ml_correction['suggested_address']}")
                     st.caption(f"Based on historical successful delivery to: {ml_correction['suggested_city']}, {ml_correction['suggested_state']}")
                 with col_ml2:
                     st.metric("Similarity Match", f"{int(ml_correction['similarity_score']*100)}%")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Structure Analysis")
            st.json(ai_result["parsed"])
        with col2:
            st.subheader("Scores & Quality")
            
            # Display ML Score
            st.metric("ML Delivery Confidence", f"{int(ml_score * 100)}%", delta=ml_label)
            st.progress(ml_score)
            
            st.divider()
            
            # Display Heuristic Score
            heuristic_score = ai_result["confidence_score"]
            st.metric("Address Completeness (Heuristic)", f"{heuristic_score}%")
            
            if ai_result["suggestions"]:
                for sug in ai_result["suggestions"]:
                    st.warning(f"- {sug}")

    with tab2:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader("Delivery Route & Location")
            coords = geo_result.get("estimated_coordinates")
            if coords:
                dest_lat, dest_lon = coords["latitude"], coords["longitude"]
                
                # Prepare PyDeck layers
                layers = []
                
                # Destination Layer (Red Glow)
                dest_data = pd.DataFrame([{"lat": dest_lat, "lon": dest_lon, "name": "📍 Destination"}])
                # Pulse Effect
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=dest_data,
                    get_position='[lon, lat]',
                    get_color='[255, 0, 0, 80]',
                    get_radius=400,
                ))
                # Core Dot
                layers.append(pdk.Layer(
                    "ScatterplotLayer",
                    data=dest_data,
                    get_position='[lon, lat]',
                    get_color='[255, 50, 50, 200]',
                    get_radius=150,
                    pickable=True
                ))

                # Agent Location Layer (Cyan Glow)
                if agent_lat and agent_lon:
                    agent_data = pd.DataFrame([{"lat": agent_lat, "lon": agent_lon, "name": "🚚 Delivery Agent"}])
                    # Pulse Effect
                    layers.append(pdk.Layer(
                        "ScatterplotLayer",
                        data=agent_data,
                        get_position='[lon, lat]',
                        get_color='[0, 255, 255, 80]',
                        get_radius=400,
                    ))
                    # Core Dot
                    layers.append(pdk.Layer(
                        "ScatterplotLayer",
                        data=agent_data,
                        get_position='[lon, lat]',
                        get_color='[0, 255, 255, 200]',
                        get_radius=150,
                        pickable=True
                    ))
                    
                    # Fetch and draw route
                    path_coords = None
                    if google_api_key:
                        path_coords = get_route_google(agent_lat, agent_lon, dest_lat, dest_lon, google_api_key)
                        if path_coords:
                            st.success("✅ Route calculated using Google Directions API")
                    
                    if not path_coords:
                         path_coords = get_route_osrm(agent_lat, agent_lon, dest_lat, dest_lon)
                         if path_coords:
                             st.success("✅ Route calculated using OSRM (Open Source Routing)")

                    if path_coords:
                         # PathLayer
                         route_data = [{"path": path_coords, "name": "🛣️ Optimal Route"}]
                         layers.append(pdk.Layer(
                             "PathLayer",
                             data=route_data,
                             get_path="path",
                             get_color="[255, 215, 0]", # Gold/Yellow
                             width_scale=5,
                             width_min_pixels=4,
                             pickable=True
                         ))
                    else:
                        st.warning("Could not fetch route (OSRM might be busy or locations too far)")

                # View State
                mid_lat = (dest_lat + agent_lat) / 2 if (agent_lat and agent_lon) else dest_lat
                mid_lon = (dest_lon + agent_lon) / 2 if (agent_lat and agent_lon) else dest_lon
                zoom_level = 13 if (agent_lat and agent_lon) else 15
                
                view_state = pdk.ViewState(
                    latitude=mid_lat, 
                    longitude=mid_lon, 
                    zoom=zoom_level, 
                    pitch=45,  # 3D Tilted View
                    bearing=0
                )
                
                # Dynamic Map Style (Dark Mode for "Black" aesthetic)
                # Mapbox Dark v10 or CartoDB Dark Matter
                map_style = "mapbox://styles/mapbox/dark-v10"
                if not mapbox_api_key:
                    map_style = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
                
                # Enhanced Tooltip
                tooltip = {
                    "html": "<b>{name}</b>",
                    "style": {
                        "backgroundColor": "#111",
                        "color": "#eee",
                        "border": "1px solid #444",
                        "borderRadius": "5px",
                        "padding": "10px"
                    }
                }

                st.pydeck_chart(pdk.Deck(
                    map_style=map_style,
                    initial_view_state=view_state,
                    layers=layers,
                    tooltip=tooltip
                ))

                st.success(f"📍 Destination Coordinates: {dest_lat}, {dest_lon}")
                resolved_address = geo_result.get("reasoning", {}).get("primary_landmark", "N/A")
                st.info(f"**Resolved Address:** {resolved_address}")
            else:
                st.error("Could not determine coordinates.")
        
        with col2:
            st.subheader("AI Reasoning Chain")
            reasoning = geo_result["reasoning"]
            
            st.markdown(f"**Primary Landmark:** `{reasoning['primary_landmark']}`")
            st.markdown(f"**Uniqueness:** `{reasoning['landmark_uniqueness']}`")
            
            st.markdown("**Spatial Logic:**")
            for logic in reasoning["spatial_logic"]:
                st.info(logic)
                
            st.markdown(f"**Offset Applied:** {reasoning['applied_offset']}")
            
            conf = geo_result["confidence"]
            st.metric("Geocode Confidence", f"{conf['score']}%", delta=conf['level'])

    with tab3:
        st.subheader("Optimized Mapbox Queries")
        st.write("These queries are optimized for Mapbox Geocoding API based on Indian address patterns.")
        
        for q in mapbox_result["optimized_queries"]:
            with st.expander(f"Rank {q['rank']}: {q['method'].upper()} - {q['expected_place_type']}"):
                if isinstance(q['query'], dict):
                    st.json(q['query'])
                else:
                    st.code(q['query'], language="text")
                st.caption(f"Reasoning: {q['reasoning']}")
                
        st.subheader("Execution Strategy")
        st.json(mapbox_result["execution_strategy"])

    with tab4:
        st.subheader("Full Reasoning Output")
        st.json(geo_result)

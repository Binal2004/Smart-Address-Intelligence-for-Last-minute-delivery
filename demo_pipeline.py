import sys
import os
import json

# Add src to path
sys.path.append(os.getcwd())

from src.normalizer import AddressNormalizer
from src.advanced_parser import AdvancedAddressParser
from src.corrector import AddressCorrector
from src.reasoning_geocoder import ReasoningGeocoder
from src.scorer import AddressConfidenceScorer

def process_address(raw_input):
    print(f"\n=======================================================")
    print(f"Processing Address: '{raw_input}'")
    print(f"=======================================================")
    
    # 1. Normalization
    print("\n[Step 1] Normalizing Text...")
    normalizer = AddressNormalizer()
    normalized_text = normalizer.normalize(raw_input)
    print(f"   -> Output: {normalized_text}")
    
    # 2. Parsing (Advanced)
    print("\n[Step 2] Parsing Components (Advanced)...")
    parser = AdvancedAddressParser()
    parsed_result = parser.parse(normalized_text)
    print(f"   -> Structure: {json.dumps(parsed_result['parsed'], indent=2)}")
    
    # 3. Correction / Standardization
    print("\n[Step 3] Correcting & Standardizing Format...")
    corrector = AddressCorrector()
    standardized_address = corrector.correct(parsed_result)
    print(f"   -> Output: {standardized_address}")
    
    # 4. Geocoding (Reasoning + Context)
    print("\n[Step 4] Geocoding & Context Analysis...")
    geocoder = ReasoningGeocoder()
    lat, lon, method = geocoder.geocode_with_reasoning(parsed_result["parsed"])
    print(f"   -> Coordinates: ({lat}, {lon})")
    print(f"   -> Method: {method}")
    
    # 5. Scoring
    print("\n[Step 5] Calculating Confidence Score...")
    scorer = AddressConfidenceScorer()
    
    # Scorer expects a flat dict for parsing, let's map it
    flat_parsed = {
        "house_number": parsed_result["parsed"]["building"]["number"],
        "street": parsed_result["parsed"]["locality"]["street"],
        "landmark": parsed_result["parsed"]["landmarks"][0]["text"] if parsed_result["parsed"]["landmarks"] else None,
        "city": parsed_result["parsed"]["locality"]["city"],
        "pincode": parsed_result["parsed"]["locality"]["pincode"]
    }
    
    score = scorer.calculate_score(flat_parsed, (lat, lon, method), raw_text=raw_input)
    label = scorer.get_quality_label(score)
    print(f"   -> Score: {score} ({label})")
    
    return {
        "original": raw_input,
        "normalized": normalized_text,
        "standardized": standardized_address,
        "coordinates": {"lat": lat, "lon": lon},
        "score": score,
        "quality": label
    }

if __name__ == "__main__":
    # User's Example
    example_input = "Near the big tree, after the chai shop, first lane from main road"
    
    # Hindi/Regional Example
    example_hindi = "Shiv Mandir ke peeche, Gali No 4, Gandhi Nagar"
    
    process_address(example_input)
    process_address(example_hindi)

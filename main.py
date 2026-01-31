import sys
import os

# Ensure src is in path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.normalizer import AddressNormalizer
from src.parser import AddressParser
from src.geocoder import SmartGeocoder
from src.scorer import AddressConfidenceScorer

def main():
    print("=== Smart Address Intelligence System ===\n")

    # Initialize Modules
    normalizer = AddressNormalizer()
    parser = AddressParser()
    geocoder = SmartGeocoder()
    scorer = AddressConfidenceScorer()

    # Input Data
    raw_address = "Near the big tree, after the chai shop, first lane from main road"
    print(f"Input Address: {raw_address}\n")

    # Step 1: Normalize
    normalized_address = normalizer.standardize(raw_address)
    print(f"1. Normalized: {normalized_address}")

    # Step 2: Parse
    parsed_components = parser.parse(normalized_address)
    print(f"2. Parsed Components:")
    for k, v in parsed_components.items():
        if v:
            print(f"   - {k}: {v}")

    # Step 3: Geocode
    lat, lon, method = geocoder.geocode(parsed_components)
    print(f"\n3. Geocoding Result:")
    print(f"   - Latitude: {lat}")
    print(f"   - Longitude: {lon}")
    print(f"   - Method: {method}")

    # Step 4: Confidence Score
    score = scorer.calculate_score(parsed_components, (lat, lon, method), raw_text=raw_address)
    label = scorer.get_quality_label(score)
    print(f"\n4. Confidence Score: {score}/1.0 ({label})")

    print("\n--- Additional Test Cases ---")
    test_addresses = [
        "near chai shop, Shivaji Nagar", # High confidence in training data
        "Unknown place, deep forest",    # Should be low
        "Flat 101, Galaxy Apts, MG Road, Bangalore" # Should be decent
    ]
    
    for addr in test_addresses:
        print(f"\nInput: {addr}")
        norm = normalizer.standardize(addr)
        parsed = parser.parse(norm)
        geo = geocoder.geocode(parsed)
        sc = scorer.calculate_score(parsed, geo, raw_text=addr)
        lbl = scorer.get_quality_label(sc)
        print(f"Score: {sc} ({lbl})")

if __name__ == "__main__":
    main()

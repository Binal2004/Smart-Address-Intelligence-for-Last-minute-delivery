from src.normalizer import AddressNormalizer

def test_normalization():
    norm = AddressNormalizer()
    
    test_cases = [
        ("Shiv Mandir ke peeche, Gandhi Nagar", "Shiv Temple Behind, Gandhi Colony"),
        ("Medical Store near Apollo Hospital", "Medical Store Near Apollo Hospital"),
        ("Bada Bazaar mein, School ke samne", "Big Market In, School Opposite"),
        ("Petrol Pump ke bagal mein", "Gas Station Next To"),
        ("Gali No 4, Block A", "Lane Number 4, Block A")
    ]
    
    print("\n--- Normalization Tests ---")
    for input_text, expected_partial in test_cases:
        result = norm.normalize(input_text)
        print(f"Input:    {input_text}")
        print(f"Output:   {result}")
        
        # We check if key translated terms are present
        if expected_partial.lower() in result.lower() or all(word.lower() in result.lower() for word in expected_partial.split()):
            print("PASS")
        else:
            print(f"FAIL (Expected terms from: '{expected_partial}')")
        print("-" * 30)

if __name__ == "__main__":
    test_normalization()

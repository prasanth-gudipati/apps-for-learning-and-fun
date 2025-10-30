#!/usr/bin/python3

"""
Test script for the global ID parsing functionality
"""

import sys
import os

# Add the parent directory to the path to import the parsing function
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def parse_global_id_input(global_id_input):
    """
    Parse global ID input which can be:
    - Single number: "50"
    - Range: "50-55" or "50:55" 
    - List: "50,52,54,56"
    - Mixed: "50,52-55,60"
    """
    global_ids = []
    
    # Split by comma for multiple entries
    parts = global_id_input.split(',')
    
    for part in parts:
        part = part.strip()
        
        # Check for range (with - or :)
        if '-' in part:
            start, end = part.split('-', 1)
            global_ids.extend(range(int(start), int(end) + 1))
        elif ':' in part:
            start, end = part.split(':', 1)
            global_ids.extend(range(int(start), int(end) + 1))
        else:
            # Single number
            global_ids.append(int(part))
    
    return sorted(list(set(global_ids)))  # Remove duplicates and sort

def test_parsing():
    """Test various input formats"""
    test_cases = [
        ("50", [50]),
        ("50-55", [50, 51, 52, 53, 54, 55]),
        ("50:55", [50, 51, 52, 53, 54, 55]),
        ("50,52,54", [50, 52, 54]),
        ("50-52,55,60-62", [50, 51, 52, 55, 60, 61, 62]),
        ("50, 52-54, 58", [50, 52, 53, 54, 58]),
        ("100:102,105,108-110", [100, 101, 102, 105, 108, 109, 110]),
        ("50,50,51", [50, 51])  # Test duplicate removal
    ]
    
    print("=== Testing Global ID Parsing ===")
    all_passed = True
    
    for input_str, expected in test_cases:
        try:
            result = parse_global_id_input(input_str)
            if result == expected:
                print(f"✓ '{input_str}' -> {result}")
            else:
                print(f"✗ '{input_str}' -> {result} (expected {expected})")
                all_passed = False
        except Exception as e:
            print(f"✗ '{input_str}' -> ERROR: {e}")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        return False
    
    return True

if __name__ == '__main__':
    success = test_parsing()
    sys.exit(0 if success else 1)
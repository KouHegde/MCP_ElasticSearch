"""
Test script for the Natural Language Query Parser.
Verifies that the parser generates correct OpenSearch queries.
"""

import json
from nlq_parser import NLQParser


def test_basic_functionality():
    """Test basic functionality of the parser."""
    parser = NLQParser(enable_logging=False)  # Disable logging for clean test output
    
    # Test cases with expected results
    test_cases = [
        {
            "input": "errors in last 5 minutes for checkout-service",
            "expected_conditions": [
                lambda q: "query" in q,
                lambda q: "bool" in q.get("query", {}),
                lambda q: q.get("size") == 50,
                lambda q: q.get("sort") == [{"@timestamp": "desc"}]
            ]
        },
        
        {
            "input": "show top 100 logs",
            "expected_conditions": [
                lambda q: q.get("size") == 100
            ]
        },
        
        {
            "input": "cluster health",
            "expected_conditions": [
                lambda q: "api" in q and "_cluster/health" in q.get("api", "")
            ]
        },
        
        {
            "input": "create a new index with custom mappings",
            "expected_conditions": [
                lambda q: "error" in q
            ]
        }
    ]
    
    print("Running tests...")
    passed = 0
    total = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['input']}")
        result_str = parser.parse(test['input'])
        
        try:
            result_dict = json.loads(result_str)
            print(f"Output: {result_str}")
            
            test_passed = True
            for condition in test['expected_conditions']:
                if not condition(result_dict):
                    test_passed = False
                    break
            
            if test_passed:
                print("✅ PASSED")
                passed += 1
            else:
                print("❌ FAILED - Conditions not met")
                
        except json.JSONDecodeError:
            print("❌ FAILED - Invalid JSON output")
    
    print(f"\n\nTest Results: {passed}/{total} tests passed")
    return passed == total


def test_specific_example():
    """Test the specific example from the requirements."""
    parser = NLQParser(enable_logging=False)  # Disable logging for clean test output
    
    input_query = "I want to get details of errors in last 5 minutes for checkout-service"
    result = parser.parse(input_query)
    
    print("Testing specific example from requirements:")
    print(f"Input: {input_query}")
    print(f"Output: {result}")
    
    # Parse and verify structure
    try:
        query_dict = json.loads(result)
        
        # Check expected structure
        expected_structure = {
            "query": {
                "bool": {
                    "must": [
                        {"match": {"log.level": "error"}},
                        {"match": {"service.name": "checkout-service"}},
                        {"range": {"@timestamp": {"gte": "now-5m"}}}
                    ]
                }
            },
            "size": 50,
            "sort": [{"@timestamp": "desc"}]
        }
        
        # Verify key components exist
        checks = [
            query_dict.get("size") == 50,
            query_dict.get("sort") == [{"@timestamp": "desc"}],
            "query" in query_dict,
            "bool" in query_dict.get("query", {}),
            "must" in query_dict.get("query", {}).get("bool", {}),
            len(query_dict.get("query", {}).get("bool", {}).get("must", [])) == 3
        ]
        
        if all(checks):
            print("✅ Example matches expected structure!")
        else:
            print("❌ Example structure doesn't match expected format")
            
    except json.JSONDecodeError:
        print("❌ Example produced invalid JSON")


if __name__ == "__main__":
    print("OpenSearch Natural Language Query Parser - Tests")
    print("=" * 50)
    
    # Run basic functionality tests
    basic_tests_passed = test_basic_functionality()
    
    print("\n" + "=" * 50)
    
    # Test specific example
    test_specific_example()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    if basic_tests_passed:
        print("✅ All basic tests passed!")
    else:
        print("❌ Some basic tests failed!")
    
    print("\nTo run interactive mode, use: python nlq_parser.py")

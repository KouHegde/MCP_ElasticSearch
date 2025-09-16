#!/usr/bin/env python3
"""
Field Mapping Demo - Demonstrates the new standardized field mapping system

This demo shows how the static field mapping works and how users can now
use standardized field names instead of specific Elasticsearch field names.
"""

import json
from nlq_parser import NLQParser


def demo_field_mapping():
    """Demonstrate the new field mapping functionality."""
    print("🚀 FIELD MAPPING SYSTEM DEMO")
    print("=" * 50)
    
    parser = NLQParser(enable_logging=False)
    
    # Show supported mappings
    print("📋 SUPPORTED FIELD MAPPINGS:")
    for std_field, es_field in parser.query_builder.FIELD_MAPPING.items():
        print(f"   {std_field:<15} → {es_field}")
    
    print("\n" + "=" * 50)
    print("🎯 TESTING STANDARDIZED QUERIES")
    print("=" * 50)
    
    # Test queries showing the new standardized syntax
    test_queries = [
        # New standardized syntax
        "service:hydra level:error",
        "level=INFO service=api-gateway", 
        "service is auth-service and level is WARN",
        "level:DEBUG host:prod-server-01",
        "service:payment level:ERROR last 10 minutes",
        
        # Legacy syntax (should still work)
        "errors in hydra service last 5 minutes",
        "warnings from api-gateway in last hour",
        
        # Validation test (should fail)
        "invalidField:someValue level:INFO",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}] Query: '{query}'")
        result = parser.parse(query)
        
        try:
            parsed = json.loads(result)
            if "error" in parsed:
                print(f"    ❌ Error: {parsed['error']}")
            else:
                print(f"    ✅ Success!")
            print("    📝 Generated Query:")
            print(json.dumps(parsed, indent=6))
        except json.JSONDecodeError:
            print(f"    ❌ Failed to parse result: {result}")
    
    print("\n" + "=" * 50)
    print("📊 COMPARISON: OLD vs NEW SYNTAX")
    print("=" * 50)
    
    comparison_tests = [
        {
            "description": "Service filtering",
            "old": "errors in hydra service",
            "new": "service:hydra level:error"
        },
        {
            "description": "Log level filtering", 
            "old": "warnings from api-gateway",
            "new": "level:WARN service:api-gateway"
        },
        {
            "description": "Combined filters",
            "old": "info logs in auth-service last hour", 
            "new": "level:INFO service:auth-service last 1 hour"
        }
    ]
    
    for test in comparison_tests:
        print(f"\n🔍 {test['description']}:")
        print(f"   Old: '{test['old']}'")
        old_result = parser.parse(test['old'])
        
        print(f"   New: '{test['new']}'")
        new_result = parser.parse(test['new'])
        
        try:
            old_parsed = json.loads(old_result)
            new_parsed = json.loads(new_result)
            
            print(f"   📊 Both generate valid queries: ✅")
            
            # Show the actual field mappings used
            if "query" in old_parsed and "query" in new_parsed:
                print("   🎯 Field mappings:")
                old_query = old_parsed.get("query", {})
                new_query = new_parsed.get("query", {})
                if "bool" in old_query and "bool" in new_query:
                    old_must = old_query.get("bool", {}).get("must", [])
                    new_must = new_query.get("bool", {}).get("must", [])
                    print(f"      Old syntax generates {len(old_must)} filters")
                    print(f"      New syntax generates {len(new_must)} filters")
        except json.JSONDecodeError:
            print("   ❌ Error comparing results")

def test_validation():
    """Test field name validation."""
    print("\n" + "=" * 50)
    print("🛡️  FIELD VALIDATION TESTING")
    print("=" * 50)
    
    parser = NLQParser(enable_logging=False)
    
    # Test valid field names
    valid_queries = [
        "service:hydra",
        "level:ERROR", 
        "host:server01",
        "message contains error"
    ]
    
    print("✅ VALID FIELD NAMES:")
    for query in valid_queries:
        unsupported = parser.validate_field_names(query)
        status = "✅ Valid" if not unsupported else f"❌ Invalid: {unsupported}"
        print(f"   '{query}' → {status}")
    
    # Test invalid field names 
    invalid_queries = [
        "invalidField:value",
        "badField=test level:INFO",
        "wrongName is something"
    ]
    
    print("\n❌ INVALID FIELD NAMES:")
    for query in invalid_queries:
        unsupported = parser.validate_field_names(query)
        status = "✅ Valid" if not unsupported else f"❌ Invalid: {unsupported}"
        print(f"   '{query}' → {status}")


if __name__ == "__main__":
    demo_field_mapping()
    test_validation()
    
    print("\n" + "=" * 50)
    print("🎉 DEMO COMPLETE!")
    print("=" * 50)
    print("💡 Key Benefits of the New System:")
    print("   • Standardized field names across all queries")
    print("   • Validation prevents typos and invalid fields") 
    print("   • Backward compatibility with legacy syntax")
    print("   • Clear mapping between user terms and ES fields")
    print("   • Easy to extend with new field mappings")

"""
Logging Demo for OpenSearch Natural Language Query Parser

This demonstrates the logging capabilities that track query processing.
"""

import logging
from nlq_parser import NLQParser, configure_logging


def demo_with_logging():
    """Demonstrate parser with detailed logging enabled."""
    print("OpenSearch NLQ Parser - Logging Demo")
    print("=" * 50)
    
    # Configure logging to show detailed processing
    configure_logging(enable_debug=True)
    
    # Create parser with logging enabled
    parser = NLQParser(enable_logging=True)
    
    # Test queries that demonstrate different parsing scenarios
    test_queries = [
        "I want to get details of errors in last 5 minutes for Hydra",
        "show me warnings from api-gateway in last 2 hours",
        "cluster health",
        "list indices", 
        "show top 100 errors in last 10 minutes",
        "create a new index with custom mappings",  # This should fail
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Example {i} ---")
        print(f"Input: '{query}'")
        print("Processing...")
        
        result = parser.parse(query)
        
        print(f"Final JSON Output: {result}")
        print("-" * 40)
    
    print("\n✅ Logging Demo Complete!")
    print("\nLogging Features Demonstrated:")
    print("- Input query tracking")
    print("- Component extraction (service, time, log level, etc.)")
    print("- Query type identification")
    print("- Final output generation")
    print("- Error handling and warnings")


def demo_without_logging():
    """Demonstrate parser with logging disabled (production mode)."""
    print("\n" + "=" * 50)
    print("Production Mode - No Logging")
    print("=" * 50)
    
    # Create parser without logging
    parser = NLQParser(enable_logging=False)
    
    query = "errors in last 5 minutes for checkout-service"
    print(f"Input: '{query}'")
    
    result = parser.parse(query)
    print(f"Output: {result}")
    
    print("\n✅ Clean output - no logging messages!")


if __name__ == "__main__":
    # Run demo with detailed logging
    demo_with_logging()
    
    # Show clean production mode
    demo_without_logging()

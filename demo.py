"""
Demo script showing the exact example from the requirements.
"""

from nlq_parser import NLQParser


def main():
    """Run the exact example from the requirements."""
    parser = NLQParser(enable_logging=False)  # Disable logging for clean demo output
    
    print("OpenSearch Natural Language Query Parser - Demo")
    print("=" * 50)
    print("\nExample from requirements:")
    print()
    
    # Exact example from requirements
    user_input = "I want to get details of errors in last 5 minutes for checkout-service"
    
    print(f"User input:")
    print(f'"{user_input}"')
    print()
    print("System output:")
    
    result = parser.parse(user_input)
    print(result)
    
    print("\n" + "=" * 50)
    print("✅ Raw JSON output ready to use in OpenSearch Dev Tools!")
    
    print("\nTo use this query:")
    print("1. Copy the JSON output above")
    print("2. Paste it into OpenSearch Dev Tools")
    print("3. Add the endpoint: GET /your-index/_search")
    print("4. Execute the query")


if __name__ == "__main__":
    main()


"""
Usage Examples for OpenSearch Natural Language Query System

This demonstrates both approaches:
1. Query Generator Only (for Dev Tools usage)
2. Full OpenSearch Client (connects and executes)
"""

import json
import os
from nlq_parser import NLQParser

# Try to import the full client
try:
    from opensearch_client import OpenSearchNLQClient, OpenSearchConfig
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False
    print("opensearch-py not installed. Only showing query generator examples.")


def example_1_query_generator():
    """
    Example 1: Query Generator Only
    
    Use this approach when you want to:
    - Generate queries for OpenSearch Dev Tools
    - Integrate with existing OpenSearch infrastructure
    - Have full control over connection and execution
    """
    print("=" * 60)
    print("APPROACH 1: Query Generator Only (Dev Tools Usage)")
    print("=" * 60)
    
    # Create parser (no OpenSearch connection needed)
    parser = NLQParser(enable_logging=True)
    
    queries = [
        "I want to get details of errors in last 5 minutes for checkout-service",
        "show me warnings from api-gateway in last 2 hours",
        "get info logs from today for user-service",
        "show top 100 errors in last 10 minutes",
        "cluster health",
        "list indices"
    ]
    
    print("\nGenerating OpenSearch queries from natural language...\n")
    
    for i, query in enumerate(queries, 1):
        print(f"Example {i}:")
        print(f"  Input:  '{query}'")
        
        # Generate query JSON
        result = parser.parse(query)
        print(f"  Output: {result}")
        
        # Show how to use in Dev Tools
        print("  Usage in Dev Tools:")
        if "api" in result:
            # API call
            api_data = json.loads(result)
            if "_cluster/health" in api_data.get("api", ""):
                print("    GET _cluster/health")
            elif "_cat/indices" in api_data.get("api", ""):
                print("    GET _cat/indices?v")
        else:
            # Search query
            print("    GET /your-index-name/_search")
            print(f"    {result}")
        
        print("-" * 50)


def example_2_full_client():
    """
    Example 2: Full OpenSearch Client
    
    Use this approach when you want to:
    - Connect directly to OpenSearch clusters
    - Execute queries and get results
    - Build applications with natural language search
    """
    if not CLIENT_AVAILABLE:
        print("\n⚠️  Full client examples skipped - opensearch-py not installed")
        print("To install: pip install opensearch-py")
        return
    
    print("\n" + "=" * 60)
    print("APPROACH 2: Full OpenSearch Client (Live Execution)")
    print("=" * 60)
    
    # Configuration options
    configs = {
        "local": OpenSearchConfig(
            hosts=[{'host': 'localhost', 'port': 9200}],
            http_auth=('admin', 'admin'),
            use_ssl=False,
            verify_certs=False
        ),
        
        "cloud": OpenSearchConfig(
            hosts=[{'host': 'your-cluster.es.amazonaws.com', 'port': 443}],
            http_auth=('username', 'password'),  # or use api_key
            use_ssl=True,
            verify_certs=True
        ),
        
        "env_based": "create_from_env"  # Uses environment variables
    }
    
    print("Configuration Examples:")
    print("1. Local Development:")
    print("   - Host: localhost:9200")
    print("   - Auth: admin/admin")
    print("   - SSL: disabled")
    print()
    print("2. Cloud/Production:")
    print("   - Host: your-cluster.domain.com:443")
    print("   - Auth: username/password or API key")
    print("   - SSL: enabled with certificate verification")
    print()
    print("3. Environment Variables:")
    print("   - OPENSEARCH_HOST, OPENSEARCH_PORT")
    print("   - OPENSEARCH_USERNAME, OPENSEARCH_PASSWORD")
    print("   - OPENSEARCH_USE_SSL")
    
    # Try to connect to a local cluster
    print("\n" + "-" * 40)
    print("Attempting connection to local cluster...")
    print("-" * 40)
    
    try:
        client = OpenSearchNLQClient(configs["local"], enable_logging=True)
        
        # Test connection
        if not client.test_connection():
            print("❌ Cannot connect to local OpenSearch cluster")
            print("Make sure OpenSearch is running on localhost:9200")
            return
        
        print("✅ Connected successfully!")
        
        # Example queries with live execution
        queries = [
            ("errors in last 5 minutes for checkout-service", "logs-*"),
            ("warnings from api-gateway last hour", "logs-*"),
            ("cluster health", None),
            ("list indices", None)
        ]
        
        for query, index in queries:
            print(f"\n--- Executing: '{query}' ---")
            
            if index:
                # Search query
                result = client.query(query, index=index, execute=True)
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    hits = result.get('hits', {})
                    total = hits.get('total', {})
                    if isinstance(total, dict):
                        count = total.get('value', 0)
                    else:
                        count = total
                    print(f"✅ Found {count} results in {result.get('took', 0)}ms")
                    
                    # Show first few results
                    for i, hit in enumerate(hits.get('hits', [])[:3]):
                        source = hit.get('_source', {})
                        timestamp = source.get('@timestamp', 'N/A')
                        service = source.get('service', {}).get('name', 'N/A')
                        level = source.get('log', {}).get('level', 'N/A')
                        message = source.get('message', 'N/A')[:100]
                        print(f"  [{i+1}] {timestamp} | {service} | {level} | {message}...")
            else:
                # API query
                result = client.query(query, execute=True)
                if "error" in result:
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"✅ Result: {json.dumps(result, indent=2)[:300]}...")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("This is normal if you don't have OpenSearch running locally")


def example_3_comparison():
    """
    Example 3: Side-by-side Comparison
    
    Shows the same query processed by both approaches
    """
    print("\n" + "=" * 60)
    print("APPROACH COMPARISON: Same Query, Different Execution")
    print("=" * 60)
    
    query = "show me errors from checkout-service in last 5 minutes"
    
    print(f"Natural Language Input: '{query}'")
    print()
    
    # Approach 1: Query Generator
    print("📝 APPROACH 1 - Query Generator:")
    parser = NLQParser(enable_logging=False)
    query_json = parser.parse(query)
    print(f"Generated JSON: {query_json}")
    print("Usage: Copy this JSON to OpenSearch Dev Tools")
    print()
    
    # Approach 2: Full Client (if available)
    if CLIENT_AVAILABLE:
        print("🚀 APPROACH 2 - Full Client:")
        print("- Connects to OpenSearch cluster")
        print("- Executes query automatically") 
        print("- Returns actual results")
        print("- Handles authentication and SSL")
        print()
        print("Example code:")
        print("```python")
        print("client = OpenSearchNLQClient(config)")
        print(f"results = client.query('{query}', index='logs-*')")
        print("print(f'Found {results[\"hits\"][\"total\"]} results')")
        print("```")
    
    print("\n🎯 WHEN TO USE EACH:")
    print()
    print("Query Generator (Approach 1):")
    print("✅ Learning/testing OpenSearch queries")
    print("✅ Using OpenSearch Dev Tools") 
    print("✅ Existing OpenSearch infrastructure")
    print("✅ Custom authentication/connection logic")
    print("✅ No additional dependencies")
    print()
    
    if CLIENT_AVAILABLE:
        print("Full Client (Approach 2):")
        print("✅ Building applications with natural language search")
        print("✅ Automated query execution")
        print("✅ Production logging/monitoring systems")
        print("✅ Multi-cluster management")
        print("✅ Built-in error handling and retries")


def main():
    """Run all examples."""
    print("OpenSearch Natural Language Query System - Usage Examples")
    print("This system offers two approaches for different use cases:")
    
    # Run examples
    example_1_query_generator()
    example_2_full_client()
    example_3_comparison()
    
    print("\n" + "=" * 60)
    print("🎉 Examples Complete!")
    print("=" * 60)
    print()
    print("Next Steps:")
    print("1. For Dev Tools usage: Use nlq_parser.py directly")
    print("2. For live queries: Install opensearch-py and use opensearch_client.py")
    print("3. Check the README.md for detailed documentation")


if __name__ == "__main__":
    main()

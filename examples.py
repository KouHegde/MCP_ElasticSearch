"""
Example queries and their expected OpenSearch JSON outputs.
This file demonstrates the capabilities of the NLQ Parser.
"""

from nlq_parser import NLQParser


def run_examples():
    """Run example queries and show outputs."""
    parser = NLQParser(enable_logging=False)  # Disable logging for clean example output
    
    examples = [
        # Basic error queries
        {
            "input": "I want to get details of errors in last 5 minutes for {serviceName}",
            "description": "Basic error query with time range and service filter"
        },
        
        # Different time ranges
        {
            "input": "show me warnings from {serviceName} in last 2 hours",
            "description": "Warning level logs with different time range"
        },
        
        {
            "input": "get info logs from today for the {serviceName}",
            "description": "Info logs for today"
        },
        
        {
            "input": "find debug logs from {serviceName} yesterday",
            "description": "Debug logs from yesterday"
        },
        
        # Size specifications
        {
            "input": "show top 100 errors in last 10 minutes for {serviceName}",
            "description": "Custom result size"
        },
        
        # Service queries
        {
            "input": "logs from {serviceName} in last hour",
            "description": "All logs from specific service"
        },
        
        # Text search
        {
            "input": "search for database connection errors in last 30 minutes",
            "description": "Text search with time filter"
        },
        
        # API queries
        {
            "input": "show cluster health",
            "description": "Cluster health API"
        },
        
        {
            "input": "list indices",
            "description": "Cat indices API"
        },
        
        # Complex queries
        {
            "input": "find timeout errors in {serviceName} last 15 minutes",
            "description": "Multiple filters combined"
        },
        
        # Unsupported query
        {
            "input": "create a new index with custom mappings",
            "description": "Unsupported query example"
        }
    ]
    
    print("OpenSearch Natural Language Query Parser - Examples")
    print("=" * 60)
    
    for i, example in enumerate(examples, 1):
        print(f"\nExample {i}: {example['description']}")
        print(f"Input: \"{example['input']}\"")
        print("Output:")
        result = parser.parse(example['input'])
        print(result)
        print("-" * 40)


if __name__ == "__main__":
    run_examples()

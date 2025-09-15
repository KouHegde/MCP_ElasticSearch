ALL # OpenSearch Natural Language Query Parser

A Python system that converts natural language queries into valid OpenSearch REST API queries. Simply describe what you want to search for in plain English, and get back executable OpenSearch JSON queries.

## Features

- 🔍 **Natural Language Processing**: Convert plain English to OpenSearch queries
- ⏰ **Time Range Support**: Handle relative times like "last 5 minutes", "today", "yesterday" 
- 🏷️ **Service Filtering**: Automatic mapping to `service.name` field
- 📊 **Log Level Filtering**: Support for error, warning, info, debug levels
- 🔧 **API Support**: Cluster health, cat APIs, and search APIs
- 📏 **Configurable Results**: Custom result sizes and automatic timestamp sorting
- 📝 **Query Logging**: Optional detailed logging of query processing steps
- ⚡ **No Dependencies**: Uses only Python standard library

## Two Usage Approaches

This system offers **two ways** to use natural language queries with OpenSearch:

### 🔧 Approach 1: Query Generator (Dev Tools)

Perfect for learning, testing, or when you have existing OpenSearch infrastructure.

```python
from nlq_parser import NLQParser

parser = NLQParser()
query = "errors in last 5 minutes for checkout-service"
result = parser.parse(query)
print(result)
```

Output:
```json
{"query":{"bool":{"must":[{"match":{"log.level":"error"}},{"match":{"service.name":"checkout-service"}},{"range":{"@timestamp":{"gte":"now-5m"}}}]}},"size":50,"sort":[{"@timestamp":"desc"}]}
```

**Use this JSON directly in OpenSearch Dev Tools:**
```
GET /your-index/_search
{"query":{"bool":{"must":[{"match":{"log.level":"error"}},{"match":{"service.name":"checkout-service"}},{"range":{"@timestamp":{"gte":"now-5m"}}}]}},"size":50,"sort":[{"@timestamp":"desc"}]}
```

### 🚀 Approach 2: Full OpenSearch Client

Perfect for building applications that need to connect and execute queries automatically.

```python
from opensearch_client import OpenSearchNLQClient, OpenSearchConfig

# Configure connection
config = OpenSearchConfig(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=('admin', 'admin'),
    use_ssl=False
)

# Create client and execute queries
client = OpenSearchNLQClient(config)
results = client.query("errors in last 5 minutes for checkout-service", 
                      index="logs-*", execute=True)

print(f"Found {results['hits']['total']} results")
for hit in results['hits']['hits']:
    print(f"- {hit['_source']['@timestamp']}: {hit['_source']['message']}")
```

## Installation Options

### Option 1: Query Generator Only (No Dependencies)
```bash
# Uses only Python standard library
git clone <repo-url>
cd MCP_ElasticSearch
python3 nlq_parser.py
```

### Option 2: Full Client with OpenSearch Connection
```bash
git clone <repo-url>
cd MCP_ElasticSearch

# Install OpenSearch client dependencies
pip install -r requirements.txt

# Test the full client
python3 usage_examples.py
```

## Quick Start Scripts

### Interactive CLI (Query Generator)
```bash
python3 nlq_parser.py
```

### Usage Examples (Both Approaches)
```bash
python3 usage_examples.py
```

### Query Generator Examples
```bash
python3 examples.py
```

### Run Tests
```bash
python3 test_parser.py
```

### Logging Demo
```bash
python3 logging_demo.py
```

### Configuration Examples
```bash
python3 config_example.py
```

## Supported Query Types

### Log Search Queries

- **Basic Error Search**: "show me errors from last hour"
- **Service-Specific**: "errors in payment-service last 30 minutes"  
- **Log Levels**: "warning logs from user-service today"
- **Text Search**: "database timeout errors last 10 minutes"

### Time Ranges

- **Relative**: "last 5 minutes", "last 2 hours", "last 3 days"
- **Absolute**: "today", "yesterday"

### Result Control

- **Custom Size**: "show top 100 errors", "limit 20 results"
- **Default**: 50 results, sorted by `@timestamp` descending

### API Queries

- **Cluster Health**: "show cluster health", "cluster status"
- **Cat APIs**: "list indices", "show nodes", "list shards"

## OpenSearch Client Features (Approach 2)

### Connection Management
- **Multiple Hosts**: Support for multi-node clusters
- **Authentication**: Username/password, API keys, AWS IAM
- **SSL/TLS**: Full certificate verification support
- **Connection Pooling**: Automatic retry and timeout handling

### Query Execution
- **Live Results**: Get actual search results, not just JSON
- **Index Targeting**: Specify which indices to search
- **Error Handling**: Graceful handling of connection and query errors
- **Result Formatting**: Clean, structured response format

### Configuration Options
```python
config = OpenSearchConfig(
    hosts=[
        {'host': 'node1.cluster.com', 'port': 9200},
        {'host': 'node2.cluster.com', 'port': 9200}
    ],
    http_auth=('username', 'password'),
    # OR api_key=('key_id', 'key_secret'),
    use_ssl=True,
    verify_certs=True,
    timeout=60,
    max_retries=3
)
```

### Environment Variables Support
```bash
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200
export OPENSEARCH_USERNAME=admin
export OPENSEARCH_PASSWORD=admin
export OPENSEARCH_USE_SSL=false
```

Then use:
```python
from opensearch_client import create_client_from_env
client = create_client_from_env()
```

## Query Rules

1. **Time Ranges**: Relative times use format `now-5m`, `now-2h`, `now-1d`
2. **Service Names**: Automatically mapped to `service.name` field
3. **Default Size**: 50 results unless specified otherwise
4. **Default Sort**: `@timestamp` descending
5. **Search API**: Uses `_search` by default unless cat/cluster API requested
6. **Error Handling**: Returns error JSON for unsupported queries

## Example Queries and Outputs

### Error Logs with Time and Service Filter

**Input**: "I want to get details of errors in last 5 minutes for checkout-service"

**Output**:
```json
{
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
```

### Custom Result Size

**Input**: "show top 100 warnings from payment-service last hour"

**Output**:
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"log.level": "warn"}},
        {"match": {"service.name": "payment-service"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "size": 100,
  "sort": [{"@timestamp": "desc"}]
}
```

### Cluster API

**Input**: "show cluster health"

**Output**:
```json
{"api": "_cluster/health"}
```

### Text Search

**Input**: "search for database connection errors last 30 minutes"

**Output**:
```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"log.level": "error"}},
        {"match": {"_all": "database"}},
        {"match": {"_all": "connection"}},
        {"range": {"@timestamp": {"gte": "now-30m"}}}
      ]
    }
  },
  "size": 50,
  "sort": [{"@timestamp": "desc"}]
}
```

## Architecture

The system consists of two main components:

### OpenSearchQueryBuilder
- Handles query construction and formatting
- Manages default behaviors (size, sorting)
- Builds specific query components (time ranges, filters)

### NLQParser  
- Parses natural language input
- Extracts query components using pattern matching
- Coordinates query building and error handling

## Supported Patterns

### Time Expressions
- `last X minutes/hours/days/weeks/months/years`
- `today`, `yesterday`
- Numbers: 5, 10, 30, etc.

### Service Names
- `service-name-service`, `for service-name`, `in service-name`
- Hyphenated names: `checkout-service`, `user-auth-service`

### Log Levels
- `error/errors`, `warn/warning/warnings`
- `info`, `debug`, `trace`

### Size Specifications
- `top X`, `first X`, `limit X`, `show X results`

## Error Handling

For unsupported queries, returns:
```json
{"error": "Unsupported query. Please rephrase or check available APIs."}
```

## Logging and Debugging

### Enable Query Logging

The parser supports detailed logging to help debug and monitor query processing:

```python
from nlq_parser import NLQParser

# Enable logging (default)
parser = NLQParser(enable_logging=True)
result = parser.parse("errors in last 5 minutes for checkout-service")

# Disable logging for production
parser = NLQParser(enable_logging=False)  
result = parser.parse("errors in last 5 minutes for checkout-service")
```

### Log Output Example

With logging enabled, you'll see detailed processing information:

```
2025-09-15 15:06:38,401 - nlq_parser - INFO - Processing query: 'errors in last 5 minutes for checkout-service'
2025-09-15 15:06:38,402 - nlq_parser - INFO - Generated OpenSearch query: {"size":50,"sort":[{"@timestamp":"desc"}],"query":{"bool":{"must":[{"match":{"log.level":"error"}},{"match":{"service.name":"checkout-service"}},{"range":{"@timestamp":{"gte":"now-5m"}}}]}}}
```

### Debug Mode

For even more detailed logging, use debug mode:

```python
from nlq_parser import NLQParser, configure_logging
import logging

# Configure debug logging  
configure_logging(enable_debug=True)
parser = NLQParser(enable_logging=True)
```

This will show:
- Input query processing
- Component extraction (service names, time ranges, log levels)
- Query type identification (search, cluster, cat APIs)
- Boolean query construction
- Error handling steps

## Installation

No external dependencies required. Uses only Python standard library.

```bash
# Clone the repository
git clone <repo-url>

# Run directly
python3 nlq_parser.py

# Or import in your code
from nlq_parser import NLQParser
```

## Contributing

1. Add new patterns to the parsing methods
2. Extend query builders for new OpenSearch features  
3. Add test cases for new functionality
4. Update examples and documentation

## License

MIT License
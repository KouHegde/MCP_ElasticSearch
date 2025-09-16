# Natural Language to OpenSearch Query Parser

Convert natural language questions into OpenSearch queries and execute them to get real log data.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive mode
python webex_client.py

# Single query mode
python webex_client.py "errors in last 5 minutes for Hydra"
```

## Features

- **Natural Language Processing**: Ask questions in plain English
- **Smart Query Generation**: Automatically builds valid OpenSearch JSON queries
- **Live Execution**: Connects to Webex logs and returns actual results
- **Service Filtering**: Maps service names to `service.name` field
- **Time Parsing**: Handles relative times like "last 5 minutes", "today"
- **Log Level Filtering**: Supports error, warning, debug, info levels

## Example Queries

```
"errors in last 5 minutes for Hydra"
"warnings from api-gateway in last hour" 
"debug logs from auth service today"
"authentication failures in last 30 minutes"
"show cluster health"
```

## Core Files

- `nlq_parser.py` - Natural language to OpenSearch query converter
- `webex_client.py` - Simple client that executes queries and returns results
- `demo.py` - Basic demo script
- `examples.py` - Query examples

## Usage

### Interactive Mode
```bash
python webex_client.py
```

### Command Line
```bash
python webex_client.py "your natural language query"
```

### Programmatic
```python
from webex_client import WebexLogsClient

client = WebexLogsClient("your-access-token")
result = client.query("errors in last hour")

if result.get("success"):
    print(f"Found {result['total_hits']} logs")
    for log in result['logs']:
        print(f"{log['timestamp']} | {log['level']} | {log['message']}")
```

## Query Structure

The system generates OpenSearch queries with:
- Default size: 50 results
- Default sort: `@timestamp` descending  
- Service name mapping to `service.name`
- Time range filtering with relative time support
- Boolean queries for multiple conditions

## License

MIT License
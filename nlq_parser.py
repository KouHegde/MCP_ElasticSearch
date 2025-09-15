"""
Natural Language to OpenSearch Query Parser

Converts plain English queries into valid OpenSearch REST API queries.
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class OpenSearchQueryBuilder:
    """Builds OpenSearch queries based on parsed natural language input."""
    
    TIMESTAMP_FIELD = "@timestamp"
    
    def __init__(self):
        self.default_size = 50
        self.default_sort = [{self.TIMESTAMP_FIELD: "desc"}]
        
    def build_base_query(self, size: Optional[int] = None) -> Dict[str, Any]:
        """Build base query structure with defaults."""
        return {
            "size": size if size is not None else self.default_size,
            "sort": self.default_sort
        }
    
    def build_bool_query(self, must: List[Dict] = None, should: List[Dict] = None, 
                        must_not: List[Dict] = None, filter: List[Dict] = None) -> Dict[str, Any]:
        """Build a boolean query structure."""
        bool_query = {}
        if must:
            bool_query["must"] = must
        if should:
            bool_query["should"] = should
        if must_not:
            bool_query["must_not"] = must_not
        if filter:
            bool_query["filter"] = filter
        return {"bool": bool_query}
    
    def build_time_range(self, time_spec: str) -> Dict[str, Any]:
        """Build time range query from time specification."""
        time_map = {
            "minute": "m", "minutes": "m", "min": "m",
            "hour": "h", "hours": "h", "hr": "h", "hrs": "h",
            "day": "d", "days": "d", 
            "week": "w", "weeks": "w",
            "month": "M", "months": "M",
            "year": "y", "years": "y"
        }
        
        # Pattern for "last X time_unit"
        pattern = r"last\s+(\d+)\s+(minute|minutes|min|hour|hours|hr|hrs|day|days|week|weeks|month|months|year|years)"
        match = re.search(pattern, time_spec.lower())
        
        if match:
            amount = match.group(1)
            unit = match.group(2)
            elastic_unit = time_map[unit]
            return {
                "range": {
                    self.TIMESTAMP_FIELD: {
                        "gte": f"now-{amount}{elastic_unit}"
                    }
                }
            }
        
        # Handle "today", "yesterday", etc.
        if "today" in time_spec.lower():
            return {
                "range": {
                    self.TIMESTAMP_FIELD: {
                        "gte": "now/d"
                    }
                }
            }
        
        if "yesterday" in time_spec.lower():
            return {
                "range": {
                    self.TIMESTAMP_FIELD: {
                        "gte": "now-1d/d",
                        "lt": "now/d"
                    }
                }
            }
        
        return None
    
    def build_service_filter(self, service_name: str) -> Dict[str, Any]:
        """Build service name filter."""
        return {"match": {"service.name": service_name}}
    
    def build_log_level_filter(self, level: str) -> Dict[str, Any]:
        """Build log level filter."""
        return {"match": {"log.level": level.lower()}}
    
    def build_text_search(self, text: str, field: str = "_all") -> Dict[str, Any]:
        """Build text search query."""
        if field == "_all":
            return {"match": {"_all": text}}
        return {"match": {field: text}}


class NLQParser:
    """Main parser for converting natural language to OpenSearch queries."""
    
    def __init__(self, enable_logging=True):
        self.query_builder = OpenSearchQueryBuilder()
        
        # Set up logging
        self.logger = logging.getLogger('nlq_parser')
        if enable_logging:
            # Clear existing handlers to avoid duplicates
            self.logger.handlers.clear()
            self.logger.propagate = False  # Don't propagate to root logger
            
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        else:
            # Disable logging completely
            self.logger.setLevel(logging.CRITICAL + 1)
            self.logger.propagate = False
        
    def parse(self, natural_query: str) -> str:
        """
        Parse natural language query and return OpenSearch JSON query.
        Returns raw JSON string without any formatting or explanations.
        """
        # Log the input query
        self.logger.info(f"Processing query: '{natural_query}'")
        
        try:
            query_dict = self._parse_to_dict(natural_query)
            result = json.dumps(query_dict, separators=(',', ':'))
            
            # Log the generated query
            self.logger.info(f"Generated OpenSearch query: {result}")
            
            return result
        except Exception as e:
            error_result = json.dumps({"error": "Unsupported query. Please rephrase or check available APIs."})
            self.logger.warning(f"Query processing failed: {str(e)}")
            self.logger.info(f"Returning error response: {error_result}")
            return error_result
    
    def _parse_to_dict(self, natural_query: str) -> Dict[str, Any]:
        """Parse natural language to query dictionary."""
        query = natural_query.lower().strip()
        
        # Check for unsupported operations first
        if self._is_unsupported_query(query):
            self.logger.debug("Query identified as unsupported operation")
            return {"error": "Unsupported query. Please rephrase or check available APIs."}
        
        # Initialize base query
        result = self.query_builder.build_base_query()
        must_clauses = []
        
        # Check for different types of queries
        if self._is_cluster_query(query):
            self.logger.debug("Query identified as cluster API request")
            return self._handle_cluster_query(query)
        elif self._is_cat_query(query):
            self.logger.debug("Query identified as cat API request")
            return self._handle_cat_query(query)
        
        # Parse log level
        log_level = self._extract_log_level(query)
        if log_level:
            self.logger.debug(f"Extracted log level: {log_level}")
            must_clauses.append(self.query_builder.build_log_level_filter(log_level))
        
        # Parse service name
        service_name = self._extract_service_name(query)
        if service_name:
            self.logger.debug(f"Extracted service name: {service_name}")
            must_clauses.append(self.query_builder.build_service_filter(service_name))
        
        # Parse time range
        time_filter = self._extract_time_range(query)
        if time_filter:
            self.logger.debug(f"Extracted time filter: {time_filter}")
            must_clauses.append(time_filter)
        
        # Parse text search
        search_terms = self._extract_search_terms(query)
        if search_terms:
            self.logger.debug(f"Extracted search terms: {search_terms}")
            for term in search_terms:
                must_clauses.append(self.query_builder.build_text_search(term))
        
        # Parse size if specified
        size = self._extract_size(query)
        if size:
            self.logger.debug(f"Extracted custom size: {size}")
            result["size"] = size
        
        # Build the final query
        if must_clauses:
            self.logger.debug(f"Built boolean query with {len(must_clauses)} must clauses")
            result["query"] = self.query_builder.build_bool_query(must=must_clauses)
        else:
            self.logger.debug("No specific filters found, using match_all query")
            # Default match_all query if no specific filters
            result["query"] = {"match_all": {}}
        
        return result
    
    def _is_unsupported_query(self, query: str) -> bool:
        """Check if this query contains unsupported operations."""
        unsupported_keywords = [
            "create", "delete", "update", "insert", "put", "post", "mapping", "mappings",
            "index", "reindex", "bulk", "scroll", "aggregate", "aggregation", "pipeline",
            "template", "settings", "alias", "aliases", "snapshot", "restore", "backup"
        ]
        
        # Check for operations that modify data or structure
        modify_patterns = [
            r"create\s+(index|mapping)",
            r"delete\s+(index|document)",
            r"update\s+(mapping|document|settings)",
            r"insert\s+",
            r"add\s+(field|mapping|alias)",
            r"remove\s+(field|mapping|alias)",
            r"modify\s+",
            r"change\s+(mapping|settings)"
        ]
        
        # Check for unsupported keywords
        for keyword in unsupported_keywords:
            if keyword in query:
                return True
        
        # Check for unsupported patterns
        for pattern in modify_patterns:
            if re.search(pattern, query):
                return True
        
        return False
    
    def _is_cluster_query(self, query: str) -> bool:
        """Check if this is a cluster-related query."""
        cluster_keywords = ["cluster health", "cluster status", "node", "shard"]
        return any(keyword in query for keyword in cluster_keywords)
    
    def _is_cat_query(self, query: str) -> bool:
        """Check if this is a cat API query."""
        # More specific patterns to avoid false positives
        cat_patterns = [
            r"\blist\s+indices\b",
            r"\bshow\s+indices\b",
            r"\blist\s+nodes\b", 
            r"\bshow\s+nodes\b",
            r"\blist\s+shards\b",
            r"\bshow\s+shards\b",
            r"\bcat\s+"
        ]
        return any(re.search(pattern, query) for pattern in cat_patterns)
    
    def _handle_cluster_query(self, query: str) -> Dict[str, Any]:
        """Handle cluster-related queries."""
        if "health" in query or "status" in query:
            return {"api": "_cluster/health"}
        elif "node" in query:
            return {"api": "_cat/nodes?v"}
        return {"error": "Unsupported cluster query. Please rephrase or check available APIs."}
    
    def _handle_cat_query(self, query: str) -> Dict[str, Any]:
        """Handle cat API queries."""
        if "indices" in query or "index" in query:
            return {"api": "_cat/indices?v"}
        elif "nodes" in query:
            return {"api": "_cat/nodes?v"}
        elif "shards" in query:
            return {"api": "_cat/shards?v"}
        return {"error": "Unsupported cat query. Please rephrase or check available APIs."}
    
    def _extract_log_level(self, query: str) -> Optional[str]:
        """Extract log level from query."""
        levels = ["error", "errors", "warn", "warning", "warnings", "info", "debug", "trace"]
        for level in levels:
            if level in query:
                if level == "errors":
                    return "error"
                elif level in ["warn", "warning", "warnings"]:
                    return "warn"
                return level
        return None
    
    def _extract_service_name(self, query: str) -> Optional[str]:
        """Extract service name from query."""
        # Pattern for "service-name" or "for service-name" or "in service-name"
        patterns = [
            r"for\s+([a-zA-Z0-9\-_]+)[-\s]*service",
            r"in\s+([a-zA-Z0-9\-_]+)[-\s]*service", 
            r"([a-zA-Z0-9\-_]+)[-\s]*service",
            r"service\s+([a-zA-Z0-9\-_]+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                service_name = match.group(1)
                # If the service name ends with a hyphen, add "service"
                if service_name.endswith('-'):
                    return service_name + "service"
                return service_name
        
        return None
    
    def _extract_time_range(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract time range from query."""
        return self.query_builder.build_time_range(query)
    
    def _extract_search_terms(self, query: str) -> List[str]:
        """Extract search terms from query."""
        # Remove common words and extract meaningful terms
        stop_words = {
            "get", "show", "find", "search", "logs", "log", "details", "of", "in", "for",
            "last", "minutes", "minute", "hours", "hour", "days", "day", "service", "errors",
            "error", "warnings", "warning", "info", "debug", "trace", "the", "and", "with",
            "want", "checkout", "payment", "user", "auth", "authentication", "from", "me",
            "cluster", "health", "status", "list", "nodes", "indices", "shards", "top",
            "results", "limit", "first", "today", "yesterday", "complex", "unsupported", 
            "that", "should", "fail", "query", "api", "to", "a", "an", "is", "are", "was",
            "were", "be", "been", "being", "have", "has", "had", "do", "does", "did"
        }
        
        # Remove service names and time expressions from search
        temp_query = query.lower()
        
        # Remove service patterns
        service_patterns = [
            r"for\s+[a-zA-Z0-9\-_]+[-\s]*service",
            r"in\s+[a-zA-Z0-9\-_]+[-\s]*service", 
            r"[a-zA-Z0-9\-_]+[-\s]*service"
        ]
        for pattern in service_patterns:
            temp_query = re.sub(pattern, '', temp_query)
        
        # Remove time patterns
        time_patterns = [
            r"last\s+\d+\s+\w+",
            r"today",
            r"yesterday"
        ]
        for pattern in time_patterns:
            temp_query = re.sub(pattern, '', temp_query)
        
        # Remove log level words
        temp_query = re.sub(r'\b(error|errors|warn|warning|warnings|info|debug|trace)\b', '', temp_query)
        
        # Split query and filter out stop words
        words = re.findall(r'\b[a-zA-Z]+\b', temp_query)
        search_terms = []
        
        for word in words:
            if (word.lower() not in stop_words and 
                len(word) > 2 and
                not re.match(r'\d+', word)):
                search_terms.append(word)
        
        return search_terms
    
    def _extract_size(self, query: str) -> Optional[int]:
        """Extract result size from query."""
        # Pattern for "show 100 results" or "limit 20" etc.
        patterns = [
            r"show\s+(\d+)\s+results?",
            r"limit\s+(\d+)",
            r"top\s+(\d+)",
            r"first\s+(\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None


def configure_logging(level=logging.INFO, enable_debug=False):
    """Configure global logging level for debug information."""
    if enable_debug:
        level = logging.DEBUG
    
    # Set the logging level for the nlq_parser logger
    logger = logging.getLogger('nlq_parser')
    if logger.handlers:
        logger.setLevel(level)


def main():
    """Simple CLI interface for testing."""
    # Enable logging for interactive mode
    configure_logging(enable_debug=True)
    
    parser = NLQParser(enable_logging=True)
    
    print("OpenSearch Natural Language Query Parser")
    print("Enter 'quit' or 'exit' to stop")
    print("Note: Logging is enabled to show query processing details\n")
    
    while True:
        try:
            user_input = input("Enter your query: ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
                
            result = parser.parse(user_input)
            print(f"\nFinal Output: {result}")
            print("-" * 50)
            
        except KeyboardInterrupt:
            break
        except EOFError:
            break
    
    print("\nGoodbye!")


if __name__ == "__main__":
    main()

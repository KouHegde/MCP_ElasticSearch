"""
OpenSearch Client with Natural Language Query Support

This module provides a full OpenSearch client that can connect to clusters
and execute queries generated from natural language input.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

try:
    from opensearchpy import OpenSearch
    from opensearchpy.exceptions import OpenSearchException, ConnectionError, AuthenticationException
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    OpenSearch = None
    OpenSearchException = Exception
    ConnectionError = Exception
    AuthenticationException = Exception

from nlq_parser import NLQParser


@dataclass
class OpenSearchConfig:
    """Configuration for OpenSearch connection."""
    hosts: List[Dict[str, Union[str, int]]]
    http_auth: Optional[tuple] = None
    api_key: Optional[tuple] = None
    use_ssl: bool = True
    verify_certs: bool = True
    ssl_assert_hostname: bool = True
    ssl_show_warn: bool = True
    timeout: int = 30
    max_retries: int = 3
    retry_on_timeout: bool = True


class OpenSearchNLQClient:
    """
    Full OpenSearch client with natural language query support.
    
    This client combines the NLQParser with actual OpenSearch connectivity
    to execute queries against live clusters.
    """
    
    def __init__(self, config: OpenSearchConfig, enable_logging: bool = True):
        """
        Initialize the OpenSearch client.
        
        Args:
            config: OpenSearch connection configuration
            enable_logging: Enable detailed logging for debugging
        """
        if not OPENSEARCH_AVAILABLE:
            raise ImportError(
                "opensearch-py is required for the full client. "
                "Install with: pip install opensearch-py"
            )
        
        self.config = config
        self.nlq_parser = NLQParser(enable_logging=enable_logging)
        
        # Set up logging
        self.logger = logging.getLogger('opensearch_client')
        if enable_logging:
            self.logger.handlers.clear()
            self.logger.propagate = False
            
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.CRITICAL + 1)
            self.logger.propagate = False
        
        # Initialize OpenSearch client
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenSearch client with configuration."""
        try:
            client_config = {
                'hosts': self.config.hosts,
                'use_ssl': self.config.use_ssl,
                'verify_certs': self.config.verify_certs,
                'ssl_assert_hostname': self.config.ssl_assert_hostname,
                'ssl_show_warn': self.config.ssl_show_warn,
                'timeout': self.config.timeout,
                'max_retries': self.config.max_retries,
                'retry_on_timeout': self.config.retry_on_timeout,
            }
            
            # Add authentication
            if self.config.http_auth:
                client_config['http_auth'] = self.config.http_auth
            elif self.config.api_key:
                client_config['api_key'] = self.config.api_key
            
            self.client = OpenSearch(**client_config)
            self.logger.info(f"OpenSearch client initialized for hosts: {self.config.hosts}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenSearch client: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test the connection to OpenSearch cluster.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            info = self.client.info()
            self.logger.info(f"Connected to OpenSearch cluster: {info.get('version', {}).get('number', 'unknown')}")
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def get_cluster_health(self) -> Dict[str, Any]:
        """Get cluster health information."""
        try:
            health = self.client.cluster.health()
            self.logger.info(f"Cluster status: {health.get('status', 'unknown')}")
            return health
        except Exception as e:
            self.logger.error(f"Failed to get cluster health: {str(e)}")
            raise
    
    def list_indices(self, pattern: str = "*") -> List[str]:
        """
        List indices matching the pattern.
        
        Args:
            pattern: Index pattern (default: all indices)
            
        Returns:
            List of index names
        """
        try:
            indices = self.client.cat.indices(index=pattern, format='json')
            index_names = [idx['index'] for idx in indices]
            self.logger.info(f"Found {len(index_names)} indices matching pattern '{pattern}'")
            return index_names
        except Exception as e:
            self.logger.error(f"Failed to list indices: {str(e)}")
            raise
    
    def query(self, natural_language_query: str, index: str = "*", 
             execute: bool = True) -> Union[str, Dict[str, Any]]:
        """
        Convert natural language to OpenSearch query and optionally execute it.
        
        Args:
            natural_language_query: Plain English query
            index: Target index pattern (default: all indices)
            execute: Whether to execute the query (True) or return JSON (False)
            
        Returns:
            If execute=True: Query results from OpenSearch
            If execute=False: Raw JSON query string
        """
        self.logger.info(f"Processing natural language query: '{natural_language_query}'")
        
        # Generate query using NLQ parser
        query_json = self.nlq_parser.parse(natural_language_query)
        
        # Handle special API calls
        try:
            query_dict = json.loads(query_json)
            
            # Handle cluster health API
            if "api" in query_dict and "_cluster/health" in query_dict["api"]:
                if execute:
                    return self.get_cluster_health()
                else:
                    return query_json
            
            # Handle cat APIs
            if "api" in query_dict and "_cat/" in query_dict["api"]:
                if "_cat/indices" in query_dict["api"]:
                    if execute:
                        return {"indices": self.list_indices()}
                    else:
                        return query_json
                # Add more cat API handlers as needed
            
            # Handle error responses
            if "error" in query_dict:
                return query_dict if execute else query_json
            
            # Execute search query
            if execute:
                return self._execute_search(query_dict, index)
            else:
                return query_json
                
        except json.JSONDecodeError:
            error_msg = "Invalid query generated"
            self.logger.error(error_msg)
            if execute:
                return {"error": error_msg}
            else:
                return query_json
    
    def _execute_search(self, query_dict: Dict[str, Any], index: str) -> Dict[str, Any]:
        """Execute a search query against OpenSearch."""
        try:
            self.logger.info(f"Executing search on index pattern: '{index}'")
            self.logger.debug(f"Query body: {json.dumps(query_dict)}")
            
            response = self.client.search(
                index=index,
                body=query_dict
            )
            
            # Log summary of results
            total_hits = response.get('hits', {}).get('total', {})
            if isinstance(total_hits, dict):
                hit_count = total_hits.get('value', 0)
            else:
                hit_count = total_hits
            
            self.logger.info(f"Query executed successfully. Found {hit_count} hits")
            return response
            
        except OpenSearchException as e:
            error_msg = f"OpenSearch query failed: {str(e)}"
            self.logger.error(error_msg)
            return {
                "error": error_msg,
                "query": query_dict,
                "index": index
            }
    
    def search_logs(self, natural_query: str, index: str = "logs-*", 
                   limit: int = None) -> Dict[str, Any]:
        """
        Convenience method for searching logs with natural language.
        
        Args:
            natural_query: Plain English description of what to search for
            index: Log index pattern (default: logs-*)
            limit: Maximum number of results to return
            
        Returns:
            Search results with formatted hits
        """
        response = self.query(natural_query, index=index, execute=True)
        
        if "error" in response:
            return response
        
        # Format the response for easier consumption
        hits = response.get('hits', {}).get('hits', [])
        if limit:
            hits = hits[:limit]
        
        formatted_results = {
            "total_hits": response.get('hits', {}).get('total', {}),
            "took_ms": response.get('took', 0),
            "logs": []
        }
        
        for hit in hits:
            log_entry = {
                "timestamp": hit.get('_source', {}).get('@timestamp'),
                "level": hit.get('_source', {}).get('log', {}).get('level'),
                "service": hit.get('_source', {}).get('service', {}).get('name'),
                "message": hit.get('_source', {}).get('message', ''),
                "source": hit.get('_source', {}),
                "score": hit.get('_score', 0)
            }
            formatted_results["logs"].append(log_entry)
        
        return formatted_results


def create_client_from_env() -> OpenSearchNLQClient:
    """
    Create client from environment variables.
    
    Expected environment variables:
    - OPENSEARCH_HOST: Cluster host (default: localhost)
    - OPENSEARCH_PORT: Cluster port (default: 9200)
    - OPENSEARCH_USERNAME: Username for authentication
    - OPENSEARCH_PASSWORD: Password for authentication
    - OPENSEARCH_USE_SSL: Use SSL (default: true)
    """
    import os
    
    host = os.getenv('OPENSEARCH_HOST', 'localhost')
    port = int(os.getenv('OPENSEARCH_PORT', '9200'))
    username = os.getenv('OPENSEARCH_USERNAME')
    password = os.getenv('OPENSEARCH_PASSWORD')
    use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'true').lower() == 'true'
    
    config = OpenSearchConfig(
        hosts=[{'host': host, 'port': port}],
        use_ssl=use_ssl,
        verify_certs=use_ssl
    )
    
    if username and password:
        config.http_auth = (username, password)
    
    return OpenSearchNLQClient(config)


# Example usage functions
def example_usage():
    """Example of how to use the OpenSearch NLQ Client."""
    
    # Configuration for OpenSearch cluster
    config = OpenSearchConfig(
        hosts=[{'host': 'localhost', 'port': 9200}],
        http_auth=('admin', 'admin'),  # or use api_key instead
        use_ssl=False,  # Set to True for production clusters
        verify_certs=False  # Set to True for production clusters
    )
    
    try:
        # Create client
        client = OpenSearchNLQClient(config, enable_logging=True)
        
        # Test connection
        if client.test_connection():
            print("✅ Connected to OpenSearch!")
        else:
            print("❌ Connection failed!")
            return
        
        # Example queries
        queries = [
            "show me errors from last 5 minutes for checkout-service",
            "warnings in api-gateway last hour",
            "cluster health",
            "list indices"
        ]
        
        for query in queries:
            print(f"\n--- Query: '{query}' ---")
            result = client.query(query, index="logs-*", execute=True)
            print(f"Result: {json.dumps(result, indent=2)[:500]}...")
            
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    example_usage()

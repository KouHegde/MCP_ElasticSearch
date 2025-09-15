"""
OpenSearch Configuration Examples

This file shows different ways to configure the OpenSearch client
for various deployment scenarios.
"""

from opensearch_client import OpenSearchConfig, OpenSearchNLQClient


# Example 1: Local Development (OpenSearch running on localhost)
def local_development_config():
    """Configuration for local OpenSearch instance."""
    return OpenSearchConfig(
        hosts=[{'host': 'localhost', 'port': 9200}],
        http_auth=('admin', 'admin'),  # Default OpenSearch credentials
        use_ssl=False,
        verify_certs=False,
        timeout=30
    )


# Example 2: AWS OpenSearch Service
def aws_opensearch_config():
    """Configuration for AWS OpenSearch Service."""
    return OpenSearchConfig(
        hosts=[{'host': 'search-your-domain.us-east-1.es.amazonaws.com', 'port': 443}],
        http_auth=('username', 'password'),  # Or use AWS IAM credentials
        use_ssl=True,
        verify_certs=True,
        timeout=60
    )


# Example 3: Self-managed cluster with SSL
def production_config():
    """Configuration for production OpenSearch cluster."""
    return OpenSearchConfig(
        hosts=[
            {'host': 'opensearch-1.company.com', 'port': 9200},
            {'host': 'opensearch-2.company.com', 'port': 9200},
            {'host': 'opensearch-3.company.com', 'port': 9200},
        ],
        http_auth=('service_account', 'secure_password'),
        use_ssl=True,
        verify_certs=True,
        ssl_assert_hostname=True,
        timeout=45,
        max_retries=5,
        retry_on_timeout=True
    )


# Example 4: API Key Authentication
def api_key_config():
    """Configuration using API key authentication."""
    return OpenSearchConfig(
        hosts=[{'host': 'your-cluster.company.com', 'port': 443}],
        api_key=('api_key_id', 'api_key_secret'),  # Instead of http_auth
        use_ssl=True,
        verify_certs=True
    )


# Example 5: Environment-based configuration
def environment_config():
    """
    Configuration using environment variables.
    
    Set these environment variables:
    - OPENSEARCH_HOST
    - OPENSEARCH_PORT
    - OPENSEARCH_USERNAME
    - OPENSEARCH_PASSWORD
    - OPENSEARCH_USE_SSL
    """
    import os
    
    host = os.getenv('OPENSEARCH_HOST', 'localhost')
    port = int(os.getenv('OPENSEARCH_PORT', '9200'))
    username = os.getenv('OPENSEARCH_USERNAME')
    password = os.getenv('OPENSEARCH_PASSWORD')
    use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'false').lower() == 'true'
    
    config = OpenSearchConfig(
        hosts=[{'host': host, 'port': port}],
        use_ssl=use_ssl,
        verify_certs=use_ssl
    )
    
    if username and password:
        config.http_auth = (username, password)
    
    return config


# Example usage
def main():
    """Example of using different configurations."""
    
    # Choose your configuration
    configs = {
        'local': local_development_config(),
        'aws': aws_opensearch_config(),
        'production': production_config(),
        'api_key': api_key_config(),
        'environment': environment_config()
    }
    
    # Use local config for this example
    config = configs['local']
    
    try:
        # Create client
        client = OpenSearchNLQClient(config, enable_logging=True)
        
        # Test connection
        if client.test_connection():
            print("✅ Connected to OpenSearch!")
            
            # Run a natural language query
            result = client.query("show me errors from last 5 minutes", execute=False)
            print(f"Generated query: {result}")
            
        else:
            print("❌ Connection failed - check your configuration")
            
    except ImportError:
        print("opensearch-py not installed. Run: pip install opensearch-py")
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    main()

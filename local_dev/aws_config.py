import boto3
import json
import os
from functools import lru_cache

class AWSConfig:
    """
    Manages AWS Secrets Manager integration for application secrets.
    Falls back to environment variables for local development.
    """
    
    def __init__(self):
        self.is_aws = os.getenv('AWS_EXECUTION_ENV') is not None
        self._secrets = None
        
    @lru_cache(maxsize=1)
    def get_secrets(self):
        """
        Fetch secrets from AWS Secrets Manager or environment variables.
        Cached to avoid repeated API calls.
        """
        if self._secrets:
            return self._secrets
            
        if self.is_aws:
            # Running in AWS - use Secrets Manager
            secret_name = os.getenv('SECRET_NAME', 'prod/fastapi/606')
            region_name = os.getenv('AWS_REGION', 'us-east-1')
            
            try:
                session = boto3.session.Session()
                client = session.client(
                    service_name='secretsmanager',
                    region_name=region_name
                )
                
                get_secret_value_response = client.get_secret_value(
                    SecretId=secret_name
                )
                self._secrets = json.loads(get_secret_value_response['SecretString'])
            except Exception as e:
                print(f"Error retrieving secrets from AWS: {e}")
                # Fall back to environment variables
                self._secrets = self._load_from_env()
        else:
            # Running locally - use environment variables
            self._secrets = self._load_from_env()
        
        return self._secrets
    
    def _load_from_env(self):
        """Load secrets from environment variables or .env file"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except:
            pass
        
        return {
            'DB_HOST': os.getenv('DB_HOST'),
            'DB_PORT': os.getenv('DB_PORT', '5432'),
            'DB_NAME': os.getenv('DB_NAME'),
            'DB_USER': os.getenv('DB_USER'),
            'DB_PASSWORD': os.getenv('DB_PASSWORD'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
        }
    
    def get(self, key, default=None):
        """Get a specific secret by key"""
        secrets = self.get_secrets()
        return secrets.get(key, default)

# Singleton instance
config = AWSConfig()
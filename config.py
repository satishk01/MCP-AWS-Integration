import os
from typing import Dict, Any

class Config:
    """Configuration management for the application"""
    
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_PROFILE = os.getenv('AWS_PROFILE', 'default')
    
    # Bedrock Configuration - Nova Pro requires inference profiles
    BEDROCK_MODEL_ID = "us.amazon.nova-pro-v1:0"  # Cross-region inference profile
    
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    
    # MCP Server Configuration
    MCP_SERVERS = {
        "git_repo_research": {
            "command": "uvx",
            "args": ["awslabs.git-repo-research-mcp-server@latest"],
            "env": {
                "AWS_PROFILE": AWS_PROFILE,
                "AWS_REGION": AWS_REGION,
                "FASTMCP_LOG_LEVEL": "ERROR",
                "GITHUB_TOKEN": GITHUB_TOKEN
            }
        },
        "code_doc_gen": {
            "command": "uvx", 
            "args": ["awslabs.code-doc-gen-mcp-server@latest"],
            "env": {
                "FASTMCP_LOG_LEVEL": "ERROR"
            }
        }
    }
    
    # Streamlit Configuration
    STREAMLIT_CONFIG = {
        "page_title": "AWS MCP Research & Documentation Assistant",
        "page_icon": "🔬",
        "layout": "wide"
    }
    
    @classmethod
    def get_aws_config(cls) -> Dict[str, Any]:
        """Get AWS configuration"""
        return {
            "region_name": cls.AWS_REGION,
            "profile_name": cls.AWS_PROFILE
        }
    
    @classmethod
    def get_bedrock_config(cls) -> Dict[str, Any]:
        """Get Bedrock configuration"""
        return {
            "model_id": cls.BEDROCK_MODEL_ID,
            "region_name": cls.AWS_REGION
        }
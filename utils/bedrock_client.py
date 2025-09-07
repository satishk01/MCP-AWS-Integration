import boto3
import json
import logging
from typing import Dict, Any, Optional, List
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class BedrockClient:
    """Client for interacting with Amazon Bedrock and Nova Pro model"""
    
    def __init__(self, region_name: str = "us-west-2", profile_name: Optional[str] = None):
        """Initialize Bedrock client"""
        try:
            # Initialize boto3 session
            if profile_name:
                session = boto3.Session(profile_name=profile_name)
                self.bedrock_runtime = session.client('bedrock-runtime', region_name=region_name)
            else:
                self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
            
            self.region_name = region_name
            self.model_id = "amazon.nova-pro-v1:0"
            
            logger.info(f"Initialized Bedrock client for region: {region_name}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    def generate_text(self, 
                     prompt: str, 
                     context: str = "", 
                     max_tokens: int = 4000,
                     temperature: float = 0.7,
                     top_p: float = 0.9) -> str:
        """Generate text using Nova Pro model"""
        try:
            # Prepare the message content
            content = f"{context}\n\n{prompt}" if context else prompt
            
            # Prepare request body for Nova Pro
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            else:
                logger.error("Unexpected response format from Nova Pro")
                return "Error: Unexpected response format"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock API error ({error_code}): {error_message}")
            return f"Error: {error_message}"
        except Exception as e:
            logger.error(f"Error generating text with Nova Pro: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_chat_response(self, 
                              messages: List[Dict[str, str]], 
                              max_tokens: int = 4000,
                              temperature: float = 0.7,
                              top_p: float = 0.9) -> str:
        """Generate chat response using Nova Pro model"""
        try:
            # Prepare request body for Nova Pro
            request_body = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p
            }
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                return response_body['content'][0]['text']
            else:
                logger.error("Unexpected response format from Nova Pro")
                return "Error: Unexpected response format"
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock API error ({error_code}): {error_message}")
            return f"Error: {error_message}"
        except Exception as e:
            logger.error(f"Error generating chat response with Nova Pro: {e}")
            return f"Error generating response: {str(e)}"
    
    def analyze_code(self, code: str, analysis_type: str = "general") -> str:
        """Analyze code using Nova Pro model"""
        prompt = f"""
        Please analyze the following code and provide insights about:
        - Code quality and best practices
        - Potential issues or improvements
        - Security considerations
        - Performance optimization opportunities
        - Documentation suggestions
        
        Analysis type: {analysis_type}
        
        Code:
        ```
        {code}
        ```
        """
        
        return self.generate_text(prompt)
    
    def enhance_documentation(self, original_doc: str, code: str = "") -> str:
        """Enhance documentation using Nova Pro model"""
        context = f"Original code:\n{code}\n\n" if code else ""
        
        prompt = f"""
        Please enhance the following documentation by:
        - Adding more detailed explanations
        - Including usage examples
        - Adding best practices and tips
        - Improving clarity and structure
        - Adding relevant links or references where appropriate
        
        Original documentation:
        {original_doc}
        """
        
        return self.generate_text(prompt, context)
    
    def explain_repository_analysis(self, analysis_results: Dict[str, Any]) -> str:
        """Explain repository analysis results using Nova Pro model"""
        context = f"Repository analysis results:\n{json.dumps(analysis_results, indent=2)}"
        
        prompt = """
        Please provide a comprehensive explanation of the repository analysis results including:
        - Summary of key findings
        - Architectural insights
        - Code quality assessment
        - Security considerations
        - Recommendations for improvement
        - Next steps for developers
        
        Make the explanation clear and actionable for developers.
        """
        
        return self.generate_text(prompt, context)
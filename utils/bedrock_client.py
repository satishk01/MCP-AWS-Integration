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
                self.bedrock_client = session.client('bedrock', region_name=region_name)
            else:
                self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region_name)
                self.bedrock_client = boto3.client('bedrock', region_name=region_name)
            
            self.region_name = region_name
            # Use inference profile for Nova Pro instead of direct model ID
            self.model_id = self._get_nova_pro_inference_profile()
            
            logger.info(f"Initialized Bedrock client for region: {region_name}")
            logger.info(f"Using Nova Pro inference profile: {self.model_id}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure your credentials.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Bedrock client: {e}")
            raise
    
    def _get_nova_pro_inference_profile(self) -> str:
        """Get the appropriate Nova Pro inference profile"""
        try:
            # Try to list inference profiles to find Nova Pro
            response = self.bedrock_client.list_inference_profiles()
            
            for profile in response.get('inferenceProfileSummaries', []):
                if 'nova-pro' in profile.get('inferenceProfileName', '').lower():
                    logger.info(f"Found Nova Pro inference profile: {profile['inferenceProfileId']}")
                    return profile['inferenceProfileId']
            
            # If no inference profile found, try the cross-region inference profile
            # This is a common pattern for Nova models
            cross_region_profile = f"us.amazon.nova-pro-v1:0"
            logger.info(f"Using cross-region inference profile: {cross_region_profile}")
            return cross_region_profile
            
        except Exception as e:
            logger.warning(f"Could not retrieve inference profiles: {e}")
            # Fallback to cross-region inference profile
            cross_region_profile = f"us.amazon.nova-pro-v1:0"
            logger.info(f"Using fallback cross-region inference profile: {cross_region_profile}")
            return cross_region_profile
    
    def generate_text(self, 
                     prompt: str, 
                     context: str = "", 
                     max_tokens: int = 4000,
                     temperature: float = 0.7) -> str:
        """Generate text using Nova Pro model"""
        try:
            # Prepare the message content
            content = f"{context}\n\n{prompt}" if context else prompt
            
            # Prepare request body for Nova Pro
            request_body = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "text": content
                            }
                        ]
                    }
                ],
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Nova Pro response format
            if 'output' in response_body and 'message' in response_body['output']:
                message = response_body['output']['message']
                if 'content' in message and len(message['content']) > 0:
                    return message['content'][0]['text']
            
            logger.error(f"Unexpected response format from Nova Pro: {response_body}")
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
                              messages: List[Dict[str, Any]], 
                              max_tokens: int = 4000,
                              temperature: float = 0.7) -> str:
        """Generate chat response using Nova Pro model"""
        try:
            # Convert messages to Nova Pro format
            nova_messages = []
            for msg in messages:
                nova_msg = {
                    "role": msg["role"],
                    "content": [
                        {
                            "text": msg["content"]
                        }
                    ]
                }
                nova_messages.append(nova_msg)
            
            # Prepare request body for Nova Pro
            request_body = {
                "messages": nova_messages,
                "inferenceConfig": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            
            # Call Bedrock
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType="application/json"
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Nova Pro response format
            if 'output' in response_body and 'message' in response_body['output']:
                message = response_body['output']['message']
                if 'content' in message and len(message['content']) > 0:
                    return message['content'][0]['text']
            
            logger.error(f"Unexpected response format from Nova Pro: {response_body}")
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
    
    def list_available_inference_profiles(self) -> List[Dict[str, Any]]:
        """List all available inference profiles"""
        try:
            response = self.bedrock_client.list_inference_profiles()
            profiles = []
            
            for profile in response.get('inferenceProfileSummaries', []):
                profiles.append({
                    'id': profile.get('inferenceProfileId'),
                    'name': profile.get('inferenceProfileName'),
                    'description': profile.get('description', ''),
                    'models': profile.get('models', [])
                })
            
            return profiles
            
        except Exception as e:
            logger.error(f"Error listing inference profiles: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test the connection to Nova Pro model"""
        try:
            test_response = self.generate_text("Hello, this is a test message.", max_tokens=50)
            return not test_response.startswith("Error:")
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
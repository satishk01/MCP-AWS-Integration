import streamlit as st
import boto3
import json
import os
from typing import Dict, Any, List
import requests
import subprocess
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="AWS MCP Research & Documentation Assistant",
    page_icon="🔬",
    layout="wide"
)

class MCPServerManager:
    """Manages MCP server interactions"""
    
    def __init__(self):
        from utils.mcp_client import SyncMCPClient
        from config import Config
        
        self.mcp_client = SyncMCPClient()
        self.git_repo_server = "git-repo-research"
        self.code_doc_server = "code-doc-gen"
        
        # Initialize MCP servers
        self._initialize_servers()
    
    def _initialize_servers(self):
        """Initialize MCP server connections"""
        try:
            # Connect to Git Repo Research server
            git_env = {
                "AWS_PROFILE": os.getenv('AWS_PROFILE', 'default'),
                "AWS_REGION": os.getenv('AWS_REGION', 'us-east-1'),
                "FASTMCP_LOG_LEVEL": "ERROR",
                "GITHUB_TOKEN": os.getenv('GITHUB_TOKEN', '')
            }
            
            self.mcp_client.connect_server(
                self.git_repo_server,
                "uvx",
                ["awslabs.git-repo-research-mcp-server@latest"],
                git_env
            )
            
            # Connect to Code Doc Gen server
            doc_env = {
                "FASTMCP_LOG_LEVEL": "ERROR"
            }
            
            self.mcp_client.connect_server(
                self.code_doc_server,
                "uvx", 
                ["awslabs.code-doc-gen-mcp-server@latest"],
                doc_env
            )
            
        except Exception as e:
            st.error(f"Failed to initialize MCP servers: {e}")
    
    def call_git_repo_research(self, repo_url: str, query: str) -> Dict[str, Any]:
        """Call the git repo research MCP server"""
        try:
            # Call the actual MCP server with the GitHub repository URL
            arguments = {
                "repository_url": repo_url,
                "query": query,
                "analysis_type": "comprehensive"
            }
            
            result = self.mcp_client.call_tool(
                self.git_repo_server,
                "analyze_repository",
                arguments
            )
            
            if "error" in result:
                return {"status": "error", "message": result["error"]}
            else:
                return {"status": "success", "analysis": result}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def call_code_doc_gen(self, code_content: str, doc_type: str = "api") -> Dict[str, Any]:
        """Call the code documentation generation MCP server"""
        try:
            # Call the actual MCP server
            arguments = {
                "code": code_content,
                "documentation_type": doc_type,
                "include_examples": True
            }
            
            result = self.mcp_client.call_tool(
                self.code_doc_server,
                "generate_documentation",
                arguments
            )
            
            if "error" in result:
                return {"status": "error", "message": result["error"]}
            else:
                return {"status": "success", "documentation": result}
                
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_available_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools for a server"""
        try:
            return self.mcp_client.list_tools(server_name)
        except Exception as e:
            st.error(f"Error listing tools for {server_name}: {e}")
            return []

class NovaProIntegration:
    """Handles Amazon Nova Pro model integration using Strands SDK"""
    
    def __init__(self, region_name: str = "us-east-1"):
        from utils.bedrock_client import BedrockClient
        from config import Config
        
        # Use region from config or parameter
        region = os.getenv('AWS_REGION', region_name)
        profile = os.getenv('AWS_PROFILE', 'default')
        
        self.bedrock_client = BedrockClient(region_name=region, profile_name=profile)
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Nova Pro model"""
        return self.bedrock_client.generate_text(prompt, context)

def main():
    st.title("🔬 AWS MCP Research & Documentation Assistant")
    st.markdown("Powered by Amazon Nova Pro and AWS Lab MCP Servers")
    
    # Show configuration status at the top
    with st.expander("📋 Configuration Status", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**AWS Settings**")
            if os.getenv('AWS_REGION'):
                st.success(f"Region: {os.getenv('AWS_REGION')}")
            else:
                st.error("Region: Not set")
                
            if os.getenv('AWS_PROFILE'):
                st.success(f"Profile: {os.getenv('AWS_PROFILE')}")
            else:
                st.error("Profile: Not set")
        
        with col2:
            st.markdown("**GitHub Settings**")
            if os.getenv('GITHUB_TOKEN'):
                st.success("Token: ✅ Configured")
            else:
                st.error("Token: ❌ Missing")
        
        with col3:
            st.markdown("**Required Inputs**")
            st.info("Repository Research:")
            st.write("• GitHub Repository URL")
            st.write("• Research Query")
            st.info("Code Documentation:")
            st.write("• Code to document")
            st.write("• Documentation type")
    
    # Initialize components
    mcp_manager = MCPServerManager()
    nova_integration = NovaProIntegration()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Load current environment variables
        current_aws_region = os.getenv('AWS_REGION', 'us-east-1')
        current_aws_profile = os.getenv('AWS_PROFILE', 'default')
        current_github_token = os.getenv('GITHUB_TOKEN', '')
        
        # AWS Configuration
        st.subheader("AWS Settings")
        
        # Show current values and allow override
        if current_aws_region:
            st.success(f"✅ AWS Region: {current_aws_region}")
            if st.checkbox("Override AWS Region"):
                aws_region = st.text_input("New AWS Region", value=current_aws_region)
                os.environ['AWS_REGION'] = aws_region
        else:
            aws_region = st.text_input("AWS Region", value="us-east-1")
            os.environ['AWS_REGION'] = aws_region
        
        if current_aws_profile:
            st.success(f"✅ AWS Profile: {current_aws_profile}")
            if st.checkbox("Override AWS Profile"):
                aws_profile = st.text_input("New AWS Profile", value=current_aws_profile)
                os.environ['AWS_PROFILE'] = aws_profile
        else:
            aws_profile = st.text_input("AWS Profile", value="default")
            os.environ['AWS_PROFILE'] = aws_profile
        
        # GitHub Configuration
        st.subheader("GitHub Settings")
        
        if current_github_token:
            st.success("✅ GitHub token loaded from environment")
            if st.checkbox("Override GitHub Token"):
                github_token = st.text_input("New GitHub Token", type="password")
                if github_token:
                    os.environ['GITHUB_TOKEN'] = github_token
        else:
            github_token = st.text_input("GitHub Token", type="password", help="Required for repository analysis")
            if github_token:
                os.environ['GITHUB_TOKEN'] = github_token
            else:
                st.warning("⚠️ GitHub token required for repo analysis")
        
        st.markdown("---")
        st.markdown("**Service Status**")
        
        # Test Nova Pro connection
        if st.button("Test Nova Pro Connection"):
            with st.spinner("Testing connection..."):
                if nova_integration.bedrock_client.test_connection():
                    st.success("✅ Nova Pro Connected")
                    st.info(f"Using inference profile: {nova_integration.bedrock_client.model_id}")
                else:
                    st.error("❌ Nova Pro Connection Failed")
        
        # Debug access issues
        if st.button("Debug Access Issues"):
            with st.spinner("Gathering debug information..."):
                debug_info = nova_integration.bedrock_client.debug_access()
                st.json(debug_info)
        
        # MCP Server Status
        if st.button("Check MCP Servers"):
            with st.spinner("Checking MCP server status..."):
                git_tools = mcp_manager.list_available_tools(mcp_manager.git_repo_server)
                doc_tools = mcp_manager.list_available_tools(mcp_manager.code_doc_server)
                
                if git_tools:
                    st.success("✅ Git Repo Research Server")
                    with st.expander("Available Git Tools"):
                        for tool in git_tools:
                            st.write(f"- {tool.get('name', 'Unknown')}")
                else:
                    st.warning("⚠️ Git Repo Research Server - No tools found")
                
                if doc_tools:
                    st.success("✅ Code Doc Gen Server")
                    with st.expander("Available Doc Tools"):
                        for tool in doc_tools:
                            st.write(f"- {tool.get('name', 'Unknown')}")
                else:
                    st.warning("⚠️ Code Doc Gen Server - No tools found")
    
    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Repository Research", "📝 Code Documentation", "🤖 AI Assistant"])
    
    with tab1:
        st.header("Repository Research")
        st.markdown("Analyze GitHub repositories using the Git Repo Research MCP server")
        st.info("📌 This tool analyzes the GitHub repository you specify, not your local files. Make sure to provide a valid GitHub repository URL.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            repo_url = st.text_input(
                "Repository URL",
                placeholder="https://github.com/owner/repo",
                help="Enter the GitHub repository URL to analyze"
            )
            
            research_query = st.text_area(
                "Research Query",
                placeholder="What would you like to research about this repository?",
                help="Describe what you want to learn about the repository"
            )
        
        with col2:
            st.markdown("**Sample Queries:**")
            sample_queries = [
                "Analyze the architecture patterns",
                "Find security vulnerabilities", 
                "Identify performance bottlenecks",
                "Review code quality metrics",
                "Map dependencies and relationships"
            ]
            
            for query in sample_queries:
                if st.button(query, key=f"sample_{query}"):
                    research_query = query
                    st.rerun()
        
        if st.button("🔍 Analyze Repository", type="primary"):
            if repo_url and research_query:
                # Validate GitHub URL
                if not repo_url.startswith("https://github.com/"):
                    st.error("Please provide a valid GitHub repository URL (https://github.com/owner/repo)")
                elif not os.getenv('GITHUB_TOKEN'):
                    st.error("Please configure your GitHub token in the sidebar")
                else:
                    with st.spinner(f"Analyzing GitHub repository: {repo_url}..."):
                        # Call MCP server
                        result = mcp_manager.call_git_repo_research(repo_url, research_query)
                    
                    if result["status"] == "success":
                        st.success("Repository analysis completed!")
                        
                        # Display the analysis results
                        analysis_data = result.get("analysis", {})
                        
                        # Generate AI insights using Nova Pro
                        context = f"GitHub repository: {repo_url}\nAnalysis results: {json.dumps(analysis_data, indent=2)}"
                        ai_prompt = f"Based on the GitHub repository analysis for '{repo_url}', provide detailed insights about: {research_query}. Focus only on the repository content, not local files."
                        
                        ai_response = nova_integration.generate_response(ai_prompt, context)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Repository Analysis Results")
                            if analysis_data:
                                st.json(analysis_data)
                            else:
                                st.info("Analysis completed - check AI insights for details")
                        
                        with col2:
                            st.subheader("AI Insights (Nova Pro)")
                            st.markdown(ai_response)
                    else:
                        st.error(f"Repository analysis failed: {result.get('message', 'Unknown error')}")
                        st.info("Make sure you have provided a valid GitHub repository URL and your GitHub token is configured.")
            else:
                st.warning("Please provide both repository URL and research query")
    
    with tab2:
        st.header("Code Documentation Generation")
        st.markdown("Generate documentation using the Code Doc Gen MCP server")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            code_input = st.text_area(
                "Code to Document",
                height=300,
                placeholder="Paste your code here...",
                help="Enter the code you want to generate documentation for"
            )
            
            doc_type = st.selectbox(
                "Documentation Type",
                ["api", "readme", "inline", "tutorial"],
                help="Select the type of documentation to generate"
            )
        
        with col2:
            st.markdown("**Sample Code:**")
            if st.button("Load Python Function Sample"):
                sample_code = '''def calculate_fibonacci(n):
    """Calculate fibonacci number"""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class DataProcessor:
    def __init__(self, data_source):
        self.data_source = data_source
    
    def process(self):
        # Process data logic here
        pass'''
                code_input = sample_code
                st.rerun()
        
        if st.button("📝 Generate Documentation", type="primary"):
            if code_input:
                with st.spinner("Generating documentation..."):
                    # Call MCP server
                    result = mcp_manager.call_code_doc_gen(code_input, doc_type)
                    
                    if result["status"] == "success":
                        st.success("Documentation generated!")
                        
                        # Display the documentation results
                        doc_data = result.get("documentation", {})
                        
                        # Enhance with Nova Pro
                        context = f"Generated documentation: {json.dumps(doc_data, indent=2)}\n\nOriginal code:\n{code_input}"
                        ai_prompt = f"Enhance this {doc_type} documentation with detailed explanations, usage examples, and best practices. Make it comprehensive and developer-friendly."
                        
                        ai_response = nova_integration.generate_response(ai_prompt, context)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("MCP Generated Documentation")
                            if doc_data:
                                st.json(doc_data)
                            else:
                                st.info("Documentation generated - check AI insights for details")
                        
                        with col2:
                            st.subheader("Enhanced Documentation (Nova Pro)")
                            st.markdown(ai_response)
                    else:
                        st.error(f"Documentation generation failed: {result.get('message', 'Unknown error')}")
            else:
                st.warning("Please provide code to document")
    
    with tab3:
        st.header("AI Assistant")
        st.markdown("Chat with Amazon Nova Pro about your research and documentation")
        
        # Chat interface
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me anything about your code or repositories..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = nova_integration.generate_response(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Sample prompts
        st.markdown("**Sample Prompts:**")
        sample_prompts = [
            "How can I improve the security of my Python application?",
            "What are the best practices for API documentation?",
            "Explain the repository analysis results in simple terms",
            "How do I optimize this code for better performance?",
            "What testing strategies should I implement?"
        ]
        
        cols = st.columns(2)
        for i, prompt in enumerate(sample_prompts):
            with cols[i % 2]:
                if st.button(prompt, key=f"prompt_{i}"):
                    # Add to chat
                    st.session_state.messages.append({"role": "user", "content": prompt})
                    response = nova_integration.generate_response(prompt)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

if __name__ == "__main__":
    main()
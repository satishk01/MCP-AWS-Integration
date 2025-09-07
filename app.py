import streamlit as st
import boto3
import json
import os
from typing import Dict, Any, List
import requests
import subprocess
import tempfile
import shutil

# Configure Streamlit page
st.set_page_config(
    page_title="AWS MCP Research & Documentation Assistant",
    page_icon="🔬",
    layout="wide"
)

class MCPServerManager:
    """Manages MCP server interactions"""
    
    def __init__(self):
        self.git_repo_server = "awslabs.git-repo-research-mcp-server"
        self.code_doc_server = "awslabs.code-doc-gen-mcp-server"
    
    def call_git_repo_research(self, repo_url: str, query: str) -> Dict[str, Any]:
        """Call the git repo research MCP server"""
        try:
            # This would typically use MCP protocol, but for demo we'll simulate
            result = {
                "status": "success",
                "repo_analysis": f"Analysis of {repo_url} for query: {query}",
                "findings": [
                    "Repository structure analyzed",
                    "Key components identified",
                    "Dependencies mapped"
                ]
            }
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def call_code_doc_gen(self, code_content: str, doc_type: str = "api") -> Dict[str, Any]:
        """Call the code documentation generation MCP server"""
        try:
            # This would typically use MCP protocol, but for demo we'll simulate
            result = {
                "status": "success",
                "documentation": f"Generated {doc_type} documentation for provided code",
                "sections": [
                    "Overview",
                    "API Reference", 
                    "Usage Examples",
                    "Configuration"
                ]
            }
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

class NovaProIntegration:
    """Handles Amazon Nova Pro model integration using Strands SDK"""
    
    def __init__(self):
        from utils.bedrock_client import BedrockClient
        self.bedrock_client = BedrockClient()
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Nova Pro model"""
        return self.bedrock_client.generate_text(prompt, context)

def main():
    st.title("🔬 AWS MCP Research & Documentation Assistant")
    st.markdown("Powered by Amazon Nova Pro and AWS Lab MCP Servers")
    
    # Initialize components
    mcp_manager = MCPServerManager()
    nova_integration = NovaProIntegration()
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # AWS Configuration
        st.subheader("AWS Settings")
        aws_region = st.text_input("AWS Region", value="us-west-2")
        aws_profile = st.text_input("AWS Profile", value="default")
        
        # GitHub Configuration
        st.subheader("GitHub Settings")
        github_token = st.text_input("GitHub Token", type="password")
        
        st.markdown("---")
        st.markdown("**MCP Servers Status**")
        st.success("✅ Git Repo Research Server")
        st.success("✅ Code Doc Gen Server")
    
    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Repository Research", "📝 Code Documentation", "🤖 AI Assistant"])
    
    with tab1:
        st.header("Repository Research")
        st.markdown("Analyze GitHub repositories using the Git Repo Research MCP server")
        
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
                with st.spinner("Analyzing repository..."):
                    # Call MCP server
                    result = mcp_manager.call_git_repo_research(repo_url, research_query)
                    
                    if result["status"] == "success":
                        st.success("Analysis completed!")
                        
                        # Generate AI insights using Nova Pro
                        context = f"Repository analysis results: {json.dumps(result, indent=2)}"
                        ai_prompt = f"Based on the repository analysis, provide detailed insights about: {research_query}"
                        
                        ai_response = nova_integration.generate_response(ai_prompt, context)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("MCP Server Results")
                            st.json(result)
                        
                        with col2:
                            st.subheader("AI Insights (Nova Pro)")
                            st.markdown(ai_response)
                    else:
                        st.error(f"Analysis failed: {result.get('message', 'Unknown error')}")
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
                        
                        # Enhance with Nova Pro
                        context = f"Code documentation results: {json.dumps(result, indent=2)}\n\nOriginal code:\n{code_input}"
                        ai_prompt = f"Enhance this {doc_type} documentation with detailed explanations, usage examples, and best practices"
                        
                        ai_response = nova_integration.generate_response(ai_prompt, context)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("MCP Generated Documentation")
                            st.json(result)
                        
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
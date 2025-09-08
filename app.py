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
    """Manages MCP server interactions with selective connection"""
    
    def __init__(self):
        from utils.mcp_client import SyncMCPClient
        from config import Config
        
        self.mcp_client = SyncMCPClient()
        
        # Available MCP servers configuration - using correct server IDs
        self.available_servers = {
            "git-repo-research": {
                "name": "Git Repository Research",
                "server_id": "git-repo-research",  # Simplified server ID
                "package": "awslabs.git-repo-research-mcp-server@latest",
                "description": "Analyze GitHub repositories, search code, and extract insights",
                "env": {
                    "AWS_PROFILE": os.getenv('AWS_PROFILE', 'default'),
                    "AWS_REGION": os.getenv('AWS_REGION', 'us-east-1'),
                    "FASTMCP_LOG_LEVEL": "ERROR",
                    "GITHUB_TOKEN": os.getenv('GITHUB_TOKEN', '')
                }
            },
            "aws-docs": {
                "name": "AWS Documentation",
                "server_id": "aws-docs",  # Simplified server ID
                "package": "awslabs.aws-documentation-mcp-server@latest",
                "description": "Search and retrieve AWS documentation",
                "env": {
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
            }
        }
        
        # Track connected servers
        self.connected_servers = {}
        self.server_tools = {}
    
    def connect_server(self, server_key: str) -> bool:
        """Connect to a specific MCP server"""
        if server_key not in self.available_servers:
            return False
            
        server_config = self.available_servers[server_key]
        
        try:
            success = self.mcp_client.connect_server(
                server_config["server_id"],
                "uvx",
                [server_config["package"]],
                server_config["env"]
            )
            
            if success:
                self.connected_servers[server_key] = server_config
                # Get available tools for this server
                tools = self.mcp_client.list_tools(server_config["server_id"])
                self.server_tools[server_key] = tools
                return True
            return False
            
        except Exception as e:
            st.error(f"Failed to connect to {server_config['name']}: {e}")
            return False
    
    def disconnect_server(self, server_key: str):
        """Disconnect from a specific MCP server"""
        if server_key in self.connected_servers:
            server_config = self.connected_servers[server_key]
            self.mcp_client.disconnect_server(server_config["server_id"])
            del self.connected_servers[server_key]
            if server_key in self.server_tools:
                del self.server_tools[server_key]
    
    def is_server_connected(self, server_key: str) -> bool:
        """Check if a server is connected"""
        return server_key in self.connected_servers
    
    def get_server_tools(self, server_key: str) -> List[Dict[str, Any]]:
        """Get available tools for a server"""
        return self.server_tools.get(server_key, [])
    
    def call_server_tool(self, server_key: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a specific server with better error handling"""
        if server_key not in self.connected_servers:
            return {"status": "error", "message": f"Server {server_key} not connected"}
        
        server_config = self.connected_servers[server_key]
        
        try:
            # Clean up arguments - remove empty values
            clean_args = {k: v for k, v in arguments.items() if v is not None and v != ""}
            
            result = self.mcp_client.call_tool(
                server_config["server_id"],
                tool_name,
                clean_args
            )
            
            if "error" in result:
                # Provide more detailed error information
                error_info = result["error"]
                if isinstance(error_info, dict):
                    error_msg = f"Code: {error_info.get('code', 'Unknown')}, Message: {error_info.get('message', 'Unknown error')}"
                    if error_info.get('data'):
                        error_msg += f", Data: {error_info.get('data')}"
                else:
                    error_msg = str(error_info)
                
                return {
                    "status": "error", 
                    "message": error_msg,
                    "debug_info": {
                        "tool_name": tool_name,
                        "arguments_sent": clean_args,
                        "server_id": server_config["server_id"],
                        "raw_error": result["error"]
                    }
                }
            else:
                return {"status": "success", "result": result}
                
        except Exception as e:
            return {
                "status": "error", 
                "message": f"Failed to call tool: {str(e)}",
                "debug_info": {
                    "tool_name": tool_name,
                    "arguments_sent": arguments,
                    "server_id": server_config["server_id"]
                }
            }
    

    


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
    
    # Initialize components
    if 'mcp_manager' not in st.session_state:
        st.session_state.mcp_manager = MCPServerManager()
    if 'nova_integration' not in st.session_state:
        st.session_state.nova_integration = NovaProIntegration()
    
    mcp_manager = st.session_state.mcp_manager
    nova_integration = st.session_state.nova_integration
    
    # Server Selection Interface
    st.header("🔧 MCP Server Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Available MCP Servers")
        
        for server_key, server_info in mcp_manager.available_servers.items():
            with st.container():
                col_info, col_status, col_action = st.columns([3, 1, 1])
                
                with col_info:
                    st.markdown(f"**{server_info['name']}**")
                    st.caption(server_info['description'])
                
                with col_status:
                    if mcp_manager.is_server_connected(server_key):
                        st.success("Connected")
                    else:
                        st.error("Disconnected")
                
                with col_action:
                    if mcp_manager.is_server_connected(server_key):
                        if st.button(f"Disconnect", key=f"disconnect_{server_key}"):
                            mcp_manager.disconnect_server(server_key)
                            st.rerun()
                    else:
                        if st.button(f"Connect", key=f"connect_{server_key}"):
                            with st.spinner(f"Connecting to {server_info['name']}..."):
                                success = mcp_manager.connect_server(server_key)
                                if success:
                                    st.success(f"Connected to {server_info['name']}")
                                else:
                                    st.error(f"Failed to connect to {server_info['name']}")
                            st.rerun()
                
                st.divider()
    
    with col2:
        st.subheader("Connection Status")
        connected_count = len(mcp_manager.connected_servers)
        total_count = len(mcp_manager.available_servers)
        
        st.metric("Connected Servers", f"{connected_count}/{total_count}")
        
        if connected_count > 0:
            st.success("Ready to use MCP tools")
        else:
            st.warning("No servers connected")
    
    # Show available tools for connected servers
    if mcp_manager.connected_servers:
        st.header("🛠️ Available Tools")
        
        for server_key in mcp_manager.connected_servers:
            server_info = mcp_manager.available_servers[server_key]
            tools = mcp_manager.get_server_tools(server_key)
            
            with st.expander(f"{server_info['name']} - {len(tools)} tools"):
                if tools:
                    for tool in tools:
                        st.markdown(f"**{tool.get('name', 'Unknown')}**")
                        if 'description' in tool:
                            st.caption(tool['description'])
                        if 'inputSchema' in tool:
                            st.json(tool['inputSchema'])
                        st.divider()
                else:
                    st.info("No tools available or failed to retrieve tools")
    
    # Quick Test Section
    if mcp_manager.connected_servers:
        with st.expander("🧪 Quick Test Tools", expanded=False):
            st.markdown("Test common MCP operations with simplified interfaces")
            
            # Git Repository Test
            if "git-repo-research" in mcp_manager.connected_servers:
                st.subheader("Git Repository Quick Test")
                
                col1, col2 = st.columns(2)
                with col1:
                    test_repo = st.text_input("Repository URL:", 
                                            value="https://github.com/octocat/Hello-World",
                                            key="test_repo")
                with col2:
                    test_query = st.text_input("Search Query:", 
                                             value="README",
                                             key="test_query")
                
                if st.button("Test Git Search", key="test_git"):
                    # Try different parameter combinations
                    param_combinations = [
                        {"query": test_query, "repository_url": test_repo},
                        {"search_query": test_query, "repo_url": test_repo},
                        {"q": test_query, "url": test_repo},
                        {"query": test_query, "url": test_repo},
                        {"repository": test_repo, "query": test_query}
                    ]
                    
                    tools = mcp_manager.get_server_tools("git-repo-research")
                    if tools:
                        tool_names = [tool.get('name', '') for tool in tools]
                        st.write(f"Available tools: {', '.join(tool_names)}")
                        
                        # Try first available tool with different parameter combinations
                        if tool_names:
                            first_tool = tool_names[0]
                            st.write(f"Testing tool: {first_tool}")
                            
                            for i, params in enumerate(param_combinations):
                                with st.spinner(f"Trying parameter combination {i+1}..."):
                                    result = mcp_manager.call_server_tool("git-repo-research", first_tool, params)
                                    
                                    if result['status'] == 'success':
                                        st.success(f"✅ Success with parameters: {params}")
                                        st.json(result['result'])
                                        break
                                    else:
                                        st.warning(f"❌ Failed with parameters: {params}")
                                        st.caption(f"Error: {result['message']}")
                    else:
                        st.error("No tools available for git-repo-research server")
            
            # AWS Docs Test
            if "aws-docs" in mcp_manager.connected_servers:
                st.subheader("AWS Documentation Quick Test")
                
                test_aws_query = st.text_input("AWS Documentation Query:", 
                                             value="EC2 instances",
                                             key="test_aws_query")
                
                if st.button("Test AWS Docs Search", key="test_aws"):
                    tools = mcp_manager.get_server_tools("aws-docs")
                    if tools:
                        tool_names = [tool.get('name', '') for tool in tools]
                        st.write(f"Available tools: {', '.join(tool_names)}")
                        
                        if tool_names:
                            first_tool = tool_names[0]
                            params = {"query": test_aws_query}
                            
                            result = mcp_manager.call_server_tool("aws-docs", first_tool, params)
                            
                            if result['status'] == 'success':
                                st.success("✅ AWS Docs search successful!")
                                st.json(result['result'])
                            else:
                                st.error(f"❌ AWS Docs search failed: {result['message']}")
                    else:
                        st.error("No tools available for aws-docs server")
    
    # Dynamic interface based on connected servers
    if mcp_manager.connected_servers:
        st.header("🚀 MCP Tools Interface")
        
        # Create tabs based on connected servers
        tab_names = []
        tab_keys = []
        
        for server_key in mcp_manager.connected_servers:
            server_info = mcp_manager.available_servers[server_key]
            tab_names.append(f"{server_info['name']}")
            tab_keys.append(server_key)
        
        # Add AI Assistant tab
        tab_names.append("🤖 AI Assistant")
        tab_keys.append("ai_assistant")
        
        tabs = st.tabs(tab_names)
        
        for i, (tab, server_key) in enumerate(zip(tabs, tab_keys)):
            with tab:
                if server_key == "ai_assistant":
                    # AI Assistant tab
                    st.header("AI Assistant (Nova Pro)")
                    st.markdown("Chat with Amazon Nova Pro for general assistance")
                    
                    user_input = st.text_area("Ask Nova Pro anything:", height=100)
                    
                    if st.button("Send to Nova Pro"):
                        if user_input:
                            with st.spinner("Generating response..."):
                                response = nova_integration.generate_response(user_input)
                                st.markdown("**Nova Pro Response:**")
                                st.markdown(response)
                        else:
                            st.warning("Please enter a question")
                
                elif server_key in mcp_manager.connected_servers:
                    # MCP Server specific interface
                    server_info = mcp_manager.available_servers[server_key]
                    tools = mcp_manager.get_server_tools(server_key)
                    
                    st.header(f"{server_info['name']}")
                    st.markdown(server_info['description'])
                    
                    if tools:
                        # Tool selection
                        tool_names = [tool.get('name', 'Unknown') for tool in tools]
                        selected_tool = st.selectbox("Select Tool:", tool_names, key=f"tool_{server_key}")
                        
                        if selected_tool:
                            # Find the selected tool
                            tool_info = next((tool for tool in tools if tool.get('name') == selected_tool), None)
                            
                            if tool_info:
                                st.markdown(f"**Tool:** {selected_tool}")
                                if 'description' in tool_info:
                                    st.markdown(f"**Description:** {tool_info['description']}")
                                
                                # Dynamic parameter input based on tool schema
                                st.subheader("Parameters")
                                
                                parameters = {}
                                if 'inputSchema' in tool_info and 'properties' in tool_info['inputSchema']:
                                    for param_name, param_info in tool_info['inputSchema']['properties'].items():
                                        param_type = param_info.get('type', 'string')
                                        param_desc = param_info.get('description', '')
                                        
                                        if param_type == 'string':
                                            if 'url' in param_name.lower() or 'repository' in param_name.lower():
                                                parameters[param_name] = st.text_input(
                                                    f"{param_name}:", 
                                                    help=param_desc,
                                                    placeholder="https://github.com/user/repo",
                                                    key=f"{server_key}_{selected_tool}_{param_name}"
                                                )
                                            else:
                                                parameters[param_name] = st.text_area(
                                                    f"{param_name}:", 
                                                    help=param_desc,
                                                    key=f"{server_key}_{selected_tool}_{param_name}"
                                                )
                                        elif param_type == 'boolean':
                                            parameters[param_name] = st.checkbox(
                                                f"{param_name}", 
                                                help=param_desc,
                                                key=f"{server_key}_{selected_tool}_{param_name}"
                                            )
                                        elif param_type == 'number' or param_type == 'integer':
                                            parameters[param_name] = st.number_input(
                                                f"{param_name}:", 
                                                help=param_desc,
                                                key=f"{server_key}_{selected_tool}_{param_name}"
                                            )
                                else:
                                    # Fallback for tools without schema
                                    st.info("No parameter schema available. Using generic inputs:")
                                    parameters['input'] = st.text_area("Input:", key=f"{server_key}_{selected_tool}_input")
                                
                                # Execute tool
                                if st.button(f"Execute {selected_tool}", key=f"execute_{server_key}_{selected_tool}"):
                                    # Filter out empty parameters
                                    filtered_params = {k: v for k, v in parameters.items() if v}
                                    
                                    if filtered_params:
                                        with st.spinner(f"Executing {selected_tool}..."):
                                            result = mcp_manager.call_server_tool(server_key, selected_tool, filtered_params)
                                            
                                            if result['status'] == 'success':
                                                st.success("Tool executed successfully!")
                                                
                                                # Display results
                                                st.subheader("Results")
                                                st.json(result['result'])
                                                
                                                # Enhanced AI analysis
                                                if st.button("Enhance with Nova Pro", key=f"enhance_{server_key}_{selected_tool}"):
                                                    context = f"MCP Tool: {selected_tool}\nParameters: {filtered_params}\nResults: {json.dumps(result['result'], indent=2)}"
                                                    ai_prompt = f"Analyze and explain these results from the {selected_tool} tool. Provide insights, summaries, and actionable recommendations."
                                                    
                                                    with st.spinner("Generating AI insights..."):
                                                        ai_response = nova_integration.generate_response(ai_prompt, context)
                                                        st.subheader("AI Insights (Nova Pro)")
                                                        st.markdown(ai_response)
                                            else:
                                                st.error(f"Tool execution failed: {result['message']}")
                                                
                                                # Show debug information for troubleshooting
                                                if 'debug_info' in result:
                                                    with st.expander("🔍 Debug Information"):
                                                        st.markdown("**Tool Details:**")
                                                        st.json(result['debug_info'])
                                                        
                                                        st.markdown("**Troubleshooting Tips:**")
                                                        if "Invalid request parameters" in result['message']:
                                                            st.markdown("- Check if parameter names match the tool's expected schema")
                                                            st.markdown("- Verify parameter types (string, number, boolean)")
                                                            st.markdown("- Ensure required parameters are provided")
                                                        elif "Method not found" in result['message']:
                                                            st.markdown("- The tool name might be incorrect")
                                                            st.markdown("- Check available tools list for correct names")
                                                        
                                                        # Show available tools for reference
                                                        available_tools = mcp_manager.get_server_tools(server_key)
                                                        if available_tools:
                                                            st.markdown("**Available Tools on this server:**")
                                                            for tool in available_tools:
                                                                st.text(f"- {tool.get('name', 'Unknown')}")
                                                
                                                # Suggest trying with different parameters
                                                st.info("💡 Try adjusting the parameters or check the tool schema above")
                                    else:
                                        st.warning("Please provide at least one parameter")
                    else:
                        st.warning("No tools available for this server")
    else:
        st.info("👆 Connect to one or more MCP servers above to start using tools")
    
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
        st.markdown("**MCP Server Status**")
        
        # Check uvx availability with detailed info and EC2 specific paths
        uvx_available = shutil.which('uvx') is not None
        uvx_path = shutil.which('uvx')
        
        # Check EC2 specific paths if not found in PATH
        if not uvx_available:
            ec2_paths = [
                "/home/ec2-user/.cargo/bin/uvx",
                os.path.expanduser("~/.cargo/bin/uvx"),
                "/root/.cargo/bin/uvx"
            ]
            for path in ec2_paths:
                if os.path.exists(path) and os.access(path, os.X_OK):
                    uvx_available = True
                    uvx_path = path
                    # Add to PATH for this session
                    bin_dir = os.path.dirname(path)
                    current_path = os.environ.get('PATH', '')
                    if bin_dir not in current_path:
                        os.environ['PATH'] = f"{bin_dir}:{current_path}"
                        st.info(f"Added {bin_dir} to PATH")
                    break
        
        # Get detailed uvx info
        uvx_info = {"available": uvx_available, "path": uvx_path, "version": None}
        
        if uvx_available and uvx_path:
            try:
                result = subprocess.run([uvx_path, '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    uvx_info["version"] = result.stdout.strip()
            except Exception as e:
                st.warning(f"uvx found but version check failed: {e}")
        
        if uvx_available:
            st.success(f"✅ uvx is installed")
            if uvx_info["version"]:
                st.info(f"Version: {uvx_info['version']}")
            if uvx_info["path"]:
                st.info(f"Path: {uvx_info['path']}")
            
            # MCP Client is ready since uvx is available
            st.success("✅ MCP Client ready")
            
            if st.button("Check MCP Servers"):
                with st.spinner("Checking MCP server status..."):
                    if mcp_manager.git_server_available:
                        st.success("✅ Git Repo Research Server")
                    else:
                        st.error("❌ Git Repo Research Server - Connection failed")
                    
                    if mcp_manager.doc_server_available:
                        st.success("✅ Code Doc Gen Server")
                    else:
                        st.error("❌ Code Doc Gen Server - Connection failed")
        else:
            st.error("❌ MCP servers not available - check uvx installation and server configuration")
        
        # Debug information
        if st.button("🔍 Debug uvx Detection"):
            st.markdown("**Debug Information:**")
            
            # Show PATH
            current_path = os.environ.get('PATH', '')
            st.text(f"PATH: {current_path}")
            
            # Check common uvx locations
            common_paths = [
                os.path.expanduser("~/.cargo/bin/uvx"),
                os.path.expanduser("~/.local/bin/uvx"),
                "/usr/local/bin/uvx",
                "/home/ec2-user/.cargo/bin/uvx"
            ]
            
            st.markdown("**Checking common uvx locations:**")
            for path in common_paths:
                exists = os.path.exists(path)
                executable = os.access(path, os.X_OK) if exists else False
                st.text(f"{path}: {'✅' if exists else '❌'} exists, {'✅' if executable else '❌'} executable")
            
            # Test uvx command
            st.markdown("**Testing uvx command:**")
            try:
                result = subprocess.run(['uvx', '--version'], capture_output=True, text=True, timeout=5)
                st.text(f"Return code: {result.returncode}")
                st.text(f"Stdout: {result.stdout}")
                st.text(f"Stderr: {result.stderr}")
            except Exception as e:
                st.text(f"Error running uvx: {e}")
            
            # Show MCP client status
            st.markdown("**MCP Client Status:**")
            st.text("MCP Client: Ready (uvx available)")
            
            # List available MCP tools
            st.markdown("**Available MCP Tools:**")
            if mcp_manager.git_server_available:
                git_tools = mcp_manager.list_available_tools(mcp_manager.git_repo_server)
                st.markdown(f"Git Repo Server Tools ({len(git_tools)}):")
                for tool in git_tools:
                    st.text(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            else:
                st.text("Git Repo Server: Not connected")
                
            if mcp_manager.doc_server_available:
                doc_tools = mcp_manager.list_available_tools(mcp_manager.code_doc_server)
                st.markdown(f"Code Doc Server Tools ({len(doc_tools)}):")
                for tool in doc_tools:
                    st.text(f"  - {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')}")
            else:
                st.text("Code Doc Server: Not connected")
    
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
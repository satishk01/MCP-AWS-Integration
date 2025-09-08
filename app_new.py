import streamlit as st
import boto3
import json
import os
from typing import Dict, Any, List
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Streamlit page
st.set_page_config(
    page_title="AWS MCP Server Tool Interface",
    page_icon="🔧",
    layout="wide"
)

class MCPServerManager:
    """Simple MCP server manager with direct tool calls"""
    
    def __init__(self):
        from utils.mcp_client import SyncMCPClient
        
        self.mcp_client = SyncMCPClient()
        self.connected_servers = {}
        
        # Available servers with their exact configurations
        self.server_configs = {
            "git-repo": {
                "name": "Git Repository Research",
                "server_id": "git-repo-research",
                "package": "awslabs.git-repo-research-mcp-server@latest",
                "env": {
                    "AWS_PROFILE": os.getenv('AWS_PROFILE', 'default'),
                    "AWS_REGION": os.getenv('AWS_REGION', 'us-east-1'),
                    "FASTMCP_LOG_LEVEL": "ERROR",
                    "GITHUB_TOKEN": os.getenv('GITHUB_TOKEN', '')
                }
            },
            "aws-docs": {
                "name": "AWS Documentation",
                "server_id": "aws-docs",
                "package": "awslabs.aws-documentation-mcp-server@latest", 
                "env": {
                    "FASTMCP_LOG_LEVEL": "ERROR"
                }
            }
        }
    
    def connect_server(self, server_key: str) -> bool:
        """Connect to a specific server"""
        if server_key not in self.server_configs:
            return False
            
        config = self.server_configs[server_key]
        
        try:
            success = self.mcp_client.connect_server(
                config["server_id"],
                "uvx",
                [config["package"]],
                config["env"]
            )
            
            if success:
                self.connected_servers[server_key] = config
                return True
            return False
            
        except Exception as e:
            st.error(f"Failed to connect to {config['name']}: {e}")
            return False
    
    def disconnect_server(self, server_key: str):
        """Disconnect from a server"""
        if server_key in self.connected_servers:
            config = self.connected_servers[server_key]
            self.mcp_client.disconnect_server(config["server_id"])
            del self.connected_servers[server_key]
    
    def list_tools(self, server_key: str) -> List[Dict[str, Any]]:
        """List available tools for a server"""
        if server_key not in self.connected_servers:
            return []
        
        config = self.connected_servers[server_key]
        try:
            return self.mcp_client.list_tools(config["server_id"])
        except Exception as e:
            st.error(f"Error listing tools: {e}")
            return []
    
    def call_tool(self, server_key: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on a server"""
        if server_key not in self.connected_servers:
            return {"error": "Server not connected"}
        
        config = self.connected_servers[server_key]
        
        try:
            result = self.mcp_client.call_tool(
                config["server_id"],
                tool_name,
                arguments
            )
            return result
        except Exception as e:
            return {"error": str(e)}

class NovaProIntegration:
    """Amazon Nova Pro integration"""
    
    def __init__(self):
        from utils.bedrock_client import BedrockClient
        
        region = os.getenv('AWS_REGION', 'us-east-1')
        profile = os.getenv('AWS_PROFILE', 'default')
        
        self.bedrock_client = BedrockClient(region_name=region, profile_name=profile)
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Nova Pro"""
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        return self.bedrock_client.generate_text(full_prompt, context)

def main():
    st.title("🔧 AWS MCP Server Tool Interface")
    st.markdown("Direct interface to AWS MCP servers with tool discovery")
    
    # Initialize components
    if 'mcp_manager' not in st.session_state:
        st.session_state.mcp_manager = MCPServerManager()
    if 'nova_integration' not in st.session_state:
        st.session_state.nova_integration = NovaProIntegration()
    
    mcp_manager = st.session_state.mcp_manager
    nova_integration = st.session_state.nova_integration
    
    # Server Management Section
    st.header("🔌 Server Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Available Servers")
        
        for server_key, config in mcp_manager.server_configs.items():
            with st.container():
                col_name, col_status, col_action = st.columns([2, 1, 1])
                
                with col_name:
                    st.write(f"**{config['name']}**")
                
                with col_status:
                    if server_key in mcp_manager.connected_servers:
                        st.success("Connected")
                    else:
                        st.error("Disconnected")
                
                with col_action:
                    if server_key in mcp_manager.connected_servers:
                        if st.button("Disconnect", key=f"disc_{server_key}"):
                            mcp_manager.disconnect_server(server_key)
                            st.rerun()
                    else:
                        if st.button("Connect", key=f"conn_{server_key}"):
                            with st.spinner(f"Connecting to {config['name']}..."):
                                success = mcp_manager.connect_server(server_key)
                                if success:
                                    st.success(f"Connected!")
                                else:
                                    st.error("Connection failed")
                            st.rerun()
    
    with col2:
        st.subheader("Connection Status")
        connected_count = len(mcp_manager.connected_servers)
        total_count = len(mcp_manager.server_configs)
        st.metric("Connected", f"{connected_count}/{total_count}")
    
    # Tool Interface Section
    if mcp_manager.connected_servers:
        st.header("🛠️ Tool Interface")
        
        # Server selection
        server_options = {key: config['name'] for key, config in mcp_manager.connected_servers.items()}
        selected_server = st.selectbox("Select Server:", list(server_options.keys()), 
                                     format_func=lambda x: server_options[x])
        
        if selected_server:
            # Get tools for selected server
            tools = mcp_manager.list_tools(selected_server)
            
            if tools:
                st.subheader(f"Available Tools ({len(tools)})")
                
                # Tool selection
                tool_options = {tool['name']: tool for tool in tools}
                selected_tool_name = st.selectbox("Select Tool:", list(tool_options.keys()))
                
                if selected_tool_name:
                    selected_tool = tool_options[selected_tool_name]
                    
                    # Display tool information
                    st.markdown(f"**Tool:** {selected_tool_name}")
                    if 'description' in selected_tool:
                        st.markdown(f"**Description:** {selected_tool['description']}")
                    
                    # Show tool schema
                    if 'inputSchema' in selected_tool:
                        with st.expander("Tool Schema"):
                            st.json(selected_tool['inputSchema'])
                    
                    # Parameter input section
                    st.subheader("Parameters")
                    
                    parameters = {}
                    
                    # Check if tool has schema
                    if 'inputSchema' in selected_tool and 'properties' in selected_tool['inputSchema']:
                        schema_props = selected_tool['inputSchema']['properties']
                        required_props = selected_tool['inputSchema'].get('required', [])
                        
                        for prop_name, prop_info in schema_props.items():
                            prop_type = prop_info.get('type', 'string')
                            prop_desc = prop_info.get('description', '')
                            is_required = prop_name in required_props
                            
                            label = f"{prop_name}{'*' if is_required else ''}"
                            
                            if prop_type == 'string':
                                if 'url' in prop_name.lower() or 'repository' in prop_name.lower():
                                    parameters[prop_name] = st.text_input(
                                        label, 
                                        help=prop_desc,
                                        placeholder="https://github.com/user/repo"
                                    )
                                else:
                                    parameters[prop_name] = st.text_area(
                                        label, 
                                        help=prop_desc,
                                        height=100
                                    )
                            elif prop_type == 'boolean':
                                parameters[prop_name] = st.checkbox(label, help=prop_desc)
                            elif prop_type in ['number', 'integer']:
                                parameters[prop_name] = st.number_input(label, help=prop_desc)
                            else:
                                parameters[prop_name] = st.text_input(label, help=prop_desc)
                    else:
                        # Generic parameter input for tools without schema
                        st.info("No schema available. Using generic parameter inputs:")
                        
                        # Common parameters for different tool types
                        if 'search' in selected_tool_name.lower() or 'git' in selected_tool_name.lower():
                            parameters['query'] = st.text_area("Search Query:", height=100)
                            parameters['repository_url'] = st.text_input("Repository URL:", 
                                                                       placeholder="https://github.com/user/repo")
                        elif 'doc' in selected_tool_name.lower():
                            parameters['query'] = st.text_area("Documentation Query:", height=100)
                        else:
                            parameters['input'] = st.text_area("Input:", height=100)
                    
                    # Execute tool
                    if st.button(f"Execute {selected_tool_name}", type="primary"):
                        # Filter out empty parameters
                        filtered_params = {k: v for k, v in parameters.items() if v}
                        
                        if filtered_params:
                            with st.spinner(f"Executing {selected_tool_name}..."):
                                result = mcp_manager.call_tool(selected_server, selected_tool_name, filtered_params)
                                
                                st.subheader("Results")
                                
                                if "error" in result:
                                    st.error(f"Tool execution failed: {result['error']}")
                                    
                                    # Show debug information
                                    with st.expander("Debug Information"):
                                        st.markdown("**Parameters sent:**")
                                        st.json(filtered_params)
                                        st.markdown("**Error details:**")
                                        st.json(result)
                                else:
                                    st.success("Tool executed successfully!")
                                    
                                    # Display raw results
                                    with st.expander("Raw Results"):
                                        st.json(result)
                                    
                                    # Enhanced display
                                    if isinstance(result, dict):
                                        if 'content' in result:
                                            st.markdown("**Content:**")
                                            st.markdown(result['content'])
                                        elif 'text' in result:
                                            st.markdown("**Text:**")
                                            st.markdown(result['text'])
                                        elif 'results' in result:
                                            st.markdown("**Results:**")
                                            st.json(result['results'])
                                        else:
                                            st.json(result)
                                    
                                    # AI Enhancement option
                                    if st.button("Enhance with Nova Pro"):
                                        context = f"MCP Tool: {selected_tool_name}\nParameters: {filtered_params}\nResults: {json.dumps(result, indent=2)}"
                                        ai_prompt = "Analyze and explain these MCP tool results. Provide insights, summaries, and actionable recommendations."
                                        
                                        with st.spinner("Generating AI insights..."):
                                            ai_response = nova_integration.generate_response(ai_prompt, context)
                                            st.subheader("AI Insights (Nova Pro)")
                                            st.markdown(ai_response)
                        else:
                            st.warning("Please provide at least one parameter")
            else:
                st.warning("No tools available for this server or failed to retrieve tools")
    else:
        st.info("👆 Connect to a server above to start using tools")
    
    # Configuration sidebar
    with st.sidebar:
        st.header("Configuration")
        
        st.subheader("Environment Variables")
        
        # Show current configuration
        aws_region = os.getenv('AWS_REGION', 'Not set')
        aws_profile = os.getenv('AWS_PROFILE', 'Not set')
        github_token = "Configured" if os.getenv('GITHUB_TOKEN') else "Not set"
        
        st.text(f"AWS Region: {aws_region}")
        st.text(f"AWS Profile: {aws_profile}")
        st.text(f"GitHub Token: {github_token}")
        
        st.divider()
        
        # Quick setup
        st.subheader("Quick Setup")
        
        if st.button("Test uvx"):
            try:
                result = subprocess.run(['uvx', '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    st.success(f"uvx working: {result.stdout.strip()}")
                else:
                    st.error(f"uvx error: {result.stderr}")
            except Exception as e:
                st.error(f"uvx not found: {e}")

if __name__ == "__main__":
    main()
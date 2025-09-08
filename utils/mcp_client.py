import json
import subprocess
import os
import time
import threading
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MCPClient:
    """Synchronous client for interacting with MCP servers"""
    
    def __init__(self):
        self.servers = {}
        self.active_connections = {}
        logger.info("MCP Client initialized - uvx is available on this system")
    
    def connect_server(self, server_name: str, command: str, args: List[str], env: Dict[str, str] = None) -> bool:
        """Connect to an MCP server"""
        try:
            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start the MCP server process using synchronous subprocess
            process = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env,
                text=True,
                bufsize=0  # Unbuffered
            )
            
            self.active_connections[server_name] = process
            logger.info(f"Connected to MCP server: {server_name}")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"Command '{command}' not found: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {server_name}: {e}")
            return False
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        try:
            if server_name not in self.active_connections:
                logger.error(f"No active connection to server: {server_name}")
                return {"error": f"No connection to {server_name}"}
            
            process = self.active_connections[server_name]
            
            # Check if process is still alive
            if process.poll() is not None:
                logger.error(f"MCP server {server_name} has terminated")
                return {"error": f"Server {server_name} has terminated"}
            
            # Prepare the MCP request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # Send request to MCP server
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response with timeout
            response_line = process.stdout.readline()
            if not response_line:
                return {"error": "No response from server"}
                
            response = json.loads(response_line.strip())
            
            if "result" in response:
                return response["result"]
            elif "error" in response:
                return {"error": response["error"]}
            else:
                return {"error": "Invalid response format"}
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            return {"error": str(e)}
    
    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server"""
        try:
            if server_name not in self.active_connections:
                return []
            
            process = self.active_connections[server_name]
            
            # Check if process is still alive
            if process.poll() is not None:
                logger.error(f"MCP server {server_name} has terminated")
                return []
            
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response with timeout
            response_line = process.stdout.readline()
            if not response_line:
                return []
                
            response = json.loads(response_line.strip())
            
            if "result" in response and "tools" in response["result"]:
                return response["result"]["tools"]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error listing tools for {server_name}: {e}")
            return []
    
    def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server"""
        try:
            if server_name in self.active_connections:
                process = self.active_connections[server_name]
                process.terminate()
                try:
                    process.wait(timeout=5)  # Wait up to 5 seconds
                except subprocess.TimeoutExpired:
                    process.kill()  # Force kill if it doesn't terminate
                del self.active_connections[server_name]
                logger.info(f"Disconnected from MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Error disconnecting from {server_name}: {e}")
    
    def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for server_name in list(self.active_connections.keys()):
            self.disconnect_server(server_name)

# Alias for backward compatibility - now the main client is already synchronous
class SyncMCPClient:
    """Synchronous MCP client - now just a direct wrapper around MCPClient"""
    
    def __init__(self):
        self.client = MCPClient()
    
    def connect_server(self, server_name: str, command: str, args: List[str], env: Dict[str, str] = None) -> bool:
        """Synchronous server connection"""
        return self.client.connect_server(server_name, command, args, env)
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous tool call"""
        return self.client.call_tool(server_name, tool_name, arguments)
    
    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Synchronous tool listing"""
        return self.client.list_tools(server_name)
    
    def disconnect_server(self, server_name: str):
        """Synchronous server disconnection"""
        self.client.disconnect_server(server_name)
    
    def disconnect_all(self):
        """Synchronous disconnect all"""
        self.client.disconnect_all()
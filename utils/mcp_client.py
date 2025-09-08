import json
import subprocess
import asyncio
import os
import concurrent.futures
import threading
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class MCPClient:
    """Client for interacting with MCP servers"""
    
    def __init__(self):
        self.servers = {}
        self.active_connections = {}
        logger.info("MCP Client initialized - uvx is available on this system")
    
    async def connect_server(self, server_name: str, command: str, args: List[str], env: Dict[str, str] = None) -> bool:
        """Connect to an MCP server"""
        try:
            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)
            
            # Start the MCP server process
            process = await asyncio.create_subprocess_exec(
                command, *args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=process_env
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
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on an MCP server"""
        try:
            if server_name not in self.active_connections:
                logger.error(f"No active connection to server: {server_name}")
                return {"error": f"No connection to {server_name}"}
            
            process = self.active_connections[server_name]
            
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
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            # Read response
            response_line = await process.stdout.readline()
            response = json.loads(response_line.decode().strip())
            
            if "result" in response:
                return response["result"]
            elif "error" in response:
                return {"error": response["error"]}
            else:
                return {"error": "Invalid response format"}
                
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            return {"error": str(e)}
    
    async def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """List available tools on an MCP server"""
        try:
            if server_name not in self.active_connections:
                return []
            
            process = self.active_connections[server_name]
            
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            response_line = await process.stdout.readline()
            response = json.loads(response_line.decode().strip())
            
            if "result" in response and "tools" in response["result"]:
                return response["result"]["tools"]
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error listing tools for {server_name}: {e}")
            return []
    
    async def disconnect_server(self, server_name: str):
        """Disconnect from an MCP server"""
        try:
            if server_name in self.active_connections:
                process = self.active_connections[server_name]
                process.terminate()
                await process.wait()
                del self.active_connections[server_name]
                logger.info(f"Disconnected from MCP server: {server_name}")
        except Exception as e:
            logger.error(f"Error disconnecting from {server_name}: {e}")
    
    async def disconnect_all(self):
        """Disconnect from all MCP servers"""
        for server_name in list(self.active_connections.keys()):
            await self.disconnect_server(server_name)

# Synchronous wrapper for Streamlit compatibility
class SyncMCPClient:
    """Synchronous wrapper for MCPClient with proper event loop handling"""
    
    def __init__(self):
        self.client = MCPClient()
    
    def _run_async(self, coro):
        """Run an async coroutine safely with proper event loop handling"""
        def run_in_thread():
            """Run the coroutine in a separate thread with its own event loop"""
            # Create a completely fresh event loop in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(coro)
            except Exception as e:
                logger.error(f"Error in async operation: {e}")
                return None
            finally:
                try:
                    # Clean up any remaining tasks
                    pending = asyncio.all_tasks(loop)
                    for task in pending:
                        task.cancel()
                    if pending:
                        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except:
                    pass
                finally:
                    loop.close()
        
        try:
            # Always run in a separate thread to avoid event loop conflicts
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 second timeout
        except concurrent.futures.TimeoutError:
            logger.error("Async operation timed out")
            return None
        except Exception as e:
            logger.error(f"Failed to run async operation: {e}")
            return None
    
    def connect_server(self, server_name: str, command: str, args: List[str], env: Dict[str, str] = None) -> bool:
        """Synchronous server connection"""
        try:
            result = self._run_async(self.client.connect_server(server_name, command, args, env))
            return result if result is not None else False
        except Exception as e:
            logger.error(f"Failed to connect server {server_name}: {e}")
            return False
    
    def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous tool call"""
        try:
            result = self._run_async(self.client.call_tool(server_name, tool_name, arguments))
            return result if result is not None else {"error": "Operation failed"}
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            return {"error": str(e)}
    
    def list_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Synchronous tool listing"""
        try:
            result = self._run_async(self.client.list_tools(server_name))
            return result if result is not None else []
        except Exception as e:
            logger.error(f"Failed to list tools for {server_name}: {e}")
            return []
    
    def disconnect_server(self, server_name: str):
        """Synchronous server disconnection"""
        try:
            self._run_async(self.client.disconnect_server(server_name))
        except Exception as e:
            logger.error(f"Failed to disconnect server {server_name}: {e}")
    
    def disconnect_all(self):
        """Synchronous disconnect all"""
        try:
            self._run_async(self.client.disconnect_all())
        except Exception as e:
            logger.error(f"Failed to disconnect all servers: {e}")
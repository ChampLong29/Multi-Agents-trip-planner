"""MCPTool 到 LangChain 工具的适配器"""

import json
from typing import Dict, Any, List, Optional
from langchain_core.tools import BaseTool
from pydantic import Field
from hello_agents.tools import MCPTool


class MCPToolAdapter(BaseTool):
    """将 MCPTool 适配为 LangChain BaseTool"""
    
    def __init__(self, mcp_tool: MCPTool, tool_name: str, tool_description: str = ""):
        """
        初始化适配器
        
        Args:
            mcp_tool: MCPTool 实例
            tool_name: 工具名称（MCP 服务器中的工具名）
            tool_description: 工具描述
        """
        self.mcp_tool = mcp_tool
        self._tool_name = tool_name
        self._tool_description = tool_description
        
        # 调用父类初始化
        super().__init__(
            name=f"{mcp_tool.name}_{tool_name}",
            description=tool_description or f"MCP工具: {tool_name}"
        )
    
    def _run(
        self,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> str:
        """执行工具"""
        try:
            # 调用 MCPTool 的 run 方法
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": self._tool_name,
                "arguments": kwargs
            })
            
            # 如果结果是字符串，直接返回
            if isinstance(result, str):
                return result
            
            # 如果结果是字典，转换为 JSON 字符串
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            return json.dumps({"error": f"MCP工具调用失败: {str(e)}"})
    
    async def _arun(
        self,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> str:
        """异步执行工具"""
        # MCPTool 目前不支持异步，使用同步方法
        return self._run(run_manager=run_manager, **kwargs)


def create_mcp_tools(mcp_tool: MCPTool) -> List[BaseTool]:
    """
    将 MCPTool 的所有工具转换为 LangChain 工具列表
    
    Args:
        mcp_tool: MCPTool 实例（需要 auto_expand=True）
        
    Returns:
        LangChain 工具列表
    """
    tools = []
    
    try:
        # 方法1: 如果 MCPTool 有 auto_expand 功能，尝试直接获取展开的工具
        if hasattr(mcp_tool, 'list_tools') and callable(mcp_tool.list_tools):
            try:
                tools_list = mcp_tool.list_tools()
                if isinstance(tools_list, list):
                    for tool_info in tools_list:
                        if isinstance(tool_info, dict):
                            tool_name = tool_info.get("name", "")
                            tool_description = tool_info.get("description", "")
                        elif isinstance(tool_info, str):
                            tool_name = tool_info
                            tool_description = ""
                        else:
                            continue
                        
                        if tool_name:
                            adapter = MCPToolAdapter(
                                mcp_tool=mcp_tool,
                                tool_name=tool_name,
                                tool_description=tool_description
                            )
                            tools.append(adapter)
                    
                    if tools:
                        print(f"✅ 通过 list_tools() 成功创建 {len(tools)} 个 MCP 工具适配器")
                        return tools
            except Exception as e:
                print(f"⚠️  使用 list_tools() 失败，尝试其他方法: {str(e)}")
        
        # 方法2: 通过 run 方法获取工具列表
        tools_info = mcp_tool.run({"action": "list_tools"})
        
        # 解析工具信息
        tools_data = None
        if isinstance(tools_info, str):
            # 尝试解析 JSON
            try:
                tools_data = json.loads(tools_info)
            except json.JSONDecodeError:
                # 如果不是 JSON，尝试查找工具名称模式
                import re
                # 尝试从字符串中提取工具名称
                tool_names = re.findall(r'"name"\s*:\s*"([^"]+)"', tools_info)
                if tool_names:
                    tools_data = [{"name": name} for name in tool_names]
                else:
                    print(f"⚠️  无法解析 MCP 工具列表: {tools_info[:200]}")
                    return tools
        else:
            tools_data = tools_info
        
        # 提取工具列表
        tools_list = []
        if isinstance(tools_data, dict):
            # 可能是 {"tools": [...]} 格式
            tools_list = tools_data.get("tools", [])
            # 也可能是直接包含工具信息的字典
            if not tools_list and "name" in tools_data:
                tools_list = [tools_data]
        elif isinstance(tools_data, list):
            tools_list = tools_data
        else:
            print(f"⚠️  MCP 工具列表格式不正确: {type(tools_data)}")
            return tools
        
        # 为每个工具创建适配器
        for tool_info in tools_list:
            if isinstance(tool_info, dict):
                tool_name = tool_info.get("name", "")
                tool_description = tool_info.get("description", "")
            elif isinstance(tool_info, str):
                tool_name = tool_info
                tool_description = ""
            else:
                continue
            
            if tool_name:
                adapter = MCPToolAdapter(
                    mcp_tool=mcp_tool,
                    tool_name=tool_name,
                    tool_description=tool_description
                )
                tools.append(adapter)
        
        if tools:
            print(f"✅ 成功创建 {len(tools)} 个 MCP 工具适配器")
        else:
            print(f"⚠️  未找到可用的 MCP 工具")
        
    except Exception as e:
        print(f"❌ 创建 MCP 工具适配器失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return tools


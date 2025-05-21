from typing import Any, Dict
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester
import json

class DataAnalyzeAgent(BaseAgent):
    """
    数据分析 Agent，用于分析初始提示中的关键信息
    """
    
    def __init__(self):
        pass
    
    async def execute(self, api_requestor: AsyncApiRequester, initial_prompt: str) -> Dict[str, Any]:
        """
        分析初始提示中的关键信息
        
        Args:
            api_requestor: API 请求器对象
            initial_prompt: 初始提示文本
            
        Returns:
            分析结果字典
        """
        # 构建完整的提示
        full_prompt = self._get_analysis_prompt(initial_prompt)
        
        # 构建 messages
        messages = [
            {
                "role": "user",
                "content": full_prompt
            }
        ]

        # 调用 API 进行分析
        try:
            response = await api_requestor.call_api(messages)
            result = await response

            print(result.get('choices', [{}])[0].get('finish_reason', {}))
            
            # 从 API 响应中提取内容
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 尝试解析 JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"JSON 解析错误: {e}")
                print(f"原始内容: {content}")
                return {
                    "is_rectangular": False,
                    "has_multiple_time_nodes": False,
                    "has_time_nodes_without_restriction": False,
                    "has_murder_motives": False,
                    "has_multiple_weapons": False,
                    "error": "JSON 解析失败"
                }
                
        except Exception as e:
            print(f"API 调用错误: {str(e)}")
            return {
                "is_rectangular": False,
                "has_multiple_time_nodes": False,
                "has_time_nodes_without_restriction": False,
                "has_murder_motives": False,
                "has_multiple_weapons": False,
                "error": str(e)
            }
        
    def _get_analysis_prompt(self, initial_prompt: str) -> str:
        """生成分析提示
        
        Args:
            initial_prompt: 初始提示文本
            
        Returns:
            完整的分析提示
        """
        return """
请分析以下初始提示，并回答以下问题：
1. 房间平面图是否是一个矩形或长条（即使有部分格子没填满也算矩形，房间平面图只有一行或一列也算矩形）？
2. 是否给出了多个时间节点（至少2个）？
3. 是否既给出了多个时间节点，但没有给出1小时之内只能不动或移动到相邻房间的限制？
4. 是否给出了每个人要有一个杀人动机？
5. 是否给出了多个可选凶器（至少2个）？

请以JSON格式返回分析结果！不要携带如"```json"或"```"等markdown格式相关字符！！！格式如下：
{{
    "is_rectangular": true/false,
    "has_multiple_time_nodes": true/false,
    "has_time_nodes_without_restriction": true/false,
    "has_murder_motives": true/false,
    "has_multiple_weapons": true/false
}}

初始提示：
{initial_prompt}
""".format(initial_prompt=initial_prompt)


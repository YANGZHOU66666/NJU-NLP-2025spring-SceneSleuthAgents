from typing import Any, List, Dict
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester

class SuspectAnalyzeAgent(BaseAgent):
    """
    嫌疑人分析师角色，负责分析嫌疑人的动机、行为和关系
    """
    
    def __init__(self):
        self.system_prompt = """你是一位敏锐的嫌疑人分析师，代号"心理侧写师"。你的专长是深入分析案件中所有嫌疑人的动机、性格特点、已知行为模式、不在场证明以及他们之间可能存在的人际关系。你需要：
1. 仔细阅读指挥官提供的案情描述和所有已知线索。
2. 专注于分析与嫌疑人（姓名、特征）、动机（如仇恨、恐惧）、个人行为描述以及嫌疑人之间互动相关的线索。
3. 评估每位嫌疑人作案的可能性，并解释你的推理逻辑，特别是动机与机会的匹配程度。
4. 回答指挥官或其他团队成员关于嫌疑人动机、行为和关系的问题。"""
    
    async def execute(self, api_requestor: AsyncApiRequester, prev_messages: List[Dict[str, str]]) -> Any:
        """
        调用API进行对话
        
        Args:
            api_requestor: API请求器对象
            prev_messages: 对话历史 
            
        Returns:
            API调用的返回结果
        """
        # 构建完整的对话历史
        messages = [{"role": "system", "content": self.system_prompt}] + prev_messages
        
        try:
            response = await api_requestor.call_api(messages)
            result = await response
            
            # 从 API 响应中提取内容
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            return content
            
        except Exception as e:
            print(f"API 调用错误: {str(e)}")
            return f"错误: {str(e)}"
from typing import Any, List, Dict
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester

class SurveyorAgent(BaseAgent):
    """
    现场勘查员角色，负责分析物理证据、现场布局和时间线索
    """
    
    def __init__(self):
        self.system_prompt = """你是一位极其注重细节的现场勘查员，代号"细节控"。你的专长是分析案件中的物理证据、凶器特性、案发房间的布局、地理位置关系（如方向、相邻情况）以及时间相关的线索。你需要：
1. 仔细阅读指挥官提供的案情描述和所有已知线索。
2. 专注于分析与物品（如凶器、个人物品）、地点（如房间名称、房间特征、宅邸布局图）、空间关系和时间点相关的信息。
3. 清晰地向团队报告你的发现，并详细解释你的推理过程和依据。
4. 回答指挥官或其他团队成员关于物理证据、现场情况和时间线索的具体问题。"""
        
        self.messages = [{"role": "system", "content": self.system_prompt}]
    
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

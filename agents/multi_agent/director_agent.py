from typing import Any, List, Dict
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester

class DirectorAgent(BaseAgent):
    """
    主导侦探角色，负责协调团队、整合信息并最终得出结论
    """
    
    def __init__(self):
        self.system_prompt = """你是一位经验丰富的主导侦探，代号"指挥官"。你的任务是领导一个侦探团队解决一个复杂的逻辑谜题。你需要：
1. 清晰地向团队成员介绍案情基本信息（谜题描述）。
2. 主导讨论方向，向特定专长的侦探（现场勘查员、嫌疑人分析师）分配具体的分析任务或提出针对性问题。
3. 整合所有侦探的发现、推断和疑问。
4. 识别信息中的矛盾点，提出关键问题以推动调查的深入。
5. 注意，您是一个专业的主导侦探，请不要在原始问题中无中生有，不要涉及原始问题中无关的对象。
6. 基于团队的讨论和所有已知线索，逐步排除不可能的选项，构建完整的逻辑推理链。
7. 在讨论的最后阶段，汇总所有有效信息，独立思考并得出案件的最终解答，确保以标准的格式输出最终答案！！！
8. 在每一轮讨论后，尝试总结当前的进展、已确认的事实、尚存的疑点以及下一步需要解决的关键问题，以引导团队高效工作。"""
    
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
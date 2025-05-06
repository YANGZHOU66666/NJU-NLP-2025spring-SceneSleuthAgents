from typing import Any, Dict
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester
import json

class BasicPromptAgent(BaseAgent):
    """
    基本的提示 Agent，用于处理单个提示并返回格式化答案
    """
    
    def __init__(self):
        pass
    
    async def call_api(self, api_requestor: AsyncApiRequester, prompt: str) -> str:
        """
        处理单个提示并返回格式化答案
        
        Args:
            api_requestor: API 请求器对象
            prompt: 提示文本
            
        Returns:
            处理后的答案字符串，格式为 "A. 答案一 B. 答案二"
        """
        # 构建完整的提示
        full_prompt = self._get_full_prompt(prompt)
        
        # 构建 messages
        messages = [
            {
                "role": "user",
                "content": full_prompt
            }
        ]
        
        # 调用 API 获取答案
        try:
            response = await api_requestor.call_api(messages)
            result = await response
            
            # 从 API 响应中提取内容
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            # 处理答案
            processed_answer = self._process_answer(content)
            return processed_answer
            
        except Exception as e:
            print(f"API 调用错误: {str(e)}")
            return f"错误: {str(e)}"
    
    def _get_full_prompt(self, prompt: str) -> str:
        """构建完整的提示
        
        Args:
            prompt: 原始提示文本
            
        Returns:
            完整的提示文本
        """
        return """
请回答以下逻辑推理问题：

{prompt}

请以JSON格式返回分析结果！不要携带如"```json"或"```"等markdown格式相关字符！！！格式如下：
{{
    "solution": {{
        "A": "答案A",
        "B": "答案B"
    }}
}}
""".format(prompt=prompt)
    
    def _process_answer(self, content: str) -> str:
        """处理 API 返回的答案
        
        Args:
            content: API 返回的原始内容
            
        Returns:
            处理后的答案字符串，格式为 "A. 答案一 B. 答案二"
        """
        try:
            # 尝试解析 JSON
            answer_dict = json.loads(content)
            
            # 确保返回字典包含 solution 字段
            if "solution" not in answer_dict:
                return "错误: 答案格式错误：缺少 solution 字段"
            
            # 获取 solution 字典
            solution = answer_dict["solution"]
            
            # 将 solution 转换为字符串格式
            answer_parts = []
            for key, value in sorted(solution.items()):
                answer_parts.append(f"{key}. {value}")
            
            return " ".join(answer_parts)
            
        except json.JSONDecodeError:
            # 如果 JSON 解析失败，尝试从文本中提取答案
            # 移除可能的 markdown 格式标记
            content = content.replace("```json", "").replace("```", "").strip()
            
            # 尝试再次解析
            try:
                answer_dict = json.loads(content)
                if "solution" not in answer_dict:
                    return "错误: 答案格式错误：缺少 solution 字段"
                
                # 获取 solution 字典
                solution = answer_dict["solution"]
                
                # 将 solution 转换为字符串格式
                answer_parts = []
                for key, value in sorted(solution.items()):
                    answer_parts.append(f"{key}. {value}")
                
                return " ".join(answer_parts)
                
            except json.JSONDecodeError:
                # 如果还是无法解析，返回错误
                return "错误: 无法解析答案格式"

from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester
import json
from solver_tool import solver_tool

class ToolCallAgent(BaseAgent):
    """
    工具调用 Agent，用于处理单个提示并返回格式化答案，支持工具调用
    """
    
    def __init__(self):
        pass
    
    async def execute(self, api_requestor: AsyncApiRequester, prompt: str) -> str:
        """
        处理单个提示并返回格式化答案，支持工具调用
        
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
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "solver_tool",
                    "description": self._get_tool_description(),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "victim": {
                                "type": "string",
                                "description": "被害人的姓名"
                            },
                            "suspects": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "嫌疑人姓名列表"
                            },
                            "weapons": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "可能的凶器名称列表"
                            },
                            "motives": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "可能的作案动机列表"
                            },
                            "room_grid": {
                                "type": "array",
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "description": "房间布局网格"
                            },
                            "times": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "案件相关的时间点列表"
                            },
                            "clues": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": ["WeaponClue", "ItemRoomTimeClue", "RelativeLocationClue", "IfAndOnlyIfClue"]
                                        }
                                    },
                                    "required": ["type"]
                                },
                                "description": "线索列表"
                            }
                        },
                        "required": ["victim", "suspects", "weapons", "room_grid", "clues"]
                    }
                }
            }
        ]
        
        # 调用 API 获取答案
        try:
            response = await api_requestor.call_api(messages, tools)
            result = await response
            print("第一次请求result", result)
            if 'tool_calls' in result['choices'][0]['message']:
                # 从 API 响应中提取内容
                response_data = result
                # 获取工具调用信息
                tool_call = response_data['choices'][0]['message']['tool_calls'][0]
                function_name = tool_call['function']['name']
                arguments = json.loads(tool_call['function']['arguments'])
                # 执行对应的函数
                if function_name == 'solver_tool':
                    print("func call arguments", arguments)
                    content = solver_tool(**arguments)
                else:
                    content = "错误: 无法解析工具调用"
                # 再次调用大模型
                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": str(content),
                    "tool_call_id": tool_call['id']
                })
                response = await api_requestor.call_api(messages)
                result = await response
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
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
请回答以下逻辑推理问题。你可以使用提供的工具来帮助解决问题。

{prompt}

请以JSON格式返回分析结果！不要携带如"```json"或"```"等markdown格式相关字符！！！格式如下：
{{
    "solution": {{
        "A": "答案A",
        "B": "答案B"
    }}
}}
""".format(prompt=prompt)
    
    def _get_tool_description(self) -> str:
        """获取工具描述
        
        Args:
            tool: 工具定义字典
            
        Returns:
            工具描述字符串
        """
        return """
使用OR-Tools求解谋杀案谜题

参数说明 (Args):
    victim (str): 被害人的姓名。
        示例: "博迪"

    suspects (list[str]): 嫌疑人姓名列表。
        示例: ["玫瑰夫人", "蜜桃小姐"]

    weapons (list[str]): 可能的凶器名称列表。
        示例: ["绳索", "马蹄铁"]

    motives (list[str]): 可能的作案动机列表。
        如果列表为空，系统会使用一个默认的"未知动机"。
        注意：当前版本的求解器主要使用一个全局的"凶杀动机"，
        更复杂的将特定动机分配给特定嫌疑人的逻辑需要额外的线索类型或模型调整。
        示例: ["复仇", "贪婪"] 或 []

    room_grid (list[list[str]]): 房间布局网格。一个二维列表，其中每个内部列表代表一行。
        - 字符串元素是房间的名称。
        - 用 "-" 表示该位置没有房间或是障碍物。
        - 列表的索引定义了房间的相对位置（例如，grid[0][0] 是左上角的房间）。
        示例:
        [
            ["书房", "客厅", "-"],
            ["餐厅", "-", "厨房"]
        ]
        这表示一个2x3的网格，书房在(0,0)，客厅在(0,1)，餐厅在(1,0)，厨房在(1,2)。

    times (list[str]): 案件相关的时间点列表。
        - 如果列表为空或只有一个元素，系统会将其视为一个单一的、代表性的时间点（内部处理为 "t0"）。
        - 如果有多个时间点，它们应该是有序的（尽管当前求解器对时间顺序的利用有限，主要用于区分不同时刻的状态）。
        示例: ["19:00", "19:15", "19:30"] 或 []

    clues (list[dict[str, any]]): 线索列表。每个线索是一个字典，其结构取决于 'type' 字段。
        支持的线索类型及格式如下：

        1.  `WeaponClue` (确定凶器线索):
            -   含义: 直接指明了本案使用的凶器。
            -   格式: `{"type": "WeaponClue", "weapon": "凶器名称"}`
            -   示例: `{"type": "WeaponClue", "weapon": "绳索"}`

        2.  `ItemRoomTimeClue` (物品-房间-时间线索):
            -   含义: 指明某个物品（被害人、嫌疑人或凶器）在特定时间点位于特定房间。
            -   格式: `{"type": "ItemRoomTimeClue", "item": "物品名称", "room": "房间名称", "time": "时间点"}`
            -   `item`: 可以是 `victim` 的名字，`suspects` 列表中的一个名字，或 `weapons` 列表中的一个名字。
            -   `time`: 应该是 `times` 列表中定义的一个时间点。如果为 `None` 或缺失，则默认为第一个处理后的时间点 (通常是 "t0")。
            -   示例: `{"type": "ItemRoomTimeClue", "item": "玫瑰夫人", "room": "书房", "time": "19:00"}`
            -   示例 (时间点为None): `{"type": "ItemRoomTimeClue", "item": "马蹄铁", "room": "厨房", "time": None}`

        3.  `RelativeLocationClue` (相对位置线索):
            -   含义: 指明物品1相对于物品2的位置关系（目前仅支持上、下、左、右，即北、南、西、东）。
            -   格式: `{"type": "RelativeLocationClue", "item1": "物品1名称", "item2": "物品2名称", "direction": "方向"}`
            -   `item1`, `item2`: 可以是 `suspects` 或 `weapons` 列表中的名字。
            -   `direction`: "北", "南", "东", "西"。
            -   注意: 当前实现假设此线索应用于第一个处理后的时间点 (通常是 "t0")。如果需要指定特定时间，此线索类型需要扩展。
            -   示例: `{"type": "RelativeLocationClue", "item1": "绳索", "item2": "蜜桃小姐", "direction": "南"}`
                (表示"绳索"在"蜜桃小姐"的正南方，即"绳索"的行索引 > "蜜桃小姐"的行索引，列索引相同)

        4.  `IfAndOnlyIfClue` (当且仅当关系线索):
            -   含义: 指明两个子线索之间是逻辑上的充分必要关系（等价关系）。
            -   格式: `{"type": "IfAndOnlyIfClue", "clue1": <子线索1字典>, "clue2": <子线索2字典>}`
            -   `clue1`, `clue2`: **必须是** `ItemRoomTimeClue` 类型的线索字典。
            -   示例:
                ```json
                {
                    "type": "IfAndOnlyIfClue",
                    "clue1": {"type": "ItemRoomTimeClue", "item": "马蹄铁", "room": "书房", "time": None},
                    "clue2": {"type": "ItemRoomTimeClue", "item": "博迪", "room": "书房", "time": None}
                }
                ```
                (表示"马蹄铁在书房"当且仅当"博迪在书房")

返回值 (Returns):
    dict: 一个包含求解结果的字典，或在无解/出错时包含 "error" 键。
            成功时的结构示例:
            {
                'murderer': '凶手名称',
                'weapon': '凶器名称',
                'murder_time': '凶杀时间点',
                'murder_location': '凶杀房间名称',
                'murder_motive': '凶杀动机',
                'suspect_locations': {
                    '嫌疑人1': {'时间点1': '房间A', '时间点2': '房间B'},
                    '嫌疑人2': {'时间点1': '房间C', '时间点2': '房间D'}
                },
                'weapon_locations': {
                    '凶器1': {'时间点1': '房间X', '时间点2': '房间Y'},
                    '凶器2': {'时间点1': '房间Z', '时间点2': '房间W'}
                },
                'motives': { # 注意：这通常反映的是全局凶杀动机，除非有更复杂的动机分配
                    '嫌疑人1': '推断出的动机或默认值',
                    '嫌疑人2': '推断出的动机或默认值'
                }
            }
"""
    
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



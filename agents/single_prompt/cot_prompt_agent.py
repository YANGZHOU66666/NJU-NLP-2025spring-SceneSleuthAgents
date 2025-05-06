# 单论对话，使用cot + one shot策略
from typing import Any, Dict
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester
import json

class COTPromptAgent(BaseAgent):
    """
    链式思考提示 Agent，用于处理侦探问题并返回格式化的 JSON 答案
    """

    def __init__(self):
        pass

    async def call_api(self, api_requestor: AsyncApiRequester, prompt: str) -> str:
        """
        处理侦探问题并返回格式化的 JSON 答案

        Args:
            api_requestor: API 请求器对象
            prompt: 提示文本

        Returns:
            处理后的答案字符串
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
            # print(result.get('choices', [{}])[0].get('finish_reason', {}))
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
        return """你需要解决如下的侦探问题：
{prompt}

解决侦探问题时，请遵循以下思考步骤：
分析已有信息：首先，整理案件中的所有已知信息，包括嫌疑人、凶器、地点、时间和其他关键线索。将这些信息系统化地列出，以确保不遗漏任何细节。
理解物理约束条件：明确房间布局、人物移动规则和凶案发生的必要条件（如凶手与受害者单独共处、凶器在场等）。
建立可能性矩阵：为每位嫌疑人、每件凶器和每个地点创建位置/状态矩阵，标注每个元素在各个时间点的可能位置。
应用逻辑推理：根据给定线索，逐步排除不可能的情况。应用演绎法和归纳法，对每条线索进行深入分析。
检验所有假设：对每个可能的场景进行假设，然后检验该假设是否与所有已知线索相符。如果发现矛盾，立即放弃该假设。
构建完整事件时间线：一旦缩小了可能性范围，尝试构建案件发生的完整时间线，确保所有线索都能在这一时间线中得到合理解释。
验证最终结论：在得出最终结论前，再次检查你的推理过程，确保没有遗漏任何关键线索或逻辑漏洞。
明确回答问题：最后，根据你的分析，明确回答所有问题，确保你的回答基于可靠的逻辑推理。

请逐步展示你的思考过程：
让我们一步一步思考这个侦探问题：

[在这里开始你的详细推理过程]

最终答案：
在你的最终JSON答案前，请先输出标志性字符串"@JSON_RESULT_START@"！！！！！然后再输出JSON结果。
在JSON结果输出完成后，立即输出标志性字符串"@JSON_RESULT_END@"！！！！！
如果你不按照这个格式输出，你将会被严重惩罚！！！

请以JSON格式返回分析结果！不要携带如"```json"或"```"等markdown格式相关字符！！！格式如下：
{{
    "solution": {{
        "A": "答案A",
        "B": "答案B",
        "C": "答案C",
        "D": "答案D",
        "E": "答案E",
        "F": "答案F",
        "G": "答案G",
        "H": "答案H"
    }},
    "reasoning": "这里是你的推理过程的简要总结"
}}

------

下面是一个示例，展示如何解决侦探问题并给出答案：

[示例问题]
冬夜深沉，雪花无声地落在都铎庄园的尖顶上。富可敌国却行踪神秘的约翰·Q·博迪先生，正在宅邸里举办一场小型但奢华的晚宴，邀请了几位最亲密的伙伴。然而，当黎明的第一缕光线穿透云层时，博迪先生被发现陈尸于宅中一隅。

警方锁定了两位嫌疑人：

• 布鲁内特先生
• 怀特夫人

凶器可能是以下两种之一：

• 左轮手枪
• 绳索

命案现场只可能位于以下两个房间之一：

1. 大厅
2. 马车房

房间布局如下：

  北
西 1 东
西 2 东
  南

根据现场勘查，凶手必须与博迪先生单独处于某个房间，且该房间内至少有一件凶器。

关键线索缓缓浮出水面：

- 博迪先生曾在大厅出现，或者布鲁内特先生曾在大厅出现
- 致命伤来自左轮手枪
- 布鲁内特先生当时所在的位置，恰好在绳索所在房间的正南方

请回答以下问题：

A. 真凶是谁？
B. 命案发生在哪个房间？
C. 怀特夫人在何处？
D. 布鲁内特先生在何处？
E. 左轮手枪在何处？
F. 绳索在何处？

[示例思考过程]
让我们一步一步思考这个侦探问题：

首先，整理已知信息：
- 两位嫌疑人：布鲁内特先生和怀特夫人
- 两种可能的凶器：左轮手枪和绳索
- 两个可能的命案现场：大厅和马车房
- 凶手必须与博迪先生单独处于某个房间，且该房间内至少有一件凶器
- 博迪先生曾在大厅出现，或者布鲁内特先生曾在大厅出现
- 致命伤来自左轮手枪
- 布鲁内特先生当时所在的位置，恰好在绳索所在房间的正南方

分析线索1："博迪先生曾在大厅出现，或者布鲁内特先生曾在大厅出现"
这意味着至少有一个是真的：博迪先生在大厅，或布鲁内特先生在大厅。

分析线索2："致命伤来自左轮手枪"
这告诉我们凶器是左轮手枪，而不是绳索。

分析线索3："布鲁内特先生当时所在的位置，恰好在绳索所在房间的正南方"
根据房间布局，如果布鲁内特先生在马车房（2），那么绳索就在大厅（1）。
如果布鲁内特先生在大厅（1），那么绳索就应该在大厅北边的某个房间，但这超出了我们的房间范围。

结合线索2和线索3，我们知道：
- 凶器是左轮手枪
- 布鲁内特先生在马车房
- 绳索在大厅

现在，考虑凶案发生的必要条件：
1. 凶手与博迪先生单独处于某个房间
2. 该房间内至少有一件凶器（在这个案例中是左轮手枪）

我们已经确定布鲁内特先生在马车房，绳索在大厅。那么左轮手枪在哪里？
由于左轮手枪是凶器，且凶案必须发生在凶手和博迪先生共处的房间，所以左轮手枪必须与博迪先生在同一个房间。

从线索1，我们知道博迪先生曾在大厅出现，或者布鲁内特先生曾在大厅出现。
我们已经确定布鲁内特先生在马车房，所以博迪先生必须在大厅。

因此，博迪先生在大厅，左轮手枪也在大厅。
布鲁内特先生在马车房，所以不可能是凶手。
那么，怀特夫人必须是凶手，且她必须在大厅与博迪先生共处。

@JSON_RESULT_START@
{{
    "solution": {{
        "A": "怀特夫人",
        "B": "大厅",
        "C": "大厅",
        "D": "马车房",
        "E": "大厅",
        "F": "大厅"
    }},
    "reasoning": "通过分析线索，我确定布鲁内特先生在马车房，绳索和左轮手枪都在大厅。由于凶器是左轮手枪，且博迪先生在大厅被杀，而布鲁内特先生在马车房，所以怀特夫人必须是凶手，且她必须在大厅与博迪先生共处。"
}}
@JSON_RESULT_END@

------

注意：
1. 只需包含题目要求的答案选项，不要添加额外的选项！！！否则你将会被严重惩罚！！！
2. 确保JSON格式正确，不要包含任何markdown标记！！！否则你将会被严重惩罚！！！
3. 确保reasoning字段包含你的推理过程的简要总结！！！否则你将会被严重惩罚！！！
4. 记得在JSON前添加"@JSON_RESULT_START@"标志！！!在JSON后添加"@JSON_RESULT_END@"标志！！！否则你将会被严重惩罚！！！
5. 请输出完整的json，不要省略任何必要信息！！！不要漏掉任何字段！！！json的大括号和逗号必须完整和匹配！！！否则你将会被严重惩罚！！！
""".format(prompt=prompt)

    def _process_answer(self, content: str) -> str:
        """处理 API 返回的答案

        Args:
            content: API 返回的原始内容

        Returns:
            处理后的答案字符串
        """
        # 查找开始标志性字符串
        start_marker = "@JSON_RESULT_START@"
        end_marker = "@JSON_RESULT_END@"
        start_pos = content.find(start_marker)

        if start_pos != -1:
            # 如果找到开始标志，查找结束标志
            content_after_start = content[start_pos + len(start_marker):]
            end_pos = content_after_start.find(end_marker)

            if end_pos != -1:
                # 如果找到结束标志，只处理两个标志之间的内容
                json_content = content_after_start[:end_pos].strip()
            else:
                # 如果没找到结束标志，处理开始标志后的所有内容
                json_content = content_after_start.strip()
        else:
            # 如果没找到开始标志，尝试处理整个内容
            json_content = content

        try:
            # 尝试解析 JSON
            # 移除可能的 markdown 格式标记
            json_content = json_content.replace("```json", "").replace("```", "").strip()

            # 尝试修复常见的JSON格式问题
            try:
                answer_dict = json.loads(json_content)
            except json.JSONDecodeError as e:
                # 尝试修复多行字符串问题
                import re
                # 使用正则表达式查找并修复多行字符串
                fixed_content = re.sub(r':\s*"([^"]*?)(?:\n)([^"]*?)"', r': "\1\\n\2"', json_content)
                fixed_content = re.sub(r'"\s*\n\s*', r'" ', fixed_content)

                try:
                    answer_dict = json.loads(fixed_content)
                    print(f"JSON修复成功: {fixed_content[:100]}...")
                except json.JSONDecodeError:
                    # 如果修复失败，抛出原始错误
                    raise e

            # 确保返回字典包含 solution 字段
            if "solution" not in answer_dict:
                return "错误: 答案格式错误：缺少 solution 字段"

            # 返回原始 JSON 字符串
            return json.dumps(answer_dict, ensure_ascii=False, indent=2)

        except json.JSONDecodeError as e:
            # 如果 JSON 解析失败，返回错误
            return f"错误: 无法解析答案格式。错误信息: {str(e)}。原始内容：{json_content}"

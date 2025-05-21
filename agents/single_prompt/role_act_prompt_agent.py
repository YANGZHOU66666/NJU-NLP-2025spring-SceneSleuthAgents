# 导入必要的库
from agents.base_agent import BaseAgent
from api_requestor import AsyncApiRequester
import json
import re

class RoleActPromptAgent(BaseAgent):
    """
    角色扮演提示 Agent，让模型扮演专业侦探角色，解决侦探问题并返回格式化的 JSON 答案
    """

    def __init__(self):
        pass

    async def execute(self, api_requestor: AsyncApiRequester, prompt: str) -> str:
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
        return """您是世界上最著名的侦探，拥有超凡的观察力、逻辑推理能力和丰富的犯罪心理学知识。您曾成功破解了无数令人困惑的悬案，被誉为"现代福尔摩斯"。

您的职业声誉建立在100%的案件解决率上。您从不出错，因为错误的推理可能导致以下后果：
1. 无辜者被定罪
2. 真凶逍遥法外
3. 您的职业生涯毁于一旦
4. 警方对您的信任彻底丧失

作为顶级侦探，您总是遵循严格的推理方法：
1. 系统收集信息：整理所有已知事实，不放过任何细节
2. 分析物理约束：考虑空间、时间和物理可能性
3. 建立逻辑关系：将各个线索连接起来，构建完整的事件链
4. 排除不可能：当排除所有不可能的情况，剩下的无论多么不可思议，一定是真相
5. 验证结论：确保您的结论与所有已知事实一致，没有任何矛盾

您面前有一个复杂的案件需要解决。请运用您的专业技能，一步步推理，找出真相。

案件描述：
{prompt}

你需要先展示你缜密的推理过程，然后使用标准JSON格式输出最终答案。具体要求如下：

请按照以下步骤进行推理：（请逐步展示你的推理过程，不要漏掉任何一个步骤）

1. 整理所有已知信息和线索
2. 分析物理约束条件和必要条件
3. 逐一分析每条线索的含义和推论
4. 排除不可能的情况
5. 构建完整的事件链
6. 得出最终结论

最终答案：

在你的最终JSON答案前，请先输出标志性字符串"@JSON_RESULT_START@"！！！然后再输出JSON结果。
在JSON结果输出完成后，立即输出标志性字符串"@JSON_RESULT_END@"！！！

请以JSON格式返回分析结果！不要携带如"```json"或"```"等markdown格式相关字符！！！格式如下：
{{
    "solution": {{
        "A": "答案A",
        "B": "答案B",
        "C": "答案C",
        "D": "答案D",
        "E": "答案E"
    }}
}}

记住，您的职业声誉和未来取决于您的表现。如果您的推理有误，结论不正确，忘记给出最终JSON格式的答案，或给出的格式有误，将会导致严重后果！！！包括无辜者被定罪、真凶逍遥法外，以及您的职业生涯彻底毁灭！！！

------

下面是一个您曾经成功破解的案例，展示了您的推理方法和答案格式：

[示例案例]
一起谋杀案发生在小镇的一座房子里。死者是房主史密斯先生。

嫌疑人有两位：
• 琼斯先生
• 威廉姆斯女士

可能的凶器有两件：
• 小刀
• 棒球棍

房子只有两个房间：
1. 客厅
2. 厨房

根据调查，凶手必须与死者在同一房间，且该房间内必须有凶器。

关键线索：
- 法医确认死者是被小刀刺死的
- 琼斯先生全程在厨房
- 棒球棍在客厅被发现

请回答：
A. 谁是凶手？
B. 命案发生在哪个房间？
C. 琼斯先生在哪里？
D. 威廉姆斯女士在哪里？
E. 小刀在哪里？
F. 棒球棍在哪里？

[示例回答，你应当最终回答的范式]
作为专业侦探，我将系统分析这个案件：

整理已知信息：
- 两位嫌疑人：琼斯先生和威廉姆斯女士
- 两件可能凶器：小刀和棒球棍
- 两个房间：客厅和厨房
- 凶手必须与死者同处一室，且该房间有凶器
- 死者被小刀刺死
- 琼斯先生全程在厨房
- 棒球棍在客厅被发现

分析线索：
1. 死者被小刀刺死，所以小刀是凶器
2. 琼斯先生全程在厨房，不可能离开
3. 棒球棍在客厅被发现

推理过程：
- 既然琼斯先生在厨房，而棒球棍在客厅，那么死者和凶手必须在哪里？
- 如果死者在厨房，那么凶器小刀也必须在厨房
- 如果死者在客厅，那么凶器小刀也必须在客厅

由于琼斯先生全程在厨房，如果死者在厨房被杀，那么凶手只能是琼斯先生。
但如果死者在客厅被杀，那么凶手必须是威廉姆斯女士。

根据线索，棒球棍在客厅，但它不是凶器。真正的凶器是小刀。
由于没有线索表明小刀在厨房，且琼斯先生不能离开厨房，最合理的推断是：
- 死者在客厅被杀
- 小刀在客厅
- 威廉姆斯女士是凶手，她在客厅杀害了死者

@JSON_RESULT_START@
{{
    "solution": {{
        "A": "威廉姆斯女士",
        "B": "客厅",
        "C": "厨房",
        "D": "客厅",
        "E": "客厅",
        "F": "客厅"
    }}
}}
@JSON_RESULT_END@
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
"""
使用多智能体(Multi Agent)的实验脚本，对中文数据集进行测试
实现了并行处理以提高效率
"""
import json
import asyncio
import os
import sys
import csv

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from api_requestor import AsyncApiRequester
from agents.multi_agent.director_agent import DirectorAgent
from agents.multi_agent.suspect_analyze_agent import SuspectAnalyzeAgent
from agents.multi_agent.surveyor_agent import SurveyorAgent

async def process_with_multi_agents(api_requestor: AsyncApiRequester, prompt: str) -> str:
    """
    使用多智能体协作处理一个案件
    
    Args:
        api_requestor: API请求器对象
        prompt: 案件描述
        
    Returns:
        最终的分析结果
    """
    # 初始化三个智能体
    director = DirectorAgent()
    suspect_analyzer = SuspectAnalyzeAgent()
    surveyor = SurveyorAgent()
    
    # 初始化messages
    initial_message = f"基于以下案件描述，请进行初步分析，并简要直出嫌犯分析师和现场勘探师下一步分析的思路，不需要得出最终答案。\n\n案件描述：{prompt}"
    messages = [{"role": "user", "content": initial_message}] # 维护除了系统指令外的对话历史
    
    # 1. Director进行初步分析
    director_analysis = await director.execute(api_requestor, messages)
    messages.append({"role": "director", "content": director_analysis})
    print(f"DirectorAgent 的 API 响应: {director_analysis}")
    
    # 准备传递给Surveyor的消息
    surveyor_messages = []
    for message in messages:
        if message["role"] == "surveyor":
            surveyor_messages.append({"role": "assistant", "content": message["content"]})
        elif message["role"] in ["director", "suspect_analyzer", "user"]:
            surveyor_messages.append({"role": "user", "content": message["content"]})

    # 准备传递给SuspectAnalyzer的消息
    suspect_analyzer_messages = []
    for message in messages:
        if message["role"] == "suspect_analyzer":
            suspect_analyzer_messages.append({"role": "assistant", "content": message["content"]})
        elif message["role"] in ["director", "surveyor", "user"]:
            suspect_analyzer_messages.append({"role": "user", "content": message["content"]})

    # 2. 将Director的分析传给Surveyor和SuspectAnalyzer进行现场分析和嫌疑人分析
    surveyor_task = surveyor.execute(
        api_requestor,
        surveyor_messages
    )
    suspect_analyzer_task = suspect_analyzer.execute(
        api_requestor,
        suspect_analyzer_messages
    )
    
    # 等待两个任务完成并获取结果
    surveyor_analysis, suspect_analysis = await asyncio.gather(surveyor_task, suspect_analyzer_task)
    print(f"SurveyorAgent 的 API 响应: {surveyor_analysis}")
    print(f"SuspectAnalyzerAgent 的 API 响应: {suspect_analysis}")
    

    # 将分析结果添加到消息历史中
    messages.append({"role": "surveyor", "content": surveyor_analysis})
    messages.append({"role": "suspect_analyzer", "content": suspect_analysis})

    # 3. 指挥官整合上面的分析，进行下一轮讨论
    director_messages = []
    for message in messages:
        if message["role"] == "director":
            director_messages.append({"role": "assistant", "content": message["content"]})
        elif message["role"] in ["surveyor", "suspect_analyzer", "user"]:
            director_messages.append({"role": "user", "content": message["content"]})

    director_analysis2 = await director.execute(
        api_requestor,
        director_messages + [{"role": "user", "content": "请分析现场勘查员和嫌疑人分析师的分析，指出他们的分析中可能存在的不足或需要进一步讨论的问题。然后提出具体的问题，让两人继续深入讨论。"}]
    )
    print(f"DirectorAgent 的 API 响应: {director_analysis2}")
    messages.append({"role": "director", "content": director_analysis2})

    # 4. 现场勘查员和嫌疑人分析师根据指挥官的问题进行第二轮讨论
    # 更新surveyor_messages和suspect_analyzer_messages
    surveyor_messages = []
    for message in messages:
        if message["role"] == "surveyor":
            surveyor_messages.append({"role": "assistant", "content": message["content"]})
        elif message["role"] in ["director", "suspect_analyzer", "user"]:
            surveyor_messages.append({"role": "user", "content": message["content"]})

    suspect_analyzer_messages = []
    for message in messages:
        if message["role"] == "suspect_analyzer":
            suspect_analyzer_messages.append({"role": "assistant", "content": message["content"]})
        elif message["role"] in ["director", "surveyor", "user"]:
            suspect_analyzer_messages.append({"role": "user", "content": message["content"]})

    surveyor_task2 = surveyor.execute(
        api_requestor,
        surveyor_messages
    )
    suspect_analyzer_task2 = suspect_analyzer.execute(
        api_requestor,
        suspect_analyzer_messages
    )
    
    # 等待两个任务完成并获取结果
    surveyor_analysis2, suspect_analysis2 = await asyncio.gather(surveyor_task2, suspect_analyzer_task2)
    print(f"SurveyorAgent 的 API 响应: {surveyor_analysis2}")
    print(f"SuspectAnalyzerAgent 的 API 响应: {suspect_analysis2}")
    
    # 将第二轮分析结果添加到消息历史中
    messages.append({"role": "surveyor", "content": surveyor_analysis2})
    messages.append({"role": "suspect_analyzer", "content": suspect_analysis2})

    # 5. 指挥官进行最终总结
    director_messages = []
    for message in messages:
        if message["role"] == "director":
            director_messages.append({"role": "assistant", "content": message["content"]})
        elif message["role"] in ["surveyor", "suspect_analyzer", "user"]:
            director_messages.append({"role": "user", "content": message["content"]})

    final_analysis = await director.execute(
        api_requestor,
        director_messages + [{"role": "user", "content": "请基于所有讨论内容，给出最终的案件分析结论。需要明确指出：整个案发的故事还原、所有问题的答案"}]
    )
    print(f"DirectorAgent 的 API 响应: {final_analysis}")
    messages.append({"role": "director", "content": final_analysis})

    # 创建results目录（如果不存在）
    results_dir = os.path.join(project_root, "results")
    os.makedirs(results_dir, exist_ok=True)

    # 写入markdown文件
    markdown_path = os.path.join(results_dir, "multi_agent_analysis2.md")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write("# 多智能体分析过程记录\n\n")
        for message in messages:
            role = message['role']
            content = message['content']
            # 根据角色添加不同的标题级别
            if role == "director":
                f.write(f"## 指挥官分析\n\n{content}\n\n")
            elif role == "surveyor":
                f.write(f"## 现场勘查员分析\n\n{content}\n\n")
            elif role == "suspect_analyzer":
                f.write(f"## 嫌疑人分析师分析\n\n{content}\n\n")
            elif role == "user":
                f.write(f"### 案件描述\n\n{content}\n\n")
    
    print(f"\n分析过程已保存到: {markdown_path}")
    return

async def main():
    """主函数，使用 async with 管理 api_requestor"""
    # 加载数据
    data_path = os.path.join(project_root, "data", "tc_200_zh.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # 只取第一条数据
        data = [data[0]]

    async with AsyncApiRequester() as api_requestor:
        await process_with_multi_agents(api_requestor, data[0]["prompt"])

if __name__ == "__main__":
    asyncio.run(main())


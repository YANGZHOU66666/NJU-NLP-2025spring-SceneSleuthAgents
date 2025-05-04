import json
import asyncio
from agents.data_analyze.data_analyze_agent import DataAnalyzeAgent
from api_requestor import AsyncApiRequester

async def main():
    """主函数，使用 async with 管理 api_requestor"""
    # 使用 async with 创建和管理 api_requestor
    async with AsyncApiRequester() as api_requestor:
        # 加载数据
        with open('data/tc_200_zh.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取第一个 prompt
        first_prompt = data[0].get('prompt', '')
        
        # 初始化 agent
        agent = DataAnalyzeAgent()
        
        # 调用 agent 进行分析
        try:
            result = await agent.call_api(api_requestor, first_prompt)
            print("分析结果:")
            print(f"矩形平面图: {result.get('is_rectangular', False)}")
            print(f"多个时间节点: {result.get('has_multiple_time_nodes', False)}")
            print(f"时间节点无移动限制: {result.get('has_time_nodes_without_restriction', False)}")
            print(f"有杀人动机: {result.get('has_murder_motives', False)}")
            print(f"多个可选凶器: {result.get('has_multiple_weapons', False)}")
            
            if 'error' in result:
                print(f"错误信息: {result['error']}")
        except Exception as e:
            print(f"分析出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())

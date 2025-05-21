# 数据探索性分析，实际效果不好
import json
import asyncio
import csv
from typing import Dict, List
from agents.data_analyze.data_analyze_agent import DataAnalyzeAgent
from api_requestor import AsyncApiRequester

def load_data(file_path: str) -> List[Dict]:
    """加载JSON数据文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_results_to_csv(results: List[Dict], file_path: str):
    """将分析结果保存到CSV文件
    
    Args:
        results: 分析结果列表
        file_path: CSV文件路径
    """
    # 定义CSV文件的表头
    fieldnames = [
        'sample_index',
        'is_rectangular',
        'has_multiple_time_nodes',
        'has_time_nodes_without_restriction',
        'has_murder_motives',
        'has_multiple_weapons'
    ]
    
    # 写入CSV文件
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n分析结果已保存到: {file_path}")

async def analyze_samples(api_requestor: AsyncApiRequester, n_samples: int = 10):
    """分析指定数量的中文样本
    
    Args:
        api_requestor: API 请求器对象
        n_samples: 要分析的样本数量，默认为10
    """
    # 加载中文数据
    zh_data = load_data('data/tc_200_zh.json')
    
    # 确保请求的样本数量不超过数据总量
    n_samples = min(n_samples, len(zh_data))
    
    # 初始化统计计数器
    stats = {
        "is_rectangular": 0,
        "has_multiple_time_nodes": 0,
        "has_time_nodes_without_restriction": 0,
        "has_murder_motives": 0,
        "has_multiple_weapons": 0,
        "total": 0
    }
    
    # 初始化 agent
    agent = DataAnalyzeAgent()
    
    print(f"\n" + "="*50)
    print(f"前{n_samples}条中文样本分析")
    print("="*50 + "\n")
    
    # 创建任务列表
    tasks = []
    
    # 为每个样本创建分析任务
    for i, sample in enumerate(zh_data[:n_samples], 1):
        # 创建分析任务
        task = asyncio.create_task(agent.execute(api_requestor, sample.get('prompt', '')))
        tasks.append((i, task))
    
    # 存储所有分析结果
    all_results = []
    
    # 等待所有任务完成
    for i, task in tasks:
        try:
            result = await task
            
            # 更新统计
            if result.get('is_rectangular', False):
                stats['is_rectangular'] += 1
            if result.get('has_multiple_time_nodes', False):
                stats['has_multiple_time_nodes'] += 1
            if result.get('has_time_nodes_without_restriction', False):
                stats['has_time_nodes_without_restriction'] += 1
            if result.get('has_murder_motives', False):
                stats['has_murder_motives'] += 1
            if result.get('has_multiple_weapons', False):
                stats['has_multiple_weapons'] += 1
            stats['total'] += 1
            
            # 存储当前样本的分析结果
            sample_result = {
                'sample_index': i,
                'is_rectangular': result.get('is_rectangular', False),
                'has_multiple_time_nodes': result.get('has_multiple_time_nodes', False),
                'has_time_nodes_without_restriction': result.get('has_time_nodes_without_restriction', False),
                'has_murder_motives': result.get('has_murder_motives', False),
                'has_multiple_weapons': result.get('has_multiple_weapons', False)
            }
            all_results.append(sample_result)
            
            print(f"\n样本 {i} 分析结果:")
            print(f"矩形平面图: {result.get('is_rectangular', False)}")
            print(f"多个时间节点: {result.get('has_multiple_time_nodes', False)}")
            print(f"时间节点无移动限制: {result.get('has_time_nodes_without_restriction', False)}")
            print(f"有杀人动机: {result.get('has_murder_motives', False)}")
            print(f"多个可选凶器: {result.get('has_multiple_weapons', False)}")
            
            if 'error' in result:
                print(f"错误信息: {result['error']}")
            
        except Exception as e:
            print(f"\n样本 {i} 分析出错: {str(e)}")
    
    # 打印统计结果
    print("\n统计结果:")
    print("="*30)
    print(f"总样本数: {stats['total']}")
    if stats['total'] > 0:
        print(f"矩形平面图比例: {stats['is_rectangular']/stats['total']*100:.2f}%")
        print(f"多个时间节点比例: {stats['has_multiple_time_nodes']/stats['total']*100:.2f}%")
        print(f"时间节点无移动限制比例: {stats['has_time_nodes_without_restriction']/stats['total']*100:.2f}%")
        print(f"有杀人动机比例: {stats['has_murder_motives']/stats['total']*100:.2f}%")
        print(f"多个可选凶器比例: {stats['has_multiple_weapons']/stats['total']*100:.2f}%")
    else:
        print("没有成功分析的样本")
    
    # 保存分析结果到CSV文件
    if all_results:
        save_results_to_csv(all_results, f'analysis_results_{n_samples}_samples.csv')

async def main():
    """主函数，使用 async with 管理 api_requestor"""
    # 使用 async with 创建和管理 api_requestor
    async with AsyncApiRequester() as api_requestor:
        # 获取用户输入的样本数量
        while True:
            try:
                n = input("请输入要查看的样本数量（默认10）: ").strip()
                if not n:  # 如果用户直接回车，使用默认值
                    n = 10
                else:
                    n = int(n)
                    if n <= 0:
                        print("请输入大于0的数字！")
                        continue
                break
            except ValueError:
                print("请输入有效的数字！")
        
        # 运行分析
        await analyze_samples(api_requestor, n)

if __name__ == "__main__":
    asyncio.run(main())

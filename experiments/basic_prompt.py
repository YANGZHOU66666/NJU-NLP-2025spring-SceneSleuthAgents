"""
使用基本提示(Basic Prompt)的实验脚本，对中文数据集进行测试
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
from agents.single_prompt.basic_prompt_agent import BasicPromptAgent
from utils import evaluate_response

async def process_samples(api_requestor: AsyncApiRequester, data: list, n_samples: int = None,
                      hooks: dict = None, max_print_length: int = 200):
    """
    并行处理样本

    Args:
        api_requestor: API 请求器对象
        data: 数据集
        n_samples: 要处理的样本数量，默认为None表示处理所有样本
        hooks: 钩子函数字典，可包含 'on_task_complete', 'on_task_error' 等
        max_print_length: 打印LLM响应时的最大长度

    Returns:
        处理结果列表和统计信息
    """
    # 如果指定了样本数量，则只处理指定数量的样本
    if n_samples is not None:
        data = data[:n_samples]

    total_samples = len(data)

    # 初始化 agent
    agent = BasicPromptAgent()

    # 初始化钩子函数
    if hooks is None:
        hooks = {}

    # 默认钩子函数
    default_hooks = {
        'on_task_complete': lambda i, response, *args:
            print(f"\n样本 {i} 完成 - 准确率: {'正确' if args[-1] == 1 else '错误'}\n"
                  f"LLM响应: {response[:max_print_length]}{'...' if len(response) > max_print_length else ''}"),
        'on_task_error': lambda i, error:
            print(f"\n样本 {i} 处理出错: {str(error)}")
    }

    # 合并默认钩子和用户提供的钩子
    for key, func in default_hooks.items():
        if key not in hooks:
            hooks[key] = func

    print(f"\n" + "="*50)
    print(f"开始处理 {total_samples} 条样本")
    print("="*50 + "\n")

    # 创建任务列表
    tasks = []

    # 为每个样本创建处理任务
    for i, sample in enumerate(data, 1):
        # 创建处理任务
        task = asyncio.create_task(agent.execute(api_requestor, sample["prompt"]))
        tasks.append((i, task, sample))

    # 存储所有处理结果
    results = []
    correct_count = 0

    print(f"\n开始处理 {total_samples} 个样本...")

    # 等待所有任务完成
    for i, task, sample in tasks:
        try:
            print(f"\n处理样本 {i}/{total_samples}...")
            model_response = await task

            # 评估回答
            accuracy = evaluate_response(model_response, sample["solution"])

            if accuracy == 1:
                correct_count += 1

            # 保存结果
            results.append({
                "prompt": sample["prompt"],
                "response": model_response,
                "solution": sample["solution"],
                "accuracy": accuracy
            })

            # 调用任务完成钩子
            if 'on_task_complete' in hooks:
                hooks['on_task_complete'](i, model_response, sample.get("solution", ""), accuracy)

        except Exception as e:
            # 调用任务错误钩子
            if 'on_task_error' in hooks:
                hooks['on_task_error'](i, e)

            results.append({
                "prompt": sample["prompt"],
                "error": str(e),
                "solution": sample["solution"],
                "accuracy": 0
            })

    print(f"\n所有样本处理完成!")

    # 计算总体准确率
    accuracy = correct_count / total_samples if total_samples > 0 else 0

    # 打印统计结果
    print("\n统计结果:")
    print("="*30)
    print(f"总样本数: {total_samples}")
    print(f"正确数量: {correct_count}")
    print(f"准确率: {accuracy:.2%}")

    return results, {
        "total_samples": total_samples,
        "correct_count": correct_count,
        "accuracy": accuracy,
        "model": "Basic Prompt Agent"
    }

async def main():
    """主函数，使用 async with 管理 api_requestor"""
    # 加载数据
    data_path = os.path.join(project_root, "data", "tc_200_zh.json")
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 创建输出目录
    output_dir = os.path.join(project_root, "results")
    os.makedirs(output_dir, exist_ok=True)

    # 处理全部数据
    n_samples = None
    print("将处理中文数据集的全部数据...")

    # 设置LLM响应的最大打印长度
    max_print_length = 200
    print(f"LLM响应的最大打印长度设置为: {max_print_length}")

    # 定义自定义钩子函数
    hooks = {
        'on_task_complete': lambda i, response, *args:
            print(f"\n{'='*30}\n样本 {i} 完成 - 准确率: {'✓ 正确' if args[-1] == 1 else '✗ 错误'}\n"
                  f"LLM响应: {response[:max_print_length]}{'...' if len(response) > max_print_length else ''}\n{'='*30}"),
        'on_task_error': lambda i, error:
            print(f"\n{'='*30}\n样本 {i} ❌ 处理出错: {str(error)}\n{'='*30}")
    }

    # 使用 async with 创建和管理 api_requestor
    async with AsyncApiRequester() as api_requestor:
        # 处理样本
        results, statistics = await process_samples(api_requestor, data, n_samples, hooks, max_print_length)

        # 保存JSON结果
        output_json_file = os.path.join(output_dir, "basic_200_zh_output.json")
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump({
                "results": results,
                "statistics": statistics
            }, f, ensure_ascii=False, indent=2)

        print(f"\n结果已保存到: {output_json_file}")

        # 保存CSV结果
        output_csv_file = os.path.join(output_dir, "basic_prompt_result.csv")
        with open(output_csv_file, "w", encoding="utf-8", newline="") as f:
            csv_writer = csv.writer(f)
            # 写入表头
            csv_writer.writerow(["样本ID", "正确/错误", "原始问题", "模型答案"])

            # 写入数据
            for i, result in enumerate(results, 1):
                # 确定状态
                if "error" in result:
                    status = "错误"
                elif result.get("accuracy", 0) == 1:
                    status = "正确"
                else:
                    status = "错误"

                # 获取原始问题和模型答案
                prompt = result.get("prompt", "")
                response = result.get("response", "")

                # 写入行
                csv_writer.writerow([i, status, prompt, response])

        print(f"CSV结果已保存到: {output_csv_file}")

if __name__ == "__main__":
    asyncio.run(main())

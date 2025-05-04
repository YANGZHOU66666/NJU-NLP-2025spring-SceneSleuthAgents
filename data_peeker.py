import json
import sys
from typing import Dict, List

def load_data(file_path: str) -> List[Dict]:
    """加载JSON数据文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def print_sample(sample: Dict, index: int):
    """打印单个样本的内容"""
    print(f"\n{'='*50}")
    print(f"样本 {index} 内容:")
    print(f"{'='*50}\n")
    
    # 打印 prompt
    print("Prompt:")
    print("-"*30)
    print(sample.get('prompt', ''))
    print()

def main():
    """主函数，用于查看数据"""
    # 加载数据
    try:
        data = load_data('data/tc_200_zh.json')
    except Exception as e:
        print(f"加载数据失败: {str(e)}")
        sys.exit(1)
    
    total_samples = len(data)
    print(f"数据总共有 {total_samples} 个样本")
    
    while True:
        try:
            # 获取用户输入的起始和结束索引
            start = input("\n请输入起始索引（0开始）: ").strip()
            if not start:  # 如果用户直接回车，使用默认值
                start = 0
            else:
                start = int(start)
                if start < 0 or start >= total_samples:
                    print(f"起始索引必须在 0 到 {total_samples-1} 之间！")
                    continue
            
            end = input("请输入结束索引（不包含）: ").strip()
            if not end:  # 如果用户直接回车，使用默认值
                end = min(start + 5, total_samples)
            else:
                end = int(end)
                if end <= start or end > total_samples:
                    print(f"结束索引必须在 {start+1} 到 {total_samples} 之间！")
                    continue
            
            # 显示指定范围内的样本
            for i in range(start, end):
                print_sample(data[i], i)
            
            # 询问是否继续
            choice = input("\n是否继续查看其他样本？(y/n): ").strip().lower()
            if choice != 'y':
                break
                
        except ValueError:
            print("请输入有效的数字！")
        except KeyboardInterrupt:
            print("\n程序已退出")
            break
        except Exception as e:
            print(f"发生错误: {str(e)}")
            break

if __name__ == "__main__":
    main()

# 南京大学人工智能学院 25春 自然语言处理课程 第二次课程设计

## 项目结构

```
.
├── agents/                      # 智能体模块
│   ├── base_agent.py           # 智能体基类
│   ├── multi_agent/            # 多智能体系统
│   │   ├── director_agent.py   # 指挥官智能体
│   │   ├── surveyor_agent.py   # 现场勘查员智能体
│   │   └── suspect_analyze_agent.py  # 嫌疑人分析师智能体
│   ├── single_prompt/          # 单prompt系统
│   │   ├── basic_prompt_agent.py    # 基础prompt智能体
│   │   ├── cot_prompt_agent.py      # 思维链prompt智能体
│   │   └── role_act_prompt_agent.py # 角色扮演prompt智能体
│   └── data_analyze/           # 用于数据分析的智能体
│       └── data_analyze_agent.py # 数据分析智能体
│
├── data/                       # 数据集目录
│   └── tc_200_zh.json         # 中文测试数据集
│
├── experiments/                # 实验脚本
│   ├── multi_agent.py         # 多智能体实验
│   ├── basic_prompt.py        # 基础prompt实验
│   ├── cot_prompt.py          # 思维链prompt实验
│   └── role_act_prompt.py     # 角色扮演prompt实验
│
├── results/                    # 实验结果
│   ├── multi_agent_analysis.md  # 多智能体分析记录（三轮讨论，效果不好）
│   ├── multi_agent_analysis2.md # 多智能体分析记录（两轮讨论）
│   └── basic_prompt_result.csv  # 基础提示实验结果
│
├── utils/                      # 工具函数
│   └── evaluate.py            # 评估函数
│
├── api_requestor.py           # 中央API请求器
├── data_peeker.py             # 数据查看器
└── README.md                  # 项目说明文档
```
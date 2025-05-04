import requests
import json

url = "https://api.siliconflow.cn/v1/chat/completions"

def add(a, b):
    """
    计算两个数的和
    """
    return a + b

def sub(a, b):
    """
    计算两个数的差
    """
    return a - b

def process_tool_call(response):
    # 解析响应
    response_data = json.loads(response.text)
    
    # 获取工具调用信息
    tool_call = response_data['choices'][0]['message']['tool_calls'][0]
    function_name = tool_call['function']['name']
    arguments = json.loads(tool_call['function']['arguments'])
    
    # 执行对应的函数
    if function_name == 'add':
        result = add(arguments['a'], arguments['b'])
    elif function_name == 'sub':
        result = sub(arguments['a'], arguments['b'])
    
    # 构造新的请求，包含工具调用结果
    new_payload = {
        "model": "THUDM/GLM-4-32B-0414",
        "messages": [
            {
                "role": "user",
                "content": "What is the sum of 1 and 2?"
            },
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [tool_call]
            },
            {
                "role": "tool",
                "content": str(result),
                "tool_call_id": tool_call['id']
            }
        ],
        "stream": False,
        "max_tokens": 512,
        "temperature": 0.7
    }
    
    # 发送新的请求
    new_response = requests.request("POST", url, json=new_payload, headers=headers)
    return new_response

payload = {
    "model": "THUDM/GLM-4-32B-0414",
    "messages": [
        {
            "role": "user",
            "content": "What is the sum of 1 and 2?"
        }
    ],
    "stream": False,
    "max_tokens": 512,
    "enable_thinking": False,
    "thinking_budget": 512,
    "min_p": 0.05,
    "stop": None,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "response_format": {"type": "text"},
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "add",
                "parameters": {"a": 1, "b": 2}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "sub",
                "parameters": {"a": 1, "b": 2}
            }
        }
    ]
}
headers = {
    "Authorization": "Bearer sk-vyimxjdmfvqsclztnnzuikgknwvleeglcoubomcbotiwlziq",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

# 如果响应包含工具调用，则处理工具调用
if 'tool_calls' in json.loads(response.text)['choices'][0]['message']:
    final_response = process_tool_call(response)
    print(final_response.text)
else:
    print(response.text)
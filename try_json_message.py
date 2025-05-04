import requests
import json

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "THUDM/GLM-4-32B-0414",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful programmer."
        },
        {
            "role": "user",
            "content": "introduce json to me"
        },
    ],
    "stream": False,
    "max_tokens": 4096,
    "enable_thinking": False,
    "thinking_budget": 4096,
    "min_p": 0.05,
    "stop": None,
    "temperature": 0.7,
    "top_p": 0.7,
    "top_k": 50,
    "frequency_penalty": 0.5,
    "n": 1,
    "response_format": {"type": "text"},
    "tools": []
}
headers = {
    "Authorization": "Bearer sk-vyimxjdmfvqsclztnnzuikgknwvleeglcoubomcbotiwlziq",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

# 将返回值转为json对象并美化打印
response_json = response.json()
print(json.dumps(response_json, ensure_ascii=False, indent=2))
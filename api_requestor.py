import asyncio
import aiohttp
import random

from typing import Dict, Any, List, Optional

class AsyncApiRequester:
    def __init__(self, 
                 model: str = "deepseek-ai/DeepSeek-V3",
                 max_tokens: int = 8192,
                 temperature: float = 0.7,
                 top_p: float = 0.7,
                 top_k: int = 50,
                 frequency_penalty: float = 0.5,
                 n: int = 1,
                 response_format: Dict = {"type": "text"},
                 max_concurrent: int = 10,
                 max_retries: int = 20,
                 api_token: Optional[str] = 'sk-vyimxjdmfvqsclztnnzuikgknwvleeglcoubomcbotiwlziq'):
        self.base_payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "frequency_penalty": frequency_penalty,
            "n": n,
            "response_format": response_format,
            "stream": False,
            "enable_thinking": False,
            "thinking_budget": 512,
            "min_p": 0.05,
            "stop": None
        }
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.task_queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._scheduler_task = None
        self.api_token = api_token
        self.session = None
        self._active_tasks = set()

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        self._scheduler_task = asyncio.create_task(self._scheduler())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        await self.stop()

    async def call_api(self, messages: List[Dict], tools: Optional[List[Dict]] = None) -> asyncio.Future:
        """对外接口，自动判断直接请求还是入队，返回Future对象"""
        payload = self.base_payload.copy()
        payload["messages"] = messages
        if tools:
            payload["tools"] = tools
            
        future = asyncio.Future()
        if len(self._active_tasks) >= self.max_concurrent:
            # 没空位，入队
            await self._enqueue_task(payload, future)
        else:
            # 有空位，直接请求
            task = asyncio.create_task(self._do_request(payload, future))
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)
        return future

    async def _do_request(self, payload: Dict[str, Any], future: asyncio.Future):
        """实际请求和重试逻辑"""
        try:
            for attempt in range(1, self.max_retries + 1):
                try:
                    print(f"[协程{asyncio.current_task().get_name()}] 开始请求: {payload['messages'][0]['content'][:30]}..., 尝试第{attempt}次")
                    print('='*50)
                    
                    headers = {
                        "Authorization": f"Bearer {self.api_token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with self.session.post(
                        "https://api.siliconflow.cn/v1/chat/completions",
                        json=payload,
                        headers=headers
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            future.set_result(result)
                            print(f"[协程{asyncio.current_task().get_name()}] 请求成功")
                            break
                        else:
                            error_text = await response.text()
                            raise Exception(f"API请求失败: {response.status} - {error_text}")
                            
                except Exception as e:
                    print(f"请求失败（第{attempt}次）: {e}")
                    if attempt == self.max_retries:
                        print("已达最大重试次数，放弃该请求")
                        future.set_exception(e)
                    else:
                        await asyncio.sleep(2 ** min(attempt, 5))  # 指数退避
        finally:
            # 请求完成后，尝试从队列中取出下一个请求
            await self._schedule_next()

    async def _enqueue_task(self, payload: Dict[str, Any], future: asyncio.Future):
        """入队"""
        await self.task_queue.put((payload, future))
        print("请求已加入队列，等待调度")

    async def _scheduler(self):
        """调度器协程，持续监控队列"""
        while not self._stop_event.is_set():
            try:
                if not self.task_queue.empty() and len(self._active_tasks) < self.max_concurrent:
                    payload, future = await self.task_queue.get()
                    task = asyncio.create_task(self._do_request(payload, future))
                    self._active_tasks.add(task)
                    task.add_done_callback(self._active_tasks.discard)
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"调度器错误: {e}")
                await asyncio.sleep(1)

    async def _schedule_next(self):
        """请求完成后尝试调度队列中的下一个请求"""
        if not self.task_queue.empty() and len(self._active_tasks) < self.max_concurrent:
            payload, future = await self.task_queue.get()
            task = asyncio.create_task(self._do_request(payload, future))
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)

    async def stop(self):
        """优雅关闭调度器"""
        if self._scheduler_task:
            self._stop_event.set()
            await self._scheduler_task
            # 等待所有活动任务完成
            if self._active_tasks:
                await asyncio.gather(*self._active_tasks, return_exceptions=True)

# 示例问题列表
QUESTIONS = [
    "1. What opportunities and challenges will the Chinese large model industry face in 2025?",
    "2. How will AI impact the future of education?",
    "3. What are the key differences between traditional machine learning and deep learning?",
    "4. How can we ensure the ethical use of AI in society?",
    "5. What are the main challenges in developing multilingual AI models?",
    "6. How will quantum computing affect the field of AI?",
    "7. What role will AI play in climate change solutions?",
    "8. How can we improve AI model interpretability?",
    "9. What are the security concerns in AI systems?",
    "10. How will AI change the job market in the next decade?"
]

async def handle_result(future):
    """处理单个请求的结果"""
    try:
        result = await future
        print(f"请求成功:")
        print(f"回答: {result.get('choices', [{}])[0].get('message', {}).get('content', '')}")
        print("-" * 50)
    except Exception as e:
        print(f"请求失败: {str(e)}")
        print("-" * 50)

async def main():
    async with AsyncApiRequester() as requester:
        tasks = []
        
        # 模拟真实场景，随机间隔发送请求
        for i, question in enumerate(QUESTIONS):
            # 随机等待0.1-1秒
            await asyncio.sleep(random.uniform(0.1, 1.0))
            
            messages = [
                {
                    "role": "user",
                    "content": question
                }
            ]
            
            print(f"发送第{i+1}个请求: {question[:30]}...")
            future = await requester.call_api(messages)
            # 为每个future添加回调
            asyncio.create_task(handle_result(future))
            tasks.append(future)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    asyncio.run(main())

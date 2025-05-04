from abc import ABC, abstractmethod
from typing import Any
from api_requestor import AsyncApiRequester

class BaseAgent(ABC):
    """
    所有 agent 的抽象基类
    """
    
    @abstractmethod
    def call_api(self, api_requestor: AsyncApiRequester, *args, **kwargs) -> Any:
        """
        调用 API 的抽象方法
        
        Args:
            api_requestor: API 请求器对象
            *args: 可变位置参数
            **kwargs: 可变关键字参数
            
        Returns:
            API 调用的返回结果
        """
        pass

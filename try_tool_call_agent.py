from agents.tool_call.tool_call_agent import ToolCallAgent
from api_requestor import AsyncApiRequester
import asyncio

async def main():
    async with AsyncApiRequester() as api_requestor:
        agent = ToolCallAgent()
        result = await agent.execute(api_requestor, """
冬夜深沉，雪花无声地落在都铎庄园的尖顶上。富可敌国却行踪神秘的约翰·Q·博迪先生，正在宅邸里举办一场小型但奢华的晚宴，邀请了几位最亲密的伙伴。然而，当黎明的第一缕光线穿透云层时，博迪先生被发现陈尸于宅中一隅。

警方锁定了两位嫌疑人：

• 布鲁内特先生
• 怀特夫人

凶器可能是以下两种之一：

• 左轮手枪
• 绳索

命案现场只可能位于以下两个房间之一：

1. 大厅
2. 马车房

房间布局如下：

  北  
西 1 东
西 2 东
  南  

根据现场勘查，凶手必须与博迪先生单独处于某个房间，且该房间内至少有一件凶器。

关键线索缓缓浮出水面：

- 博迪先生曾在大厅出现，或者布鲁内特先生曾在大厅出现
- 致命伤来自左轮手枪
- 布鲁内特先生当时所在的位置，恰好在绳索所在房间的正南方

请回答以下问题：

A. 真凶是谁？
B. 命案发生在哪个房间？

以及以下延伸问题：

C. 怀特夫人在何处？
D. 布鲁内特先生在何处？
E. 左轮手枪在何处？
F. 绳索在何处？

请按以下格式提交答案：

A. 嫌疑人
B. 房间
C. 房间
D. 房间
E. 房间
F. 房间

祝您好运，侦探。""")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
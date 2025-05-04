from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, FunctionMessage, AIMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from typing import Annotated, Sequence, TypedDict, List, Dict, Any
import functools, json, os

# 1. 安装与配置工具
os.environ['TAVILY_API_KEY'] = "<Your_Tavily_API_Key>"
os.environ['SILICONFLOW_API_KEY'] = "sk-vyimxjdmfvqsclztnnzuikgknwvleeglcoubomcbotiwlziq"
os.environ['SILICONFLOW_API_BASE'] = "https://api.siliconflow.cn/v1"

tavily_tool = TavilySearchResults(max_results=5)
repl = PythonREPL()

@tool
def python_repl(code: Annotated[str, "要执行的 Python 代码"]):
    """
    执行给定的 Python 代码并返回结果。
    
    Args:
        code: 要执行的 Python 代码字符串
        
    Returns:
        执行结果或错误信息
    """
    try:
        result = repl.run(code)
    except Exception as e:
        return f"执行失败: {e!r}"
    return f"执行成功:\\n```python\n{code}\n```\\n输出：{result}"

tools = [tavily_tool, python_repl]

# 2. 定义状态类型
class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    sender: str

# 3. 创建工具节点
tool_node = ToolNode(tools)

# 4. 路由器节点
def router(state):
    last = state["messages"][-1]
    if isinstance(last, dict) and "function_call" in last.get("additional_kwargs", {}):
        return "call_tool"
    if isinstance(last, dict) and "content" in last and "FINAL ANSWER" in last["content"]:
        return "end"
    if len(state["messages"]) > 10:  # 添加最大消息数限制
        return "end"
    return "continue"

# 5. 生成 Agent 工厂函数
def create_agent(llm, tools, system_msg):
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.utils.function_calling import convert_to_openai_function
    funcs = [convert_to_openai_function(t) for t in tools]
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_msg),
        MessagesPlaceholder(variable_name="messages")
    ]).partial(tool_names=", ".join([t.name for t in tools]))
    return prompt | llm.bind_tools(funcs)

# 使用硅基流动的模型
llm = ChatOpenAI(
    model="THUDM/GLM-4-32B-0414",
    temperature=0,
    openai_api_key=os.environ['SILICONFLOW_API_KEY'],
    openai_api_base=os.environ['SILICONFLOW_API_BASE']
)

research_agent = create_agent(llm, [tavily_tool], "请准确查找并输出数据。")
chart_agent    = create_agent(llm, [python_repl], "请生成可执行的绘图代码。")

# 6. 包装为节点函数
def agent_node(state, agent, name):
    out = agent.invoke(state)
    if isinstance(out, FunctionMessage): 
        msg = out.dict()
    else:
        msg = HumanMessage(**out.dict(exclude={"type","name"}), name=name).dict()
    return {"messages": [msg], "sender": name}

research_node = functools.partial(agent_node, agent=research_agent, name="Researcher")
chart_node    = functools.partial(agent_node, agent=chart_agent,    name="ChartGenerator")

# 7. 组装 StateGraph
workflow = StateGraph(AgentState)
workflow.add_node("Researcher", research_node)
workflow.add_node("ChartGenerator", chart_node)
workflow.add_node("call_tool", tool_node)
workflow.add_conditional_edges("Researcher", router, {"continue":"ChartGenerator", "call_tool":"call_tool", "end":END})
workflow.add_conditional_edges("ChartGenerator", router, {"continue":"Researcher", "call_tool":"call_tool", "end":END})
workflow.add_conditional_edges("call_tool", lambda s: s["sender"], {"Researcher":"Researcher","ChartGenerator":"ChartGenerator"})
workflow.set_entry_point("Researcher")

# 8. 编译并执行工作流
graph = workflow.compile()
for step in graph.stream(
    {"messages":[{"role": "user", "content": "请获取过去五年马来西亚GDP并绘制折线图。"}], "sender": "Researcher"},
    {"recursion_limit": 5},  # 限制递归深度
):
    print(step)
    print("----")

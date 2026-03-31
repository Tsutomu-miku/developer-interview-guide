# Agent 架构面试指南

AI Agent（智能体）是当前大语言模型应用的最重要方向之一。Agent 能够自主感知环境、制定计划、调用工具并根据反馈迭代优化，远超传统的 "输入-输出" 对话模式。本章全面覆盖 Agent 的核心概念、架构设计、记忆系统、规划能力、多 Agent 协作以及主流框架的深入解析。

---

## 1. Agent 定义与核心组件

### 1.1 什么是 AI Agent

AI Agent 是一个以大语言模型（LLM）为核心推理引擎的自主系统，它能够：
- **感知**外部环境（接收用户输入、观察工具返回结果）
- **思考**并制定行动计划（推理、规划、分解任务）
- **行动**执行具体操作（调用工具、API、生成文本）
- **反思**评估结果并调整策略

### 1.2 核心组件

```
Agent = LLM（大脑） + Memory（记忆） + Planning（规划） + Tools（工具）
```

| 组件 | 职责 | 类比 |
|------|------|------|
| LLM | 核心推理与决策引擎 | 大脑 |
| Memory | 存储历史信息和经验 | 记忆系统 |
| Planning | 分解任务、制定计划 | 前额叶皮层 |
| Tools | 与外部世界交互的能力 | 双手 |

> **面试题：AI Agent 和普通的 LLM 对话有什么根本区别？**
>
> 核心区别在于**自主性和行动能力**：
> 1. **目标驱动 vs 响应驱动**：Agent 围绕目标自主规划和执行一系列步骤，普通对话仅对单个输入做出响应
> 2. **工具使用**：Agent 可以调用搜索引擎、执行代码、操作数据库等，普通对话只能生成文本
> 3. **迭代循环**：Agent 在 "思考-行动-观察" 循环中反复迭代直到达成目标，普通对话是一次性的
> 4. **记忆管理**：Agent 维护结构化的记忆系统，普通对话仅依赖上下文窗口
> 5. **错误恢复**：Agent 能根据失败反馈调整策略，普通对话无法自我纠正

---

## 2. Agent 工作流程

### 2.1 核心循环：Perception → Planning → Action → Observation

```python
class SimpleAgent:
    def __init__(self, llm, tools, memory):
        self.llm = llm
        self.tools = tools
        self.memory = memory
    
    def run(self, task):
        self.memory.add("user", task)
        
        while not self.is_task_complete():
            # 1. Perception - 感知当前状态
            context = self.memory.get_context()
            
            # 2. Planning - 思考下一步行动
            thought = self.llm.think(context)
            
            # 3. Action - 执行行动
            if thought.requires_tool:
                result = self.execute_tool(thought.tool_name, thought.tool_args)
            else:
                result = thought.final_answer
            
            # 4. Observation - 观察结果
            self.memory.add("observation", result)
        
        return self.memory.get_final_answer()
```

### 2.2 ReAct 执行模式

ReAct 是当前最主流的 Agent 执行模式，交替进行推理（Thought）和行动（Action）：

```
用户: 帮我查一下北京明天的天气，如果会下雨就提醒我带伞

Thought: 我需要查询北京明天的天气信息
Action: weather_api(city="北京", date="明天")
Observation: 北京明天多云转小雨，气温15-22°C，降水概率70%

Thought: 天气预报显示明天有小雨，降水概率70%，我需要提醒用户带伞
Action: 生成最终回答
Answer: 北京明天的天气是多云转小雨，气温15-22°C。降水概率较高（70%），建议您明天出门记得带伞。
```

> **面试题：ReAct 模式相比纯推理（CoT）和纯行动有什么优势？**
>
> **纯推理（CoT）的问题**：模型只能利用内部知识，无法获取最新信息或执行操作，容易产生幻觉。
> **纯行动的问题**：盲目调用工具，缺乏策略性，可能做很多无用操作。
> **ReAct 的优势**：(1) Thought 步骤让模型在行动前显式推理，提高决策质量；(2) Action 的 Observation 结果为后续推理提供了真实依据，减少幻觉；(3) 交替进行使得模型能够根据观察动态调整策略；(4) 中间推理过程可解释性强，方便调试。

---

## 3. 规划能力

### 3.1 Task Decomposition（任务分解）

将复杂任务分解为多个可执行的子任务：

```python
decomposition_prompt = """
你是一个任务规划专家。请将以下复杂任务分解为具体的执行步骤：

任务：{task}

请按以下格式输出：
1. [子任务1] - 预期输出
2. [子任务2] - 预期输出
...

注意：
- 每个子任务应该是原子性的，可以独立执行
- 子任务之间的依赖关系要明确
- 优先执行没有依赖的子任务
"""
```

### 3.2 规划策略

**Plan-and-Execute**：先生成完整计划，再逐步执行。适合结构化、步骤清晰的任务。

```
Plan:
1. 搜索相关论文
2. 阅读论文摘要
3. 提取关键发现
4. 对比不同论文观点
5. 生成综述报告

Execute: 按顺序执行每一步
```

**动态规划（Adaptive Planning）**：执行过程中根据中间结果动态调整计划。

**分层规划（Hierarchical Planning）**：高层计划定义宏观方向，低层计划处理具体细节。

> **面试题：Plan-and-Execute 和 ReAct 有什么区别？各适用于什么场景？**
>
> **Plan-and-Execute**：先制定完整计划再执行。优点是全局视角好、执行路径清晰；缺点是计划可能因中间结果变化而失效。适合步骤相对确定的任务（如数据处理流程、报告生成）。
>
> **ReAct**：边想边做，每一步根据观察决定下一步。优点是灵活适应变化、能处理不确定性；缺点是可能缺乏全局规划、容易陷入局部循环。适合探索性强的任务（如信息检索、调试问题）。
>
> **实际应用**中常结合使用：先用 Plan-and-Execute 制定大致计划，每一步的执行用 ReAct 模式，同时支持根据执行结果 Re-plan（重新规划）。

---

## 4. 记忆系统

### 4.1 短期记忆（Short-term / Working Memory）

- 本质是**对话上下文窗口**中的信息
- 包含当前对话历史、中间推理步骤、工具返回结果
- 受 context window 大小限制
- 生命周期：单次对话/任务

### 4.2 长期记忆（Long-term Memory）

存储跨对话/跨会话的持久信息：

```python
class LongTermMemory:
    def __init__(self, vector_store):
        self.vector_store = vector_store
    
    def store(self, content, metadata=None):
        """将信息存入长期记忆"""
        embedding = embed(content)
        self.vector_store.add(
            embedding=embedding,
            text=content,
            metadata={
                "timestamp": datetime.now(),
                "type": metadata.get("type", "general"),
                **metadata
            }
        )
    
    def retrieve(self, query, top_k=5, filters=None):
        """从长期记忆中检索相关信息"""
        return self.vector_store.search(
            query_embedding=embed(query),
            top_k=top_k,
            filters=filters
        )
```

### 4.3 向量存储记忆

将对话历史、任务结果等编码为向量存储在向量数据库中，查询时检索最相关的记忆片段。适合大量历史信息的场景。

### 4.4 对话缓冲记忆（Conversation Buffer Memory）

```python
# LangChain 对话缓冲记忆
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(return_messages=True)
memory.save_context(
    {"input": "我叫张三"},
    {"output": "你好，张三！有什么可以帮助你的？"}
)
# 直接保留完整对话历史，简单但占用 token 多
```

### 4.5 摘要记忆（Summary Memory）

```python
from langchain.memory import ConversationSummaryMemory

memory = ConversationSummaryMemory(llm=llm)
# 将对话历史压缩为摘要
# "用户自我介绍为张三，是一名Python开发者，正在开发一个RAG系统"
```

### 4.6 实体记忆（Entity Memory）

提取和维护对话中出现的实体信息：

```python
# 存储结构
entities = {
    "张三": "用户本人，Python开发者，在开发RAG系统",
    "RAG系统": "用户正在开发的项目，使用Pinecone作为向量数据库",
    "Pinecone": "向量数据库，用户已经部署了"
}
```

> **面试题：Agent 的记忆系统应该如何设计？不同类型的记忆如何配合使用？**
>
> 采用**分层记忆架构**：
> 1. **工作记忆（L1）**：当前对话的最近 N 轮，保持在 context window 中，用于即时推理
> 2. **会话记忆（L2）**：当前会话的完整历史，超出 context window 部分用摘要压缩或向量存储
> 3. **长期记忆（L3）**：跨会话的持久信息，存储在向量数据库中，按需检索
> 4. **结构化记忆（L4）**：实体关系、用户画像等结构化信息，存储在关系数据库中
>
> **配合策略**：每次推理时，L1 完整注入上下文；L2 按相关性检索部分注入；L3 只在需要时检索（如用户提到过去的对话）；L4 作为 System Prompt 的一部分持续生效。

---

## 5. 反思机制

### 5.1 Reflexion

Agent 在任务执行后对自身表现进行反思，生成改进建议存入记忆，指导未来行为：

```
任务结果：代码执行失败，IndexError: list index out of range

Reflexion: 
- 我在处理列表时没有检查边界条件
- 下次处理列表操作时，应该先验证列表长度
- 应该在关键步骤添加异常处理

将此反思存入长期记忆，下次遇到类似任务时检索使用
```

### 5.2 Self-Critique

在生成最终输出前进行自我批评和修正：

```python
critique_prompt = """
请审查以下回答是否存在问题：

原始问题：{question}
回答：{answer}

检查项：
1. 事实准确性：是否有错误的信息？
2. 完整性：是否遗漏了重要内容？
3. 逻辑性：推理过程是否合理？
4. 格式：是否符合要求的输出格式？

如果发现问题，请指出并给出修正后的回答。
"""
```

> **面试题：反思机制如何提升 Agent 的性能？实现上有哪些挑战？**
>
> **提升方式**：(1) 从错误中学习——将失败经验存为记忆，避免重复犯错；(2) 质量把关——生成后自我审查，减少低质量输出；(3) 策略优化——分析多次执行的模式，优化决策策略。
>
> **挑战**：(1) LLM 的自我评估能力有限，可能无法准确识别自身错误（自我评估偏差）；(2) 反思增加了推理成本和延迟；(3) 反思记忆的管理——过多的历史反思可能引入噪音；(4) 需要设计何时触发反思的策略，不能每步都反思。

---

## 6. 单 Agent 架构设计

### 6.1 基础架构

```python
class Agent:
    def __init__(self, llm, tools, memory, system_prompt):
        self.llm = llm
        self.tools = {t.name: t for t in tools}
        self.memory = memory
        self.system_prompt = system_prompt
        self.max_iterations = 10
    
    def run(self, user_input):
        self.memory.add_message("user", user_input)
        
        for i in range(self.max_iterations):
            # 构造 prompt
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.memory.get_messages()
            ]
            
            # LLM 推理
            response = self.llm.chat(messages, tools=self.get_tool_schemas())
            
            # 判断是否调用工具
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    result = self.tools[tool_call.name].execute(tool_call.args)
                    self.memory.add_message("tool", result, tool_call_id=tool_call.id)
            else:
                # 最终回答
                self.memory.add_message("assistant", response.content)
                return response.content
        
        return "达到最大迭代次数，任务未完成"
```

### 6.2 关键设计决策

1. **迭代上限**：防止无限循环，通常设置 5-15 次
2. **退出条件**：LLM 决定不再调用工具时视为完成
3. **错误处理**：工具执行失败时将错误信息反馈给 LLM
4. **成本控制**：记录 token 消耗，设置预算上限

---

## 7. 多 Agent 系统

### 7.1 协作模式

**层级模式（Hierarchical）**：

```
       ┌─────────────┐
       │  Supervisor  │  (管理者Agent)
       └──────┬───────┘
         ┌────┼────┐
    ┌────┴──┐ │ ┌──┴────┐
    │Worker1│ │ │Worker3│  (执行者Agent)
    └───────┘ │ └───────┘
          ┌───┴───┐
          │Worker2│
          └───────┘
```

管理者 Agent 负责分配任务、监督进度和整合结果。每个 Worker Agent 专注于特定领域。

**对等模式（Peer-to-Peer）**：

所有 Agent 地位平等，通过消息传递协作。适合需要协商和讨论的场景。

**辩论模式（Debate）**：

多个 Agent 对同一问题给出不同观点，通过辩论达成共识或由仲裁者决策。

### 7.2 通信协议

```python
# Agent 之间的消息格式
class AgentMessage:
    sender: str        # 发送者Agent名称
    receiver: str      # 接收者Agent名称
    content: str       # 消息内容
    message_type: str  # 类型：task/result/question/feedback
    metadata: dict     # 附加信息
```

### 7.3 冲突解决

当多个 Agent 意见不一致时：
- **投票机制**：多数表决
- **权重投票**：根据 Agent 的专业性赋予不同权重
- **仲裁者**：由专门的 Supervisor Agent 做最终决策
- **协商轮次**：限制辩论轮次，超时则采用最高置信度的答案

> **面试题：多 Agent 系统相比单 Agent 有什么优势和挑战？**
>
> **优势**：(1) **专业化分工**——每个 Agent 专注于擅长的领域，整体能力更强；(2) **并行执行**——独立子任务可同时进行，提高效率；(3) **鲁棒性**——单个 Agent 失败不影响整体系统；(4) **可扩展性**——添加新能力只需增加新 Agent。
>
> **挑战**：(1) **通信开销**——Agent 之间的消息传递增加延迟和 token 消耗；(2) **协调复杂性**——任务分配、进度同步、冲突解决需要额外设计；(3) **一致性维护**——确保多个 Agent 对共享状态的理解一致；(4) **调试困难**——问题可能出在任何 Agent 或它们之间的交互中；(5) **成本**——多个 LLM 调用的成本远高于单 Agent。

---

## 8. LangChain 框架详解

### 8.1 核心概念

**Chain**：将多个处理步骤串联的管道：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

# LCEL (LangChain Expression Language) 语法
prompt = ChatPromptTemplate.from_template("翻译以下文本为{language}：{text}")
llm = ChatOpenAI(model="gpt-4o")
output_parser = StrOutputParser()

chain = prompt | llm | output_parser
result = chain.invoke({"language": "英文", "text": "你好世界"})
```

**Agent**：具有工具调用和推理能力的自主系统：

```python
from langchain.agents import create_tool_calling_agent, AgentExecutor

agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = agent_executor.invoke({"input": "北京今天天气怎么样？"})
```

**Memory**：管理对话历史和状态：

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=10)  # 保留最近10轮
```

**Tool**：Agent 可调用的外部能力：

```python
from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    """搜索互联网获取最新信息"""
    return web_search_api(query)
```

**Callback**：用于日志、追踪、流式输出的钩子机制：

```python
from langchain.callbacks import StdOutCallbackHandler
agent_executor.invoke({"input": "..."}, config={"callbacks": [StdOutCallbackHandler()]})
```

### 8.2 LangChain 的优缺点

> **面试题：你如何评价 LangChain？它适合什么场景？**
>
> **优点**：(1) 丰富的集成——支持数百个 LLM、向量数据库、工具的连接器；(2) 快速原型——可以几十行代码搭建 RAG/Agent；(3) 社区活跃——文档多、示例多。
>
> **缺点**：(1) 过度抽象——太多封装层导致调试困难，出错时难以定位问题；(2) API 不稳定——频繁breaking changes；(3) 性能开销——封装引入额外延迟；(4) 黑盒问题——Chain 内部行为不透明。
>
> **适合场景**：快速原型验证、概念验证（PoC）。生产环境建议根据复杂度决定：简单应用可直接用 OpenAI SDK；复杂 Agent 用 LangGraph；需要极致可控性则自建框架。

---

## 9. LangGraph

LangGraph 是 LangChain 团队推出的 Agent 编排框架，基于图（Graph）结构定义 Agent 的控制流。

### 9.1 核心概念

- **State（状态）**：在图中流转的数据，类似于"全局变量"
- **Node（节点）**：执行具体操作的函数
- **Edge（边）**：定义节点之间的流转关系
- **Conditional Edge（条件边）**：根据状态决定下一个节点

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    next_action: str

def reasoning_node(state: AgentState) -> AgentState:
    """推理节点：决定下一步行动"""
    response = llm.invoke(state["messages"])
    if response.tool_calls:
        return {"messages": [response], "next_action": "tool"}
    return {"messages": [response], "next_action": "end"}

def tool_node(state: AgentState) -> AgentState:
    """工具执行节点"""
    tool_calls = state["messages"][-1].tool_calls
    results = [execute_tool(tc) for tc in tool_calls]
    return {"messages": results, "next_action": "reason"}

def should_continue(state: AgentState) -> str:
    """条件路由"""
    if state["next_action"] == "end":
        return END
    return "tool"

# 构建图
graph = StateGraph(AgentState)
graph.add_node("reason", reasoning_node)
graph.add_node("tool", tool_node)
graph.set_entry_point("reason")
graph.add_conditional_edges("reason", should_continue, {"tool": "tool", END: END})
graph.add_edge("tool", "reason")

app = graph.compile()
result = app.invoke({"messages": [HumanMessage(content="你好")]})
```

### 9.2 LangGraph 的优势

1. **可视化**：图结构可以直观地展示 Agent 的控制流
2. **可控性**：显式定义状态转移，避免黑盒行为
3. **Human-in-the-Loop**：在关键节点插入人工审核
4. **持久化**：支持状态持久化，Agent 可以暂停和恢复
5. **流式输出**：支持节点级别的 streaming

> **面试题：LangGraph 和传统的 LangChain Agent 有什么区别？什么场景下应该使用 LangGraph？**
>
> 传统 LangChain Agent 是**线性循环**（think → act → observe → think...），控制流由 LLM 自行决定，缺乏显式的状态管理。LangGraph 是**图结构**，开发者显式定义状态、节点和转移条件，对流程有完全控制。
>
> **使用 LangGraph 的场景**：(1) 复杂工作流——有分支、循环、并行的场景；(2) 需要 Human-in-the-Loop——在关键决策点需要人工确认；(3) 多 Agent 协作——不同 Agent 作为不同节点；(4) 需要状态持久化——支持长时间运行的任务；(5) 需要可观测性——清晰的执行路径便于调试和审计。

---

## 10. CrewAI 框架

CrewAI 专注于多 Agent 角色扮演和协作：

```python
from crewai import Agent, Task, Crew

# 定义 Agent
researcher = Agent(
    role="高级研究分析师",
    goal="发现AI领域最新的突破性技术",
    backstory="你是一名经验丰富的技术研究员...",
    tools=[search_tool, web_scraper],
    llm=llm
)

writer = Agent(
    role="技术内容作者",
    goal="将研究发现转化为易懂的文章",
    backstory="你是一名擅长科技写作的资深编辑...",
    llm=llm
)

# 定义任务
research_task = Task(
    description="研究2024年最重要的AI突破",
    agent=researcher,
    expected_output="详细的研究报告"
)

writing_task = Task(
    description="基于研究报告撰写一篇科普文章",
    agent=writer,
    context=[research_task],  # 依赖研究任务的输出
    expected_output="一篇800字的科普文章"
)

# 组建团队
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    verbose=True
)

result = crew.kickoff()
```

CrewAI 的特点是用"角色扮演"的方式定义 Agent，每个 Agent 有明确的角色、目标和背景故事，以及支持灵活的任务依赖和委托机制。

---

## 11. AutoGen 框架

Microsoft 的 AutoGen 专注于多 Agent 对话式协作：

```python
from autogen import AssistantAgent, UserProxyAgent

assistant = AssistantAgent(
    name="助手",
    llm_config={"model": "gpt-4o"},
    system_message="你是一个有帮助的AI助手。"
)

user_proxy = UserProxyAgent(
    name="用户代理",
    human_input_mode="NEVER",  # ALWAYS / TERMINATE / NEVER
    code_execution_config={"work_dir": "coding"}
)

# 自动对话执行
user_proxy.initiate_chat(
    assistant,
    message="用Python分析这个CSV文件的销售趋势"
)
```

AutoGen 的特点是通过 Agent 之间的自动对话来完成任务，支持代码执行和人机交互。

---

## 12. OpenAI Assistants API

OpenAI 的 Assistants API 提供了托管式的 Agent 能力：

```python
from openai import OpenAI
client = OpenAI()

# 创建 Assistant
assistant = client.beta.assistants.create(
    name="数据分析师",
    instructions="你是一个数据分析专家，善于用Python分析数据。",
    tools=[
        {"type": "code_interpreter"},
        {"type": "file_search"}
    ],
    model="gpt-4o"
)

# 创建 Thread（对话线程）
thread = client.beta.threads.create()

# 添加消息
client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="请分析这份销售数据"
)

# 运行 Assistant
run = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant.id
)
```

特点：托管式记忆管理、内置 Code Interpreter 和 File Search、支持 Function Calling。

> **面试题：比较 LangGraph、CrewAI、AutoGen 和 OpenAI Assistants API 的适用场景。**
>
> | 框架 | 最佳场景 | 优势 | 劣势 |
> |------|---------|------|------|
> | LangGraph | 复杂工作流、需要精确控制流程 | 可控性强、支持持久化 | 学习曲线陡 |
> | CrewAI | 多角色协作、创意类任务 | 直观的角色定义、简单易用 | 对精确控制支持较弱 |
> | AutoGen | 多Agent对话、代码相关任务 | 自动对话机制、代码执行 | 调试较困难 |
> | Assistants API | 快速上线、托管运维 | 零运维、内置工具 | 供应商锁定、定制性有限 |

---

## 13. Agent 评估与调试

### 13.1 评估维度

1. **任务完成率**：Agent 能否成功完成指定任务
2. **步骤效率**：完成任务所需的步骤数（LLM 调用次数）
3. **工具使用准确率**：是否选择了正确的工具和参数
4. **最终答案质量**：答案的准确性、完整性、相关性
5. **鲁棒性**：面对异常输入和工具错误时的表现
6. **成本**：Token 消耗和 API 调用费用

### 13.2 调试工具

- **LangSmith**：LangChain 官方追踪平台，可视化每步执行
- **Phoenix (Arize)**：开源可观测性工具
- **Verbose/Debug 模式**：打印每步 Thought/Action/Observation
- **断点调试**：在 LangGraph 中设置检查点

> **面试题：Agent 在生产环境中常见的失败模式有哪些？如何预防？**
>
> 1. **无限循环**：Agent 反复执行相同操作 → 设置最大迭代次数，检测重复行为
> 2. **工具调用错误**：参数格式错误、工具不可用 → 严格的参数校验、优雅降级
> 3. **规划偏差**：分解的子任务不合理 → 使用 Plan-and-Replan 策略
> 4. **幻觉行为**：编造工具名或参数 → 限制工具列表、严格校验 tool_call
> 5. **成本失控**：复杂任务消耗大量 token → 设置预算上限和早停机制
> 6. **安全风险**：Agent 执行了不应该执行的操作 → 权限控制、敏感操作人工确认

---

## 总结

Agent 架构是 LLM 应用从"对话"走向"行动"的关键转变。面试中需要展示对 Agent 核心概念（感知-规划-行动-观察循环）、记忆系统设计、规划策略、多 Agent 协作模式的深入理解，以及对主流框架（LangChain/LangGraph/CrewAI/AutoGen）的实践经验。重点是能够根据实际业务需求选择合适的架构和框架，并预见和解决生产环境中的常见问题。

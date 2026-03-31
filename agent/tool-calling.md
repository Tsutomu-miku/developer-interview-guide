# 工具调用与 Function Calling 面试指南

工具调用（Tool Calling / Function Calling）是 AI Agent 区别于普通对话模型的核心能力。它使 LLM 能够与外部世界交互——搜索信息、执行代码、查询数据库、调用 API 等。本章全面覆盖 Function Calling 的原理、实现、工具编排、MCP 协议、安全性以及生产环境中的设计模式。

---

## 1. Function Calling 原理

### 1.1 工作流程

Function Calling 是一个 LLM 与外部工具之间的结构化交互协议：

```
1. 开发者定义工具（函数签名 + JSON Schema 描述）
2. 用户提出问题
3. LLM 判断是否需要调用工具
4. 如果需要，LLM 生成结构化的函数调用请求（函数名 + 参数）
5. 应用程序执行实际的函数调用
6. 将执行结果返回给 LLM
7. LLM 基于结果生成最终回答
```

**关键认知**：LLM 本身不执行函数——它只是生成"我想调用什么函数、传什么参数"的结构化指令。实际的函数执行由应用程序完成。

### 1.2 底层原理

模型在训练阶段学习了大量函数调用的模式数据。当提供工具定义后，模型将工具描述信息编码到上下文中，在生成过程中有两个选择：

1. **生成普通文本**：直接回答用户问题
2. **生成特殊的 tool_call 结构**：指定要调用的函数名和参数

模型通过分析用户意图和可用工具的描述来决定是否调用工具、调用哪个工具以及使用什么参数。

> **面试题：Function Calling 和直接让 LLM 生成代码有什么区别？为什么需要 Function Calling 机制？**
>
> 1. **结构化 vs 非结构化**：Function Calling 输出的是严格的 JSON 结构（函数名+参数），可以被程序可靠解析；让 LLM 生成代码则是自由文本，解析不稳定。
> 2. **安全性**：Function Calling 由开发者预定义了工具列表，LLM 只能在给定工具中选择；自由生成代码可能产生任意危险操作。
> 3. **可控性**：开发者完全控制函数的实际实现——LLM 只负责"决定调用什么"，实际执行由受控环境完成。
> 4. **可靠性**：参数类型、必需字段等通过 JSON Schema 约束，减少格式错误。
> 5. **解耦性**：工具实现可以独立更新，不影响 LLM 的使用方式。

---

## 2. OpenAI Function Calling API

### 2.1 完整示例

```python
from openai import OpenAI
import json

client = OpenAI()

# 1. 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息。当用户询问天气相关问题时调用此函数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "温度单位，默认摄氏度"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# 2. 发起请求
messages = [{"role": "user", "content": "北京今天天气怎么样？"}]
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
    tool_choice="auto"  # auto / none / required / 指定函数
)

# 3. 处理工具调用
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        # 4. 执行实际函数
        if function_name == "get_weather":
            result = get_weather_api(arguments["city"], arguments.get("unit", "celsius"))
        
        # 5. 将结果返回给 LLM
        messages.append(message)  # 添加 assistant 的 tool_call 消息
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    
    # 6. LLM 生成最终回答
    final_response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools
    )
    print(final_response.choices[0].message.content)
```

### 2.2 tool_choice 参数

| 值 | 行为 |
|---|------|
| `"auto"` | 模型自行决定是否调用工具（默认） |
| `"none"` | 强制不调用任何工具 |
| `"required"` | 强制调用至少一个工具 |
| `{"type": "function", "function": {"name": "xxx"}}` | 强制调用指定函数 |

> **面试题：tool_choice 的不同选项分别适用于什么场景？**
>
> - `"auto"`：通用场景，让模型根据用户输入自主判断是否需要工具
> - `"none"`：需要纯文本回答时（如闲聊、总结已有信息），或想在某些步骤中禁止工具调用
> - `"required"`：确定当前步骤一定需要工具调用时（如 Agent 的行动步骤）
> - **指定函数**：知道需要哪个特定工具时，如表单填写后一定要调用提交函数；也用于 Structured Output——将函数定义为数据结构，强制模型输出符合该结构的 JSON

---

## 3. 工具定义

### 3.1 JSON Schema 描述

好的工具定义是 Function Calling 成功的关键。核心要素：

```python
{
    "type": "function",
    "function": {
        "name": "search_database",
        "description": """搜索产品数据库。
        
使用场景：当用户询问产品信息、价格、库存等问题时调用。
不要在用户只是闲聊或询问非产品相关问题时调用此函数。

返回格式：JSON数组，每个元素包含产品名称、价格和库存状态。""",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索关键词，如产品名称、类别、品牌"
                },
                "category": {
                    "type": "string",
                    "enum": ["电子产品", "服装", "食品", "家居", "其他"],
                    "description": "产品类别筛选"
                },
                "price_range": {
                    "type": "object",
                    "properties": {
                        "min": {"type": "number", "description": "最低价格（元）"},
                        "max": {"type": "number", "description": "最高价格（元）"}
                    },
                    "description": "价格范围筛选"
                },
                "in_stock": {
                    "type": "boolean",
                    "description": "是否只搜索有库存的产品，默认true"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量上限，默认10",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    }
}
```

### 3.2 工具描述最佳实践

1. **函数名**：使用清晰的动词+名词格式（`search_database`、`send_email`、`create_ticket`）
2. **description**：
   - 说明函数做什么
   - 说明什么场景下应该调用
   - 说明什么场景下不应该调用
   - 说明返回值的格式
3. **参数描述**：每个参数都要有清晰的描述和示例
4. **enum 约束**：对有限选项的参数使用 `enum`
5. **必需参数**：只将真正必需的参数放入 `required`

> **面试题：工具的 description 写得好坏会如何影响模型表现？你有什么写作建议？**
>
> description 是 LLM 决定是否调用工具以及如何传参的核心依据。写得差会导致：(1) 该调用时不调用（description 不清晰）；(2) 不该调用时调用（没说明边界）；(3) 参数传错（参数描述模糊）。
>
> **写作建议**：
> 1. 把 description 当作写给人类的 API 文档，清晰描述功能、使用场景和限制
> 2. 为关键参数提供示例值
> 3. 说明函数的副作用（如 "此操作会发送邮件，不可撤销"）
> 4. 如果有多个相似工具，在 description 中明确区分它们的使用条件
> 5. 避免过度简洁——模型需要足够信息来做正确决策

---

## 4. 工具编排

### 4.1 串行调用

按顺序逐个调用工具，后一个工具的输入依赖前一个工具的输出：

```python
# 示例：先搜索用户信息，再查询订单
# Step 1: 搜索用户
user = search_user(name="张三")
# Step 2: 使用用户ID查询订单
orders = get_orders(user_id=user["id"])
# Step 3: 基于订单信息回答
```

### 4.2 并行调用

多个独立的工具调用可以同时执行。OpenAI API 支持模型在一次响应中返回多个 tool_calls：

```python
# 模型可能同时返回多个 tool_calls
response.choices[0].message.tool_calls = [
    ToolCall(id="call_1", function=Function(name="get_weather", arguments='{"city":"北京"}')),
    ToolCall(id="call_2", function=Function(name="get_weather", arguments='{"city":"上海"}')),
]

# 并行执行
import asyncio

async def execute_parallel(tool_calls):
    tasks = [execute_tool(tc) for tc in tool_calls]
    results = await asyncio.gather(*tasks)
    return results
```

### 4.3 嵌套调用

一个工具的实现内部可能需要调用其他工具或触发另一个 Agent：

```python
@tool
def analyze_competitor(company_name: str) -> str:
    """分析竞争对手，内部涉及多个子任务"""
    # 嵌套调用：搜索 → 数据提取 → 分析
    search_results = search_web(f"{company_name} latest news")
    financial_data = query_database(f"SELECT * FROM financials WHERE company='{company_name}'")
    analysis = llm.analyze(search_results, financial_data)
    return analysis
```

> **面试题：如何处理工具之间的依赖关系？如果某个工具调用失败怎么办？**
>
> **依赖管理**：
> 1. **显式依赖图**：构建工具调用的 DAG（有向无环图），并行执行无依赖的节点，串行执行有依赖的节点
> 2. **状态传递**：将前一个工具的输出存入共享状态，后续工具从状态中读取
> 3. **LLM 自主编排**：让 LLM 根据当前观察结果决定下一步调用什么工具
>
> **失败处理**：
> 1. **重试**：对暂时性错误（网络超时、限流）进行指数退避重试（通常 3 次）
> 2. **降级**：提供备选工具或方案（如搜索 API 失败则用缓存数据）
> 3. **反馈给 LLM**：将错误信息返回给 LLM，让它调整策略（更换参数、换另一个工具）
> 4. **优雅终止**：超过重试次数后告知用户部分功能暂时不可用
> 5. **幂等性设计**：对于有副作用的工具（发邮件、下订单），确保重试不会导致重复执行

---

## 5. 常见工具类型

### 5.1 搜索工具

```python
@tool
def web_search(query: str, num_results: int = 5) -> str:
    """搜索互联网获取最新信息。

    Args:
        query: 搜索查询字符串
        num_results: 返回结果数量
    
    Returns:
        搜索结果的标题、摘要和链接
    """
    results = tavily_client.search(query, max_results=num_results)
    return format_search_results(results)
```

### 5.2 代码执行工具

```python
@tool
def execute_python(code: str) -> str:
    """在安全沙箱中执行Python代码。
    
    可以用于数据分析、数学计算、图表生成等。
    代码在隔离环境中运行，超时30秒。
    
    Args:
        code: 要执行的Python代码
    
    Returns:
        代码的标准输出和错误输出
    """
    result = sandbox.run(code, timeout=30)
    return f"stdout: {result.stdout}\nstderr: {result.stderr}"
```

### 5.3 数据库查询工具

```python
@tool
def query_database(sql: str) -> str:
    """执行只读SQL查询。

    仅支持SELECT语句，禁止INSERT/UPDATE/DELETE。
    查询结果限制最多100行。
    
    Args:
        sql: SQL查询语句（仅SELECT）
    
    Returns:
        查询结果的JSON格式
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "错误：仅支持SELECT查询"
    result = db.execute(sql + " LIMIT 100")
    return json.dumps(result, ensure_ascii=False)
```

### 5.4 API 调用工具

```python
@tool
def call_api(endpoint: str, method: str = "GET", body: dict = None) -> str:
    """调用内部REST API。

    Args:
        endpoint: API端点路径（如 /api/users）
        method: HTTP方法（GET/POST）
        body: POST请求体
    
    Returns:
        API响应结果
    """
    response = requests.request(method, BASE_URL + endpoint, json=body, timeout=10)
    return response.json()
```

### 5.5 文件操作工具

```python
@tool
def read_file(file_path: str) -> str:
    """读取文件内容。仅允许读取指定目录下的文件。
    
    Args:
        file_path: 文件路径（相对于工作目录）
    """
    safe_path = os.path.join(WORKSPACE_DIR, file_path)
    if not safe_path.startswith(WORKSPACE_DIR):
        return "错误：不允许访问工作目录外的文件"
    with open(safe_path, 'r') as f:
        return f.read()
```

---

## 6. MCP（Model Context Protocol）协议详解

### 6.1 MCP 是什么

MCP（Model Context Protocol）是 Anthropic 在 2024 年提出的开放标准，旨在标准化 LLM 应用与外部数据源、工具的连接方式。MCP 定义了一套统一的协议，使 AI 应用能够以标准化方式发现和调用工具。

### 6.2 MCP 架构

```
┌─────────────────┐
│   MCP Host       │  (AI 应用，如 Claude Desktop, IDE)
│  ┌─────────────┐ │
│  │  MCP Client  │ │  (协议客户端)
│  └──────┬──────┘ │
└─────────┼────────┘
          │ (MCP协议)
          │
   ┌──────┴──────┐
   │  MCP Server  │  (工具/数据源提供者)
   │ ┌──────────┐ │
   │ │ Resources │ │  (数据资源)
   │ │ Tools     │ │  (可调用工具)
   │ │ Prompts   │ │  (提示模板)
   │ └──────────┘ │
   └─────────────┘
```

### 6.3 MCP 核心概念

- **Resources（资源）**：MCP Server 暴露的数据资源，类似于 REST API 的 GET 端点
- **Tools（工具）**：可执行的操作，由 LLM 决定何时调用
- **Prompts（提示模板）**：预定义的提示模板，可由用户选择使用
- **Sampling（采样）**：Server 可以请求 Client 的 LLM 完成推理

### 6.4 MCP Server 示例

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("weather-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="获取指定城市的天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名称"}
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        weather = await fetch_weather(arguments["city"])
        return [TextContent(type="text", text=json.dumps(weather))]
```

> **面试题：MCP 协议解决了什么问题？它和传统的 Function Calling 有什么关系？**
>
> **解决的问题**：在 MCP 之前，每个 AI 应用需要为每个工具/数据源编写定制的集成代码，形成 M×N 的复杂度。MCP 标准化了连接协议，使得任何 MCP Client 可以连接任何 MCP Server，降为 M+N 的复杂度（类似 USB 协议标准化了设备连接）。
>
> **与 Function Calling 的关系**：Function Calling 是 LLM 层面的能力——模型决定调用什么函数。MCP 是应用层面的协议——标准化工具如何被发现、描述和调用。两者互补：MCP Server 暴露的 Tools 最终通过 Function Calling 机制被 LLM 调用。MCP 还额外提供了 Resources（数据访问）和 Prompts（提示模板）等 Function Calling 不涵盖的能力。

---

## 7. 代码解释器（Code Interpreter）

### 7.1 核心能力

代码解释器允许 Agent 动态生成和执行代码来完成任务：

- **数据分析**：读取 CSV/Excel，进行统计分析
- **数学计算**：精确的数值计算（LLM 直接计算容易出错）
- **图表生成**：使用 matplotlib/plotly 生成可视化图表
- **文件处理**：格式转换、数据清洗

### 7.2 沙箱实现

```python
import subprocess
import tempfile

class CodeSandbox:
    def __init__(self, timeout=30, max_memory="256m"):
        self.timeout = timeout
        self.max_memory = max_memory
    
    def execute(self, code: str) -> dict:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write(code)
            f.flush()
            
            try:
                result = subprocess.run(
                    ["python", f.name],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    # 资源限制
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
                )
                return {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
            except subprocess.TimeoutExpired:
                return {"error": "执行超时", "timeout": self.timeout}
```

> **面试题：Code Interpreter 的沙箱需要考虑哪些安全问题？**
>
> 1. **文件系统隔离**：限制可访问的目录，禁止读取系统文件和敏感数据
> 2. **网络隔离**：禁止或限制网络访问，防止数据外泄
> 3. **资源限制**：CPU 时间、内存、磁盘空间上限，防止资源耗尽（DoS）
> 4. **危险操作禁止**：禁止 `os.system`、`subprocess`、`eval`、`exec` 等（或限制在更深层沙箱内）
> 5. **进程隔离**：使用 Docker 容器或 gVisor 等沙箱技术隔离进程
> 6. **超时控制**：设置执行时间上限（通常 30-60 秒）
> 7. **输出限制**：限制 stdout/stderr 的大小，防止内存溢出
> 8. **包限制**：只允许预装的安全 Python 包

---

## 8. Web 浏览器工具

```python
@tool
def browse_web(url: str, action: str = "read") -> str:
    """浏览网页并提取内容。

    Args:
        url: 要访问的网页URL
        action: 操作类型 - read(读取内容)/screenshot(截图)/click(点击元素)
    
    Returns:
        网页的文本内容或截图
    """
    if action == "read":
        # 使用 headless browser 获取渲染后的内容
        page = browser.goto(url)
        return page.get_text_content(max_length=5000)
    elif action == "screenshot":
        page = browser.goto(url)
        return page.screenshot()
```

Web 浏览器工具使 Agent 能够：
- 访问和阅读网页内容
- 填写表单、点击按钮
- 截取屏幕截图
- 提取结构化数据

---

## 9. 工具选择策略

### 9.1 模型如何选择工具

LLM 根据以下信息选择工具：
1. **用户意图**：分析用户查询的语义
2. **工具描述**：匹配 description 中的使用场景
3. **参数可行性**：判断是否能从上下文中提取所需参数
4. **历史经验**：训练数据中的工具使用模式

### 9.2 优化工具选择

```python
# 策略1：工具数量控制
# 工具过多会导致选择困难和性能下降
# 建议：单次提供不超过 15-20 个工具

# 策略2：工具分组
# 根据任务阶段提供不同的工具子集
def get_tools_for_stage(stage):
    if stage == "research":
        return [web_search, read_document, summarize]
    elif stage == "coding":
        return [code_executor, file_reader, file_writer]
    elif stage == "communication":
        return [send_email, create_ticket, notify]

# 策略3：工具路由
# 用一个轻量级模型先分类意图，再选择工具子集
def route_tools(user_query):
    intent = classifier.predict(user_query)
    return tool_groups[intent]
```

> **面试题：当可用工具数量很多（如 50+）时，如何保证模型选对工具？**
>
> 1. **分层选择**：先用 LLM 或分类器判断大类（搜索 / 数据处理 / 通讯），再在子类中选择具体工具
> 2. **工具检索**：将工具描述向量化，根据用户查询检索最相关的 Top-K 工具，只将这些工具提供给 LLM
> 3. **场景分组**：根据对话阶段或任务类型动态加载工具子集
> 4. **优化描述**：确保每个工具的 description 清晰且有区分度
> 5. **减少冗余**：合并功能相似的工具，用参数区分不同行为
> 6. **两阶段调用**：第一阶段让 LLM 从完整列表中选择工具名，第二阶段只提供选中工具的完整定义

---

## 10. 错误处理与重试机制

### 10.1 错误类型

```python
class ToolError:
    PARSE_ERROR = "参数解析错误"      # LLM 生成了无效的 JSON
    VALIDATION_ERROR = "参数校验错误"  # 参数类型或值不合法
    EXECUTION_ERROR = "执行错误"       # 工具运行时错误
    TIMEOUT_ERROR = "超时错误"         # 工具执行超时
    PERMISSION_ERROR = "权限错误"      # 无权执行该操作
    RATE_LIMIT_ERROR = "限流错误"      # API 调用频率超限
```

### 10.2 重试策略

```python
import time
from functools import wraps

def retry_with_backoff(max_retries=3, base_delay=1, backoff_factor=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutError, ConnectionError) as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (backoff_factor ** attempt)
                    time.sleep(delay)
                except ValueError as e:
                    # 参数错误不重试，直接反馈给 LLM
                    return {"error": str(e), "retry": False}
            return {"error": "超过最大重试次数", "retry": False}
        return wrapper
    return decorator

@retry_with_backoff(max_retries=3)
def execute_tool(tool_name, arguments):
    tool = tool_registry[tool_name]
    validated_args = tool.validate(arguments)
    return tool.execute(validated_args)
```

### 10.3 错误反馈给 LLM

```python
# 将错误信息结构化地返回给 LLM
error_message = {
    "role": "tool",
    "tool_call_id": tool_call.id,
    "content": json.dumps({
        "error": True,
        "error_type": "VALIDATION_ERROR",
        "message": "参数 'date' 的格式应为 YYYY-MM-DD，收到的值为 '明天'",
        "suggestion": "请将日期转换为具体日期格式，如 2024-01-15"
    })
}
```

> **面试题：工具调用失败时，你会如何设计错误处理流程？**
>
> 分层错误处理：
> 1. **预检验**：在调用前验证参数合法性，不合法则直接将错误和修正建议反馈给 LLM
> 2. **可重试错误**：网络超时、限流等暂时性错误，自动指数退避重试（最多 3 次）
> 3. **不可重试错误**：参数错误、权限不足等确定性错误，将详细错误信息和修正建议反馈给 LLM，让它调整参数重试
> 4. **降级方案**：工具持续不可用时启用备选方案（如搜索 API 不可用，使用缓存结果或告知用户）
> 5. **熔断器**：某个工具连续失败超过阈值时暂时禁用，避免浪费 token
> 6. **日志和告警**：记录所有错误，高频错误触发告警

---

## 11. 安全性

### 11.1 工具权限控制

```python
class ToolPermission:
    READ_ONLY = "read_only"       # 只读操作
    READ_WRITE = "read_write"     # 读写操作
    ADMIN = "admin"               # 管理员操作
    DANGEROUS = "dangerous"       # 危险操作（需人工确认）

class SecureToolRegistry:
    def __init__(self):
        self.tools = {}
        self.permissions = {}
    
    def register(self, tool, permission_level):
        self.tools[tool.name] = tool
        self.permissions[tool.name] = permission_level
    
    def execute(self, tool_name, args, user_permission):
        required = self.permissions[tool_name]
        if not self.has_permission(user_permission, required):
            raise PermissionError(f"权限不足：需要 {required}")
        
        if required == ToolPermission.DANGEROUS:
            if not self.get_human_confirmation(tool_name, args):
                return {"error": "用户拒绝执行此操作"}
        
        return self.tools[tool_name].execute(args)
```

### 11.2 输入校验

```python
def validate_tool_input(tool_name, arguments):
    """严格校验工具输入"""
    schema = tool_schemas[tool_name]
    
    # JSON Schema 校验
    jsonschema.validate(arguments, schema)
    
    # 自定义安全校验
    if tool_name == "query_database":
        # SQL 注入防护
        if any(keyword in arguments["sql"].upper() 
               for keyword in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]):
            raise ValueError("仅允许 SELECT 查询")
    
    if tool_name == "read_file":
        # 路径穿越防护
        if ".." in arguments["file_path"]:
            raise ValueError("不允许路径穿越")
```

### 11.3 沙箱执行

对于执行代码或操作文件系统的工具，必须在沙箱中运行：
- **Docker 容器**：进程级隔离
- **gVisor**：系统调用级隔离
- **WASM（WebAssembly）**：轻量级沙箱
- **Firecracker microVM**：虚拟机级隔离

> **面试题：如何防止 Agent 通过工具调用造成安全问题？**
>
> 采用纵深防御策略：
> 1. **最小权限原则**：每个工具只授予完成任务所需的最小权限；数据库工具只允许 SELECT；文件工具只允许访问指定目录
> 2. **输入验证**：所有工具参数经过严格的类型检查和安全校验
> 3. **沙箱隔离**：代码执行在隔离的容器/沙箱中运行
> 4. **人工确认**：高风险操作（发邮件、删除数据、支付）需要人工确认
> 5. **审计日志**：记录所有工具调用的完整日志（who/what/when/result）
> 6. **速率限制**：限制工具调用频率，防止滥用
> 7. **输出过滤**：工具返回结果中过滤敏感信息（密码、token、PII）

---

## 12. 工具注册与发现

### 12.1 工具注册表

```python
class ToolRegistry:
    _instance = None
    
    def __init__(self):
        self.tools = {}
        self.categories = {}
    
    def register(self, tool, category="default", tags=None):
        self.tools[tool.name] = {
            "tool": tool,
            "category": category,
            "tags": tags or [],
            "schema": tool.get_schema(),
            "usage_count": 0,
            "avg_latency": 0
        }
        self.categories.setdefault(category, []).append(tool.name)
    
    def discover(self, query=None, category=None, tags=None):
        """根据条件发现可用工具"""
        candidates = list(self.tools.values())
        if category:
            names = self.categories.get(category, [])
            candidates = [self.tools[n] for n in names]
        if tags:
            candidates = [t for t in candidates if set(tags) & set(t["tags"])]
        if query:
            # 语义匹配工具描述
            candidates = semantic_search(query, candidates)
        return candidates
```

### 12.2 动态工具加载

```python
# 按需加载工具插件
import importlib

def load_tool_plugin(plugin_name):
    module = importlib.import_module(f"tools.{plugin_name}")
    tool = module.create_tool()
    registry.register(tool)
    return tool
```

---

## 13. 实际项目中的工具设计模式

### 13.1 组合工具模式

将多个原子工具组合为高级工具：

```python
@tool
def research_topic(topic: str) -> str:
    """对某个主题进行全面研究。内部组合搜索、阅读、总结等操作。"""
    # 搜索相关文章
    search_results = web_search(topic, num_results=10)
    # 阅读前3篇文章
    contents = [read_webpage(r["url"]) for r in search_results[:3]]
    # 总结要点
    summary = llm.summarize(contents)
    return summary
```

### 13.2 确认工具模式

对有副作用的操作先生成预览，确认后再执行：

```python
@tool
def send_email_preview(to: str, subject: str, body: str) -> str:
    """生成邮件预览，等待用户确认后发送"""
    return f"准备发送邮件：\n收件人：{to}\n主题：{subject}\n正文：{body}\n\n请确认是否发送？"

@tool
def send_email_confirm(email_id: str) -> str:
    """确认并发送已预览的邮件"""
    email = pending_emails[email_id]
    return smtp.send(email)
```

### 13.3 幂等工具模式

确保工具多次调用不会产生重复副作用：

```python
@tool
def create_order(order_id: str, items: list) -> str:
    """创建订单（幂等操作：相同order_id只创建一次）"""
    existing = db.get_order(order_id)
    if existing:
        return f"订单 {order_id} 已存在，无需重复创建"
    return db.create_order(order_id, items)
```

> **面试题：请设计一个实际场景中的工具集合（如客服 Agent），并解释你的设计思路。**
>
> 客服 Agent 工具集合设计：
>
> | 工具名 | 功能 | 权限级别 |
> |--------|------|----------|
> | search_knowledge_base | 搜索知识库/FAQ | 只读 |
> | get_user_info | 查询用户基本信息 | 只读 |
> | get_order_status | 查询订单状态 | 只读 |
> | create_ticket | 创建工单 | 读写 |
> | transfer_to_human | 转接人工客服 | 读写 |
> | apply_refund | 申请退款 | 危险（需确认） |
> | send_notification | 发送通知 | 读写 |
>
> **设计思路**：(1) 按权限分级——只读工具自由使用，写入工具需记录，危险操作需确认；(2) 职责单一——每个工具只做一件事；(3) 降级路径——复杂问题转接人工；(4) 幂等设计——create_ticket 使用唯一 ID 防止重复创建。

---

## 总结

工具调用是 Agent 从 "能说" 到 "能做" 的关键桥梁。面试中需要展示对 Function Calling 完整流程的理解（定义 → 调用 → 解析 → 执行 → 反馈）、工具设计的最佳实践（清晰描述、参数校验、错误处理）、MCP 等新兴标准的认知、以及安全性的纵深防御思路。在实际项目中，工具的设计质量直接决定了 Agent 的可靠性和安全性。

# 浏览器原理面试指南

> 浏览器是前端开发最重要的运行环境。深入理解浏览器的工作原理，能帮助我们写出更高性能的代码，也是前端面试中的高频考点。本指南从浏览器架构、页面加载、渲染流程、V8 引擎、垃圾回收、安全策略、缓存机制等方面进行全面梳理。

---

## 一、浏览器架构

现代浏览器（以 Chrome 为例）采用**多进程架构**，主要包括以下进程：

### 1. Browser 主进程（浏览器进程）

Browser 进程是浏览器的"大管家"，负责：

- **UI 管理**：地址栏、书签、前进后退按钮等浏览器界面的渲染与交互。
- **网络请求调度**：虽然具体的网络 I/O 由网络进程执行，但 Browser 进程负责发起和调度请求。
- **存储管理**：Cookie、localStorage、IndexedDB 等存储的管理。
- **子进程管理**：创建和销毁渲染进程、GPU 进程等，协调各进程间的通信（IPC）。
- **文件访问**：处理文件下载、文件上传等涉及操作系统文件系统的操作。

### 2. Renderer 渲染进程

渲染进程是浏览器的核心，负责将 HTML、CSS、JavaScript 转化为用户可以交互的页面。

- 内部集成 **Blink 渲染引擎**（负责 HTML 解析、CSS 计算、布局、绘制）和 **V8 JavaScript 引擎**（负责 JS 执行）。
- **进程隔离策略**：Chrome 默认采用 Site Isolation（站点隔离），即每个站点（same-site）一个渲染进程。这意味着同一个 Tab 中如果有跨站点的 iframe，iframe 会运行在独立的渲染进程中。早期 Chrome 是每个 Tab 一个渲染进程，后来改为按站点划分以提升安全性。
- 渲染进程运行在**沙箱（Sandbox）**中，不能直接访问操作系统资源，需要通过 Browser 进程代理。

### 3. GPU 进程

- 负责 GPU 任务的处理，包括 CSS 3D 变换、WebGL、视频解码等。
- 将各个渲染进程提交的**合成帧**进行最终合成，输出到屏幕。
- 所有 GPU 操作集中在一个进程中，避免多个进程同时操作 GPU 带来的稳定性问题。

### 4. Network 网络进程

- 独立的网络服务进程，负责所有网络请求的发起和接收。
- 处理 DNS 解析、TCP/TLS 连接、HTTP 请求/响应、缓存策略等。
- 独立成进程可以提升稳定性，网络故障不会影响其他功能。

### 5. Plugin 插件进程

- 每个类型的插件（如 Flash，现已淘汰）运行在独立进程中。
- 插件崩溃不会影响浏览器或页面。
- 现代浏览器中，浏览器扩展（Extension）也运行在独立的进程中。

### 多进程架构的优势

| 优势 | 说明 |
|------|------|
| **稳定性** | 一个页面或插件崩溃不会导致整个浏览器崩溃 |
| **安全性** | 渲染进程运行在沙箱中，恶意代码无法直接操作系统 |
| **流畅性** | JavaScript 执行不会阻塞浏览器 UI 响应 |

### 多进程架构的劣势

- **内存占用高**：每个进程都需要独立的内存空间，包含公共基础设施的副本（如 V8 引擎实例）。
- **进程间通信开销**：IPC（Inter-Process Communication）有一定的性能成本。

---

## 二、页面加载全过程

> **面试题：从输入 URL 到页面显示，经历了什么？**

这是浏览器原理中最经典的面试题，答案涵盖网络、渲染、安全等多个知识领域。

### 1. URL 解析

浏览器首先判断输入的内容是 URL 还是搜索关键词。如果是 URL，会补全协议（如添加 `https://`）。然后对 URL 进行解析，提取出协议、域名、端口、路径、查询参数、片段标识符等信息。对非 ASCII 字符进行编码（encodeURIComponent）。

### 2. DNS 解析（域名解析）

将域名（如 `www.example.com`）解析为 IP 地址。DNS 解析有**递归查询**和**迭代查询**两种方式，缓存层级如下：

```
浏览器 DNS 缓存 → 操作系统 DNS 缓存 → hosts 文件
→ 本地 DNS 服务器（ISP 提供）
→ 根域名服务器（.）
→ 顶级域名服务器（.com）
→ 权威域名服务器（example.com）
```

- **递归查询**：客户端向本地 DNS 服务器发起请求，本地 DNS 服务器如果没有缓存，会依次向上级查询并最终返回结果给客户端。客户端只需发一次请求。
- **迭代查询**：本地 DNS 服务器向根域名服务器查询时，根域名服务器不会帮忙查到底，而是返回下一级服务器的地址，本地 DNS 服务器再去查下一级。

> **面试题：DNS 解析优化手段有哪些？**
>
> - `dns-prefetch`：`<link rel="dns-prefetch" href="//cdn.example.com">`
> - 减少不同域名的使用数量
> - 使用 CDN 就近解析

### 3. TCP 三次握手

浏览器与服务器建立 TCP 连接，经历三次握手（详见网络章节）。

### 4. TLS 握手（HTTPS）

如果是 HTTPS 协议，还需要进行 TLS 握手，协商加密套件、验证证书、交换密钥。TLS 1.2 需要 2-RTT，TLS 1.3 优化到 1-RTT。

### 5. 发送 HTTP 请求

建立连接后，浏览器构造 HTTP 请求报文（请求行、请求头、请求体），发送给服务器。请求头中包含 Cookie、User-Agent、Accept 等信息。

### 6. 服务器处理与响应

服务器接收请求后进行处理（可能涉及负载均衡、反向代理、应用逻辑、数据库查询等），返回 HTTP 响应报文（状态行、响应头、响应体）。

### 7. 浏览器解析与渲染

收到响应后，浏览器开始解析 HTML 并进入渲染流程（详见下一节）。

### 8. 连接关闭

页面加载完成后，如果是 HTTP/1.0 或未设置 `keep-alive`，会通过四次挥手关闭 TCP 连接。HTTP/1.1 默认保持连接复用。

---

## 三、渲染流程

> **面试题：浏览器的渲染流程是怎样的？什么是回流和重绘？**

### 渲染流水线

```
HTML → DOM Tree
                 ↘
                  → Render Tree → Layout → Paint → Composite → 屏幕显示
                 ↗
CSS  → CSSOM
```

### 详细步骤

#### 1. 解析 HTML，构建 DOM Tree

HTML 解析器（Parser）将 HTML 字节流按以下流程转换为 DOM 树：

```
字节（Bytes）→ 字符（Characters）→ 令牌（Tokens）→ 节点（Nodes）→ DOM Tree
```

**注意**：

- 遇到 `<script>` 标签会**暂停 HTML 解析**，先下载并执行 JavaScript（因为 JS 可能修改 DOM）。
- `async` 属性：异步下载，下载完立即执行（不保证顺序）。
- `defer` 属性：异步下载，在 DOMContentLoaded 之前按顺序执行。

#### 2. 解析 CSS，构建 CSSOM

CSS 解析器将 CSS 样式表（外部、内联、行内）转换为 CSSOM（CSS Object Model）。CSS 解析**不会阻塞 DOM 解析**，但**会阻塞渲染**（浏览器需要等 CSSOM 构建完成才能进行渲染）。

#### 3. 合成 Render Tree（渲染树）

将 DOM Tree 和 CSSOM 合并为 Render Tree：

- **不包含**不可见元素：`display: none` 的元素不在渲染树中（但 `visibility: hidden` 和 `opacity: 0` 的元素仍在渲染树中，因为它们占据布局空间或参与合成）。
- **不包含** `<head>`、`<meta>` 等非可视元素。

#### 4. Layout 布局（回流 / Reflow）

计算 Render Tree 中每个节点的**几何信息**：位置（x, y）、大小（width, height）。

- 这是一个递归过程，从根节点开始，逐层计算每个节点的布局。
- **触发回流的操作**：改变窗口大小、修改元素尺寸/位置/边距、添加/删除 DOM 元素、读取 offsetWidth/offsetHeight/getBoundingClientRect 等布局属性。

#### 5. Paint 绘制（重绘 / Repaint）

将布局结果转换为**绘制指令列表**（Paint Records），记录绘制的顺序和方式。

- 绘制操作按照层叠上下文（Stacking Context）分层进行。
- **只触发重绘不触发回流的操作**：修改 color、background-color、visibility、box-shadow 等不影响几何信息的属性。

#### 6. Composite 合成

将页面分为多个**合成层（Compositing Layers）**，各层独立光栅化后由 GPU 合成最终图像。

**创建合成层的条件**：

- `transform: translateZ(0)` 或 `translate3d(0,0,0)`
- `will-change: transform`
- `opacity` 动画
- `<video>`、`<canvas>`、`<iframe>` 等元素
- `position: fixed`

**合成层的优势**：

- 合成层的变换（transform、opacity）直接在 GPU 上处理，**不触发回流和重绘**，性能极佳。
- 合成层更新不影响其他层。

**`will-change` 属性**：

```css
.animated-element {
  will-change: transform, opacity; /* 提前告知浏览器该元素将发生变换 */
}
```

> **面试题：如何减少回流和重绘？**
>
> 1. 使用 `transform` 代替 `top/left` 做动画（只触发合成）
> 2. 使用 `visibility: hidden` 代替 `display: none`（前者只重绘，后者触发回流）
> 3. 批量修改 DOM：使用 DocumentFragment 或脱离文档流后修改
> 4. 避免频繁读取触发回流的属性，或使用变量缓存
> 5. 使用 `will-change` 提前声明变化的属性

---

## 四、V8 引擎

> **面试题：V8 引擎是如何执行 JavaScript 代码的？**

V8 是 Google 开发的高性能 JavaScript 和 WebAssembly 引擎，用于 Chrome 浏览器和 Node.js。

### 执行流水线

```
JavaScript 源码
    ↓
Scanner（词法分析）→ Token 流
    ↓
Parser（语法分析）→ AST（抽象语法树）
    ↓
Ignition（解释器）→ 字节码（Bytecode）
    ↓
Sparkplug（基线编译器）→ 轻度优化的机器码
    ↓
TurboFan（优化编译器）→ 高度优化的机器码
```

### 各阶段详解

#### 1. Scanner 词法分析

将源代码字符串拆分为一个个 Token（词法单元）。例如 `var a = 1;` 会被拆分为 `var`（关键字）、`a`（标识符）、`=`（赋值运算符）、`1`（数字字面量）、`;`（分号）。

#### 2. Parser 语法分析

将 Token 流按照语法规则组织为 AST（抽象语法树）。V8 采用**延迟解析（Lazy Parsing）**策略：对于函数体内部的代码，如果函数没有被调用，就先不解析，只进行**预解析（Pre-parsing）**，记录函数的位置和作用域信息，等到函数实际被调用时再完整解析。这大大加快了初始解析速度。

#### 3. Ignition 解释器

将 AST 编译为**字节码**并逐条解释执行。字节码是一种介于 AST 和机器码之间的中间表示，比机器码更紧凑。Ignition 同时收集**类型反馈（Type Feedback）**信息，记录变量和操作的类型，为后续优化编译提供依据。

#### 4. Sparkplug 基线编译器

V8 在 v9.1 中引入的非优化编译器，将字节码快速编译为机器码，不做复杂优化。相比 Ignition 解释执行，Sparkplug 编译后的代码执行更快，但编译速度也很快，几乎不增加延迟。

#### 5. TurboFan 优化编译器

对**热点函数**（被多次调用的函数）进行深度优化编译，生成高度优化的机器码。优化手段包括：

- **内联（Inlining）**：将被调用函数的代码内联到调用处，消除函数调用开销。
- **逃逸分析（Escape Analysis）**：分析对象是否逃逸出函数作用域，如果没有则可以在栈上分配而非堆上。
- **类型特化（Type Specialization）**：根据收集到的类型反馈，生成针对特定类型的优化代码。

### Inline Cache（IC，内联缓存）

V8 使用 IC 机制缓存属性访问的查找结果。当代码首次访问 `obj.x` 时，V8 需要查找 `x` 属性的位置，查到后会将查找结果缓存起来。下次再访问同一类型对象的 `x` 属性时，直接使用缓存结果，无需重新查找。

IC 状态变化：**未初始化 → 单态（Monomorphic）→ 多态（Polymorphic）→ 超态（Megamorphic）**。单态最快，超态最慢。

### Hidden Class（隐藏类）

V8 为每个对象创建一个 Hidden Class（也叫 Map 或 Shape），记录对象的属性布局（每个属性的名称、偏移量、类型等）。

```javascript
// 推荐：以相同顺序初始化属性，共享 Hidden Class
function Point(x, y) {
  this.x = x; // Hidden Class 0 → Hidden Class 1
  this.y = y; // Hidden Class 1 → Hidden Class 2
}
const p1 = new Point(1, 2); // 使用 Hidden Class 2
const p2 = new Point(3, 4); // 共享同一个 Hidden Class 2

// 不推荐：动态增删属性，导致 Hidden Class 分裂
const obj = {};
obj.a = 1; // Hidden Class 变化
obj.b = 2; // Hidden Class 再次变化
delete obj.a; // 触发 Hidden Class 降级，V8 回退到慢速字典模式
```

### 反优化（Deoptimization）

当 TurboFan 的优化假设被违反时（如类型发生变化），优化后的机器码会被丢弃，回退到 Ignition 字节码执行。这叫做**反优化**。

```javascript
function add(a, b) {
  return a + b;
}

// 前 10000 次调用传入数字，TurboFan 优化为数字加法
for (let i = 0; i < 10000; i++) add(i, i);

// 突然传入字符串，类型假设被违反，触发反优化
add("hello", "world");
```

> **面试题：如何写出 V8 友好的代码？**
>
> 1. 以固定顺序初始化对象属性（共享 Hidden Class）
> 2. 不要动态增删属性（特别是 `delete` 操作）
> 3. 保持函数参数类型稳定（避免反优化）
> 4. 使用 TypedArray 存储数值数据

---

## 五、垃圾回收（GC）

> **面试题：V8 的垃圾回收机制是怎样的？**

V8 的堆内存分为**新生代（Young Generation）**和**老生代（Old Generation）**，分别使用不同的回收策略。

### 新生代（Scavenge 算法）

新生代存储**存活时间短**的对象，空间较小（通常 1~8 MB）。

采用 **Scavenge 算法**（基于 Cheney 算法）：

1. 新生代空间分为两个等大的半空间：**From 空间**（使用中）和 **To 空间**（空闲）。
2. 新对象分配在 From 空间。
3. 当 From 空间快满时，触发 GC：
   - 使用**广度优先遍历**（Cheney 算法的特点），从 GC Roots 开始标记 From 空间中所有存活对象。
   - 将存活对象**复制**到 To 空间（按顺序排列，消除内存碎片）。
   - 清空 From 空间。
   - **交换 From 和 To 空间**的角色。
4. **晋升条件**：如果一个对象已经经历过一次 Scavenge 存活，或者 To 空间使用率超过 25%，该对象会被移动到老生代。

**优点**：速度快，适合频繁回收。  
**缺点**：空间利用率只有 50%（始终有一半空间空闲）。

### 老生代（Mark-Sweep + Mark-Compact）

老生代存储**存活时间长**的对象和从新生代晋升的对象，空间较大。

#### Mark-Sweep（标记清除）

1. **标记阶段**：从 GC Roots（全局对象、调用栈中的变量等）出发，递归遍历所有可达对象并标记为存活。
2. **清除阶段**：遍历整个堆，回收未被标记的对象所占的内存。

**缺点**：会产生**内存碎片**（被回收的空间是不连续的）。

#### Mark-Compact（标记整理）

在 Mark-Sweep 的基础上增加**整理阶段**：将所有存活对象向内存一端移动，然后清理边界外的所有内存。

**优点**：消除内存碎片。  
**缺点**：需要移动对象、更新引用，速度较慢。

V8 实际上是混合使用 Mark-Sweep 和 Mark-Compact：大部分时候用 Mark-Sweep（快），当碎片率过高时才用 Mark-Compact（整理）。

#### 增量标记（Incremental Marking）

老生代堆可能很大，一次性标记所有对象会导致长时间停顿（Stop-The-World）。增量标记将标记工作拆分为多个小步骤，穿插在 JavaScript 执行之间，每次只标记一小部分对象。使用**三色标记法**（白色-未访问、灰色-已访问未完成、黑色-已完成）和**写屏障（Write Barrier）**来保证正确性。

#### 并发标记（Concurrent Marking）

V8 在主线程执行 JavaScript 的同时，使用**辅助线程**进行标记工作。这进一步减少了主线程的停顿时间。并发标记同样依赖写屏障来处理标记过程中对象引用的变化。

### GC 触发条件

- 新生代 From 空间快满时，触发 Scavenge。
- 老生代内存使用率达到阈值时，触发 Mark-Sweep/Mark-Compact。
- 手动调用 `global.gc()`（Node.js 中需要 `--expose-gc` 参数）。
- 内存分配失败时，强制触发 GC。

---

## 六、同源策略与跨域

> **面试题：什么是同源策略？如何解决跨域问题？**

### 同源的定义

两个 URL 的**协议（Protocol）**、**域名（Host）**、**端口（Port）**完全相同，即为同源。

```
https://www.example.com:443/path
  ↑协议      ↑域名       ↑端口

https://www.example.com/a 和 https://www.example.com/b → 同源 ✓
http://www.example.com 和 https://www.example.com      → 不同源 ✗（协议不同）
https://www.example.com 和 https://api.example.com     → 不同源 ✗（域名不同）
https://www.example.com 和 https://www.example.com:8080 → 不同源 ✗（端口不同）
```

同源策略限制的操作：DOM 访问、Cookie/localStorage/IndexedDB 读取、AJAX 请求。

### 跨域解决方案

#### 1. CORS（Cross-Origin Resource Sharing，跨域资源共享）

CORS 是 W3C 标准，是最主流的跨域方案。由**服务端**设置响应头来允许跨域。

**简单请求**（满足以下所有条件）：
- 方法为 GET / HEAD / POST
- Content-Type 为 `text/plain`、`multipart/form-data`、`application/x-www-form-urlencoded`
- 不包含自定义头部

简单请求直接发送，浏览器自动在请求头中添加 `Origin` 字段，服务端返回 `Access-Control-Allow-Origin` 即可。

**预检请求（Preflight）**：非简单请求会先发送一个 `OPTIONS` 请求进行"预检"。

```
OPTIONS /api/data HTTP/1.1
Origin: https://www.example.com
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: Content-Type, Authorization

HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://www.example.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 86400
```

#### 2. JSONP（JSON with Padding）

利用 `<script>` 标签不受同源策略限制的特性：

```javascript
// 前端
function handleResponse(data) {
  console.log(data);
}
const script = document.createElement('script');
script.src = 'https://api.example.com/data?callback=handleResponse';
document.body.appendChild(script);

// 服务端返回
handleResponse({"name": "张三", "age": 25});
```

**局限**：只支持 GET 请求、有安全风险（XSS）、无法获取状态码。

#### 3. 反向代理

```nginx
# Nginx 反向代理配置
server {
    listen 80;
    server_name www.example.com;

    location /api/ {
        proxy_pass https://api.backend.com/;
        proxy_set_header Host $host;
    }
}
```

开发环境中可使用 Webpack devServer proxy 或 Node.js 中间件（如 http-proxy-middleware）实现代理。

#### 4. postMessage（跨窗口通信）

```javascript
// 发送方（父窗口）
const iframe = document.getElementById('myIframe');
iframe.contentWindow.postMessage({ type: 'greeting', data: 'hello' }, 'https://other.com');

// 接收方（iframe 页面）
window.addEventListener('message', (event) => {
  if (event.origin !== 'https://parent.com') return; // 验证来源
  console.log(event.data); // { type: 'greeting', data: 'hello' }
});
```

#### 5. WebSocket

WebSocket 协议不受同源策略限制，可以自由跨域通信。

---

## 七、认证方案

> **面试题：Cookie、Session、Token、JWT 各有什么特点？**

### Cookie

| 属性 | 说明 |
|------|------|
| `HttpOnly` | 禁止 JavaScript 访问，防止 XSS 窃取 Cookie |
| `Secure` | 只在 HTTPS 连接中发送 |
| `SameSite` | `Strict`：完全禁止第三方 Cookie；`Lax`：导航到第三方时允许（GET）；`None`：允许第三方（需配合 Secure） |
| `Domain` | Cookie 生效的域名，默认当前域名（不含子域名） |
| `Path` | Cookie 生效的路径 |
| `Expires / Max-Age` | 过期时间。`Expires` 是绝对时间，`Max-Age` 是相对秒数 |

**限制**：每个域名下 Cookie 大小不超过 **4KB**，数量通常限制在 20~50 个。

### Session

- 会话数据存储在**服务端**（内存 / 文件 / 数据库）。
- 服务端生成唯一的 **Session ID**，通过 Cookie（`Set-Cookie: JSESSIONID=xxx`）传递给客户端。
- 客户端后续请求自动携带 Session ID，服务端据此查找对应的会话数据。
- **分布式 Session**：多台服务器间共享 Session，常用方案是将 Session 存储在 **Redis** 中。

### Token

- **无状态**：服务端不存储会话信息，Token 本身包含用户信息和签名。
- **存储位置**：通常存在 localStorage 或内存中，通过请求头 `Authorization: Bearer <token>` 发送。
- **刷新机制**：使用短期 Access Token + 长期 Refresh Token。Access Token 过期后用 Refresh Token 获取新的 Access Token。

### JWT（JSON Web Token）

JWT 由三部分组成，用 `.` 分隔：

```
Header.Payload.Signature
```

- **Header**：Base64 编码的 JSON，包含算法类型（如 `HS256`）和 Token 类型（`JWT`）。
- **Payload**：Base64 编码的 JSON，包含声明（Claims），如 `sub`（主题）、`exp`（过期时间）、`iat`（签发时间）和自定义数据。
- **Signature**：`HMACSHA256(base64UrlEncode(header) + "." + base64UrlEncode(payload), secret)`。

**优点**：无状态可扩展、跨域友好、适合微服务架构。  
**缺点**：无法主动作废（除非使用黑名单）、Payload 只是 Base64 编码不是加密（不要放敏感信息）、Token 体积较大。

**刷新 Token 方案**：Access Token（短期，如 15 分钟）+ Refresh Token（长期，如 7 天）。Refresh Token 被泄露风险更低（仅在刷新时使用），且可以存储在 HttpOnly Cookie 中。

---

## 八、浏览器缓存

> **面试题：浏览器的缓存机制是怎样的？强缓存和协商缓存有什么区别？**

### 强缓存

浏览器直接使用本地缓存，**不向服务器发请求**，返回状态码 `200 (from disk/memory cache)`。

| 头部 | 说明 |
|------|------|
| `Cache-Control: max-age=31536000` | 缓存有效期，单位秒（优先级更高） |
| `Cache-Control: no-cache` | 不使用强缓存，每次都要进行协商缓存验证 |
| `Cache-Control: no-store` | 完全不缓存，每次都从服务器获取 |
| `Cache-Control: public` | 允许中间代理缓存 |
| `Cache-Control: private` | 只允许浏览器缓存，不允许代理缓存 |
| `Expires` | HTTP/1.0 的缓存头，是一个绝对时间（GMT 格式），优先级低于 Cache-Control |

### 协商缓存

强缓存失效后，浏览器**向服务器发请求验证**缓存是否仍然有效。如果有效，服务器返回 `304 Not Modified`（不返回资源内容），浏览器继续使用本地缓存。

| 请求头 | 响应头 | 说明 |
|--------|--------|------|
| `If-None-Match` | `ETag` | 资源的唯一标识（哈希值），精确但计算有开销 |
| `If-Modified-Since` | `Last-Modified` | 资源最后修改时间，精度为秒，可能不准确 |

ETag 优先级高于 Last-Modified。

### 缓存优先级

```
Service Worker → Memory Cache → Disk Cache → Push Cache → 网络请求
```

1. **Service Worker**：完全可编程的缓存，优先级最高。
2. **Memory Cache**：存在内存中，速度最快，关闭 Tab 后清除。通常缓存当前页面已加载的资源（如图片、脚本）。
3. **Disk Cache**：存在磁盘中，容量大，持久化。根据 HTTP 头部决定缓存策略。
4. **Push Cache**：HTTP/2 服务器推送的资源缓存，生命周期很短（约 5 分钟），仅在会话（Session）内有效。

---

## 九、Web 存储

> **面试题：localStorage、sessionStorage、IndexedDB 的区别？**

| 特性 | localStorage | sessionStorage | IndexedDB |
|------|-------------|----------------|----------|
| **容量** | ~5 MB | ~5 MB | 无固定上限（通常数百 MB） |
| **生命周期** | 永久存储，除非手动清除 | 页面会话期间，关闭标签页即清除 | 永久存储 |
| **作用域** | 同源所有页面共享 | 同源 + 同一标签页 | 同源所有页面共享 |
| **API** | 同步 | 同步 | 异步（基于事件/Promise） |
| **数据格式** | 字符串键值对 | 字符串键值对 | 结构化数据（对象、二进制等） |
| **索引** | 无 | 无 | 支持索引查询 |
| **事务** | 无 | 无 | 支持事务（ACID） |
| **使用场景** | 用户偏好、主题设置 | 表单临时数据、页面状态 | 离线数据、大量结构化数据 |

---

## 十、Web Workers

> **面试题：Web Workers 有哪几种？Service Worker 的生命周期是什么？**

### Dedicated Worker（专用 Worker）

```javascript
// 主线程
const worker = new Worker('worker.js');
worker.postMessage({ type: 'calculate', data: [1, 2, 3, 4, 5] });
worker.onmessage = (event) => {
  console.log('结果:', event.data);
};

// worker.js
self.onmessage = (event) => {
  const { type, data } = event.data;
  if (type === 'calculate') {
    const sum = data.reduce((a, b) => a + b, 0);
    self.postMessage(sum);
  }
};
```

**特点**：与创建它的页面一对一绑定、通过 `postMessage` 通信（数据是结构化克隆，非共享）、**不能操作 DOM**。

### Shared Worker（共享 Worker）

多个同源页面可以共享同一个 Shared Worker 实例，通过 `port` 对象通信。适合多标签页间的数据共享。

### Service Worker

Service Worker 是一种特殊的 Worker，运行在独立线程中，充当浏览器与网络之间的**代理**。它是 PWA（Progressive Web App）的核心技术。

**生命周期**：

```
注册（register）→ 安装（install）→ 激活（activate）→ 运行（fetch / push / sync）
```

1. **install 事件**：首次注册时触发，用于预缓存关键资源。调用 `event.waitUntil()` 等待缓存完成。
2. **activate 事件**：安装后激活时触发，用于清理旧版本缓存。新的 Service Worker 默认要等到旧的 Service Worker 控制的所有页面关闭后才会激活（可调用 `self.skipWaiting()` 跳过等待）。
3. **fetch 事件**：拦截页面发出的所有网络请求，可以自定义响应策略（缓存优先、网络优先、缓存回退等）。

```javascript
// 注册 Service Worker
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('SW 注册成功', reg.scope))
    .catch(err => console.error('SW 注册失败', err));
}

// sw.js
const CACHE_NAME = 'v1';

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache =>
      cache.addAll(['/index.html', '/styles.css', '/app.js'])
    )
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(names =>
      Promise.all(names.filter(n => n !== CACHE_NAME).map(n => caches.delete(n)))
    )
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(cached => cached || fetch(event.request))
  );
});
```

---

## 十一、事件机制

> **面试题：事件流的三个阶段是什么？事件委托的原理和优势？**

### 事件流三阶段

```
       ① 捕获阶段           ③ 冒泡阶段
Window ──────→ ... ──→ Target ──→ ... ──────→ Window
                       ② 目标阶段
```

1. **捕获阶段（Capturing Phase）**：事件从 `window` 逐级向下传播到目标元素的父元素。
2. **目标阶段（Target Phase）**：事件到达目标元素。
3. **冒泡阶段（Bubbling Phase）**：事件从目标元素逐级向上传播到 `window`。

### addEventListener

```javascript
element.addEventListener(type, handler, options);
```

`options` 可以是布尔值（`useCapture`，默认 `false` 表示冒泡阶段触发），也可以是对象：

```javascript
{
  capture: false,  // 是否在捕获阶段触发
  once: true,      // 是否只触发一次后自动移除
  passive: true    // 是否永远不调用 preventDefault（提升滚动性能）
}
```

### 事件委托

利用事件冒泡机制，将子元素的事件监听器统一绑定到父元素上：

```javascript
// 不推荐：为每个 li 绑定事件
document.querySelectorAll('li').forEach(li => {
  li.addEventListener('click', handleClick);
});

// 推荐：事件委托
document.querySelector('ul').addEventListener('click', (event) => {
  const target = event.target;
  if (target.tagName === 'LI') {
    handleClick(target);
  }
});
```

**优势**：减少内存占用（少量监听器）、自动处理动态添加的子元素、简化代码。

**注意**：`focus`、`blur`、`mouseenter`、`mouseleave` 等事件**不冒泡**，无法使用事件委托。可以使用 `focusin`、`focusout` 替代前两者。

### 事件方法对比

| 方法 | 作用 |
|------|------|
| `stopPropagation()` | 阻止事件继续传播（不再触发后续的捕获/冒泡阶段处理器） |
| `stopImmediatePropagation()` | 阻止传播 + 阻止同一元素上其他同类事件处理器的执行 |
| `preventDefault()` | 阻止浏览器默认行为（如链接跳转、表单提交） |

---

## 十二、定时器与渲染

> **面试题：requestAnimationFrame 和 setTimeout 做动画有什么区别？requestIdleCallback 是什么？**

### requestAnimationFrame（rAF）

```javascript
function animate() {
  element.style.transform = `translateX(${position}px)`;
  position += 2;
  if (position < 300) {
    requestAnimationFrame(animate);
  }
}
requestAnimationFrame(animate);
```

- 浏览器在**下一次重绘之前**调用回调函数。
- 回调频率与屏幕刷新率同步，通常为 **60fps（约 16.7ms 一帧）**。
- 当页面不可见（Tab 切换到后台）时，rAF **自动暂停**，节省 CPU 和电量。
- 相比 `setTimeout(fn, 16)`，rAF 不会出现丢帧或过度绘制的问题。

### requestIdleCallback（rIC）

```javascript
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0 && tasks.length > 0) {
    doTask(tasks.pop());
  }
  if (tasks.length > 0) {
    requestIdleCallback(doNextTasks);
  }
}, { timeout: 2000 }); // 超过 2 秒强制执行
```

- 在浏览器**空闲时段**执行回调。一帧中如果还有剩余时间（16.7ms 内渲染工作完成后），就会调用 rIC 回调。
- `deadline.timeRemaining()` 返回当前帧剩余的空闲时间（毫秒）。
- `timeout` 参数：如果超过指定时间还没有空闲，强制执行回调（避免饥饿）。
- **React Fiber 的灵感来源**：React 的 Concurrent Mode 借鉴了 rIC 的思想，将渲染工作拆分为小任务，利用浏览器空闲时间执行，实现可中断的渲染。但 React 并未直接使用 rIC（因为兼容性和触发频率问题），而是使用 `MessageChannel` 模拟类似的调度机制。

---

> **总结**：浏览器原理是前端面试的必考内容，理解这些底层机制不仅能帮助通过面试，更能在实际工作中写出高性能、高安全性的前端应用。建议结合 Chrome DevTools 的 Performance、Network、Application 面板进行实践，加深理解。
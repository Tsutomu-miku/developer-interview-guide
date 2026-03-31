# 网络协议面试指南

## 一、HTTP协议基础

### 1.1 HTTP请求方法

> 面试题：GET和POST有什么区别？

HTTP定义了一组请求方法，用于指示对资源执行的操作：

| 方法 | 描述 | 幂等 | 安全 |
|------|------|------|------|
| GET | 获取资源 | ✅ | ✅ |
| POST | 提交数据/创建资源 | ❌ | ❌ |
| PUT | 替换目标资源 | ✅ | ❌ |
| PATCH | 部分修改资源 | ❌ | ❌ |
| DELETE | 删除资源 | ✅ | ❌ |
| OPTIONS | 获取通信选项（预检请求） | ✅ | ✅ |
| HEAD | 与GET相同但无响应体 | ✅ | ✅ |

**GET vs POST 全面对比：**

| 对比维度 | GET | POST |
|----------|-----|------|
| 语义 | 获取资源 | 提交数据 |
| 参数位置 | URL查询字符串 | 请求体Body |
| 参数长度 | 受URL长度限制（约2KB~8KB，浏览器差异） | 理论无限制（服务器可配置） |
| 缓存 | 可被浏览器缓存 | 默认不缓存 |
| 编码类型 | application/x-www-form-urlencoded | 支持多种（form-data/json/text等） |
| 安全性 | 参数暴露在URL中，浏览器历史可见 | 参数在Body中，相对安全 |
| 幂等性 | 幂等（多次请求结果一致） | 非幂等（可能产生副作用） |
| 书签 | 可收藏为书签 | 不能收藏 |
| 回退 | 浏览器回退无害 | 回退会重新提交 |
| TCP包 | 产生一个TCP数据包（Header+Data一起发） | 可能产生两个TCP包（先Header，返回100后再发Data，Firefox例外） |

### 1.2 HTTP状态码

> 面试题：常见的HTTP状态码有哪些？分别表示什么含义？

**1xx 信息响应：**
- **100 Continue**：客户端应继续发送请求体
- **101 Switching Protocols**：协议切换（如WebSocket握手）

**2xx 成功：**
- **200 OK**：请求成功
- **201 Created**：资源创建成功（POST/PUT响应）
- **204 No Content**：成功但无返回内容（DELETE常用）
- **206 Partial Content**：部分内容（Range请求/断点续传）

**3xx 重定向：**
- **301 Moved Permanently**：永久重定向（搜索引擎更新链接，浏览器缓存）
- **302 Found**：临时重定向（可能将POST改为GET）
- **304 Not Modified**：协商缓存命中，使用本地缓存
- **307 Temporary Redirect**：临时重定向（严格保持请求方法不变）
- **308 Permanent Redirect**：永久重定向（严格保持请求方法不变）

**4xx 客户端错误：**
- **400 Bad Request**：请求语法错误/参数无效
- **401 Unauthorized**：未认证（需要登录）
- **403 Forbidden**：已认证但无权限
- **404 Not Found**：资源不存在
- **405 Method Not Allowed**：请求方法不允许
- **413 Payload Too Large**：请求体超过服务器限制
- **429 Too Many Requests**：请求频率超限（限流）

**5xx 服务端错误：**
- **500 Internal Server Error**：服务器内部错误
- **502 Bad Gateway**：网关/代理收到上游服务器无效响应
- **503 Service Unavailable**：服务暂时不可用（过载/维护）
- **504 Gateway Timeout**：网关/代理等待上游服务器超时

### 1.3 HTTP头部

**通用头部：**

```
Cache-Control: max-age=3600, public     // 缓存控制
Connection: keep-alive                   // 持久连接
Date: Mon, 31 Mar 2025 00:00:00 GMT     // 日期
```

**请求头部：**

```
Accept: application/json                 // 可接受的响应类型
Accept-Encoding: gzip, deflate, br       // 可接受的编码
Accept-Language: zh-CN,zh;q=0.9          // 语言偏好
Authorization: Bearer eyJhbGciOi...      // 认证信息
Cookie: session_id=abc123                // Cookie
Host: www.example.com                    // 目标主机
If-None-Match: "etag123"                 // 协商缓存ETag
If-Modified-Since: Mon, 01 Jan 2025...  // 协商缓存时间
Origin: https://www.example.com          // 跨域请求来源
Referer: https://www.example.com/page    // 来源页面
User-Agent: Mozilla/5.0...               // 客户端标识
```

**响应头部：**

```
Access-Control-Allow-Origin: *           // CORS允许的源
Access-Control-Allow-Methods: GET,POST   // CORS允许的方法
Access-Control-Allow-Headers: Content-Type // CORS允许的头
Access-Control-Allow-Credentials: true   // CORS允许携带凭证
Content-Type: application/json; charset=utf-8
Content-Length: 1234
ETag: "etag123"                          // 资源标识
Last-Modified: Mon, 01 Jan 2025...      // 最后修改时间
Set-Cookie: id=abc; HttpOnly; Secure     // 设置Cookie
```

---

## 二、HTTP版本演进

> 面试题：HTTP/1.0、HTTP/1.1、HTTP/2、HTTP/3有什么区别？

### 2.1 HTTP/1.0

- **短连接**：每次请求都需要建立新的TCP连接，请求完成后关闭
- 每次连接只能发送一个请求
- 无Host头，不支持虚拟主机
- 缓存控制：仅Expires和If-Modified-Since

### 2.2 HTTP/1.1

- **持久连接**：Connection: keep-alive默认开启，TCP连接复用
- **管道化（Pipelining）**：可在同一连接上连续发送多个请求，但响应必须按序返回（**队头阻塞 Head-of-Line Blocking**）
- **Host头**：支持虚拟主机（同一IP托管多个域名）
- **断点续传**：Range请求头，支持分片下载
- 新增方法：PUT、PATCH、DELETE、OPTIONS
- 增强缓存：Cache-Control、ETag

**HTTP/1.1的问题：**
- 队头阻塞：前一个响应未完成，后续响应被阻塞
- 头部冗余：每次请求携带大量重复头部（Cookie等）
- 并发限制：浏览器对同一域名限制6~8个TCP连接

### 2.3 HTTP/2

```
┌─────────────────────────┐
│      HTTP/2 连接         │
│  ┌─────────────────┐    │
│  │    二进制分帧层    │    │
│  │  ┌────┐ ┌────┐  │    │
│  │  │帧1 │ │帧2 │  │    │  ← Stream 1 (请求A)
│  │  └────┘ └────┘  │    │
│  │  ┌────┐ ┌────┐  │    │
│  │  │帧3 │ │帧4 │  │    │  ← Stream 2 (请求B)
│  │  └────┘ └────┘  │    │
│  └─────────────────┘    │
│         TCP连接           │
└─────────────────────────┘
```

**核心特性：**

- **多路复用（Multiplexing）**：同一TCP连接上并发多个请求/响应Stream，解决HTTP层队头阻塞
- **头部压缩（HPACK）**：静态表（61个常见头部）+ 动态表（连接期间协商）+ 霍夫曼编码，头部体积减少85%+
- **服务器推送（Server Push）**：服务器主动推送关联资源（如HTML中引用的CSS/JS），减少往返
- **二进制分帧层**：HTTP消息被分解为帧（Frame），多个帧组成流（Stream），多个流在一个连接中复用
- **流优先级（Stream Priority）**：客户端指定流的依赖关系和权重

**HTTP/2的不足：**
- TCP层队头阻塞依然存在（丢包会阻塞所有流）
- TCP+TLS握手延迟（1-3 RTT）

### 2.4 HTTP/3

- **QUIC协议**：基于UDP实现可靠传输（Google设计）
- **彻底解决队头阻塞**：每个Stream独立，单个流丢包不影响其他流
- **0-RTT建连**：结合TLS 1.3，首次1-RTT，重连0-RTT
- **连接迁移**：使用Connection ID标识连接（而非IP+Port），网络切换（如WiFi→4G）不断连
- **TLS 1.3内置**：加密集成在QUIC层中，减少握手延迟
- **前向纠错（FEC）**：通过冗余数据恢复丢失的包，减少重传

---

## 三、HTTPS

> 面试题：HTTPS是如何保证安全的？TLS握手过程是怎样的？

### 3.1 加密方式

**对称加密（Symmetric Encryption）：**
- 加密和解密使用**同一个密钥**
- 算法：AES（高级加密标准）、DES、3DES、ChaCha20
- 优点：加解密速度快
- 缺点：密钥分发问题（如何安全地将密钥传给对方？）

**非对称加密（Asymmetric Encryption）：**
- **公钥加密，私钥解密**（也可私钥签名，公钥验签）
- 算法：RSA（2048/4096位）、ECC（椭圆曲线，256位≈RSA 3072位安全强度）
- 优点：解决密钥分发问题
- 缺点：加解密速度慢（比对称加密慢100~1000倍）

**混合加密（HTTPS实际使用）：**
1. 非对称加密交换"会话密钥"（对称密钥）
2. 后续通信使用对称加密传输数据

### 3.2 CA证书与数字签名

**证书链：**
```
根CA证书（Root CA，预装在浏览器/OS中）
  └── 中间CA证书（Intermediate CA）
        └── 服务器证书（Server Certificate）
```

**数字签名流程：**
1. 服务器将证书内容做Hash得到摘要
2. CA用自己的**私钥**对摘要加密，生成数字签名
3. 客户端用CA的**公钥**解密签名，与自己计算的Hash对比
4. 一致则证明证书未被篡改

**证书验证过程：**
1. 客户端收到服务器证书
2. 检查证书有效期、域名是否匹配
3. 沿证书链向上验证（中间CA→根CA），根CA是否在信任列表中
4. 检查证书吊销状态（CRL/OCSP）

### 3.3 TLS握手流程

**TLS 1.2 四次握手（2-RTT）：**

```
Client                          Server
  |                                |
  |------ ClientHello ----------->|  (支持的TLS版本/加密套件/随机数Client Random)
  |                                |
  |<----- ServerHello ------------|  (选定TLS版本/加密套件/随机数Server Random)
  |<----- Certificate ------------|  (服务器证书)
  |<----- ServerHelloDone --------|
  |                                |
  |------ ClientKeyExchange ----->|  (Pre-Master Secret，用服务器公钥加密)
  |------ ChangeCipherSpec ------>|  (切换为加密通信)
  |------ Finished --------------->|  (加密的握手验证数据)
  |                                |
  |<----- ChangeCipherSpec --------|  (切换为加密通信)
  |<----- Finished ----------------|  (加密的握手验证数据)
  |                                |
  |====== 加密数据传输 =============|
```

双方通过 Client Random + Server Random + Pre-Master Secret 计算出相同的 **Master Secret**，派生出会话密钥。

**TLS 1.3 握手（1-RTT，恢复会话0-RTT）：**
- 仅支持5个安全的加密套件，移除RSA密钥交换（仅保留ECDHE/DHE前向保密）
- ClientHello直接携带密钥交换参数（key_share），减少1个RTT
- 会话恢复可0-RTT（Early Data），但需防重放攻击

---

## 四、TCP协议

### 4.1 三次握手

> 面试题：TCP为什么需要三次握手？两次行不行？

```
Client                   Server
  |                        |
  |--- SYN, seq=x ------->|   第1次：客户端发起连接
  |                        |   (Client: SYN_SENT)
  |<-- SYN+ACK,           |   第2次：服务器确认并发起连接
  |    seq=y, ack=x+1 ----|   (Server: SYN_RCVD)
  |                        |
  |--- ACK, ack=y+1 ----->|   第3次：客户端确认
  |                        |   (Both: ESTABLISHED)
```

**为什么是三次（不是两次）：**

1. **防止历史连接初始化**：如果客户端发送的旧SYN延迟到达，两次握手会导致服务器错误建立连接。三次握手允许客户端在第三步发现是旧连接并发RST拒绝
2. **同步双方初始序列号（ISN）**：客户端和服务器各需确认对方的ISN，至少需要三次消息交换
3. **避免资源浪费**：两次握手时服务器在第二步就分配资源，若第三步的ACK丢失，服务器资源白白占用

### 4.2 四次挥手

> 面试题：TCP为什么需要四次挥手？TIME_WAIT状态的作用？

```
Client                    Server
  |                         |
  |--- FIN, seq=u -------->|   第1次：客户端请求关闭
  |                         |   (Client: FIN_WAIT_1)
  |<-- ACK, ack=u+1 -------|   第2次：服务器确认
  |                         |   (Client: FIN_WAIT_2, Server: CLOSE_WAIT)
  |                         |   (服务器可能还有数据要发送...)
  |<-- FIN, seq=w ---------|   第3次：服务器请求关闭
  |                         |   (Server: LAST_ACK)
  |--- ACK, ack=w+1 ------>|   第4次：客户端确认
  |                         |   (Client: TIME_WAIT → 等待2MSL → CLOSED)
  |                         |   (Server: CLOSED)
```

**为什么是四次（不是三次）：**
- TCP是全双工的，每个方向需要独立关闭
- 第2次ACK确认收到FIN后，服务器可能还有未发完的数据（**半关闭状态CLOSE_WAIT**）
- 服务器发完数据后才发FIN

**TIME_WAIT等待2MSL的原因：**
- **确保最后的ACK到达**：如果ACK丢失，服务器会重发FIN，客户端需要在TIME_WAIT状态处理
- **等待旧报文段消失**：2MSL（Maximum Segment Lifetime，通常60s）确保本次连接的所有报文都从网络中消失，避免影响新连接

### 4.3 TCP vs UDP

| 对比维度 | TCP | UDP |
|----------|-----|-----|
| 连接 | 面向连接（三次握手） | 无连接 |
| 可靠性 | 可靠传输（确认/重传/排序） | 不可靠（尽最大努力交付） |
| 有序性 | 保证数据有序 | 不保证顺序 |
| 流量控制 | 滑动窗口 | 无 |
| 拥塞控制 | 有（慢启动/拥塞避免） | 无 |
| 速度 | 较慢（连接建立+确认开销） | 快（无连接开销） |
| 头部开销 | 20字节 | 8字节 |
| 传输方式 | 字节流 | 数据报 |
| 使用场景 | HTTP/HTTPS/FTP/SMTP/SSH | DNS/DHCP/视频流/实时游戏/QUIC |

### 4.4 TCP拥塞控制

> 面试题：TCP拥塞控制的四个阶段？

```
cwnd
  |          ssthresh
  |            |
  |     .......|........超时
  |    /       |       \
  |   / 拥塞避免|        \  新ssthresh = cwnd/2
  |  /  (线性) |         \
  | / 慢启动   |          \→ 重新慢启动
  |/ (指数)    |
  +————————————————————→ time
```

1. **慢启动（Slow Start）**：cwnd从1个MSS开始，每收到一个ACK，cwnd翻倍（指数增长），直到达到ssthresh
2. **拥塞避免（Congestion Avoidance）**：cwnd超过ssthresh后，每RTT增加1个MSS（线性增长）
3. **快重传（Fast Retransmit）**：收到3个重复ACK时立即重传丢失的段，无需等待超时
4. **快恢复（Fast Recovery）**：ssthresh = cwnd/2，cwnd = ssthresh + 3，进入拥塞避免（而非从慢启动重来）

---

## 五、DNS解析

> 面试题：DNS解析过程是怎样的？

### 5.1 解析流程

```
浏览器DNS缓存 → OS DNS缓存 → hosts文件 → 本地DNS服务器缓存
    ↓ (未命中)
本地DNS服务器 ——迭代查询——→ 根DNS服务器（.）
                            ↓ 返回顶级域NS
                         顶级DNS服务器（.com）
                            ↓ 返回权威域NS
                         权威DNS服务器（example.com）
                            ↓ 返回IP地址
                         返回结果给客户端
```

- **递归查询**：客户端→本地DNS服务器（客户端只发一次请求，DNS服务器代为查询）
- **迭代查询**：本地DNS服务器→各级DNS服务器（每次返回下一级的地址，本地DNS自己去查）

### 5.2 DNS记录类型

| 类型 | 描述 | 示例 |
|------|------|------|
| A | 域名→IPv4地址 | example.com → 93.184.216.34 |
| AAAA | 域名→IPv6地址 | example.com → 2606:2800:220:1:... |
| CNAME | 域名别名→另一个域名 | www.example.com → example.com |
| MX | 邮件交换记录 | example.com → mail.example.com |
| NS | 域名服务器记录 | example.com → ns1.example.com |
| TXT | 文本记录（SPF/DKIM验证等） | v=spf1 include:... |

### 5.3 DNS优化

- **DNS预解析**：`<link rel="dns-prefetch" href="//api.example.com">`
- **DNS缓存**：TTL（Time To Live）控制缓存时间
- **DNS-over-HTTPS（DoH）**：通过HTTPS加密DNS查询，防止DNS劫持/监听
- **DNS-over-TLS（DoT）**：通过TLS加密DNS查询

---

## 六、CDN原理

> 面试题：CDN是如何加速访问的？

### 6.1 CDN工作流程

```
用户 → DNS解析 → GSLB全局负载均衡（根据IP/延迟/负载选择最优节点）
                    ↓
              边缘节点（Edge Server）
              ├── 缓存命中 → 直接返回内容
              └── 缓存未命中 → 回源
                    ↓
              源站服务器（Origin Server）
                    ↓
              返回内容 + 边缘节点缓存
```

### 6.2 核心概念

- **GSLB（Global Server Load Balancing）**：全局负载均衡，根据用户地理位置、网络延迟、节点负载等选择最近/最优的CDN节点
- **边缘节点**：部署在各地的缓存服务器，就近服务用户
- **回源**：缓存未命中时向源站请求资源
- **缓存策略**：遵循HTTP缓存头（Cache-Control/Expires）、支持自定义缓存规则、缓存刷新/预热

### 6.3 CDN适用场景

- 静态资源加速（JS/CSS/图片/视频）
- 动态内容加速（动态路由优化）
- 安全防护（DDoS防护/WAF）
- HTTPS卸载（边缘节点终止TLS，减轻源站压力）

---

## 七、WebSocket

> 面试题：WebSocket和HTTP有什么区别？

### 7.1 基本概念

WebSocket是一种在单个TCP连接上进行**全双工通信**的协议。客户端和服务器可以随时互相发送数据。

### 7.2 握手过程

WebSocket连接通过HTTP Upgrade建立：

```
// 客户端请求
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

// 服务器响应
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

### 7.3 与HTTP轮询对比

| 方式 | 原理 | 实时性 | 开销 |
|------|------|--------|------|
| 短轮询 | 客户端定时发请求 | 低（取决于间隔） | 高（大量无效请求） |
| 长轮询 | 服务器hold请求直到有数据 | 中 | 中（保持连接） |
| SSE | 服务器单向推送（text/event-stream） | 高 | 低（单向/自动重连） |
| WebSocket | 全双工双向通信 | 高 | 低（握手后帧开销小） |

### 7.4 心跳机制

```javascript
// 客户端心跳实现
let heartbeatTimer = null;

function startHeartbeat(ws) {
  heartbeatTimer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }));
    }
  }, 30000); // 30秒一次
}

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'pong') {
    // 收到心跳响应，连接正常
    return;
  }
  // 处理业务消息...
};

ws.onclose = () => {
  clearInterval(heartbeatTimer);
  // 重连逻辑...
};
```

### 7.5 Socket.IO

- 封装了WebSocket，支持自动降级（WebSocket→HTTP长轮询）
- 支持**房间（Room）**和**命名空间（Namespace）**
- 自动重连、心跳检测
- 广播、多路复用

---

## 八、RESTful API设计

> 面试题：如何设计一个好的RESTful API？

### 8.1 设计原则

**资源命名：**
```
GET    /users              // 获取用户列表
GET    /users/123          // 获取单个用户
POST   /users              // 创建用户
PUT    /users/123          // 替换用户（全量更新）
PATCH  /users/123          // 部分更新用户
DELETE /users/123          // 删除用户

GET    /users/123/posts    // 获取用户的文章列表（嵌套资源）
```

**设计规范：**
- 使用**名词**复数表示资源：`/users` 而非 `/getUser`
- HTTP方法表示操作语义，不在URL中出现动词
- 使用小写字母和连字符：`/user-profiles` 而非 `/userProfiles`
- 嵌套不超过2层：`/users/123/posts` 可以，避免 `/users/123/posts/456/comments/789`

**版本控制：**
```
// URL路径（推荐）
GET /api/v1/users

// 请求头
Accept: application/vnd.api.v1+json
```

**过滤、分页、排序：**
```
GET /users?status=active&role=admin        // 过滤
GET /users?page=2&per_page=20             // 分页
GET /users?sort=created_at&order=desc     // 排序
GET /users?fields=id,name,email           // 字段选择
```

**统一响应格式：**
```json
{
  "code": 200,
  "message": "success",
  "data": { },
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

### 8.2 HATEOAS

Hypermedia as the Engine of Application State，响应中包含相关资源的链接：

```json
{
  "id": 123,
  "name": "张三",
  "links": {
    "self": "/users/123",
    "posts": "/users/123/posts",
    "followers": "/users/123/followers"
  }
}
```

---

## 九、GraphQL

> 面试题：GraphQL相比REST有什么优势？

### 9.1 核心概念

**Query（查询）：**
```graphql
query {
  user(id: "123") {
    name
    email
    posts(first: 5) {
      title
      createdAt
    }
  }
}
```

**Mutation（变更）：**
```graphql
mutation {
  createUser(input: { name: "张三", email: "zhang@example.com" }) {
    id
    name
  }
}
```

**Subscription（订阅）：**
```graphql
subscription {
  messageAdded(channelId: "123") {
    content
    sender {
      name
    }
  }
}
```

### 9.2 Schema定义

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
}

type Query {
  user(id: ID!): User
  users(page: Int, perPage: Int): [User!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
}
```

### 9.3 GraphQL vs REST

| 对比维度 | REST | GraphQL |
|----------|------|----------|
| 端点 | 多个端点（/users, /posts） | 单个端点（/graphql） |
| 数据获取 | 固定数据结构（可能过度获取） | 客户端指定需要的字段 |
| 欠获取 | 需多次请求关联资源 | 一次请求获取嵌套关联数据 |
| 类型系统 | 无内置类型 | 强类型Schema |
| 版本控制 | URL或Header版本号 | Schema演进（@deprecated） |
| 缓存 | HTTP缓存天然支持 | 需额外处理（Apollo Cache） |
| 文件上传 | 原生支持multipart | 需额外处理（graphql-upload） |
| 学习曲线 | 低 | 中等 |

### 9.4 N+1问题

```javascript
// 查询10个用户及其文章，不优化时：
// 1次查询用户列表 + 10次查询每个用户的文章 = 11次查询

// 使用DataLoader批量加载解决：
const postLoader = new DataLoader(async (userIds) => {
  const posts = await db.posts.find({ authorId: { $in: userIds } });
  return userIds.map(id => posts.filter(p => p.authorId === id));
});

// Resolver中使用
const resolvers = {
  User: {
    posts: (user) => postLoader.load(user.id) // 自动批量
  }
};
```

DataLoader会收集同一事件循环内的所有load调用，合并为一次批量查询，将N+1问题降为2次查询。

---

## 十、面试高频综合题

### 10.1 从输入URL到页面显示的网络部分

> 面试题：请详细描述从浏览器输入URL到页面显示过程中涉及的网络协议

1. **URL解析**：判断是搜索词还是URL，补全协议（https://）
2. **DNS解析**：域名→IP地址（递归+迭代查询，多级缓存）
3. **TCP三次握手**：建立可靠连接
4. **TLS握手**：如果是HTTPS，建立安全通道（1-2 RTT）
5. **HTTP请求**：发送请求报文（方法/URL/头部/体）
6. **服务器处理**：Web服务器→应用服务器→数据库，返回响应
7. **HTTP响应**：状态码+响应头+响应体（HTML/JSON等）
8. **TCP四次挥手**：短连接时关闭（HTTP/1.1默认keep-alive）

### 10.2 如何优化网络性能

- DNS预解析（dns-prefetch）
- 预连接（preconnect）
- HTTP/2多路复用
- 资源压缩（Gzip/Brotli）
- CDN加速
- 合理使用缓存（强缓存+协商缓存）
- 减少请求数（雪碧图/合并请求/内联小资源）
- 减小请求体积（Tree-shaking/代码分割/图片优化）
- 使用WebSocket替代轮询（实时场景）

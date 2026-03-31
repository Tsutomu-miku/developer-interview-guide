# 全栈开发面试指南

> 涵盖前端、Node.js、Go 后端、AI Agent 开发及经典算法题的全面面试准备资料

📖 **在线阅读**：[https://tsutomu-miku.github.io/developer-interview-guide/](https://tsutomu-miku.github.io/developer-interview-guide/)

## 📚 内容概览

本指南包含 **42 个章节**，覆盖全栈开发面试的方方面面，每个章节都包含详细的知识点讲解、代码示例和高频面试题。

### 第一部分：前端开发（14 章）

| 章节 | 内容 |
|------|------|
| HTML与CSS | HTML5 语义化、CSS 盒模型、BFC、Flexbox、Grid、响应式、动画 |
| JavaScript核心 | 数据类型、闭包、this、原型链、EventLoop、Promise、ES6+ |
| TypeScript | 类型系统、泛型、工具类型、条件类型、装饰器、协变逆变 |
| 浏览器原理 | 多进程架构、渲染流水线、V8 引擎、跨域、缓存、Web Workers |
| 网络协议 | HTTP/1-3、HTTPS/TLS、TCP、DNS、CDN、WebSocket、REST、GraphQL |
| React | Fiber 架构、Hooks、状态管理、SSR/Next.js、React 18/19 |
| Vue | 响应式原理、Composition API、Pinia、模板编译、keep-alive |
| 前端工程化 | Webpack、Vite、Babel、Monorepo、CI/CD、微前端 |
| 性能优化 | Core Web Vitals、Lighthouse、虚拟滚动、内存泄漏 |
| 前端安全 | XSS、CSRF、CSP、HTTPS 中间人、SQL 注入 |
| **微前端与微模块** 🆕 | qiankun、Module Federation、single-spa、micro-app、wujie、garfish |
| **移动端H5开发** 🆕 | 移动适配、Hybrid、JSBridge、小程序、React Native、Flutter |
| **状态管理深度解析** 🆕 | Redux、Zustand、Jotai、Pinia、Signals、TanStack Query、XState |
| **设计模式与架构** 🆕 | 设计模式应用、MVC/MVVM、React Patterns、SOLID 原则 |

### 第二部分：Node.js 开发（7 章）

| 章节 | 内容 |
|------|------|
| Node.js基础 | 架构、模块系统、Buffer、全局对象 |
| 事件循环 | Event Loop 六阶段、微任务宏任务、nextTick |
| 流与文件系统 | Readable/Writable/Transform/Duplex Stream |
| 常用框架 | Express、Koa、NestJS |
| 数据库操作 | MySQL、MongoDB、Redis、ORM |
| 最佳实践 | 错误处理、日志、微服务、部署 |
| **Serverless与边缘计算** 🆕 | Lambda、Cloudflare Workers、Edge Runtime、SSR/ISR |

### 第三部分：Go 后端开发（7 章）

| 章节 | 内容 |
|------|------|
| Go语言基础 | 类型系统、slice/map 内部实现、接口、错误处理 |
| 并发编程 | Goroutine、GMP 模型、Channel、sync、Context |
| 内存管理 | 内存分配、逃逸分析、三色标记 GC、sync.Pool |
| Web框架 | net/http、Gin、gRPC、中间件 |
| 数据库设计 | GORM、MySQL 索引/事务、Redis、消息队列 |
| 测试与实践 | 测试、pprof、项目结构、设计模式 |
| **云原生与容器化** 🆕 | Docker、Kubernetes、Operator、Istio、GitOps |

### 第四部分：AI Agent 开发（7 章）

| 章节 | 内容 |
|------|------|
| 大语言模型基础 | Transformer、Attention、训练范式、推理优化 |
| Prompt Engineering | 提示工程技巧、Few-shot、CoT、自洽性 |
| RAG检索增强生成 | 向量数据库、Embedding、检索策略、重排序 |
| Agent架构 | ReAct、Plan-and-Execute、多 Agent 协作 |
| 工具调用 | Function Calling、工具编排、MCP 协议 |
| 实战与进阶 | 生产部署、成本优化、安全防护 |
| **评估与可观测性** 🆕 | LLM 评估、Agent 评估、LangFuse、Guardrails |

### 第五部分：经典算法题（7 章）

| 章节 | 内容 |
|------|------|
| 数组与字符串 | 双指针、滑动窗口、前缀和 |
| 链表 | 反转、环检测、LRU 缓存 |
| 树与图 | 遍历、BST、LCA、拓扑排序 |
| 动态规划 | 背包、股票交易、最长子序列 |
| 排序与搜索 | 排序算法、二分搜索 |
| 回溯与贪心 | 全排列、N 皇后、跳跃游戏 |
| **系统设计** 🆕 | 短链接、Feed 流、秒杀、IM、限流器、KV 存储 |

## 🔍 特色功能

- **全文搜索**：支持中文分词的全文搜索，快速定位知识点
- **代码示例**：每个知识点都配有可运行的代码示例
- **面试导向**：每章包含 10-20 道高频面试题及详细解答
- **深度覆盖**：从基础到高级，事无巨细

## 🚀 本地运行

```bash
# 安装 HonKit
npm install -g honkit

# 安装插件
honkit install

# 本地预览
honkit serve
```

## 📄 License

MIT

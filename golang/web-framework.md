# Go Web框架与HTTP面试指南

## 一、net/http 标准库

### 1.1 基本用法

Go 标准库 `net/http` 功能强大，很多生产项目直接使用它而无需第三方框架。

```go
// 最简 HTTP 服务器
func main() {
    http.HandleFunc("/hello", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello, World!")
    })
    http.ListenAndServe(":8080", nil)
}
```

### 1.2 核心接口

> **面试题：net/http 的 Handler 接口是什么？DefaultServeMux 是什么？**

```go
type Handler interface {
    ServeHTTP(ResponseWriter, *Request)
}
```

所有 HTTP 处理逻辑都围绕 `Handler` 接口展开。任何实现了 `ServeHTTP` 方法的类型都可以作为 HTTP 处理器。

`HandlerFunc` 是一个适配器，让普通函数满足 Handler 接口：

```go
type HandlerFunc func(ResponseWriter, *Request)

func (f HandlerFunc) ServeHTTP(w ResponseWriter, r *Request) {
    f(w, r)
}
```

`DefaultServeMux` 是默认的路由多路复用器。当 `http.ListenAndServe` 的第二个参数为 nil 时使用。生产环境建议显式创建 `ServeMux` 或使用第三方路由器。

### 1.3 ServeMux 路由匹配

标准 ServeMux 使用最长前缀匹配：
- `/` 匹配所有未匹配的路径
- `/api/` 匹配 `/api/` 前缀的所有路径
- `/api/users` 精确匹配

**Go 1.22+ 增强路由：**
```go
mux := http.NewServeMux()
mux.HandleFunc("GET /api/users/{id}", getUser)    // 方法+路径参数
mux.HandleFunc("POST /api/users", createUser)
mux.HandleFunc("GET /api/users/{id}/posts/{postID}", getUserPost)

func getUser(w http.ResponseWriter, r *http.Request) {
    id := r.PathValue("id")  // 获取路径参数
}
```

### 1.4 HTTP Server 内部流程

```
客户端请求 → Listener.Accept()
           → 为每个连接创建一个 goroutine
           → conn.serve()
           → 读取请求 → 路由匹配 → 调用 Handler.ServeHTTP()
           → 写入响应
```

每个 HTTP 连接对应一个 goroutine，这是 Go HTTP 服务器的并发模型。

### 1.5 http.Client 与连接池

```go
// 默认 Client 使用 DefaultTransport，包含连接池
client := &http.Client{
    Timeout: 10 * time.Second,
    Transport: &http.Transport{
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
    },
}
```

> **面试题：http.Client 使用时有哪些常见错误？**

1. **不复用 Client**：每次请求创建新 Client 导致连接无法复用
2. **不读取完 Response Body**：连接不会被归还到连接池
3. **不关闭 Response Body**：内存泄漏

```go
resp, err := client.Get(url)
if err != nil {
    return err
}
defer resp.Body.Close()
// 即使不需要 body 内容，也必须读取并丢弃
io.Copy(io.Discard, resp.Body)
```

---

## 二、Gin 框架详解

> **面试题：Gin 框架的核心特性是什么？与标准库相比有什么优势？**

### 2.1 核心特性

- **高性能路由**：基于 Radix Tree（压缩前缀树），路由匹配 O(n) n 为路径长度
- **中间件支持**：洋葱模型的中间件链
- **参数绑定**：自动绑定 JSON/XML/Form 到结构体
- **验证**：集成 `go-playground/validator`
- **错误管理**：集中式错误处理
- **渲染**：支持 JSON/XML/HTML/YAML 等多种响应格式

### 2.2 基本使用

```go
func main() {
    r := gin.Default() // 包含 Logger 和 Recovery 中间件

    r.GET("/users/:id", getUser)
    r.POST("/users", createUser)

    // 路由组
    api := r.Group("/api/v1")
    api.Use(AuthMiddleware())
    {
        api.GET("/users", listUsers)
        api.PUT("/users/:id", updateUser)
    }

    r.Run(":8080")
}

func getUser(c *gin.Context) {
    id := c.Param("id")           // 路径参数
    name := c.Query("name")       // 查询参数
    page := c.DefaultQuery("page", "1")

    c.JSON(http.StatusOK, gin.H{
        "id":   id,
        "name": name,
        "page": page,
    })
}
```

### 2.3 参数绑定与验证

```go
type CreateUserReq struct {
    Name  string `json:"name" binding:"required,min=2,max=50"`
    Email string `json:"email" binding:"required,email"`
    Age   int    `json:"age" binding:"gte=0,lte=150"`
}

func createUser(c *gin.Context) {
    var req CreateUserReq
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    // 处理请求
}
```

### 2.4 Gin 中间件

```go
func LoggerMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        start := time.Now()

        // 请求前
        c.Next() // 执行后续处理器

        // 请求后
        latency := time.Since(start)
        status := c.Writer.Status()
        log.Printf("[%d] %s %s %v", status, c.Request.Method, c.Request.URL.Path, latency)
    }
}

func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
            return // Abort 后不会执行后续处理器
        }
        c.Set("userID", parseToken(token))
        c.Next()
    }
}
```

### 2.5 Gin 的 Context

`gin.Context` 是 Gin 的核心，贯穿整个请求生命周期：

```go
// 数据传递
c.Set("key", value)
val, exists := c.Get("key")

// 请求信息
c.Request        // *http.Request
c.Writer         // gin.ResponseWriter
c.Param("id")   // 路径参数
c.Query("q")    // 查询参数
c.PostForm("f") // 表单参数
c.GetHeader("h") // 请求头

// 响应
c.JSON(code, obj)
c.String(code, format, values...)
c.HTML(code, name, data)
c.File(filepath)

// 流程控制
c.Next()    // 执行下一个处理器
c.Abort()   // 终止后续处理器
```

---

## 三、gRPC 详解

> **面试题：gRPC 与 REST 有什么区别？gRPC 有哪四种调用模式？**

### 3.1 gRPC 概述

gRPC 是 Google 开源的高性能 RPC 框架：
- 使用 **Protocol Buffers** 作为 IDL（接口定义语言）和序列化格式
- 基于 **HTTP/2** 协议（多路复用、头部压缩、双向流）
- 支持多种语言
- 比 JSON + HTTP/1.1 更高效（二进制编码、更小的体积）

### 3.2 Protocol Buffers

```protobuf
syntax = "proto3";
package user;

option go_package = "pb/user";

service UserService {
    rpc GetUser(GetUserRequest) returns (GetUserResponse);
    rpc ListUsers(ListUsersRequest) returns (stream User);
    rpc CreateUsers(stream CreateUserRequest) returns (CreateUsersResponse);
    rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}

message User {
    int64 id = 1;
    string name = 2;
    string email = 3;
    repeated string tags = 4;
}

message GetUserRequest {
    int64 id = 1;
}

message GetUserResponse {
    User user = 1;
}
```

### 3.3 四种调用模式

**1. Unary RPC（一元调用）：** 最基本的请求-响应模式
```go
// 服务端
func (s *server) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.GetUserResponse, error) {
    user, err := s.db.FindUser(req.Id)
    if err != nil {
        return nil, status.Errorf(codes.NotFound, "user not found: %v", err)
    }
    return &pb.GetUserResponse{User: user}, nil
}

// 客户端
resp, err := client.GetUser(ctx, &pb.GetUserRequest{Id: 1})
```

**2. Server Streaming（服务端流）：** 客户端发一个请求，服务端返回一个流
```go
// 服务端
func (s *server) ListUsers(req *pb.ListUsersRequest, stream pb.UserService_ListUsersServer) error {
    for _, user := range users {
        if err := stream.Send(user); err != nil {
            return err
        }
    }
    return nil
}

// 客户端
stream, err := client.ListUsers(ctx, req)
for {
    user, err := stream.Recv()
    if err == io.EOF { break }
    if err != nil { return err }
    fmt.Println(user)
}
```

**3. Client Streaming（客户端流）：** 客户端发送流，服务端返回一个响应
```go
// 服务端
func (s *server) CreateUsers(stream pb.UserService_CreateUsersServer) error {
    var count int
    for {
        req, err := stream.Recv()
        if err == io.EOF {
            return stream.SendAndClose(&pb.CreateUsersResponse{Count: int32(count)})
        }
        if err != nil { return err }
        // 处理 req
        count++
    }
}
```

**4. Bidirectional Streaming（双向流）：** 双方同时发送流
```go
// 服务端
func (s *server) Chat(stream pb.UserService_ChatServer) error {
    for {
        msg, err := stream.Recv()
        if err == io.EOF { return nil }
        if err != nil { return err }
        // 处理并回复
        stream.Send(&pb.ChatMessage{Text: "reply: " + msg.Text})
    }
}
```

### 3.4 gRPC 拦截器（Interceptor）

```go
// 一元拦截器
func unaryInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    start := time.Now()
    // 前处理
    log.Printf("gRPC method: %s", info.FullMethod)

    resp, err := handler(ctx, req) // 执行实际处理

    // 后处理
    log.Printf("gRPC method: %s, duration: %v, error: %v",
        info.FullMethod, time.Since(start), err)
    return resp, err
}

// 注册拦截器
server := grpc.NewServer(
    grpc.UnaryInterceptor(unaryInterceptor),
    grpc.StreamInterceptor(streamInterceptor),
    // 多个拦截器使用 ChainUnaryInterceptor
    grpc.ChainUnaryInterceptor(authInterceptor, logInterceptor, recoveryInterceptor),
)
```

### 3.5 gRPC 错误处理

```go
import "google.golang.org/grpc/status"
import "google.golang.org/grpc/codes"

// 返回 gRPC 错误
return nil, status.Errorf(codes.NotFound, "user %d not found", id)
return nil, status.Errorf(codes.InvalidArgument, "invalid email format")
return nil, status.Errorf(codes.Internal, "database error: %v", err)

// 客户端处理
resp, err := client.GetUser(ctx, req)
if err != nil {
    st, ok := status.FromError(err)
    if ok {
        fmt.Println("Code:", st.Code())
        fmt.Println("Message:", st.Message())
    }
}
```

---

## 四、中间件实现原理

> **面试题：HTTP 中间件的本质是什么？Gin 的中间件链是如何实现的？**

### 4.1 中间件本质

中间件本质上是**装饰器模式**的应用，通过包装 Handler 在请求处理前后添加逻辑。

### 4.2 标准库中间件

```go
// 标准库中间件就是 Handler 的包装函数
func loggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
    })
}

func authMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "Unauthorized", http.StatusUnauthorized)
            return
        }
        next.ServeHTTP(w, r)
    })
}

// 链式组合
handler := loggingMiddleware(authMiddleware(actualHandler))
```

### 4.3 Gin 的中间件链实现

Gin 使用**洋葱模型**，核心是 `HandlersChain`（Handler 切片）和 `index` 索引：

```go
type Context struct {
    handlers HandlersChain  // []HandlerFunc
    index    int8           // 当前执行到第几个 handler
    // ...
}

func (c *Context) Next() {
    c.index++
    for c.index < int8(len(c.handlers)) {
        c.handlers[c.index](c)
        c.index++
    }
}

func (c *Context) Abort() {
    c.index = abortIndex // 设置为最大值，后续 handler 不再执行
}
```

执行流程：
```
Middleware1 前半段
  → Middleware2 前半段
    → Handler 执行
  ← Middleware2 后半段
← Middleware1 后半段
```

---

## 五、路由实现原理

> **面试题：Gin 的路由是如何实现的？为什么要用前缀树？**

### 5.1 前缀树（Trie）

普通前缀树将路径的每个字符作为节点：

```
/api/users → / → a → p → i → / → u → s → e → r → s
/api/posts → / → a → p → i → / → p → o → s → t → s
```

### 5.2 Radix Tree（压缩前缀树）

Gin 使用 Radix Tree，将共同前缀合并为一个节点：

```
                    /api/
                   /      \
              users        posts
              /   \           \
           /:id   /list     /:id
```

优势：
- 节点更少，内存更小
- 查找路径更短，匹配更快
- 时间复杂度 O(n)，n 为路径长度（与路由总数无关）

### 5.3 Gin 路由树结构

```go
type node struct {
    path      string        // 当前节点的路径片段
    indices   string        // 子节点首字符索引（加速查找）
    children  []*node       // 子节点
    handlers  HandlersChain // 该路由的处理器链
    priority  uint32        // 优先级（子路由数量）
    nType     nodeType      // 节点类型：static/root/param/catchAll
    maxParams uint8         // 子树中最大参数数量
    wildChild bool          // 是否有通配符子节点
}
```

每种 HTTP 方法（GET、POST 等）维护一棵独立的 Radix Tree。

### 5.4 路由参数

```go
r.GET("/users/:id", handler)     // 参数路由，匹配一个路径段
r.GET("/files/*filepath", handler) // 通配符路由，匹配剩余所有路径
```

---

## 六、优雅关机

> **面试题：如何实现 Go HTTP 服务的优雅关机？**

优雅关机（Graceful Shutdown）是指在关闭服务时，不直接中断正在处理的请求，而是：
1. 停止接受新请求
2. 等待正在处理的请求完成
3. 超时后强制关闭

### 6.1 标准库实现

```go
func main() {
    srv := &http.Server{
        Addr:    ":8080",
        Handler: setupRouter(),
    }

    // 在 goroutine 中启动服务
    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("listen: %s\n", err)
        }
    }()

    // 等待中断信号
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    log.Println("Shutting down server...")

    // 给正在处理的请求 30 秒完成
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("Server forced to shutdown:", err)
    }

    log.Println("Server exiting")
}
```

### 6.2 Shutdown 内部流程

`srv.Shutdown(ctx)` 做了以下事情：
1. 设置 `inShutdown` 标志，不再接受新连接
2. 关闭所有 listener
3. 关闭所有空闲连接
4. 等待所有活跃连接处理完毕或 context 超时
5. 返回 nil 或 context 错误

### 6.3 Gin 框架的优雅关机

Gin 底层使用标准库的 `http.Server`，优雅关机方式完全一致：

```go
func main() {
    router := gin.Default()
    router.GET("/", handler)

    srv := &http.Server{
        Addr:    ":8080",
        Handler: router,
    }

    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("listen: %s\n", err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    srv.Shutdown(ctx)
}
```

---

## 七、HTTP 客户端最佳实践

> **面试题：在 Go 中如何正确使用 HTTP 客户端？有哪些性能优化手段？**

### 7.1 全局复用 Client

```go
// 错误：每次请求创建新 Client
func bad() {
    resp, err := http.Get(url) // 使用 DefaultClient，但自定义配置时常创建新的
}

// 正确：全局复用
var httpClient = &http.Client{
    Timeout: 30 * time.Second,
    Transport: &http.Transport{
        DialContext: (&net.Dialer{
            Timeout:   30 * time.Second,
            KeepAlive: 30 * time.Second,
        }).DialContext,
        MaxIdleConns:          100,
        MaxIdleConnsPerHost:   10,
        MaxConnsPerHost:       100,
        IdleConnTimeout:       90 * time.Second,
        TLSHandshakeTimeout:   10 * time.Second,
        ExpectContinueTimeout: 1 * time.Second,
    },
}
```

### 7.2 正确处理 Response

```go
resp, err := httpClient.Do(req)
if err != nil {
    return err
}
defer resp.Body.Close()

// 限制读取大小，防止恶意大响应
body, err := io.ReadAll(io.LimitReader(resp.Body, 10<<20)) // 最大 10MB
```

### 7.3 连接池调优

```go
transport := &http.Transport{
    // 所有 host 的最大空闲连接总数
    MaxIdleConns: 100,
    // 每个 host 的最大空闲连接数（重要！默认只有2）
    MaxIdleConnsPerHost: 20,
    // 空闲连接的超时时间
    IdleConnTimeout: 90 * time.Second,
    // 每个 host 的最大连接数（0=无限制）
    MaxConnsPerHost: 0,
}
```

### 7.4 请求重试与熔断

```go
// 简单重试
func doWithRetry(client *http.Client, req *http.Request, maxRetries int) (*http.Response, error) {
    var resp *http.Response
    var err error
    for i := 0; i <= maxRetries; i++ {
        resp, err = client.Do(req)
        if err == nil && resp.StatusCode < 500 {
            return resp, nil
        }
        if resp != nil {
            io.Copy(io.Discard, resp.Body)
            resp.Body.Close()
        }
        // 指数退避
        time.Sleep(time.Duration(1<<uint(i)) * 100 * time.Millisecond)
    }
    return resp, err
}
```

### 7.5 Context 超时控制

```go
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
if err != nil {
    return err
}

resp, err := httpClient.Do(req)
if err != nil {
    if ctx.Err() == context.DeadlineExceeded {
        log.Println("request timeout")
    }
    return err
}
```

### 7.6 HTTP/2

Go 的 `http.Transport` 在连接 HTTPS 时默认自动启用 HTTP/2：

```go
// 默认自动启用 HTTP/2（HTTPS）
client := &http.Client{}

// 强制启用 HTTP/2（即使是自定义 Transport）
import "golang.org/x/net/http2"
transport := &http.Transport{}
http2.ConfigureTransport(transport)
client := &http.Client{Transport: transport}
```

---

## 八、综合面试题

> **面试题：如何设计一个高性能的 Go HTTP API 服务？**

**架构设计要点：**

1. **路由层**：使用 Gin/Chi 等高性能路由框架
2. **中间件**：日志、认证、限流、CORS、链路追踪、panic recovery
3. **参数验证**：结构体 tag + validator
4. **业务层**：依赖注入，接口解耦
5. **数据层**：连接池、读写分离、缓存策略
6. **优雅关机**：signal 捕获 + Shutdown
7. **可观测性**：结构化日志、Prometheus 指标、分布式追踪
8. **配置管理**：Viper/环境变量/配置中心

```go
// 典型项目启动流程
func main() {
    // 1. 加载配置
    cfg := config.Load()
    
    // 2. 初始化依赖
    db := database.NewConnection(cfg.DB)
    cache := redis.NewClient(cfg.Redis)
    
    // 3. 初始化服务层
    userService := service.NewUserService(db, cache)
    
    // 4. 初始化路由
    router := setupRouter(userService)
    
    // 5. 启动服务器
    srv := &http.Server{Addr: cfg.Addr, Handler: router}
    go srv.ListenAndServe()
    
    // 6. 优雅关机
    gracefulShutdown(srv, db, cache)
}
```

> **面试题：REST API 和 gRPC 分别适用于什么场景？**

| 特性 | REST (JSON/HTTP) | gRPC (Protobuf/HTTP2) |
|------|------------------|-----------------------|
| 通信协议 | HTTP/1.1 | HTTP/2 |
| 数据格式 | JSON（文本） | Protobuf（二进制） |
| 性能 | 较低 | 较高（更小的体积、更快的序列化） |
| 浏览器支持 | 原生支持 | 需要 gRPC-Web |
| 流式通信 | 不原生支持 | 四种流模式 |
| 代码生成 | 通常手写 | .proto 自动生成 |
| 适用场景 | 对外 API、Web 前端 | 微服务内部通信 |
| 可读性 | 高（JSON 文本） | 低（二进制） |
| 学习成本 | 低 | 较高 |

**选择建议：**
- 对外暴露 API / 前端调用 → REST
- 微服务间内部通信 / 高性能要求 → gRPC
- 很多团队采用混合架构：对外 REST，内部 gRPC

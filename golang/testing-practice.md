# Go测试与最佳实践面试指南

## 一、单元测试

### 1.1 基础测试

Go 内置了完善的测试框架，测试文件以 `_test.go` 结尾，测试函数以 `Test` 开头：

```go
// math.go
package math

func Add(a, b int) int {
    return a + b
}

func Divide(a, b float64) (float64, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}
```

```go
// math_test.go
package math

import "testing"

func TestAdd(t *testing.T) {
    result := Add(2, 3)
    if result != 5 {
        t.Errorf("Add(2, 3) = %d; want 5", result)
    }
}
```

### 1.2 表驱动测试（Table-Driven Tests）

Go 社区推崇的标准测试模式：

```go
func TestDivide(t *testing.T) {
    tests := []struct {
        name    string
        a, b    float64
        want    float64
        wantErr bool
    }{
        {"normal division", 10, 2, 5, false},
        {"division by zero", 10, 0, 0, true},
        {"negative numbers", -10, 2, -5, false},
        {"decimal result", 7, 3, 2.3333333333333335, false},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := Divide(tt.a, tt.b)
            if (err != nil) != tt.wantErr {
                t.Errorf("Divide() error = %v, wantErr %v", err, tt.wantErr)
                return
            }
            if got != tt.want {
                t.Errorf("Divide() = %v, want %v", got, tt.want)
            }
        })
    }
}
```

### 1.3 测试辅助方法

```go
// TestMain: 整个包的测试入口
func TestMain(m *testing.M) {
    // 测试前的全局设置
    setup()
    code := m.Run() // 运行所有测试
    // 测试后的全局清理
    teardown()
    os.Exit(code)
}

// t.Helper(): 标记辅助函数，错误信息指向调用者
func assertEqual(t *testing.T, got, want interface{}) {
    t.Helper()
    if got != want {
        t.Errorf("got %v, want %v", got, want)
    }
}

// t.Cleanup(): 注册清理函数
func TestWithDB(t *testing.T) {
    db := setupTestDB(t)
    t.Cleanup(func() {
        db.Close()
    })
    // 测试代码
}

// t.Parallel(): 并行测试
func TestParallel(t *testing.T) {
    t.Parallel()
    // 该测试将与其他 Parallel 测试并行执行
}
```

### 1.4 测试覆盖率

```bash
# 运行测试并生成覆盖率
go test -coverprofile=coverage.out ./...

# 查看覆盖率报告
go tool cover -func=coverage.out

# 生成 HTML 报告
go tool cover -html=coverage.out -o coverage.html
```

> **面试题：测试覆盖率 100% 意味着什么？覆盖率应该追求多高？**

100% 覆盖率**不等于**没有 bug。它只表示所有代码行都被执行过，但不保证所有逻辑分支和边界条件都被正确测试。建议核心业务逻辑覆盖率达到 80% 以上，关键路径（支付、认证等）尽量接近 100%。

---

## 二、基准测试（Benchmark）

> **面试题：如何对 Go 代码进行性能基准测试？如何避免编译器优化影响结果？**

### 2.1 基本用法

```go
func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(2, 3)
    }
}

// 运行基准测试
// go test -bench=BenchmarkAdd -benchmem -count=3
// BenchmarkAdd-8   1000000000   0.256 ns/op   0 B/op   0 allocs/op
```

输出说明：
- `1000000000`：运行次数（b.N 由框架自动调整）
- `0.256 ns/op`：每次操作耗时
- `0 B/op`：每次操作分配的字节数
- `0 allocs/op`：每次操作的内存分配次数

### 2.2 避免编译器优化

```go
// 错误：编译器可能优化掉整个调用
func BenchmarkBad(b *testing.B) {
    for i := 0; i < b.N; i++ {
        Add(2, 3) // 结果未使用，可能被优化
    }
}

// 正确：将结果赋值给包级变量
var result int

func BenchmarkGood(b *testing.B) {
    var r int
    for i := 0; i < b.N; i++ {
        r = Add(2, 3)
    }
    result = r // 防止编译器优化
}
```

### 2.3 比较基准测试

```bash
# 安装 benchstat
go install golang.org/x/perf/cmd/benchstat@latest

# 运行优化前后的基准测试
go test -bench=. -count=10 > old.txt
# (修改代码)
go test -bench=. -count=10 > new.txt

# 比较结果
benchstat old.txt new.txt
```

### 2.4 子基准测试

```go
func BenchmarkConcat(b *testing.B) {
    sizes := []int{10, 100, 1000, 10000}
    for _, size := range sizes {
        b.Run(fmt.Sprintf("size=%d", size), func(b *testing.B) {
            strs := make([]string, size)
            for i := range strs {
                strs[i] = "hello"
            }
            b.ResetTimer() // 重置计时器，排除准备时间
            for i := 0; i < b.N; i++ {
                strings.Join(strs, ",")
            }
        })
    }
}
```

---

## 三、Mock 测试

> **面试题：Go 中如何做 Mock 测试？有哪些常用方案？**

### 3.1 接口 Mock（推荐）

Go 推崇通过接口实现依赖注入和 Mock：

```go
// 定义接口
type UserRepository interface {
    GetByID(ctx context.Context, id int64) (*User, error)
    Create(ctx context.Context, user *User) error
}

// 业务层依赖接口
type UserService struct {
    repo UserRepository
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

func (s *UserService) GetUser(ctx context.Context, id int64) (*User, error) {
    user, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("get user: %w", err)
    }
    return user, nil
}
```

```go
// Mock 实现
type MockUserRepo struct {
    GetByIDFunc func(ctx context.Context, id int64) (*User, error)
    CreateFunc  func(ctx context.Context, user *User) error
}

func (m *MockUserRepo) GetByID(ctx context.Context, id int64) (*User, error) {
    return m.GetByIDFunc(ctx, id)
}

func (m *MockUserRepo) Create(ctx context.Context, user *User) error {
    return m.CreateFunc(ctx, user)
}

// 测试
func TestUserService_GetUser(t *testing.T) {
    mockRepo := &MockUserRepo{
        GetByIDFunc: func(ctx context.Context, id int64) (*User, error) {
            if id == 1 {
                return &User{ID: 1, Name: "Alice"}, nil
            }
            return nil, errors.New("not found")
        },
    }

    svc := NewUserService(mockRepo)

    user, err := svc.GetUser(context.Background(), 1)
    if err != nil {
        t.Fatal(err)
    }
    if user.Name != "Alice" {
        t.Errorf("got name %q, want Alice", user.Name)
    }

    _, err = svc.GetUser(context.Background(), 999)
    if err == nil {
        t.Error("expected error for non-existent user")
    }
}
```

### 3.2 使用 mockgen（gomock）

```bash
# 安装
go install go.uber.org/mock/mockgen@latest

# 生成 Mock
mockgen -source=repository.go -destination=mock_repository.go -package=mocks
```

```go
func TestWithGoMock(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mockRepo := mocks.NewMockUserRepository(ctrl)
    mockRepo.EXPECT().
        GetByID(gomock.Any(), int64(1)).
        Return(&User{ID: 1, Name: "Alice"}, nil).
        Times(1)

    svc := NewUserService(mockRepo)
    user, err := svc.GetUser(context.Background(), 1)
    assert.NoError(t, err)
    assert.Equal(t, "Alice", user.Name)
}
```

### 3.3 使用 testify

```go
import (
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "github.com/stretchr/testify/suite"
)

// assert: 失败后继续执行
func TestWithAssert(t *testing.T) {
    assert.Equal(t, 5, Add(2, 3))
    assert.NotNil(t, user)
    assert.Contains(t, "hello world", "hello")
    assert.ErrorIs(t, err, ErrNotFound)
}

// require: 失败后立即停止
func TestWithRequire(t *testing.T) {
    user, err := GetUser(1)
    require.NoError(t, err)  // 如果 err != nil，测试立即停止
    require.NotNil(t, user)
    assert.Equal(t, "Alice", user.Name)
}

// 测试套件
type UserServiceTestSuite struct {
    suite.Suite
    svc  *UserService
    repo *MockUserRepo
}

func (s *UserServiceTestSuite) SetupTest() {
    s.repo = &MockUserRepo{}
    s.svc = NewUserService(s.repo)
}

func (s *UserServiceTestSuite) TestGetUser() {
    s.repo.GetByIDFunc = func(ctx context.Context, id int64) (*User, error) {
        return &User{ID: 1, Name: "Alice"}, nil
    }
    user, err := s.svc.GetUser(context.Background(), 1)
    s.NoError(err)
    s.Equal("Alice", user.Name)
}

func TestUserServiceSuite(t *testing.T) {
    suite.Run(t, new(UserServiceTestSuite))
}
```

### 3.4 httptest（HTTP 测试）

```go
func TestHandler(t *testing.T) {
    // 创建测试路由
    router := setupRouter()

    // 创建请求
    body := strings.NewReader(`{"name":"Alice","email":"alice@example.com"}`)
    req := httptest.NewRequest("POST", "/api/users", body)
    req.Header.Set("Content-Type", "application/json")

    // 记录响应
    w := httptest.NewRecorder()
    router.ServeHTTP(w, req)

    // 验证
    assert.Equal(t, http.StatusCreated, w.Code)

    var resp map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &resp)
    assert.Equal(t, "Alice", resp["name"])
}

// 测试外部 HTTP 依赖（Mock HTTP 服务器）
func TestExternalAPI(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
    }))
    defer server.Close()

    // 将 server.URL 作为外部 API 地址传给被测代码
    client := NewAPIClient(server.URL)
    result, err := client.GetStatus()
    assert.NoError(t, err)
    assert.Equal(t, "ok", result.Status)
}
```

---

## 四、pprof 性能分析

> **面试题：Go 中如何做性能分析？pprof 支持哪些分析类型？**

### 4.1 分析类型

| 类型 | 说明 | 命令 |
|------|------|------|
| CPU | CPU 使用热点 | `go tool pprof cpu.prof` |
| Heap | 堆内存分配 | `go tool pprof heap.prof` |
| Goroutine | goroutine 栈信息 | `go tool pprof goroutine.prof` |
| Allocs | 内存分配统计 | `go tool pprof allocs.prof` |
| Block | 阻塞操作 | `go tool pprof block.prof` |
| Mutex | 锁竞争 | `go tool pprof mutex.prof` |

### 4.2 HTTP pprof

```go
import _ "net/http/pprof"

func main() {
    go func() {
        log.Println(http.ListenAndServe(":6060", nil))
    }()
    // 主程序...
}
```

```bash
# 交互式分析
go tool pprof http://localhost:6060/debug/pprof/heap
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# 常用命令
(pprof) top 20       # 查看前20个热点函数
(pprof) list funcName # 查看函数级别详情
(pprof) web           # 生成 SVG 调用图
(pprof) flame         # 火焰图（需要安装 graphviz）
```

### 4.3 代码中使用 pprof

```go
import "runtime/pprof"

// CPU 分析
f, _ := os.Create("cpu.prof")
pprof.StartCPUProfile(f)
defer pprof.StopCPUProfile()

// 内存分析
f, _ := os.Create("mem.prof")
runtime.GC() // 先 GC 获取更准确的数据
pprof.WriteHeapProfile(f)
f.Close()
```

### 4.4 基准测试中的 pprof

```bash
# 生成 CPU 和内存 profile
go test -bench=BenchmarkXxx -cpuprofile cpu.prof -memprofile mem.prof

# 分析
go tool pprof cpu.prof
```

### 4.5 火焰图分析

```bash
# 方式1：pprof 内置
go tool pprof -http=:8080 cpu.prof
# 浏览器访问 http://localhost:8080/ui/flamegraph

# 方式2：使用 go-torch（较旧）
go-torch -u http://localhost:6060 -t 30
```

火焰图的横轴表示 CPU 时间占比，纵轴表示调用栈深度。越宽的块表示占用 CPU 越多，是优化的重点。

---

## 五、项目结构

> **面试题：Go 项目通常采用什么样的目录结构？**

### 5.1 标准项目布局

参考社区广泛采用的 `golang-standards/project-layout`：

```
myproject/
├── cmd/                    # 主应用入口
│   ├── server/
│   │   └── main.go
│   └── worker/
│       └── main.go
├── internal/               # 私有代码（不被外部包引用）
│   ├── handler/           # HTTP/gRPC 处理器
│   │   └── user.go
│   ├── service/           # 业务逻辑层
│   │   └── user.go
│   ├── repository/        # 数据访问层
│   │   └── user.go
│   ├── model/             # 数据模型
│   │   └── user.go
│   └── middleware/        # 中间件
│       └── auth.go
├── pkg/                    # 可被外部引用的公共包
│   ├── response/
│   └── validator/
├── api/                    # API 定义（protobuf/swagger）
│   └── proto/
├── configs/               # 配置文件
│   └── config.yaml
├── deployments/           # 部署配置（Docker/K8s）
│   ├── Dockerfile
│   └── k8s/
├── scripts/               # 脚本
├── test/                  # 集成测试
├── go.mod
├── go.sum
└── Makefile
```

### 5.2 分层架构

```
Handler (API层)        ← 接收请求，参数验证，调用 Service
    ↓
Service (业务层)       ← 核心业务逻辑，事务管理
    ↓
Repository (数据层)    ← 数据访问，SQL 查询
    ↓
Model (模型层)         ← 数据结构定义
```

```go
// handler 层
func (h *UserHandler) GetUser(c *gin.Context) {
    id, _ := strconv.ParseInt(c.Param("id"), 10, 64)
    user, err := h.userService.GetByID(c.Request.Context(), id)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, user)
}

// service 层
type UserService struct {
    repo  UserRepository
    cache CacheRepository
}

func (s *UserService) GetByID(ctx context.Context, id int64) (*model.User, error) {
    // 先查缓存
    user, err := s.cache.GetUser(ctx, id)
    if err == nil { return user, nil }
    // 再查数据库
    user, err = s.repo.GetByID(ctx, id)
    if err != nil { return nil, err }
    // 写缓存
    s.cache.SetUser(ctx, user)
    return user, nil
}

// repository 层
type UserRepo struct { db *gorm.DB }

func (r *UserRepo) GetByID(ctx context.Context, id int64) (*model.User, error) {
    var user model.User
    err := r.db.WithContext(ctx).First(&user, id).Error
    return &user, err
}
```

### 5.3 依赖注入

```go
// 手动依赖注入
func main() {
    db := initDB()
    cache := initRedis()

    userRepo := repository.NewUserRepo(db)
    userCache := repository.NewUserCache(cache)
    userService := service.NewUserService(userRepo, userCache)
    userHandler := handler.NewUserHandler(userService)

    router := gin.Default()
    router.GET("/users/:id", userHandler.GetUser)
    router.Run(":8080")
}

// 使用 Wire（Google 的依赖注入代码生成工具）
// wire.go
//go:build wireinject

func InitializeApp() (*App, error) {
    wire.Build(
        initDB,
        initRedis,
        repository.NewUserRepo,
        repository.NewUserCache,
        service.NewUserService,
        handler.NewUserHandler,
        NewApp,
    )
    return nil, nil
}
```

---

## 六、设计模式在 Go 中的实践

> **面试题：Go 中常用的设计模式有哪些？与 Java 的设计模式有什么区别？**

Go 由于没有类继承、简洁的接口机制，设计模式的实现更加简洁。

### 6.1 单例模式

```go
// 使用 sync.Once（推荐）
type Database struct{}

var (
    dbInstance *Database
    dbOnce     sync.Once
)

func GetDB() *Database {
    dbOnce.Do(func() {
        dbInstance = &Database{}
    })
    return dbInstance
}
```

### 6.2 工厂模式

```go
type Storage interface {
    Save(key string, data []byte) error
    Load(key string) ([]byte, error)
}

func NewStorage(storageType string) (Storage, error) {
    switch storageType {
    case "file":
        return &FileStorage{}, nil
    case "s3":
        return &S3Storage{}, nil
    case "memory":
        return &MemoryStorage{}, nil
    default:
        return nil, fmt.Errorf("unknown storage type: %s", storageType)
    }
}
```

### 6.3 策略模式

```go
type Compressor interface {
    Compress(data []byte) ([]byte, error)
}

type GzipCompressor struct{}
func (g *GzipCompressor) Compress(data []byte) ([]byte, error) { /* ... */ }

type ZstdCompressor struct{}
func (z *ZstdCompressor) Compress(data []byte) ([]byte, error) { /* ... */ }

type FileProcessor struct {
    compressor Compressor // 策略注入
}

func (p *FileProcessor) Process(data []byte) ([]byte, error) {
    return p.compressor.Compress(data)
}
```

### 6.4 选项模式（Options Pattern）

Go 中非常常用的参数传递模式：

```go
type Server struct {
    addr     string
    port     int
    timeout  time.Duration
    maxConns int
}

type Option func(*Server)

func WithPort(port int) Option {
    return func(s *Server) { s.port = port }
}

func WithTimeout(timeout time.Duration) Option {
    return func(s *Server) { s.timeout = timeout }
}

func WithMaxConns(maxConns int) Option {
    return func(s *Server) { s.maxConns = maxConns }
}

func NewServer(addr string, opts ...Option) *Server {
    s := &Server{
        addr:     addr,
        port:     8080,        // 默认值
        timeout:  30 * time.Second,
        maxConns: 100,
    }
    for _, opt := range opts {
        opt(s)
    }
    return s
}

// 使用
srv := NewServer("0.0.0.0",
    WithPort(9090),
    WithTimeout(60*time.Second),
)
```

### 6.5 装饰器模式

```go
type Handler func(ctx context.Context, req interface{}) (interface{}, error)

func WithLogging(h Handler) Handler {
    return func(ctx context.Context, req interface{}) (interface{}, error) {
        log.Printf("request: %v", req)
        resp, err := h(ctx, req)
        log.Printf("response: %v, error: %v", resp, err)
        return resp, err
    }
}

func WithRetry(h Handler, maxRetries int) Handler {
    return func(ctx context.Context, req interface{}) (interface{}, error) {
        var resp interface{}
        var err error
        for i := 0; i <= maxRetries; i++ {
            resp, err = h(ctx, req)
            if err == nil { return resp, nil }
            time.Sleep(time.Duration(i) * time.Second)
        }
        return resp, err
    }
}

// 组合
handler = WithLogging(WithRetry(baseHandler, 3))
```

---

## 七、编码规范

### 7.1 命名规范

```go
// 包名：小写，简洁，单数
package user     // 好
package utils    // 不太好（过于通用）

// 导出标识符：大写开头
type UserService struct{}  // 导出
type userRepo struct{}     // 不导出

// 接口命名：动词+er 后缀（单方法接口）
type Reader interface { Read(p []byte) (n int, err error) }
type Stringer interface { String() string }

// 变量命名：驼峰，缩略词全大写
var userID int64     // 不是 userId
var httpClient *http.Client
var xmlParser *XMLParser

// 错误变量：Err 前缀
var ErrNotFound = errors.New("not found")
var ErrInvalidInput = errors.New("invalid input")
```

### 7.2 错误处理规范

```go
// 1. 不要忽略错误
result, err := doSomething()
if err != nil {
    return fmt.Errorf("do something: %w", err) // 包装错误并携带上下文
}

// 2. 错误只处理一次（不要又 log 又 return）
// 错误示例
if err != nil {
    log.Printf("error: %v", err) // 打了日志
    return err                    // 又返回了 → 上层可能再打一次
}

// 3. 使用 %w 包装错误，保留错误链
return fmt.Errorf("query user %d: %w", userID, err)
```

### 7.3 并发编码规范

```go
// 1. 传递 context 作为第一个参数
func ProcessOrder(ctx context.Context, orderID int64) error {}

// 2. channel 方向明确
func producer(ch chan<- int) {}  // 只发送
func consumer(ch <-chan int) {}  // 只接收

// 3. goroutine 生命周期可控
func startWorker(ctx context.Context) {
    go func() {
        for {
            select {
            case <-ctx.Done():
                return
            case task := <-taskCh:
                process(task)
            }
        }
    }()
}
```

---

## 八、日志管理

> **面试题：Go 中如何选择日志库？结构化日志有什么优势？**

### 8.1 日志库选型

| 日志库 | 特点 |
|--------|------|
| log（标准库） | 简单，无级别、无结构化 |
| slog（Go 1.21+） | 官方结构化日志，推荐新项目使用 |
| zap（Uber） | 高性能，零分配，广泛使用 |
| zerolog | 零分配 JSON 日志 |
| logrus | 功能丰富，性能一般 |

### 8.2 slog（推荐）

```go
import "log/slog"

// 创建 JSON 格式的 logger
logger := slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
    Level: slog.LevelInfo,
}))

// 结构化日志
logger.Info("user created",
    slog.Int64("user_id", 123),
    slog.String("email", "alice@example.com"),
    slog.Duration("latency", 42*time.Millisecond),
)
// 输出: {"time":"...","level":"INFO","msg":"user created","user_id":123,"email":"alice@example.com","latency":"42ms"}

// 设置为默认 logger
slog.SetDefault(logger)
```

### 8.3 zap

```go
import "go.uber.org/zap"

logger, _ := zap.NewProduction()
defer logger.Sync()

sugar := logger.Sugar()
sugar.Infow("user created",
    "user_id", 123,
    "email", "alice@example.com",
)

// 高性能模式（避免 interface{} 分配）
logger.Info("user created",
    zap.Int64("user_id", 123),
    zap.String("email", "alice@example.com"),
)
```

### 8.4 日志最佳实践

1. **使用结构化日志**：便于日志聚合和搜索
2. **携带 request_id/trace_id**：通过 context 传递
3. **合理的日志级别**：Debug（开发）、Info（业务流程）、Warn（异常但可恢复）、Error（需要关注的错误）
4. **不要记录敏感信息**：密码、Token、身份证号等
5. **日志采样**：高频日志使用采样避免性能影响

```go
// 通过 context 携带 trace_id
func loggerFromContext(ctx context.Context) *slog.Logger {
    traceID, _ := ctx.Value("trace_id").(string)
    return slog.Default().With(slog.String("trace_id", traceID))
}
```

---

## 九、配置管理

### 9.1 Viper

```go
import "github.com/spf13/viper"

func initConfig() {
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath("./configs")
    viper.AutomaticEnv()                    // 自动读取环境变量
    viper.SetEnvPrefix("APP")               // 环境变量前缀
    viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_")) // 嵌套key映射

    if err := viper.ReadInConfig(); err != nil {
        log.Fatal(err)
    }
}

// 获取配置
port := viper.GetInt("server.port")
dbDSN := viper.GetString("database.dsn")

// 绑定到结构体
type Config struct {
    Server struct {
        Port    int           `mapstructure:"port"`
        Timeout time.Duration `mapstructure:"timeout"`
    } `mapstructure:"server"`
    Database struct {
        DSN             string `mapstructure:"dsn"`
        MaxOpenConns    int    `mapstructure:"max_open_conns"`
    } `mapstructure:"database"`
}

var cfg Config
viper.Unmarshal(&cfg)
```

### 9.2 配置管理最佳实践

1. **环境变量优先**：12-Factor App 原则，支持通过环境变量覆盖配置文件
2. **配置结构体化**：定义 Config struct 并在启动时校验
3. **敏感信息加密**：密码、密钥通过环境变量或密钥管理服务获取
4. **配置热更新**：使用配置中心（etcd/Consul/Nacos）实现不重启更新

```go
// 配置校验
type Config struct {
    Port int `validate:"required,gte=1,lte=65535"`
    DSN  string `validate:"required"`
}

func (c *Config) Validate() error {
    validate := validator.New()
    return validate.Struct(c)
}
```

---

## 十、综合面试题

> **面试题：如何保证 Go 项目的代码质量？**

**CI/CD 流水线中应包含：**

1. **代码格式化**：`gofmt -s`、`goimports`
2. **静态分析**：`go vet`、`staticcheck`、`golangci-lint`
3. **单元测试**：`go test -race -coverprofile=coverage.out ./...`
4. **覆盖率检查**：设置覆盖率阈值（如 80%）
5. **基准测试**：关键路径有基准测试
6. **安全扫描**：`gosec`、`govulncheck`
7. **代码审查**：PR Review

```makefile
# Makefile 示例
.PHONY: lint test build

lint:
	golangci-lint run ./...

test:
	go test -race -coverprofile=coverage.out ./...
	go tool cover -func=coverage.out

build:
	CGO_ENABLED=0 GOOS=linux go build -o bin/server ./cmd/server

ci: lint test build
```

> **面试题：Go 项目上线前的检查清单？**

1. **功能测试**：单元测试和集成测试全部通过
2. **性能测试**：基准测试无回归，pprof 无内存泄漏
3. **并发安全**：`go test -race` 无数据竞争
4. **配置检查**：生产环境配置正确（数据库连接、超时设置等）
5. **日志完善**：关键路径有日志，错误日志有上下文
6. **监控告警**：Prometheus 指标暴露，Grafana 面板配置
7. **优雅关机**：确保 Shutdown 逻辑正确
8. **回滚方案**：具备快速回滚能力
9. **限流熔断**：核心接口配置限流，依赖服务配置熔断
10. **文档更新**：API 文档、变更日志更新

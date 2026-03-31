# Go并发编程面试指南

## 一、Goroutine

### 1.1 什么是 Goroutine

Goroutine 是 Go 运行时管理的轻量级线程（用户态线程/协程）。与操作系统线程相比：

| 特性 | Goroutine | OS 线程 |
|------|-----------|---------|
| 初始栈大小 | 2-8 KB（可动态增长） | 1-8 MB（固定） |
| 创建成本 | 极低（几百纳秒） | 较高（微秒级） |
| 调度 | Go runtime 用户态调度 | OS 内核态调度 |
| 切换成本 | 几十纳秒 | 微秒级 |
| 数量 | 可达数十万 | 通常数千 |

```go
go func() {
    fmt.Println("I'm a goroutine")
}()
```

### 1.2 Goroutine 栈管理

Goroutine 的栈是**动态增长**的：
- 初始分配很小（通常 2KB 或 8KB）
- 当函数调用时检测栈空间是否不足
- 不足时分配更大的栈并拷贝旧栈数据（连续栈方案，Go 1.4+）
- 之前的分段栈方案存在"热分裂"问题已被弃用

---

## 二、GMP 模型详解

> **面试题：请详细描述 Go 调度器的 GMP 模型及其调度过程。**

### 2.1 三个核心组件

**G（Goroutine）：** 代表一个 goroutine，包含栈信息、状态、任务函数等。

**M（Machine）：** 代表一个操作系统线程。M 必须绑定一个 P 才能执行 G。M 的数量默认限制为 10000（可通过 `runtime.SetMaxThreads` 修改）。

**P（Processor）：** 代表逻辑处理器，是 G 和 M 之间的桥梁。P 的数量由 `GOMAXPROCS` 决定（默认等于 CPU 核心数）。P 维护一个本地 G 队列（local run queue）。

```
                    ┌──────────────┐
                    │  全局队列 GRQ  │
                    │  [G] [G] [G]  │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │   P0    │       │   P1    │       │   P2    │
   │ LRQ:   │       │ LRQ:   │       │ LRQ:   │
   │ [G][G] │       │ [G]    │       │ [G][G] │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                  │                  │
   ┌────┴────┐       ┌────┴────┐       ┌────┴────┐
   │   M0    │       │   M1    │       │   M2    │
   │ (执行G) │       │ (执行G) │       │ (执行G) │
   └─────────┘       └─────────┘       └─────────┘
```

### 2.2 调度过程

1. **G 的创建**：`go func()` 创建新的 G，优先放入当前 P 的本地队列，队列满时将一半 G 移到全局队列
2. **G 的执行**：M 从绑定的 P 的本地队列获取 G 执行
3. **G 的窃取**：当 P 本地队列为空时，优先从全局队列获取，然后尝试从其他 P **窃取**（work stealing）一半的 G
4. **G 的阻塞**：
   - **系统调用阻塞**：M 与 P 解绑，P 寻找空闲的 M（或创建新 M）继续执行其他 G
   - **channel/锁阻塞**：G 被挂起放入等待队列，M 继续执行其他 G
5. **G 的唤醒**：被阻塞的 G 条件满足后重新放入某个 P 的本地队列

### 2.3 抢占式调度

**Go 1.14 之前（协作式抢占）：**
- 依赖函数调用时插入的**栈增长检查点**进行抢占
- 问题：纯计算的死循环（`for {}` 无函数调用）无法被抢占

**Go 1.14+（基于信号的抢占）：**
- 使用 `SIGURG` 信号实现异步抢占
- 当 G 运行超过 10ms，调度器通过向对应的 M 发送信号来抢占
- 解决了死循环无法调度的问题

```go
// Go 1.14 之前，这个 goroutine 可能永远不会被调度出去
go func() {
    for {
        // 纯计算，没有函数调用
    }
}()
// Go 1.14+ 可以通过信号抢占
```

### 2.4 调度器的设计哲学

- **复用线程**：通过 work stealing 和 hand off 减少线程创建/销毁
- **局部性**：优先从本地队列获取 G，减少锁竞争
- **并行**：GOMAXPROCS 个 P 可以并行执行

---

## 三、Channel

> **面试题：Channel 的底层是怎么实现的？有缓冲和无缓冲 channel 的区别是什么？**

### 3.1 底层结构

```go
type hchan struct {
    qcount   uint           // 队列中的元素个数
    dataqsiz uint           // 环形缓冲区大小
    buf      unsafe.Pointer // 环形缓冲区指针
    elemsize uint16         // 元素大小
    closed   uint32         // 是否已关闭
    elemtype *_type         // 元素类型
    sendx    uint           // 发送索引
    recvx    uint           // 接收索引
    recvq    waitq          // 等待接收的 goroutine 队列
    sendq    waitq          // 等待发送的 goroutine 队列
    lock     mutex          // 互斥锁
}
```

Channel 内部使用**环形缓冲区**存储数据，`recvq` 和 `sendq` 是等待队列（sudog 链表）。

### 3.2 无缓冲 vs 有缓冲

```go
ch1 := make(chan int)     // 无缓冲：发送和接收必须同步
ch2 := make(chan int, 10) // 有缓冲：缓冲区满之前发送不阻塞
```

**无缓冲 channel：** 发送操作会阻塞直到有接收者准备好，反之亦然。适用于 goroutine 间的同步。

**有缓冲 channel：** 缓冲区未满时发送不阻塞，缓冲区非空时接收不阻塞。适用于异步通信。

### 3.3 发送过程详解

1. 如果 `recvq` 中有等待的接收者 → 直接将数据拷贝给接收者（绕过缓冲区）
2. 如果缓冲区有空间 → 将数据放入缓冲区
3. 否则 → 当前 G 被挂起放入 `sendq`

### 3.4 Channel 关闭规则

```go
close(ch) // 关闭 channel
```

**关键规则：**
- 向已关闭的 channel **发送**数据 → **panic**
- 从已关闭的 channel **接收**数据 → 返回缓冲区中的剩余数据，缓冲区空后返回零值
- **重复关闭** channel → **panic**
- 关闭 nil channel → **panic**

**判断 channel 是否关闭：**
```go
val, ok := <-ch
if !ok {
    // channel 已关闭且缓冲区为空
}
```

### 3.5 单向 Channel

```go
func producer(ch chan<- int) { // 只能发送
    ch <- 42
}

func consumer(ch <-chan int) { // 只能接收
    val := <-ch
}
```

> **面试题：如何优雅地关闭 channel？**

遵循原则：**由发送者关闭 channel，不要由接收者关闭**。多个发送者的场景可以通过额外的 done channel 或 sync.Once 来协调：

```go
// 多发送者模式
func main() {
    ch := make(chan int)
    done := make(chan struct{})
    var once sync.Once

    closeCh := func() {
        once.Do(func() { close(ch) })
    }

    // 多个发送者
    for i := 0; i < 3; i++ {
        go func(id int) {
            defer closeCh()
            ch <- id
        }(i)
    }

    // 接收者
    for v := range ch {
        fmt.Println(v)
    }
}
```

---

## 四、select 语句

### 4.1 多路复用

```go
select {
case msg := <-ch1:
    fmt.Println("from ch1:", msg)
case msg := <-ch2:
    fmt.Println("from ch2:", msg)
case ch3 <- data:
    fmt.Println("sent to ch3")
}
```

- 多个 case 同时就绪时，**随机选择**一个执行（避免饥饿）
- 没有任何 case 就绪且无 default → 阻塞
- 有 default → 所有 case 未就绪时执行 default（非阻塞）

### 4.2 超时控制

```go
select {
case result := <-ch:
    fmt.Println(result)
case <-time.After(5 * time.Second):
    fmt.Println("timeout")
}
```

### 4.3 空 select

```go
select {}  // 永久阻塞，常用于主 goroutine 阻塞等待
```

---

## 五、sync 包

### 5.1 Mutex（互斥锁）

```go
var mu sync.Mutex
mu.Lock()
// 临界区
mu.Unlock()
```

Go 的 Mutex 实现经历了多次优化，当前采用**正常模式**和**饥饿模式**：
- **正常模式**：锁释放后，等待中的 goroutine 与新到达的 goroutine 竞争，新到达的 goroutine 有优势（已在 CPU 上运行）
- **饥饿模式**：当等待时间超过 1ms 时切换，锁直接交给等待队列中最久的 goroutine

### 5.2 RWMutex（读写锁）

```go
var rw sync.RWMutex
rw.RLock()   // 读锁，多个读锁可并存
rw.RUnlock()
rw.Lock()    // 写锁，排斥所有读锁和写锁
rw.Unlock()
```

适用于**读多写少**场景。写锁申请时会阻止新的读锁获取（防止写锁饥饿）。

### 5.3 WaitGroup

```go
var wg sync.WaitGroup
for i := 0; i < 10; i++ {
    wg.Add(1)
    go func(id int) {
        defer wg.Done()
        // 工作
    }(i)
}
wg.Wait()
```

**注意：** `wg.Add(1)` 必须在启动 goroutine **之前**调用，否则可能出现 `Wait()` 提前返回。

### 5.4 Once

```go
var once sync.Once
var instance *Singleton

func GetInstance() *Singleton {
    once.Do(func() {
        instance = &Singleton{}
    })
    return instance
}
```

`sync.Once` 底层使用 `atomic` + `Mutex` 实现双重检查锁定（double-checked locking），保证函数只执行一次。

### 5.5 sync.Map

```go
var m sync.Map
m.Store("key", "value")
val, ok := m.Load("key")
m.Delete("key")
m.Range(func(key, value interface{}) bool {
    fmt.Println(key, value)
    return true // 返回 false 停止遍历
})
```

sync.Map 内部维护了两个 map：
- **read map**（只读，无锁访问）：存储频繁读取的数据
- **dirty map**（需要锁）：存储新写入的数据

适用场景：key 相对稳定、读多写少、或各 goroutine 操作不同 key 的场景。

### 5.6 sync.Pool

```go
var pool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

buf := pool.Get().(*bytes.Buffer)
buf.Reset()
// 使用 buf
pool.Put(buf)
```

sync.Pool 是临时对象池，用于减少内存分配和 GC 压力。**注意：Pool 中的对象可能在任何时候被 GC 回收**，不要用于持久化存储。

### 5.7 Cond

```go
var mu sync.Mutex
cond := sync.NewCond(&mu)

// 等待方
mu.Lock()
for !condition {
    cond.Wait() // 自动释放锁并等待，被唤醒后自动获取锁
}
// 处理
mu.Unlock()

// 通知方
mu.Lock()
condition = true
cond.Signal()    // 唤醒一个等待者
// cond.Broadcast() // 唤醒所有等待者
mu.Unlock()
```

---

## 六、原子操作（sync/atomic）

```go
var counter int64

// 原子增减
atomic.AddInt64(&counter, 1)
atomic.AddInt64(&counter, -1)

// 原子读写
val := atomic.LoadInt64(&counter)
atomic.StoreInt64(&counter, 100)

// CAS（比较并交换）
swapped := atomic.CompareAndSwapInt64(&counter, old, new)

// Go 1.19+ atomic.Int64
var ai atomic.Int64
ai.Add(1)
ai.Load()
ai.Store(100)
```

原子操作比互斥锁更轻量，适用于简单的计数器、标志位等场景。

---

## 七、Context

> **面试题：Context 有哪些类型？各自的使用场景是什么？**

### 7.1 四种派生 Context

```go
// 1. WithCancel: 手动取消
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// 2. WithTimeout: 超时自动取消
ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
defer cancel()

// 3. WithDeadline: 指定截止时间
ctx, cancel := context.WithDeadline(context.Background(), time.Now().Add(time.Hour))
defer cancel()

// 4. WithValue: 携带请求级别数据
ctx := context.WithValue(context.Background(), "requestID", "abc-123")
```

### 7.2 使用规范

1. Context 应作为函数的**第一个参数**传递，命名为 `ctx`
2. 不要将 Context 存储在结构体中
3. 不要传递 nil Context，不确定时使用 `context.TODO()`
4. WithValue 只用于请求级别的数据（如 requestID、认证信息），不要滥用

### 7.3 Context 在 HTTP Server 中的传播

```go
func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    // ctx 在请求取消（客户端断开连接）时自动取消
    
    result, err := doWork(ctx)
    if err != nil {
        if ctx.Err() == context.Canceled {
            // 客户端取消了请求
            return
        }
    }
}

func doWork(ctx context.Context) (string, error) {
    select {
    case <-ctx.Done():
        return "", ctx.Err()
    case result := <-longOperation():
        return result, nil
    }
}
```

---

## 八、并发模式

### 8.1 Fan-out / Fan-in

```go
// Fan-out: 多个 goroutine 从同一个 channel 读取
func fanOut(ch <-chan int, workers int) []<-chan int {
    channels := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        channels[i] = worker(ch)
    }
    return channels
}

// Fan-in: 将多个 channel 合并为一个
func fanIn(channels ...<-chan int) <-chan int {
    out := make(chan int)
    var wg sync.WaitGroup
    for _, ch := range channels {
        wg.Add(1)
        go func(c <-chan int) {
            defer wg.Done()
            for v := range c {
                out <- v
            }
        }(ch)
    }
    go func() {
        wg.Wait()
        close(out)
    }()
    return out
}
```

### 8.2 Pipeline（流水线）

```go
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

// 使用
ch := square(square(generate(2, 3, 4)))
for v := range ch {
    fmt.Println(v) // 16, 81, 256
}
```

### 8.3 Worker Pool

```go
func workerPool(jobs <-chan int, results chan<- int, numWorkers int) {
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for job := range jobs {
                results <- process(job)
            }
        }(i)
    }
    go func() {
        wg.Wait()
        close(results)
    }()
}
```

---

## 九、并发安全

### 9.1 数据竞争检测

使用 `-race` 标志启用竞争检测器：

```bash
go run -race main.go
go test -race ./...
```

Race Detector 在运行时监控所有内存访问，检测是否存在无同步保护的并发读写。会增加约 5-10 倍的执行时间和 5-10 倍的内存使用。

### 9.2 死锁排查

Go 运行时能检测所有 goroutine 都阻塞的情况，输出 `fatal error: all goroutines are asleep - deadlock!`。但**部分死锁**（只有部分 goroutine 死锁）无法被自动检测。

常见死锁场景：
```go
// 1. 单个 goroutine 在无缓冲 channel 上自发自收
ch := make(chan int)
ch <- 1 // 死锁

// 2. 互相等待
chA := make(chan int)
chB := make(chan int)
go func() { <-chA; chB <- 1 }()
go func() { <-chB; chA <- 1 }()

// 3. 锁的顺序不一致
go func() { muA.Lock(); muB.Lock() }()
go func() { muB.Lock(); muA.Lock() }()
```

---

## 十、Goroutine 泄漏

> **面试题：什么是 Goroutine 泄漏？如何排查？**

### 10.1 常见原因

1. **channel 发送/接收未配对**：goroutine 阻塞在 channel 操作上无法退出
2. **无限循环无退出条件**：goroutine 内部死循环
3. **锁未释放**：goroutine 阻塞在锁上
4. **context 未取消**：下游服务无响应导致 goroutine 永远等待

```go
// 泄漏示例：生产者不关闭 channel
func leak() {
    ch := make(chan int)
    go func() {
        for val := range ch { // 永远不会退出
            fmt.Println(val)
        }
    }()
    // ch 没有被关闭，goroutine 泄漏
}
```

### 10.2 排查方法

```go
// 1. 运行时获取 goroutine 数量
fmt.Println(runtime.NumGoroutine())

// 2. 使用 pprof
import _ "net/http/pprof"
go http.ListenAndServe(":6060", nil)
// 访问 http://localhost:6060/debug/pprof/goroutine?debug=1

// 3. 使用 goleak 测试库
func TestNoLeak(t *testing.T) {
    defer goleak.VerifyNone(t)
    // 测试代码
}
```

### 10.3 预防措施

- 始终传递 context 并响应取消信号
- 确保 channel 发送者负责关闭 channel
- 使用 `select` + `done channel` 提供退出机制
- 为网络操作设置超时

---

## 十一、经典并发面试题

### 题目一：交替打印奇偶数

> **面试题：用两个 goroutine 交替打印 1 到 100 的奇偶数。**

```go
func printOddEven() {
    ch := make(chan struct{})
    var wg sync.WaitGroup
    wg.Add(2)

    // 打印奇数
    go func() {
        defer wg.Done()
        for i := 1; i <= 100; i += 2 {
            <-ch
            fmt.Println("goroutine1:", i)
            ch <- struct{}{}
        }
    }()

    // 打印偶数
    go func() {
        defer wg.Done()
        for i := 2; i <= 100; i += 2 {
            <-ch
            fmt.Println("goroutine2:", i)
            ch <- struct{}{}
        }
    }()

    ch <- struct{}{} // 启动
    wg.Wait()
}
```

### 题目二：限制并发数

> **面试题：如何限制最多同时运行 N 个 goroutine？**

```go
// 方法1：使用带缓冲 channel 作为信号量
func limitedConcurrency(tasks []func(), maxConcurrency int) {
    sem := make(chan struct{}, maxConcurrency)
    var wg sync.WaitGroup
    for _, task := range tasks {
        wg.Add(1)
        sem <- struct{}{} // 获取信号量
        go func(t func()) {
            defer wg.Done()
            defer func() { <-sem }() // 释放信号量
            t()
        }(task)
    }
    wg.Wait()
}

// 方法2：使用 errgroup
func limitedWithErrgroup(tasks []func() error, maxConcurrency int) error {
    g, _ := errgroup.WithContext(context.Background())
    g.SetLimit(maxConcurrency)
    for _, task := range tasks {
        t := task
        g.Go(func() error { return t() })
    }
    return g.Wait()
}
```

### 题目三：用 Channel 实现互斥锁

> **面试题：如何用 channel 实现一个互斥锁？**

```go
type ChanMutex struct {
    ch chan struct{}
}

func NewChanMutex() *ChanMutex {
    mu := &ChanMutex{ch: make(chan struct{}, 1)}
    mu.ch <- struct{}{} // 初始状态：可获取
    return mu
}

func (m *ChanMutex) Lock() {
    <-m.ch
}

func (m *ChanMutex) Unlock() {
    m.ch <- struct{}{}
}
```

### 题目四：实现超时控制

> **面试题：如何实现一个带超时的 goroutine？**

```go
func doWithTimeout(ctx context.Context, timeout time.Duration, fn func() (interface{}, error)) (interface{}, error) {
    ctx, cancel := context.WithTimeout(ctx, timeout)
    defer cancel()

    resultCh := make(chan interface{}, 1)
    errCh := make(chan error, 1)

    go func() {
        result, err := fn()
        if err != nil {
            errCh <- err
            return
        }
        resultCh <- result
    }()

    select {
    case <-ctx.Done():
        return nil, ctx.Err()
    case err := <-errCh:
        return nil, err
    case result := <-resultCh:
        return result, nil
    }
}
```

### 题目五：生产者-消费者模型

> **面试题：实现一个支持优雅关闭的生产者-消费者模型。**

```go
func producerConsumer() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    ch := make(chan int, 10)
    var wg sync.WaitGroup

    // 生产者
    wg.Add(1)
    go func() {
        defer wg.Done()
        defer close(ch)
        for i := 0; ; i++ {
            select {
            case <-ctx.Done():
                return
            case ch <- i:
                time.Sleep(100 * time.Millisecond)
            }
        }
    }()

    // 消费者
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for val := range ch {
                fmt.Printf("consumer %d: %d\n", id, val)
            }
        }(i)
    }

    // 5秒后取消
    time.Sleep(5 * time.Second)
    cancel()
    wg.Wait()
}
```

### 题目六：用 N 个 goroutine 按顺序打印 1-100

> **面试题：用 N 个 goroutine 轮流按顺序打印 1 到 100。**

```go
func sequentialPrint(n int) {
    chs := make([]chan struct{}, n)
    for i := 0; i < n; i++ {
        chs[i] = make(chan struct{})
    }

    var wg sync.WaitGroup
    num := 1

    for i := 0; i < n; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for {
                <-chs[id]
                if num > 100 {
                    // 通知下一个 goroutine 退出
                    if id+1 < n {
                        chs[(id+1)%n] <- struct{}{}
                    }
                    return
                }
                fmt.Printf("goroutine %d: %d\n", id, num)
                num++
                chs[(id+1)%n] <- struct{}{} // 通知下一个
            }
        }(i)
    }

    chs[0] <- struct{}{} // 启动第一个
    wg.Wait()
}
```

---

## 十二、并发编程最佳实践

1. **优先使用 channel 进行通信**，而不是通过共享内存："Don't communicate by sharing memory; share memory by communicating."
2. **保持 goroutine 的生命周期可控**，始终提供退出机制
3. **使用 `context.Context` 传递取消信号和超时**
4. **避免在热路径上使用锁**，考虑无锁设计或 `sync/atomic`
5. **使用 `go vet`、`-race` 和 goleak 检测并发问题**
6. **Channel 所有权清晰**：谁创建谁关闭，谁发送谁关闭
7. **不要过度并发**，goroutine 虽轻量但不是免费的（栈内存、调度开销）

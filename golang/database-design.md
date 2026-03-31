# Go数据库与系统设计面试指南

## 一、GORM 框架

### 1.1 基本用法

GORM 是 Go 中最流行的 ORM 框架，支持 MySQL、PostgreSQL、SQLite、SQL Server。

```go
import (
    "gorm.io/gorm"
    "gorm.io/driver/mysql"
)

// 连接数据库
dsn := "user:pass@tcp(127.0.0.1:3306)/dbname?charset=utf8mb4&parseTime=True&loc=Local"
db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{
    Logger: logger.Default.LogMode(logger.Info),
})

// 获取底层 *sql.DB 设置连接池
sqlDB, _ := db.DB()
sqlDB.SetMaxIdleConns(10)
sqlDB.SetMaxOpenConns(100)
sqlDB.SetConnMaxLifetime(time.Hour)
```

### 1.2 模型定义

```go
type User struct {
    gorm.Model            // 内嵌 ID, CreatedAt, UpdatedAt, DeletedAt
    Name     string       `gorm:"type:varchar(100);not null;index"`
    Email    string       `gorm:"type:varchar(200);uniqueIndex"`
    Age      int          `gorm:"default:0"`
    Profile  Profile      `gorm:"foreignKey:UserID"` // has one
    Orders   []Order      `gorm:"foreignKey:UserID"` // has many
}

type Profile struct {
    ID     uint
    UserID uint
    Bio    string
}

type Order struct {
    ID     uint
    UserID uint
    Amount float64
}
```

### 1.3 CRUD 操作

```go
// Create
user := User{Name: "Alice", Email: "alice@example.com"}
result := db.Create(&user)
fmt.Println(user.ID)             // 自动填充 ID
fmt.Println(result.RowsAffected) // 受影响的行数

// Read
var user User
db.First(&user, 1)                              // 主键查询
db.Where("name = ?", "Alice").First(&user)       // 条件查询
db.Where("age > ? AND name LIKE ?", 18, "%ali%").Find(&users) // 多条件

// Update
db.Model(&user).Update("name", "Bob")
db.Model(&user).Updates(User{Name: "Bob", Age: 25}) // 零值不更新
db.Model(&user).Updates(map[string]interface{}{"name": "Bob", "age": 0}) // 零值也更新

// Delete（软删除，设置 DeletedAt）
db.Delete(&user, 1)
// 永久删除
db.Unscoped().Delete(&user, 1)
```

### 1.4 预加载（Eager Loading）

```go
// Preload: 单独查询关联表
db.Preload("Profile").Preload("Orders").Find(&users)

// Joins: LEFT JOIN 查询
db.Joins("Profile").Find(&users)

// 条件预加载
db.Preload("Orders", "amount > ?", 100).Find(&users)

// 嵌套预加载
db.Preload("Orders.Items").Find(&users)
```

> **面试题：GORM 使用中有哪些常见的性能陷阱？**

1. **N+1 查询问题**：不使用 Preload 导致循环中查询关联数据
2. **不使用连接池**：未设置 `MaxOpenConns` 导致连接数暴增
3. **全表扫描**：查询条件未命中索引
4. **大批量操作**：应使用 `CreateInBatches` 而非逐条插入
5. **事务滥用**：不必要的事务增加锁持有时间
6. **软删除陷阱**：忘记 `Unscoped()` 导致查询结果不符预期

```go
// 批量插入
var users []User
db.CreateInBatches(users, 100) // 每批 100 条

// 原生 SQL（复杂查询推荐）
db.Raw("SELECT * FROM users WHERE age > ? AND deleted_at IS NULL", 18).Scan(&users)
```

---

## 二、MySQL 索引优化

> **面试题：B+树为什么适合做数据库索引？聚簇索引和非聚簇索引有什么区别？**

### 2.1 B+树索引

B+树是 InnoDB 存储引擎的默认索引结构：

**B+树特点：**
- 所有数据存储在**叶子节点**，非叶子节点只存储索引键
- 叶子节点通过**双向链表**连接，利于范围查询
- 树的高度通常为 3-4 层，一次查询只需 3-4 次磁盘 I/O
- 每个节点大小为一个页（16KB），可以存储大量索引键

**为什么不用哈希索引：**
- 哈希索引不支持范围查询
- 不支持排序
- 不支持最左前缀匹配
- 存在哈希冲突

**为什么不用红黑树/AVL 树：**
- 树高度大，磁盘 I/O 次数多
- B+树扇出更大，同样数据量树更矮

### 2.2 聚簇索引 vs 非聚簇索引

| 特性 | 聚簇索引 | 非聚簇索引（二级索引） |
|------|---------|-------------------|
| 叶子节点存储 | 完整行数据 | 索引列 + 主键值 |
| 数量 | 每表只有一个 | 可以有多个 |
| 默认 | 主键索引 | 其他索引 |
| 查询效率 | 直接获取数据 | 可能需要**回表** |

**回表：** 通过二级索引找到主键值，再通过主键在聚簇索引中查找完整数据。

### 2.3 覆盖索引

当查询所需的所有列都在索引中时，无需回表，称为**覆盖索引**：

```sql
-- 复合索引 (name, age)
-- 覆盖索引查询（不需要回表）
SELECT name, age FROM users WHERE name = 'Alice';

-- 需要回表（email 不在索引中）
SELECT name, age, email FROM users WHERE name = 'Alice';
```

### 2.4 索引优化原则

1. **最左前缀原则**：复合索引 `(a, b, c)` 可以优化 `WHERE a=?`、`WHERE a=? AND b=?`、`WHERE a=? AND b=? AND c=?`
2. **避免索引失效**：
   - 对索引列使用函数：`WHERE YEAR(created_at) = 2024` → 失效
   - 隐式类型转换：`WHERE phone = 13800138000`（phone 是 varchar）→ 失效
   - LIKE 左模糊：`WHERE name LIKE '%alice'` → 失效
   - OR 条件中有非索引列 → 可能失效
   - 不等于 `!=`、`<>` → 可能失效
3. **选择性高的列优先建索引**（区分度大的列）
4. **避免冗余索引**：`(a)` 和 `(a, b)` 同时存在时，`(a)` 是冗余的

### 2.5 Explain 分析

```sql
EXPLAIN SELECT * FROM users WHERE name = 'Alice' AND age > 20;
```

关键字段：
- **type**：查询类型（从好到差：system > const > eq_ref > ref > range > index > ALL）
- **key**：实际使用的索引
- **rows**：预估扫描行数
- **Extra**：额外信息（Using index=覆盖索引，Using filesort=需排序，Using temporary=需临时表）

---

## 三、MySQL 事务

> **面试题：MySQL 的事务隔离级别有哪些？InnoDB 如何通过 MVCC 实现可重复读？**

### 3.1 ACID

- **Atomicity（原子性）**：事务要么全部成功，要么全部回滚（undo log）
- **Consistency（一致性）**：事务执行前后数据库状态一致
- **Isolation（隔离性）**：并发事务之间互不干扰（MVCC + 锁）
- **Durability（持久性）**：事务提交后数据永久保存（redo log）

### 3.2 隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---------|------|----------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 |
| READ COMMITTED | 不可能 | 可能 | 可能 |
| REPEATABLE READ（InnoDB 默认） | 不可能 | 不可能 | InnoDB 基本不可能 |
| SERIALIZABLE | 不可能 | 不可能 | 不可能 |

### 3.3 MVCC（多版本并发控制）

InnoDB 每行数据有两个隐藏列：
- `DB_TRX_ID`：最后修改该行的事务 ID
- `DB_ROLL_PTR`：回滚指针，指向 undo log 中该行的上一个版本

**ReadView（快照读的可见性判断）：**
- `m_ids`：创建 ReadView 时活跃的事务 ID 列表
- `min_trx_id`：活跃事务中最小的 ID
- `max_trx_id`：下一个将分配的事务 ID
- `creator_trx_id`：创建该 ReadView 的事务 ID

**可见性规则：**
1. `DB_TRX_ID == creator_trx_id` → 可见（自己修改的）
2. `DB_TRX_ID < min_trx_id` → 可见（事务已提交）
3. `DB_TRX_ID >= max_trx_id` → 不可见（事务在快照之后开始）
4. `min_trx_id <= DB_TRX_ID < max_trx_id` → 检查是否在 m_ids 中，在则不可见，不在则可见

**RC vs RR 的区别：**
- **RC（读已提交）**：每次 SELECT 创建新的 ReadView
- **RR（可重复读）**：整个事务复用第一次 SELECT 创建的 ReadView

### 3.4 锁机制

**行锁类型：**
- **共享锁（S Lock）**：`SELECT ... LOCK IN SHARE MODE`
- **排他锁（X Lock）**：`SELECT ... FOR UPDATE`
- **Record Lock**：锁定索引记录
- **Gap Lock**：锁定索引间隙（防止幻读）
- **Next-Key Lock**：Record Lock + Gap Lock

```go
// GORM 中使用事务
err := db.Transaction(func(tx *gorm.DB) error {
    // 悲观锁
    var user User
    if err := tx.Clauses(clause.Locking{Strength: "UPDATE"}).
        Where("id = ?", 1).First(&user).Error; err != nil {
        return err
    }
    user.Balance -= 100
    return tx.Save(&user).Error
})
```

---

## 四、Redis 在 Go 中的使用

> **面试题：Go 中使用 Redis 有哪些最佳实践？如何防止缓存穿透/雪崩/击穿？**

### 4.1 go-redis 基本用法

```go
import "github.com/redis/go-redis/v9"

rdb := redis.NewClient(&redis.Options{
    Addr:         "localhost:6379",
    Password:     "",
    DB:           0,
    PoolSize:     100,           // 连接池大小
    MinIdleConns: 10,            // 最小空闲连接
    DialTimeout:  5 * time.Second,
    ReadTimeout:  3 * time.Second,
    WriteTimeout: 3 * time.Second,
})

// 基本操作
ctx := context.Background()
rdb.Set(ctx, "key", "value", time.Hour)
val, err := rdb.Get(ctx, "key").Result()
if err == redis.Nil {
    // key 不存在
}
```

### 4.2 常见使用模式

**缓存模式：**
```go
func GetUser(ctx context.Context, id int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", id)

    // 1. 查缓存
    data, err := rdb.Get(ctx, cacheKey).Bytes()
    if err == nil {
        var user User
        json.Unmarshal(data, &user)
        return &user, nil
    }

    // 2. 查数据库
    user, err := db.GetUser(id)
    if err != nil {
        return nil, err
    }

    // 3. 写缓存
    data, _ = json.Marshal(user)
    rdb.Set(ctx, cacheKey, data, time.Hour+time.Duration(rand.Intn(300))*time.Second)
    return user, nil
}
```

**分布式锁：**
```go
func acquireLock(ctx context.Context, key string, ttl time.Duration) (bool, error) {
    return rdb.SetNX(ctx, "lock:"+key, "1", ttl).Result()
}

func releaseLock(ctx context.Context, key string) error {
    // 使用 Lua 脚本保证原子性
    script := redis.NewScript(`
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    `)
    return script.Run(ctx, rdb, []string{"lock:" + key}, "1").Err()
}
```

### 4.3 缓存三大问题

**缓存穿透**（查询不存在的数据）：
- 布隆过滤器过滤不存在的 key
- 缓存空值（设置较短 TTL）

**缓存雪崩**（大量缓存同时过期）：
- TTL 加随机值避免同时过期
- 多级缓存（本地缓存 + Redis）
- 熔断降级

**缓存击穿**（热点 key 过期）：
- singleflight 合并并发请求
- 互斥锁（分布式锁）控制只有一个请求查 DB
- 永不过期 + 异步更新

```go
import "golang.org/x/sync/singleflight"

var sf singleflight.Group

func GetUserWithSingleFlight(ctx context.Context, id int64) (*User, error) {
    cacheKey := fmt.Sprintf("user:%d", id)
    data, err := rdb.Get(ctx, cacheKey).Bytes()
    if err == nil {
        var user User
        json.Unmarshal(data, &user)
        return &user, nil
    }

    // singleflight 合并并发请求
    v, err, _ := sf.Do(cacheKey, func() (interface{}, error) {
        user, err := db.GetUser(id)
        if err != nil {
            return nil, err
        }
        data, _ := json.Marshal(user)
        rdb.Set(ctx, cacheKey, data, time.Hour)
        return user, nil
    })
    if err != nil {
        return nil, err
    }
    return v.(*User), nil
}
```

---

## 五、消息队列

### 5.1 Kafka 在 Go 中的使用

```go
// 使用 segmentio/kafka-go
import "github.com/segmentio/kafka-go"

// 生产者
writer := &kafka.Writer{
    Addr:         kafka.TCP("localhost:9092"),
    Topic:        "user-events",
    Balancer:     &kafka.LeastBytes{},
    BatchSize:    100,
    BatchTimeout: 10 * time.Millisecond,
    RequiredAcks: kafka.RequireAll, // 等待所有副本确认
}

err := writer.WriteMessages(ctx, kafka.Message{
    Key:   []byte("user-123"),
    Value: []byte(`{"event":"created"}`),
})

// 消费者
reader := kafka.NewReader(kafka.ReaderConfig{
    Brokers:  []string{"localhost:9092"},
    GroupID:  "my-group",
    Topic:    "user-events",
    MinBytes: 1,
    MaxBytes: 10e6,
})

for {
    msg, err := reader.ReadMessage(ctx)
    if err != nil { break }
    fmt.Printf("offset=%d key=%s value=%s\n", msg.Offset, msg.Key, msg.Value)
}
```

### 5.2 消息队列核心概念

> **面试题：Kafka 如何保证消息不丢失？如何保证消息不重复消费？**

**消息不丢失：**
1. **生产者**：设置 `acks=all`，确保所有 ISR 副本都确认
2. **Broker**：设置 `replication.factor >= 3`，`min.insync.replicas >= 2`
3. **消费者**：手动提交 offset，处理完成后再提交

**消息不重复（幂等性）：**
1. 生产者幂等：Kafka 支持 `enable.idempotence=true`
2. 消费者幂等：业务层面保证
   - 数据库唯一约束
   - Redis 去重（消息 ID 为 key）
   - 状态机（检查业务状态是否已更新）

### 5.3 消息队列选型

| 特性 | Kafka | RabbitMQ |
|------|-------|----------|
| 吞吐量 | 极高（百万/秒） | 中等（万级/秒） |
| 延迟 | 毫秒级 | 微秒~毫秒级 |
| 消息模型 | 发布-订阅 | 队列+交换机 |
| 持久化 | 磁盘顺序写 | 内存+磁盘 |
| 适用场景 | 日志、事件流、大数据 | 业务消息、任务队列 |

---

## 六、分布式系统设计

### 6.1 CAP 定理

> **面试题：什么是 CAP 定理？在实际系统中如何选择？**

分布式系统不可能同时满足以下三个特性，最多只能满足两个：

- **C（Consistency，一致性）**：所有节点同一时刻看到的数据一致
- **A（Availability，可用性）**：每个请求都能得到响应（不保证数据最新）
- **P（Partition tolerance，分区容错）**：网络分区时系统继续运行

实际中 P 是必须的（网络分区一定会发生），因此选择在 CP 和 AP 之间：
- **CP 系统**：ZooKeeper、etcd、HBase（保证一致性，牺牲部分可用性）
- **AP 系统**：Cassandra、DynamoDB（保证可用性，牺牲强一致性）

### 6.2 BASE 理论

对 CAP 中 AP 方案的补充：
- **BA（Basically Available）**：基本可用
- **S（Soft State）**：允许中间状态
- **E（Eventually Consistent）**：最终一致性

### 6.3 一致性哈希

> **面试题：什么是一致性哈希？它解决了什么问题？**

**普通哈希的问题：** `node = hash(key) % N`，当节点数 N 变化时，几乎所有 key 的映射都会改变，导致缓存大量失效。

**一致性哈希：**
1. 将哈希空间组成一个环（0 ~ 2^32-1）
2. 节点映射到环上
3. Key 映射到环上后，顺时针找到第一个节点
4. 增删节点只影响相邻节点的数据

**虚拟节点：** 解决节点分布不均匀的问题，每个物理节点对应多个虚拟节点。

```go
type ConsistentHash struct {
    ring     map[uint32]string // hash -> node
    keys     []uint32          // sorted hashes
    replicas int               // 虚拟节点数
}

func (c *ConsistentHash) Get(key string) string {
    hash := c.hash(key)
    idx := sort.Search(len(c.keys), func(i int) bool {
        return c.keys[i] >= hash
    })
    if idx == len(c.keys) {
        idx = 0
    }
    return c.ring[c.keys[idx]]
}
```

### 6.4 分布式锁

> **面试题：Go 中如何实现分布式锁？Redis 分布式锁有什么问题？**

**Redis 分布式锁（Redisson/go-redis）：**
```go
// 获取锁：SET key value NX EX ttl
// 释放锁：Lua 脚本（判断值相等后删除）

// 问题：
// 1. 锁过期但业务未完成 → 续期（看门狗机制）
// 2. Redis 主从切换导致锁丢失 → RedLock 算法
// 3. 非可重入 → 用 hash 结构记录持有次数
```

**etcd 分布式锁：**
```go
import clientv3 "go.etcd.io/etcd/client/v3"
import "go.etcd.io/etcd/client/v3/concurrency"

cli, _ := clientv3.New(clientv3.Config{Endpoints: []string{"localhost:2379"}})
session, _ := concurrency.NewSession(cli, concurrency.WithTTL(10))
mutex := concurrency.NewMutex(session, "/my-lock/")

if err := mutex.Lock(ctx); err != nil {
    log.Fatal(err)
}
// 临界区
mutex.Unlock(ctx)
```

etcd 锁基于 Raft 共识算法，比 Redis 锁更可靠，但延迟更高。

### 6.5 分布式事务

**常见方案：**

1. **2PC（两阶段提交）**：协调者先发 Prepare，所有参与者确认后再发 Commit。问题：同步阻塞、单点故障。

2. **TCC（Try-Confirm-Cancel）**：
   - Try：预留资源
   - Confirm：确认执行
   - Cancel：取消释放资源

3. **Saga 模式**：将长事务拆分为一系列本地事务，每个本地事务有对应的补偿操作。失败时按反序执行补偿。

4. **本地消息表**：
   - 业务操作和消息写入同一个本地事务
   - 异步发送消息到消息队列
   - 消费者消费后回调确认
   - 定时任务补偿未发送/未确认的消息

---

## 七、微服务架构

> **面试题：Go 微服务架构中通常包含哪些组件？如何做服务治理？**

### 7.1 核心组件

```
                        ┌─────────────┐
                        │  API Gateway│ (Kong/Traefik/自研)
                        └──────┬──────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
     ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
     │ User Service│   │Order Service│   │Pay Service  │
     │   (gRPC)    │   │   (gRPC)    │   │   (gRPC)    │
     └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
            │                  │                  │
     ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
     │  MySQL      │   │  MySQL      │   │  MySQL      │
     │  Redis      │   │  Redis      │   │  Redis      │
     └─────────────┘   │  Kafka      │   └─────────────┘
                        └─────────────┘
```

### 7.2 服务注册与发现

```go
// 使用 etcd 做服务注册
func registerService(cli *clientv3.Client, name, addr string) error {
    lease, _ := cli.Grant(context.Background(), 10) // 10秒租约
    _, err := cli.Put(context.Background(),
        fmt.Sprintf("/services/%s/%s", name, addr),
        addr,
        clientv3.WithLease(lease.ID),
    )
    // 续约
    ch, _ := cli.KeepAlive(context.Background(), lease.ID)
    go func() {
        for range ch {} // 自动续约
    }()
    return err
}

// 服务发现
func discoverService(cli *clientv3.Client, name string) ([]string, error) {
    resp, err := cli.Get(context.Background(),
        fmt.Sprintf("/services/%s/", name),
        clientv3.WithPrefix(),
    )
    if err != nil { return nil, err }
    var addrs []string
    for _, kv := range resp.Kvs {
        addrs = append(addrs, string(kv.Value))
    }
    return addrs, nil
}
```

### 7.3 负载均衡

gRPC 内置支持多种负载均衡策略：

```go
// 客户端负载均衡
conn, err := grpc.Dial(
    "my-service",
    grpc.WithDefaultServiceConfig(`{"loadBalancingPolicy":"round_robin"}`),
    grpc.WithResolvers(etcdResolver), // 自定义 resolver
)
```

常见策略：轮询（Round Robin）、加权轮询、最少连接数、一致性哈希。

### 7.4 熔断与限流

**熔断（Circuit Breaker）：**
```go
// 使用 sony/gobreaker
cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
    Name:        "my-service",
    MaxRequests: 3,                // 半开状态最大请求数
    Interval:    10 * time.Second, // 统计窗口
    Timeout:     30 * time.Second, // 熔断后恢复时间
    ReadyToTrip: func(counts gobreaker.Counts) bool {
        return counts.ConsecutiveFailures > 5 // 连续失败5次熔断
    },
})

result, err := cb.Execute(func() (interface{}, error) {
    return callRemoteService()
})
```

**限流（Rate Limiting）：**
```go
// 令牌桶
import "golang.org/x/time/rate"

limiter := rate.NewLimiter(rate.Limit(100), 200) // 每秒100个请求，突发200

func rateLimitMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        if !limiter.Allow() {
            c.AbortWithStatusJSON(429, gin.H{"error": "too many requests"})
            return
        }
        c.Next()
    }
}
```

### 7.5 链路追踪

```go
// 使用 OpenTelemetry
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

tracer := otel.Tracer("my-service")

func handleRequest(ctx context.Context) error {
    ctx, span := tracer.Start(ctx, "handleRequest")
    defer span.End()

    // span 会随 context 传播到下游服务
    return callDownstream(ctx)
}
```

### 7.6 Go 微服务框架选型

| 框架 | 特点 |
|------|------|
| Go-kit | 微服务工具集，理念先进但学习曲线高 |
| Go-micro | 插件化微服务框架 |
| Kratos (B站) | 生产验证，gRPC+HTTP，Wire 依赖注入 |
| Go-zero (好未来) | 内置代码生成、API 定义、服务治理 |
| Kitex (字节) | 高性能 RPC 框架，支持 Thrift 和 gRPC |

> **面试题：微服务拆分的原则是什么？**

1. **单一职责**：每个服务只负责一个业务领域
2. **高内聚低耦合**：服务内部高内聚，服务之间通过清晰的 API 交互
3. **数据库独立**：每个服务拥有独立的数据库
4. **团队对齐**：服务边界与团队边界对齐（康威定律）
5. **渐进拆分**：从单体逐步拆分，不要一开始就过度拆分
6. **避免循环依赖**：服务间的依赖关系应该是单向的

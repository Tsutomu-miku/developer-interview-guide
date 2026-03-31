# 系统设计面试题

> 系统设计面试是高级工程师面试中最重要的环节之一。本章从方法论到经典案例，全面覆盖系统设计面试的核心知识点。

---

## 一、系统设计方法论

### 1.1 四步法框架

系统设计面试通常遵循以下四步框架，每一步都需要与面试官充分沟通：

```
第一步：需求澄清（5分钟）
  ├── 功能性需求：系统需要做什么？
  ├── 非功能性需求：性能、可用性、一致性要求
  └── 边界与约束：用户规模、地域分布

第二步：容量估算（5分钟）
  ├── QPS估算（读/写分离）
  ├── 存储估算（数据增长）
  └── 带宽估算

第三步：高层设计 → 详细设计（25分钟）
  ├── API设计
  ├── 数据模型
  ├── 高层架构图
  └── 核心组件详细设计

第四步：扩展与优化（5分钟）
  ├── 瓶颈分析
  ├── 扩展方案
  └── 监控与容灾
```

### 1.2 需求分析

**功能性需求（Functional Requirements）：**

- 系统提供的核心功能，即用户能做什么
- 示例：用户能够创建短链接、用户能够发送消息

**非功能性需求（Non-Functional Requirements）：**

| 维度 | 说明 | 典型指标 |
|------|------|----------|
| 高可用性 | 系统持续可用 | 99.99%（年宕机 < 52分钟） |
| 低延迟 | 响应速度快 | P99 < 200ms |
| 高吞吐 | 处理大量请求 | 10万+ QPS |
| 可扩展性 | 水平扩展能力 | 线性扩展 |
| 一致性 | 数据正确性 | 强一致/最终一致 |
| 持久性 | 数据不丢失 | 多副本、WAL |

### 1.3 容量估算模板

```
假设条件：
- DAU（日活用户）: 1亿
- 每用户每天平均操作: 10次
- 读写比: 10:1

QPS估算：
- 日请求量 = 1亿 × 10 = 10亿
- 平均QPS = 10亿 / 86400 ≈ 11,574
- 峰值QPS = 平均QPS × 3 ≈ 35,000
- 读QPS ≈ 32,000，写QPS ≈ 3,200

存储估算：
- 每条数据平均大小: 500 bytes
- 日新增数据 = 10亿 × 500B = 500GB
- 年新增数据 = 500GB × 365 ≈ 180TB

带宽估算：
- 入流量 = 3,200 × 500B = 1.6MB/s
- 出流量 = 32,000 × 500B = 16MB/s
```

### 1.4 常见 Trade-off

**一致性 vs 可用性（CAP定理）：**

```
面试问：如何在一致性和可用性之间做选择？

答：取决于业务场景：
- 金融交易 → 选择一致性（CP系统），宁可不可用也不能数据错误
- 社交Feed → 选择可用性（AP系统），短暂不一致可接受
- 电商库存 → 核心路径强一致（扣减），查询路径最终一致
```

**延迟 vs 吞吐：**

- 批处理增加吞吐，但单条延迟上升
- 同步写入降低延迟，但限制吞吐
- 缓存降低读延迟，但引入一致性问题

---

## 二、经典系统设计题

### 2.1 短链接系统（URL Shortener）

#### 需求分析

```
功能性需求：
1. 给定长URL，生成短链接
2. 访问短链接，重定向到原始URL
3. 可选：自定义短链接、过期时间、统计点击量

非功能性需求：
- 高可用：核心重定向服务 99.99%
- 低延迟：重定向 < 50ms
- 短链接不可预测（安全性）
```

#### 容量估算

```
假设：每天创建1亿条短链接，读写比 100:1
写QPS = 1亿 / 86400 ≈ 1,160
读QPS = 1,160 × 100 = 116,000
存储（5年）= 1亿 × 365 × 5 × 500B ≈ 91TB
```

#### API设计

```
POST /api/v1/shorten
Request:  { "long_url": "https://...", "expiry": "2025-12-31" }
Response: { "short_url": "https://t.cn/abc123", "created_at": "..." }

GET /:shortCode
Response: 301/302 Redirect to long_url
```

#### 数据模型

```sql
CREATE TABLE url_mapping (
    id          BIGINT PRIMARY KEY AUTO_INCREMENT,
    short_code  VARCHAR(7) UNIQUE NOT NULL,
    long_url    TEXT NOT NULL,
    user_id     BIGINT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at  TIMESTAMP,
    click_count BIGINT DEFAULT 0,
    INDEX idx_short_code (short_code)
);
```

#### 核心设计：短码生成

```python
# 方案一：哈希 + Base62
import hashlib, string

BASE62 = string.digits + string.ascii_letters  # 0-9a-zA-Z

def to_base62(num):
    """将数字转换为Base62编码"""
    if num == 0:
        return BASE62[0]
    result = []
    while num > 0:
        result.append(BASE62[num % 62])
        num //= 62
    return ''.join(reversed(result))

def generate_short_code(long_url):
    """MD5哈希取前7位Base62"""
    md5 = hashlib.md5(long_url.encode()).hexdigest()
    num = int(md5[:12], 16)  # 取前12位十六进制
    return to_base62(num)[:7]  # 截取7位，62^7 ≈ 3.5万亿

# 方案二：分布式ID生成器（Snowflake）+ Base62
# 优点：保证唯一性，无需检测冲突
# 缺点：ID递增，可预测
```

#### 301 vs 302重定向

```
面试问：短链接重定向应该用301还是302？

答：
- 301（永久重定向）：浏览器缓存，后续直接跳转，减少服务器压力
  缺点：无法统计点击量
- 302（临时重定向）：每次都经过服务器
  优点：可以统计点击、做A/B测试、动态修改目标URL

实际选择：大多数短链接服务使用302，因为统计功能是核心需求。
```

#### 高层架构

```
Client → Load Balancer → API Server → Cache (Redis)
                                     ↓ miss
                                   Database (MySQL)
                                     ↓ 异步
                                   Analytics Service → ClickHouse
```

#### 缓存策略

```python
# 读取流程（Cache-Aside）
def redirect(short_code):
    # 1. 查缓存
    long_url = redis.get(f"url:{short_code}")
    if long_url:
        return redirect_302(long_url)
    
    # 2. 查数据库
    record = db.query("SELECT long_url FROM url_mapping WHERE short_code = ?", short_code)
    if not record:
        return 404
    
    # 3. 写入缓存（设置TTL）
    redis.setex(f"url:{short_code}", 3600 * 24, record.long_url)
    return redirect_302(record.long_url)
```

---

### 2.2 Feed流系统（Twitter/微博）

#### 需求分析

```
功能性需求：
1. 用户发布推文（文本、图片）
2. 用户查看自己的Timeline（关注者的推文）
3. 关注/取关其他用户

非功能性需求：
- 读多写少，Timeline查询延迟 < 200ms
- 高可用，最终一致性可接受
- 支持大V（千万粉丝）场景
```

#### 核心设计：推模型 vs 拉模型

```
推模型（Fan-out on Write）：
  用户发推 → 异步写入所有粉丝的Timeline缓存
  优点：读取极快（直接读缓存）
  缺点：大V发推时写扩散巨大（1000万粉丝 = 1000万次写入）

拉模型（Fan-out on Read）：
  用户查看Timeline → 实时从关注列表中拉取最新推文 → 合并排序
  优点：写入简单
  缺点：读取慢，需要合并多个源的数据

混合模型（Twitter实际方案）：
  普通用户 → 推模型（粉丝数 < 5000）
  大V用户 → 拉模型（粉丝数 > 5000）
  Timeline = 推模型缓存 + 实时拉取大V推文 → 合并
```

#### 数据模型

```sql
-- 推文表
CREATE TABLE tweets (
    tweet_id   BIGINT PRIMARY KEY,  -- Snowflake ID
    user_id    BIGINT NOT NULL,
    content    TEXT,
    media_urls JSON,
    created_at TIMESTAMP,
    INDEX idx_user_time (user_id, created_at DESC)
);

-- 关注关系表
CREATE TABLE follows (
    follower_id  BIGINT,
    followee_id  BIGINT,
    created_at   TIMESTAMP,
    PRIMARY KEY (follower_id, followee_id),
    INDEX idx_followee (followee_id)
);

-- Timeline缓存（Redis Sorted Set）
-- Key: timeline:{user_id}
-- Score: tweet_created_at (时间戳)
-- Member: tweet_id
```

#### Fanout服务实现

```python
async def publish_tweet(user_id, content):
    # 1. 写入推文表
    tweet_id = snowflake.next_id()
    db.insert("tweets", tweet_id=tweet_id, user_id=user_id, content=content)
    
    # 2. 获取粉丝列表
    followers = db.query("SELECT follower_id FROM follows WHERE followee_id = ?", user_id)
    
    # 3. 判断推拉模型
    if len(followers) > 5000:
        # 大V：不推送，读取时实时拉取
        return tweet_id
    
    # 4. 异步推送到粉丝Timeline（消息队列）
    for batch in chunk(followers, 1000):
        mq.send("fanout_queue", {
            "tweet_id": tweet_id,
            "follower_ids": batch,
            "created_at": time.time()
        })
    
    return tweet_id

# Fanout消费者
def fanout_consumer(message):
    tweet_id = message["tweet_id"]
    for follower_id in message["follower_ids"]:
        redis.zadd(f"timeline:{follower_id}", {tweet_id: message["created_at"]})
        redis.zremrangebyrank(f"timeline:{follower_id}", 0, -801)  # 只保留最新800条
```

---

### 2.3 即时通讯系统（IM/Chat）

#### 核心挑战

```
1. 实时性：消息秒达
2. 可靠性：消息不丢失、不重复、保序
3. 已读未读状态同步
4. 离线消息推送
5. 海量连接管理
```

#### WebSocket长连接管理

```javascript
// 连接管理服务
class ConnectionManager {
    constructor() {
        this.connections = new Map(); // userId -> WebSocket
    }
    
    addConnection(userId, ws) {
        this.connections.set(userId, ws);
        // 注册到Redis，记录用户连接到哪台服务器
        redis.hset('user_connections', userId, SERVER_ID);
    }
    
    async sendMessage(targetUserId, message) {
        const ws = this.connections.get(targetUserId);
        if (ws) {
            // 用户在当前服务器
            ws.send(JSON.stringify(message));
        } else {
            // 查找用户在哪台服务器，通过消息队列转发
            const serverId = await redis.hget('user_connections', targetUserId);
            if (serverId) {
                mq.publish(`server:${serverId}`, message);
            } else {
                // 用户离线，存储离线消息
                await storeOfflineMessage(targetUserId, message);
            }
        }
    }
}
```

#### 消息存储与同步

```
消息存储模型（写扩散 vs 读扩散）：

写扩散（每个会话参与者存一份）：
  优点：读取简单，按收件箱查
  缺点：群聊写扩散大（500人群 = 500次写入）

读扩散（消息只存一份，按会话ID查）：
  优点：写入简单
  缺点：多会话需要合并查询

实际方案：单聊用写扩散，群聊用读扩散
```

```sql
-- 消息表（按会话分表）
CREATE TABLE messages (
    msg_id        BIGINT PRIMARY KEY,
    conversation_id BIGINT NOT NULL,
    sender_id     BIGINT NOT NULL,
    content       TEXT,
    msg_type      TINYINT,  -- 1:文本 2:图片 3:语音
    created_at    TIMESTAMP,
    INDEX idx_conv_time (conversation_id, created_at)
);

-- 已读状态（每个用户在每个会话中已读到哪条消息）
CREATE TABLE read_cursors (
    user_id          BIGINT,
    conversation_id  BIGINT,
    last_read_msg_id BIGINT,
    PRIMARY KEY (user_id, conversation_id)
);
```

---

### 2.4 秒杀系统

#### 核心挑战与解决方案

```
挑战：短时间内极高并发（百万级QPS），且库存有限

核心原则：
1. 请求尽量拦截在上游（CDN → Nginx → 应用层 → 数据库）
2. 读多写少，缓存为王
3. 异步处理，削峰填谷
```

#### 多级限流架构

```
用户请求 → CDN静态资源 → Nginx限流（令牌桶）
         → 应用层校验（登录态、黑名单、验证码）
         → Redis预扣库存
         → 消息队列异步下单
         → 数据库最终扣减
```

#### 库存扣减方案

```python
# Redis + Lua脚本原子扣减库存
DEDUCT_STOCK_LUA = """
local stock = tonumber(redis.call('GET', KEYS[1]))
if stock and stock > 0 then
    redis.call('DECR', KEYS[1])
    return 1  -- 扣减成功
else
    return 0  -- 库存不足
end
"""

async def seckill(user_id, item_id):
    # 1. 基础校验
    if not check_login(user_id):
        return "请先登录"
    if redis.sismember(f"seckill:bought:{item_id}", user_id):
        return "请勿重复购买"
    
    # 2. Redis原子扣减库存
    result = redis.eval(DEDUCT_STOCK_LUA, 1, f"seckill:stock:{item_id}")
    if result == 0:
        return "商品已售罄"
    
    # 3. 发送消息队列，异步创建订单
    mq.send("order_queue", {
        "user_id": user_id,
        "item_id": item_id,
        "timestamp": time.time()
    })
    
    # 4. 标记用户已购买
    redis.sadd(f"seckill:bought:{item_id}", user_id)
    
    return "下单成功，请等待支付"
```

#### 分布式锁防超卖

```python
# Redis分布式锁（Redisson方案）
import redis
import uuid
import time

class DistributedLock:
    def __init__(self, redis_client, key, ttl=10):
        self.redis = redis_client
        self.key = f"lock:{key}"
        self.ttl = ttl
        self.token = str(uuid.uuid4())
    
    def acquire(self):
        """获取锁"""
        return self.redis.set(self.key, self.token, nx=True, ex=self.ttl)
    
    def release(self):
        """释放锁（Lua脚本保证原子性）"""
        lua = """
        if redis.call('GET', KEYS[1]) == ARGV[1] then
            return redis.call('DEL', KEYS[1])
        else
            return 0
        end
        """
        return self.redis.eval(lua, 1, self.key, self.token)
```

---

### 2.5 分布式文件存储（类Google Drive）

#### 核心功能设计

```
功能性需求：
1. 文件上传/下载
2. 文件版本管理
3. 文件同步（多设备）
4. 文件分享

非功能性需求：
- 支持大文件（GB级别）
- 断点续传
- 文件去重（相同内容只存一份）
```

#### 文件分片上传

```javascript
// 前端：大文件分片上传
class ChunkUploader {
    constructor(file, chunkSize = 5 * 1024 * 1024) { // 5MB per chunk
        this.file = file;
        this.chunkSize = chunkSize;
        this.totalChunks = Math.ceil(file.size / chunkSize);
    }
    
    async upload() {
        // 1. 计算文件指纹（用于去重）
        const fileHash = await this.calculateHash();
        
        // 2. 请求上传初始化，获取uploadId
        const { uploadId, existingChunks } = await fetch('/api/upload/init', {
            method: 'POST',
            body: JSON.stringify({
                fileName: this.file.name,
                fileSize: this.file.size,
                fileHash: fileHash,
                totalChunks: this.totalChunks
            })
        }).then(r => r.json());
        
        // 3. 秒传检测
        if (existingChunks === 'COMPLETE') {
            console.log('秒传成功！文件已存在');
            return;
        }
        
        // 4. 断点续传：只上传未完成的分片
        const uploaded = new Set(existingChunks);
        for (let i = 0; i < this.totalChunks; i++) {
            if (uploaded.has(i)) continue; // 跳过已上传分片
            
            const start = i * this.chunkSize;
            const end = Math.min(start + this.chunkSize, this.file.size);
            const chunk = this.file.slice(start, end);
            
            await this.uploadChunk(uploadId, i, chunk);
        }
        
        // 5. 合并分片
        await fetch(`/api/upload/complete/${uploadId}`, { method: 'POST' });
    }
    
    async calculateHash() {
        // 抽样哈希：首尾各取2MB + 中间取2MB，避免全量计算
        const sampleSize = 2 * 1024 * 1024;
        const chunks = [];
        chunks.push(this.file.slice(0, sampleSize));
        chunks.push(this.file.slice(this.file.size / 2, this.file.size / 2 + sampleSize));
        chunks.push(this.file.slice(-sampleSize));
        
        const buffer = await new Blob(chunks).arrayBuffer();
        const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
        return Array.from(new Uint8Array(hashBuffer)).map(b => b.toString(16).padStart(2, '0')).join('');
    }
}
```

---

### 2.6 搜索自动补全（TypeAhead）

#### Trie树实现

```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
        self.hot_score = 0  # 搜索热度
        self.top_results = []  # 缓存该前缀下的Top K结果

class AutoComplete:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, word, score):
        """插入一个搜索词及其热度分数"""
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            # 更新该前缀下的Top K结果
            self._update_top_k(node, word, score)
        node.is_end = True
        node.hot_score = score
    
    def search(self, prefix, k=10):
        """根据前缀返回Top K热门搜索建议"""
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        return node.top_results[:k]
    
    def _update_top_k(self, node, word, score, k=10):
        """维护每个节点的Top K列表"""
        node.top_results.append((word, score))
        node.top_results.sort(key=lambda x: -x[1])
        node.top_results = node.top_results[:k]
```

#### 实际生产优化

```
1. 分层缓存：浏览器缓存 → CDN → Redis → Trie服务
2. 防抖请求：用户停止输入300ms后才发送请求
3. 异步更新：搜索热度通过Kafka异步更新Trie树
4. 分片：按首字母将Trie分布到不同机器
5. 个性化：结合用户搜索历史调整排序
```

---

### 2.7 限流器设计（Rate Limiter）

#### 四种限流算法对比

```python
# 1. 固定窗口计数器
class FixedWindowCounter:
    """简单但有边界突发问题：窗口切换瞬间可能有2倍流量"""
    def __init__(self, limit, window_sec):
        self.limit = limit
        self.window_sec = window_sec
        self.counts = {}  # window_key -> count
    
    def allow(self, key):
        window = int(time.time() / self.window_sec)
        window_key = f"{key}:{window}"
        count = self.counts.get(window_key, 0)
        if count >= self.limit:
            return False
        self.counts[window_key] = count + 1
        return True

# 2. 滑动窗口日志
class SlidingWindowLog:
    """精确但内存消耗大，需要存储每个请求的时间戳"""
    def __init__(self, limit, window_sec):
        self.limit = limit
        self.window_sec = window_sec
        self.logs = {}  # key -> [timestamps]
    
    def allow(self, key):
        now = time.time()
        if key not in self.logs:
            self.logs[key] = []
        # 移除过期时间戳
        self.logs[key] = [t for t in self.logs[key] if now - t < self.window_sec]
        if len(self.logs[key]) >= self.limit:
            return False
        self.logs[key].append(now)
        return True

# 3. 令牌桶算法
class TokenBucket:
    """允许突发流量，适合大多数场景"""
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
    
    def allow(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

# 4. 漏桶算法
class LeakyBucket:
    """固定速率处理，流量整形"""
    def __init__(self, capacity, leak_rate):
        self.capacity = capacity
        self.leak_rate = leak_rate  # requests per second
        self.water = 0
        self.last_leak = time.time()
    
    def allow(self):
        now = time.time()
        elapsed = now - self.last_leak
        self.water = max(0, self.water - elapsed * self.leak_rate)
        self.last_leak = now
        if self.water < self.capacity:
            self.water += 1
            return True
        return False
```

#### 分布式限流（Redis实现）

```lua
-- Redis + Lua实现滑动窗口限流
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- 移除窗口外的记录
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- 获取当前窗口内的请求数
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, now .. ':' .. math.random())
    redis.call('EXPIRE', key, window)
    return 1  -- 允许
else
    return 0  -- 拒绝
end
```

---

### 2.8 KV存储引擎

#### LSM-Tree架构

```
写入流程：
  Client → WAL(Write-Ahead Log) → MemTable(内存跳表)
           ↓ MemTable满时
         Flush → SSTable(磁盘有序文件)
           ↓ SSTable积累
         Compaction → 合并SSTable

读取流程：
  Client → MemTable → Level 0 SSTable → Level 1 SSTable → ...
           ↑ Bloom Filter 快速判断key是否存在
```

#### 核心组件实现

```python
import bisect, os, json, hashlib

class MemTable:
    """内存中的有序KV存储（简化版跳表用排序列表代替）"""
    def __init__(self, max_size=1024 * 1024):  # 1MB
        self.data = {}  # key -> value
        self.size = 0
        self.max_size = max_size
    
    def put(self, key, value):
        old_size = len(self.data.get(key, b''))
        self.data[key] = value
        self.size += len(key) + len(value) - old_size
    
    def get(self, key):
        return self.data.get(key)
    
    def is_full(self):
        return self.size >= self.max_size
    
    def flush_to_sstable(self, path):
        """将MemTable写入磁盘SSTable"""
        sorted_items = sorted(self.data.items())
        with open(path, 'w') as f:
            for key, value in sorted_items:
                f.write(json.dumps({"key": key, "value": value}) + '\n')
        self.data.clear()
        self.size = 0

class BloomFilter:
    """布隆过滤器：快速判断key是否可能存在"""
    def __init__(self, size=1024 * 1024, hash_count=3):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [0] * size
    
    def add(self, key):
        for i in range(self.hash_count):
            idx = int(hashlib.md5(f"{key}:{i}".encode()).hexdigest(), 16) % self.size
            self.bit_array[idx] = 1
    
    def might_contain(self, key):
        for i in range(self.hash_count):
            idx = int(hashlib.md5(f"{key}:{i}".encode()).hexdigest(), 16) % self.size
            if self.bit_array[idx] == 0:
                return False  # 一定不存在
        return True  # 可能存在（有误判率）
```

---

## 三、前端特有系统设计

### 3.1 设计一个组件库

```
核心考虑点：
1. 架构设计
   - Monorepo管理（pnpm workspace / turborepo）
   - 每个组件独立包发布
   - 按需引入（Tree-shaking友好）

2. 组件设计原则
   - 无障碍（WAI-ARIA）
   - 受控/非受控模式
   - 组合模式（Compound Components）
   - 样式方案：CSS Variables + CSS-in-JS / Tailwind

3. 开发体验
   - Storybook文档 + 可交互Playground
   - TypeScript类型完整
   - 单元测试 + 视觉回归测试

4. 构建发布
   - ESM + CJS双格式
   - 按需加载 babel-plugin
   - 语义化版本 + Changeset管理
```

### 3.2 设计在线文档编辑器

```
核心挑战：多人实时协同编辑

解决方案对比：
┌──────────┬─────────────────────┬─────────────────────┐
│          │ OT (Operational     │ CRDT (Conflict-free │
│          │ Transformation)     │ Replicated Data Type│
├──────────┼─────────────────────┼─────────────────────┤
│ 原理     │ 操作变换，需要中央  │ 数据结构天然支持    │
│          │ 服务器协调          │ 合并，去中心化      │
├──────────┼─────────────────────┼─────────────────────┤
│ 代表产品 │ Google Docs         │ Figma               │
├──────────┼─────────────────────┼─────────────────────┤
│ 开源实现 │ ShareDB             │ Yjs, Automerge      │
├──────────┼─────────────────────┼─────────────────────┤
│ 优点     │ 成熟，带宽占用小    │ 天然支持离线编辑    │
├──────────┼─────────────────────┼─────────────────────┤
│ 缺点     │ 服务器逻辑复杂      │ 内存占用较大        │
└──────────┴─────────────────────┴─────────────────────┘

技术栈选型：
编辑器引擎：ProseMirror / Slate.js / Lexical
协同方案：Yjs + WebSocket Provider
游标同步：Awareness Protocol
```

### 3.3 设计前端监控系统

```javascript
// 前端监控SDK核心设计
class MonitorSDK {
    constructor(config) {
        this.config = config;
        this.queue = [];       // 上报队列
        this.init();
    }
    
    init() {
        this.captureErrors();       // 错误监控
        this.capturePerformance();  // 性能监控
        this.captureUserBehavior(); // 行为监控
    }
    
    // 1. 错误监控
    captureErrors() {
        // JS运行时错误
        window.addEventListener('error', (event) => {
            this.report({ type: 'js_error', message: event.message, stack: event.error?.stack });
        });
        // Promise未捕获异常
        window.addEventListener('unhandledrejection', (event) => {
            this.report({ type: 'promise_error', reason: String(event.reason) });
        });
        // 资源加载失败
        window.addEventListener('error', (event) => {
            if (event.target?.src || event.target?.href) {
                this.report({ type: 'resource_error', url: event.target.src || event.target.href });
            }
        }, true);
    }
    
    // 2. 性能监控
    capturePerformance() {
        new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
                if (entry.entryType === 'largest-contentful-paint') {
                    this.report({ type: 'performance', metric: 'LCP', value: entry.startTime });
                }
            }
        }).observe({ entryTypes: ['largest-contentful-paint'] });
        
        // Web Vitals: FCP, LCP, CLS, FID, TTFB, INP
    }
    
    // 3. 上报策略
    report(data) {
        this.queue.push({ ...data, timestamp: Date.now(), url: location.href });
        if (this.queue.length >= 10) {
            this.flush();
        }
    }
    
    flush() {
        if (this.queue.length === 0) return;
        const data = [...this.queue];
        this.queue = [];
        // 使用 sendBeacon 保证页面关闭时也能上报
        navigator.sendBeacon('/api/monitor', JSON.stringify(data));
    }
}
```

### 3.4 设计A/B测试平台

```
核心架构：
1. 实验配置服务：创建实验、设定分流比例
2. 分流SDK：根据userId哈希稳定分流
3. 数据采集：曝光埋点 + 转化埋点
4. 统计分析：假设检验（p-value）、置信区间

分流算法核心：
  bucket = hash(userId + experimentId) % 100
  如果 bucket < trafficPercent → 进入实验组
  否则 → 对照组

关键原则：
- 同一用户多次访问分到同一组（稳定性）
- 不同实验间互不干扰（正交分流）
- 支持灰度放量（10% → 50% → 100%）
```

### 3.5 设计图片懒加载SDK

```javascript
class LazyLoad {
    constructor(options = {}) {
        this.threshold = options.threshold || '200px';
        this.placeholder = options.placeholder || 'data:image/gif;base64,R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==';
        this.observer = null;
        this.init();
    }
    
    init() {
        // 优先使用 IntersectionObserver
        if ('IntersectionObserver' in window) {
            this.observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.loadImage(entry.target);
                            this.observer.unobserve(entry.target);
                        }
                    });
                },
                { rootMargin: this.threshold }
            );
        }
        this.observe();
    }
    
    observe() {
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = this.placeholder;
            if (this.observer) {
                this.observer.observe(img);
            } else {
                // 降级：scroll事件 + getBoundingClientRect
                this.fallbackLazy(img);
            }
        });
    }
    
    loadImage(img) {
        const src = img.dataset.src;
        // 预加载：先用Image对象加载，成功后替换
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = src;
            img.classList.add('loaded');
        };
        tempImg.onerror = () => {
            img.src = this.placeholder;
            img.classList.add('error');
        };
        tempImg.src = src;
    }
}
```

---

## 四、分布式系统核心概念

### 4.1 CAP定理

```
CAP定理：分布式系统最多同时满足以下三者中的两个：
- C（Consistency）：一致性，所有节点看到的数据一样
- A（Availability）：可用性，每个请求都能收到响应
- P（Partition Tolerance）：分区容错性，网络分区时系统仍能运行

由于网络分区不可避免，实际选择是 CP 或 AP：
- CP系统：ZooKeeper, etcd, HBase → 网络分区时拒绝服务
- AP系统：Cassandra, DynamoDB → 网络分区时返回可能过时的数据
```

### 4.2 一致性模型

```
强一致性（Linearizability）：
  写完立刻可读到最新值
  实现：Raft/Paxos共识协议
  代表：etcd, ZooKeeper
  代价：延迟高，吞吐低

最终一致性（Eventual Consistency）：
  写入后经过一段时间，所有节点最终一致
  实现：Gossip协议、Anti-Entropy
  代表：Cassandra, DynamoDB
  优点：高可用，低延迟

因果一致性（Causal Consistency）：
  有因果关系的操作按序可见
  实现：向量时钟（Vector Clock）
```

### 4.3 分布式事务

```
2PC（两阶段提交）：
  阶段1（Prepare）：协调者询问所有参与者是否可提交
  阶段2（Commit/Abort）：协调者根据投票结果决定提交或回滚
  缺点：同步阻塞、单点故障、数据不一致风险

TCC（Try-Confirm-Cancel）：
  Try：预留资源（冻结库存、冻结余额）
  Confirm：确认操作（实际扣减）
  Cancel：取消操作（释放冻结）
  优点：每个阶段都是本地事务，性能好
  缺点：业务侵入性强，需要实现三个接口

Saga：
  将长事务拆分为多个本地事务，每个有对应的补偿操作
  T1 → T2 → T3（任何一步失败，执行补偿 C3 → C2 → C1）
  编排方式：协同式（事件驱动） / 编排式（中央协调器）
  适用：跨服务的长流程（订单创建 → 扣库存 → 扣余额）
```

### 4.4 一致性哈希

```
传统哈希：hash(key) % N → 节点增减导致大量数据迁移
一致性哈希：将节点和数据映射到同一个哈希环上

核心原理：
  哈希环：[0, 2^32)
  节点映射：hash(nodeIP) → 环上位置
  数据映射：hash(key) → 顺时针找到第一个节点

虚拟节点优化：
  每个物理节点创建多个虚拟节点（如150个）
  解决数据分布不均匀问题

节点增删时：
  新增节点：只影响环上相邻的数据迁移
  删除节点：数据转移到下一个节点
  影响范围：1/N的数据（N为节点数）
```

### 4.5 分库分表

```
垂直分库：按业务拆分（用户库、订单库、商品库）
垂直分表：将大字段拆分到扩展表

水平分库分表：
  分片策略：
  - 范围分片：id 1-100万→库1, 100-200万→库2（热点问题）
  - 哈希分片：hash(id) % N（分布均匀，扩容困难）
  - 一致性哈希分片：扩容只迁移部分数据

  分片键选择原则：
  1. 高频查询字段（如user_id）
  2. 数据分布均匀
  3. 避免跨分片查询

  常见问题：
  - 跨分片JOIN：冗余数据 / 应用层聚合
  - 全局唯一ID：Snowflake / 号段模式
  - 跨分片排序分页：各分片取TopN再合并（性能差）
  - 数据迁移：双写方案 → 校验 → 切换
```

---

## 五、面试高频问答

### Q1：如何设计一个高并发系统？

```
回答框架：
1. 请求层面：CDN加速、负载均衡、动静分离
2. 应用层面：无状态设计、水平扩展、异步处理
3. 缓存层面：多级缓存（浏览器→CDN→Redis→本地缓存）
4. 数据层面：读写分离、分库分表、NoSQL
5. 消息层面：消息队列削峰、异步解耦
6. 限流降级：令牌桶限流、熔断降级、核心链路保护
```

### Q2：缓存穿透、击穿、雪崩如何解决？

```
缓存穿透（查询不存在的数据）：
  - 布隆过滤器拦截
  - 缓存空值（设置短TTL）

缓存击穿（热点key过期，大量请求直接打DB）：
  - 互斥锁（singleflight）：只放一个请求去DB，其他等待
  - 热点key永不过期（后台异步更新）

缓存雪崩（大量key同时过期）：
  - TTL加随机偏移量
  - 多级缓存兜底
  - 集群部署Redis（避免整体宕机）
```

### Q3：消息队列如何保证消息不丢失？

```
三个阶段：
1. 生产者 → MQ：同步发送 + 确认机制（ACK）
2. MQ存储：持久化到磁盘 + 多副本复制
3. MQ → 消费者：手动ACK（处理完再确认）

Kafka为例：
  生产者：acks=all（所有ISR副本确认）
  Broker：replication.factor=3, min.insync.replicas=2
  消费者：手动提交offset，处理成功后再提交
```

### Q4：如何保证分布式系统的幂等性？

```
幂等性：同一操作执行一次和执行多次效果一样

常见方案：
1. 唯一ID + 去重表
   INSERT INTO dedup_table (request_id) VALUES (?) ON DUPLICATE KEY IGNORE
   
2. 数据库乐观锁
   UPDATE account SET balance = balance - 100 WHERE id = ? AND version = ?
   
3. Token机制
   下单前获取token → 下单时携带token → 服务端验证token是否已使用

4. 状态机
   订单状态：待支付 → 已支付 → 已发货
   每次操作校验当前状态，不合法则拒绝
```

---

> 系统设计没有标准答案，关键在于展示清晰的思维过程、合理的trade-off分析、以及对实际工程问题的理解深度。面试中要主动与面试官沟通，不断确认需求和约束。

# Node.js 数据库操作面试指南

## 一、MySQL 操作

> **面试题：Node.js 中如何操作 MySQL 数据库？mysql2 和 Sequelize 有什么区别？**

### 1.1 mysql2 原生驱动

`mysql2` 是 Node.js 中最常用的 MySQL 驱动，兼容 `mysql` 库的 API，但性能更好，支持 Promise 和预处理语句。

```javascript
// 基本连接
const mysql = require('mysql2/promise');

// 创建连接
const connection = await mysql.createConnection({
  host: 'localhost',
  port: 3306,
  user: 'root',
  password: 'password',
  database: 'mydb',
  charset: 'utf8mb4'
});

// 查询
const [rows] = await connection.execute('SELECT * FROM users WHERE id = ?', [1]);
console.log(rows);

// 插入
const [result] = await connection.execute(
  'INSERT INTO users (name, email) VALUES (?, ?)',
  ['Alice', 'alice@example.com']
);
console.log('插入 ID:', result.insertId);

// 更新
const [updateResult] = await connection.execute(
  'UPDATE users SET name = ? WHERE id = ?',
  ['Bob', 1]
);
console.log('影响行数:', updateResult.affectedRows);

// 删除
await connection.execute('DELETE FROM users WHERE id = ?', [1]);

// 关闭连接
await connection.end();
```

### 1.2 连接池（Pool）

```javascript
const mysql = require('mysql2/promise');

// 创建连接池（推荐生产环境使用）
const pool = mysql.createPool({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'mydb',
  waitForConnections: true,    // 连接池满时等待
  connectionLimit: 10,          // 最大连接数
  maxIdle: 10,                  // 最大空闲连接数
  idleTimeout: 60000,           // 空闲连接超时时间（毫秒）
  queueLimit: 0,                // 等待队列限制（0 = 无限制）
  enableKeepAlive: true,        // 保持连接活跃
  keepAliveInitialDelay: 0
});

// 使用连接池执行查询
const [rows] = await pool.execute('SELECT * FROM users');

// 或者获取单个连接
const conn = await pool.getConnection();
try {
  const [rows] = await conn.execute('SELECT * FROM users');
  return rows;
} finally {
  conn.release(); // 必须释放连接回池中
}
```

### 1.3 Sequelize ORM

```javascript
const { Sequelize, DataTypes, Op } = require('sequelize');

// 创建实例
const sequelize = new Sequelize('mydb', 'root', 'password', {
  host: 'localhost',
  dialect: 'mysql',
  pool: {
    max: 10,
    min: 0,
    acquire: 30000,  // 获取连接的超时时间
    idle: 10000      // 连接空闲超时时间
  },
  logging: console.log, // 打印 SQL（生产环境设为 false）
});

// 测试连接
await sequelize.authenticate();

// 定义模型
const User = sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  name: {
    type: DataTypes.STRING(100),
    allowNull: false,
    validate: {
      notEmpty: true,
      len: [2, 100]
    }
  },
  email: {
    type: DataTypes.STRING(255),
    unique: true,
    validate: { isEmail: true }
  },
  age: {
    type: DataTypes.INTEGER,
    validate: { min: 0, max: 150 }
  },
  status: {
    type: DataTypes.ENUM('active', 'inactive'),
    defaultValue: 'active'
  }
}, {
  tableName: 'users',
  timestamps: true,     // 自动添加 createdAt/updatedAt
  paranoid: true,        // 软删除（添加 deletedAt）
  underscored: true,     // 使用下划线命名法（created_at 而不是 createdAt）
  indexes: [
    { fields: ['email'], unique: true },
    { fields: ['status'] }
  ]
});

// 关联关系
const Post = sequelize.define('Post', {
  title: DataTypes.STRING,
  content: DataTypes.TEXT,
});

User.hasMany(Post, { foreignKey: 'userId', as: 'posts' });
Post.belongsTo(User, { foreignKey: 'userId', as: 'author' });

// CRUD 操作
// 创建
const user = await User.create({ name: 'Alice', email: 'alice@example.com' });

// 批量创建
await User.bulkCreate([
  { name: 'Bob', email: 'bob@example.com' },
  { name: 'Charlie', email: 'charlie@example.com' }
]);

// 查询
const users = await User.findAll({
  where: {
    status: 'active',
    age: { [Op.gte]: 18 },
    name: { [Op.like]: '%alice%' }
  },
  include: [{ model: Post, as: 'posts' }],
  order: [['createdAt', 'DESC']],
  limit: 10,
  offset: 0,
  attributes: ['id', 'name', 'email'] // 选择字段
});

// findOne
const user = await User.findOne({ where: { email: 'alice@example.com' } });

// findByPk
const user = await User.findByPk(1);

// findOrCreate
const [user, created] = await User.findOrCreate({
  where: { email: 'alice@example.com' },
  defaults: { name: 'Alice' }
});

// 更新
await User.update({ status: 'inactive' }, { where: { id: 1 } });

// 删除
await User.destroy({ where: { id: 1 } });

// 聚合查询
const count = await User.count({ where: { status: 'active' } });
const maxAge = await User.max('age');
const result = await User.findAll({
  attributes: [
    'status',
    [sequelize.fn('COUNT', sequelize.col('id')), 'count']
  ],
  group: ['status']
});
```

---

## 二、PostgreSQL 操作

> **面试题：Node.js 中如何操作 PostgreSQL？pg 库有什么特点？**

```javascript
const { Pool, Client } = require('pg');

// 连接池
const pool = new Pool({
  host: 'localhost',
  port: 5432,
  user: 'postgres',
  password: 'password',
  database: 'mydb',
  max: 20,                // 连接池最大连接数
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// 查询
const { rows } = await pool.query('SELECT * FROM users WHERE id = $1', [1]);
console.log(rows[0]);

// PostgreSQL 特有功能

// 1. JSONB 操作
await pool.query(
  `INSERT INTO products (name, metadata) VALUES ($1, $2)`,
  ['Phone', JSON.stringify({ brand: 'Apple', color: 'black' })]
);

// JSONB 查询
const { rows } = await pool.query(
  `SELECT * FROM products WHERE metadata->>'brand' = $1`,
  ['Apple']
);

// 2. 数组类型
await pool.query(
  `INSERT INTO users (name, tags) VALUES ($1, $2)`,
  ['Alice', ['admin', 'developer']]
);

// 3. 全文搜索
const { rows } = await pool.query(
  `SELECT * FROM articles WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('english', $1)`,
  ['node & javascript']
);

// 4. 监听/通知（实时功能）
const client = new Client();
await client.connect();

client.on('notification', (msg) => {
  console.log('收到通知:', msg.channel, msg.payload);
});

await client.query('LISTEN new_order');
// 另一个连接中执行：NOTIFY new_order, '{"orderId": 123}'

// 5. 使用连接池中的单个连接执行事务
const client = await pool.connect();
try {
  await client.query('BEGIN');
  await client.query('INSERT INTO accounts (id, balance) VALUES ($1, $2)', [1, 100]);
  await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [50, 1]);
  await client.query('COMMIT');
} catch (e) {
  await client.query('ROLLBACK');
  throw e;
} finally {
  client.release();
}
```

---

## 三、MongoDB 操作

> **面试题：Node.js 中如何操作 MongoDB？Mongoose 的 Schema 设计有哪些最佳实践？**

### 3.1 原生 MongoDB 驱动

```javascript
const { MongoClient, ObjectId } = require('mongodb');

const client = new MongoClient('mongodb://localhost:27017', {
  maxPoolSize: 10,
  minPoolSize: 2,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
});

await client.connect();
const db = client.db('mydb');
const collection = db.collection('users');

// 插入
const result = await collection.insertOne({ name: 'Alice', age: 30 });
await collection.insertMany([{ name: 'Bob' }, { name: 'Charlie' }]);

// 查询
const user = await collection.findOne({ _id: new ObjectId('...') });
const users = await collection.find({ age: { $gte: 18 } }).toArray();

// 更新
await collection.updateOne({ _id: new ObjectId('...') }, { $set: { name: 'NewName' } });
await collection.updateMany({ status: 'active' }, { $inc: { visits: 1 } });

// 删除
await collection.deleteOne({ _id: new ObjectId('...') });

// 聚合管道
const result = await collection.aggregate([
  { $match: { status: 'active' } },
  { $group: { _id: '$city', count: { $sum: 1 }, avgAge: { $avg: '$age' } } },
  { $sort: { count: -1 } },
  { $limit: 10 }
]).toArray();

// 索引
await collection.createIndex({ email: 1 }, { unique: true });
await collection.createIndex({ name: 'text', bio: 'text' }); // 文本索引

// 关闭连接
await client.close();
```

### 3.2 Mongoose ODM

```javascript
const mongoose = require('mongoose');

// 连接
await mongoose.connect('mongodb://localhost:27017/mydb', {
  maxPoolSize: 10,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
});

// 监听连接事件
mongoose.connection.on('connected', () => console.log('MongoDB 已连接'));
mongoose.connection.on('error', (err) => console.error('MongoDB 连接错误:', err));
mongoose.connection.on('disconnected', () => console.log('MongoDB 断开连接'));

// 定义 Schema
const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: [true, '用户名必填'],
    trim: true,
    minlength: [2, '用户名至少 2 个字符'],
    maxlength: [50, '用户名最多 50 个字符']
  },
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    validate: {
      validator: function(v) {
        return /^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/.test(v);
      },
      message: '邮箱格式不正确'
    }
  },
  password: {
    type: String,
    required: true,
    select: false  // 查询时默认不返回
  },
  role: {
    type: String,
    enum: ['user', 'admin', 'moderator'],
    default: 'user'
  },
  profile: {
    avatar: String,
    bio: { type: String, maxlength: 500 }
  },
  tags: [String],
  friends: [{ type: mongoose.Schema.Types.ObjectId, ref: 'User' }],
}, {
  timestamps: true,  // 自动添加 createdAt/updatedAt
  toJSON: { virtuals: true },
  toObject: { virtuals: true }
});

// 虚拟属性
userSchema.virtual('posts', {
  ref: 'Post',
  localField: '_id',
  foreignField: 'author'
});

// 索引
userSchema.index({ email: 1 }, { unique: true });
userSchema.index({ name: 'text', 'profile.bio': 'text' });
userSchema.index({ createdAt: -1 });

// 中间件（钩子）
userSchema.pre('save', async function(next) {
  if (!this.isModified('password')) return next();
  const bcrypt = require('bcrypt');
  this.password = await bcrypt.hash(this.password, 10);
  next();
});

userSchema.post('save', function(doc) {
  console.log('用户已保存:', doc.name);
});

// 实例方法
userSchema.methods.comparePassword = async function(candidatePassword) {
  const bcrypt = require('bcrypt');
  return bcrypt.compare(candidatePassword, this.password);
};

// 静态方法
userSchema.statics.findByEmail = function(email) {
  return this.findOne({ email: email.toLowerCase() });
};

// 查询辅助方法
userSchema.query.active = function() {
  return this.where({ status: 'active' });
};

// 创建模型
const User = mongoose.model('User', userSchema);

// CRUD 操作
// 创建
const user = new User({ name: 'Alice', email: 'alice@example.com', password: '123456' });
await user.save();
// 或
const user = await User.create({ name: 'Bob', email: 'bob@example.com', password: '123456' });

// 查询
const users = await User.find({ role: 'user' })
  .select('name email')
  .sort({ createdAt: -1 })
  .skip(0)
  .limit(10)
  .lean(); // lean() 返回普通 JS 对象（性能更好）

// 关联查询（populate）
const user = await User.findById(id).populate('friends', 'name email');
const userWithPosts = await User.findById(id).populate({
  path: 'posts',
  select: 'title createdAt',
  options: { sort: { createdAt: -1 }, limit: 5 }
});

// 更新
await User.findByIdAndUpdate(id, { $set: { name: 'NewName' } }, { new: true, runValidators: true });

// 删除
await User.findByIdAndDelete(id);
```

---

## 四、Redis 操作

> **面试题：Node.js 中如何使用 Redis？ioredis 有什么优势？**

```javascript
const Redis = require('ioredis');

// 创建连接
const redis = new Redis({
  host: '127.0.0.1',
  port: 6379,
  password: 'your-password',
  db: 0,
  retryStrategy(times) {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  maxRetriesPerRequest: 3,
  lazyConnect: true,        // 延迟连接
  enableReadyCheck: true
});

await redis.connect();

// 字符串操作
await redis.set('key', 'value');
await redis.set('key', 'value', 'EX', 3600); // 设置过期时间（秒）
await redis.set('key', 'value', 'PX', 60000); // 毫秒
await redis.set('key', 'value', 'NX');        // 仅当 key 不存在时设置
const value = await redis.get('key');
await redis.del('key');
await redis.incr('counter');
await redis.incrby('counter', 10);

// Hash 操作
await redis.hset('user:1', 'name', 'Alice', 'age', '30');
await redis.hget('user:1', 'name');
const user = await redis.hgetall('user:1'); // { name: 'Alice', age: '30' }

// List 操作
await redis.lpush('queue', 'task1', 'task2');
await redis.rpop('queue');
await redis.lrange('queue', 0, -1);

// Set 操作
await redis.sadd('tags', 'node', 'javascript');
await redis.smembers('tags');
await redis.sismember('tags', 'node');

// Sorted Set（有序集合）
await redis.zadd('leaderboard', 100, 'Alice', 90, 'Bob', 80, 'Charlie');
const top3 = await redis.zrevrange('leaderboard', 0, 2, 'WITHSCORES');

// 过期时间
await redis.expire('key', 3600);
await redis.ttl('key'); // 剩余过期时间（秒）

// Pipeline（批量操作，减少网络往返）
const pipeline = redis.pipeline();
pipeline.set('key1', 'value1');
pipeline.set('key2', 'value2');
pipeline.get('key1');
pipeline.get('key2');
const results = await pipeline.exec();

// 事务
const multi = redis.multi();
multi.set('key1', 'value1');
multi.set('key2', 'value2');
const results = await multi.exec();

// 发布/订阅
const sub = new Redis();
const pub = new Redis();

sub.subscribe('channel1', 'channel2');
sub.on('message', (channel, message) => {
  console.log(`收到消息 [${channel}]: ${message}`);
});

pub.publish('channel1', JSON.stringify({ type: 'notification', data: 'Hello' }));

// Lua 脚本（原子操作）
const result = await redis.eval(
  `
  local current = redis.call('GET', KEYS[1])
  if current == ARGV[1] then
    redis.call('DEL', KEYS[1])
    return 1
  end
  return 0
  `,
  1,           // KEY 的数量
  'lock:key',  // KEYS[1]
  'lock-value' // ARGV[1]
);

// 关闭连接
await redis.quit();
```

---

## 五、ORM vs 原生查询

> **面试题：使用 ORM 和原生 SQL 查询各有什么优缺点？什么时候该用哪个？**

| 维度             | ORM（Sequelize/Mongoose）             | 原生查询（mysql2/pg）                  |
| ---------------- | ------------------------------------- | -------------------------------------- |
| 开发效率         | 高（自动生成 SQL，模型抽象）          | 低（手写 SQL）                         |
| 学习曲线         | 需要学习 ORM API                      | 需要掌握 SQL                           |
| 性能             | 较低（额外的抽象层开销）              | 较高（直接执行 SQL）                   |
| 复杂查询         | 可能受限，复杂查询需要回退到原生 SQL  | 灵活，可以写任意复杂的 SQL             |
| 数据库迁移       | 内置支持                              | 需要额外工具                           |
| 类型安全         | 模型提供一定的类型约束                | 无（需配合 TypeScript 类型）           |
| 数据库切换       | 相对容易（抽象层屏蔽差异）            | 困难（SQL 方言不同）                   |
| 关联查询         | 自动处理（eager/lazy loading）        | 手动 JOIN                              |
| 适用场景         | CRUD 为主、快速开发、中小型项目       | 复杂查询、高性能要求、大型项目         |

**最佳实践**：结合使用。在日常的 CRUD 操作中使用 ORM 提高效率，在复杂查询或性能关键路径上使用原生 SQL。

```javascript
// Sequelize 中使用原生查询
const [results] = await sequelize.query(
  `SELECT u.name, COUNT(p.id) as post_count 
   FROM users u 
   LEFT JOIN posts p ON u.id = p.user_id 
   WHERE u.status = :status 
   GROUP BY u.id 
   HAVING post_count > :minPosts`,
  {
    replacements: { status: 'active', minPosts: 5 },
    type: Sequelize.QueryTypes.SELECT
  }
);
```

---

## 六、连接池管理

> **面试题：什么是数据库连接池？为什么需要连接池？如何正确配置？**

### 6.1 为什么需要连接池

数据库连接是昂贵的资源：
1. **TCP 三次握手**：建立连接需要网络往返
2. **认证过程**：用户名密码验证
3. **资源分配**：数据库为每个连接分配内存和线程
4. **连接数限制**：数据库有最大连接数限制

连接池预先创建一组连接并重复使用，避免频繁创建和销毁连接的开销。

### 6.2 连接池配置原则

```javascript
// 连接池大小的经验公式
// connections = (核心数 * 2) + 磁盘数
// 对于 4 核 CPU + 1 个 SSD，最优连接数约为 9-10

const pool = mysql.createPool({
  connectionLimit: 10,          // 最大连接数
  waitForConnections: true,     // 连接池满时等待（而不是报错）
  queueLimit: 0,                // 等待队列大小（0 = 无限）
  enableKeepAlive: true,        // TCP KeepAlive
  keepAliveInitialDelay: 10000, // KeepAlive 初始延迟
});

// 监控连接池状态
setInterval(() => {
  const poolStatus = {
    totalConnections: pool.pool._allConnections.length,
    freeConnections: pool.pool._freeConnections.length,
    queuedRequests: pool.pool._connectionQueue.length,
  };
  console.log('连接池状态:', poolStatus);
}, 30000);

// 优雅关闭
process.on('SIGTERM', async () => {
  await pool.end();
  console.log('连接池已关闭');
  process.exit(0);
});
```

---

## 七、事务处理

> **面试题：Node.js 中如何处理数据库事务？什么场景需要用事务？**

事务确保一组数据库操作要么全部成功，要么全部回滚（ACID 特性）。

### 7.1 mysql2 事务

```javascript
const connection = await pool.getConnection();
try {
  await connection.beginTransaction();

  // 转账操作：A 向 B 转 100 元
  await connection.execute(
    'UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?',
    [100, accountA, 100]
  );
  
  await connection.execute(
    'UPDATE accounts SET balance = balance + ? WHERE id = ?',
    [100, accountB]
  );

  await connection.commit();
  console.log('转账成功');
} catch (err) {
  await connection.rollback();
  console.error('转账失败，已回滚:', err);
  throw err;
} finally {
  connection.release();
}
```

### 7.2 Sequelize 事务

```javascript
// 方式1：托管事务（自动提交/回滚，推荐）
const result = await sequelize.transaction(async (t) => {
  const user = await User.create({ name: 'Alice', email: 'alice@example.com' }, { transaction: t });
  await Profile.create({ userId: user.id, bio: 'Hello' }, { transaction: t });
  return user;
  // 如果回调函数成功返回，事务自动提交
  // 如果回调函数抛出异常，事务自动回滚
});

// 方式2：非托管事务（手动控制）
const t = await sequelize.transaction();
try {
  await User.create({ name: 'Alice' }, { transaction: t });
  await Post.create({ title: 'Hello' }, { transaction: t });
  await t.commit();
} catch (err) {
  await t.rollback();
  throw err;
}

// 事务隔离级别
const { Transaction } = require('sequelize');
await sequelize.transaction({
  isolationLevel: Transaction.ISOLATION_LEVELS.SERIALIZABLE
}, async (t) => {
  // ...
});
```

### 7.3 Mongoose 事务（需要 MongoDB 副本集）

```javascript
const session = await mongoose.startSession();
session.startTransaction();

try {
  const user = await User.create([{ name: 'Alice' }], { session });
  await Post.create([{ title: 'Hello', author: user[0]._id }], { session });
  
  await session.commitTransaction();
} catch (err) {
  await session.abortTransaction();
  throw err;
} finally {
  session.endSession();
}
```

---

## 八、数据库迁移

> **面试题：什么是数据库迁移？在 Node.js 中如何管理数据库迁移？**

数据库迁移（Migration）是对数据库 schema 进行版本控制的方式，每次迁移包含 `up`（执行变更）和 `down`（回滚变更）两个操作。

### Sequelize 迁移

```bash
# 安装 CLI
npm install -g sequelize-cli

# 初始化
sequelize init

# 创建迁移文件
sequelize migration:generate --name create-users-table
```

```javascript
// migrations/20240101000000-create-users-table.js
module.exports = {
  up: async (queryInterface, Sequelize) => {
    await queryInterface.createTable('users', {
      id: {
        type: Sequelize.INTEGER,
        primaryKey: true,
        autoIncrement: true,
      },
      name: {
        type: Sequelize.STRING(100),
        allowNull: false,
      },
      email: {
        type: Sequelize.STRING(255),
        unique: true,
        allowNull: false,
      },
      created_at: {
        type: Sequelize.DATE,
        defaultValue: Sequelize.literal('CURRENT_TIMESTAMP'),
      },
      updated_at: {
        type: Sequelize.DATE,
        defaultValue: Sequelize.literal('CURRENT_TIMESTAMP'),
      },
    });

    // 添加索引
    await queryInterface.addIndex('users', ['email'], { unique: true });
  },

  down: async (queryInterface) => {
    await queryInterface.dropTable('users');
  },
};
```

```bash
# 运行迁移
sequelize db:migrate

# 回滚上一次迁移
sequelize db:migrate:undo

# 回滚所有迁移
sequelize db:migrate:undo:all

# 种子数据
sequelize seed:generate --name demo-users
sequelize db:seed:all
```

---

## 九、N+1 查询问题

> **面试题：什么是 N+1 查询问题？在 Node.js 中如何解决？**

### 9.1 什么是 N+1 问题

N+1 问题是指在查询关联数据时，先执行 1 次查询获取主表数据（N 条记录），然后对每条记录执行 1 次查询获取关联数据，共执行 N+1 次查询。

```javascript
// N+1 问题示例
const posts = await Post.findAll(); // 1 次查询获取所有文章

for (const post of posts) {
  // 每篇文章都要查询一次作者，如果有 100 篇文章就是 100 次查询
  const author = await User.findByPk(post.userId);
  post.author = author;
}
// 总共 101 次查询！
```

### 9.2 解决方案

```javascript
// 方案1：预加载（Eager Loading）- Sequelize
const posts = await Post.findAll({
  include: [{ model: User, as: 'author' }]
});
// 只执行 2 次查询：SELECT * FROM posts; SELECT * FROM users WHERE id IN (...)

// 方案2：批量加载 - Mongoose populate
const posts = await Post.find().populate('author', 'name email');
// 只执行 2 次查询

// 方案3：DataLoader（GraphQL 场景常用）
const DataLoader = require('dataloader');

const userLoader = new DataLoader(async (userIds) => {
  const users = await User.findAll({
    where: { id: userIds }
  });
  // DataLoader 要求返回的数组顺序和 keys 一致
  const userMap = new Map(users.map(u => [u.id, u]));
  return userIds.map(id => userMap.get(id) || null);
});

// 使用 DataLoader
const author = await userLoader.load(post.userId); // 自动批量化

// 方案4：手动批量查询
const posts = await Post.findAll();
const userIds = [...new Set(posts.map(p => p.userId))];
const users = await User.findAll({ where: { id: userIds } });
const userMap = new Map(users.map(u => [u.id, u]));
posts.forEach(p => { p.author = userMap.get(p.userId); });
```

---

## 十、数据库索引优化

> **面试题：什么是数据库索引？如何在 Node.js 项目中正确使用索引？**

### 10.1 索引的基本概念

索引是一种数据结构（通常是 B+ 树），用于加速数据库的查询操作。类比字典的目录，通过索引可以快速定位到数据行，避免全表扫描。

### 10.2 索引类型

```sql
-- 主键索引（自动创建）
PRIMARY KEY (id)

-- 唯一索引
CREATE UNIQUE INDEX idx_email ON users(email);

-- 普通索引
CREATE INDEX idx_status ON users(status);

-- 复合索引（注意最左前缀原则）
CREATE INDEX idx_status_created ON users(status, created_at);

-- 全文索引
CREATE FULLTEXT INDEX idx_content ON articles(title, content);
```

### 10.3 在 Node.js ORM 中定义索引

```javascript
// Sequelize
const User = sequelize.define('User', {
  email: { type: DataTypes.STRING, unique: true }, // 唯一索引
  name: DataTypes.STRING,
  status: DataTypes.STRING,
}, {
  indexes: [
    { fields: ['status'] },
    { fields: ['status', 'createdAt'] }, // 复合索引
    { fields: ['name'], type: 'FULLTEXT' } // 全文索引
  ]
});

// Mongoose
const userSchema = new mongoose.Schema({ /* ... */ });
userSchema.index({ email: 1 }, { unique: true });
userSchema.index({ status: 1, createdAt: -1 }); // 复合索引
userSchema.index({ name: 'text', bio: 'text' }); // 文本索引
userSchema.index({ location: '2dsphere' }); // 地理空间索引
```

### 10.4 查询分析

```javascript
// MySQL - EXPLAIN
const [analysis] = await pool.execute('EXPLAIN SELECT * FROM users WHERE status = ? AND created_at > ?', ['active', '2024-01-01']);
console.log(analysis);
// 关注 type（ALL/index/range/ref/const）、rows、Extra

// MongoDB - explain
const explanation = await User.find({ status: 'active' }).explain('executionStats');
console.log(explanation.executionStats);
// 关注 totalDocsExamined vs totalDocsReturned
```

### 10.5 索引使用原则

1. **频繁查询的字段**添加索引
2. **WHERE、JOIN、ORDER BY** 中使用的字段优先建索引
3. **选择性高的字段**更适合建索引（如 email 比 gender 更适合）
4. **复合索引遵循最左前缀原则**：`(A, B, C)` 索引可用于 `A`、`A,B`、`A,B,C` 的查询，但不能用于单独的 `B` 或 `C`
5. **避免过多索引**：索引会减慢写入速度，增加存储空间
6. **避免在索引列上使用函数或运算**
7. **定期分析慢查询并优化索引**

---

## 十一、缓存策略

> **面试题：什么是缓存穿透、缓存击穿和缓存雪崩？如何解决？**

### 11.1 缓存穿透

**定义**：查询一个不存在的数据，缓存中没有，每次请求都直接打到数据库。

**场景**：恶意攻击，大量请求不存在的 ID。

```javascript
// 解决方案1：缓存空值
async function getUser(id) {
  const cacheKey = `user:${id}`;
  let user = await redis.get(cacheKey);
  
  if (user !== null) {
    return user === 'NULL' ? null : JSON.parse(user);
  }
  
  user = await db.query('SELECT * FROM users WHERE id = ?', [id]);
  
  if (user) {
    await redis.set(cacheKey, JSON.stringify(user), 'EX', 3600);
  } else {
    // 缓存空值，过期时间短一些
    await redis.set(cacheKey, 'NULL', 'EX', 60);
  }
  
  return user;
}

// 解决方案2：布隆过滤器（Bloom Filter）
const BloomFilter = require('bloom-filters');
const filter = new BloomFilter.BloomFilter(10000, 0.01);

// 初始化时加载所有有效 ID
const allIds = await db.query('SELECT id FROM users');
allIds.forEach(row => filter.add(String(row.id)));

async function getUserSafe(id) {
  // 先检查布隆过滤器
  if (!filter.has(String(id))) {
    return null; // 一定不存在
  }
  // 可能存在，查缓存和数据库
  return getUser(id);
}
```

### 11.2 缓存击穿

**定义**：某个热点 key 过期的瞬间，大量并发请求同时访问该 key，全部打到数据库。

```javascript
// 解决方案1：互斥锁（分布式锁）
async function getUserWithLock(id) {
  const cacheKey = `user:${id}`;
  const lockKey = `lock:user:${id}`;
  
  let user = await redis.get(cacheKey);
  if (user) return JSON.parse(user);
  
  // 尝试获取锁
  const locked = await redis.set(lockKey, '1', 'NX', 'EX', 10);
  
  if (locked) {
    try {
      // 获取锁成功，查数据库
      user = await db.query('SELECT * FROM users WHERE id = ?', [id]);
      await redis.set(cacheKey, JSON.stringify(user), 'EX', 3600);
      return user;
    } finally {
      await redis.del(lockKey);
    }
  } else {
    // 获取锁失败，等待后重试
    await new Promise(resolve => setTimeout(resolve, 100));
    return getUserWithLock(id);
  }
}

// 解决方案2：逻辑过期（不设置 Redis TTL，在值中记录逻辑过期时间）
async function getUserLogicalExpiry(id) {
  const cacheKey = `user:${id}`;
  const cached = await redis.get(cacheKey);
  
  if (cached) {
    const { data, expireAt } = JSON.parse(cached);
    if (Date.now() < expireAt) {
      return data; // 未过期
    }
    // 逻辑过期，异步更新缓存
    refreshCacheAsync(id);
    return data; // 返回旧数据
  }
  
  return fetchAndCache(id);
}
```

### 11.3 缓存雪崩

**定义**：大量缓存 key 在同一时间过期，或者 Redis 服务宕机，导致大量请求涌向数据库。

```javascript
// 解决方案1：过期时间添加随机值
async function cacheWithJitter(key, data, baseTTL = 3600) {
  const jitter = Math.floor(Math.random() * 600); // 0-600秒的随机值
  await redis.set(key, JSON.stringify(data), 'EX', baseTTL + jitter);
}

// 解决方案2：多级缓存
class MultiLevelCache {
  constructor(redis, localCacheTTL = 60) {
    this.redis = redis;
    this.localCache = new Map();
    this.localCacheTTL = localCacheTTL;
  }

  async get(key) {
    // L1：本地缓存
    const local = this.localCache.get(key);
    if (local && local.expireAt > Date.now()) {
      return local.value;
    }

    // L2：Redis 缓存
    const remote = await this.redis.get(key);
    if (remote) {
      const value = JSON.parse(remote);
      this.localCache.set(key, {
        value,
        expireAt: Date.now() + this.localCacheTTL * 1000
      });
      return value;
    }

    return null;
  }

  async set(key, value, ttl = 3600) {
    const jitter = Math.floor(Math.random() * 300);
    await this.redis.set(key, JSON.stringify(value), 'EX', ttl + jitter);
    this.localCache.set(key, {
      value,
      expireAt: Date.now() + this.localCacheTTL * 1000
    });
  }
}

// 解决方案3：熔断降级
// 当数据库压力过大时，返回默认值或错误提示
// 配合 Circuit Breaker 模式使用
```

---

## 常见面试题汇总

> **Q：ORM 的 Eager Loading 和 Lazy Loading 有什么区别？**

Eager Loading（急切加载）在查询主数据时同时加载关联数据，通常通过 JOIN 或额外的批量查询实现。Lazy Loading（懒加载）在首次访问关联属性时才触发查询。Eager Loading 适用于确定需要关联数据的场景，避免 N+1 问题；Lazy Loading 适用于不确定是否需要关联数据的场景，但可能产生 N+1 问题。

> **Q：Redis 为什么快？**

1. 纯内存操作，不涉及磁盘 I/O；2. 单线程模型避免了上下文切换和锁竞争；3. 使用 I/O 多路复用（epoll）处理并发连接；4. 高效的数据结构（如 SDS、跳表、压缩列表等）。Redis 6.0+ 引入了多线程处理网络 I/O，但命令执行仍是单线程。

> **Q：数据库连接池大小设为多少合适？**

一般公式为 `connections = (CPU 核心数 * 2) + 磁盘数`。对于 4 核 CPU + SSD，约为 9-10 个连接。但实际应以性能测试为准。过大的连接池反而会降低性能（上下文切换开销）。连接池大小也要考虑数据库服务器的最大连接数限制和应用实例数量。

> **Q：MongoDB 和 MySQL 如何选择？**

MySQL（关系型）适合数据结构固定、需要事务支持、强一致性的场景（如金融、电商订单）。MongoDB（文档型）适合数据结构灵活多变、读多写少、需要水平扩展的场景（如内容管理、日志记录、物联网数据）。实际项目中可以同时使用：核心业务数据用 MySQL，非结构化数据/日志用 MongoDB。
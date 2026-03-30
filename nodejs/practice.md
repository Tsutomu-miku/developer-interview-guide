# Node.js 最佳实践与进阶面试指南

## 一、错误处理最佳实践

> **面试题：Node.js 中如何正确处理错误？操作错误和程序错误有什么区别？**

### 1.1 操作错误 vs 程序错误

**操作错误（Operational Errors）**：运行时可预见的错误，如网络断开、文件不存在、请求超时、用户输入无效等。这些错误是应用正常运行中可能遇到的，需要正确处理和恢复。

**程序错误（Programmer Errors）**：代码 bug，如传入错误类型的参数、读取 undefined 的属性、内存泄漏等。这些错误应该通过修复代码来解决。

```javascript
// 操作错误 - 应该处理
async function readConfig(path) {
  try {
    return await fs.promises.readFile(path, 'utf8');
  } catch (err) {
    if (err.code === 'ENOENT') {
      // 文件不存在，返回默认配置
      return getDefaultConfig();
    }
    throw err; // 其他错误继续抛出
  }
}

// 程序错误 - 应该修复代码
function divide(a, b) {
  if (typeof a !== 'number' || typeof b !== 'number') {
    throw new TypeError('参数必须是数字'); // 参数校验
  }
  if (b === 0) {
    throw new RangeError('除数不能为零');
  }
  return a / b;
}
```

### 1.2 自定义错误类

```javascript
// 基础应用错误
class AppError extends Error {
  constructor(message, statusCode, errorCode) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
    this.errorCode = errorCode;
    this.isOperational = true; // 标记为操作错误
    Error.captureStackTrace(this, this.constructor);
  }
}

// 具体的错误类型
class NotFoundError extends AppError {
  constructor(resource = '资源') {
    super(`${resource}不存在`, 404, 'NOT_FOUND');
  }
}

class ValidationError extends AppError {
  constructor(message, details) {
    super(message, 400, 'VALIDATION_ERROR');
    this.details = details;
  }
}

class UnauthorizedError extends AppError {
  constructor(message = '未授权') {
    super(message, 401, 'UNAUTHORIZED');
  }
}

class ForbiddenError extends AppError {
  constructor(message = '禁止访问') {
    super(message, 403, 'FORBIDDEN');
  }
}
```

### 1.3 全局错误处理

```javascript
// 未捕获的异常
process.on('uncaughtException', (err) => {
  console.error('未捕获的异常:', err);
  // 记录日志
  logger.fatal({ err }, '未捕获的异常');
  // 优雅关闭后退出
  gracefulShutdown().then(() => process.exit(1));
});

// 未处理的 Promise 拒绝
process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的 Promise 拒绝:', reason);
  logger.error({ reason }, '未处理的 Promise 拒绝');
  // Node.js 15+ 默认行为是终止进程
});

// 优雅关闭
async function gracefulShutdown() {
  console.log('正在优雅关闭...');
  
  // 停止接受新请求
  server.close();
  
  // 等待现有请求完成（设置超时）
  const timeout = setTimeout(() => {
    console.error('强制关闭');
    process.exit(1);
  }, 30000);
  
  // 关闭数据库连接
  await pool.end();
  await redis.quit();
  await mongoose.disconnect();
  
  clearTimeout(timeout);
  console.log('优雅关闭完成');
}

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);
```

### 1.4 异步错误处理模式

```javascript
// Express 中的异步错误处理
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

app.get('/users', asyncHandler(async (req, res) => {
  const users = await userService.findAll(); // 错误自动传递给 next
  res.json(users);
}));

// 统一的错误响应格式
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  
  const response = {
    success: false,
    error: {
      code: err.errorCode || 'INTERNAL_ERROR',
      message: err.isOperational ? err.message : '服务器内部错误',
    }
  };
  
  if (process.env.NODE_ENV === 'development') {
    response.error.stack = err.stack;
    response.error.details = err.details;
  }
  
  // 记录日志
  if (statusCode >= 500) {
    logger.error({ err, req: { method: req.method, url: req.url } }, err.message);
  }
  
  res.status(statusCode).json(response);
});
```

---

## 二、日志管理

> **面试题：Node.js 项目中如何做日志管理？winston 和 pino 有什么区别？**

### 2.1 winston

```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'my-api' },
  transports: [
    // 错误日志单独写文件
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error',
      maxsize: 10 * 1024 * 1024, // 10MB
      maxFiles: 5,
      tailable: true
    }),
    // 所有日志
    new winston.transports.File({
      filename: 'logs/combined.log',
      maxsize: 10 * 1024 * 1024,
      maxFiles: 10
    }),
  ],
});

// 开发环境添加控制台输出
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

// 使用
logger.info('服务器启动', { port: 3000 });
logger.error('数据库连接失败', { error: err.message, stack: err.stack });
logger.warn('请求超时', { url: '/api/users', duration: '5000ms' });
```

### 2.2 pino（高性能推荐）

```javascript
const pino = require('pino');

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  transport: process.env.NODE_ENV === 'development'
    ? { target: 'pino-pretty', options: { colorize: true } }
    : undefined,
  serializers: {
    req: pino.stdSerializers.req,
    res: pino.stdSerializers.res,
    err: pino.stdSerializers.err,
  },
  redact: ['req.headers.authorization', 'req.headers.cookie'], // 脱敏
});

// pino 比 winston 快 5-10 倍
// 因为它使用 JSON.stringify 而不是格式化字符串
// 日志输出到 stdout，由外部工具（如 pino-tee）负责分发

// Express 集成
const pinoHttp = require('pino-http');
app.use(pinoHttp({ logger }));

// Fastify 内置 pino
const fastify = require('fastify')({ logger: true });
```

### 2.3 winston vs pino 对比

| 特性       | winston                  | pino                     |
| ---------- | ------------------------ | ------------------------ |
| 性能       | 中等                     | 极高（快 5-10 倍）      |
| 格式化     | 内置丰富的 format        | JSON 输出，外部格式化    |
| 传输目标   | 内置多种 transport       | stdout，外部管道处理     |
| 生态系统   | 丰富                     | 增长中                   |
| API 风格   | 灵活多样                 | 简洁统一                 |
| 适用场景   | 通用项目                 | 高性能要求               |

---

## 三、安全最佳实践

> **面试题：Node.js 应用中有哪些常见的安全风险？如何防范？**

### 3.1 SQL 注入防护

```javascript
// 危险！直接拼接 SQL
const sql = `SELECT * FROM users WHERE name = '${userInput}'`;
// 如果 userInput = "'; DROP TABLE users; --"  就会删除整张表

// 正确：使用参数化查询
await pool.execute('SELECT * FROM users WHERE name = ?', [userInput]);

// Sequelize 自动防 SQL 注入
await User.findAll({ where: { name: userInput } });
```

### 3.2 XSS 防护

```javascript
// 输入过滤和输出编码
const xss = require('xss');

// 过滤用户输入中的 HTML
const cleanContent = xss(userInput);

// 设置安全响应头
const helmet = require('helmet');
app.use(helmet());
// helmet 会设置 Content-Security-Policy 等安全头

// 对于 API 响应，设置正确的 Content-Type
res.setHeader('Content-Type', 'application/json');
```

### 3.3 CSRF 防护

```javascript
const csrf = require('csurf');
const cookieParser = require('cookie-parser');

app.use(cookieParser());
app.use(csrf({ cookie: true }));

// 在表单中包含 CSRF token
app.get('/form', (req, res) => {
  res.render('form', { csrfToken: req.csrfToken() });
});

// 对于 SPA + API 的架构，通常使用以下替代方案：
// 1. SameSite Cookie
// 2. Double Submit Cookie
// 3. JWT Token（无 cookie = 无 CSRF）
```

### 3.4 Rate Limiting

```javascript
const rateLimit = require('express-rate-limit');
const RedisStore = require('rate-limit-redis');

// 基于 IP 的限流
const apiLimiter = rateLimit({
  store: new RedisStore({
    sendCommand: (...args) => redis.call(...args),
  }),
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: { error: '请求过于频繁' },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.ip,
});

app.use('/api/', apiLimiter);

// 登录接口更严格的限流
const loginLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1小时
  max: 5,
  message: { error: '登录尝试次数过多，请1小时后再试' }
});

app.post('/api/login', loginLimiter, loginController);
```

### 3.5 Helmet 安全头

```javascript
const helmet = require('helmet');

app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", 'data:', 'https:'],
    },
  },
  crossOriginEmbedderPolicy: true,
  crossOriginOpenerPolicy: true,
  crossOriginResourcePolicy: { policy: "same-site" },
  hsts: { maxAge: 31536000, includeSubDomains: true },
  noSniff: true,
  referrerPolicy: { policy: "strict-origin-when-cross-origin" },
}));
```

### 3.6 其他安全措施

```javascript
// 1. 环境变量管理敏感信息
require('dotenv').config();
const dbPassword = process.env.DB_PASSWORD;

// 2. 密码哈希
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 12);
const isMatch = await bcrypt.compare(password, hash);

// 3. 输入验证
const Joi = require('joi');
const schema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).max(128).required(),
  age: Joi.number().integer().min(0).max(150)
});
const { error, value } = schema.validate(req.body);

// 4. 防止 HTTP 参数污染
const hpp = require('hpp');
app.use(hpp());

// 5. 限制请求体大小
app.use(express.json({ limit: '10kb' }));

// 6. 依赖安全审计
// npm audit
// npm audit fix
```

---

## 四、性能优化

> **面试题：如何排查 Node.js 应用的性能问题？内存泄漏如何定位？**

### 4.1 内存泄漏排查

```javascript
// 常见内存泄漏原因
// 1. 全局变量不断增长
// 2. 闭包引用
// 3. 事件监听器未移除
// 4. 定时器未清理
// 5. 缓存无限增长

// 监控内存使用
setInterval(() => {
  const usage = process.memoryUsage();
  console.log({
    rss: `${(usage.rss / 1024 / 1024).toFixed(2)} MB`,       // 总内存
    heapTotal: `${(usage.heapTotal / 1024 / 1024).toFixed(2)} MB`, // V8 堆总大小
    heapUsed: `${(usage.heapUsed / 1024 / 1024).toFixed(2)} MB`,  // V8 堆使用量
    external: `${(usage.external / 1024 / 1024).toFixed(2)} MB`,  // C++ 对象内存
    arrayBuffers: `${(usage.arrayBuffers / 1024 / 1024).toFixed(2)} MB`
  });
}, 10000);

// 使用 --inspect 标志启动，配合 Chrome DevTools 分析堆快照
// node --inspect app.js
// 打开 chrome://inspect 进行分析

// 生成堆快照
const v8 = require('v8');
const fs = require('fs');

function takeHeapSnapshot() {
  const snapshotStream = v8.writeHeapSnapshot();
  console.log('堆快照已保存:', snapshotStream);
}

// 定期记录 GC 信息
// node --expose-gc --trace-gc app.js
```

### 4.2 CPU Profiling

```javascript
// 方式1：使用 --prof 标志
// node --prof app.js
// 生成 isolate-xxx.log 文件
// node --prof-process isolate-xxx.log > profile.txt

// 方式2：使用 v8-profiler-next
const profiler = require('v8-profiler-next');

function startProfiling(duration = 10000) {
  profiler.startProfiling('CPU Profile');
  
  setTimeout(() => {
    const profile = profiler.stopProfiling('CPU Profile');
    profile.export((error, result) => {
      fs.writeFileSync('cpu-profile.cpuprofile', result);
      profile.delete();
      console.log('CPU Profile 已保存');
    });
  }, duration);
}

// 方式3：使用 clinic.js（推荐）
// npm install -g clinic
// clinic doctor -- node app.js
// clinic flame -- node app.js
// clinic bubbleprof -- node app.js
```

### 4.3 性能优化技巧

```javascript
// 1. 使用流处理大数据
// 见 stream.md

// 2. 缓存（内存缓存 + Redis）
const NodeCache = require('node-cache');
const cache = new NodeCache({ stdTTL: 600, checkperiod: 120 });

// 3. 数据库查询优化
// - 添加索引
// - 避免 N+1 查询
// - 使用连接池
// - 只查询需要的字段

// 4. 压缩响应
const compression = require('compression');
app.use(compression());

// 5. 集群模式利用多核
const cluster = require('cluster');
const numCPUs = require('os').cpus().length;

// 6. 异步操作并行化
// 错误：串行执行
const user = await getUser(id);
const posts = await getPosts(id);
const comments = await getComments(id);

// 正确：并行执行
const [user, posts, comments] = await Promise.all([
  getUser(id),
  getPosts(id),
  getComments(id)
]);

// 7. 避免同步操作
// 不要在热路径上使用 fs.readFileSync, JSON.parse(大文件) 等

// 8. 使用 Worker Threads 处理 CPU 密集任务
```

---

## 五、测试

> **面试题：Node.js 项目中如何进行测试？单元测试、集成测试、E2E 测试有什么区别？**

### 5.1 测试金字塔

```
        /  E2E  \        少量 - 验证完整用户流程
       /Integration\     适量 - 验证模块之间的交互
      / Unit Tests  \    大量 - 验证单个函数/模块
```

### 5.2 单元测试（Jest）

```javascript
// user.service.js
class UserService {
  constructor(userRepository) {
    this.userRepository = userRepository;
  }

  async findById(id) {
    const user = await this.userRepository.findById(id);
    if (!user) throw new NotFoundError('用户');
    return user;
  }

  async create(data) {
    if (!data.email) throw new ValidationError('邮箱必填');
    return this.userRepository.create(data);
  }
}

// user.service.test.js
describe('UserService', () => {
  let userService;
  let mockRepository;

  beforeEach(() => {
    // Mock 依赖
    mockRepository = {
      findById: jest.fn(),
      create: jest.fn(),
    };
    userService = new UserService(mockRepository);
  });

  describe('findById', () => {
    it('应该返回用户', async () => {
      const mockUser = { id: '1', name: 'Alice' };
      mockRepository.findById.mockResolvedValue(mockUser);

      const result = await userService.findById('1');
      
      expect(result).toEqual(mockUser);
      expect(mockRepository.findById).toHaveBeenCalledWith('1');
    });

    it('用户不存在时应该抛出 NotFoundError', async () => {
      mockRepository.findById.mockResolvedValue(null);

      await expect(userService.findById('999'))
        .rejects
        .toThrow(NotFoundError);
    });
  });

  describe('create', () => {
    it('邮箱为空时应该抛出 ValidationError', async () => {
      await expect(userService.create({ name: 'Alice' }))
        .rejects
        .toThrow(ValidationError);
    });

    it('应该成功创建用户', async () => {
      const userData = { name: 'Alice', email: 'alice@example.com' };
      const createdUser = { id: '1', ...userData };
      mockRepository.create.mockResolvedValue(createdUser);

      const result = await userService.create(userData);
      
      expect(result).toEqual(createdUser);
      expect(mockRepository.create).toHaveBeenCalledWith(userData);
    });
  });
});
```

### 5.3 集成测试

```javascript
// app.integration.test.js
const request = require('supertest');
const app = require('../app');

describe('User API', () => {
  beforeAll(async () => {
    // 连接测试数据库
    await connectTestDB();
  });

  afterAll(async () => {
    await disconnectTestDB();
  });

  beforeEach(async () => {
    await clearDatabase();
  });

  describe('POST /api/users', () => {
    it('应该创建新用户', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({ name: 'Alice', email: 'alice@example.com' })
        .expect(201);

      expect(response.body).toMatchObject({
        name: 'Alice',
        email: 'alice@example.com'
      });
      expect(response.body).toHaveProperty('id');
    });

    it('缺少必填字段应返回 400', async () => {
      const response = await request(app)
        .post('/api/users')
        .send({ name: 'Alice' })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });

    it('邮箱重复应返回 409', async () => {
      await request(app)
        .post('/api/users')
        .send({ name: 'Alice', email: 'alice@example.com' });

      const response = await request(app)
        .post('/api/users')
        .send({ name: 'Bob', email: 'alice@example.com' })
        .expect(409);
    });
  });

  describe('GET /api/users/:id', () => {
    it('应该返回指定用户', async () => {
      const createRes = await request(app)
        .post('/api/users')
        .send({ name: 'Alice', email: 'alice@example.com' });

      const response = await request(app)
        .get(`/api/users/${createRes.body.id}`)
        .expect(200);

      expect(response.body.name).toBe('Alice');
    });

    it('用户不存在应返回 404', async () => {
      await request(app)
        .get('/api/users/nonexistent')
        .expect(404);
    });
  });
});
```

---

## 六、API 设计

> **面试题：RESTful API、GraphQL 和 gRPC 各有什么特点？如何选择？**

### 6.1 RESTful API

```javascript
// RESTful 设计原则
// 1. 使用名词（资源）而非动词
// GET    /api/users          获取用户列表
// GET    /api/users/:id      获取单个用户
// POST   /api/users          创建用户
// PUT    /api/users/:id      全量更新用户
// PATCH  /api/users/:id      部分更新用户
// DELETE /api/users/:id      删除用户

// 2. 嵌套资源
// GET /api/users/:userId/posts  获取某用户的文章

// 3. 查询参数用于过滤、排序、分页
// GET /api/users?status=active&sort=-createdAt&page=1&limit=20

// 4. 版本控制
// /api/v1/users
// 或通过 Header: Accept: application/vnd.myapi.v1+json

// 5. 统一响应格式
const response = {
  success: true,
  data: { id: 1, name: 'Alice' },
  meta: { page: 1, total: 100, limit: 20 }
};
```

### 6.2 GraphQL

```javascript
const { ApolloServer, gql } = require('apollo-server-express');

const typeDefs = gql`
  type User {
    id: ID!
    name: String!
    email: String!
    posts: [Post!]!
  }

  type Post {
    id: ID!
    title: String!
    content: String
    author: User!
  }

  type Query {
    users(page: Int, limit: Int): [User!]!
    user(id: ID!): User
  }

  type Mutation {
    createUser(name: String!, email: String!): User!
    updateUser(id: ID!, name: String, email: String): User!
  }
`;

const resolvers = {
  Query: {
    users: (_, { page, limit }) => userService.findAll(page, limit),
    user: (_, { id }) => userService.findById(id),
  },
  Mutation: {
    createUser: (_, args) => userService.create(args),
  },
  User: {
    posts: (user) => postService.findByUserId(user.id), // 字段级解析
  },
};

const server = new ApolloServer({ typeDefs, resolvers });
await server.start();
server.applyMiddleware({ app });
```

### 6.3 对比选型

| 特性         | REST         | GraphQL       | gRPC            |
| ------------ | ------------ | ------------- | --------------- |
| 数据格式     | JSON         | JSON          | Protocol Buffers |
| 传输协议     | HTTP/1.1     | HTTP/1.1      | HTTP/2          |
| 类型系统     | 无（需Swagger）| 强类型 Schema | 强类型 .proto   |
| 性能         | 中等         | 中等          | 高              |
| 灵活性       | 固定端点     | 按需查询      | 固定接口        |
| 适用场景     | 公开 API     | 前端驱动API   | 微服务间通信    |
| 学习曲线     | 低           | 中等          | 较高            |

---

## 七、认证与授权

> **面试题：JWT、Session、OAuth2 各自的原理和适用场景是什么？**

### 7.1 JWT（JSON Web Token）

```javascript
const jwt = require('jsonwebtoken');

const SECRET = process.env.JWT_SECRET;
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;

// 生成 Token
function generateTokens(user) {
  const accessToken = jwt.sign(
    { userId: user.id, role: user.role },
    SECRET,
    { expiresIn: '15m' } // 短期有效
  );

  const refreshToken = jwt.sign(
    { userId: user.id },
    REFRESH_SECRET,
    { expiresIn: '7d' } // 长期有效
  );

  return { accessToken, refreshToken };
}

// 验证中间件
function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: '未提供 Token' });
  }

  const token = authHeader.substring(7);
  try {
    const payload = jwt.verify(token, SECRET);
    req.user = payload;
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token 已过期' });
    }
    return res.status(401).json({ error: 'Token 无效' });
  }
}

// 刷新 Token
app.post('/api/refresh', async (req, res) => {
  const { refreshToken } = req.body;
  try {
    const payload = jwt.verify(refreshToken, REFRESH_SECRET);
    const user = await User.findByPk(payload.userId);
    const tokens = generateTokens(user);
    res.json(tokens);
  } catch {
    res.status(401).json({ error: 'Refresh Token 无效' });
  }
});

// 授权中间件
function authorize(...roles) {
  return (req, res, next) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: '权限不足' });
    }
    next();
  };
}

// 使用
app.get('/api/admin/users', authenticate, authorize('admin'), (req, res) => {
  // 只有 admin 角色才能访问
});
```

### 7.2 Session 认证

```javascript
const session = require('express-session');
const RedisStore = require('connect-redis').default;

app.use(session({
  store: new RedisStore({ client: redis }),
  secret: process.env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    maxAge: 24 * 60 * 60 * 1000, // 1天
    sameSite: 'strict'
  }
}));

// 登录
app.post('/api/login', async (req, res) => {
  const { email, password } = req.body;
  const user = await User.findByEmail(email);
  if (!user || !await bcrypt.compare(password, user.password)) {
    return res.status(401).json({ error: '邮箱或密码错误' });
  }
  req.session.userId = user.id;
  req.session.role = user.role;
  res.json({ message: '登录成功' });
});

// 认证中间件
function requireAuth(req, res, next) {
  if (!req.session.userId) {
    return res.status(401).json({ error: '未登录' });
  }
  next();
}
```

### 7.3 JWT vs Session

| 特性         | JWT                          | Session                        |
| ------------ | ---------------------------- | ------------------------------ |
| 存储位置     | 客户端（localStorage/Cookie）| 服务端（Redis/内存）           |
| 无状态性     | 无状态                       | 有状态                         |
| 扩展性       | 好（无需共享存储）           | 需要共享 Session 存储          |
| 安全性       | 无法即时吊销                 | 可以即时吊销                   |
| 性能         | 不需要查询存储               | 需要查询 Redis/内存            |
| 适用场景     | 分布式系统、移动端           | 传统 Web 应用                  |

---

## 八、文件上传与下载

> **面试题：Node.js 中如何实现文件上传和下载？如何处理大文件上传？**

```javascript
const multer = require('multer');
const path = require('path');

// 配置存储
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

// 文件过滤
const fileFilter = (req, file, cb) => {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('不支持的文件类型'), false);
  }
};

const upload = multer({
  storage,
  fileFilter,
  limits: { fileSize: 5 * 1024 * 1024 } // 5MB
});

// 单文件上传
app.post('/upload', upload.single('avatar'), (req, res) => {
  res.json({
    filename: req.file.filename,
    size: req.file.size,
    url: `/uploads/${req.file.filename}`
  });
});

// 多文件上传
app.post('/upload-multiple', upload.array('photos', 10), (req, res) => {
  res.json({ files: req.files.map(f => f.filename) });
});

// 文件下载
app.get('/download/:filename', (req, res) => {
  const filePath = path.join(__dirname, 'uploads', req.params.filename);
  res.download(filePath, req.params.filename, (err) => {
    if (err) res.status(404).json({ error: '文件不存在' });
  });
});

// 流式下载（大文件）
app.get('/download-stream/:filename', (req, res) => {
  const filePath = path.join(__dirname, 'uploads', req.params.filename);
  const stat = fs.statSync(filePath);
  
  res.setHeader('Content-Length', stat.size);
  res.setHeader('Content-Type', 'application/octet-stream');
  res.setHeader('Content-Disposition', `attachment; filename="${req.params.filename}"`);
  
  const stream = fs.createReadStream(filePath);
  stream.pipe(res);
});
```

---

## 九、定时任务

> **面试题：Node.js 中如何实现定时任务？**

```javascript
// 方式1：node-cron（适合简单的定时任务）
const cron = require('node-cron');

// 每天凌晨 2 点执行
cron.schedule('0 2 * * *', async () => {
  console.log('执行每日数据清理');
  await cleanOldData();
});

// 每 5 分钟执行
cron.schedule('*/5 * * * *', () => {
  console.log('检查健康状态');
});

// Cron 表达式: 秒(可选) 分 时 日 月 周
// * * * * * *
// │ │ │ │ │ │
// │ │ │ │ │ └── 周几 (0-7, 0和7都是周日)
// │ │ │ │ └──── 月 (1-12)
// │ │ │ └────── 日 (1-31)
// │ │ └──────── 时 (0-23)
// │ └────────── 分 (0-59)
// └──────────── 秒 (0-59, 可选)

// 方式2：BullMQ（分布式任务队列，推荐生产环境）
const { Queue, Worker } = require('bullmq');

const emailQueue = new Queue('email', { connection: redis });

// 添加延迟任务
await emailQueue.add('welcome', { userId: '123' }, {
  delay: 60000,         // 延迟 1 分钟执行
  attempts: 3,          // 失败重试 3 次
  backoff: { type: 'exponential', delay: 2000 },
  removeOnComplete: true,
  removeOnFail: 1000,
});

// 添加重复任务
await emailQueue.add('daily-report', { type: 'report' }, {
  repeat: { cron: '0 8 * * 1-5' } // 工作日早上 8 点
});

// 处理任务
const worker = new Worker('email', async (job) => {
  const { userId } = job.data;
  await sendEmail(userId);
  console.log(`邮件已发送给用户 ${userId}`);
}, { connection: redis, concurrency: 5 });

worker.on('completed', (job) => console.log(`任务 ${job.id} 完成`));
worker.on('failed', (job, err) => console.error(`任务 ${job.id} 失败:`, err));
```

---

## 十、消息队列

> **面试题：什么是消息队列？Node.js 中如何使用消息队列？**

### 10.1 RabbitMQ（amqplib）

```javascript
const amqp = require('amqplib');

// 生产者
async function publishMessage(queue, message) {
  const connection = await amqp.connect('amqp://localhost');
  const channel = await connection.createChannel();
  
  await channel.assertQueue(queue, { durable: true });
  channel.sendToQueue(queue, Buffer.from(JSON.stringify(message)), {
    persistent: true
  });
  
  console.log('消息已发送:', message);
  await channel.close();
  await connection.close();
}

// 消费者
async function consumeMessages(queue) {
  const connection = await amqp.connect('amqp://localhost');
  const channel = await connection.createChannel();
  
  await channel.assertQueue(queue, { durable: true });
  channel.prefetch(1); // 每次只处理一条消息
  
  channel.consume(queue, async (msg) => {
    const data = JSON.parse(msg.content.toString());
    console.log('收到消息:', data);
    
    try {
      await processMessage(data);
      channel.ack(msg); // 确认消息
    } catch (err) {
      channel.nack(msg, false, true); // 拒绝并重新入队
    }
  });
}
```

### 10.2 Kafka（kafkajs）

```javascript
const { Kafka } = require('kafkajs');

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: ['localhost:9092']
});

// 生产者
const producer = kafka.producer();
await producer.connect();
await producer.send({
  topic: 'user-events',
  messages: [
    { key: 'user-1', value: JSON.stringify({ event: 'login', userId: '1' }) }
  ],
});

// 消费者
const consumer = kafka.consumer({ groupId: 'my-group' });
await consumer.connect();
await consumer.subscribe({ topic: 'user-events', fromBeginning: true });

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const event = JSON.parse(message.value.toString());
    console.log(`收到消息 [${topic}/${partition}]:`, event);
  },
});
```

---

## 十一、WebSocket 实时通信

> **面试题：Node.js 中如何实现 WebSocket 通信？Socket.io 和 ws 有什么区别？**

### 11.1 Socket.io

```javascript
const { Server } = require('socket.io');
const http = require('http');
const express = require('express');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*' },
  pingTimeout: 60000,
  pingInterval: 25000,
});

// 中间件（认证）
io.use((socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    const user = jwt.verify(token, SECRET);
    socket.user = user;
    next();
  } catch (err) {
    next(new Error('认证失败'));
  }
});

// 连接事件
io.on('connection', (socket) => {
  console.log(`用户连接: ${socket.user.name}`);

  // 加入房间
  socket.join(`user:${socket.user.id}`);

  // 监听消息
  socket.on('chat:message', async (data) => {
    const message = await saveMessage(data);
    // 发送给房间内所有人
    io.to(data.roomId).emit('chat:message', message);
  });

  // 加入聊天室
  socket.on('room:join', (roomId) => {
    socket.join(roomId);
    socket.to(roomId).emit('room:userJoined', socket.user);
  });

  // 断开连接
  socket.on('disconnect', (reason) => {
    console.log(`用户断开: ${socket.user.name}, 原因: ${reason}`);
  });
});

// 向特定用户发送
io.to(`user:${userId}`).emit('notification', { message: '您有新消息' });

// 广播（除了发送者外的所有人）
socket.broadcast.emit('user:online', { userId: socket.user.id });

server.listen(3000);
```

### 11.2 ws 库（轻量级）

```javascript
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws, req) => {
  ws.on('message', (data) => {
    const message = JSON.parse(data);
    // 广播给所有连接的客户端
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(message));
      }
    });
  });

  ws.on('close', () => console.log('客户端断开'));
  ws.send(JSON.stringify({ type: 'welcome', message: '连接成功' }));
});
```

### 11.3 Socket.io vs ws

| 特性         | Socket.io              | ws                      |
| ------------ | ---------------------- | ----------------------- |
| 体积         | 较大                   | 极小                    |
| 功能         | 丰富（房间、广播等）   | 基础 WebSocket          |
| 自动重连     | 内置                   | 需自行实现              |
| 降级方案     | 自动（long-polling等） | 无                      |
| 适用场景     | 复杂实时应用           | 简单实时通信/高性能     |

---

## 十二、SSE（Server-Sent Events）

> **面试题：什么是 SSE？它和 WebSocket 有什么区别？**

SSE 是一种服务器向客户端推送事件的技术，基于 HTTP 协议。

```javascript
app.get('/api/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // 发送事件
  function sendEvent(data, event = 'message') {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  }

  sendEvent({ message: '连接成功' }, 'connected');

  const interval = setInterval(() => {
    sendEvent({ time: new Date().toISOString() }, 'heartbeat');
  }, 5000);

  req.on('close', () => {
    clearInterval(interval);
    console.log('SSE 连接关闭');
  });
});
```

SSE vs WebSocket：SSE 是单向的（服务器到客户端），基于 HTTP，自动重连，更简单。WebSocket 是双向的，独立协议，性能更高，适合需要双向通信的场景（如聊天）。SSE 适用于通知推送、实时数据流、进度更新等单向推送场景。

---

## 十三、微服务架构

> **面试题：Node.js 微服务架构有哪些常见模式和注意事项？**

```javascript
// 服务发现与注册
// 使用 Consul、Eureka 或 Kubernetes Service Discovery

// API 网关模式
// 使用 Kong、Nginx 或自建 Express/Fastify 网关
const gateway = express();
const { createProxyMiddleware } = require('http-proxy-middleware');

gateway.use('/api/users', createProxyMiddleware({
  target: 'http://user-service:3001',
  changeOrigin: true
}));

gateway.use('/api/orders', createProxyMiddleware({
  target: 'http://order-service:3002',
  changeOrigin: true
}));

// 熔断器模式
const CircuitBreaker = require('opossum');

const breaker = new CircuitBreaker(callExternalService, {
  timeout: 3000,         // 超时时间
  errorThresholdPercentage: 50,  // 错误率阈值
  resetTimeout: 10000    // 半开状态等待时间
});

breaker.on('open', () => console.log('熔断器打开'));
breaker.on('halfOpen', () => console.log('熔断器半开'));
breaker.on('close', () => console.log('熔断器关闭'));

breaker.fallback(() => ({ data: '降级数据' }));
const result = await breaker.fire(params);
```

---

## 十四、Docker 部署 Node.js 应用

> **面试题：如何使用 Docker 部署 Node.js 应用？Dockerfile 有哪些最佳实践？**

```dockerfile
# 多阶段构建
# Stage 1: 安装依赖
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: 构建
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: 运行
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nodeuser

COPY --from=deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY package.json ./

USER nodeuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DB_HOST=mysql
      - REDIS_HOST=redis
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: mydb
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

volumes:
  mysql_data:
```

---

## 十五、PM2 进程管理

> **面试题：PM2 有哪些功能？如何在生产环境中使用 PM2？**

```bash
# 基本命令
pm2 start app.js                    # 启动应用
pm2 start app.js -i max             # cluster 模式，利用所有 CPU
pm2 start app.js -i 4               # 指定 4 个实例
pm2 start app.js --name my-api      # 指定名称
pm2 start app.js --watch            # 文件变化时自动重启

pm2 list                            # 查看所有进程
pm2 monit                           # 监控面板
pm2 logs                            # 查看日志
pm2 logs my-api --lines 100         # 查看指定应用的最近 100 行日志

pm2 restart my-api                  # 重启
pm2 reload my-api                   # 零停机重启（graceful reload）
pm2 stop my-api                     # 停止
pm2 delete my-api                   # 删除

pm2 save                            # 保存进程列表
pm2 startup                         # 设置开机自启
```

```javascript
// ecosystem.config.js（推荐使用配置文件）
module.exports = {
  apps: [{
    name: 'my-api',
    script: 'dist/index.js',
    instances: 'max',           // 或具体数字
    exec_mode: 'cluster',       // cluster 模式
    max_memory_restart: '500M', // 内存超过 500M 自动重启
    env: {
      NODE_ENV: 'development',
      PORT: 3000
    },
    env_production: {
      NODE_ENV: 'production',
      PORT: 3000
    },
    log_date_format: 'YYYY-MM-DD HH:mm:ss',
    error_file: './logs/error.log',
    out_file: './logs/out.log',
    merge_logs: true,
    // 优雅关闭
    kill_timeout: 5000,
    listen_timeout: 10000,
    wait_ready: true,           // 等待应用发送 ready 信号
    // 自动重启策略
    exp_backoff_restart_delay: 100,
    max_restarts: 10,
    min_uptime: '10s',
  }]
};
```

```javascript
// 在应用中配置优雅关闭
const server = app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
  // 通知 PM2 应用已就绪
  process.send && process.send('ready');
});

process.on('SIGINT', () => {
  console.log('收到 SIGINT，正在优雅关闭...');
  server.close(() => {
    console.log('HTTP 服务器已关闭');
    // 关闭数据库连接等资源
    process.exit(0);
  });
});
```

---

## 常见面试题汇总

> **Q：Node.js 生产环境部署的最佳实践有哪些？**

1. 使用 PM2 或容器化（Docker + Kubernetes）管理进程；2. 设置 `NODE_ENV=production`（Express 性能提升 3 倍）；3. 使用反向代理（Nginx）处理静态文件、SSL 终止、负载均衡；4. 实现健康检查端点；5. 结构化日志（JSON 格式，使用 pino）；6. 监控和告警（APM 工具如 Datadog、New Relic）；7. 优雅关闭处理；8. 环境变量管理敏感配置；9. 使用 HTTPS；10. 定期更新依赖和安全审计。

> **Q：如何防止 Node.js 应用被 DDoS 攻击？**

1. 使用 Rate Limiting 限制请求频率；2. 使用 Nginx 或 CDN 作为前置代理吸收流量；3. 设置请求体大小限制；4. 使用 helmet 设置安全头；5. 配置超时（请求超时、Keep-Alive 超时）；6. 使用云服务商的 DDoS 防护（如 AWS Shield、Cloudflare）；7. 限制并发连接数。

> **Q：如何实现 Node.js 的零停机部署？**

1. PM2 的 `pm2 reload` 命令支持零停机重启（逐个重启 cluster 实例）；2. Kubernetes 的 Rolling Update 策略；3. 蓝绿部署：同时运行两个版本，切换流量；4. 金丝雀发布：先将少量流量导向新版本，逐步增加。关键是应用要支持优雅关闭——收到终止信号后停止接受新请求，等待现有请求完成后再退出。

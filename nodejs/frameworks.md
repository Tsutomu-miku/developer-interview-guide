# Node.js 常用框架面试指南

## 一、Express 框架

> **面试题：Express 是什么？它的核心特性有哪些？**

Express 是 Node.js 中最流行、最广泛使用的 Web 框架，由 TJ Holowaychuk 创建。它提供了简洁、灵活的 API 来构建 Web 应用和 API。Express 是一个“非侵入式”的极简框架，核心只包含路由和中间件，其他功能通过中间件扩展。

### 1.1 中间件原理

> **面试题：请解释 Express 的中间件机制。Express 的中间件模型是洋葱模型吗？**

Express 的中间件采用的是**线性模型**（非洋葱模型）。中间件按照注册顺序依次执行，通过 `next()` 函数将控制权传递给下一个中间件。

```javascript
const express = require('express');
const app = express();

// 中间件的本质是一个函数：(req, res, next) => {}
// 按照注册顺序依次执行

// 中间件1：日志
app.use((req, res, next) => {
  console.log(`[${new Date().toISOString()}] ${req.method} ${req.url}`);
  const start = Date.now();
  
  // 注意：Express 的线性模型中，这里的“后续代码”在 next() 调用后继续执行
  // 但无法保证下游中间件是否已经完成（可能是异步的）
  next();
  
  // 这行会在 next() 同步返回后立即执行
  // 但响应可能还没有完成（如果下游有异步操作）
  console.log(`耗时: ${Date.now() - start}ms`);
});

// 中间件2：设置公共头
app.use((req, res, next) => {
  res.set('X-Powered-By', 'MyApp');
  next();
});

// 路由处理
app.get('/api/users', (req, res) => {
  res.json([{ id: 1, name: 'Alice' }]);
});

// 执行流程：中间件1 → next() → 中间件2 → next() → 路由处理
```

中间件的类型：

```javascript
// 1. 应用级中间件
app.use(middleware);
app.use('/api', middleware); // 指定路径前缀

// 2. 路由级中间件
const router = express.Router();
router.use(middleware);

// 3. 错误处理中间件（4个参数）
app.use((err, req, res, next) => { /* ... */ });

// 4. 内置中间件
app.use(express.json());           // 解析 JSON body
app.use(express.urlencoded({ extended: true })); // 解析 URL 编码 body
app.use(express.static('public')); // 静态文件服务

// 5. 第三方中间件
const cors = require('cors');
app.use(cors());
```

### 1.2 路由系统

```javascript
const express = require('express');
const app = express();
const router = express.Router();

// 基本路由
app.get('/', (req, res) => res.send('Hello'));
app.post('/users', (req, res) => res.json(req.body));
app.put('/users/:id', (req, res) => res.json({ id: req.params.id }));
app.delete('/users/:id', (req, res) => res.sendStatus(204));

// 路由参数
app.get('/users/:userId/posts/:postId', (req, res) => {
  const { userId, postId } = req.params;
  res.json({ userId, postId });
});

// 路由参数验证（param 中间件）
app.param('userId', (req, res, next, id) => {
  // 预处理 userId 参数
  const user = findUserById(id);
  if (!user) return res.status(404).json({ error: 'User not found' });
  req.user = user;
  next();
});

// 查询参数
// GET /search?keyword=node&page=1
app.get('/search', (req, res) => {
  const { keyword, page } = req.query;
  res.json({ keyword, page });
});

// 路由分组（Router）
const userRouter = express.Router();
userRouter.get('/', listUsers);
userRouter.post('/', createUser);
userRouter.get('/:id', getUser);
userRouter.put('/:id', updateUser);
userRouter.delete('/:id', deleteUser);

app.use('/api/users', userRouter);

// 链式路由
app.route('/books')
  .get((req, res) => { /* 获取列表 */ })
  .post((req, res) => { /* 创建 */ });

// 正则匹配路由
app.get(/.*fly$/, (req, res) => {
  res.send('匹配以 fly 结尾的路径');
});
```

### 1.3 错误处理中间件

> **面试题：Express 中如何统一处理错误？**

```javascript
const express = require('express');
const app = express();

// 自定义错误类
class AppError extends Error {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = true;
  }
}

// 路由中抛出错误
app.get('/api/users/:id', async (req, res, next) => {
  try {
    const user = await findUser(req.params.id);
    if (!user) {
      throw new AppError('用户不存在', 404);
    }
    res.json(user);
  } catch (err) {
    next(err); // 传递给错误处理中间件
  }
});

// 封装异步错误处理
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

app.get('/api/posts', asyncHandler(async (req, res) => {
  const posts = await getPosts();
  res.json(posts);
  // 如果 getPosts 抛出异常，会自动被 catch 并传递给 next
}));

// 404 处理（放在所有路由之后）
app.use((req, res, next) => {
  next(new AppError(`找不到 ${req.originalUrl}`, 404));
});

// 统一错误处理中间件（必须有4个参数）
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;
  const message = err.isOperational ? err.message : '服务器内部错误';

  console.error('Error:', err);

  res.status(statusCode).json({
    status: 'error',
    statusCode,
    message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
});
```

### 1.4 常用中间件

```javascript
const express = require('express');
const app = express();

// body-parser（Express 4.16+ 已内置）
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// cors - 跨域资源共享
const cors = require('cors');
app.use(cors({
  origin: ['http://localhost:3000', 'https://myapp.com'],
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400 // 预检请求缓存时间（秒）
}));

// helmet - 安全 HTTP 头
const helmet = require('helmet');
app.use(helmet()); // 设置多种安全相关的 HTTP 头

// morgan - HTTP 请求日志
const morgan = require('morgan');
app.use(morgan('combined')); // Apache 格式
app.use(morgan('dev'));       // 开发格式（彩色）
// 自定义格式
app.use(morgan(':method :url :status :response-time ms'));

// compression - 响应压缩
const compression = require('compression');
app.use(compression());

// rate-limit - 请求限流
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 分钟
  max: 100,                  // 每个 IP 最多 100 次请求
  message: '请求过于频繁，请稍后再试'
});
app.use('/api/', limiter);

// cookie-parser
const cookieParser = require('cookie-parser');
app.use(cookieParser('secret'));

// express-session
const session = require('express-session');
app.use(session({
  secret: 'my-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { secure: true, maxAge: 24 * 60 * 60 * 1000 }
}));

// multer - 文件上传
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });
app.post('/upload', upload.single('file'), (req, res) => {
  res.json({ file: req.file });
});
```

---

## 二、Koa 框架

> **面试题：Koa 是什么？它与 Express 有什么区别？**

Koa 是由 Express 的原班人马打造的下一代 Web 框架，目标是成为一个更小、更有表现力、更健壮的 Web 框架。Koa 的核心特点是使用 async/await 处理异步操作，以及真正的洋葱模型中间件。

### 2.1 与 Express 的核心区别

| 对比维度     | Express                         | Koa                              |
| ------------ | ------------------------------- | -------------------------------- |
| 中间件模型   | 线性模型                        | 洋葱模型                         |
| 异步处理     | 回调函数/手动 try-catch         | 原生 async/await                 |
| 内置功能     | 较多（路由、静态文件等）        | 极简（几乎没有内置中间件）        |
| 错误处理     | 需要特殊的错误中间件            | try-catch 自动捕获               |
| Context      | req 和 res 分开                 | 统一的 ctx 对象                  |
| 路由         | 内置                            | 需要 koa-router 等第三方库       |
| 响应处理     | `res.send()`/`res.json()`       | `ctx.body = ...`                 |
| 体积         | 较大                            | 更小                             |

### 2.2 洋葱模型中间件

> **面试题：请解释 Koa 的洋葱模型，它和 Express 的中间件模型有什么不同？**

Koa 的洋葱模型意味着请求先从外向内穿过所有中间件（`await next()` 之前的代码），到达最内层后再从内向外返回（`await next()` 之后的代码）。这使得每个中间件都可以在请求处理前后执行逻辑。

```javascript
const Koa = require('koa');
const app = new Koa();

// 洋葱模型演示
app.use(async (ctx, next) => {
  console.log('1 - 进入中间件 A');
  await next();
  console.log('6 - 离开中间件 A');
});

app.use(async (ctx, next) => {
  console.log('2 - 进入中间件 B');
  await next();
  console.log('5 - 离开中间件 B');
});

app.use(async (ctx, next) => {
  console.log('3 - 进入中间件 C');
  ctx.body = 'Hello Koa';
  console.log('4 - 离开中间件 C');
});

app.listen(3000);

// 请求时输出顺序：
// 1 - 进入中间件 A
// 2 - 进入中间件 B
// 3 - 进入中间件 C
// 4 - 离开中间件 C
// 5 - 离开中间件 B
// 6 - 离开中间件 A
```

洋葱模型的实际应用 -- 精确的请求耗时统计：

```javascript
// Koa 的洋葱模型让这变得简单而准确
app.use(async (ctx, next) => {
  const start = Date.now();
  await next(); // 等待所有下游中间件执行完毕
  const ms = Date.now() - start;
  ctx.set('X-Response-Time', `${ms}ms`);
  console.log(`${ctx.method} ${ctx.url} - ${ms}ms`);
});

// 对比 Express：由于是线性模型，next() 是同步返回的
// 如果下游有异步操作，无法在 next() 之后准确计算耗时
```

### 2.3 koa-compose 原理

Koa 的中间件组合是通过 `koa-compose` 实现的，其核心代码非常精简：

```javascript
// koa-compose 简化实现
function compose(middlewares) {
  return function(ctx, next) {
    let index = -1;
    
    function dispatch(i) {
      if (i <= index) return Promise.reject(new Error('next() called multiple times'));
      index = i;
      
      let fn = middlewares[i];
      if (i === middlewares.length) fn = next;
      if (!fn) return Promise.resolve();
      
      try {
        return Promise.resolve(fn(ctx, function next() {
          return dispatch(i + 1);
        }));
      } catch (err) {
        return Promise.reject(err);
      }
    }
    
    return dispatch(0);
  };
}
```

### 2.4 Context 对象

```javascript
app.use(async (ctx) => {
  // ctx.request - Koa 的 Request 对象
  // ctx.response - Koa 的 Response 对象
  // ctx.req - Node.js 原生 IncomingMessage
  // ctx.res - Node.js 原生 ServerResponse

  // 请求信息（ctx 上的别名，委托到 ctx.request）
  ctx.method;       // HTTP 方法
  ctx.url;          // 请求 URL
  ctx.path;         // 路径
  ctx.query;        // 解析后的查询参数对象
  ctx.headers;      // 请求头
  ctx.ip;           // 客户端 IP
  ctx.host;         // 主机名
  ctx.get('Content-Type'); // 获取请求头

  // 响应（ctx 上的别名，委托到 ctx.response）
  ctx.status = 200;
  ctx.body = { data: 'hello' };   // 自动设置 Content-Type
  ctx.set('Cache-Control', 'no-cache');
  ctx.redirect('/login');
  ctx.type = 'application/json';

  // 状态管理（在中间件之间共享数据）
  ctx.state.user = { id: 1, name: 'Alice' };

  // Cookie
  ctx.cookies.set('token', 'xxx', { httpOnly: true });
  const token = ctx.cookies.get('token');

  // 抛出 HTTP 错误
  ctx.throw(403, '禁止访问');
  ctx.assert(ctx.state.user, 401, '未登录');
});
```

### 2.5 Koa 错误处理

```javascript
const Koa = require('koa');
const app = new Koa();

// 全局错误处理中间件（放在最外层）
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    ctx.status = err.status || err.statusCode || 500;
    ctx.body = {
      status: 'error',
      message: err.message,
      ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
    };
    // 触发应用级错误事件
    ctx.app.emit('error', err, ctx);
  }
});

// 应用级错误监听
app.on('error', (err, ctx) => {
  console.error('服务器错误:', err);
});

// 在路由中抛出错误会被自动捕获
app.use(async (ctx) => {
  const user = await findUser(ctx.params.id);
  if (!user) {
    ctx.throw(404, '用户不存在');
  }
  ctx.body = user;
});
```

---

## 三、NestJS 框架

> **面试题：NestJS 是什么？它有什么特点和优势？**

NestJS 是一个用于构建高效、可扩展的 Node.js 服务端应用的框架。它使用 TypeScript 编写（也支持纯 JavaScript），底层可以基于 Express 或 Fastify。NestJS 深受 Angular 的启发，采用模块化架构、依赖注入、装饰器等设计模式。

### 3.1 模块化架构

> **面试题：NestJS 的模块系统是如何组织的？Module、Controller、Service、Provider 分别是什么？**

```typescript
// user.module.ts - 模块：组织和管理相关的功能
import { Module } from '@nestjs/common';
import { UserController } from './user.controller';
import { UserService } from './user.service';

@Module({
  imports: [],            // 导入其他模块
  controllers: [UserController],  // 注册控制器
  providers: [UserService],       // 注册提供者（服务）
  exports: [UserService],         // 导出供其他模块使用
})
export class UserModule {}

// user.controller.ts - 控制器：处理 HTTP 请求路由
import { Controller, Get, Post, Body, Param, Query } from '@nestjs/common';
import { UserService } from './user.service';
import { CreateUserDto } from './dto/create-user.dto';

@Controller('users')  // 路由前缀 /users
export class UserController {
  constructor(private readonly userService: UserService) {} // 依赖注入

  @Get()
  findAll(@Query('page') page: number) {
    return this.userService.findAll(page);
  }

  @Get(':id')
  findOne(@Param('id') id: string) {
    return this.userService.findOne(id);
  }

  @Post()
  create(@Body() createUserDto: CreateUserDto) {
    return this.userService.create(createUserDto);
  }
}

// user.service.ts - 服务：处理业务逻辑
import { Injectable, NotFoundException } from '@nestjs/common';

@Injectable()
export class UserService {
  private users = [];

  findAll(page: number) {
    return this.users;
  }

  findOne(id: string) {
    const user = this.users.find(u => u.id === id);
    if (!user) throw new NotFoundException('用户不存在');
    return user;
  }

  create(data: CreateUserDto) {
    const user = { id: Date.now().toString(), ...data };
    this.users.push(user);
    return user;
  }
}

// create-user.dto.ts - DTO：数据传输对象
import { IsString, IsEmail, MinLength } from 'class-validator';

export class CreateUserDto {
  @IsString()
  @MinLength(2)
  name: string;

  @IsEmail()
  email: string;
}
```

### 3.2 依赖注入（IoC 容器）

> **面试题：NestJS 的依赖注入是如何工作的？什么是 IoC 容器？**

IoC（Inversion of Control，控制反转）是一种设计原则，将对象的创建和管理权交给框架（IoC 容器），而不是由开发者手动创建。NestJS 的 IoC 容器负责实例化、管理和注入依赖。

```typescript
// 基本依赖注入
@Injectable()
export class DatabaseService {
  async query(sql: string) { /* ... */ }
}

@Injectable()
export class UserService {
  // NestJS 自动实例化 DatabaseService 并注入
  constructor(private readonly db: DatabaseService) {}

  async findAll() {
    return this.db.query('SELECT * FROM users');
  }
}

// 自定义 Provider
@Module({
  providers: [
    // 标准注入
    UserService,

    // 值 Provider
    { provide: 'CONFIG', useValue: { apiKey: 'xxx' } },

    // 工厂 Provider
    {
      provide: 'ASYNC_CONNECTION',
      useFactory: async (configService: ConfigService) => {
        const connection = await createConnection(configService.get('DB_URL'));
        return connection;
      },
      inject: [ConfigService],
    },

    // 类 Provider（别名）
    { provide: 'IUserService', useClass: UserService },
  ],
})
export class AppModule {}

// 注入自定义 Provider
@Injectable()
export class SomeService {
  constructor(
    @Inject('CONFIG') private config: any,
    @Inject('ASYNC_CONNECTION') private connection: any,
  ) {}
}

// 作用域
@Injectable({ scope: Scope.DEFAULT })     // 单例（默认）
@Injectable({ scope: Scope.REQUEST })     // 每个请求创建新实例
@Injectable({ scope: Scope.TRANSIENT })   // 每次注入创建新实例
```

### 3.3 装饰器

```typescript
// NestJS 中常用的装饰器

// 类装饰器
@Controller('users')       // 控制器
@Injectable()              // 可注入的服务
@Module({})                // 模块

// 方法装饰器（HTTP 方法）
@Get(':id')
@Post()
@Put(':id')
@Delete(':id')
@Patch(':id')

// 参数装饰器
@Body()                    // 请求体
@Param('id')               // 路由参数
@Query('page')             // 查询参数
@Headers('authorization')  // 请求头
@Req()                     // 原始 Request 对象
@Res()                     // 原始 Response 对象

// 自定义装饰器
import { createParamDecorator, ExecutionContext } from '@nestjs/common';

export const CurrentUser = createParamDecorator(
  (data: unknown, ctx: ExecutionContext) => {
    const request = ctx.switchToHttp().getRequest();
    return request.user;
  },
);

// 使用自定义装饰器
@Get('profile')
getProfile(@CurrentUser() user: User) {
  return user;
}

// 组合装饰器
import { applyDecorators } from '@nestjs/common';

export function Auth(...roles: Role[]) {
  return applyDecorators(
    UseGuards(AuthGuard, RolesGuard),
    Roles(...roles),
    ApiBearerAuth(),
  );
}
```

### 3.4 管道、守卫、拦截器、过滤器

> **面试题：NestJS 中的 Pipes、Guards、Interceptors、ExceptionFilters 分别是什么？它们的执行顺序是什么？**

请求生命周期执行顺序：
```
请求 → Guards → Interceptors(前) → Pipes → Controller → Interceptors(后) → ExceptionFilters（如果有异常）→ 响应
```

```typescript
// 1. 管道（Pipe）- 数据验证和转换
import { PipeTransform, Injectable, BadRequestException } from '@nestjs/common';

@Injectable()
export class ParseIntPipe implements PipeTransform<string, number> {
  transform(value: string): number {
    const val = parseInt(value, 10);
    if (isNaN(val)) {
      throw new BadRequestException('参数必须是整数');
    }
    return val;
  }
}

// 使用内置管道
@Get(':id')
findOne(@Param('id', ParseIntPipe) id: number) {
  return this.service.findOne(id);
}

// ValidationPipe（搭配 class-validator）
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,       // 自动剥离未定义的属性
  forbidNonWhitelisted: true,
  transform: true,       // 自动转换类型
}));

// 2. 守卫（Guard）- 认证和授权
@Injectable()
export class AuthGuard implements CanActivate {
  constructor(private jwtService: JwtService) {}

  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const token = request.headers.authorization?.replace('Bearer ', '');
    if (!token) return false;

    try {
      const payload = this.jwtService.verify(token);
      request.user = payload;
      return true;
    } catch {
      return false;
    }
  }
}

@UseGuards(AuthGuard)
@Get('profile')
getProfile(@CurrentUser() user) {
  return user;
}

// 3. 拦截器（Interceptor）- 请求/响应转换、缓存、日志
@Injectable()
export class TransformInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    console.log('Before...');
    const now = Date.now();

    return next.handle().pipe(
      map(data => ({
        code: 200,
        message: 'success',
        data,
        timestamp: new Date().toISOString(),
      })),
      tap(() => console.log(`After... ${Date.now() - now}ms`)),
    );
  }
}

// 4. 异常过滤器（ExceptionFilter）
@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse();
    const request = ctx.getRequest();
    const status = exception.getStatus();

    response.status(status).json({
      statusCode: status,
      message: exception.message,
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}
```

### 3.5 微服务支持

```typescript
// NestJS 支持多种微服务传输层
import { Transport, MicroserviceOptions } from '@nestjs/microservices';

// TCP 微服务
const app = await NestFactory.createMicroservice<MicroserviceOptions>(AppModule, {
  transport: Transport.TCP,
  options: { host: '0.0.0.0', port: 3001 },
});

// Redis 微服务
const app = await NestFactory.createMicroservice(AppModule, {
  transport: Transport.REDIS,
  options: { host: 'localhost', port: 6379 },
});

// RabbitMQ 微服务
const app = await NestFactory.createMicroservice(AppModule, {
  transport: Transport.RMQ,
  options: {
    urls: ['amqp://localhost:5672'],
    queue: 'my_queue',
  },
});

// gRPC 微服务
const app = await NestFactory.createMicroservice(AppModule, {
  transport: Transport.GRPC,
  options: {
    package: 'hero',
    protoPath: join(__dirname, 'hero.proto'),
  },
});

// 消息模式
@Controller()
export class MathController {
  @MessagePattern({ cmd: 'sum' })
  sum(data: number[]): number {
    return data.reduce((a, b) => a + b, 0);
  }

  @EventPattern('user_created')
  handleUserCreated(data: any) {
    console.log('用户创建事件:', data);
  }
}
```

---

## 四、Fastify 框架

> **面试题：Fastify 有什么特点？为什么说它是高性能的？**

Fastify 是一个高性能、低开销的 Node.js Web 框架，主要特点：

1. **高性能**：使用 JSON Schema 编译序列化函数，JSON 序列化速度比 `JSON.stringify` 快 2-3 倍
2. **Schema 验证**：内置基于 JSON Schema 的请求/响应验证
3. **插件系统**：高度可扩展的插件架构，支持封装和作用域
4. **TypeScript 友好**：一流的 TypeScript 支持
5. **日志**：内置高性能日志（pino）

```javascript
const fastify = require('fastify')({ logger: true });

// JSON Schema 验证 + 序列化
const opts = {
  schema: {
    body: {
      type: 'object',
      required: ['name', 'email'],
      properties: {
        name: { type: 'string', minLength: 2 },
        email: { type: 'string', format: 'email' }
      }
    },
    response: {
      200: {
        type: 'object',
        properties: {
          id: { type: 'number' },
          name: { type: 'string' },
          email: { type: 'string' }
        }
      }
    }
  }
};

fastify.post('/users', opts, async (request, reply) => {
  const user = await createUser(request.body);
  return user; // 自动使用 Schema 进行序列化（更快）
});

// 插件系统
fastify.register(require('@fastify/cors'));
fastify.register(require('@fastify/helmet'));
fastify.register(require('@fastify/rate-limit'), {
  max: 100,
  timeWindow: '1 minute'
});

// 装饰器
fastify.decorate('db', databaseConnection);
fastify.decorateRequest('user', null);

// 钩子（生命周期）
fastify.addHook('onRequest', async (request, reply) => {
  // 认证检查
});

fastify.addHook('preSerialization', async (request, reply, payload) => {
  // 在响应序列化之前修改 payload
  return { data: payload, timestamp: Date.now() };
});

fastify.listen({ port: 3000 });
```

---

## 五、框架选型对比

> **面试题：在实际项目中，如何选择 Express、Koa、NestJS、Fastify？**

| 维度           | Express          | Koa              | NestJS           | Fastify          |
| -------------- | ---------------- | ---------------- | ---------------- | ---------------- |
| 学习曲线       | 低               | 低               | 高               | 中               |
| 生态系统       | 最丰富           | 较丰富           | 丰富             | 增长中           |
| 性能           | 中               | 中               | 取决于底层       | 高               |
| TypeScript     | 需配置           | 需配置           | 原生支持         | 良好支持         |
| 架构约束       | 无               | 无               | 强约束（模块化） | 弱约束           |
| 适合场景       | 中小型项目       | 中型项目         | 大型企业项目     | 高性能 API       |
| 中间件模型     | 线性             | 洋葱模型         | 装饰器+AOP       | 插件+钩子        |
| 维护状态       | 活跃             | 较活跃           | 非常活跃         | 非常活跃         |

**选型建议**：

1. **快速原型/小型项目**：Express（生态最丰富，入门最快）
2. **追求代码优雅和精准控制**：Koa（轻量、洋葱模型）
3. **大型企业级应用/团队协作**：NestJS（架构清晰、TypeScript 原生、模块化）
4. **高性能 API 服务**：Fastify（极致性能、Schema 验证）
5. **微服务架构**：NestJS（内置微服务支持、gRPC、消息队列）
6. **前端 SSR 的 BFF 层**：Express 或 Koa（简单灵活）

---

## 常见面试题汇总

> **Q：Express 中 `app.use` 和 `app.get` 有什么区别？**

`app.use` 匹配所有 HTTP 方法，路径匹配是前缀匹配（`app.use('/api', fn)` 会匹配 `/api`、`/api/users` 等）。`app.get` 只匹配 GET 方法，路径是精确匹配。`app.use` 通常用于注册中间件，`app.get` 用于定义路由。

> **Q：Koa 中 `ctx.body` 赋值后为什么不需要调用 `res.send()`？**

Koa 在所有中间件执行完毕后，会自动检查 `ctx.body` 的值并发送响应。如果 `ctx.body` 是对象/数组，自动设置 Content-Type 为 `application/json` 并序列化；如果是字符串，设置为 `text/html` 或 `text/plain`；如果是 Buffer，设置为 `application/octet-stream`；如果是 Stream，直接 pipe 到响应。

> **Q：NestJS 中的模块是单例的吗？**

是的。在 NestJS 中，默认情况下模块是单例的。当多个模块导入同一个模块时，它们共享同一个模块实例。Provider（服务）默认也是单例的（`Scope.DEFAULT`），整个应用生命周期中只创建一个实例。可以通过设置 `scope: Scope.REQUEST` 使其变为请求作用域。

> **Q：如何理解 NestJS 的 AOP（面向切面编程）？**

NestJS 的 Guards、Interceptors、Pipes、ExceptionFilters 就是 AOP 的体现。AOP 允许你在不修改业务逻辑代码的情况下，添加横切关注点（如日志、认证、缓存、错误处理等）。这些“切面”通过装饰器声明式地应用到控制器或方法上，保持了核心业务逻辑的纯净。

> **Q：Express 中间件中忘记调用 `next()` 会怎样？**

如果中间件既没有调用 `next()` 也没有发送响应（`res.send()`/`res.json()` 等），请求将会被挂起，客户端最终会收到超时错误。这是 Express 开发中常见的问题。在 Koa 中也是类似的，忘记 `await next()` 会导致下游中间件不执行。
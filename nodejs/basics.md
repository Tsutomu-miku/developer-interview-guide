# Node.js 基础面试指南

## 一、Node.js 是什么

> **面试题：请简述 Node.js 是什么，它有哪些核心特性？**

Node.js 是一个基于 Chrome V8 引擎构建的 JavaScript 运行时环境，它使得 JavaScript 可以脱离浏览器在服务端运行。Node.js 由 Ryan Dahl 于 2009 年发布，其设计目标是构建高性能、可扩展的网络应用程序。

Node.js 的四大核心特性：

1. **基于 V8 引擎**：V8 是 Google 开发的高性能 JavaScript 引擎，使用 C++ 编写，能够将 JavaScript 编译为机器码执行，性能极高。Node.js 直接内嵌了 V8 引擎，因此具备出色的执行效率。

2. **事件驱动（Event-Driven）**：Node.js 采用事件驱动的编程模型。几乎所有的 I/O 操作都会触发事件，通过 EventEmitter 类来管理事件的注册与触发。当某个操作完成时，对应的回调函数会被放入事件队列等待执行。

3. **非阻塞 I/O（Non-blocking I/O）**：Node.js 的 I/O 操作（文件读写、网络请求、数据库查询等）默认都是异步非阻塞的。当发起一个 I/O 操作时，Node.js 不会等待其完成，而是继续执行后续代码，I/O 操作完成后通过回调通知。

4. **单线程**：Node.js 的主线程（事件循环线程）是单线程的，所有的 JavaScript 代码都在这个线程上执行。但底层的 libuv 线程池会处理一些需要阻塞的操作（如文件 I/O），因此 Node.js 并非完全的单线程。

```javascript
// 非阻塞 I/O 示例
const fs = require('fs');

console.log('开始读取文件');

fs.readFile('/path/to/file', 'utf8', (err, data) => {
  if (err) throw err;
  console.log('文件读取完成');
});

console.log('继续执行其他代码'); // 这行会先于"文件读取完成"打印
```

---

## 二、Node.js 适用场景与不适用场景

> **面试题：Node.js 适用于哪些场景？哪些场景不适合使用 Node.js？**

### 适用场景

1. **I/O 密集型应用**：如 Web 服务器、API 网关、实时聊天应用。Node.js 的非阻塞 I/O 模型在处理大量并发连接时表现优异。
2. **实时应用**：如 WebSocket 聊天室、在线协作编辑、实时通知推送、在线游戏等。
3. **RESTful API / GraphQL 服务**：Node.js 轻量高效，非常适合构建 API 服务。
4. **微服务架构**：Node.js 启动速度快、内存占用低，适合部署微服务。
5. **服务端渲染（SSR）**：React、Vue 等前端框架的服务端渲染，Node.js 是天然的选择。
6. **命令行工具（CLI）**：如 webpack、eslint、create-react-app 等。
7. **流式数据处理**：如视频/音频转码、日志处理。
8. **BFF（Backend For Frontend）层**：作为前端和后端微服务之间的中间层。

### 不适用场景

1. **CPU 密集型任务**：如复杂的数学运算、图像处理、视频编码。由于单线程特性，长时间的 CPU 计算会阻塞事件循环。不过 Node.js 12+ 引入了 Worker Threads 可以缓解此问题。
2. **大型单体应用**：虽然 NestJS 等框架提供了良好的架构支持，但传统大型企业级应用通常更适合 Java/C# 等语言。
3. **需要严格类型安全的关键系统**：Node.js 的动态类型特性使其在某些对类型安全要求极高的场景中不够理想（TypeScript 可以部分缓解）。

---

## 三、Node.js 与浏览器中 JS 的区别

> **面试题：Node.js 中的 JavaScript 和浏览器中的 JavaScript 有什么区别？**

| 对比维度         | 浏览器中的 JS                 | Node.js 中的 JS                  |
| ---------------- | ----------------------------- | -------------------------------- |
| 运行环境         | 浏览器                        | 服务器/命令行                    |
| 全局对象         | `window`                      | `global`（Node.js 12+ 也支持 `globalThis`）|
| DOM/BOM          | 有 `document`、`window` 等    | 没有 DOM/BOM API                 |
| 模块系统         | ES Modules（`import/export`） | CommonJS（`require/module.exports`），也支持 ESM |
| 文件系统访问     | 受限（需要用户授权）          | 完全访问（`fs` 模块）            |
| 网络请求         | `fetch`/`XMLHttpRequest`      | `http`/`https` 模块，`fetch`（Node 18+）|
| 多线程           | Web Workers                   | Worker Threads / child_process   |
| 包管理           | 无内置                        | npm/yarn/pnpm                    |
| 进程管理         | 无                            | `process` 对象                   |
| 二进制数据       | `ArrayBuffer`/`Blob`          | `Buffer`                         |
| 标准输出         | `console.log` → 控制台        | `console.log` → stdout           |

---

## 四、全局对象

> **面试题：Node.js 中有哪些重要的全局对象？请分别介绍。**

Node.js 中的全局对象可以在所有模块中直接使用，无需 `require`。

### 4.1 global

`global` 是 Node.js 的顶层全局对象，类似于浏览器中的 `window`。在 Node.js 中，在模块顶层用 `var` 声明的变量不会成为 `global` 的属性（与浏览器不同），因为每个模块都被包裹在一个函数作用域中。

```javascript
// 浏览器中
var a = 10;
console.log(window.a); // 10

// Node.js 中
var a = 10;
console.log(global.a); // undefined
```

从 Node.js 12 开始，推荐使用 `globalThis` 作为跨平台的全局对象引用。

### 4.2 process

`process` 对象提供了当前 Node.js 进程的信息和控制能力。它是一个 EventEmitter 实例，详见下一节。

### 4.3 Buffer

`Buffer` 类用于处理二进制数据，在文件操作、网络通信中经常使用。详见后续章节。

### 4.4 __dirname 和 __filename

```javascript
console.log(__dirname);  // 当前模块所在目录的绝对路径，如 /home/user/project/src
console.log(__filename); // 当前模块文件的绝对路径，如 /home/user/project/src/index.js
```

**注意**：在 ESM 模块（`.mjs` 或 `"type": "module"`）中，`__dirname` 和 `__filename` 不可用，需要通过以下方式获取：

```javascript
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
```

### 4.5 其他全局对象/函数

- `setTimeout` / `clearTimeout`
- `setInterval` / `clearInterval`
- `setImmediate` / `clearImmediate`（Node.js 特有）
- `console`
- `URL` / `URLSearchParams`
- `TextEncoder` / `TextDecoder`
- `queueMicrotask`

---

## 五、process 对象详解

> **面试题：请详细介绍 Node.js 中的 process 对象的常用属性和方法。**

### 5.1 process.env

`process.env` 返回一个包含用户环境变量的对象。常用于读取配置：

```javascript
// 设置环境变量（通常在启动时）
// NODE_ENV=production node app.js

console.log(process.env.NODE_ENV); // 'production'
console.log(process.env.PATH);     // 系统 PATH 环境变量

// 可以动态设置（仅在当前进程有效）
process.env.MY_VAR = 'hello';
```

### 5.2 process.argv

`process.argv` 返回一个数组，包含启动 Node.js 进程时传入的命令行参数：

```javascript
// 运行命令: node app.js --port 3000 --env production

console.log(process.argv);
// [
//   '/usr/local/bin/node',    // argv[0]: Node.js 可执行文件路径
//   '/home/user/app.js',      // argv[1]: 被执行的脚本文件路径
//   '--port',                  // argv[2]: 第一个参数
//   '3000',                    // argv[3]
//   '--env',                   // argv[4]
//   'production'               // argv[5]
// ]
```

实际项目中通常使用 `yargs`、`commander` 或 `minimist` 等库来解析命令行参数。

### 5.3 process.cwd()

返回 Node.js 进程的当前工作目录（即运行 `node` 命令时所在的目录）：

```javascript
console.log(process.cwd()); // 如 /home/user/project

// 注意与 __dirname 的区别：
// __dirname 是当前文件所在的目录，不受工作目录影响
// process.cwd() 是执行命令时的工作目录，可能不同
```

### 5.4 process.nextTick(callback)

`process.nextTick` 将回调函数放入"nextTick 队列"，在当前操作完成后、事件循环继续之前执行。它的优先级高于所有微任务和宏任务：

```javascript
console.log('1');

process.nextTick(() => {
  console.log('2 - nextTick');
});

Promise.resolve().then(() => {
  console.log('3 - Promise');
});

console.log('4');

// 输出顺序: 1 → 4 → 2 - nextTick → 3 - Promise
```

### 5.5 process.exit([code])

强制终止 Node.js 进程。`code` 默认为 0（正常退出），非 0 表示异常退出：

```javascript
process.exit(0); // 正常退出
process.exit(1); // 异常退出

// 更推荐的方式是设置退出码后让进程自然退出
process.exitCode = 1;
```

### 5.6 其他常用属性和方法

```javascript
process.pid;           // 当前进程 ID
process.ppid;          // 父进程 ID
process.version;       // Node.js 版本，如 'v18.17.0'
process.versions;      // Node.js 及其依赖库的版本信息
process.platform;      // 操作系统平台，如 'linux', 'darwin', 'win32'
process.arch;          // CPU 架构，如 'x64', 'arm64'
process.memoryUsage(); // 内存使用情况
process.uptime();      // 进程运行时间（秒）
process.hrtime.bigint(); // 高精度时间（纳秒）

// 标准输入输出
process.stdin;   // 可读流
process.stdout;  // 可写流
process.stderr;  // 可写流

// 事件监听
process.on('uncaughtException', (err) => {
  console.error('未捕获的异常:', err);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('未处理的 Promise 拒绝:', reason);
});

process.on('exit', (code) => {
  console.log('进程即将退出，退出码:', code);
});

process.on('SIGINT', () => {
  console.log('收到 SIGINT 信号（Ctrl+C）');
  process.exit(0);
});
```

---

## 六、Buffer（二进制数据处理）

> **面试题：什么是 Buffer？为什么 Node.js 需要 Buffer？如何创建和操作 Buffer？**

### 6.1 什么是 Buffer

Buffer 是 Node.js 中用于处理二进制数据的类。在处理文件 I/O、网络通信、加密等操作时，数据通常以二进制形式存在，Buffer 提供了直接操作这些二进制数据的能力。

Buffer 在 V8 堆外分配内存（使用 C++ 层的内存），因此性能较高，不受 V8 垃圾回收的直接管理。

### 6.2 创建 Buffer

```javascript
// 1. Buffer.alloc(size) - 创建指定大小的 Buffer，初始化为 0
const buf1 = Buffer.alloc(10);
console.log(buf1); // <Buffer 00 00 00 00 00 00 00 00 00 00>

// 2. Buffer.allocUnsafe(size) - 创建未初始化的 Buffer（更快但可能包含旧数据）
const buf2 = Buffer.allocUnsafe(10);

// 3. Buffer.from(array) - 从数组创建
const buf3 = Buffer.from([72, 101, 108, 108, 111]);
console.log(buf3.toString()); // 'Hello'

// 4. Buffer.from(string, encoding) - 从字符串创建
const buf4 = Buffer.from('你好世界', 'utf8');
console.log(buf4); // <Buffer e4 bd a0 e5 a5 bd e4 b8 96 e7 95 8c>
console.log(buf4.length); // 12（UTF-8 中文占 3 字节）

// 5. Buffer.from(buffer) - 从另一个 Buffer 复制
const buf5 = Buffer.from(buf4);

// 注意：new Buffer() 已弃用，不要使用
```

### 6.3 读写操作

```javascript
const buf = Buffer.alloc(4);

// 写入
buf.writeUInt8(0x48, 0);  // 写入单字节
buf.writeUInt8(0x69, 1);
buf.write('Hi', 0, 'utf8'); // 写入字符串

// 读取
console.log(buf.readUInt8(0)); // 72
console.log(buf[0]);           // 72
console.log(buf.toString('utf8', 0, 2)); // 'Hi'

// 切片（共享内存）
const slice = buf.slice(0, 2);
slice[0] = 0x41; // 修改 slice 也会影响原 buf

// 复制（不共享内存）
const copy = Buffer.alloc(2);
buf.copy(copy, 0, 0, 2);

// 拼接
const combined = Buffer.concat([Buffer.from('Hello'), Buffer.from(' World')]);
console.log(combined.toString()); // 'Hello World'

// 比较
Buffer.from('abc').compare(Buffer.from('abd')); // -1
Buffer.from('abc').equals(Buffer.from('abc'));   // true
```

### 6.4 编码转换

```javascript
const str = '面试指南';
const buf = Buffer.from(str, 'utf8');

// 支持的编码: utf8, ascii, base64, base64url, hex, latin1, binary, ucs2/utf16le
console.log(buf.toString('base64'));  // '6Z2i6K+V5oyH5Y2X'
console.log(buf.toString('hex'));     // 'e99da2e8af95e68c87e58d97'

// Base64 解码
const decoded = Buffer.from('SGVsbG8=', 'base64');
console.log(decoded.toString()); // 'Hello'
```

---

## 七、模块系统

> **面试题：请详细介绍 Node.js 的 CommonJS 模块系统，包括 require 的加载机制和缓存原理。**

### 7.1 CommonJS 加载原理

每个 Node.js 文件都被视为一个独立的模块。在执行时，Node.js 会将模块代码包裹在一个函数中：

```javascript
(function(exports, require, module, __filename, __dirname) {
  // 你的模块代码
});
```

这就是为什么每个模块都有 `exports`、`require`、`module`、`__filename`、`__dirname` 这些变量。

### 7.2 require 加载机制

`require()` 的解析步骤如下：

1. **核心模块**（如 `fs`、`path`、`http`）：直接从 Node.js 内部加载，优先级最高。
2. **路径模块**（以 `/`、`./`、`../` 开头）：按照路径查找文件。
3. **第三方模块**（不带路径）：从 `node_modules` 目录逐级向上查找。

文件查找顺序（以 `require('./foo')` 为例）：
1. 精确文件名匹配：`foo`
2. 补全扩展名：`foo.js` → `foo.json` → `foo.node`
3. 目录查找：`foo/package.json` 中的 `main` 字段 → `foo/index.js` → `foo/index.json` → `foo/index.node`

```javascript
// require 的缓存机制
// 第一次 require 后，模块会被缓存在 require.cache 中
// 后续的 require 直接返回缓存的 module.exports

const mod1 = require('./myModule');
const mod2 = require('./myModule');
console.log(mod1 === mod2); // true（同一个引用）

// 查看缓存
console.log(require.cache);

// 清除缓存（谨慎使用）
delete require.cache[require.resolve('./myModule')];
```

### 7.3 module.exports vs exports

```javascript
// module.exports 是模块真正的导出对象
// exports 是 module.exports 的引用（快捷方式）

// 正确用法
exports.name = 'Alice';
exports.greet = function() { return 'Hello'; };
// 等价于
module.exports.name = 'Alice';
module.exports.greet = function() { return 'Hello'; };

// 直接赋值必须用 module.exports
module.exports = class User {
  constructor(name) { this.name = name; }
};

// 错误用法！直接给 exports 赋值会切断引用
exports = { name: 'Alice' }; // 无效，不会改变 module.exports
```

### 7.4 循环依赖处理

> **面试题：Node.js 如何处理循环依赖（循环引用）？**

当模块 A 和模块 B 相互 `require` 时，Node.js 不会死循环。它的处理策略是：返回未完成的导出对象（部分加载）。

```javascript
// a.js
console.log('a.js 开始');
exports.done = false;
const b = require('./b');
console.log('在 a.js 中, b.done =', b.done);
exports.done = true;
console.log('a.js 结束');

// b.js
console.log('b.js 开始');
exports.done = false;
const a = require('./a');
console.log('在 b.js 中, a.done =', a.done); // false（a 尚未执行完）
exports.done = true;
console.log('b.js 结束');

// main.js
const a = require('./a');
const b = require('./b');

// 输出：
// a.js 开始
// b.js 开始
// 在 b.js 中, a.done = false  ← 注意这里是 false
// b.js 结束
// 在 a.js 中, b.done = true
// a.js 结束
```

结论：在循环依赖中，某些导出可能是不完整的。最佳实践是尽量避免循环依赖，或者将共享代码抽取到独立模块中。

---

## 八、ESM 在 Node.js 中的使用

> **面试题：Node.js 中如何使用 ES Modules？CommonJS 和 ESM 有什么区别？**

### 8.1 启用 ESM 的方式

1. 使用 `.mjs` 扩展名
2. 在 `package.json` 中设置 `"type": "module"`
3. 在命令行使用 `--input-type=module` 标志

### 8.2 CommonJS vs ESM 核心区别

| 特性           | CommonJS                        | ESM                               |
| -------------- | ------------------------------- | --------------------------------- |
| 语法           | `require()` / `module.exports`  | `import` / `export`               |
| 加载时机       | 运行时加载（动态）              | 编译时加载（静态）                |
| 加载方式       | 同步加载                        | 异步加载                          |
| 导出值         | 值的拷贝                        | 值的引用（实时绑定）              |
| `this` 指向    | `module.exports`                | `undefined`                       |
| 顶层 `await`   | 不支持                          | 支持                              |
| `__dirname`    | 可用                            | 不可用，需通过 `import.meta.url` 获取 |
| Tree Shaking   | 不支持                          | 支持                              |

```javascript
// ESM 导出
export const name = 'Alice';
export default function greet() { return 'Hello'; }

// ESM 导入
import greet, { name } from './module.mjs';

// 动态导入（CommonJS 和 ESM 都支持）
const module = await import('./module.mjs');

// ESM 中使用 CommonJS 模块
import pkg from './cjs-module.cjs'; // 默认导入
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const cjsModule = require('./cjs-module.cjs');
```

---

## 九、npm / yarn / pnpm 包管理

> **面试题：请比较 npm、yarn 和 pnpm 的区别和各自优势。**

### 9.1 npm

npm（Node Package Manager）是 Node.js 的默认包管理器，随 Node.js 一起安装。

- npm v3+ 采用扁平化的 `node_modules` 结构（尽可能减少嵌套）
- npm v5+ 引入 `package-lock.json` 确保依赖版本一致
- npm v7+ 支持 workspaces（monorepo 管理）

### 9.2 yarn

Facebook 于 2016 年发布，解决了早期 npm 的性能和一致性问题。

- 并行安装依赖，速度更快
- 使用 `yarn.lock` 锁定版本
- Yarn 2（Berry）引入了 Plug'n'Play（PnP），不再使用 `node_modules`
- 支持 workspaces

### 9.3 pnpm

pnpm（performant npm）以高效的磁盘空间利用和严格的依赖管理著称。

- **内容寻址存储**：所有包存储在全局的 `.pnpm-store` 中，项目中通过硬链接引用，极大节省磁盘空间
- **非扁平的 node_modules**：使用符号链接创建嵌套结构，避免了幽灵依赖问题
- **严格模式**：项目只能访问 `package.json` 中声明的依赖，不能访问未声明的间接依赖
- 速度通常最快
- 原生支持 monorepo

```bash
# 常用命令对比
# 安装所有依赖
npm install        / yarn install    / pnpm install
# 添加依赖
npm install lodash / yarn add lodash / pnpm add lodash
# 全局安装
npm install -g xxx / yarn global add xxx / pnpm add -g xxx
# 运行脚本
npm run build      / yarn build      / pnpm build
# 删除依赖
npm uninstall xxx  / yarn remove xxx / pnpm remove xxx
```

---

## 十、package.json 重要字段详解

> **面试题：package.json 中有哪些重要字段？请分别介绍它们的作用。**

```jsonc
{
  // 基本信息
  "name": "my-project",          // 包名（必须唯一，小写，可含 - 和 _）
  "version": "1.0.0",            // 语义化版本号 (major.minor.patch)
  "description": "项目描述",
  "keywords": ["node", "api"],   // 搜索关键词
  "license": "MIT",              // 开源协议
  "author": "Your Name <email@example.com>",
  "repository": { "type": "git", "url": "https://github.com/xxx/yyy" },

  // 入口文件
  "main": "dist/index.js",       // CommonJS 入口（require 时使用）
  "module": "dist/index.mjs",    // ESM 入口（构建工具优先使用）
  "types": "dist/index.d.ts",    // TypeScript 类型声明入口
  "exports": {                   // 条件导出（Node.js 12.11+，优先级高于 main）
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.cjs",
      "types": "./dist/index.d.ts"
    },
    "./utils": "./dist/utils.js"
  },
  "type": "module",              // 指定模块系统: "module"(ESM) 或 "commonjs"(默认)
  "bin": {                       // 可执行命令
    "my-cli": "./bin/cli.js"
  },
  "files": ["dist", "README.md"], // 发布到 npm 时包含的文件

  // 脚本
  "scripts": {
    "dev": "nodemon src/index.js",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "jest",
    "lint": "eslint src/",
    "prepare": "husky install",    // 生命周期钩子
    "prepublishOnly": "npm run build"
  },

  // 依赖
  "dependencies": {},            // 生产依赖
  "devDependencies": {},         // 开发依赖
  "peerDependencies": {},        // 同等依赖（插件系统常用）
  "optionalDependencies": {},    // 可选依赖（安装失败不会报错）
  "bundledDependencies": [],     // 打包时一起打包的依赖

  // 引擎约束
  "engines": {
    "node": ">=16.0.0",
    "npm": ">=8.0.0"
  },
  "engineStrict": true,

  // 私有包（防止误发布到 npm）
  "private": true,

  // Workspaces（monorepo）
  "workspaces": [
    "packages/*"
  ],

  // 浏览器兼容
  "browserslist": ["> 1%", "last 2 versions"],

  // 配置
  "config": {
    "port": "3000"               // 可通过 process.env.npm_package_config_port 访问
  }
}
```

---

## 十一、npm scripts 生命周期

> **面试题：npm scripts 的生命周期钩子有哪些？执行顺序是怎样的？**

npm 为某些脚本提供了 `pre` 和 `post` 钩子：

```jsonc
{
  "scripts": {
    "prebuild": "echo 'build 前执行'",
    "build": "tsc",
    "postbuild": "echo 'build 后执行'"
  }
}
```

运行 `npm run build` 时，执行顺序为：`prebuild` → `build` → `postbuild`。

### 特殊的生命周期脚本

| 脚本             | 触发时机                                              |
| ---------------- | ----------------------------------------------------- |
| `prepare`        | 安装依赖后（`npm install`）和打包发布前               |
| `prepublishOnly` | 仅在 `npm publish` 前执行                             |
| `prepack`        | 打包前（`npm pack` 或 `npm publish`）                 |
| `postpack`       | 打包后                                                |
| `preinstall`     | `npm install` 之前                                    |
| `install`        | `npm install` 期间                                    |
| `postinstall`    | `npm install` 之后                                    |
| `preuninstall`   | `npm uninstall` 之前                                  |
| `postuninstall`  | `npm uninstall` 之后                                  |

`npm install` 的完整生命周期：`preinstall` → `install` → `postinstall` → `prepublish`（已弃用）→ `prepare`

---

## 十二、npx 的作用

> **面试题：npx 是什么？它有什么用途？**

`npx` 是 npm v5.2+ 自带的命令行工具，主要用途包括：

1. **执行本地安装的包**：无需在 scripts 中定义，直接执行 `node_modules/.bin/` 下的命令。

```bash
# 不使用 npx
./node_modules/.bin/eslint src/
# 使用 npx
npx eslint src/
```

2. **临时执行远程包**：无需全局安装，一次性下载执行后自动清理。

```bash
npx create-react-app my-app
npx cowsay "Hello"
npx @angular/cli new my-app
```

3. **执行不同版本的包**：

```bash
npx node@14 --version    # 使用 Node.js 14 运行
npx -p typescript tsc --init  # 使用 TypeScript 编译器
```

4. **执行 GitHub gist 或仓库中的代码**：

```bash
npx github:user/repo
npx https://gist.github.com/xxx
```

---

## 常见面试题汇总

> **Q：Node.js 中的 `require` 是同步还是异步的？为什么？**

`require` 是同步加载的。因为 CommonJS 设计上需要在模块加载完成后才能获取导出的值，同步加载保证了模块依赖的确定性。在服务端环境中，文件系统读取速度快，同步加载不会造成明显的性能问题。而 ESM 的 `import` 是异步的，更适合网络环境。

> **Q：`dependencies` 和 `devDependencies` 的区别是什么？**

- `dependencies`：项目运行时需要的依赖，如 `express`、`lodash`。执行 `npm install --production` 时只会安装这些依赖。
- `devDependencies`：仅开发阶段需要的依赖，如 `jest`、`eslint`、`webpack`。生产环境部署时不需要。

使用 `npm install xxx --save-dev`（或 `-D`）安装到 devDependencies。

> **Q：`package-lock.json` 的作用是什么？**

`package-lock.json` 锁定了项目依赖树中每个包的精确版本号和下载地址，确保在不同环境、不同时间安装依赖时得到完全一致的 `node_modules` 结构。它应该被提交到版本控制系统中。

> **Q：如何理解语义化版本号（SemVer）？`^` 和 `~` 有什么区别？**

语义化版本号格式：`major.minor.patch`（主版本号.次版本号.修订号）。

- `^1.2.3`：兼容更新，允许次版本号和修订号升级（`>=1.2.3 <2.0.0`）
- `~1.2.3`：修订更新，只允许修订号升级（`>=1.2.3 <1.3.0`）
- `1.2.3`：精确版本
- `*`：任意版本
- `>=1.0.0`：大于等于指定版本

> **Q：Node.js 是单线程的，为什么还能处理高并发？**

虽然 JavaScript 的执行是单线程的，但 Node.js 的高并发能力来源于其**事件驱动**和**非阻塞 I/O** 的设计。当遇到 I/O 操作时，Node.js 会将其交给底层的 libuv 处理（libuv 内部维护了一个线程池），主线程继续处理其他请求。当 I/O 操作完成后，回调函数会被放入事件队列等待执行。这种模型使得单线程也能同时处理数千甚至数万个并发连接，因为大部分时间线程都在处理"快速"的 JavaScript 代码，而"慢速"的 I/O 操作被异步化了。
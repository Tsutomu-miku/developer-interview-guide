# Node.js 流与文件系统面试指南

## 一、流的概念与类型

> **面试题：什么是 Node.js 中的流（Stream）？有哪几种类型？为什么要使用流？**

流（Stream）是 Node.js 中处理数据的一种抽象接口。流可以将数据分成小块（chunk）进行处理，而不是一次性将整个数据加载到内存中。这在处理大文件、网络通信等场景中至关重要。

**为什么使用流**：
- **内存效率**：不需要一次性将大量数据加载到内存，逐块处理
- **时间效率**：不需要等到所有数据可用才开始处理，可以边读边处理
- **组合性**：通过 `pipe` 将多个流连接在一起，形成数据处理管道

### 1.1 四种流类型

```javascript
const { Readable, Writable, Duplex, Transform } = require('stream');
```

| 类型        | 说明                        | 典型示例                                  |
| ----------- | --------------------------- | ----------------------------------------- |
| Readable    | 可读流，数据的来源          | `fs.createReadStream`、`http.IncomingMessage`、`process.stdin` |
| Writable    | 可写流，数据的目的地        | `fs.createWriteStream`、`http.ServerResponse`、`process.stdout` |
| Duplex      | 双工流，既可读又可写（独立）| `net.Socket`、`zlib` 流                   |
| Transform   | 转换流，在读写过程中可以修改数据 | `zlib.createGzip()`、`crypto.createCipher()` |

```javascript
const fs = require('fs');

// Readable 示例
const readable = fs.createReadStream('input.txt');

// Writable 示例
const writable = fs.createWriteStream('output.txt');

// pipe 连接
readable.pipe(writable);

// Transform 示例：将数据转换为大写
const { Transform } = require('stream');
const upperCase = new Transform({
  transform(chunk, encoding, callback) {
    this.push(chunk.toString().toUpperCase());
    callback();
  }
});

fs.createReadStream('input.txt')
  .pipe(upperCase)
  .pipe(fs.createWriteStream('output.txt'));
```

---

## 二、流的两种模式

> **面试题：Node.js 中可读流有哪两种工作模式？如何在它们之间切换？**

可读流有两种工作模式：**flowing（流动模式）** 和 **paused（暂停模式）**。

### 2.1 流动模式（Flowing Mode）

数据自动从底层系统读取，并通过 `data` 事件尽可能快地提供给应用程序。

切换到流动模式的方式：
- 添加 `data` 事件监听器
- 调用 `stream.resume()` 方法
- 调用 `stream.pipe()` 方法

```javascript
const fs = require('fs');
const readable = fs.createReadStream('file.txt');

// 方式1：监听 data 事件
readable.on('data', (chunk) => {
  console.log(`接收到 ${chunk.length} 字节数据`);
});

readable.on('end', () => {
  console.log('数据读取完毕');
});

// 方式2：pipe
readable.pipe(process.stdout);
```

### 2.2 暂停模式（Paused Mode）

数据不会自动读取，需要显式调用 `stream.read()` 方法来读取数据块。

切换到暂停模式的方式：
- 调用 `stream.pause()` 方法
- 如果没有管道目标，移除所有 `data` 事件监听器
- 如果有管道目标，调用 `stream.unpipe()` 移除所有管道

```javascript
const fs = require('fs');
const readable = fs.createReadStream('file.txt');

// 暂停模式 - 需要手动调用 read()
readable.on('readable', () => {
  let chunk;
  while (null !== (chunk = readable.read())) {
    console.log(`接收到 ${chunk.length} 字节数据`);
  }
});

readable.on('end', () => {
  console.log('数据读取完毕');
});
```

### 2.3 模式切换的注意事项

```javascript
const readable = fs.createReadStream('file.txt');

// 流动模式
readable.on('data', (chunk) => {
  console.log(chunk);
  readable.pause(); // 暂停流
  
  setTimeout(() => {
    readable.resume(); // 3秒后恢复流动
  }, 3000);
});
```

初始状态下，可读流处于暂停模式。不要同时使用 `data` 事件和 `readable` 事件，这会导致不可预测的行为。

---

## 三、pipe 机制

> **面试题：请解释 Node.js 流的 pipe 机制是如何工作的。**

`pipe()` 方法将可读流的输出连接到可写流的输入，自动管理数据流动和背压：

```javascript
readable.pipe(writable);
```

### 3.1 pipe 的内部工作原理

`pipe` 的简化实现：

```javascript
// pipe 的简化原理
Readable.prototype.pipe = function(dest) {
  const src = this;
  
  // 监听可读流的 data 事件
  src.on('data', (chunk) => {
    // 将数据写入可写流
    const canWrite = dest.write(chunk);
    
    // 如果可写流的缓冲区满了，暂停可读流（背压处理）
    if (!canWrite) {
      src.pause();
    }
  });
  
  // 当可写流的缓冲区排空时，恢复可读流
  dest.on('drain', () => {
    src.resume();
  });
  
  // 当可读流结束时，结束可写流
  src.on('end', () => {
    dest.end();
  });
  
  // 错误处理
  src.on('error', (err) => {
    dest.destroy(err);
  });
  
  return dest; // 支持链式调用
};
```

### 3.2 链式 pipe

```javascript
const fs = require('fs');
const zlib = require('zlib');

// 读取文件 → 压缩 → 写入文件
fs.createReadStream('input.txt')
  .pipe(zlib.createGzip())
  .pipe(fs.createWriteStream('input.txt.gz'));

// 解压
fs.createReadStream('input.txt.gz')
  .pipe(zlib.createGunzip())
  .pipe(fs.createWriteStream('output.txt'));
```

### 3.3 pipeline（推荐）

Node.js 10+ 引入了 `stream.pipeline()`，相比直接使用 `pipe`，它能正确处理错误和清理资源：

```javascript
const { pipeline } = require('stream');
const { promisify } = require('util');
const pipelineAsync = promisify(pipeline);

// 回调方式
pipeline(
  fs.createReadStream('input.txt'),
  zlib.createGzip(),
  fs.createWriteStream('input.txt.gz'),
  (err) => {
    if (err) {
      console.error('Pipeline 失败:', err);
    } else {
      console.log('Pipeline 完成');
    }
  }
);

// Promise 方式（Node.js 15+ 也可以直接使用 stream/promises）
const { pipeline } = require('stream/promises');

async function compress() {
  await pipeline(
    fs.createReadStream('input.txt'),
    zlib.createGzip(),
    fs.createWriteStream('input.txt.gz')
  );
  console.log('压缩完成');
}
```

`pipe()` 在出错时不会自动销毁流，可能导致内存泄漏。而 `pipeline()` 会在出错时自动清理所有流。

---

## 四、背压（Backpressure）问题与处理

> **面试题：什么是流的背压（Backpressure）？如何处理？**

### 4.1 什么是背压

背压是指当数据的生产速度大于消费速度时，未处理的数据在缓冲区中积累的现象。如果不处理背压，可能导致内存溢出或数据丢失。

典型场景：从一个快速的 SSD 读取数据，写入一个慢速的网络连接。

### 4.2 背压的产生

```javascript
const fs = require('fs');

const readable = fs.createReadStream('huge-file.dat');   // 读取很快
const writable = fs.createWriteStream('output.dat');      // 写入较慢

// 错误做法 - 不处理背压
readable.on('data', (chunk) => {
  writable.write(chunk); // 写入速度跟不上，数据堆积在内存中
});

// 正确做法 - 手动处理背压
readable.on('data', (chunk) => {
  const canWrite = writable.write(chunk);
  if (!canWrite) {
    // 可写流缓冲区满了，暂停可读流
    readable.pause();
  }
});

writable.on('drain', () => {
  // 可写流缓冲区排空了，恢复可读流
  readable.resume();
});
```

### 4.3 最佳处理方式

```javascript
// 方式1：使用 pipe（自动处理背压）
readable.pipe(writable);

// 方式2：使用 pipeline（推荐）
const { pipeline } = require('stream/promises');
await pipeline(readable, writable);

// 方式3：使用 async iterator（Node.js 10+）
async function processStream(readable, writable) {
  for await (const chunk of readable) {
    const canWrite = writable.write(chunk);
    if (!canWrite) {
      await new Promise((resolve) => writable.once('drain', resolve));
    }
  }
  writable.end();
}
```

### 4.4 highWaterMark

`highWaterMark` 是流的内部缓冲区大小阈值，决定了何时触发背压：

```javascript
// 默认值
// Readable: 16KB（objectMode 下为 16 个对象）
// Writable: 16KB

// 自定义 highWaterMark
const readable = fs.createReadStream('file.txt', {
  highWaterMark: 64 * 1024 // 64KB
});

const writable = fs.createWriteStream('output.txt', {
  highWaterMark: 32 * 1024 // 32KB
});
```

当可写流的内部缓冲区超过 `highWaterMark` 时，`write()` 返回 `false`，表示应该暂停写入。当缓冲区排空到 `highWaterMark` 以下时，触发 `drain` 事件。

---

## 五、自定义可读流/可写流

> **面试题：如何实现自定义的可读流和可写流？**

### 5.1 自定义可读流

```javascript
const { Readable } = require('stream');

// 方式1：继承 Readable 类
class Counter extends Readable {
  constructor(max, options) {
    super(options);
    this.max = max;
    this.current = 0;
  }

  _read(size) {
    if (this.current <= this.max) {
      this.push(String(this.current++) + '\n');
    } else {
      this.push(null); // 表示流结束
    }
  }
}

const counter = new Counter(10);
counter.pipe(process.stdout);

// 方式2：使用构造函数选项
const readable = new Readable({
  read(size) {
    this.push('hello\n');
    this.push(null);
  }
});

// 方式3：从迭代器/生成器创建（Node.js 12+）
async function* generateData() {
  yield 'Hello ';
  yield 'World';
}

const readableFromGen = Readable.from(generateData());
readableFromGen.pipe(process.stdout);

// 方式4：对象模式
const objectReadable = new Readable({
  objectMode: true,
  read() {
    this.push({ name: 'Alice', age: 30 });
    this.push({ name: 'Bob', age: 25 });
    this.push(null);
  }
});
```

### 5.2 自定义可写流

```javascript
const { Writable } = require('stream');

// 自定义可写流 - 数据收集器
class Collector extends Writable {
  constructor(options) {
    super(options);
    this.data = [];
  }

  _write(chunk, encoding, callback) {
    this.data.push(chunk.toString());
    console.log(`写入: ${chunk}`);
    callback(); // 必须调用 callback 表示写入完成
  }

  _final(callback) {
    console.log('所有数据:', this.data.join(''));
    callback();
  }
}

const collector = new Collector();
collector.write('Hello ');
collector.write('World');
collector.end(); // 触发 _final
```

### 5.3 自定义 Transform 流

```javascript
const { Transform } = require('stream');

// 将 CSV 行转换为 JSON 对象
class CsvToJson extends Transform {
  constructor(headers, options) {
    super({ ...options, objectMode: true });
    this.headers = headers;
    this.isFirstLine = true;
  }

  _transform(chunk, encoding, callback) {
    const line = chunk.toString().trim();
    if (this.isFirstLine) {
      this.isFirstLine = false;
      if (!this.headers) {
        this.headers = line.split(',');
        return callback();
      }
    }

    const values = line.split(',');
    const obj = {};
    this.headers.forEach((header, i) => {
      obj[header.trim()] = values[i]?.trim();
    });
    this.push(obj);
    callback();
  }
}
```

### 5.4 自定义 Duplex 流

```javascript
const { Duplex } = require('stream');

class MyDuplex extends Duplex {
  constructor(options) {
    super(options);
    this.data = [];
  }

  _read(size) {
    if (this.data.length > 0) {
      this.push(this.data.shift());
    } else {
      // 稍后再尝试
      setTimeout(() => this._read(size), 100);
    }
  }

  _write(chunk, encoding, callback) {
    this.data.push(chunk);
    callback();
  }
}
```

---

## 六、文件系统 fs 模块

> **面试题：Node.js 的 fs 模块有哪几种 API 风格？它们的区别是什么？**

### 6.1 三种 API 风格

```javascript
const fs = require('fs');
const fsPromises = require('fs').promises; // 或 require('fs/promises')

// 1. 同步 API（阻塞事件循环）
try {
  const data = fs.readFileSync('file.txt', 'utf8');
  console.log(data);
} catch (err) {
  console.error(err);
}

// 2. 回调 API（异步，不阻塞）
fs.readFile('file.txt', 'utf8', (err, data) => {
  if (err) { console.error(err); return; }
  console.log(data);
});

// 3. Promise API（异步，推荐）
async function readFile() {
  try {
    const data = await fsPromises.readFile('file.txt', 'utf8');
    console.log(data);
  } catch (err) {
    console.error(err);
  }
}
```

### 6.2 常用文件操作

```javascript
const fs = require('fs/promises');

// 读取文件
const content = await fs.readFile('file.txt', 'utf8');

// 写入文件（覆盖）
await fs.writeFile('file.txt', '新内容', 'utf8');

// 追加内容
await fs.appendFile('file.txt', '\n追加内容', 'utf8');

// 删除文件
await fs.unlink('file.txt');

// 重命名/移动文件
await fs.rename('old.txt', 'new.txt');

// 复制文件
await fs.copyFile('source.txt', 'dest.txt');

// 获取文件信息
const stats = await fs.stat('file.txt');
console.log(stats.isFile());      // 是否是文件
console.log(stats.isDirectory()); // 是否是目录
console.log(stats.size);          // 文件大小（字节）
console.log(stats.mtime);         // 最后修改时间

// 检查文件是否存在
try {
  await fs.access('file.txt', fs.constants.F_OK);
  console.log('文件存在');
} catch {
  console.log('文件不存在');
}

// 创建目录（递归）
await fs.mkdir('a/b/c', { recursive: true });

// 读取目录
const files = await fs.readdir('src');
const filesWithTypes = await fs.readdir('src', { withFileTypes: true });
filesWithTypes.forEach(dirent => {
  console.log(dirent.name, dirent.isDirectory() ? '目录' : '文件');
});

// 删除目录（递归）
await fs.rm('dist', { recursive: true, force: true });

// 创建符号链接
await fs.symlink('target.txt', 'link.txt');

// 修改文件权限
await fs.chmod('file.txt', 0o755);

// 截断文件
await fs.truncate('file.txt', 100); // 保留前 100 字节
```

---

## 七、大文件读写方案

> **面试题：如何在 Node.js 中高效地处理大文件（几 GB 甚至更大）？**

### 7.1 使用流逐块处理

```javascript
const fs = require('fs');

// 读取大文件
const readStream = fs.createReadStream('huge-file.log', {
  encoding: 'utf8',
  highWaterMark: 64 * 1024 // 每次读取 64KB
});

let lineCount = 0;

readStream.on('data', (chunk) => {
  lineCount += chunk.split('\n').length - 1;
});

readStream.on('end', () => {
  console.log(`总行数: ${lineCount}`);
});

readStream.on('error', (err) => {
  console.error('读取错误:', err);
});
```

### 7.2 逐行读取（readline）

```javascript
const fs = require('fs');
const readline = require('readline');

async function processLineByLine(filePath) {
  const fileStream = fs.createReadStream(filePath);
  const rl = readline.createInterface({
    input: fileStream,
    crlfDelay: Infinity // 识别 \r\n 为一行
  });

  let lineNum = 0;
  for await (const line of rl) {
    lineNum++;
    // 逐行处理
    if (line.includes('ERROR')) {
      console.log(`第 ${lineNum} 行: ${line}`);
    }
  }

  console.log(`处理完成，共 ${lineNum} 行`);
}

processLineByLine('server.log');
```

### 7.3 大文件复制

```javascript
const fs = require('fs');
const { pipeline } = require('stream/promises');

// 方式1：使用 pipeline（推荐）
async function copyFile(src, dest) {
  await pipeline(
    fs.createReadStream(src),
    fs.createWriteStream(dest)
  );
}

// 方式2：使用 fs.copyFile（内部优化，可能使用操作系统的零拷贝）
await fs.promises.copyFile('source.dat', 'dest.dat');

// 方式3：带进度报告的复制
function copyWithProgress(src, dest) {
  return new Promise((resolve, reject) => {
    const stat = fs.statSync(src);
    let copied = 0;

    const readStream = fs.createReadStream(src);
    const writeStream = fs.createWriteStream(dest);

    readStream.on('data', (chunk) => {
      copied += chunk.length;
      const progress = ((copied / stat.size) * 100).toFixed(1);
      process.stdout.write(`\r复制进度: ${progress}%`);
    });

    readStream.pipe(writeStream);
    writeStream.on('finish', () => {
      console.log('\n复制完成');
      resolve();
    });
    writeStream.on('error', reject);
    readStream.on('error', reject);
  });
}
```

### 7.4 分块上传大文件

```javascript
const fs = require('fs');
const path = require('path');

async function splitFile(filePath, chunkSize = 10 * 1024 * 1024) { // 10MB
  const stat = await fs.promises.stat(filePath);
  const totalChunks = Math.ceil(stat.size / chunkSize);
  const chunks = [];

  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = Math.min(start + chunkSize, stat.size);
    const chunkPath = `${filePath}.part${i}`;

    await new Promise((resolve, reject) => {
      const readStream = fs.createReadStream(filePath, { start, end: end - 1 });
      const writeStream = fs.createWriteStream(chunkPath);
      readStream.pipe(writeStream);
      writeStream.on('finish', resolve);
      writeStream.on('error', reject);
    });

    chunks.push(chunkPath);
  }

  return chunks;
}
```

---

## 八、文件监听

> **面试题：Node.js 中如何监听文件变化？`fs.watch` 和 `fs.watchFile` 有什么区别？**

### 8.1 fs.watch

基于操作系统的文件系统事件通知（如 Linux 的 inotify、macOS 的 FSEvents），性能好但可能不够可靠：

```javascript
const fs = require('fs');

const watcher = fs.watch('./src', { recursive: true }, (eventType, filename) => {
  console.log(`事件类型: ${eventType}, 文件: ${filename}`);
  // eventType: 'rename'（创建/删除/重命名）或 'change'（内容修改）
});

watcher.on('error', (err) => {
  console.error('监听错误:', err);
});

// 停止监听
// watcher.close();
```

### 8.2 fs.watchFile

基于轮询（polling）的方式，通过定期检查文件 stat 来检测变化。可靠性更高但性能较差：

```javascript
fs.watchFile('file.txt', { interval: 1000 }, (curr, prev) => {
  if (curr.mtime !== prev.mtime) {
    console.log('文件已被修改');
  }
});

// 停止监听
fs.unwatchFile('file.txt');
```

### 8.3 chokidar（推荐）

在生产环境中，推荐使用 `chokidar` 库，它解决了 `fs.watch` 的跨平台兼容性问题：

```javascript
const chokidar = require('chokidar');

const watcher = chokidar.watch('./src', {
  ignored: /(^|[\/\\])\../, // 忽略点文件
  persistent: true,
  ignoreInitial: true,       // 忽略初始扫描触发的 add 事件
  awaitWriteFinish: {        // 等待写入完成（避免重复触发）
    stabilityThreshold: 200,
    pollInterval: 100
  }
});

watcher
  .on('add', (path) => console.log(`文件新增: ${path}`))
  .on('change', (path) => console.log(`文件修改: ${path}`))
  .on('unlink', (path) => console.log(`文件删除: ${path}`))
  .on('addDir', (path) => console.log(`目录新增: ${path}`))
  .on('unlinkDir', (path) => console.log(`目录删除: ${path}`))
  .on('error', (error) => console.error(`监听错误: ${error}`))
  .on('ready', () => console.log('初始扫描完成'));
```

### 8.4 fs.watch vs fs.watchFile 对比

| 特性         | fs.watch                    | fs.watchFile              |
| ------------ | --------------------------- | ------------------------- |
| 实现方式     | 操作系统事件通知            | 轮询                      |
| 性能         | 高                          | 低（定期轮询）            |
| 可靠性       | 平台差异较大                | 跨平台一致                |
| 支持目录     | 是                          | 否（仅监听单个文件）       |
| 网络文件系统 | 可能不支持                  | 支持（基于轮询）           |
| CPU 占用     | 低                          | 较高（文件多时）           |

---

## 九、path 模块常用 API

> **面试题：Node.js 的 path 模块有哪些常用方法？**

```javascript
const path = require('path');

// path.join() - 拼接路径（自动处理分隔符和 ..）
path.join('/home', 'user', '..', 'admin', 'file.txt');
// '/home/admin/file.txt'

// path.resolve() - 解析为绝对路径（从右到左处理，遇到绝对路径停止）
path.resolve('src', 'index.js');
// '/当前工作目录/src/index.js'
path.resolve('/home', 'user', 'file.txt');
// '/home/user/file.txt'

// path.basename() - 获取文件名
path.basename('/home/user/file.txt');      // 'file.txt'
path.basename('/home/user/file.txt', '.txt'); // 'file'

// path.dirname() - 获取目录名
path.dirname('/home/user/file.txt');       // '/home/user'

// path.extname() - 获取扩展名
path.extname('file.txt');      // '.txt'
path.extname('file.tar.gz');   // '.gz'
path.extname('file');          // ''

// path.parse() - 解析路径为对象
path.parse('/home/user/file.txt');
// { root: '/', dir: '/home/user', base: 'file.txt', ext: '.txt', name: 'file' }

// path.format() - 从对象生成路径（parse 的逆操作）
path.format({ dir: '/home/user', base: 'file.txt' });
// '/home/user/file.txt'

// path.isAbsolute() - 判断是否为绝对路径
path.isAbsolute('/home/user');  // true
path.isAbsolute('./src');       // false

// path.relative() - 获取两个路径之间的相对路径
path.relative('/home/user/src', '/home/user/dist');
// '../dist'

// path.normalize() - 规范化路径
path.normalize('/home/user/../admin/./file.txt');
// '/home/admin/file.txt'

// path.sep - 系统路径分隔符
path.sep; // Linux/macOS: '/'   Windows: '\\'

// path.delimiter - 环境变量路径分隔符
path.delimiter; // Linux/macOS: ':'   Windows: ';'

// path.posix / path.win32 - 指定平台的方法
path.posix.join('a', 'b');   // 'a/b'（始终使用 /）
path.win32.join('a', 'b');   // 'a\\b'（始终使用 \）
```

### path.join vs path.resolve 的区别

```javascript
// path.join 只是简单拼接
path.join('src', 'index.js');          // 'src/index.js'（相对路径）
path.join('/home', 'user', 'file');    // '/home/user/file'

// path.resolve 始终返回绝对路径
path.resolve('src', 'index.js');       // '/cwd/src/index.js'（基于 cwd）
path.resolve('/home', 'user', 'file'); // '/home/user/file'

// 关键区别：处理以 / 开头的片段
path.join('/home', '/user');    // '/home/user'（简单拼接）
path.resolve('/home', '/user'); // '/user'（遇到绝对路径重新开始）
```

---

## 十、处理 CSV/JSON 大文件的最佳实践

> **面试题：如何在 Node.js 中高效处理大型 CSV 和 JSON 文件？**

### 10.1 处理大型 CSV 文件

```javascript
const fs = require('fs');
const { Transform } = require('stream');
const { pipeline } = require('stream/promises');

// 方式1：使用 csv-parser 库（推荐）
const csv = require('csv-parser');

const results = [];
fs.createReadStream('large-data.csv')
  .pipe(csv())
  .on('data', (row) => {
    // 逐行处理
    if (row.amount > 1000) {
      results.push(row);
    }
  })
  .on('end', () => {
    console.log(`筛选出 ${results.length} 条记录`);
  });

// 方式2：手动实现 CSV 解析的 Transform 流
class CsvParser extends Transform {
  constructor(options = {}) {
    super({ ...options, objectMode: true });
    this.headers = null;
    this.buffer = '';
  }

  _transform(chunk, encoding, callback) {
    this.buffer += chunk.toString();
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop(); // 保留最后一个不完整的行

    for (const line of lines) {
      if (!line.trim()) continue;
      if (!this.headers) {
        this.headers = line.split(',').map(h => h.trim());
        continue;
      }
      const values = line.split(',');
      const obj = {};
      this.headers.forEach((h, i) => { obj[h] = values[i]?.trim(); });
      this.push(obj);
    }
    callback();
  }

  _flush(callback) {
    if (this.buffer.trim() && this.headers) {
      const values = this.buffer.split(',');
      const obj = {};
      this.headers.forEach((h, i) => { obj[h] = values[i]?.trim(); });
      this.push(obj);
    }
    callback();
  }
}

// 方式3：CSV 写入
const { stringify } = require('csv-stringify');

const data = [
  { name: 'Alice', age: 30 },
  { name: 'Bob', age: 25 }
];

const stringifier = stringify({ header: true });
stringifier.pipe(fs.createWriteStream('output.csv'));

data.forEach(row => stringifier.write(row));
stringifier.end();
```

### 10.2 处理大型 JSON 文件

对于大型 JSON 文件，不能使用 `JSON.parse()` 一次性解析（内存不足），应使用流式 JSON 解析器：

```javascript
// 方式1：使用 JSONStream 库
const JSONStream = require('JSONStream');

// 假设 JSON 结构为 { "users": [ {...}, {...}, ... ] }
fs.createReadStream('huge-data.json')
  .pipe(JSONStream.parse('users.*'))
  .on('data', (user) => {
    // 逐个处理 user 对象
    console.log(user.name);
  })
  .on('end', () => {
    console.log('处理完成');
  });

// 方式2：使用 stream-json 库（更强大）
const { parser } = require('stream-json');
const { streamArray } = require('stream-json/streamers/StreamArray');

const jsonPipeline = fs.createReadStream('huge-array.json')
  .pipe(parser())
  .pipe(streamArray());

jsonPipeline.on('data', ({ key, value }) => {
  // key 是数组索引，value 是元素
  console.log(`第 ${key} 个元素:`, value);
});

// 方式3：NDJSON（Newline Delimited JSON）- 每行一个 JSON 对象
// 这是处理大量 JSON 数据的最佳格式
const readline = require('readline');

async function processNDJSON(filePath) {
  const rl = readline.createInterface({
    input: fs.createReadStream(filePath),
    crlfDelay: Infinity
  });

  let count = 0;
  for await (const line of rl) {
    if (line.trim()) {
      const obj = JSON.parse(line);
      count++;
      // 处理每个对象
    }
  }
  console.log(`处理了 ${count} 条记录`);
}

// 方式4：大型 JSON 写入（流式）
class JsonArrayWriter {
  constructor(filePath) {
    this.stream = fs.createWriteStream(filePath);
    this.first = true;
    this.stream.write('[\n');
  }

  write(obj) {
    if (!this.first) {
      this.stream.write(',\n');
    }
    this.first = false;
    this.stream.write(JSON.stringify(obj));
  }

  end() {
    this.stream.write('\n]');
    this.stream.end();
    return new Promise((resolve) => this.stream.on('finish', resolve));
  }
}

const writer = new JsonArrayWriter('output.json');
for (let i = 0; i < 1000000; i++) {
  writer.write({ id: i, name: `user_${i}` });
}
await writer.end();
```

---

## 常见面试题汇总

> **Q：`fs.readFile` 和 `fs.createReadStream` 有什么区别？什么时候使用哪个？**

`fs.readFile` 将整个文件读入内存后返回，适合小文件。`fs.createReadStream` 以流的方式分块读取，适合大文件。当文件大于可用内存或需要逐步处理时，必须使用流。一般原则：文件小于 100MB 可以用 `readFile`，大于 100MB 建议用流。

> **Q：流的 `data` 事件和 `readable` 事件有什么区别？**

`data` 事件在流动模式下触发，每当有数据可读时自动触发，数据以参数形式传递给回调函数。`readable` 事件在暂停模式下触发，通知消费者有数据可读，需要手动调用 `read()` 方法来获取数据。不要同时使用两者。

> **Q：为什么 `pipe()` 不会导致内存溢出？**

`pipe()` 内部实现了背压机制。当可写流的缓冲区满了（`write()` 返回 `false`）时，`pipe()` 会自动调用可读流的 `pause()` 暂停数据读取。当可写流触发 `drain` 事件（缓冲区排空）时，`pipe()` 会自动调用 `resume()` 恢复读取。这样确保了内存中始终只保留有限的数据。

> **Q：如何实现一个文件的逐行读取？**

使用 `readline` 模块配合 `createReadStream`：创建一个 readline 接口，将文件流作为输入。可以通过 `for await...of` 遍历每一行，也可以监听 `line` 事件。这种方式内存效率高，适合处理大文件。

> **Q：`path.join` 和 `path.resolve` 的区别？**

`path.join` 只是将多个路径片段用系统分隔符拼接起来，结果可能是相对路径。`path.resolve` 从右到左解析路径，始终返回绝对路径（如果所有参数都是相对路径，则以 `process.cwd()` 为基准）。处理以 `/` 开头的中间路径时，`join` 会保留前面的路径，而 `resolve` 会将其视为新的根路径。
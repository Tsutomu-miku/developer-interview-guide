# Node.js 事件循环面试指南

## 一、事件循环概述

> **面试题：什么是 Node.js 的事件循环？它是如何工作的？**

事件循环（Event Loop）是 Node.js 处理非阻塞 I/O 操作的核心机制。尽管 JavaScript 是单线程的，但通过将操作尽可能地委托给操作系统内核（或 libuv 线程池），Node.js 能够高效地处理并发操作。

Node.js 的事件循环由 **libuv** 库实现。libuv 是一个跨平台的异步 I/O 库，它为 Node.js 提供了事件循环、线程池、文件系统操作、DNS 解析、网络通信等能力。

事件循环的基本流程：
1. Node.js 启动后，初始化事件循环
2. 处理输入脚本（同步代码执行、注册异步回调）
3. 进入事件循环，按照阶段顺序不断轮询
4. 当没有更多的回调需要处理、没有活跃的句柄/请求时，进程退出

```
   ┌───────────────────────────┐
┌─>│           timers          │  执行 setTimeout/setInterval 回调
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     pending callbacks     │  执行系统级别的回调（如 TCP 错误）
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │       idle, prepare       │  仅 Node.js 内部使用
│  └─────────────┬─────────────┘      ┌───────────────┐
│  ┌─────────────┴─────────────┐      │   incoming:   │
│  │           poll            │<─────┤  connections, │
│  └─────────────┬─────────────┘      │   data, etc.  │
│  ┌─────────────┴─────────────┐      └───────────────┘
│  │           check           │  执行 setImmediate 回调
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │      close callbacks      │  执行关闭回调，如 socket.on('close')
│  └─────────────┬─────────────┘
└─────────────────┘
```

---

## 二、事件循环六个阶段详解

> **面试题：请详细介绍 Node.js 事件循环的六个阶段。**

### 2.1 timers（定时器阶段）

执行已经到期的 `setTimeout()` 和 `setInterval()` 的回调。注意，定时器的回调不一定在精确的延迟时间后执行，它只保证不会在指定时间之前执行。实际执行时间取决于系统调度和事件循环中其他回调的执行情况。

```javascript
// setTimeout 的最小延迟
// 即使设置为 0ms，实际延迟至少为 1ms（Node.js 将 0 当作 1 处理）
setTimeout(() => console.log('timer'), 0);
```

### 2.2 pending callbacks（待定回调阶段）

执行延迟到下一个循环迭代的 I/O 回调。这个阶段处理一些系统级别的操作的回调，例如 TCP 连接错误（`ECONNREFUSED`）。大部分 I/O 回调是在 poll 阶段处理的，这里处理的是上一轮循环中推迟的回调。

### 2.3 idle, prepare（空闲/准备阶段）

这两个阶段仅供 Node.js 内部使用，开发者无法直接与之交互。`idle` 阶段在每次循环中都会执行，`prepare` 阶段在 poll 之前执行。

### 2.4 poll（轮询阶段）

这是事件循环中最重要的阶段，负责两件事：

1. **计算应该阻塞和轮询 I/O 的时间**
2. **处理 poll 队列中的事件和回调**

当事件循环进入 poll 阶段且没有被调度的定时器时：
- 如果 poll 队列**不为空**：依次执行队列中的回调，直到队列为空或达到系统限制。
- 如果 poll 队列**为空**：
  - 如果有 `setImmediate()` 回调：进入 check 阶段。
  - 如果没有 `setImmediate()`：等待回调被添加到队列中，然后立即执行。

如果有到期的定时器，会绕回到 timers 阶段执行定时器回调。

### 2.5 check（检查阶段）

专门执行 `setImmediate()` 的回调。`setImmediate()` 实际上是一个特殊的定时器，它在事件循环的 check 阶段执行，即在 poll 阶段完成后立即执行。

### 2.6 close callbacks（关闭回调阶段）

执行关闭事件的回调，如 `socket.on('close', ...)` 或 `server.on('close', ...)`。如果一个 socket 或句柄被突然关闭（如 `socket.destroy()`），`close` 事件将在这个阶段触发。

---

## 三、process.nextTick vs Promise.then vs setTimeout vs setImmediate

> **面试题：请比较 process.nextTick、Promise.then、setTimeout 和 setImmediate 的执行顺序和区别。**

### 3.1 执行优先级

```
process.nextTick > Promise.then (微任务) > setTimeout/setInterval (timers 阶段) ≈ setImmediate (check 阶段)
```

### 3.2 详细对比

| 方法              | 类型       | 所属阶段      | 优先级   | 说明                                           |
| ----------------- | ---------- | ------------- | -------- | ---------------------------------------------- |
| `process.nextTick`| nextTick队列| 不属于任何阶段 | 最高     | 在当前操作完成后、事件循环继续前立即执行         |
| `Promise.then`    | 微任务     | 微任务队列    | 次高     | 在 nextTick 之后、下一个宏任务之前执行           |
| `setTimeout(fn, 0)`| 宏任务    | timers 阶段   | 较低     | 至少延迟 1ms，在 timers 阶段执行                |
| `setImmediate`    | 宏任务     | check 阶段    | 较低     | 在当前 poll 阶段完成后执行                       |

### 3.3 process.nextTick 的特殊性

`process.nextTick` 不属于事件循环的任何阶段。它有自己独立的队列，在每个阶段切换之前都会被清空执行。如果递归调用 `process.nextTick`，可能会饿死事件循环（I/O 永远得不到处理）。

```javascript
// 危险！会饿死事件循环
function dangerous() {
  process.nextTick(dangerous);
}
dangerous();
// I/O 回调永远不会执行
```

### 3.4 setTimeout vs setImmediate

在主模块中，两者的执行顺序是**不确定的**，因为受到进程性能和系统调度的影响：

```javascript
// 主模块中 - 顺序不确定
setTimeout(() => console.log('setTimeout'), 0);
setImmediate(() => console.log('setImmediate'));
// 可能输出: setTimeout → setImmediate
// 也可能: setImmediate → setTimeout
```

但在一个 I/O 回调中，`setImmediate` **总是先于** `setTimeout` 执行：

```javascript
const fs = require('fs');

fs.readFile(__filename, () => {
  setTimeout(() => console.log('setTimeout'), 0);
  setImmediate(() => console.log('setImmediate'));
});
// 输出顺序总是: setImmediate → setTimeout
// 因为在 I/O 回调（poll 阶段）中，check 阶段紧随其后
```

---

## 四、微任务与宏任务在 Node.js 中的执行顺序

> **面试题：Node.js 中微任务和宏任务的执行顺序是怎样的？**

### 4.1 任务分类

**微任务（Microtask）**：
- `process.nextTick`（严格来说是 nextTick 队列，优先级高于微任务）
- `Promise.then` / `Promise.catch` / `Promise.finally`
- `queueMicrotask()`

**宏任务（Macrotask / Task）**：
- `setTimeout` / `setInterval`
- `setImmediate`
- I/O 操作回调
- UI 渲染（浏览器环境）

### 4.2 执行模型（Node.js 11+ 版本）

```
同步代码执行完毕
  ↓
清空 nextTick 队列
  ↓
清空微任务队列（Promise 等）
  ↓
进入事件循环 timers 阶段
  → 执行一个宏任务回调
    → 清空 nextTick 队列
    → 清空微任务队列
  → 执行下一个宏任务回调
    → 清空 nextTick 队列
    → 清空微任务队列
  → ...
  ↓
进入下一个阶段
  → 同样的模式：每个宏任务后清空微任务
  ↓
...循环
```

关键规则：**每执行完一个宏任务回调，就会清空所有的 nextTick 队列和微任务队列**。

---

## 五、Node.js 10 vs Node.js 11+ 事件循环差异

> **面试题：Node.js 10 和 Node.js 11+ 的事件循环有什么区别？**

这是一个非常重要的知识点。Node.js 11 对事件循环的行为做了关键性的改变，使其更接近浏览器的行为。

### Node.js 10（旧行为）

在同一个阶段中，先执行完**所有**宏任务回调，然后再统一清空微任务队列。

### Node.js 11+（新行为）

在同一个阶段中，每执行完**一个**宏任务回调，就立即清空 nextTick 队列和微任务队列，然后再执行下一个宏任务回调。

```javascript
// 关键差异示例
setTimeout(() => {
  console.log('timer1');
  Promise.resolve().then(() => console.log('promise1'));
}, 0);

setTimeout(() => {
  console.log('timer2');
  Promise.resolve().then(() => console.log('promise2'));
}, 0);

// Node.js 10 输出:
// timer1 → timer2 → promise1 → promise2
// （先执行完所有 timers 回调，再处理微任务）

// Node.js 11+ 输出:
// timer1 → promise1 → timer2 → promise2
// （每个 timer 回调后立即处理微任务，与浏览器行为一致）
```

### 为什么要做这个改变

为了与浏览器的行为保持一致。在浏览器中，每执行一个宏任务后就会处理所有微任务，Node.js 11+ 统一了这一行为，减少了跨平台开发的心智负担。

---

## 六、阻塞事件循环的场景与解决方案

> **面试题：哪些操作会阻塞 Node.js 的事件循环？如何避免？**

### 6.1 阻塞场景

1. **CPU 密集型计算**：大循环、复杂算法、数据加密/解密
2. **同步 I/O 操作**：`fs.readFileSync`、`fs.writeFileSync` 等同步方法
3. **JSON 操作大对象**：`JSON.parse()` 和 `JSON.stringify()` 处理超大 JSON
4. **正则表达式灾难性回溯**：不当的正则表达式匹配
5. **递归调用 process.nextTick**：饿死事件循环
6. **大量同步日志写入**

```javascript
// 阻塞示例：CPU 密集计算
function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
fibonacci(45); // 会阻塞事件循环好几秒

// 阻塞示例：同步文件读取
const data = fs.readFileSync('huge-file.txt'); // 阻塞！

// 阻塞示例：灾难性正则回溯
const evil = /^(a+)+$/;
evil.test('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa!'); // 可能导致 ReDoS
```

### 6.2 解决方案

```javascript
// 方案1：使用 Worker Threads
const { Worker, isMainThread, parentPort } = require('worker_threads');

if (isMainThread) {
  const worker = new Worker(__filename);
  worker.on('message', (result) => {
    console.log('计算结果:', result);
  });
  worker.postMessage(45); // 将 CPU 密集任务交给 Worker
} else {
  parentPort.on('message', (n) => {
    parentPort.postMessage(fibonacci(n));
  });
}

// 方案2：将大任务拆分为小块，使用 setImmediate 让出控制权
function processChunk(data, index, callback) {
  if (index >= data.length) return callback();
  // 处理一小块数据
  processItem(data[index]);
  // 让出事件循环
  setImmediate(() => processChunk(data, index + 1, callback));
}

// 方案3：使用 child_process 创建子进程
const { fork } = require('child_process');
const child = fork('./heavy-computation.js');
child.send({ n: 45 });
child.on('message', (result) => console.log(result));

// 方案4：使用异步 API 替代同步 API
// 不要这样做
const data = fs.readFileSync('file.txt');
// 应该这样做
const data = await fs.promises.readFile('file.txt');

// 方案5：使用流处理大文件
const readStream = fs.createReadStream('huge-file.txt');
readStream.on('data', (chunk) => { /* 逐块处理 */ });
```

---

## 七、经典面试输出题

### 题目一：基础执行顺序

```javascript
console.log('1');

setTimeout(function() {
  console.log('2');
  process.nextTick(function() {
    console.log('3');
  });
  new Promise(function(resolve) {
    console.log('4');
    resolve();
  }).then(function() {
    console.log('5');
  });
});

process.nextTick(function() {
  console.log('6');
});

new Promise(function(resolve) {
  console.log('7');
  resolve();
}).then(function() {
  console.log('8');
});

setTimeout(function() {
  console.log('9');
  process.nextTick(function() {
    console.log('10');
  });
  new Promise(function(resolve) {
    console.log('11');
    resolve();
  }).then(function() {
    console.log('12');
  });
});
```

**答案（Node.js 11+）**：`1 → 7 → 6 → 8 → 2 → 4 → 3 → 5 → 9 → 11 → 10 → 12`

**解析**：
1. 同步代码执行：输出 `1`，注册 setTimeout1，注册 nextTick，Promise 构造函数同步执行输出 `7`，注册 then，注册 setTimeout2。
2. 同步代码执行完毕，先清空 nextTick 队列：输出 `6`。
3. 清空微任务队列：输出 `8`。
4. 进入 timers 阶段，执行 setTimeout1：输出 `2`，Promise 构造函数输出 `4`，注册 nextTick 和 then。
5. setTimeout1 执行完，清空 nextTick：输出 `3`，清空微任务：输出 `5`。
6. 执行 setTimeout2：输出 `9`，Promise 构造函数输出 `11`，注册 nextTick 和 then。
7. setTimeout2 执行完，清空 nextTick：输出 `10`，清空微任务：输出 `12`。

---

### 题目二：nextTick 与 Promise 的优先级

```javascript
process.nextTick(() => {
  console.log('nextTick1');
  process.nextTick(() => {
    console.log('nextTick2');
  });
});

Promise.resolve().then(() => {
  console.log('promise1');
  process.nextTick(() => {
    console.log('nextTick in promise');
  });
}).then(() => {
  console.log('promise2');
});
```

**答案**：`nextTick1 → nextTick2 → promise1 → promise2 → nextTick in promise`

**解析**：
1. 同步代码执行完毕，先清空 nextTick 队列：输出 `nextTick1`。
2. nextTick1 的回调中又注册了 nextTick2，继续清空 nextTick 队列：输出 `nextTick2`。
3. nextTick 队列清空后，开始清空微任务队列：输出 `promise1`。
4. promise1 中注册了新的 nextTick，但此时微任务队列中还有 promise2（then 链），继续清空微任务：输出 `promise2`。
5. 微任务清空后，再检查 nextTick 队列：输出 `nextTick in promise`。

**注意**：在 nextTick 回调中新添加的 nextTick 会在当前 nextTick 队列清空期间继续执行。但 Promise 中新添加的 nextTick 需要等到当前微任务清空后再执行。

---

### 题目三：setTimeout 与 setImmediate

```javascript
const fs = require('fs');

console.log('start');

setTimeout(() => console.log('setTimeout1'), 0);
setTimeout(() => {
  console.log('setTimeout2');
  Promise.resolve().then(() => console.log('promise in setTimeout'));
}, 0);

setImmediate(() => console.log('setImmediate1'));
setImmediate(() => {
  console.log('setImmediate2');
  process.nextTick(() => console.log('nextTick in setImmediate'));
});

fs.readFile(__filename, () => {
  console.log('I/O callback');
  setTimeout(() => console.log('setTimeout in I/O'), 0);
  setImmediate(() => console.log('setImmediate in I/O'));
  process.nextTick(() => console.log('nextTick in I/O'));
});

Promise.resolve().then(() => console.log('promise1'));
process.nextTick(() => console.log('nextTick1'));

console.log('end');
```

**答案**：
```
start
end
nextTick1
promise1
setTimeout1
setTimeout2
promise in setTimeout
setImmediate1
setImmediate2
nextTick in setImmediate
I/O callback
nextTick in I/O
setImmediate in I/O
setTimeout in I/O
```

**解析**：
1. 同步代码：输出 `start`、`end`。
2. 清空 nextTick：`nextTick1`。
3. 清空微任务：`promise1`。
4. timers 阶段：`setTimeout1`，然后 `setTimeout2`，执行后清空微任务 `promise in setTimeout`。
5. check 阶段：`setImmediate1`，然后 `setImmediate2`，执行后清空 nextTick `nextTick in setImmediate`。
6. 下一轮循环中 I/O 回调就绪：`I/O callback`，清空 `nextTick in I/O`。
7. 在 I/O 回调中注册的 setImmediate 优先于 setTimeout：`setImmediate in I/O`。
8. 最后执行 `setTimeout in I/O`。

---

### 题目四：async/await 与事件循环

```javascript
async function async1() {
  console.log('async1 start');
  await async2();
  console.log('async1 end');
}

async function async2() {
  console.log('async2');
  return new Promise((resolve) => {
    console.log('async2 promise');
    resolve();
  }).then(() => {
    console.log('async2 then');
  });
}

console.log('script start');

setTimeout(() => {
  console.log('setTimeout');
}, 0);

async1();

new Promise((resolve) => {
  console.log('promise1');
  resolve();
}).then(() => {
  console.log('promise2');
});

process.nextTick(() => {
  console.log('nextTick');
});

console.log('script end');
```

**答案**：`script start → async1 start → async2 → async2 promise → promise1 → script end → nextTick → async2 then → promise2 → async1 end → setTimeout`

**解析**：
1. 同步代码依次执行：`script start`，调用 async1 输出 `async1 start`，调用 async2 输出 `async2` 和 `async2 promise`，然后 async2 返回的 Promise 的 then 注册微任务。
2. `await` 等同于将后续代码放入 `.then()`，但需要等待 async2 返回的 Promise 完全 resolve。
3. 继续同步代码：输出 `promise1`，注册 then 微任务，注册 nextTick，输出 `script end`。
4. 清空 nextTick：`nextTick`。
5. 清空微任务：`async2 then`（async2 中 Promise 的 then），`promise2`（外部 Promise 的 then）。
6. 此时 async2 完全 resolve，`async1 end` 被放入微任务队列并执行：`async1 end`。
7. 进入 timers 阶段：`setTimeout`。

---

### 题目五：综合题

```javascript
console.log('1');

setTimeout(() => {
  console.log('2');
}, 10);

setImmediate(() => {
  console.log('3');
});

new Promise((resolve) => {
  console.log('4');
  resolve();
  console.log('5');
}).then(() => {
  console.log('6');

  setTimeout(() => {
    console.log('7');
  }, 0);

  setImmediate(() => {
    console.log('8');
  });
});

process.nextTick(() => {
  console.log('9');

  process.nextTick(() => {
    console.log('10');
  });
});

console.log('11');
```

**答案**：`1 → 4 → 5 → 11 → 9 → 10 → 6 → 3 → 8 → 7 → 2`

**解析**：
1. 同步代码：`1`，setTimeout(10ms) 注册，setImmediate 注册，Promise 构造函数中 `4` 和 `5`，then 注册，nextTick 注册，`11`。
2. 清空 nextTick：`9`，新 nextTick 注册，继续清空：`10`。
3. 清空微任务：`6`，注册 setTimeout(0ms) 和 setImmediate。
4. check 阶段（setImmediate）：`3`、`8`。
5. timers 阶段：`7`（0ms 定时器已到期），`2`（10ms 定时器可能已到期，取决于执行速度）。

---

### 题目六（附加）：微任务嵌套

```javascript
Promise.resolve()
  .then(() => {
    console.log('then1');
    return Promise.resolve('then1 return');
  })
  .then((val) => {
    console.log(val);
  });

Promise.resolve()
  .then(() => {
    console.log('then2');
  })
  .then(() => {
    console.log('then3');
  })
  .then(() => {
    console.log('then4');
  });
```

**答案**：`then1 → then2 → then3 → then1 return → then4`

**解析**：当 `.then()` 中返回一个 `Promise.resolve()` 时，会产生额外的两个微任务（根据 ECMAScript 规范，`return Promise.resolve(val)` 会比 `return val` 多两个微任务周期）。因此 `then1 return` 会被延迟执行。

---

## 八、Worker Threads（工作线程）

> **面试题：什么是 Worker Threads？它和 child_process、cluster 有什么区别？**

Worker Threads 是 Node.js 10.5 引入（Node.js 12 稳定）的多线程方案，允许在独立的线程中运行 JavaScript 代码，适用于 CPU 密集型任务。

### 8.1 基本使用

```javascript
// main.js
const { Worker, isMainThread, workerData } = require('worker_threads');

if (isMainThread) {
  // 主线程
  const worker = new Worker('./worker.js', {
    workerData: { start: 1, end: 1000000 }
  });

  worker.on('message', (result) => {
    console.log('计算结果:', result);
  });

  worker.on('error', (err) => {
    console.error('Worker 错误:', err);
  });

  worker.on('exit', (code) => {
    if (code !== 0) console.error(`Worker 以退出码 ${code} 停止`);
  });
} else {
  // Worker 线程
  // ...
}

// worker.js
const { parentPort, workerData } = require('worker_threads');

function heavyComputation({ start, end }) {
  let sum = 0;
  for (let i = start; i <= end; i++) {
    sum += i;
  }
  return sum;
}

const result = heavyComputation(workerData);
parentPort.postMessage(result);
```

### 8.2 共享内存（SharedArrayBuffer）

Worker Threads 支持通过 `SharedArrayBuffer` 实现线程间的共享内存，配合 `Atomics` API 进行线程安全操作：

```javascript
// 主线程
const { Worker } = require('worker_threads');

const sharedBuffer = new SharedArrayBuffer(4); // 4 字节
const sharedArray = new Int32Array(sharedBuffer);
sharedArray[0] = 0;

const worker = new Worker('./worker.js', {
  workerData: { sharedBuffer }
});

worker.on('exit', () => {
  console.log('共享值:', sharedArray[0]); // 被 worker 修改后的值
});

// worker.js
const { workerData } = require('worker_threads');
const sharedArray = new Int32Array(workerData.sharedBuffer);
Atomics.add(sharedArray, 0, 42); // 原子操作
```

### 8.3 与其他多任务方案的对比

| 特性           | Worker Threads | child_process | Cluster    |
| -------------- | -------------- | ------------- | ---------- |
| 线程/进程      | 线程           | 进程          | 进程       |
| 内存共享       | 支持           | 不支持        | 不支持     |
| 通信方式       | MessagePort    | IPC 管道      | IPC 管道   |
| 启动开销       | 较小           | 较大          | 较大       |
| 适用场景       | CPU 密集计算   | 运行外部程序  | 多核 HTTP  |
| 资源消耗       | 低             | 高            | 高         |

---

## 九、child_process（子进程）

> **面试题：Node.js 中 child_process 模块提供了哪些创建子进程的方法？它们有什么区别？**

### 9.1 四种创建方式

```javascript
const { exec, execFile, spawn, fork } = require('child_process');

// 1. exec - 创建 shell 执行命令，缓冲输出
// 适用于：执行简单的 shell 命令，输出数据量不大
exec('ls -la', { maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
  if (error) { console.error('执行错误:', error); return; }
  console.log('stdout:', stdout);
  console.log('stderr:', stderr);
});

// 2. execFile - 直接执行文件，不创建 shell（更安全、更高效）
// 适用于：执行特定的可执行文件
execFile('node', ['--version'], (error, stdout) => {
  console.log('Node 版本:', stdout);
});

// 3. spawn - 创建子进程，流式处理输入输出
// 适用于：长时间运行的进程、大量数据输出
const child = spawn('find', ['.', '-name', '*.js']);

child.stdout.on('data', (data) => {
  console.log(`stdout: ${data}`);
});

child.stderr.on('data', (data) => {
  console.error(`stderr: ${data}`);
});

child.on('close', (code) => {
  console.log(`子进程退出码: ${code}`);
});

// 4. fork - 创建 Node.js 子进程，内置 IPC 通信通道
// 适用于：运行 Node.js 脚本，父子进程需要通信
const worker = fork('./compute.js');

worker.send({ type: 'start', data: [1, 2, 3, 4, 5] });

worker.on('message', (msg) => {
  console.log('子进程返回:', msg);
});
```

### 9.2 详细对比

| 方法       | 是否创建 Shell | 输出方式 | IPC 通道 | 适用场景                       |
| ---------- | -------------- | -------- | -------- | ------------------------------ |
| `exec`     | 是             | 缓冲     | 无       | 简单 shell 命令，小量输出      |
| `execFile` | 否             | 缓冲     | 无       | 执行文件，更安全               |
| `spawn`    | 可选           | 流       | 可选     | 长时间进程，大量数据            |
| `fork`     | 否             | 流       | 自动创建 | Node.js 脚本，需要父子通信     |

### 9.3 fork 通信示例

```javascript
// parent.js
const { fork } = require('child_process');
const child = fork('./child.js');

child.send({ type: 'compute', n: 40 });

child.on('message', (msg) => {
  console.log('结果:', msg.result);
  child.kill(); // 完成后杀死子进程
});

// child.js
process.on('message', (msg) => {
  if (msg.type === 'compute') {
    const result = fibonacci(msg.n);
    process.send({ result });
  }
});

function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}
```

---

## 十、Cluster 模块（多进程）

> **面试题：Node.js 的 Cluster 模块是什么？它是如何实现多进程的？**

Cluster 模块允许创建多个子进程（worker），它们共享同一个服务器端口，充分利用多核 CPU。

### 10.1 基本使用

```javascript
const cluster = require('cluster');
const http = require('http');
const numCPUs = require('os').cpus().length;

if (cluster.isMaster) {
  console.log(`主进程 ${process.pid} 正在运行`);

  // Fork workers
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  cluster.on('exit', (worker, code, signal) => {
    console.log(`工作进程 ${worker.process.pid} 已退出`);
    // 自动重启
    cluster.fork();
  });

  // 监听工作进程的消息
  for (const id in cluster.workers) {
    cluster.workers[id].on('message', (msg) => {
      console.log(`收到来自工作进程 ${id} 的消息:`, msg);
    });
  }
} else {
  // 工作进程可以共享同一个 TCP 连接
  http.createServer((req, res) => {
    res.writeHead(200);
    res.end(`Hello from worker ${process.pid}\n`);
  }).listen(8000);

  console.log(`工作进程 ${process.pid} 已启动`);
}
```

### 10.2 工作原理

Cluster 的底层实现基于 `child_process.fork()`。主进程（Master）负责监听端口并将连接分发给工作进程（Worker）。

在 Linux 上，Node.js 默认使用**轮询（Round-Robin）调度策略**（`cluster.schedulingPolicy = cluster.SCHED_RR`）。主进程接受连接，然后以轮询方式将其分发给可用的工作进程。

在 Windows 上，默认使用操作系统的调度策略（`SCHED_NONE`），由操作系统决定哪个工作进程处理连接。

### 10.3 Cluster vs PM2

在生产环境中，通常使用 PM2 来管理 Node.js 的多进程，因为 PM2 提供了更完善的功能：

- 进程守护和自动重启
- 负载均衡
- 日志管理
- 零停机重启（graceful reload）
- 监控和性能指标
- 环境变量管理

```bash
# PM2 使用 cluster 模式
pm2 start app.js -i max  # 根据 CPU 核心数创建进程
pm2 start app.js -i 4    # 创建 4 个进程
pm2 reload app.js         # 零停机重启
pm2 monit                 # 监控面板
```

---

## 常见面试题汇总

> **Q：事件循环中，nextTick 队列和微任务队列哪个先执行？**

nextTick 队列先执行。在每个阶段切换时（以及每个宏任务执行后），Node.js 首先清空 nextTick 队列，然后清空 Promise 微任务队列，最后才进入下一个阶段或执行下一个宏任务。

> **Q：为什么 process.nextTick 的优先级高于 Promise？**

这是 Node.js 的设计决策。`process.nextTick` 的回调被存放在一个独立的队列中，这个队列会在每次 C++ 层和 JavaScript 层切换时清空。从实现角度看，nextTick 队列是在 V8 的微任务队列之外维护的，因此具有更高的优先级。

> **Q：如何让 CPU 密集型任务不阻塞主线程？**

1. 使用 `Worker Threads` 在独立线程中运行
2. 使用 `child_process.fork()` 创建子进程处理
3. 将大任务分割成小块，使用 `setImmediate()` 在事件循环迭代间穿插执行
4. 使用 C++ 原生插件（Addon）处理
5. 将计算任务卸载到外部服务（如 Rust/Go 微服务）

> **Q：setImmediate 和 setTimeout(fn, 0) 谁先执行？**

在顶层代码中，两者的执行顺序不确定，取决于系统性能和事件循环的启动时间。但在 I/O 回调中，`setImmediate` 总是先于 `setTimeout(fn, 0)` 执行，因为 I/O 回调在 poll 阶段执行，poll 之后紧接着是 check 阶段（setImmediate），而 timers 阶段要等到下一轮循环。
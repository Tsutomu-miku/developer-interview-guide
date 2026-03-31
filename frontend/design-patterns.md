# 前端设计模式与架构

> **面试优先级**: ⭐⭐⭐ (LOW PRIORITY — 中大厂中高级岗位常考，但频率低于框架原理和工程化)
>
> 本章覆盖：经典设计模式在前端的落地、主流架构模式对比、React 高级设计模式、组件设计原则（SOLID）、以及 10+ 道高频面试题。

---

## 一、设计模式在前端的应用

### 1.1 单例模式（Singleton）

> **核心思想**：保证一个类只有一个实例，并提供全局访问点。

**典型场景**：全局状态管理（Store）、全局弹窗/Toast、全局 Loading 遮罩。

```javascript
// ========== 通用单例工厂 ==========
class Singleton {
  static getInstance(...args) {
    if (!this._instance) {
      this._instance = new this(...args);
    }
    return this._instance;
  }
}

// ========== 全局弹窗单例 ==========
class Modal extends Singleton {
  constructor() {
    super();
    this.visible = false;
    this.el = document.createElement('div');
    this.el.className = 'global-modal';
    document.body.appendChild(this.el);
  }

  show(content) {
    this.visible = true;
    this.el.innerHTML = content;
    this.el.style.display = 'block';
  }

  hide() {
    this.visible = false;
    this.el.style.display = 'none';
  }
}

// 无论调用多少次，都返回同一个实例
const m1 = Modal.getInstance();
const m2 = Modal.getInstance();
console.log(m1 === m2); // true

// ========== 全局状态单例（简化版 Store） ==========
class Store extends Singleton {
  constructor(initialState = {}) {
    super();
    this._state = initialState;
    this._listeners = [];
  }

  getState() {
    return this._state;
  }

  setState(partial) {
    this._state = { ...this._state, ...partial };
    this._listeners.forEach((fn) => fn(this._state));
  }

  subscribe(fn) {
    this._listeners.push(fn);
    return () => {
      this._listeners = this._listeners.filter((l) => l !== fn);
    };
  }
}
```

**面试要点**：
- ES Module 天然单例（模块只执行一次）；
- `new Vuex.Store()` / `createStore()` 本质是单例思想；
- 注意惰性初始化与线程安全（JS 单线程无此问题）。

---

### 1.2 观察者模式 / 发布订阅模式

> **观察者模式**：Subject（被观察者）直接通知 Observer（观察者），二者紧耦合。
>
> **发布/订阅模式**：通过中间的「事件通道（EventBus）」解耦，发布者和订阅者互不感知。

#### 手写 EventEmitter（高频面试题）

```javascript
class EventEmitter {
  constructor() {
    this._events = Object.create(null); // 无原型链，更纯净
  }

  // 订阅事件
  on(event, fn) {
    (this._events[event] || (this._events[event] = [])).push(fn);
    return this; // 支持链式调用
  }

  // 只订阅一次
  once(event, fn) {
    const wrapper = (...args) => {
      fn.apply(this, args);
      this.off(event, wrapper);
    };
    wrapper._original = fn; // 保留引用，方便 off 时也能移除
    this.on(event, wrapper);
    return this;
  }

  // 触发事件
  emit(event, ...args) {
    const fns = this._events[event];
    if (!fns || fns.length === 0) return false;
    // 拷贝一份防止在回调中 off 导致数组塌陷
    fns.slice().forEach((fn) => fn.apply(this, args));
    return true;
  }

  // 取消订阅
  off(event, fn) {
    if (!fn) {
      // 不传 fn 则移除该事件所有监听
      delete this._events[event];
      return this;
    }
    const fns = this._events[event];
    if (!fns) return this;
    this._events[event] = fns.filter(
      (f) => f !== fn && f._original !== fn
    );
    return this;
  }

  // 获取监听器数量
  listenerCount(event) {
    return (this._events[event] || []).length;
  }

  // 移除所有事件
  removeAllListeners() {
    this._events = Object.create(null);
    return this;
  }
}

// ---------- 使用示例 ----------
const bus = new EventEmitter();
const handler = (data) => console.log('收到:', data);

bus.on('login', handler);
bus.once('init', () => console.log('初始化仅执行一次'));

bus.emit('login', { user: 'Tom' }); // 收到: { user: 'Tom' }
bus.emit('init');                    // 初始化仅执行一次
bus.emit('init');                    // 无输出

bus.off('login', handler);
bus.emit('login', { user: 'Jerry' }); // 无输出
```

**面试追问**：
- `on` 与 `addEventListener` 的区别？→ 后者在 DOM 上，支持 `capture / passive / once` 选项。
- 如何避免内存泄漏？→ 组件卸载时 `off`；使用 WeakRef 存储回调。
- `once` 为什么要保留 `_original`？→ 允许用户用原始函数 `off`。

---

### 1.3 策略模式（Strategy）

> **核心思想**：定义一系列算法，把它们封装起来，并且使它们可以互相替换。

**典型场景**：表单校验、权限判断、价格计算。

```javascript
// ========== 表单校验策略 ==========
const strategies = {
  required(value, errMsg) {
    if (value.trim() === '') return errMsg;
  },
  minLength(value, length, errMsg) {
    if (value.length < length) return errMsg;
  },
  maxLength(value, length, errMsg) {
    if (value.length > length) return errMsg;
  },
  isMobile(value, errMsg) {
    if (!/^1[3-9]\d{9}$/.test(value)) return errMsg;
  },
  isEmail(value, errMsg) {
    if (!/^\w+@\w+\.\w+$/.test(value)) return errMsg;
  },
};

class Validator {
  constructor() {
    this.rules = [];
  }

  addRule(value, strategyArr) {
    // strategyArr: ['required:用户名不能为空', 'minLength:6:长度不少于6位']
    strategyArr.forEach((rule) => {
      const parts = rule.split(':');
      const strategyName = parts.shift();
      const errMsg = parts.pop();
      this.rules.push(() => strategies[strategyName](value, ...parts, errMsg));
    });
  }

  validate() {
    for (const rule of this.rules) {
      const err = rule();
      if (err) return err;
    }
    return null; // 校验通过
  }
}

// ---------- 使用 ----------
const validator = new Validator();
validator.addRule('', ['required:用户名不能为空']);
validator.addRule('123', ['minLength:6:密码不少于6位']);
console.log(validator.validate()); // "用户名不能为空"
```

---

### 1.4 装饰器模式（Decorator）

> **核心思想**：在不改变原对象的情况下，动态地给对象添加额外职责。

**前端落地**：React HOC、Class Decorators、函数包装。

```javascript
// ========== 函数装饰器：日志 ==========
function withLog(fn) {
  return function (...args) {
    console.log(`[LOG] 调用 ${fn.name}，参数:`, args);
    const result = fn.apply(this, args);
    console.log(`[LOG] 返回值:`, result);
    return result;
  };
}

const add = (a, b) => a + b;
const loggedAdd = withLog(add);
loggedAdd(1, 2);
// [LOG] 调用 add，参数: [1, 2]
// [LOG] 返回值: 3

// ========== React HOC（装饰器思想） ==========
function withAuth(WrappedComponent) {
  return function AuthComponent(props) {
    const isLoggedIn = useAuth(); // 自定义 Hook
    if (!isLoggedIn) {
      return <Redirect to="/login" />;
    }
    return <WrappedComponent {...props} />;
  };
}

// 使用
const ProtectedPage = withAuth(DashboardPage);

// ========== ES 装饰器提案（Stage 3） ==========
function readonly(target, name, descriptor) {
  descriptor.writable = false;
  return descriptor;
}

class MathHelper {
  @readonly
  PI() {
    return 3.14159;
  }
}
```

---

### 1.5 代理模式（Proxy）

> **核心思想**：为其他对象提供一种代理以控制对这个对象的访问。

```javascript
// ========== 数据响应式代理（Vue 3 原理简化） ==========
function reactive(target) {
  const handler = {
    get(obj, key, receiver) {
      const result = Reflect.get(obj, key, receiver);
      track(obj, key); // 依赖收集
      // 递归代理嵌套对象
      return typeof result === 'object' && result !== null
        ? reactive(result)
        : result;
    },
    set(obj, key, value, receiver) {
      const oldVal = obj[key];
      const result = Reflect.set(obj, key, value, receiver);
      if (oldVal !== value) {
        trigger(obj, key); // 触发更新
      }
      return result;
    },
    deleteProperty(obj, key) {
      const result = Reflect.deleteProperty(obj, key);
      trigger(obj, key);
      return result;
    },
  };
  return new Proxy(target, handler);
}

// ========== 虚拟滚动中的代理思想 ==========
// 只渲染可视区域内的 DOM，对外暴露「全部数据」的接口
class VirtualList {
  constructor(container, items, itemHeight) {
    this.container = container;
    this.allItems = items;
    this.itemHeight = itemHeight;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight);
    this.startIndex = 0;

    container.addEventListener('scroll', () => this._onScroll());
    this._render();
  }

  _onScroll() {
    this.startIndex = Math.floor(this.container.scrollTop / this.itemHeight);
    this._render();
  }

  _render() {
    const end = Math.min(this.startIndex + this.visibleCount + 1, this.allItems.length);
    const visibleItems = this.allItems.slice(this.startIndex, end);
    // ... 仅渲染 visibleItems 到 DOM
  }
}

// ========== 缓存代理 ==========
function createCacheProxy(fn) {
  const cache = new Map();
  return new Proxy(fn, {
    apply(target, thisArg, args) {
      const key = JSON.stringify(args);
      if (cache.has(key)) return cache.get(key);
      const result = Reflect.apply(target, thisArg, args);
      cache.set(key, result);
      return result;
    },
  });
}

const heavyCalc = (n) => {
  console.log('计算中...');
  return n * n;
};

const cachedCalc = createCacheProxy(heavyCalc);
cachedCalc(10); // 计算中... → 100
cachedCalc(10); // 直接返回 100（无 "计算中..."）
```

---

### 1.6 工厂模式（Factory）

> **核心思想**：将对象的创建过程封装，调用者无需关心具体构造细节。

```javascript
// ========== 简单工厂 ==========
class Button {
  constructor(type) {
    this.type = type;
  }
  render() {
    return `<button class="btn-${this.type}">${this.type}</button>`;
  }
}

function createButton(type) {
  switch (type) {
    case 'primary': return new Button('primary');
    case 'danger':  return new Button('danger');
    case 'link':    return new Button('link');
    default:        return new Button('default');
  }
}

// ========== React.createElement 即工厂模式 ==========
// JSX 编译后：React.createElement(type, props, ...children)
// 根据 type 是字符串/函数/类 来创建不同的 Fiber 节点
function createElement(type, config, ...children) {
  const props = { ...config, children };
  return {
    $$typeof: Symbol.for('react.element'),
    type,
    props,
    key: config?.key ?? null,
    ref: config?.ref ?? null,
  };
}

// ========== 抽象工厂：跨平台 UI ==========
class WebUIFactory {
  createButton(text)  { return `<button>${text}</button>`; }
  createInput(placeholder) { return `<input placeholder="${placeholder}" />`; }
}

class MobileUIFactory {
  createButton(text)  { return `<View><Text>${text}</Text></View>`; }
  createInput(placeholder) { return `<TextInput placeholder="${placeholder}" />`; }
}

function getUIFactory(platform) {
  return platform === 'web' ? new WebUIFactory() : new MobileUIFactory();
}
```

---

### 1.7 适配器模式（Adapter）

> **核心思想**：将一个接口转换为客户端期望的另一个接口。

```javascript
// ========== API 兼容层 ==========
// 旧接口返回 { code: 0, result: [...] }
// 新接口返回 { code: 200, data: { list: [...], total: 100 } }

class APIAdapter {
  static normalize(response, isLegacy = false) {
    if (isLegacy) {
      return {
        success: response.code === 0,
        data: response.result || [],
        total: response.result?.length || 0,
      };
    }
    return {
      success: response.code === 200,
      data: response.data?.list || [],
      total: response.data?.total || 0,
    };
  }
}

// 业务层统一使用
async function fetchList(url, isLegacy) {
  const raw = await fetch(url).then((r) => r.json());
  return APIAdapter.normalize(raw, isLegacy);
}

// ========== 第三方库适配 ==========
// 适配 axios 和 fetch 的统一请求层
class HttpAdapter {
  constructor(engine = 'fetch') {
    this.engine = engine;
  }

  async get(url, config = {}) {
    if (this.engine === 'axios') {
      const res = await axios.get(url, config);
      return res.data;
    }
    const res = await fetch(url, config);
    return res.json();
  }

  async post(url, data, config = {}) {
    if (this.engine === 'axios') {
      const res = await axios.post(url, data, config);
      return res.data;
    }
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      ...config,
    });
    return res.json();
  }
}
```

---

### 1.8 组合模式（Composite）

> **核心思想**：将对象组合成树形结构以表示"部分—整体"关系，使得单个对象和组合对象的使用具有一致性。

```javascript
// ========== 文件/文件夹统一操作 ==========
class FileNode {
  constructor(name) {
    this.name = name;
  }
  getSize() { return this._size || 0; }
  display(indent = 0) {
    console.log(' '.repeat(indent) + this.name);
  }
}

class FolderNode {
  constructor(name) {
    this.name = name;
    this.children = [];
  }
  add(node)    { this.children.push(node); return this; }
  remove(node) { this.children = this.children.filter((c) => c !== node); }
  getSize()    { return this.children.reduce((sum, c) => sum + c.getSize(), 0); }
  display(indent = 0) {
    console.log(' '.repeat(indent) + `[${this.name}]`);
    this.children.forEach((c) => c.display(indent + 2));
  }
}

// ========== React 组件树本质就是组合模式 ==========
// <App>
//   <Header />
//   <Main>
//     <Sidebar />
//     <Content />
//   </Main>
//   <Footer />
// </App>
// React 递归处理 children，对叶子节点和容器节点统一调用 render。
```

---

### 1.9 迭代器模式（Iterator）

> **核心思想**：提供一种方法顺序访问聚合对象中的各个元素，而不暴露该对象的内部表示。

```javascript
// ========== 自定义可迭代对象 ==========
class Range {
  constructor(start, end) {
    this.start = start;
    this.end = end;
  }

  [Symbol.iterator]() {
    let current = this.start;
    const end = this.end;
    return {
      next() {
        if (current <= end) {
          return { value: current++, done: false };
        }
        return { done: true };
      },
    };
  }
}

for (const num of new Range(1, 5)) {
  console.log(num); // 1, 2, 3, 4, 5
}

console.log([...new Range(1, 3)]); // [1, 2, 3]

// ========== 生成器实现无限序列 ==========
function* fibonacci() {
  let [a, b] = [0, 1];
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

// 取前 10 个
const fib = fibonacci();
const first10 = Array.from({ length: 10 }, () => fib.next().value);
console.log(first10); // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]

// ========== DOM 树迭代器 ==========
function* walkDOM(node) {
  yield node;
  for (const child of node.children) {
    yield* walkDOM(child);
  }
}

// 使用: for (const el of walkDOM(document.body)) { ... }
```

---

### 1.10 中介者模式（Mediator）

> **核心思想**：用一个中介对象封装一系列对象的交互，使各对象不需要显式地互相引用。

```javascript
// ========== 状态管理作为中介者 ==========
class StoreMediator {
  constructor() {
    this.state = {};
    this.components = new Map();
  }

  register(name, component) {
    this.components.set(name, component);
  }

  setState(key, value, source) {
    this.state[key] = value;
    // 通知除来源以外的所有已注册组件
    for (const [name, comp] of this.components) {
      if (name !== source) {
        comp.onStateChange(key, value);
      }
    }
  }

  getState(key) {
    return this.state[key];
  }
}

// 组件无需互相引用，只和中介者通信
class SearchBox {
  constructor(mediator) {
    this.mediator = mediator;
    mediator.register('search', this);
  }
  onChange(keyword) {
    this.mediator.setState('keyword', keyword, 'search');
  }
  onStateChange(key, value) {
    if (key === 'keyword') console.log('[SearchBox] 同步关键字:', value);
  }
}

class ResultList {
  constructor(mediator) {
    this.mediator = mediator;
    mediator.register('result', this);
  }
  onStateChange(key, value) {
    if (key === 'keyword') console.log('[ResultList] 按关键字过滤:', value);
  }
}

// Redux / Vuex 本质是中介者模式的变体
```

---

## 二、架构模式

### 2.1 MVC / MVP / MVVM 对比

| 维度 | MVC | MVP | MVVM |
|------|-----|-----|------|
| **全称** | Model-View-Controller | Model-View-Presenter | Model-View-ViewModel |
| **数据流** | 双向（View ↔ Model 可直接交互） | 单向（View ↔ Presenter ↔ Model） | 双向绑定（View ↔ ViewModel） |
| **View 与 Model 关系** | View 知道 Model | 完全隔离 | 通过 ViewModel 绑定 |
| **典型代表** | Backbone.js | Android MVP | Vue.js / Angular |
| **Controller/Presenter 角色** | 路由转发、薄逻辑 | 厚逻辑、处理所有交互 | ViewModel 自动同步 |
| **测试难度** | Controller 依赖 View，较难 | Presenter 纯逻辑，易测试 | ViewModel 易测试 |

```
MVC:   User → Controller → Model → View
                  ↑___________|

MVP:   User → View → Presenter → Model
                  ↑        ↓
                  ←————————←

MVVM:  User → View ⟷ ViewModel ⟷ Model
                 (双向绑定)
```

---

### 2.2 Flux / Redux 单向数据流

```
          ┌──── Action ────┐
          │                │
          ▼                │
      Dispatcher      ←  View
          │
          ▼
        Store ──→ View(re-render)
```

**Redux 三大原则**：
1. **单一数据源**（Single Source of Truth）：整个应用只有一个 Store。
2. **State 只读**：唯一改变 State 的方式是 dispatch Action。
3. **纯函数修改**：Reducer 是纯函数 `(prevState, action) => newState`。

```javascript
// ========== 极简 Redux 实现 ==========
function createStore(reducer, initialState) {
  let state = initialState;
  let listeners = [];

  const getState = () => state;

  const dispatch = (action) => {
    state = reducer(state, action);
    listeners.forEach((fn) => fn());
    return action;
  };

  const subscribe = (fn) => {
    listeners.push(fn);
    return () => {
      listeners = listeners.filter((l) => l !== fn);
    };
  };

  // 初始化
  dispatch({ type: '@@INIT' });

  return { getState, dispatch, subscribe };
}

// 中间件机制
function applyMiddleware(...middlewares) {
  return (createStore) => (reducer, initialState) => {
    const store = createStore(reducer, initialState);
    let dispatch = store.dispatch;

    const api = {
      getState: store.getState,
      dispatch: (action) => dispatch(action),
    };

    const chain = middlewares.map((mw) => mw(api));
    dispatch = compose(...chain)(store.dispatch);

    return { ...store, dispatch };
  };
}

function compose(...fns) {
  if (fns.length === 0) return (arg) => arg;
  if (fns.length === 1) return fns[0];
  return fns.reduce((a, b) => (...args) => a(b(...args)));
}
```

---

### 2.3 组件化架构

```
应用
├── 基础组件层（Button / Input / Modal）
├── 业务组件层（UserCard / OrderTable）
├── 页面组件层（HomePage / DetailPage）
└── 布局组件层（Header / Sidebar / Footer）
```

**组件化核心原则**：
- **高内聚低耦合**：组件内部逻辑自洽，对外依赖最小化。
- **单向数据流**：props 向下，events 向上。
- **可组合性**：通过 `children` / `slots` / `render props` 实现灵活组合。
- **可复用性**：抽离通用逻辑到 Hooks / Mixins / HOC。

---

### 2.4 插件化架构

```javascript
// ========== 插件系统设计 ==========
class App {
  constructor() {
    this.hooks = {
      beforeInit: new SyncHook(),
      afterInit:  new SyncHook(),
      beforeRequest: new AsyncSeriesHook(),
      afterResponse: new AsyncSeriesHook(),
    };
    this.plugins = [];
  }

  use(plugin) {
    if (typeof plugin.install === 'function') {
      plugin.install(this);
    } else if (typeof plugin === 'function') {
      plugin(this);
    }
    this.plugins.push(plugin);
    return this; // 链式调用
  }

  async init() {
    this.hooks.beforeInit.call();
    // ... 初始化逻辑
    this.hooks.afterInit.call();
  }
}

// 插件示例
const loggerPlugin = {
  install(app) {
    app.hooks.beforeRequest.tapAsync('Logger', async (ctx) => {
      console.log(`[${new Date().toISOString()}] ${ctx.method} ${ctx.url}`);
    });
  },
};

// Webpack / Vite / Babel / ESLint 都基于插件化架构
```

---

### 2.5 DDD（领域驱动设计）在前端

| 概念 | 前端映射 |
|------|---------|
| **领域（Domain）** | 业务模块（订单、用户、商品） |
| **实体（Entity）** | 带 ID 的业务对象（User, Order） |
| **值对象（Value Object）** | 无 ID 的纯数据（Address, Money） |
| **聚合根（Aggregate Root）** | 模块入口组件/Store |
| **领域服务（Domain Service）** | 纯业务逻辑函数（calculateDiscount） |
| **应用服务（Application Service）** | 页面级 useCase / Controller |
| **仓储（Repository）** | API 层 / 数据访问层 |

```
src/
├── domains/
│   ├── order/
│   │   ├── entities/       # Order, OrderItem
│   │   ├── valueObjects/   # Money, Address
│   │   ├── services/       # calculateTotal, applyDiscount
│   │   ├── repository.ts   # API 调用
│   │   └── store.ts        # 状态管理
│   ├── user/
│   └── product/
├── application/            # 页面级编排
├── infrastructure/         # 基础设施（HTTP、Storage、Router）
└── presentation/           # UI 组件
```

---

## 三、React 设计模式

### 3.1 Compound Components（复合组件）

> 多个组件协作完成一个完整功能，通过隐式共享状态。

```jsx
// ========== Select 复合组件 ==========
const SelectContext = React.createContext();

function Select({ children, value, onChange }) {
  return (
    <SelectContext.Provider value={{ value, onChange }}>
      <div className="custom-select">{children}</div>
    </SelectContext.Provider>
  );
}

function Option({ value: optionValue, children }) {
  const { value, onChange } = React.useContext(SelectContext);
  const isSelected = value === optionValue;

  return (
    <div
      className={`option ${isSelected ? 'selected' : ''}`}
      onClick={() => onChange(optionValue)}
    >
      {children}
    </div>
  );
}

Select.Option = Option;

// ---------- 使用 ----------
function App() {
  const [value, setValue] = useState('apple');
  return (
    <Select value={value} onChange={setValue}>
      <Select.Option value="apple">苹果</Select.Option>
      <Select.Option value="banana">香蕉</Select.Option>
      <Select.Option value="cherry">樱桃</Select.Option>
    </Select>
  );
}
```

---

### 3.2 Render Props

> 通过一个值为函数的 prop 来共享代码逻辑。

```jsx
// ========== 鼠标位置追踪 ==========
function MouseTracker({ render }) {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handler = (e) => setPosition({ x: e.clientX, y: e.clientY });
    window.addEventListener('mousemove', handler);
    return () => window.removeEventListener('mousemove', handler);
  }, []);

  return render(position);
}

// 使用
<MouseTracker
  render={({ x, y }) => (
    <p>鼠标位置: ({x}, {y})</p>
  )}
/>

// ========== 通用数据获取 ==========
function DataFetcher({ url, render }) {
  const [state, setState] = useState({ loading: true, data: null, error: null });

  useEffect(() => {
    setState({ loading: true, data: null, error: null });
    fetch(url)
      .then((res) => res.json())
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((error) => setState({ loading: false, data: null, error }));
  }, [url]);

  return render(state);
}

<DataFetcher
  url="/api/users"
  render={({ loading, data, error }) => {
    if (loading) return <Spinner />;
    if (error) return <ErrorMessage error={error} />;
    return <UserList users={data} />;
  }}
/>
```

---

### 3.3 Custom Hooks（自定义 Hook）

> 当代 React 最推荐的逻辑复用方式，替代 HOC / Render Props 大部分场景。

```jsx
// ========== useDebounce ==========
function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// ========== useLocalStorage ==========
function useLocalStorage(key, initialValue) {
  const [stored, setStored] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value) => {
    const valueToStore = value instanceof Function ? value(stored) : value;
    setStored(valueToStore);
    window.localStorage.setItem(key, JSON.stringify(valueToStore));
  };

  return [stored, setValue];
}

// ========== useFetch ==========
function useFetch(url, options = {}) {
  const [state, setState] = useState({
    loading: true,
    data: null,
    error: null,
  });

  const abortRef = useRef(null);

  useEffect(() => {
    abortRef.current?.abort();
    abortRef.current = new AbortController();

    setState((prev) => ({ ...prev, loading: true }));

    fetch(url, { ...options, signal: abortRef.current.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => setState({ loading: false, data, error: null }))
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setState({ loading: false, data: null, error: err });
        }
      });

    return () => abortRef.current?.abort();
  }, [url]);

  return state;
}

// ========== useClickOutside ==========
function useClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (e) => {
      if (!ref.current || ref.current.contains(e.target)) return;
      handler(e);
    };
    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);
    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}
```

---

### 3.4 Provider Pattern

> 使用 Context 提供全局或局部共享状态，避免 props drilling。

```jsx
// ========== 主题 Provider ==========
const ThemeContext = React.createContext({
  theme: 'light',
  toggle: () => {},
});

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');

  const toggle = useCallback(() => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  const value = useMemo(() => ({ theme, toggle }), [theme, toggle]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}

// ---------- 使用 ----------
function App() {
  return (
    <ThemeProvider>
      <Header />
      <Main />
    </ThemeProvider>
  );
}

function Header() {
  const { theme, toggle } = useTheme();
  return (
    <header className={theme}>
      <button onClick={toggle}>切换主题</button>
    </header>
  );
}
```

---

### 3.5 Container / Presentational

> 将**数据逻辑**与**UI 渲染**分离。

```jsx
// ========== Presentational（纯展示） ==========
function UserCard({ name, avatar, role, onFollow }) {
  return (
    <div className="user-card">
      <img src={avatar} alt={name} />
      <h3>{name}</h3>
      <span>{role}</span>
      <button onClick={onFollow}>关注</button>
    </div>
  );
}

// ========== Container（数据逻辑） ==========
function UserCardContainer({ userId }) {
  const { data: user, loading } = useFetch(`/api/users/${userId}`);
  const [isFollowed, setIsFollowed] = useState(false);

  const handleFollow = async () => {
    await fetch(`/api/follow/${userId}`, { method: 'POST' });
    setIsFollowed(true);
  };

  if (loading) return <Skeleton />;

  return (
    <UserCard
      name={user.name}
      avatar={user.avatar}
      role={user.role}
      onFollow={handleFollow}
    />
  );
}
```

> **现代趋势**：Custom Hooks 已大量取代 Container 组件的角色。数据逻辑封装在 Hook 中，组件本身既获取数据又渲染 UI。

---

### 3.6 State Reducer Pattern

> 将组件的状态更新逻辑通过 reducer 暴露给使用者，实现高度可控。

```jsx
// ========== 可自定义状态逻辑的 Toggle ==========
function useToggle({ initialOn = false, reducer = toggleReducer } = {}) {
  const [{ on }, dispatch] = useReducer(reducer, { on: initialOn });

  const toggle = () => dispatch({ type: 'TOGGLE' });
  const setOn   = () => dispatch({ type: 'ON' });
  const setOff  = () => dispatch({ type: 'OFF' });

  return { on, toggle, setOn, setOff };
}

function toggleReducer(state, action) {
  switch (action.type) {
    case 'TOGGLE': return { on: !state.on };
    case 'ON':     return { on: true };
    case 'OFF':    return { on: false };
    default:       return state;
  }
}

// ---------- 使用者自定义 reducer ----------
function customReducer(state, action) {
  // 限制：最多只能切换 4 次
  if (action.type === 'TOGGLE' && state.count >= 4) {
    return state; // 忽略
  }
  const newState = toggleReducer(state, action);
  return action.type === 'TOGGLE'
    ? { ...newState, count: (state.count || 0) + 1 }
    : newState;
}

function App() {
  const { on, toggle } = useToggle({ reducer: customReducer });
  return <button onClick={toggle}>{on ? '开' : '关'}</button>;
}
```

---

## 四、组件设计原则（SOLID 在前端）

### 4.1 单一职责原则（SRP）

```jsx
// ❌ 职责混杂
function UserDashboard() {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [notifications, setNotifications] = useState([]);

  useEffect(() => { /* 获取用户 */ }, []);
  useEffect(() => { /* 获取订单 */ }, []);
  useEffect(() => { /* 获取通知 */ }, []);

  return (
    <div>
      {/* 用户信息渲染 */}
      {/* 订单列表渲染 */}
      {/* 通知列表渲染 */}
    </div>
  );
}

// ✅ 拆分职责
function UserDashboard() {
  return (
    <div>
      <UserProfile />
      <OrderList />
      <NotificationPanel />
    </div>
  );
}
```

### 4.2 开闭原则（OCP）

```jsx
// ❌ 每次新增类型都要修改组件
function Alert({ type, message }) {
  if (type === 'success') return <div className="green">{message}</div>;
  if (type === 'error')   return <div className="red">{message}</div>;
  if (type === 'warning') return <div className="yellow">{message}</div>;
  // 新增类型需要改这里...
}

// ✅ 对扩展开放，对修改关闭
const ALERT_STYLES = {
  success: { className: 'green', icon: '✓' },
  error:   { className: 'red',   icon: '✗' },
  warning: { className: 'yellow', icon: '⚠' },
};

function Alert({ type, message }) {
  const style = ALERT_STYLES[type] || ALERT_STYLES.success;
  return (
    <div className={style.className}>
      <span>{style.icon}</span> {message}
    </div>
  );
}

// 新增类型只需扩展配置
ALERT_STYLES.info = { className: 'blue', icon: 'ℹ' };
```

### 4.3 里氏替换原则（LSP）

```jsx
// 子组件应能替换父组件而不影响正确性
// ✅ 所有 Button 变体共享同一 Props 接口
interface ButtonProps {
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}

function PrimaryButton(props: ButtonProps) {
  return <button className="btn-primary" {...props} />;
}

function DangerButton(props: ButtonProps) {
  return <button className="btn-danger" {...props} />;
}

// 可在任何需要 Button 的地方互换使用
function Toolbar({ ActionButton = PrimaryButton }) {
  return <ActionButton onClick={handleSave}>保存</ActionButton>;
}
```

### 4.4 接口隔离原则（ISP）

```jsx
// ❌ Props 过于庞大
interface UserComponentProps {
  name: string;
  email: string;
  avatar: string;
  orders: Order[];
  notifications: Notification[];
  onFollow: () => void;
  onMessage: () => void;
  onBlock: () => void;
}

// ✅ 按职责拆分 Props
interface UserBasicProps {
  name: string;
  email: string;
  avatar: string;
}

interface UserActionsProps {
  onFollow: () => void;
  onMessage: () => void;
}

function UserAvatar({ name, avatar }: Pick<UserBasicProps, 'name' | 'avatar'>) {
  return <img src={avatar} alt={name} />;
}
```

### 4.5 依赖倒置原则（DIP）

```jsx
// ❌ 高层模块直接依赖低层实现
function UserList() {
  useEffect(() => {
    axios.get('/api/users').then(/* ... */); // 直接依赖 axios
  }, []);
}

// ✅ 依赖抽象接口
// api.ts
export interface IHttpClient {
  get<T>(url: string): Promise<T>;
  post<T>(url: string, data: unknown): Promise<T>;
}

// 注入实现
const HttpContext = React.createContext<IHttpClient>(null!);

function UserList() {
  const http = useContext(HttpContext);
  useEffect(() => {
    http.get('/api/users').then(/* ... */);
  }, [http]);
}

// 测试时注入 mock
<HttpContext.Provider value={mockHttp}>
  <UserList />
</HttpContext.Provider>
```

### 4.6 Props 设计最佳实践

| 原则 | 说明 | 示例 |
|------|------|------|
| **最小必要** | 只暴露必需的 props | 不要把整个 `user` 对象传入只需要 `name` 的组件 |
| **合理默认值** | 减少调用方负担 | `size = 'medium'` |
| **语义化命名** | props 名应体现意图 | `onSubmit` 而非 `handler` |
| **受控 + 非受控兼容** | 同时支持两种模式 | `value` + `defaultValue` |
| **回调约定** | `on` + 动词 | `onChange`, `onSelect`, `onClose` |
| **枚举优于布尔** | 避免多个互斥 boolean | `variant="primary"` 而非 `isPrimary` |
| **组合优于配置** | children > renderXxx > config | `<Tabs><Tab>` 而非 `<Tabs items={[...]}` |

### 4.7 可测试性设计

```javascript
// ========== 纯函数易测试 ==========
// utils/price.js
export function calculateTotal(items, discount = 0) {
  const subtotal = items.reduce((sum, item) => sum + item.price * item.qty, 0);
  return Math.max(0, subtotal * (1 - discount));
}

// __tests__/price.test.js
describe('calculateTotal', () => {
  it('无折扣', () => {
    expect(calculateTotal([{ price: 10, qty: 2 }])).toBe(20);
  });
  it('八折', () => {
    expect(calculateTotal([{ price: 100, qty: 1 }], 0.2)).toBe(80);
  });
  it('空列表', () => {
    expect(calculateTotal([])).toBe(0);
  });
});

// ========== 依赖注入易 Mock ==========
// 组件接收 fetcher 函数，测试时替换为 mock
function ProductList({ fetchProducts = defaultFetch }) {
  const [products, setProducts] = useState([]);
  useEffect(() => {
    fetchProducts().then(setProducts);
  }, [fetchProducts]);
  return (
    <ul>
      {products.map((p) => <li key={p.id}>{p.name}</li>)}
    </ul>
  );
}

// 测试
const mockFetch = () => Promise.resolve([{ id: 1, name: '测试商品' }]);
render(<ProductList fetchProducts={mockFetch} />);
```

---

## 五、高频面试题精选（10+ 道）

### 题目 1：手写发布订阅模式（EventEmitter）

> 见 1.2 节完整实现。要求：`on / off / once / emit`，注意 `once` 的 `_original` 引用、`emit` 时的数组拷贝。

---

### 题目 2：单例模式有哪些应用场景？ES Module 为什么天然是单例？

**答**：
- 场景：全局弹窗、Vuex/Redux Store、日志系统、WebSocket 连接管理。
- ES Module 只会在首次 `import` 时执行并缓存导出值，后续 `import` 直接读缓存，等价于单例。

---

### 题目 3：观察者模式和发布订阅的区别？

**答**：

| 维度 | 观察者模式 | 发布订阅模式 |
|------|-----------|-------------|
| 耦合度 | Subject 直接持有 Observer 引用 | 通过事件中心解耦，双方互不感知 |
| 通信方式 | 同步调用 `observer.update()` | 可异步，通过事件名匹配 |
| 前端例子 | `Object.defineProperty` 的 setter | EventBus、Node.js EventEmitter |

---

### 题目 4：手写一个简易 Redux（createStore）

> 见 2.2 节实现。关键：`getState`、`dispatch`（调用 reducer 并通知 listeners）、`subscribe`（返回 unsubscribe）。

---

### 题目 5：策略模式如何优化大量 if/else？

**答**：
1. 把每个分支逻辑封装为一个策略函数。
2. 用 Map/对象映射 `strategyName → handler`。
3. 调用时 `strategies[name](params)`，新增策略只需添加映射，无需修改调用方。

```javascript
// 优化前
function getPrice(userType, price) {
  if (userType === 'vip')      return price * 0.8;
  if (userType === 'svip')     return price * 0.6;
  if (userType === 'employee') return price * 0.5;
  return price;
}

// 优化后
const priceStrategies = {
  vip:      (price) => price * 0.8,
  svip:     (price) => price * 0.6,
  employee: (price) => price * 0.5,
  default:  (price) => price,
};

function getPrice(userType, price) {
  return (priceStrategies[userType] || priceStrategies.default)(price);
}
```

---

### 题目 6：React 中 HOC、Render Props、Custom Hooks 的对比和选择？

| 维度 | HOC | Render Props | Custom Hooks |
|------|-----|-------------|--------------|
| **形式** | 函数包裹组件 | 组件接收 render 函数 | 函数调用 |
| **类型推断** | 较难（props 来源不透明） | 一般 | 最好 |
| **嵌套地狱** | 易出现多层包裹 | 回调嵌套 | 无嵌套 |
| **调试** | 组件名层层包裹 | 尚可 | 清晰 |
| **推荐场景** | 需要操作生命周期/Props 注入 | 需要动态决定渲染内容 | **默认首选** |

> 现代 React 项目优先 Custom Hooks，HOC 用于需要包裹组件的场景（如路由守卫），Render Props 几乎被 Hooks 替代。

---

### 题目 7：MVVM 的双向绑定原理？

**答**：
- **Vue 2**：`Object.defineProperty` 劫持 getter/setter → 依赖收集（Dep + Watcher）→ 视图更新。
- **Vue 3**：`Proxy` 代理 → `ReactiveEffect` → 触发 `trigger` → 调度更新。
- **Angular**：脏检查（Zone.js 拦截异步事件 → 触发 `$digest` 循环对比）。

核心流程：`数据变化 → 拦截 → 通知依赖 → 更新 DOM`。

---

### 题目 8：什么是 Compound Components？解决什么问题？

**答**：
- 多个子组件通过共享的 Context 隐式通信，对外提供统一的 API。
- 解决**配置式组件 props 过多**的问题，让使用者以声明式的 JSX 结构来组合功能。
- 典型例子：`<Select><Select.Option>` / `<Tabs><Tab>` / `<Accordion><Panel>`。

---

### 题目 9：如何设计一个可扩展的组件库？

**答**：
1. **分层架构**：原子组件 → 分子组件 → 有机组件（Atomic Design）。
2. **样式方案**：CSS Variables + Design Token，支持主题切换。
3. **TypeScript**：严格类型约束，导出完整类型定义。
4. **按需加载**：Tree-shaking 友好（ESM 导出），支持 `babel-plugin-import`。
5. **测试策略**：单元测试（Jest + Testing Library）+ 视觉回归（Storybook + Chromatic）。
6. **文档驱动**：每个组件有 Playground + API 文档 + 最佳实践。
7. **版本管理**：遵循 SemVer，CHANGELOG 自动生成。

---

### 题目 10：代理模式在前端有哪些应用？

**答**：
- **Vue 3 响应式**：`Proxy` 拦截读写实现依赖收集与触发更新。
- **虚拟滚动**：代理全量数据列表，实际只渲染可视区域。
- **缓存代理**：对昂贵计算/API 请求结果做缓存。
- **图片懒加载**：先加载占位图，进入可视区再替换真实 src。
- **Axios 拦截器**：在请求/响应前后插入统一逻辑（本质是代理）。
- **ES Proxy 验证**：用 `set` trap 做属性赋值校验。

---

### 题目 11：MVC/MVP/MVVM 的核心区别？前端框架分别属于哪种？

**答**（见 2.1 节对比表）：
- **MVC**：View 可直接访问 Model，Controller 薄 → Backbone。
- **MVP**：View 与 Model 完全隔离，Presenter 厚 → 传统 Android。
- **MVVM**：ViewModel 通过数据绑定自动同步 View 与 Model → Vue / Angular。
- **React** 更接近 **View 层库 + 单向数据流（Flux）**，非典型 MVC/MVVM。

---

### 题目 12：装饰器模式和代理模式有什么区别？

**答**：

| 维度 | 装饰器 | 代理 |
|------|--------|------|
| **意图** | 增强/扩展功能 | 控制访问 |
| **对象关系** | 多层嵌套包装 | 一对一替代 |
| **生命周期** | 动态组合 | 通常在创建时确定 |
| **前端举例** | HOC、AOP 日志 | Proxy 响应式、缓存代理 |

---

### 题目 13：如何用迭代器模式实现一个树结构的深度优先遍历？

```javascript
class TreeNode {
  constructor(value, children = []) {
    this.value = value;
    this.children = children;
  }

  // 深度优先
  *[Symbol.iterator]() {
    yield this.value;
    for (const child of this.children) {
      yield* child;
    }
  }
}

const tree = new TreeNode('root', [
  new TreeNode('A', [
    new TreeNode('A1'),
    new TreeNode('A2'),
  ]),
  new TreeNode('B', [
    new TreeNode('B1'),
  ]),
]);

console.log([...tree]); // ['root', 'A', 'A1', 'A2', 'B', 'B1']
```

---

### 题目 14：中介者模式和发布订阅模式有什么区别？

**答**：
- **中介者**：各组件显式注册到中介者，中介者了解每个组件的存在，负责**编排协调**。
- **发布订阅**：发布者和订阅者互不知道对方存在，只通过**事件名**通信，更松散。
- 前端状态管理（Redux/Vuex）兼具两者特征：Store 既是中介者（了解所有 reducer），也是事件中心（dispatch action）。

---

## 六、设计模式选择速查表

| 场景 | 推荐模式 | 备注 |
|------|---------|------|
| 全局唯一实例 | 单例 | Store、弹窗、WebSocket |
| 组件间通信 | 发布订阅 / 中介者 | EventBus / Store |
| 消除 if/else | 策略 | 表单校验、价格策略 |
| 增强组件能力 | 装饰器 | HOC、日志、权限 |
| 控制访问 | 代理 | 响应式、缓存、懒加载 |
| 对象创建封装 | 工厂 | createElement、跨平台 UI |
| 接口不兼容 | 适配器 | API 版本兼容、三方库封装 |
| 树形结构操作 | 组合 | 组件树、文件系统 |
| 遍历集合 | 迭代器 | 自定义序列、Tree Walker |
| 状态逻辑复用 | Custom Hook | 替代 HOC / Render Props |
| 复杂组件 API | Compound Components | Select、Tabs、Accordion |
| 外部控制内部状态 | State Reducer | 高度可定制组件 |

---

## 七、总结与学习路线

```
入门期：理解单例 → 观察者 → 策略 → 工厂
           ↓
进阶期：装饰器 → 代理 → 适配器 → 组合 → 迭代器
           ↓
框架期：Compound Components → Render Props → Custom Hooks
           ↓
架构期：MVC/MVVM 对比 → Flux/Redux → 插件化 → DDD
           ↓
高级期：SOLID 原则 → 可测试性设计 → 组件库架构
```

**面试建议**：
1. 手写能力：`EventEmitter`、`createStore`、`策略模式优化 if/else` 必须滚瓜烂熟。
2. 模式识别：能说出所用框架/库背后的设计模式（Vue → 观察者 + 代理、React → 工厂 + 组合）。
3. 取舍能力：不是所有场景都需要设计模式，过度设计比没有设计更糟糕。
4. SOLID 原则：结合实际组件设计来阐述，不要背概念。

---

> **下一章推荐**：TypeScript 高级类型与类型体操 / 前端工程化与构建工具

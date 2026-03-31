# React面试指南

## 一、React基础概念

### 1.1 JSX本质

> 面试题：JSX是什么？它的本质是什么？

JSX（JavaScript XML）是JavaScript的一种语法扩展，它允许我们在JavaScript代码中编写类似HTML的标记语言。JSX并不是一种新的语言，而是一种语法糖，最终会被编译工具（如Babel）转换为标准的JavaScript函数调用。

**JSX的本质**是`React.createElement(type, props, ...children)`的调用。每一段JSX代码在编译后都会生成一个`React.createElement`调用，该函数返回一个普通的JavaScript对象，这个对象就是所谓的虚拟DOM（React Element）。

**React 17+的JSX Transform**：从React 17开始，引入了全新的JSX转换机制。在新的转换方式下，编译器会自动从`react/jsx-runtime`模块导入辅助函数，开发者不再需要在每个使用JSX的文件中手动`import React from 'react'`。这不仅减少了样板代码，还略微减小了打包体积。

**代码示例——JSX编译前后对比：**

编译前的JSX写法：

```jsx
function App() {
  return (
    <div className="container">
      <h1>Hello, React!</h1>
      <p>This is a paragraph.</p>
    </div>
  );
}
```

经过Babel编译后（React 16及之前的经典模式）：

```javascript
function App() {
  return React.createElement(
    'div',
    { className: 'container' },
    React.createElement('h1', null, 'Hello, React!'),
    React.createElement('p', null, 'This is a paragraph.')
  );
}
```

React 17+新JSX Transform编译后：

```javascript
import { jsx as _jsx, jsxs as _jsxs } from 'react/jsx-runtime';

function App() {
  return _jsxs('div', {
    className: 'container',
    children: [
      _jsx('h1', { children: 'Hello, React!' }),
      _jsx('p', { children: 'This is a paragraph.' }),
    ],
  });
}
```

`React.createElement`返回的对象结构大致如下：

```javascript
{
  $$typeof: Symbol(react.element),
  type: 'div',
  key: null,
  ref: null,
  props: {
    className: 'container',
    children: [
      { type: 'h1', props: { children: 'Hello, React!' } },
      { type: 'p', props: { children: 'This is a paragraph.' } }
    ]
  }
}
```

需要注意的关键点：
- JSX中的`className`对应HTML的`class`属性，`htmlFor`对应`for`属性
- JSX表达式使用`{}`包裹JavaScript表达式
- JSX必须有一个根元素，或使用Fragment（`<></>`）
- JSX中的注释使用`{/* 注释内容 */}`
- JSX防注入攻击：React DOM在渲染之前会对嵌入的值进行转义，可以有效防止XSS攻击

---

### 1.2 虚拟DOM与Diff算法

> 面试题：React的Diff算法是怎么工作的？

**虚拟DOM（Virtual DOM）** 是一种用轻量级JavaScript对象来描述真实DOM结构的编程概念。每次状态更新时，React会创建一棵新的虚拟DOM树，然后与旧树进行比较（Diff），计算出最小的DOM操作集合，最终批量更新到真实DOM上。这种方式避免了直接操作真实DOM带来的高昂性能开销。

虚拟DOM的工作流程：
1. 状态变化触发重新渲染
2. 生成新的虚拟DOM树
3. 新旧虚拟DOM树进行Diff比较
4. 计算出最小变更补丁（Patch）
5. 批量应用补丁到真实DOM

**Diff算法的三个核心策略假设：**

**策略一：Tree Diff（树级别比较）**

React对虚拟DOM树进行逐层比较，只比较同一层级的节点。如果一个节点在旧树的A层级，在新树中移动到了B层级，React不会尝试复用它，而是直接删除旧节点并在新位置创建新节点。这个策略将比较的时间复杂度从O(n³)降低到了O(n)。

在实际开发中，跨层级的DOM移动操作是极其罕见的，因此这个假设在绝大多数场景下都是合理的。

**策略二：Component Diff（组件级别比较）**

- 如果两个组件是相同类型（如都是`<UserCard>`），React会递归比较它们的子树
- 如果两个组件类型不同（如`<UserCard>`变成了`<ProductCard>`），React会直接销毁旧组件及其整个子树，然后创建新组件和新子树
- 开发者可以通过`shouldComponentUpdate`或`React.memo`来手动控制是否需要更新

**策略三：Element Diff（同层子元素比较）**

当同一层级有多个子节点时，React通过`key`属性来标识每个节点的身份。基于key，React可以高效地判断节点是新增、删除还是移动的。

具体操作类型：
- **插入（INSERT_MARKUP）**：新节点不在旧集合中，创建新节点并插入
- **移动（MOVE_EXISTING）**：节点在新旧集合中都存在，但位置发生了变化
- **删除（REMOVE_NODE）**：旧节点不在新集合中，或者同key节点类型不同

移动算法的核心逻辑：React维护一个`lastIndex`变量（初始为0），遍历新集合中的每个节点，在旧集合中查找对应key的节点。如果旧节点的索引小于`lastIndex`，则该节点需要移动；否则更新`lastIndex`为旧节点的索引值。

这也是为什么使用数组索引作为key在列表顺序变化时会产生问题——因为索引不能唯一标识元素的身份，可能导致不必要的重渲染甚至UI错误。

---

### 1.3 React Fiber架构

> 面试题：什么是Fiber？为什么React要引入Fiber？

**Fiber的诞生背景**

在React 15及之前的版本中，React使用递归方式（Stack Reconciler）来处理虚拟DOM的比较和更新。这种递归调用一旦开始就无法中断，如果组件树非常庞大，整个渲染过程可能占用主线程很长时间（超过16ms），导致页面卡顿、动画掉帧、用户交互无响应等问题。

Fiber架构就是为了解决这个问题而诞生的。

**Fiber节点的链表结构**

每个Fiber节点是一个JavaScript对象，包含以下关键指针：
- `child`：指向第一个子节点
- `sibling`：指向下一个兄弟节点
- `return`：指向父节点

这种链表结构替代了之前的树形递归结构，使得遍历过程可以在任意节点暂停和恢复。

```javascript
// Fiber节点的核心结构（简化版）
{
  tag: FunctionComponent | ClassComponent | HostComponent,
  type: 'div' | App | Button,       // 组件类型
  key: null | string,                // 唯一标识
  stateNode: DOM节点 | 组件实例,      // 对应的真实节点
  child: Fiber | null,               // 第一个子Fiber
  sibling: Fiber | null,             // 下一个兄弟Fiber
  return: Fiber | null,              // 父Fiber
  pendingProps: Object,              // 新的props
  memoizedProps: Object,             // 上次渲染的props
  memoizedState: Object,             // 上次渲染的state
  updateQueue: UpdateQueue,          // 更新队列
  flags: Placement | Update | Deletion, // 副作用标记
  lanes: Lane,                       // 优先级
  alternate: Fiber | null,           // 双缓冲对应的Fiber
}
```

**时间切片（Time Slicing）**

Fiber架构将渲染工作拆分成多个小的工作单元（Unit of Work）。每个工作单元处理一个Fiber节点。React利用`requestIdleCallback`的思想（实际使用`MessageChannel`实现），在每帧中预留约5ms的时间来执行渲染工作。当时间片用完时，React会将控制权交还给浏览器，让浏览器处理用户输入、动画等高优先级任务，然后在下一个空闲时间继续未完成的工作。

**优先级调度（Lane模型）**

React 18引入了Lane模型来管理更新优先级。每个Lane是一个32位二进制数中的一个或多个位，不同的Lane代表不同的优先级级别：

| 优先级 | Lane | 说明 |
|--------|------|------|
| 同步（SyncLane） | 最高 | 用户输入、点击等直接交互 |
| 输入连续（InputContinuousLane） | 高 | 拖拽、滚动等连续输入 |
| 默认（DefaultLane） | 中 | 网络请求回调、setTimeout |
| 过渡（TransitionLane） | 低 | useTransition标记的更新 |
| 空闲（IdleLane） | 最低 | 离屏渲染、预加载 |

**双缓冲机制（Double Buffering）**

React同时维护两棵Fiber树：
- **current tree**：当前屏幕上展示的内容对应的Fiber树
- **workInProgress tree**：正在构建中的新Fiber树

当workInProgress树构建完成并提交后，它就变成了新的current树。这种机制避免了在构建过程中出现不完整的UI状态。

**可中断的两阶段渲染**

- **Render阶段（可中断）**：遍历Fiber树，为每个节点执行beginWork和completeWork，计算需要变更的内容，标记副作用（flags）。这个阶段可以被更高优先级的任务打断
- **Commit阶段（不可中断）**：将Render阶段计算出的变更同步应用到真实DOM上。分为三个子阶段：Before Mutation（执行getSnapshotBeforeUpdate）→ Mutation（执行DOM操作）→ Layout（执行componentDidMount/Update、useLayoutEffect）

---

## 二、组件与生命周期

### 2.1 类组件生命周期

> 面试题：React组件的生命周期有哪些？各阶段分别做了什么？

React类组件的生命周期分为三个主要阶段：挂载（Mount）、更新（Update）和卸载（Unmount），以及错误处理阶段。

**挂载阶段（Mount）：**

```
constructor(props)
  → static getDerivedStateFromProps(props, state)
  → render()
  → componentDidMount()
```

- `constructor`：初始化state、绑定事件处理方法。注意不要在constructor中调用setState
- `getDerivedStateFromProps`：静态方法，根据props派生state。每次render前都会调用。返回对象来更新state，返回null不更新
- `render`：纯函数，返回JSX。不能在render中执行副作用操作
- `componentDidMount`：组件挂载到DOM后调用。适合发起网络请求、添加订阅、操作DOM

**更新阶段（Update）：**

```
static getDerivedStateFromProps(props, state)
  → shouldComponentUpdate(nextProps, nextState)
  → render()
  → getSnapshotBeforeUpdate(prevProps, prevState)
  → componentDidUpdate(prevProps, prevState, snapshot)
```

- `shouldComponentUpdate`：返回布尔值决定是否重新渲染。是性能优化的关键钩子。PureComponent自动进行浅比较
- `getSnapshotBeforeUpdate`：在DOM更新前捕获信息（如滚动位置），返回值作为componentDidUpdate的第三个参数
- `componentDidUpdate`：更新后调用。可以在此进行DOM操作或网络请求（注意要加条件判断避免死循环）

**卸载阶段（Unmount）：**

```
componentWillUnmount()
```

- `componentWillUnmount`：组件从DOM移除前调用。执行清理工作：取消网络请求、清除定时器、移除事件监听、取消订阅

**错误处理（Error Boundary）：**

```
static getDerivedStateFromError(error)
componentDidCatch(error, errorInfo)
```

- `getDerivedStateFromError`：在后代组件抛出错误后调用，更新state以显示降级UI
- `componentDidCatch`：在后代组件抛出错误后调用，用于记录错误日志

```javascript
class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo.componentStack);
    // 上报错误到监控服务
    reportError(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <h1>页面出错了，请稍后重试</h1>;
    }
    return this.props.children;
  }
}
```

**已废弃的生命周期方法（React 16.3+标记为UNSAFE）：**
- `UNSAFE_componentWillMount`
- `UNSAFE_componentWillReceiveProps`
- `UNSAFE_componentWillUpdate`

这些方法在Fiber架构下可能被多次调用，因此被标记为不安全并逐步废弃。

---

### 2.2 函数组件与Hooks

> 面试题：函数组件和类组件有什么区别？

函数组件本质上是一个接收props并返回JSX的纯函数。它没有自己的生命周期方法和实例（this），但通过Hooks可以实现类组件的所有功能。

**函数组件相比类组件的优势：**

1. **更简洁的代码**：没有class语法、constructor、this绑定等样板代码
2. **更好的逻辑复用**：自定义Hook可以轻松抽取和共享逻辑，不需要HOC或render props
3. **避免this指向问题**：不存在this绑定的困扰
4. **更好的Tree Shaking**：函数组件更容易被打包工具优化
5. **与Fiber架构天然契合**：函数组件的调用方式更适合可中断的渲染机制

**Hooks模拟生命周期的对应关系：**

| 类组件生命周期 | Hooks等效方式 |
|--------------|-------------|
| constructor | useState初始化state |
| componentDidMount | useEffect(() => {}, []) |
| componentDidUpdate | useEffect(() => {}, [deps]) |
| componentWillUnmount | useEffect(() => { return cleanup }, []) |
| shouldComponentUpdate | React.memo + useMemo |
| getDerivedStateFromProps | 在渲染期间直接根据props更新state |

---

## 三、Hooks详解

### 3.1 useState

> 面试题：useState的更新是同步还是异步的？

`useState`是React中最基础的Hook，用于在函数组件中管理状态。

**基本用法：**

```javascript
const [state, setState] = useState(initialValue);

// 直接更新
setState(newValue);

// 函数式更新（推荐在依赖前一个状态时使用）
setState(prevState => prevState + 1);

// 惰性初始化（初始值需要复杂计算时使用）
const [state, setState] = useState(() => {
  return expensiveComputation(props);
});
```

**关于同步和异步的回答：**

在React 18之前：
- 在React合成事件和生命周期中，setState是"异步"的（实际是批量更新，不是真正的异步）
- 在setTimeout、原生事件、Promise回调中，setState是"同步"的

在React 18之后（引入Automatic Batching）：
- **所有场景下setState都是批量处理的**，包括Promise、setTimeout、原生事件处理函数等
- 如果需要强制同步更新，可以使用`flushSync`

```javascript
import { flushSync } from 'react-dom';

function handleClick() {
  flushSync(() => {
    setCount(c => c + 1);
  });
  // DOM已更新
  console.log(document.getElementById('count').textContent); // 最新值
}
```

**批量更新机制（React 18 Automatic Batching）：**

```javascript
function handleClick() {
  setCount(c => c + 1);  // 不会立即触发渲染
  setFlag(f => !f);       // 不会立即触发渲染
  // React会将以上更新合并，只触发一次重新渲染
}

// React 18之前，setTimeout中不会批量更新
// React 18之后，setTimeout中也会自动批量更新
setTimeout(() => {
  setCount(c => c + 1);
  setFlag(f => !f);
  // React 18: 只触发一次渲染
}, 1000);
```

**闭包陷阱及解决方案：**

闭包陷阱是使用useState时最常见的问题。由于函数组件每次渲染都会创建一个新的闭包环境，如果在异步回调中引用state，拿到的可能是过期的值。

```javascript
const [count, setCount] = useState(0);

// 闭包陷阱示例
useEffect(() => {
  const timer = setInterval(() => {
    console.log(count); // 始终为0，因为闭包捕获的是初始值
    setCount(c => c + 1); // 函数式更新解决
  }, 1000);
  return () => clearInterval(timer);
}, []);
```

**解决闭包陷阱的方式：**

1. **函数式更新**：`setCount(c => c + 1)`，不依赖外部的count变量
2. **useRef存储最新值**：

```javascript
const countRef = useRef(count);
countRef.current = count; // 每次渲染更新ref

useEffect(() => {
  const timer = setInterval(() => {
    console.log(countRef.current); // 始终是最新值
  }, 1000);
  return () => clearInterval(timer);
}, []);
```

3. **正确设置依赖数组**：将state添加到useEffect的依赖中

---

### 3.2 useEffect

> 面试题：useEffect和useLayoutEffect有什么区别？

`useEffect`用于处理函数组件中的副作用，如数据获取、订阅、手动修改DOM等。

**副作用管理与依赖数组：**

```javascript
// 1. 每次渲染后都执行（无依赖数组）
useEffect(() => {
  console.log('每次render后都会执行');
});

// 2. 仅在挂载时执行（空依赖数组）
useEffect(() => {
  console.log('仅在mount时执行');
  return () => {
    console.log('仅在unmount时执行清理');
  };
}, []);

// 3. 依赖变化时执行
useEffect(() => {
  console.log(`userId变为: ${userId}`);
  fetchUserData(userId);
  return () => {
    // 清理上一次effect（在下一次effect执行前或组件卸载时调用）
    cancelRequest();
  };
}, [userId]);
```

**清理函数的执行时机：**
- 组件卸载时执行清理
- 在依赖变化、重新执行effect之前，先执行上一次的清理函数
- 清理函数用于取消订阅、清除定时器、取消网络请求等

**useEffect vs useLayoutEffect：**

| 对比项 | useEffect | useLayoutEffect |
|-------|-----------|------------------|
| 执行时机 | 异步执行，DOM更新后、浏览器绘制后 | 同步执行，DOM变更后、浏览器绘制前 |
| 是否阻塞渲染 | 不阻塞，用户可以先看到更新后的UI | 阻塞，在effect执行完毕后才绘制 |
| 适用场景 | 数据获取、事件订阅、日志记录等 | DOM测量、强制同步布局、防止闪烁 |
| 性能影响 | 对性能影响小 | 可能导致延迟绘制，应谨慎使用 |

```javascript
// useLayoutEffect的典型使用场景——防止UI闪烁
function Tooltip({ targetRef, content }) {
  const [position, setPosition] = useState({ top: 0, left: 0 });

  // 使用useLayoutEffect测量DOM并设置位置
  // 如果用useEffect，用户可能先看到tooltip在错误位置然后跳到正确位置
  useLayoutEffect(() => {
    const rect = targetRef.current.getBoundingClientRect();
    setPosition({ top: rect.bottom + 8, left: rect.left });
  }, [targetRef]);

  return (
    <div style={{ position: 'fixed', ...position }}>
      {content}
    </div>
  );
}
```

---

### 3.3 useContext

> 面试题：useContext的性能问题如何解决？

`useContext`用于消费React Context，实现跨组件的数据传递，避免prop drilling（逐层传递props）。

**基本用法：**

```javascript
// 1. 创建Context
const ThemeContext = React.createContext('light');

// 2. 提供Context
function App() {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <Layout />
    </ThemeContext.Provider>
  );
}

// 3. 消费Context
function ThemedButton() {
  const { theme, setTheme } = useContext(ThemeContext);
  return (
    <button className={theme} onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
      当前主题: {theme}
    </button>
  );
}
```

**性能问题：** 当Provider的value发生变化时，所有消费该Context的组件都会重新渲染，即使它们只用了value中的一部分数据。

**优化方案：**

1. **拆分Context**：将不同的数据放入不同的Context，减少不必要的更新范围

```javascript
const ThemeContext = React.createContext('light');
const UserContext = React.createContext(null);
// 组件只订阅自己需要的Context
```

2. **useMemo包裹value**：避免Provider每次渲染都创建新的value对象

```javascript
function App() {
  const [theme, setTheme] = useState('light');
  const value = useMemo(() => ({ theme, setTheme }), [theme]);
  return (
    <ThemeContext.Provider value={value}>
      <Layout />
    </ThemeContext.Provider>
  );
}
```

3. **使用use-context-selector**：只在选择的值变化时才重新渲染

```javascript
import { createContext, useContextSelector } from 'use-context-selector';

const AppContext = createContext(null);

function UserName() {
  // 只在name变化时重新渲染，age变化不会触发
  const name = useContextSelector(AppContext, ctx => ctx.name);
  return <span>{name}</span>;
}
```

---

### 3.4 useReducer

> 面试题：useReducer和useState分别适合什么场景？

`useReducer`是useState的替代方案，适合管理包含复杂逻辑的状态。它采用dispatch + reducer模式，类似于Redux。

```javascript
const initialState = { count: 0, step: 1 };

function reducer(state, action) {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + state.step };
    case 'decrement':
      return { ...state, count: state.count - state.step };
    case 'setStep':
      return { ...state, step: action.payload };
    case 'reset':
      return initialState;
    default:
      throw new Error(`Unknown action type: ${action.type}`);
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, initialState);

  return (
    <div>
      <p>Count: {state.count} (step: {state.step})</p>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
      <button onClick={() => dispatch({ type: 'setStep', payload: 5 })}>Step=5</button>
      <button onClick={() => dispatch({ type: 'reset' })}>Reset</button>
    </div>
  );
}
```

**useReducer vs useState对比：**

| 场景 | useState | useReducer |
|------|----------|------------|
| 简单状态（布尔/数字/字符串） | 推荐 | 不必要 |
| 多个相关联的状态 | 多个useState调用 | 推荐，统一管理 |
| 复杂的更新逻辑 | setState回调复杂 | 推荐，逻辑集中在reducer |
| 深层子组件需要更新状态 | 需要传递多个setter | dispatch稳定引用，配合Context |
| 测试 | 难以单独测试逻辑 | reducer是纯函数，易于测试 |

---

### 3.5 useMemo

> 面试题：useMemo和useCallback有什么区别？

`useMemo`用于缓存计算结果，仅在依赖项变化时才重新计算。

```javascript
const memoizedValue = useMemo(() => {
  return expensiveComputation(a, b);
}, [a, b]);
```

**使用场景：**

1. **避免昂贵计算重复执行：**

```javascript
function ProductList({ products, filter }) {
  // 只有products或filter变化时才重新过滤和排序
  const filteredProducts = useMemo(() => {
    return products
      .filter(p => p.category === filter)
      .sort((a, b) => b.price - a.price);
  }, [products, filter]);

  return filteredProducts.map(p => <ProductCard key={p.id} product={p} />);
}
```

2. **稳定引用，配合React.memo：**

```javascript
function Parent({ items }) {
  // 如果不用useMemo，每次Parent渲染都会创建新的数组引用
  const sortedItems = useMemo(() => [...items].sort(), [items]);
  return <MemoizedChild items={sortedItems} />;
}
```

**不要滥用useMemo的情况：**
- 简单的基本类型计算（如数字相加）不需要memo，memo本身有内存开销和比较开销
- 如果组件渲染很快，缓存的收益可能不如memo的开销大
- 依赖项频繁变化导致memo几乎每次都重新计算

---

### 3.6 useCallback

`useCallback`用于缓存函数引用，仅在依赖项变化时才返回新的函数。

```javascript
const memoizedCallback = useCallback(() => {
  doSomething(a, b);
}, [a, b]);
```

**本质上，useCallback(fn, deps) 等价于 useMemo(() => fn, deps)。**

**典型使用场景——配合React.memo防止子组件不必要的重渲染：**

```javascript
const MemoizedChild = React.memo(function Child({ onClick, label }) {
  console.log('Child render:', label);
  return <button onClick={onClick}>{label}</button>;
});

function Parent() {
  const [count, setCount] = useState(0);
  const [text, setText] = useState('');

  // 如果不用useCallback，每次Parent渲染都创建新的函数引用
  // 导致MemoizedChild即使props.label没变也会重新渲染
  const handleClick = useCallback(() => {
    setCount(c => c + 1);
  }, []);

  return (
    <div>
      <input value={text} onChange={e => setText(e.target.value)} />
      <p>Count: {count}</p>
      <MemoizedChild onClick={handleClick} label="Click me" />
    </div>
  );
}
```

---

### 3.7 useRef

`useRef`返回一个可变的ref对象，其`.current`属性被初始化为传入的参数。该对象在组件的整个生命周期内保持不变。

**用途一：DOM引用**

```javascript
function TextInput() {
  const inputRef = useRef(null);

  const focusInput = () => {
    inputRef.current.focus();
  };

  return (
    <>
      <input ref={inputRef} type="text" />
      <button onClick={focusInput}>聚焦输入框</button>
    </>
  );
}
```

**用途二：存储可变值（不触发重渲染）**

```javascript
function Timer() {
  const [count, setCount] = useState(0);
  const timerIdRef = useRef(null);

  const startTimer = () => {
    timerIdRef.current = setInterval(() => {
      setCount(c => c + 1);
    }, 1000);
  };

  const stopTimer = () => {
    clearInterval(timerIdRef.current);
  };

  return (
    <div>
      <p>{count}</p>
      <button onClick={startTimer}>Start</button>
      <button onClick={stopTimer}>Stop</button>
    </div>
  );
}
```

**forwardRef转发ref到子组件：**

```javascript
const FancyInput = React.forwardRef((props, ref) => {
  return <input ref={ref} className="fancy" {...props} />;
});

function Parent() {
  const inputRef = useRef(null);
  return <FancyInput ref={inputRef} placeholder="请输入..." />;
}
```

**useImperativeHandle暴露方法：**

```javascript
const CustomInput = React.forwardRef((props, ref) => {
  const inputRef = useRef(null);

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current.focus(),
    clear: () => { inputRef.current.value = ''; },
    getValue: () => inputRef.current.value,
  }));

  return <input ref={inputRef} {...props} />;
});

function Parent() {
  const inputRef = useRef(null);
  return (
    <div>
      <CustomInput ref={inputRef} />
      <button onClick={() => inputRef.current.focus()}>聚焦</button>
      <button onClick={() => inputRef.current.clear()}>清空</button>
    </div>
  );
}
```

---

### 3.8 自定义Hook

自定义Hook是以`use`为前缀命名的函数，通过组合内置Hook来封装可复用的状态逻辑。它是React中实现逻辑复用的首选方式。

**常见自定义Hook的完整实现：**

**useDebounce——防抖Hook：**

```javascript
function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// 使用示例
function SearchInput() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 500);

  useEffect(() => {
    if (debouncedQuery) {
      fetchSearchResults(debouncedQuery);
    }
  }, [debouncedQuery]);

  return <input value={query} onChange={e => setQuery(e.target.value)} />;
}
```

**useFetch——数据请求Hook：**

```javascript
function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const abortController = new AbortController();
    setLoading(true);
    setError(null);

    fetch(url, { ...options, signal: abortController.signal })
      .then(res => {
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => {
        if (err.name !== 'AbortError') {
          setError(err);
          setLoading(false);
        }
      });

    return () => abortController.abort();
  }, [url]);

  return { data, loading, error };
}

// 使用示例
function UserProfile({ userId }) {
  const { data: user, loading, error } = useFetch(`/api/users/${userId}`);
  if (loading) return <Spinner />;
  if (error) return <ErrorMessage error={error} />;
  return <div>{user.name}</div>;
}
```

**useLocalStorage——本地存储Hook：**

```javascript
function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}

// 使用示例
function Settings() {
  const [theme, setTheme] = useLocalStorage('theme', 'light');
  return <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>{theme}</button>;
}
```

**usePrevious——获取上一次渲染的值：**

```javascript
function usePrevious(value) {
  const ref = useRef();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}

// 使用示例
function Counter() {
  const [count, setCount] = useState(0);
  const prevCount = usePrevious(count);

  return (
    <div>
      <p>当前值: {count}，上一次值: {prevCount}</p>
      <button onClick={() => setCount(c => c + 1)}>+1</button>
    </div>
  );
}
```

**useClickOutside——检测点击外部区域：**

```javascript
function useClickOutside(ref, handler) {
  useEffect(() => {
    const listener = (event) => {
      if (!ref.current || ref.current.contains(event.target)) {
        return;
      }
      handler(event);
    };

    document.addEventListener('mousedown', listener);
    document.addEventListener('touchstart', listener);

    return () => {
      document.removeEventListener('mousedown', listener);
      document.removeEventListener('touchstart', listener);
    };
  }, [ref, handler]);
}

// 使用示例
function Dropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useClickOutside(dropdownRef, () => setIsOpen(false));

  return (
    <div ref={dropdownRef}>
      <button onClick={() => setIsOpen(!isOpen)}>Toggle</button>
      {isOpen && <ul className="dropdown-menu">
        <li>选项A</li>
        <li>选项B</li>
        <li>选项C</li>
      </ul>}
    </div>
  );
}
```

---

## 四、React事件系统

### 4.1 合成事件

> 面试题：React的事件机制和原生事件有什么区别？

React实现了自己的事件系统——合成事件（SyntheticEvent）。它是对浏览器原生事件的跨浏览器包装，提供了与原生事件一致的API（如`stopPropagation`、`preventDefault`），同时确保在不同浏览器中行为一致。

**事件委托机制的演变：**

- **React 16及之前**：所有事件都委托到`document`节点上。这在页面中存在多个React应用时可能产生冲突
- **React 17+**：事件委托到React挂载的root容器节点上（如`document.getElementById('root')`）。这个改变使得多个React版本可以安全共存于同一页面

**事件池（Event Pooling）：**

在React 16中，SyntheticEvent对象会被复用（池化）。事件回调执行完毕后，所有属性会被清空（设为null），以减少垃圾回收压力。如果需要异步访问事件对象，需要调用`event.persist()`来保留。React 17已经废弃了事件池机制，事件对象不再被复用。

**与原生事件的执行顺序：**

```
原生捕获阶段（从document到目标元素）
  → 原生目标阶段（目标元素上的原生事件）
  → 原生冒泡阶段（从目标元素到root容器）
  → React合成事件（捕获 → 冒泡）
```

```javascript
function App() {
  const divRef = useRef(null);

  useEffect(() => {
    // 原生事件
    divRef.current.addEventListener('click', () => {
      console.log('1. 原生事件');
    });
    document.addEventListener('click', () => {
      console.log('4. document原生事件');
    });
  }, []);

  return (
    <div
      ref={divRef}
      onClick={() => console.log('2. React合成事件（冒泡）')}
      onClickCapture={() => console.log('React合成事件（捕获）')}
    >
      点击我
    </div>
  );
}
// React 17+点击输出顺序:
// React合成事件（捕获）
// 1. 原生事件
// 2. React合成事件（冒泡）
// 4. document原生事件
```

**注意事项：**
- React合成事件中调用`e.stopPropagation()`不能阻止原生事件的传播
- 尽量不要混用React事件和原生事件
- React中没有事件捕获的`addEventListener`等效写法，使用`onClickCapture`等Capture后缀的属性

---

## 五、状态管理

### 5.1 Context API

React内置的状态管理方案，适用于简单的全局状态共享，如主题切换、国际化语言、当前用户信息等。

**不适合的场景：** 频繁更新的状态（如表单输入、动画状态），因为Context的value变化会导致所有消费者重渲染。

### 5.2 Redux

Redux是最经典的React状态管理库，基于Flux架构的单向数据流。

**核心概念：**
- **Store**：全局唯一的状态容器
- **Action**：描述状态变更的纯对象 `{ type: 'ADD_TODO', payload: { text: '学React' } }`
- **Reducer**：纯函数，接收当前state和action，返回新的state
- **Dispatch**：派发action的方法，触发reducer执行

**中间件：**
- **redux-thunk**：允许action creator返回函数（而非对象），用于处理异步逻辑
- **redux-saga**：使用Generator函数管理副作用，更适合复杂的异步流程（如竞态处理、取消请求）

**Redux Toolkit（RTK）——现代Redux开发的标准方式：**

```javascript
import { createSlice, configureStore, createAsyncThunk } from '@reduxjs/toolkit';

// 异步Thunk
const fetchUsers = createAsyncThunk('users/fetch', async () => {
  const response = await fetch('/api/users');
  return response.json();
});

// Slice
const usersSlice = createSlice({
  name: 'users',
  initialState: {
    list: [],
    loading: false,
    error: null,
  },
  reducers: {
    addUser(state, action) {
      state.list.push(action.payload); // RTK内部使用Immer，可以直接"修改"state
    },
    removeUser(state, action) {
      state.list = state.list.filter(u => u.id !== action.payload);
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchUsers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchUsers.fulfilled, (state, action) => {
        state.loading = false;
        state.list = action.payload;
      })
      .addCase(fetchUsers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  },
});

export const { addUser, removeUser } = usersSlice.actions;

// Store
const store = configureStore({
  reducer: {
    users: usersSlice.reducer,
  },
});
```

### 5.3 Zustand

Zustand是一个轻量级的状态管理库，以简洁的API和极小的体积著称。

```javascript
import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';

// 创建store
const useStore = create(
  devtools(
    persist(
      (set, get) => ({
        count: 0,
        users: [],
        increment: () => set((state) => ({ count: state.count + 1 })),
        decrement: () => set((state) => ({ count: state.count - 1 })),
        fetchUsers: async () => {
          const response = await fetch('/api/users');
          const users = await response.json();
          set({ users });
        },
        // 使用get获取当前状态
        doubleCount: () => get().count * 2,
      }),
      { name: 'app-storage' } // persist配置
    )
  )
);

// 使用——选择性订阅（只在count变化时重渲染）
function Counter() {
  const count = useStore((state) => state.count);
  const increment = useStore((state) => state.increment);
  return <button onClick={increment}>{count}</button>;
}
```

**Zustand vs Redux对比：**

| 对比项 | Zustand | Redux (RTK) |
|-------|---------|-------------|
| 样板代码 | 极少 | 较多（即使用RTK） |
| Provider | 不需要 | 需要`<Provider store={store}>` |
| 学习曲线 | 低 | 中等 |
| 选择性订阅 | 内置selector | 需要useSelector |
| 中间件 | 内置persist/devtools等 | 需要额外配置 |
| 适用规模 | 小到中型项目 | 中到大型项目 |

### 5.4 其他方案

**Jotai（原子化状态管理）：**
- 自底向上的原子化模型，每个atom是独立的状态单元
- 类似于React的useState，但可以跨组件共享
- 天然支持异步atom和派生atom

**Recoil（Facebook出品）：**
- atom（状态单元）和selector（派生状态/异步数据流）
- 与React Concurrent Mode深度集成
- 支持异步selector和数据流图

---

## 六、React Router v6

### 6.1 路由基础配置

```javascript
import { BrowserRouter, Routes, Route, Outlet, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="users" element={<Users />}>
            <Route path=":userId" element={<UserDetail />} />
          </Route>
          <Route path="dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

function Layout() {
  return (
    <div>
      <nav>导航栏</nav>
      <Outlet />  {/* 渲染子路由 */}
      <footer>页脚</footer>
    </div>
  );
}
```

**BrowserRouter vs HashRouter：**
- `BrowserRouter`：使用HTML5 History API（pushState），URL无#号，需要服务器配置支持
- `HashRouter`：使用URL的hash部分（`#/path`），不需要服务器配置，兼容性好

### 6.2 常用Hook

```javascript
import {
  useNavigate,
  useParams,
  useSearchParams,
  useLocation,
  useMatch,
} from 'react-router-dom';

function UserDetail() {
  // 获取动态路由参数
  const { userId } = useParams();

  // 编程式导航
  const navigate = useNavigate();
  const goBack = () => navigate(-1);
  const goToHome = () => navigate('/', { replace: true });

  // 查询参数
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get('tab');

  // 当前location信息
  const location = useLocation();
  console.log(location.pathname, location.search, location.state);

  // 匹配路由模式
  const match = useMatch('/users/:userId');
  console.log(match?.params.userId);

  return <div>User: {userId}</div>;
}
```

### 6.3 懒加载路由

```javascript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
```

### 6.4 路由守卫实现

```javascript
function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    // 未登录时重定向到登录页，并保存来源路径
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}

// 登录后跳回原页面
function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  const handleLogin = async () => {
    await login();
    navigate(from, { replace: true });
  };

  return <button onClick={handleLogin}>登录</button>;
}
```

---

## 七、React性能优化

> 面试题：React有哪些性能优化方式？

### 7.1 减少不必要渲染

**React.memo：**

```javascript
// 浅比较props，props不变则跳过渲染
const ExpensiveList = React.memo(function ExpensiveList({ items, onSelect }) {
  return items.map(item => (
    <div key={item.id} onClick={() => onSelect(item.id)}>
      {item.name}
    </div>
  ));
});

// 自定义比较函数
const UserCard = React.memo(
  function UserCard({ user, onClick }) {
    return <div onClick={onClick}>{user.name}</div>;
  },
  (prevProps, nextProps) => {
    // 返回true表示props相同，跳过渲染
    return prevProps.user.id === nextProps.user.id
        && prevProps.user.name === nextProps.user.name;
  }
);
```

**useMemo/useCallback稳定props引用：**

确保传递给React.memo子组件的对象和函数引用是稳定的，否则memo无意义。

**key的正确使用：**
- 使用稳定且唯一的key（如数据库ID）
- 避免使用数组索引（index）作为key的问题：列表重排时，index对应的元素变了但key没变，React误以为是同一元素而复用，导致状态混乱和不正确的渲染

```javascript
// 错误：使用index作为key
{items.map((item, index) => <Item key={index} data={item} />)}

// 正确：使用唯一且稳定的ID
{items.map(item => <Item key={item.id} data={item} />)}
```

### 7.2 代码分割

**React.lazy + Suspense：**

```javascript
// 路由级懒加载
const Dashboard = lazy(() => import('./pages/Dashboard'));

// 组件级懒加载
const HeavyChart = lazy(() => import('./components/HeavyChart'));

function AnalyticsPage() {
  const [showChart, setShowChart] = useState(false);
  return (
    <div>
      <button onClick={() => setShowChart(true)}>显示图表</button>
      {showChart && (
        <Suspense fallback={<ChartSkeleton />}>
          <HeavyChart />
        </Suspense>
      )}
    </div>
  );
}
```

**动态import()：** 配合Webpack/Vite实现按需加载，将应用拆分为多个chunk，减少初始加载体积。

### 7.3 虚拟列表

当需要渲染成千上万条数据的长列表时，虚拟列表是必备的优化手段。

**原理：** 仅渲染可视区域及其上下缓冲区内的DOM节点，而非全部数据。通过计算滚动位置来动态决定哪些元素需要渲染。

```javascript
import { FixedSizeList as List } from 'react-window';

function VirtualList({ data }) {
  const Row = ({ index, style }) => (
    <div style={style} className="list-item">
      {data[index].name}
    </div>
  );

  return (
    <List
      height={600}           // 可视区域高度
      itemCount={data.length} // 总数据量
      itemSize={50}           // 每项高度
      width="100%"
    >
      {Row}
    </List>
  );
}
```

常用库：
- `react-window`：轻量级，API简洁
- `react-virtuoso`：功能更丰富，支持动态高度、分组、无限滚动等

### 7.4 其他优化

**useTransition/useDeferredValue标记低优先级更新：**

```javascript
function SearchResults() {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();

  const handleChange = (e) => {
    // 输入框更新是高优先级的
    setQuery(e.target.value);
    // 搜索结果更新标记为低优先级
    startTransition(() => {
      setSearchQuery(e.target.value);
    });
  };

  return (
    <div>
      <input value={query} onChange={handleChange} />
      {isPending ? <Spinner /> : <Results query={searchQuery} />}
    </div>
  );
}

// useDeferredValue
function SearchResults({ query }) {
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  return (
    <div style={{ opacity: isStale ? 0.5 : 1 }}>
      <ExpensiveList query={deferredQuery} />
    </div>
  );
}
```

**其他优化手段：**
- 批量更新：React 18自动批量处理，减少渲染次数
- 合理使用Context：拆分Context，避免大范围不必要重渲染
- `useId`：生成服务端和客户端一致的稳定ID，避免hydration不匹配

---

## 八、服务端渲染SSR

### 8.1 SSR vs CSR vs SSG

| 渲染模式 | 全称 | 首屏速度 | SEO | 服务器压力 | 适用场景 |
|---------|------|---------|-----|-----------|--------|
| SSR | Server-Side Rendering | 快 | 好 | 大 | 内容动态、需SEO |
| CSR | Client-Side Rendering | 慢（白屏） | 差 | 小 | 后台管理系统、SPA |
| SSG | Static Site Generation | 最快 | 好 | 无 | 博客、文档、营销页 |

**SSR的工作流程：**
1. 用户请求页面
2. 服务器执行React组件，生成完整的HTML字符串
3. 将HTML发送给浏览器（用户立即看到内容，但不可交互）
4. 浏览器下载JavaScript bundle
5. React在客户端进行hydration（注水），将事件监听器附加到已有DOM上
6. 页面变为可交互

### 8.2 Next.js

Next.js是React生态中最主流的全栈框架，支持多种渲染模式。

**Pages Router（传统路由模式）：**

```javascript
// SSG - 构建时生成静态页面
export async function getStaticProps() {
  const posts = await fetchPosts();
  return { props: { posts }, revalidate: 60 }; // ISR: 60秒后增量再生成
}

// SSR - 每次请求时在服务器端渲染
export async function getServerSideProps(context) {
  const { params, req, res, query } = context;
  const user = await fetchUser(params.id);
  return { props: { user } };
}

// SSG动态路由的路径预生成
export async function getStaticPaths() {
  const posts = await fetchAllPosts();
  return {
    paths: posts.map(post => ({ params: { id: String(post.id) } })),
    fallback: 'blocking', // true | false | 'blocking'
  };
}
```

**App Router（Next.js 13+，基于React Server Components）：**

- **React Server Components（RSC）**：默认所有组件都是服务端组件，在服务器上渲染，零JavaScript发送到客户端。需要交互的组件用`'use client'`标记
- **Streaming SSR**：使用Suspense实现流式渲染，先发送页面骨架，数据加载完成后流式补充内容
- **Server Actions**：在服务端直接处理表单提交和数据变更

```javascript
// app/page.js (Server Component，默认)
async function PostsPage() {
  const posts = await db.posts.findMany(); // 直接访问数据库
  return (
    <div>
      {posts.map(post => <PostCard key={post.id} post={post} />)}
      <Suspense fallback={<CommentsSkeleton />}>
        <Comments /> {/* 流式加载 */}
      </Suspense>
    </div>
  );
}

// app/actions.js
'use server';
export async function createPost(formData) {
  const title = formData.get('title');
  await db.posts.create({ data: { title } });
  revalidatePath('/posts');
}
```

**App Router高级特性：**
- 并行路由（`@folder`）：同一页面同时渲染多个独立的区域
- 拦截路由（`(.)folder`、`(..)folder`）：实现模态框等覆盖式导航
- 中间件（`middleware.ts`）：在请求到达页面前执行逻辑（认证、重定向、国际化等）

---

## 九、React 18新特性

> 面试题：React 18带来了哪些重要更新？

### Automatic Batching（自动批量更新）

React 18之前，只有在React事件处理函数中的状态更新才会批量处理。React 18将自动批量更新扩展到所有场景：

```javascript
// React 18: 以下所有场景都会自动批量更新，只触发一次渲染
// 1. Promise回调
fetch('/api').then(() => {
  setCount(c => c + 1);
  setFlag(f => !f);
});

// 2. setTimeout
setTimeout(() => {
  setCount(c => c + 1);
  setFlag(f => !f);
}, 1000);

// 3. 原生事件处理
element.addEventListener('click', () => {
  setCount(c => c + 1);
  setFlag(f => !f);
});
```

### Concurrent Rendering（并发渲染）

并发渲染是React 18最核心的特性。它不是一个具体的API，而是一种底层机制：React可以同时准备多个版本的UI，渲染过程是可中断的。当有更高优先级的更新到来时，React可以暂停当前渲染，处理紧急更新，然后再恢复。

### useTransition

标记非紧急的状态更新，让React优先处理更重要的更新（如用户输入）。

```javascript
function TabContainer() {
  const [tab, setTab] = useState('home');
  const [isPending, startTransition] = useTransition();

  function selectTab(nextTab) {
    startTransition(() => {
      setTab(nextTab); // 标记为非紧急更新
    });
  }

  return (
    <div>
      <TabButtons onSelect={selectTab} />
      {isPending && <Spinner />}
      <TabContent tab={tab} />
    </div>
  );
}
```

### useDeferredValue

延迟更新一个值的显示，让UI在等待数据时保持响应。适合输入框联想等场景。

### Suspense for Data Fetching

Suspense不再仅限于代码分割，可以用于数据获取场景，与并发特性配合使用。

### Streaming SSR with Suspense

使用`renderToPipeableStream`替代`renderToString`，实现流式服务端渲染。页面可以分块发送，Suspense边界内的内容在准备好后单独流式传输。

### createRoot替代ReactDOM.render

```javascript
// React 17
import ReactDOM from 'react-dom';
ReactDOM.render(<App />, document.getElementById('root'));

// React 18
import { createRoot } from 'react-dom/client';
const root = createRoot(document.getElementById('root'));
root.render(<App />);
```

必须使用`createRoot`才能启用React 18的并发特性。

---

## 十、React 19新特性

> 面试题：React 19有哪些新特性？

### React Server Components（RSC）

React 19正式稳定了Server Components。服务端组件在服务器上渲染，不发送任何JavaScript到客户端。它们可以直接访问后端资源（数据库、文件系统、内部API），大幅减少客户端bundle大小。

```javascript
// Server Component（默认）
async function PostPage({ params }) {
  // 直接查询数据库，代码不会发送到客户端
  const post = await db.post.findUnique({ where: { id: params.id } });
  const comments = await db.comment.findMany({ where: { postId: params.id } });

  return (
    <article>
      <h1>{post.title}</h1>
      <p>{post.content}</p>
      <LikeButton postId={post.id} />  {/* 客户端组件 */}
      <CommentList comments={comments} />
    </article>
  );
}
```

### Server Actions

通过`'use server'`标记，可以在客户端组件中直接调用服务端函数。

```javascript
// actions.js
'use server';

export async function addToCart(productId) {
  const cart = await getCart();
  await db.cart.update({
    data: { items: { push: productId } },
  });
  revalidatePath('/cart');
}

// 客户端组件中使用
'use client';
import { addToCart } from './actions';

function AddToCartButton({ productId }) {
  return (
    <form action={addToCart.bind(null, productId)}>
      <button type="submit">加入购物车</button>
    </form>
  );
}
```

### use() Hook

`use()`是一个全新的Hook，可以读取Promise和Context。它可以在条件语句和循环中调用（这是其他Hook不允许的）。

```javascript
import { use, Suspense } from 'react';

function Comments({ commentsPromise }) {
  // use()会自动等待Promise resolve，配合Suspense展示loading
  const comments = use(commentsPromise);
  return comments.map(c => <Comment key={c.id} data={c} />);
}

function Page() {
  const commentsPromise = fetchComments(); // 不await，传递Promise
  return (
    <Suspense fallback={<Spinner />}>
      <Comments commentsPromise={commentsPromise} />
    </Suspense>
  );
}

// 在条件语句中读取Context
function StatusIcon({ isAdmin }) {
  if (isAdmin) {
    const theme = use(ThemeContext); // 可以在if中使用
    return <Icon theme={theme} name="admin" />;
  }
  return <Icon name="user" />;
}
```

### Actions（异步状态管理）

React 19引入了Actions概念——使用异步转换的函数。Actions自动管理pending状态、错误处理和乐观更新。

```javascript
function UpdateProfileForm() {
  const [error, submitAction, isPending] = useActionState(
    async (previousState, formData) => {
      const error = await updateProfile(formData);
      if (error) return error;
      redirect('/profile');
      return null;
    },
    null
  );

  return (
    <form action={submitAction}>
      <input name="name" />
      {error && <p className="error">{error}</p>}
      <button disabled={isPending}>
        {isPending ? '提交中...' : '更新'}
      </button>
    </form>
  );
}
```

### useFormStatus

在表单的子组件中获取父表单的提交状态。

```javascript
import { useFormStatus } from 'react-dom';

function SubmitButton() {
  const { pending, data, method, action } = useFormStatus();
  return (
    <button type="submit" disabled={pending}>
      {pending ? '提交中...' : '提交'}
    </button>
  );
}
```

### useActionState

管理表单action的状态，包括返回值和pending状态（替代此前的useFormState）。

### useOptimistic

实现乐观更新——在服务端操作完成之前先乐观地更新UI，如果操作失败则自动回滚。

```javascript
function MessageList({ messages, sendMessage }) {
  const [optimisticMessages, addOptimistic] = useOptimistic(
    messages,
    (currentMessages, newMessage) => [
      ...currentMessages,
      { ...newMessage, sending: true },
    ]
  );

  async function handleSubmit(formData) {
    const text = formData.get('text');
    addOptimistic({ text, sending: true }); // 立即显示
    await sendMessage(text);                // 等待服务器响应
  }

  return (
    <div>
      {optimisticMessages.map((msg, i) => (
        <div key={i} style={{ opacity: msg.sending ? 0.7 : 1 }}>
          {msg.text} {msg.sending && '(发送中...)'}
        </div>
      ))}
      <form action={handleSubmit}>
        <input name="text" />
        <button>发送</button>
      </form>
    </div>
  );
}
```

### ref作为prop（无需forwardRef）

React 19中，函数组件可以直接接收`ref`作为prop，不再需要`forwardRef`包裹。

```javascript
// React 19之前
const FancyInput = forwardRef((props, ref) => {
  return <input ref={ref} className="fancy" />;
});

// React 19
function FancyInput({ ref, ...props }) {
  return <input ref={ref} className="fancy" {...props} />;
}
```

### Context直接用作Provider

不再需要`<Context.Provider>`，可以直接将Context组件作为Provider使用。

```javascript
const ThemeContext = createContext('light');

// React 19之前
function App() {
  return (
    <ThemeContext.Provider value="dark">
      <Page />
    </ThemeContext.Provider>
  );
}

// React 19
function App() {
  return (
    <ThemeContext value="dark">
      <Page />
    </ThemeContext>
  );
}
```

---

## 总结

React的知识体系非常庞大，从基础的JSX和组件概念，到Fiber架构、Hooks的深入理解，再到性能优化和服务端渲染，每个领域都值得深入研究。在面试中，重要的不仅仅是记住API的用法，更关键的是理解其背后的设计原理和解决的问题场景。建议结合实际项目经验来准备面试，将理论知识与实践相结合，才能在面试中展现出真正的技术深度。
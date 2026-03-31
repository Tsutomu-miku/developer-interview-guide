# 微前端与微模块

> 本文系统梳理微前端架构的核心概念、主流方案、底层原理与高频面试题，适合中高级前端工程师面试备战与架构选型参考。

---

## 一、微前端概述

### 1.1 什么是微前端

微前端（Micro Frontends）是一种将前端应用拆解为多个**独立交付**的小型应用，再通过一个**主应用（基座）**在运行时将它们组合成一个完整产品的架构模式。其核心思想借鉴了后端微服务：

- **技术栈无关**：各子应用可以使用 React、Vue、Angular 等不同框架
- **独立开发、独立部署**：团队自治，子应用拥有自己的仓库和 CI/CD
- **运行时集成**：在浏览器中按需加载和组合子应用
- **增量升级**：可以逐步对遗留系统进行现代化改造

### 1.2 微前端解决的问题

| 问题 | 描述 |
|------|------|
| 巨石应用膨胀 | 单体前端项目代码量巨大，构建慢、协作难 |
| 技术栈锁定 | 无法在同一产品中使用不同框架 |
| 团队耦合 | 多个团队改同一个仓库，频繁冲突 |
| 遗留系统升级 | 老系统不能一次性重写，需要渐进迁移 |
| 独立部署需求 | 子业务希望独立发布，不影响其他模块 |

### 1.3 适用场景

- **大型企业级中后台系统**：如 CRM、ERP、运营平台，多个业务模块由不同团队负责
- **遗留系统渐进式迁移**：将 jQuery / AngularJS 老项目逐步替换为 React / Vue
- **跨团队协作的平台型产品**：各团队独立迭代，通过基座统一聚合
- **SaaS 多租户可插拔架构**：不同租户启用不同功能模块

### 1.4 微前端 vs Monorepo vs iframe

| 维度 | 微前端 | Monorepo | iframe |
|------|--------|----------|--------|
| 技术栈独立 | ✅ 完全独立 | ❌ 通常统一 | ✅ 完全独立 |
| 独立部署 | ✅ | ❌ 通常整体构建 | ✅ |
| 共享运行时 | ✅ 可共享依赖 | ✅ 天然共享 | ❌ 完全隔离 |
| 用户体验 | ✅ 单页体验 | ✅ 单页体验 | ❌ 白屏、性能差 |
| 通信便捷性 | 中等 | ✅ 直接引用 | ❌ postMessage |
| 路由管理 | 需要方案支持 | ✅ 天然统一 | ❌ 双滚动条 |
| CSS 隔离 | 需要方案支持 | 需要规范 | ✅ 天然隔离 |
| JS 隔离 | 需要沙箱 | 无需隔离 | ✅ 天然隔离 |
| 适用场景 | 大型多团队 | 中型统一技术栈 | 简单集成 |

> **面试要点**：iframe 看似"完美隔离"，但存在白屏、性能差、URL 不同步、弹窗无法全局居中、Cookie 共享受限（SameSite）等问题，实际项目中很少直接作为微前端方案使用。

---

## 二、主流方案对比

### 2.1 single-spa：路由劫持与生命周期

**single-spa** 是微前端领域的开山之作，提供了应用注册与生命周期管理的基础能力。

#### 核心原理：路由劫持

single-spa 通过劫持浏览器路由事件来决定激活哪个子应用：

```javascript
// single-spa 路由劫持核心原理（简化）
const originalPushState = window.history.pushState;
const originalReplaceState = window.history.replaceState;

window.history.pushState = function (...args) {
  const result = originalPushState.apply(this, args);
  // 路由变化后，重新检查哪些子应用需要挂载/卸载
  reroute();
  return result;
};

window.addEventListener('popstate', () => {
  reroute();
});

function reroute() {
  const appsThatShouldBeActive = registeredApps.filter(app =>
    app.activeWhen(window.location)
  );
  // 挂载需要激活的应用，卸载不再激活的应用
  appsToMount.forEach(app => app.mount());
  appsToUnmount.forEach(app => app.unmount());
}
```

#### 子应用生命周期

每个 single-spa 子应用必须导出三个生命周期钩子：

```javascript
// 子应用入口 - React 示例
import React from 'react';
import ReactDOM from 'react-dom';
import singleSpaReact from 'single-spa-react';
import App from './App';

const lifecycles = singleSpaReact({
  React,
  ReactDOM,
  rootComponent: App,
  errorBoundary(err, info, props) {
    return <div>子应用加载出错: {err.message}</div>;
  },
});

// 必须导出这三个生命周期
export const bootstrap = lifecycles.bootstrap; // 初始化，只执行一次
export const mount = lifecycles.mount;         // 挂载，路由激活时执行
export const unmount = lifecycles.unmount;     // 卸载，路由离开时执行
```

```javascript
// 主应用注册子应用
import { registerApplication, start } from 'single-spa';

registerApplication({
  name: 'app-react',
  app: () => System.import('http://localhost:3001/main.js'),
  activeWhen: (location) => location.pathname.startsWith('/react'),
  customProps: { authToken: 'xxx' },
});

registerApplication({
  name: 'app-vue',
  app: () => System.import('http://localhost:3002/main.js'),
  activeWhen: '/vue',
});

start(); // 启动 single-spa
```

**single-spa 的局限性**：
- 没有内置 JS 沙箱和 CSS 隔离
- 没有提供子应用加载策略（需要配合 SystemJS 等）
- 通信机制需要自行实现

---

### 2.2 qiankun：阿里巴巴微前端方案

qiankun 基于 single-spa 封装，补齐了沙箱隔离、样式隔离、预加载等关键能力，是国内使用最广泛的微前端方案。

#### 2.2.1 JS 沙箱机制

qiankun 提供了三种沙箱实现：

**（1）快照沙箱（SnapshotSandbox）**

适用于不支持 Proxy 的环境（如 IE11）。原理是在子应用挂载前**拍摄 window 快照**，卸载时**恢复快照**：

```javascript
// 手写快照沙箱
class SnapshotSandbox {
  constructor() {
    this.windowSnapshot = {};
    this.modifyProps = {};
    this.active = false;
  }

  // 激活沙箱：保存当前 window 快照，恢复上次的修改
  activate() {
    // 1. 拍摄当前 window 快照
    this.windowSnapshot = {};
    for (const key in window) {
      this.windowSnapshot[key] = window[key];
    }
    // 2. 恢复上次运行时的修改
    Object.keys(this.modifyProps).forEach(key => {
      window[key] = this.modifyProps[key];
    });
    this.active = true;
  }

  // 停用沙箱：记录修改，恢复 window 到快照状态
  deactivate() {
    this.modifyProps = {};
    for (const key in window) {
      if (window[key] !== this.windowSnapshot[key]) {
        // 记录变更
        this.modifyProps[key] = window[key];
        // 恢复原值
        window[key] = this.windowSnapshot[key];
      }
    }
    this.active = false;
  }
}

// 使用示例
const sandbox = new SnapshotSandbox();
sandbox.activate();
window.testVar = 'hello from micro app';
console.log(window.testVar); // 'hello from micro app'
sandbox.deactivate();
console.log(window.testVar); // undefined（已恢复）
sandbox.activate();
console.log(window.testVar); // 'hello from micro app'（恢复修改）
```

> **缺点**：快照沙箱无法支持多个子应用同时激活（因为直接修改 window 对象），且遍历 window 性能较差。

**（2）Legacy Proxy 沙箱（LegacySandbox）**

使用 Proxy 代理 window 对象，记录子应用对 window 的新增和修改：

```javascript
// Legacy Proxy 沙箱（简化实现）
class LegacySandbox {
  constructor() {
    this.addedKeys = new Set();    // 新增的属性
    this.modifiedMap = new Map();   // 修改的属性（原始值）
    this.currentMap = new Map();    // 当前沙箱内的值

    const rawWindow = window;
    const self = this;

    this.proxyWindow = new Proxy(rawWindow, {
      set(target, key, value) {
        if (!rawWindow.hasOwnProperty(key)) {
          self.addedKeys.add(key);
        } else if (!self.modifiedMap.has(key)) {
          self.modifiedMap.set(key, rawWindow[key]);
        }
        self.currentMap.set(key, value);
        rawWindow[key] = value;
        return true;
      },
      get(target, key) {
        return rawWindow[key];
      },
    });
  }

  activate() {
    this.currentMap.forEach((value, key) => {
      window[key] = value;
    });
  }

  deactivate() {
    this.modifiedMap.forEach((value, key) => {
      window[key] = value;
    });
    this.addedKeys.forEach(key => {
      delete window[key];
    });
  }
}
```

**（3）Proxy 沙箱（ProxySandbox）— 推荐**

每个子应用拥有独立的 fakeWindow，不直接修改全局 window，**支持多实例并行**：

```javascript
// Proxy 沙箱核心实现（简化版）
class ProxySandbox {
  constructor() {
    this.isRunning = false;
    const rawWindow = window;
    const fakeWindow = Object.create(null);

    this.proxyWindow = new Proxy(fakeWindow, {
      set(target, key, value) {
        if (this.isRunning) {
          target[key] = value;
          return true;
        }
        return true;
      }.bind(this),

      get(target, key) {
        // 优先从 fakeWindow 取值，取不到再从 rawWindow 取
        if (key in target) {
          return target[key];
        }
        const rawValue = rawWindow[key];
        // 对于函数需要绑定正确的 this
        if (typeof rawValue === 'function' && !rawValue.prototype) {
          return rawValue.bind(rawWindow);
        }
        return rawValue;
      },

      has(target, key) {
        return key in target || key in rawWindow;
      },
    });
  }

  activate() {
    this.isRunning = true;
  }

  deactivate() {
    this.isRunning = false;
  }
}

// 多实例互不干扰
const sandbox1 = new ProxySandbox();
const sandbox2 = new ProxySandbox();
sandbox1.activate();
sandbox2.activate();
sandbox1.proxyWindow.name = 'app1';
sandbox2.proxyWindow.name = 'app2';
console.log(sandbox1.proxyWindow.name); // 'app1'
console.log(sandbox2.proxyWindow.name); // 'app2'
console.log(window.name); // ''（原始 window 未被修改）
```

#### 2.2.2 样式隔离

qiankun 提供两种样式隔离方案：

```javascript
// 注册子应用时开启样式隔离
registerMicroApps([
  {
    name: 'app1',
    entry: '//localhost:8081',
    container: '#container',
    activeRule: '/app1',
    props: { shared: sharedState },
  },
], {
  sandbox: {
    strictStyleIsolation: true,    // 方案一：Shadow DOM 隔离
    // experimentalStyleIsolation: true, // 方案二：scoped CSS 隔离
  },
});
```

**strictStyleIsolation（Shadow DOM）**：
- 将子应用的 DOM 包裹在 Shadow DOM 中
- 优点：样式完全隔离
- 缺点：一些弹窗组件（如 antd Modal）会挂载到 document.body，逃逸出 Shadow DOM

**experimentalStyleIsolation（Scoped CSS）**：
- 给子应用的所有样式规则增加特殊选择器前缀
- 例如 `.btn { color: red; }` 变成 `div[data-qiankun="app1"] .btn { color: red; }`

#### 2.2.3 应用间通信

qiankun 提供了 `initGlobalState` API 来实现应用间通信：

```javascript
// 主应用 - 初始化全局状态
import { initGlobalState, MicroAppStateActions } from 'qiankun';

const state = {
  user: { name: '张三', role: 'admin' },
  theme: 'dark',
};

const actions: MicroAppStateActions = initGlobalState(state);

// 主应用监听变化
actions.onGlobalStateChange((newState, prevState) => {
  console.log('主应用监听到状态变化:', newState);
});

// 主应用修改状态
actions.setGlobalState({ theme: 'light' });
```

```javascript
// 子应用 - 在 mount 生命周期中获取通信方法
export async function mount(props) {
  // props 中会注入 onGlobalStateChange 和 setGlobalState
  props.onGlobalStateChange((state, prev) => {
    console.log('子应用接收到状态:', state);
    // 更新子应用内部状态
    store.commit('updateUser', state.user);
  });

  // 子应用修改全局状态
  props.setGlobalState({ theme: 'compact' });

  // 挂载子应用
  renderApp(props.container);
}
```

#### 2.2.4 loadMicroApp 手动加载

除了路由自动激活，qiankun 还提供了 `loadMicroApp` API 来手动加载子应用，适合在页面内嵌入组件级子应用：

```javascript
import { loadMicroApp } from 'qiankun';

// 在某个 React 组件中手动加载子应用
function Dashboard() {
  const containerRef = useRef(null);
  const microAppRef = useRef(null);

  useEffect(() => {
    microAppRef.current = loadMicroApp({
      name: 'widget-chart',
      entry: '//localhost:8082',
      container: containerRef.current,
      props: { chartType: 'bar', data: chartData },
    });

    return () => {
      // 组件卸载时，卸载子应用
      microAppRef.current.unmount();
    };
  }, []);

  return <div ref={containerRef} />;
}
```

---

### 2.3 Module Federation（Webpack 5）

Module Federation（模块联邦）是 Webpack 5 内置的模块共享方案，允许多个独立构建的应用在运行时共享模块。

#### 2.3.1 核心原理

```javascript
// Remote 应用 - webpack.config.js（提供模块的一方）
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'remoteApp',               // 模块名
      filename: 'remoteEntry.js',       // 入口文件名
      exposes: {
        './Button': './src/components/Button',  // 暴露的模块
        './utils': './src/utils/index',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
};
```

```javascript
// Host 应用 - webpack.config.js（消费模块的一方）
const { ModuleFederationPlugin } = require('webpack').container;

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'hostApp',
      remotes: {
        remoteApp: 'remoteApp@http://localhost:3001/remoteEntry.js',
      },
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
      },
    }),
  ],
};
```

```javascript
// Host 应用中使用远程模块
const RemoteButton = React.lazy(() => import('remoteApp/Button'));
const { formatDate } = await import('remoteApp/utils');

function App() {
  return (
    <React.Suspense fallback={<div>加载中...</div>}>
      <RemoteButton onClick={() => alert('来自远程的按钮！')} />
    </React.Suspense>
  );
}
```

#### 2.3.2 Shared 依赖机制

shared 配置是 Module Federation 最重要的优化手段：

```javascript
shared: {
  react: {
    singleton: true,          // 全局只加载一份
    requiredVersion: '^18.0.0',
    eager: false,             // 是否立即加载（而非异步）
    strictVersion: false,     // 版本不匹配时是否报错
  },
  lodash: {
    singleton: false,         // 允许多版本共存
    requiredVersion: '^4.17.0',
  },
  '@company/design-system': {
    singleton: true,
    version: '2.0.0',
    eager: true,              // 设为 eager 避免异步加载闪烁
  },
}
```

#### 2.3.3 动态远程加载

```javascript
// 运行时动态加载远程模块（不写死在配置中）
function loadRemoteModule(scope, module) {
  return async () => {
    await __webpack_init_sharing__('default');
    const container = window[scope];
    await container.init(__webpack_share_scopes__.default);
    const factory = await container.get(module);
    return factory();
  };
}

// 使用示例 - 动态决定加载哪个远程应用
async function loadDynamicRemote(remoteUrl, scopeName, moduleName) {
  // 1. 动态加载远程入口文件
  const script = document.createElement('script');
  script.src = remoteUrl;
  script.type = 'text/javascript';
  script.async = true;

  await new Promise((resolve, reject) => {
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });

  // 2. 初始化共享作用域
  await __webpack_init_sharing__('default');
  const container = window[scopeName];
  await container.init(__webpack_share_scopes__.default);

  // 3. 获取模块
  const factory = await container.get(moduleName);
  return factory();
}

// 从配置中心获取远程地址并加载
const remoteConfig = await fetch('/api/remote-config').then(r => r.json());
const RemoteWidget = React.lazy(() =>
  loadDynamicRemote(
    remoteConfig.widgetUrl,   // 'http://cdn.example.com/widget/remoteEntry.js'
    'widgetApp',
    './Widget'
  )
);
```

---

### 2.4 micro-app（京东）

micro-app 基于 **Web Components** 实现，通过自定义元素 `<micro-app>` 来加载子应用，使用更加简洁。

```javascript
// 主应用 - 安装和注册
import microApp from '@micro-zoe/micro-app';

microApp.start({
  plugins: {
    modules: {
      'app-vue': [{
        loader(code) {
          // 可以对子应用代码进行处理
          return code.replace('http://localhost:3001', 'https://cdn.example.com');
        },
      }],
    },
  },
});
```

```html
<!-- 主应用模板 - 通过 Web Component 标签使用 -->
<template>
  <div>
    <h1>主应用</h1>
    <micro-app
      name="app-vue"
      url="http://localhost:8081/"
      baseroute="/app-vue"
      :data="dataForChild"
      @datachange="handleDataChange"
      iframe
      keep-alive
    ></micro-app>
  </div>
</template>

<script>
export default {
  data() {
    return {
      dataForChild: { user: { name: '张三' } },
    };
  },
  methods: {
    handleDataChange(event) {
      console.log('子应用发送的数据:', event.detail.data);
    },
  },
};
</script>
```

```javascript
// 子应用 - 通信（发送数据给主应用）
if (window.__MICRO_APP_ENVIRONMENT__) {
  // 向主应用发送数据
  window.microApp.dispatch({ type: 'UPDATE_CART', payload: { count: 5 } });

  // 监听主应用发来的数据
  window.microApp.addDataListener((data) => {
    console.log('收到主应用数据:', data);
  });
}
```

**micro-app 特点**：
- 零依赖，基于 Web Components，使用 `<micro-app>` 标签
- 侵入性低，子应用几乎无需改造
- 支持 iframe 沙箱模式（v1.0+）
- 支持 keep-alive 缓存、预加载

---

### 2.5 wujie（腾讯）

wujie 采用 **iframe + Web Components** 的独特方案：用 iframe 来提供天然的 JS 沙箱，用 Web Components（Shadow DOM）来渲染 UI：

```javascript
// 主应用 - React 中使用 wujie
import WujieReact from 'wujie-react';

function App() {
  return (
    <div>
      <WujieReact
        width="100%"
        height="100%"
        name="vue-child"
        url="http://localhost:8082/"
        sync={true}
        alive={true}
        props={{ token: 'xxx', userInfo: currentUser }}
        beforeLoad={(appWindow) => {
          console.log('子应用即将加载', appWindow);
        }}
        afterMount={() => {
          console.log('子应用挂载完成');
        }}
      />
    </div>
  );
}
```

**wujie 核心架构**：

```
┌──────────────────────────────────────────────┐
│                   主应用                       │
│  ┌────────────────────────────────────────┐   │
│  │  Shadow DOM (Web Component)            │   │
│  │  ┌──────────────────────────────────┐  │   │
│  │  │       子应用 DOM 渲染区域         │  │   │
│  │  │    （样式隔离 by Shadow DOM）     │  │   │
│  │  └──────────────────────────────────┘  │   │
│  └────────────────────────────────────────┘   │
│                                               │
│  ┌────────────────────────────────────────┐   │
│  │  隐藏的 iframe                         │   │
│  │  ┌──────────────────────────────────┐  │   │
│  │  │   子应用 JS 运行在 iframe 中      │  │   │
│  │  │   （JS 隔离 by iframe sandbox）   │  │   │
│  │  └──────────────────────────────────┘  │   │
│  └────────────────────────────────────────┘   │
└──────────────────────────────────────────────┘
```

**优点**：
- 天然的 JS 隔离（iframe），不存在沙箱逃逸问题
- 天然的 CSS 隔离（Shadow DOM）
- iframe 中的 document.body 被代理到 Shadow DOM，保证 DOM 操作正确
- 支持 vite 构建的子应用

---

### 2.6 garfish（字节跳动）

garfish 是字节跳动开源的微前端框架，强调**高性能**和**可扩展的插件体系**：

```javascript
// 主应用配置
import Garfish from 'garfish';

Garfish.run({
  basename: '/',
  domGetter: '#container',
  apps: [
    {
      name: 'react-app',
      activeWhen: '/react',
      entry: 'http://localhost:3001',
    },
    {
      name: 'vue-app',
      activeWhen: '/vue',
      entry: 'http://localhost:3002',
    },
  ],
  // 全局生命周期钩子
  beforeLoad(appInfo) {
    console.log(`准备加载子应用: ${appInfo.name}`);
  },
  afterMount(appInfo) {
    console.log(`子应用挂载完成: ${appInfo.name}`);
  },
  // 错误处理
  onNotMatchRouter(path) {
    console.log('未匹配到子应用路由:', path);
  },
});
```

```javascript
// garfish 子应用入口 - Vue 3 示例
import { createApp } from 'vue';
import App from './App.vue';
import { vueBridge } from '@garfish/bridge-vue-v3';

export const provider = vueBridge({
  rootComponent: App,
  // 可自定义创建 app 实例的逻辑
  handleInstance(vueApp, garfishProps) {
    // 注入路由 basename
    vueApp.use(router(garfishProps.basename));
    vueApp.use(store);
  },
});

// 独立运行支持
if (!window.__GARFISH__) {
  const app = createApp(App);
  app.use(router('/'));
  app.mount('#app');
}
```

**garfish 特点**：
- 插件化架构，核心能力（路由、沙箱、加载器）均可通过插件扩展
- 支持 Snapshot 和 VM 两种沙箱
- 提供官方 bridge 包简化子应用接入
- 内置资源预加载与缓存策略

---

### 主流方案全面对比

| 特性 | single-spa | qiankun | Module Federation | micro-app | wujie | garfish |
|------|-----------|---------|-------------------|-----------|-------|---------|
| 基础原理 | 路由劫持 | 路由劫持+沙箱 | 模块共享 | Web Components | iframe+WC | 路由劫持+插件 |
| JS 沙箱 | ❌ | ✅ Proxy/快照 | ❌ | ✅ iframe可选 | ✅ iframe | ✅ Proxy/快照 |
| CSS 隔离 | ❌ | ✅ Shadow/Scoped | ❌ | ✅ Shadow DOM | ✅ Shadow DOM | ✅ |
| 子应用改造 | 多 | 中等 | 少 | 极少 | 极少 | 中等 |
| 多实例 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 预加载 | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| Vite 支持 | 差 | 差 | 需插件 | ✅ | ✅ | ✅ |

---

## 三、核心技术深度解析

### 3.1 JS 沙箱实现

#### 3.1.1 with + Proxy 沙箱

这是一种在 qiankun 中使用的巧妙手段——通过 `with` 语句改变作用域链，配合 `Proxy` 拦截属性访问：

```javascript
// with + Proxy 实现沙箱（手写完整版）
function createSandbox() {
  const fakeWindow = {};
  const rawWindow = window;

  const proxy = new Proxy(fakeWindow, {
    get(target, key) {
      // 拦截 window 和 self 的访问，返回 proxy 自身
      if (key === 'window' || key === 'self' || key === 'globalThis') {
        return proxy;
      }
      // 优先从沙箱中读取
      if (Reflect.has(target, key)) {
        return Reflect.get(target, key);
      }
      // 回退到真实 window
      const rawValue = Reflect.get(rawWindow, key);
      if (typeof rawValue === 'function') {
        // 原生方法需要绑定到原始 window
        const bindMethods = ['alert', 'addEventListener', 'setTimeout', 'setInterval'];
        if (bindMethods.includes(key)) {
          return rawValue.bind(rawWindow);
        }
      }
      return rawValue;
    },

    set(target, key, value) {
      // 所有写操作都写入沙箱
      Reflect.set(target, key, value);
      return true;
    },

    has(target, key) {
      // with 语句中的属性查找会触发 has 拦截
      return true; // 让 with 语句将所有变量访问都拦截到 proxy 上
    },
  });

  return proxy;
}

// 在沙箱中执行子应用代码
function execScriptInSandbox(code, sandbox) {
  const wrappedCode = `
    (function(window, self, globalThis) {
      with(window) {
        ${code}
      }
    })
  `;
  const fn = new Function('window', 'self', 'globalThis', `with(window){ ${code} }`);
  fn.call(sandbox, sandbox, sandbox, sandbox);
}

// 使用示例
const sandbox = createSandbox();
execScriptInSandbox(`
  var foo = 'bar';
  window.customProp = 'hello';
  console.log(foo);        // 'bar'
  console.log(customProp); // 'hello'
`, sandbox);

console.log(window.customProp); // undefined（主应用 window 不受影响）
```

#### 3.1.2 iframe 沙箱

利用 iframe 的天然隔离能力实现沙箱：

```javascript
// iframe 沙箱实现
class IframeSandbox {
  constructor() {
    this.iframe = document.createElement('iframe');
    this.iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin');
    this.iframe.style.display = 'none';
    document.body.appendChild(this.iframe);
    this.sandboxWindow = this.iframe.contentWindow;
  }

  execScript(code) {
    const scriptElement = this.sandboxWindow.document.createElement('script');
    scriptElement.textContent = code;
    this.sandboxWindow.document.body.appendChild(scriptElement);
  }

  // 代理 DOM 操作：将 iframe 中的 document.body 代理到主应用的容器
  patchDocument(containerElement) {
    const sandboxDoc = this.sandboxWindow.document;

    Object.defineProperty(this.sandboxWindow, 'document', {
      get() {
        return new Proxy(sandboxDoc, {
          get(target, key) {
            if (key === 'body' || key === 'documentElement') {
              return containerElement;
            }
            if (key === 'querySelector' || key === 'getElementById') {
              return (...args) => containerElement[key](...args);
            }
            const value = target[key];
            return typeof value === 'function' ? value.bind(target) : value;
          },
        });
      },
    });
  }

  destroy() {
    document.body.removeChild(this.iframe);
  }
}
```

#### 3.1.3 三种沙箱对比

| 维度 | 快照沙箱 | Proxy 沙箱 | iframe 沙箱 |
|------|---------|-----------|------------|
| 浏览器兼容 | IE11+ | Proxy 支持的浏览器 | 全部 |
| 多实例支持 | ❌ | ✅ | ✅ |
| 性能 | 差（遍历window） | 好 | 好 |
| 隔离程度 | 弱 | 中（需处理逃逸） | 强（天然隔离） |
| 实现复杂度 | 低 | 中 | 高（DOM代理） |

---

### 3.2 CSS 隔离方案

#### 3.2.1 Shadow DOM 隔离

```javascript
// Shadow DOM 隔离子应用样式
class MicroAppContainer extends HTMLElement {
  constructor() {
    super();
    // 创建 Shadow DOM
    this.shadow = this.attachShadow({ mode: 'open' });
  }

  loadApp(htmlContent) {
    // 将子应用的 HTML 内容放入 Shadow DOM
    this.shadow.innerHTML = htmlContent;

    // 处理子应用的 <style> 标签
    const styles = this.shadow.querySelectorAll('style');
    styles.forEach(style => {
      // 样式自动被 Shadow DOM 隔离，不会影响外部
      console.log('隔离的样式:', style.textContent);
    });
  }

  // 处理子应用通过 JS 动态创建的样式
  patchStyleInsertion() {
    const originalAppendChild = this.shadow.appendChild.bind(this.shadow);
    const originalInsertBefore = this.shadow.insertBefore.bind(this.shadow);

    // 拦截 document.head.appendChild(styleElement)
    // 将其重定向到 Shadow DOM 内部
    return { appendChild: originalAppendChild, insertBefore: originalInsertBefore };
  }
}

customElements.define('micro-app-container', MicroAppContainer);
```

#### 3.2.2 Scoped CSS（PostCSS Namespace）

```javascript
// PostCSS 插件 - 给所有选择器添加命名空间前缀
const postcss = require('postcss');

const scopedPlugin = (appName) => {
  return {
    postcssPlugin: 'postcss-micro-app-scope',
    Rule(rule) {
      // 跳过 keyframes 内的规则
      if (rule.parent && rule.parent.type === 'atrule' &&
          rule.parent.name === 'keyframes') {
        return;
      }

      rule.selectors = rule.selectors.map(selector => {
        // 跳过已有前缀的选择器
        if (selector.startsWith(`[data-app="${appName}"]`)) {
          return selector;
        }
        // :root 和 body 等特殊选择器处理
        if (selector === ':root' || selector === 'body' || selector === 'html') {
          return `[data-app="${appName}"]`;
        }
        return `[data-app="${appName}"] ${selector}`;
      });
    },
  };
};

// 使用示例
async function scopeCSS(cssCode, appName) {
  const result = await postcss([scopedPlugin(appName)]).process(cssCode, {
    from: undefined,
  });
  return result.css;
}

// 转换示例
// 输入: .btn { color: red; } h1 { font-size: 24px; }
// 输出: [data-app="app1"] .btn { color: red; } [data-app="app1"] h1 { font-size: 24px; }
```

#### 3.2.3 CSS 隔离方案对比

```javascript
// 运行时动态 Scoped（qiankun experimentalStyleIsolation 原理）
function scopeStyleElement(styleElement, appName) {
  const prefix = `div[data-qiankun="${appName}"]`;
  const sheet = styleElement.sheet;

  if (!sheet) return;

  const rules = Array.from(sheet.cssRules);
  rules.forEach((rule, index) => {
    if (rule instanceof CSSStyleRule) {
      const newSelector = rule.selectorText
        .split(',')
        .map(s => `${prefix} ${s.trim()}`)
        .join(', ');
      const newRule = `${newSelector} { ${rule.style.cssText} }`;
      sheet.deleteRule(index);
      sheet.insertRule(newRule, index);
    }
  });
}
```

| 方案 | 隔离强度 | 弹窗样式 | 动态样式 | 性能 |
|------|---------|---------|---------|------|
| Shadow DOM | 强 | ❌ 逃逸 | ✅ 自动隔离 | 好 |
| Scoped CSS | 中 | ✅ 可处理 | 需拦截 | 中 |
| CSS Modules | 弱（仅类名） | ✅ | ✅ | 好 |
| BEM 约定 | 弱 | ✅ | ✅ | 好 |

---

### 3.3 应用间通信

#### 3.3.1 CustomEvent 通信

```javascript
// 基于 CustomEvent 实现发布-订阅通信
class MicroAppEventBus {
  constructor() {
    this.eventTarget = new EventTarget();
  }

  // 发送事件
  emit(eventName, data) {
    const event = new CustomEvent(eventName, {
      detail: data,
      bubbles: false,
    });
    this.eventTarget.dispatchEvent(event);
  }

  // 监听事件
  on(eventName, callback) {
    const handler = (e) => callback(e.detail);
    this.eventTarget.addEventListener(eventName, handler);
    // 返回取消订阅函数
    return () => this.eventTarget.removeEventListener(eventName, handler);
  }

  // 一次性监听
  once(eventName, callback) {
    const handler = (e) => callback(e.detail);
    this.eventTarget.addEventListener(eventName, handler, { once: true });
  }
}

// 挂载到全局，供所有子应用使用
window.__MICRO_EVENT_BUS__ = new MicroAppEventBus();

// 子应用 A - 发送消息
window.__MICRO_EVENT_BUS__.emit('cart:updated', { count: 3, total: 299 });

// 子应用 B - 接收消息
const unsubscribe = window.__MICRO_EVENT_BUS__.on('cart:updated', (data) => {
  console.log('购物车更新:', data); // { count: 3, total: 299 }
});
// 组件卸载时取消订阅
unsubscribe();
```

#### 3.3.2 Props 传递

```javascript
// 主应用传递 props 给子应用（以 qiankun 为例）
const sharedActions = {
  // 共享方法
  navigate: (path) => history.push(path),
  getToken: () => localStorage.getItem('token'),
  showGlobalLoading: () => store.dispatch('setLoading', true),
  hideGlobalLoading: () => store.dispatch('setLoading', false),
  // 共享数据
  userInfo: currentUser,
  permissions: userPermissions,
};

registerMicroApps([
  {
    name: 'sub-app',
    entry: '//localhost:8081',
    container: '#container',
    activeRule: '/sub',
    props: sharedActions, // 通过 props 注入到子应用
  },
]);
```

#### 3.3.3 全局 Store 通信

```javascript
// 跨应用共享的响应式 Store（精简实现）
class SharedStore {
  constructor(initialState = {}) {
    this._state = initialState;
    this._listeners = new Map();
    this._id = 0;
  }

  getState() {
    return { ...this._state };
  }

  setState(partialState) {
    const prevState = { ...this._state };
    this._state = { ...this._state, ...partialState };
    // 通知所有订阅者
    this._listeners.forEach((listener) => {
      listener(this._state, prevState);
    });
  }

  subscribe(listener) {
    const id = ++this._id;
    this._listeners.set(id, listener);
    // 立即发送当前状态
    listener(this._state, this._state);
    return () => this._listeners.delete(id);
  }

  // 提供给 React 的 hook
  useStore(selector = (s) => s) {
    const [state, setState] = React.useState(() => selector(this._state));

    React.useEffect(() => {
      return this.subscribe((newState) => {
        const selected = selector(newState);
        setState(selected);
      });
    }, []);

    return state;
  }
}

// 全局唯一实例
window.__SHARED_STORE__ = new SharedStore({
  user: null,
  theme: 'light',
  locale: 'zh-CN',
  notifications: [],
});

// 子应用中使用
function UserAvatar() {
  const user = window.__SHARED_STORE__.useStore(state => state.user);
  return user ? <img src={user.avatar} alt={user.name} /> : <span>未登录</span>;
}
```

---

### 3.4 路由管理与资源加载

#### 3.4.1 路由同步

```javascript
// 主子应用路由同步方案
class MicroRouter {
  constructor(basePath) {
    this.basePath = basePath;
    this.apps = new Map();
  }

  // 注册子应用路由规则
  register(appName, activeRule) {
    this.apps.set(appName, {
      activeRule,
      active: false,
    });
  }

  // 匹配当前路由
  matchApps(pathname) {
    const matched = [];
    this.apps.forEach((config, name) => {
      if (typeof config.activeRule === 'function') {
        if (config.activeRule(pathname)) matched.push(name);
      } else if (pathname.startsWith(config.activeRule)) {
        matched.push(name);
      }
    });
    return matched;
  }

  // 监听路由变化
  listen(callback) {
    const handleRouteChange = () => {
      const matched = this.matchApps(window.location.pathname);
      callback(matched, window.location);
    };

    window.addEventListener('popstate', handleRouteChange);
    // 拦截 pushState
    const originalPushState = history.pushState;
    history.pushState = function (...args) {
      originalPushState.apply(this, args);
      handleRouteChange();
    };
  }
}
```

#### 3.4.2 HTML Entry 资源加载

```javascript
// HTML Entry 加载原理（qiankun 使用 import-html-entry）
async function loadHTMLEntry(entryUrl) {
  // 1. 获取 HTML 内容
  const html = await fetch(entryUrl).then(res => res.text());

  // 2. 解析 HTML，提取资源
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, 'text/html');

  // 3. 提取外部 CSS
  const styles = [];
  doc.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
    const href = new URL(link.getAttribute('href'), entryUrl).href;
    styles.push(fetch(href).then(res => res.text()));
  });
  doc.querySelectorAll('style').forEach(style => {
    styles.push(Promise.resolve(style.textContent));
  });

  // 4. 提取外部 JS
  const scripts = [];
  doc.querySelectorAll('script').forEach(script => {
    if (script.src) {
      const src = new URL(script.getAttribute('src'), entryUrl).href;
      scripts.push({ type: 'external', src });
    } else if (script.textContent.trim()) {
      scripts.push({ type: 'inline', content: script.textContent });
    }
  });

  // 5. 提取模板（去掉 script 和 link 后的 HTML）
  doc.querySelectorAll('script').forEach(s => s.remove());
  doc.querySelectorAll('link[rel="stylesheet"]').forEach(l => l.remove());
  const template = doc.body.innerHTML;

  // 6. 加载所有 CSS 内容
  const styleContents = await Promise.all(styles);

  return {
    template,
    styles: styleContents,
    scripts,
    // 执行子应用脚本的方法
    async execScripts(sandbox) {
      for (const script of scripts) {
        const code = script.type === 'external'
          ? await fetch(script.src).then(r => r.text())
          : script.content;
        execScriptInSandbox(code, sandbox);
      }
      // 返回子应用导出的生命周期
      return sandbox.__MICRO_APP_EXPORTS__;
    },
  };
}
```

---

## 四、微模块（Module Federation 深度）

### 4.1 Module Federation 2.0

Module Federation 2.0（由 `@module-federation/enhanced`）引入了更强大的运行时能力：

```javascript
// Module Federation 2.0 配置示例
const { ModuleFederationPlugin } = require('@module-federation/enhanced/webpack');

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: 'host',
      remotes: {
        remote1: 'remote1@http://localhost:3001/mf-manifest.json',
      },
      shared: {
        react: { singleton: true },
        'react-dom': { singleton: true },
      },
      // 2.0 新增：运行时插件
      runtimePlugins: [
        require.resolve('./src/mf-plugins/fallback-plugin'),
        require.resolve('./src/mf-plugins/retry-plugin'),
      ],
    }),
  ],
};
```

#### 运行时插件系统

```javascript
// 自定义运行时插件 - 加载失败容错
// src/mf-plugins/fallback-plugin.js
export default function fallbackPlugin() {
  return {
    name: 'fallback-plugin',

    // 远程模块加载前的钩子
    beforeRequest(args) {
      console.log(`准备加载远程模块: ${args.id}`);
      return args;
    },

    // 加载错误时的容错处理
    errorLoadRemote({ id, error, from, origin }) {
      console.error(`远程模块 ${id} 加载失败:`, error);

      // 返回降级模块
      const FallbackComponent = () => {
        return React.createElement(
          'div',
          { className: 'fallback-container' },
          `模块 ${id} 暂时不可用，请稍后重试`
        );
      };
      return () => ({ default: FallbackComponent });
    },

    // 模块解析前的钩子
    beforeInit(args) {
      // 可以动态修改共享依赖配置
      return args;
    },

    // 共享依赖解析钩子
    resolveShare(args) {
      // 自定义共享依赖版本策略
      const { shareScopeMap, scope, pkgName, version } = args;
      return args;
    },
  };
}
```

```javascript
// 自定义运行时插件 - 重试机制
// src/mf-plugins/retry-plugin.js
export default function retryPlugin() {
  return {
    name: 'retry-plugin',
    async loadRemote(args) {
      const maxRetries = 3;
      let lastError;

      for (let i = 0; i < maxRetries; i++) {
        try {
          return await args.origin.loadRemote(args.id);
        } catch (error) {
          lastError = error;
          console.warn(`加载重试 ${i + 1}/${maxRetries}: ${args.id}`);
          // 指数退避
          await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
        }
      }
      throw lastError;
    },
  };
}
```

### 4.2 Vite 集成（vite-plugin-federation）

由于 Module Federation 最初是 Webpack 5 的功能，Vite 生态通过 `@originjs/vite-plugin-federation` 提供了支持：

```javascript
// Remote 应用 - vite.config.js
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'remote-app',
      filename: 'remoteEntry.js',
      exposes: {
        './UserCard': './src/components/UserCard.vue',
        './useAuth': './src/composables/useAuth.ts',
      },
      shared: ['vue', 'vue-router', 'pinia'],
    }),
  ],
  build: {
    target: 'esnext',
    minify: false,       // 开发阶段建议关闭
    cssCodeSplit: false,  // MF 要求关闭 CSS 代码分割
  },
});
```

```javascript
// Host 应用 - vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import federation from '@originjs/vite-plugin-federation';

export default defineConfig({
  plugins: [
    react(),
    federation({
      name: 'host-app',
      remotes: {
        remoteApp: 'http://localhost:5001/assets/remoteEntry.js',
      },
      shared: ['react', 'react-dom'],
    }),
  ],
});
```

```vue
<!-- Host 应用中使用远程 Vue 组件 -->
<template>
  <div class="dashboard">
    <h2>仪表盘</h2>
    <Suspense>
      <template #default>
        <RemoteUserCard :userId="currentUserId" />
      </template>
      <template #fallback>
        <div class="skeleton">加载中...</div>
      </template>
    </Suspense>
  </div>
</template>

<script setup>
import { defineAsyncComponent, ref } from 'vue';

const RemoteUserCard = defineAsyncComponent(
  () => import('remoteApp/UserCard')
);

const currentUserId = ref('user-001');
</script>
```

### 4.3 粒度设计：页面级 vs 组件级 vs 函数级

Module Federation 支持多种粒度的模块共享：

```javascript
// ===== 页面级共享 =====
// 适合：独立的业务页面，如订单管理、用户中心
// remote webpack.config.js
exposes: {
  './OrderPage': './src/pages/OrderManagement',
  './UserCenter': './src/pages/UserCenter',
},

// host 使用
const OrderPage = React.lazy(() => import('orderApp/OrderPage'));
<Route path="/orders" element={<OrderPage />} />
```

```javascript
// ===== 组件级共享 =====
// 适合：跨应用复用的 UI 组件，如通用表格、图表组件
// remote webpack.config.js
exposes: {
  './DataTable': './src/components/DataTable',
  './BarChart': './src/components/BarChart',
  './UserAvatar': './src/components/UserAvatar',
},

// host 使用
const DataTable = React.lazy(() => import('sharedUI/DataTable'));
function MyPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <DataTable columns={columns} dataSource={data} />
    </Suspense>
  );
}
```

```javascript
// ===== 函数级共享 =====
// 适合：工具函数、业务逻辑、hooks
// remote webpack.config.js
exposes: {
  './utils': './src/utils/index',
  './useAuth': './src/hooks/useAuth',
  './validators': './src/utils/validators',
},

// host 使用
const { formatCurrency, parseDate } = await import('sharedUtils/utils');
const { useAuth } = await import('authApp/useAuth');

function CheckoutPage() {
  const { user, logout } = useAuth();
  const formattedPrice = formatCurrency(totalPrice);
  // ...
}
```

```
粒度设计决策树：

┌─ 是否有独立路由？
│  ├─ 是 → 页面级共享（子应用独立路由和状态管理）
│  └─ 否 ─┐
│          ├─ 是否有 UI 渲染？
│          │  ├─ 是 → 组件级共享（暴露组件，接受 props）
│          │  └─ 否 → 函数级共享（暴露纯函数/hooks）
```

**各粒度对比**：

| 维度 | 页面级 | 组件级 | 函数级 |
|------|--------|--------|--------|
| 独立性 | 最强 | 中 | 最弱 |
| 复用灵活度 | 低 | 高 | 最高 |
| 通信复杂度 | 低（路由驱动） | 中（props/events） | 低（函数调用） |
| 加载粒度 | 粗（整页） | 中 | 细（单函数） |
| 适用场景 | 业务域拆分 | UI 复用 | 逻辑复用 |

---

## 五、微前端中的 Angular 模板处理

在使用 Angular 子应用时，如果涉及模板插值语法，需要注意在文档和代码块中正确处理：

```html
{% raw %}
<!-- Angular 子应用中的模板 -->
<div class="user-profile">
  <h2>{{ user.name }}</h2>
  <p>角色: {{ user.role }}</p>
  <span *ngIf="user.isAdmin">{{ adminLabel }}</span>
</div>
{% endraw %}
```

```typescript
{% raw %}
// Angular 子应用暴露为微前端
@Component({
  selector: 'app-widget',
  template: `
    <div class="widget-container">
      <h3>{{ title }}</h3>
      <ul>
        <li *ngFor="let item of items">
          {{ item.name }} - {{ item.value | currency }}
        </li>
      </ul>
      <p>总计: {{ total | number:'1.2-2' }}</p>
    </div>
  `,
})
export class WidgetComponent {
  @Input() title = '数据看板';
  items = [];
  get total() {
    return this.items.reduce((sum, item) => sum + item.value, 0);
  }
}
{% endraw %}
```

```html
{% raw %}
<!-- Vue 中使用双花括号插值 -->
<template>
  <div class="micro-widget">
    <span>用户名: {{ username }}</span>
    <span>余额: {{ balance.toFixed(2) }}</span>
    <div v-for="app in microApps" :key="app.name">
      {{ app.name }} - {{ app.status }}
    </div>
  </div>
</template>
{% endraw %}
```

---

## 六、实践与高频面试题

### 面试题 1：什么是微前端？和 iframe 相比有什么优势？

**参考答案**：

微前端是将前端应用拆分成多个小型应用，由一个基座在运行时组合的架构模式。与 iframe 相比：

1. **用户体验**：微前端保持单页应用体验，无白屏；iframe 有加载延迟和白屏
2. **URL 同步**：微前端可统一管理路由；iframe 的 URL 与主应用不同步
3. **弹窗定位**：微前端弹窗可全屏居中；iframe 弹窗只能在 iframe 区域内
4. **共享资源**：微前端可共享依赖（如 React）；iframe 每个都独立加载
5. **通信便捷**：微前端可直接共享状态；iframe 只能用 postMessage
6. **SEO**：微前端对搜索引擎更友好；iframe 内容难以被爬虫抓取

---

### 面试题 2：请解释 qiankun 的三种 JS 沙箱及其区别

**参考答案**：

1. **快照沙箱（SnapshotSandbox）**：挂载前遍历 window 属性做快照，卸载时对比差异恢复。缺点：不支持多实例、性能差。
2. **Legacy Proxy 沙箱（LegacySandbox）**：用 Proxy 代理 window，记录新增和修改的属性。支持单实例，但仍然直接修改 window。
3. **Proxy 沙箱（ProxySandbox）**：每个子应用一个 fakeWindow，所有读写都在 fakeWindow 上，不修改原始 window。支持多实例并行，是推荐方案。

---

### 面试题 3：手写一个简单的 Proxy 沙箱

```javascript
// 面试常考：手写 Proxy 沙箱
function createProxySandbox(appName) {
  const fakeWindow = Object.create(null);
  let isActive = false;

  const proxy = new Proxy(fakeWindow, {
    get(target, key) {
      // window 和 self 指向代理对象
      if (key === 'window' || key === 'self' || key === 'globalThis') {
        return proxy;
      }
      // 优先从沙箱读取
      if (key in target) {
        return target[key];
      }
      // 兜底到真实 window
      const rawValue = window[key];
      if (typeof rawValue === 'function' && !/^[A-Z]/.test(key)) {
        return rawValue.bind(window);
      }
      return rawValue;
    },

    set(target, key, value) {
      if (isActive) {
        target[key] = value;
        console.log(`[${appName}] 设置属性 ${String(key)}`);
      }
      return true;
    },

    has(target, key) {
      return key in target || key in window;
    },

    deleteProperty(target, key) {
      if (key in target) {
        delete target[key];
        return true;
      }
      return true;
    },
  });

  return {
    proxy,
    activate() { isActive = true; },
    deactivate() { isActive = false; },
  };
}
```

---

### 面试题 4：微前端中 CSS 隔离有哪些方案？各有什么优缺点？

**参考答案**：

| 方案 | 优点 | 缺点 |
|------|------|------|
| Shadow DOM | 隔离彻底，自动生效 | 弹窗挂载到 body 外逃逸、样式穿透困难 |
| Scoped CSS（属性选择器前缀） | 兼容性好、弹窗样式可处理 | 需运行时处理、有性能开销 |
| CSS Modules | 构建时处理、性能好 | 只处理 className，不处理标签选择器 |
| BEM 命名约定 | 简单、无运行时开销 | 依赖人工遵守、无法强制隔离 |
| PostCSS Namespace | 构建时自动添加前缀 | 需要子应用接入构建插件 |

---

### 面试题 5：Module Federation 和微前端有什么关系？它的 shared 机制是如何工作的？

**参考答案**：

Module Federation 是 Webpack 5 的模块联邦特性，它实现了跨应用的模块共享。它和传统微前端（如 qiankun）的关系是**互补**的——MF 解决的是模块级别的共享复用，传统微前端解决的是应用级别的隔离和集成。

shared 工作机制：
1. 构建时，Webpack 将 shared 依赖标记为异步模块
2. 运行时，各应用通过 `__webpack_share_scopes__` 共享作用域协商版本
3. 如果配置了 `singleton: true`，全局只加载一份，使用语义化版本中满足所有要求的最高版本
4. 如果版本不匹配且 `strictVersion: true`，会抛出警告或错误
5. `eager: true` 会将 shared 模块打入入口 chunk 而非异步加载

---

### 面试题 6：微前端如何处理子应用之间的路由冲突？

**参考答案**：

1. **路由前缀隔离**：给每个子应用分配独立的路由前缀，如 `/app1/*`、`/app2/*`
2. **baseroute/basename 传递**：主应用将路由前缀通过 props 传递给子应用，子应用在自己的 router 中使用此 basename
3. **路由监听协调**：主应用统一拦截 `pushState`/`replaceState`/`popstate`，根据路由规则决定激活哪个子应用
4. **History 与 Hash 统一**：建议所有子应用统一使用 History 模式或 Hash 模式，避免混用导致冲突

---

### 面试题 7：qiankun 子应用的生命周期及执行顺序是什么？

**参考答案**：

```
首次加载：bootstrap → mount
路由切出：unmount
再次进入：mount（不会再执行 bootstrap）
应用更新：update（loadMicroApp 模式）
```

- `bootstrap`：仅在首次加载时调用一次，做初始化
- `mount`：每次子应用被激活时调用，渲染 DOM
- `unmount`：每次子应用离开时调用，清理 DOM、解绑事件
- `update`：`loadMicroApp` 模式下 props 更新时调用

---

### 面试题 8：微前端中如何实现子应用预加载？

```javascript
// qiankun 预加载策略
import { prefetchApps } from 'qiankun';

// 方式一：手动预加载
prefetchApps([
  { name: 'app1', entry: '//localhost:8081' },
  { name: 'app2', entry: '//localhost:8082' },
]);

// 方式二：注册时配置预加载
start({
  prefetch: 'all',           // 'all' | 'popstate' | string[] | function
  // prefetch: ['app1'],     // 只预加载指定应用
  // prefetch: (apps) => {   // 自定义策略
  //   return { criticalApps: [apps[0]], minorApps: apps.slice(1) };
  // },
});
```

```javascript
// 手写预加载核心逻辑
function prefetchApp(entry) {
  // 利用 requestIdleCallback 在浏览器空闲时加载
  if (window.requestIdleCallback) {
    requestIdleCallback(async () => {
      // 1. 预加载 HTML
      const html = await fetch(entry).then(r => r.text());

      // 2. 解析并预加载 JS 和 CSS 资源
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, 'text/html');

      // 预加载 CSS
      doc.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
        const prefetchLink = document.createElement('link');
        prefetchLink.rel = 'prefetch';
        prefetchLink.href = new URL(link.getAttribute('href'), entry).href;
        document.head.appendChild(prefetchLink);
      });

      // 预加载 JS
      doc.querySelectorAll('script[src]').forEach(script => {
        const prefetchLink = document.createElement('link');
        prefetchLink.rel = 'prefetch';
        prefetchLink.href = new URL(script.getAttribute('src'), entry).href;
        document.head.appendChild(prefetchLink);
      });
    });
  }
}
```

---

### 面试题 9：微前端如何处理公共依赖？

**参考答案**：

| 方案 | 实现方式 | 优缺点 |
|------|---------|--------|
| externals + CDN | 子应用配置 externals，从 CDN 全局加载 | 简单但灵活性差 |
| Module Federation shared | 构建配置 shared，运行时协商版本 | 灵活，支持多版本 |
| 主应用注入 | 主应用加载公共库并挂到 window | 简单但强耦合 |
| Import Maps | 浏览器原生模块映射 | 现代方案但兼容性有限 |

---

### 面试题 10：什么是沙箱逃逸？如何避免？

**参考答案**：

沙箱逃逸是指子应用绕过沙箱限制，直接修改了主应用的全局状态。常见的逃逸场景：

1. **原型链污染**：通过 `window.__proto__` 或 `Object.prototype` 修改全局原型
2. **DOM 操作泄漏**：`document.body.appendChild` 创建的元素脱离子应用容器
3. **闭包引用**：子应用在 unmount 后仍有定时器或事件监听持有引用
4. **eval/new Function**：动态代码执行可能逃逸沙箱作用域

**防护措施**：
- 冻结关键原型对象（`Object.freeze(Object.prototype)` 需谨慎）
- 拦截 DOM 操作，重写 `createElement`、`appendChild`
- unmount 时自动清理定时器和事件监听
- 使用 iframe 沙箱获得更强的隔离

---

### 面试题 11：微前端中如何做灰度发布和版本管理？

```javascript
// 基于配置中心的灰度方案
async function getAppConfig(appName, userId) {
  const config = await fetch('/api/micro-app-config', {
    headers: { 'X-User-Id': userId },
  }).then(r => r.json());

  // 配置中心返回格式
  // {
  //   "app1": {
  //     "stable": "https://cdn.com/app1/v1.2.0/",
  //     "canary": "https://cdn.com/app1/v1.3.0-beta/",
  //     "canaryRatio": 0.1,        // 10% 灰度
  //     "canaryUsers": ["user001"]  // 白名单
  //   }
  // }

  const appConfig = config[appName];
  const isCanaryUser =
    appConfig.canaryUsers?.includes(userId) ||
    hashToRatio(userId) < appConfig.canaryRatio;

  return isCanaryUser ? appConfig.canary : appConfig.stable;
}

function hashToRatio(userId) {
  let hash = 0;
  for (let i = 0; i < userId.length; i++) {
    hash = ((hash << 5) - hash) + userId.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash % 100) / 100;
}

// 动态注册子应用
const entry = await getAppConfig('orderApp', currentUser.id);
registerMicroApps([{
  name: 'orderApp',
  entry,  // 灰度版本 or 稳定版本
  container: '#container',
  activeRule: '/orders',
}]);
```

---

### 面试题 12：请比较 qiankun、micro-app、wujie 三种方案的隔离机制

**参考答案**：

| 维度 | qiankun | micro-app | wujie |
|------|---------|-----------|-------|
| JS 隔离 | Proxy 代理 window | iframe 沙箱（可选） | iframe（天然隔离） |
| CSS 隔离 | Shadow DOM / Scoped | Shadow DOM | Shadow DOM |
| 隔离强度 | 中（有逃逸风险） | 中-强 | 强（iframe 天然隔离） |
| 多实例 | ProxySandbox 支持 | 支持 | 支持 |
| 子应用改造 | 需改造入口文件 | 几乎零改造 | 几乎零改造 |
| DOM 代理 | 无 | 无 | iframe document → Shadow DOM |

---

### 面试题 13：Module Federation 2.0 相比 1.0 有哪些改进？

**参考答案**：

1. **运行时插件系统**：可在模块加载的各阶段注入自定义逻辑（容错、重试、日志等）
2. **Manifest 协议**：用 `mf-manifest.json` 替代 `remoteEntry.js`，支持更丰富的元数据
3. **类型提示**：自动生成远程模块的 TypeScript 类型定义
4. **Chrome DevTools**：提供浏览器调试插件
5. **框架无关**：不再绑定 Webpack，支持 Rspack、Vite 等构建工具
6. **动态路由**：内置对远程路由的支持

---

### 面试题 14：微前端项目中如何做性能优化？

**参考答案**：

1. **资源预加载**：利用 `requestIdleCallback` 或路由预测提前加载子应用资源
2. **公共依赖共享**：通过 MF shared 或 externals 避免重复加载 React、Vue 等
3. **按需加载**：子应用内部继续做路由懒加载和代码分割
4. **缓存策略**：合理设置子应用资源的 Cache-Control，使用 Content Hash
5. **减少沙箱开销**：评估是否真的需要 JS 沙箱，单实例场景可简化
6. **HTML Entry 缓存**：缓存解析后的模板和脚本列表
7. **keep-alive**：对频繁切换的子应用保持实例存活
8. **SSR 支持**：关键子应用使用服务端渲染减少白屏时间

---

### 面试题 15：如何设计一个微前端的统一登录和鉴权方案？

```javascript
// 统一登录鉴权方案
// 1. 主应用负责登录，将 token 存储在共享位置
class AuthManager {
  constructor() {
    this.tokenKey = '__MICRO_AUTH_TOKEN__';
    this.userKey = '__MICRO_USER_INFO__';
  }

  // 登录成功后存储
  setAuth(token, userInfo) {
    // 方案一：Cookie（推荐，子应用自动携带）
    document.cookie = `token=${token}; path=/; SameSite=Lax; Secure`;

    // 方案二：SharedStore
    window.__SHARED_STORE__?.setState({ token, userInfo });

    // 方案三：localStorage（同域可共享）
    localStorage.setItem(this.tokenKey, token);
    localStorage.setItem(this.userKey, JSON.stringify(userInfo));
  }

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  getUserInfo() {
    const raw = localStorage.getItem(this.userKey);
    return raw ? JSON.parse(raw) : null;
  }

  // 2. 注入 Axios 拦截器给子应用使用
  createAxiosInterceptor() {
    return {
      request: (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      responseError: (error) => {
        if (error.response?.status === 401) {
          // token 过期，统一跳转到主应用的登录页
          window.__MICRO_EVENT_BUS__?.emit('auth:expired');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      },
    };
  }

  // 3. 权限校验
  hasPermission(permission) {
    const userInfo = this.getUserInfo();
    return userInfo?.permissions?.includes(permission) ?? false;
  }

  // 4. 路由守卫 - 子应用无权限时阻止加载
  checkAppPermission(appName) {
    const appPermissionMap = {
      'admin-app': 'system:admin',
      'finance-app': 'finance:read',
      'hr-app': 'hr:read',
    };
    const requiredPermission = appPermissionMap[appName];
    return !requiredPermission || this.hasPermission(requiredPermission);
  }
}

// 主应用中使用
const authManager = new AuthManager();

// qiankun 子应用注册时注入鉴权能力
registerMicroApps(
  apps.filter(app => authManager.checkAppPermission(app.name)),
  {
    beforeMount: [
      (app) => {
        if (!authManager.getToken()) {
          window.location.href = '/login';
          return Promise.reject('未登录');
        }
      },
    ],
  }
);
```

---

### 面试题 16：手写一个简化版微前端框架的核心加载逻辑

```javascript
// 简化版微前端框架核心
class MiniMicroFrontend {
  constructor() {
    this.apps = [];
    this.currentApp = null;
  }

  // 注册子应用
  registerApp(config) {
    this.apps.push({
      ...config,
      status: 'NOT_LOADED',
      instance: null,
    });
  }

  // 启动
  async start() {
    // 监听路由变化
    window.addEventListener('popstate', () => this.reroute());
    const rawPush = history.pushState;
    history.pushState = (...args) => {
      rawPush.apply(history, args);
      this.reroute();
    };
    // 初次路由匹配
    await this.reroute();
  }

  async reroute() {
    const path = window.location.pathname;

    // 找到需要激活的应用
    const targetApp = this.apps.find(app => {
      if (typeof app.activeRule === 'function') {
        return app.activeRule(path);
      }
      return path.startsWith(app.activeRule);
    });

    // 卸载当前应用
    if (this.currentApp && this.currentApp !== targetApp) {
      await this.unmountApp(this.currentApp);
    }

    // 加载并挂载新应用
    if (targetApp) {
      if (targetApp.status === 'NOT_LOADED') {
        await this.loadApp(targetApp);
      }
      await this.mountApp(targetApp);
    }
  }

  async loadApp(app) {
    // 1. HTML Entry 加载
    const html = await fetch(app.entry).then(r => r.text());
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');

    // 2. 创建沙箱
    app.sandbox = createProxySandbox(app.name);
    app.sandbox.activate();

    // 3. 提取并执行脚本
    const scripts = doc.querySelectorAll('script[src]');
    for (const script of scripts) {
      const src = new URL(script.getAttribute('src'), app.entry).href;
      const code = await fetch(src).then(r => r.text());
      const wrapped = `(function(window,self){${code}}).call(this,this,this)`;
      new Function('window', 'self', `with(window){${code}}`).call(
        app.sandbox.proxy,
        app.sandbox.proxy,
        app.sandbox.proxy
      );
    }

    // 4. 获取导出的生命周期
    app.instance = app.sandbox.proxy.__MICRO_APP_EXPORTS__;
    app.status = 'LOADED';

    // 5. bootstrap
    await app.instance?.bootstrap?.();
  }

  async mountApp(app) {
    const container = document.querySelector(app.container);
    await app.instance?.mount?.({ container });
    app.status = 'MOUNTED';
    this.currentApp = app;
  }

  async unmountApp(app) {
    await app.instance?.unmount?.();
    const container = document.querySelector(app.container);
    if (container) container.innerHTML = '';
    app.status = 'LOADED';
    app.sandbox?.deactivate();
    this.currentApp = null;
  }
}

// 使用
const microFE = new MiniMicroFrontend();
microFE.registerApp({
  name: 'app1',
  entry: 'http://localhost:8081',
  container: '#micro-container',
  activeRule: '/app1',
});
microFE.start();
```

---

### 面试题 17：微前端架构下如何做错误监控和异常处理？

```javascript
// 全局错误监控方案
class MicroAppErrorMonitor {
  constructor() {
    this.errorMap = new Map();
    this.init();
  }

  init() {
    // 1. 捕获 JS 运行时错误
    window.addEventListener('error', (event) => {
      this.report({
        type: 'runtime_error',
        appName: this.detectAppName(event.filename),
        message: event.message,
        stack: event.error?.stack,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
      });
    });

    // 2. 捕获 Promise 未处理异常
    window.addEventListener('unhandledrejection', (event) => {
      this.report({
        type: 'unhandled_promise',
        appName: this.detectAppName(),
        message: event.reason?.message || String(event.reason),
        stack: event.reason?.stack,
      });
    });

    // 3. 捕获资源加载失败
    window.addEventListener('error', (event)=> {
      const target = event.target;
      if (target instanceof HTMLScriptElement || target instanceof HTMLLinkElement) {
        this.report({
          type: 'resource_load_error',
          appName: this.detectAppName(target.src || target.href),
          resource: target.src || target.href,
          tagName: target.tagName,
        });
      }
    }, true); // 注意用捕获阶段
  }

  detectAppName(url) {
    // 根据资源 URL 判断属于哪个子应用
    const appMap = {
      'localhost:8081': 'app1',
      'localhost:8082': 'app2',
      'cdn.example.com/app1': 'app1',
    };
    for (const [pattern, name] of Object.entries(appMap)) {
      if (url?.includes(pattern)) return name;
    }
    return 'main-app';
  }

  report(errorInfo) {
    console.error(`[${errorInfo.appName}] ${errorInfo.type}:`, errorInfo);
    // 上报到监控平台
    navigator.sendBeacon('/api/error-report', JSON.stringify({
      ...errorInfo,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    }));
  }
}
```

---

### 面试题 18：微前端选型决策的核心考量因素有哪些？

**参考答案**：

1. **团队规模与分工**：多团队独立交付选微前端，单团队选 Monorepo
2. **技术栈一致性**：技术栈统一时 MF 更轻量，多技术栈需要 qiankun/wujie 等完整方案
3. **隔离需求强度**：需要强隔离选 wujie（iframe），中等隔离选 qiankun
4. **子应用改造成本**：零改造需求选 micro-app/wujie，可接受适度改造选 qiankun/garfish
5. **构建工具链**：Webpack 项目首选 MF，Vite 项目优先考虑 micro-app/wujie
6. **性能要求**：高性能要求关注预加载、共享依赖、keep-alive 能力
7. **社区生态与维护**：qiankun 社区最大，MF 有 Webpack 官方支持
8. **子应用粒度**：页面级选传统微前端，组件级/函数级选 MF

---

## 总结：微前端技术选型速查

```
场景分析决策树:

是否需要技术栈无关？
├─ 是 → 需要完整微前端方案
│  ├─ 隔离要求强？ → wujie（iframe 沙箱）
│  ├─ 子应用零改造？ → micro-app（Web Components）
│  ├─ 生态成熟度要求高？ → qiankun（社区最大）
│  └─ 字节技术栈？ → garfish（插件化架构）
│
└─ 否（技术栈统一）
   ├─ 需要组件/函数级复用？ → Module Federation
   ├─ 团队规模小？ → Monorepo（Turborepo/Nx）
   └─ 简单集成需求？ → iframe（最简方案）
```

> **核心记忆点**：微前端不是银弹。在技术栈统一、团队规模不大的场景下，Monorepo + 组件库可能是更好的选择。微前端的价值在于解决**组织层面**的协作问题，而非纯粹的技术问题。

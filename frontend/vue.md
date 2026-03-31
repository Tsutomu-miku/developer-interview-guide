# Vue 面试指南

## 1. Vue2 与 Vue3 的核心区别

> 面试题：Vue2 和 Vue3 在响应式原理上有什么本质区别？

**Vue2 响应式原理 — Object.defineProperty**

Vue2 使用 `Object.defineProperty` 对数据对象的每个属性进行劫持，通过 getter 收集依赖，通过 setter 触发更新。

```javascript
// Vue2 响应式简化实现
function defineReactive(obj, key, val) {
  const dep = new Dep();
  Object.defineProperty(obj, key, {
    get() {
      if (Dep.target) {
        dep.depend(); // 收集依赖
      }
      return val;
    },
    set(newVal) {
      if (newVal === val) return;
      val = newVal;
      dep.notify(); // 通知更新
    }
  });
}
```

Vue2 的局限性：
- 无法检测对象属性的新增和删除（需要 `Vue.set` / `Vue.delete`）
- 无法检测数组索引和长度的变化（需要重写数组方法）
- 初始化时需要递归遍历所有属性，性能开销大

**Vue3 响应式原理 — Proxy / Reflect**

Vue3 使用 ES6 的 `Proxy` 对整个对象进行代理，配合 `Reflect` 完成操作转发。

```javascript
// Vue3 响应式简化实现
function reactive(target) {
  return new Proxy(target, {
    get(target, key, receiver) {
      track(target, key); // 依赖追踪
      const result = Reflect.get(target, key, receiver);
      if (isObject(result)) {
        return reactive(result); // 惰性递归
      }
      return result;
    },
    set(target, key, value, receiver) {
      const oldValue = target[key];
      const result = Reflect.set(target, key, value, receiver);
      if (oldValue !== value) {
        trigger(target, key); // 触发更新
      }
      return result;
    },
    deleteProperty(target, key) {
      const result = Reflect.deleteProperty(target, key);
      trigger(target, key);
      return result;
    }
  });
}
```

Vue3 的优势：
- 可以检测属性的新增、删除
- 可以检测数组索引和长度变化
- 惰性递归，只在访问时才代理嵌套对象，初始化性能更好
- 支持 Map、Set、WeakMap、WeakSet 等集合类型

**其他核心区别**

| 对比项 | Vue2 | Vue3 |
|--------|------|------|
| API 风格 | Options API | Composition API + Options API |
| 生命周期 | beforeCreate/created 等 | setup() + onMounted 等 |
| 根实例 | new Vue() | createApp() |
| Fragment | 不支持，需单根节点 | 支持多根节点 |
| Teleport | 不支持 | 内置支持 |
| Suspense | 不支持 | 实验性支持 |
| TypeScript | 支持较弱 | 原生友好 |
| Tree-shaking | 不支持 | 完全支持 |

---

## 2. 虚拟 DOM 与 Diff 算法

> 面试题：Vue 的虚拟 DOM 是什么？Diff 算法是如何工作的？

**虚拟 DOM（Virtual DOM）**

虚拟 DOM 是用 JavaScript 对象来描述真实 DOM 结构的一种抽象表示。每次状态变化时，Vue 会生成新的虚拟 DOM 树，通过 Diff 算法比较新旧两棵树的差异，最终只将必要的变更应用到真实 DOM 上。

```javascript
// VNode 结构示例
const vnode = {
  type: 'div',
  props: { id: 'app', class: 'container' },
  children: [
    { type: 'h1', props: null, children: 'Hello' },
    { type: 'p', props: null, children: 'World' }
  ]
};
```

**Vue2 Diff — 双端比较**

Vue2 采用双端比较算法，同时从新旧子节点列表的两端开始对比，共有四种比较方式：
1. 旧头 vs 新头
2. 旧尾 vs 新尾
3. 旧头 vs 新尾
4. 旧尾 vs 新头

如果四种都不匹配，则用 key 在旧节点中查找。

**Vue3 Diff — 最长递增子序列（LIS）**

Vue3 在双端比较的基础上引入了最长递增子序列（Longest Increasing Subsequence）优化：
1. 先处理前置和后置相同节点（预处理）
2. 对于中间乱序部分，建立新节点 key → index 映射
3. 计算最长递增子序列，最大限度减少 DOM 移动操作

```javascript
// LIS 核心思想：找到不需要移动的最长序列
// 假设旧序列索引为 [2, 3, 1, 5, 4]
// LIS = [2, 3, 5]，只需移动不在 LIS 中的节点
```

**为什么需要 key？**

- key 是 VNode 的唯一标识，帮助 Diff 算法准确识别节点
- 没有 key 时，Vue 使用就地复用策略，可能导致状态错乱
- 不建议用 index 作为 key，因为列表变化时 index 会变化，导致错误复用

---

## 3. Composition API

> 面试题：Composition API 相比 Options API 有什么优势？

**Options API 的问题**

```javascript
// Options API 中，同一逻辑关注点被分散到不同选项中
export default {
  data() {
    return { count: 0, user: null };
  },
  computed: {
    doubleCount() { return this.count * 2; }
  },
  methods: {
    increment() { this.count++; },
    fetchUser() { /* ... */ }
  },
  mounted() {
    this.fetchUser();
  }
};
```

**Composition API 的优势**

```javascript
// Composition API：按逻辑关注点组织代码
import { ref, computed, onMounted } from 'vue';

// 计数逻辑
function useCounter() {
  const count = ref(0);
  const doubleCount = computed(() => count.value * 2);
  const increment = () => count.value++;
  return { count, doubleCount, increment };
}

// 用户逻辑
function useUser() {
  const user = ref(null);
  const fetchUser = async () => {
    user.value = await api.getUser();
  };
  onMounted(fetchUser);
  return { user, fetchUser };
}

// 组合使用
export default {
  setup() {
    const { count, doubleCount, increment } = useCounter();
    const { user } = useUser();
    return { count, doubleCount, increment, user };
  }
};
```

核心优势：
1. **逻辑复用**：通过 composables（组合函数）替代 mixins，无命名冲突、数据来源清晰
2. **代码组织**：相关逻辑集中在一起，而非分散到 data/methods/computed 等选项中
3. **TypeScript 支持**：天然支持类型推导，无需额外声明
4. **Tree-shaking**：按需引入 API，未使用的功能不会被打包

---

## 4. 组件通信方式

> 面试题：Vue 中有哪些组件通信方式？

| 通信方式 | 适用场景 | Vue 版本 |
|----------|---------|----------|
| props / emit | 父子组件 | 2 & 3 |
| v-model | 父子双向绑定 | 2 & 3 |
| provide / inject | 跨层级组件 | 2 & 3 |
| EventBus | 任意组件 | 2（3 中需第三方库） |
| Vuex / Pinia | 全局状态管理 | 2 & 3 |
| $refs | 父访问子实例 | 2 & 3 |
| $attrs / $listeners | 属性透传 | 2（3 中合并为 $attrs）|
| expose / defineExpose | 子暴露给父 | 3 |
| slot 作用域插槽 | 子向父传递渲染数据 | 2 & 3 |

```javascript
// Vue3 provide / inject 示例
// 祖先组件
import { provide, ref } from 'vue';
const theme = ref('dark');
provide('theme', theme);

// 后代组件
import { inject } from 'vue';
const theme = inject('theme', 'light'); // 第二个参数为默认值
```

```javascript
// Vue3 defineExpose 示例
// 子组件
<script setup>
import { ref } from 'vue';
const count = ref(0);
const reset = () => { count.value = 0; };
defineExpose({ count, reset });
</script>

// 父组件
<template>
  <ChildComponent ref="childRef" />
</template>
<script setup>
import { ref, onMounted } from 'vue';
const childRef = ref(null);
onMounted(() => {
  console.log(childRef.value.count);
  childRef.value.reset();
});
</script>
```

---

## 5. 生命周期钩子

> 面试题：Vue3 的生命周期有哪些？与 Vue2 有什么对应关系？

| Vue2（Options API） | Vue3（Options API） | Vue3（Composition API） |
|---------------------|---------------------|------------------------|
| beforeCreate | beforeCreate | setup() |
| created | created | setup() |
| beforeMount | beforeMount | onBeforeMount |
| mounted | mounted | onMounted |
| beforeUpdate | beforeUpdate | onBeforeUpdate |
| updated | updated | onUpdated |
| beforeDestroy | beforeUnmount | onBeforeUnmount |
| destroyed | unmounted | onUnmounted |
| — | — | onActivated |
| — | — | onDeactivated |
| errorCaptured | errorCaptured | onErrorCaptured |

**执行顺序（父子组件）**

挂载阶段：父 beforeMount → 子 beforeMount → 子 mounted → 父 mounted

更新阶段：父 beforeUpdate → 子 beforeUpdate → 子 updated → 父 updated

卸载阶段：父 beforeUnmount → 子 beforeUnmount → 子 unmounted → 父 unmounted

---

## 6. computed、watch 与 watchEffect

> 面试题：computed、watch 和 watchEffect 有什么区别？

```javascript
import { ref, computed, watch, watchEffect } from 'vue';

const firstName = ref('张');
const lastName = ref('三');

// computed：有缓存，依赖不变不会重新计算
const fullName = computed(() => `${firstName.value}${lastName.value}`);

// watch：明确指定侦听源，可获取新旧值，默认惰性执行
watch(firstName, (newVal, oldVal) => {
  console.log(`姓从 ${oldVal} 变为 ${newVal}`);
});

// watch 侦听多个源
watch([firstName, lastName], ([newFirst, newLast], [oldFirst, oldLast]) => {
  console.log('姓名变化');
});

// watchEffect：自动收集依赖，立即执行，无法获取旧值
watchEffect(() => {
  console.log(`当前姓名：${firstName.value}${lastName.value}`);
});
```

| 特性 | computed | watch | watchEffect |
|------|----------|-------|-------------|
| 返回值 | 有（计算结果） | 无 | 无 |
| 缓存 | 有 | 无 | 无 |
| 惰性 | 是（访问时才计算） | 是（默认） | 否（立即执行） |
| 旧值 | 不提供 | 提供 | 不提供 |
| 依赖声明 | 自动 | 手动指定 | 自动收集 |

---

## 7. Vue Router

> 面试题：Vue Router 的导航守卫有哪些？路由懒加载如何实现？

**导航守卫**

```javascript
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/dashboard',
      component: () => import('./views/Dashboard.vue'), // 路由懒加载
      meta: { requiresAuth: true },
      beforeEnter: (to, from) => {
        // 路由独享守卫
        console.log('进入 dashboard 前');
      }
    }
  ]
});

// 全局前置守卫
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    next('/login');
  } else {
    next();
  }
});

// 全局后置钩子
router.afterEach((to, from) => {
  document.title = to.meta.title || '默认标题';
});
```

**完整的导航解析流程**：
1. 导航被触发
2. 在失活的组件里调用 `onBeforeRouteLeave`
3. 调用全局的 `beforeEach` 守卫
4. 在重用的组件里调用 `onBeforeRouteUpdate`
5. 在路由配置里调用 `beforeEnter`
6. 解析异步路由组件
7. 在被激活的组件里调用 `onBeforeRouteEnter`（Vue2 仅 Options API）
8. 调用全局的 `beforeResolve` 守卫
9. 导航被确认
10. 调用全局的 `afterEach` 钩子
11. 触发 DOM 更新
12. 调用 `onBeforeRouteEnter` 中 next 的回调函数（Vue2）

**hash 模式 vs history 模式**

| 特性 | hash 模式 | history 模式 |
|------|----------|-------------|
| URL 格式 | `/#/path` | `/path` |
| 原理 | hashchange 事件 | History API (pushState/replaceState) |
| 服务器配置 | 不需要 | 需要配置 fallback |
| SEO | 不友好 | 友好 |
| 兼容性 | 好 | IE10+ |

---

## 8. Pinia 状态管理

> 面试题：Pinia 与 Vuex 有什么区别？

```javascript
// Pinia Store 定义
import { defineStore } from 'pinia';

// Option Store 风格
export const useCounterStore = defineStore('counter', {
  state: () => ({ count: 0, name: 'Pinia' }),
  getters: {
    doubleCount: (state) => state.count * 2,
  },
  actions: {
    increment() {
      this.count++;
    },
    async fetchData() {
      const data = await api.getData();
      this.name = data.name;
    }
  }
});

// Setup Store 风格（推荐）
export const useCounterStore = defineStore('counter', () => {
  const count = ref(0);
  const name = ref('Pinia');
  const doubleCount = computed(() => count.value * 2);

  function increment() {
    count.value++;
  }

  return { count, name, doubleCount, increment };
});
```

| 对比项 | Vuex | Pinia |
|--------|------|-------|
| mutations | 需要 | 去掉了 |
| modules | 嵌套模块 | 扁平化 Store |
| TypeScript | 支持弱 | 完美支持 |
| 体积 | 较大 | ~1KB |
| DevTools | 支持 | 支持 |
| 代码分割 | 不支持 | 自动 |
| Composition API | 适配弱 | 原生支持 |

---

## 9. 模板编译原理

> 面试题：Vue 的模板编译过程是怎样的？

Vue 模板编译分为三个阶段：

1. **解析（Parse）**：将模板字符串解析为 AST（抽象语法树）
2. **转换/优化（Transform/Optimize）**：对 AST 进行静态标记和优化
3. **代码生成（Generate）**：将优化后的 AST 生成 render 函数代码

```javascript
// 模板
// <div id="app">
//   <p>{{ message }}</p>
//   <span>静态文本</span>
// </div>

// 编译后的 render 函数（简化）
function render(_ctx) {
  return h('div', { id: 'app' }, [
    h('p', null, _ctx.message),    // 动态节点
    h('span', null, '静态文本')     // 静态节点，会被提升
  ]);
}
```

---

## 10. keep-alive 缓存

> 面试题：keep-alive 的原理是什么？如何控制缓存？

`keep-alive` 是 Vue 内置的抽象组件，用于缓存不活跃的组件实例而不是销毁它们。

```html
<template>
  <!-- 基础用法 -->
  <keep-alive>
    <component :is="currentComponent" />
  </keep-alive>

  <!-- include / exclude 控制 -->
  <keep-alive :include="['ComponentA', 'ComponentB']" :exclude="['ComponentC']" :max="10">
    <router-view />
  </keep-alive>
</template>

<script setup>
import { onActivated, onDeactivated } from 'vue';

// 缓存组件特有的生命周期
onActivated(() => {
  console.log('组件被激活（从缓存恢复）');
});

onDeactivated(() => {
  console.log('组件被停用（进入缓存）');
});
</script>
```

**缓存策略 — LRU（最近最少使用）**

`keep-alive` 内部使用 LRU 缓存策略。当缓存数量超过 `max` 限制时，会销毁最近最久未使用的组件实例。

---

## 11. nextTick 原理

> 面试题：Vue.nextTick 的实现原理是什么？

`nextTick` 用于在下次 DOM 更新循环结束之后执行延迟回调。Vue 的响应式更新是异步的，数据变化后 DOM 不会立即更新，而是将更新放入队列，在同一事件循环的微任务阶段统一执行。

```javascript
import { ref, nextTick } from 'vue';

const count = ref(0);

async function increment() {
  count.value++;
  // DOM 尚未更新
  console.log(document.getElementById('count').textContent); // 旧值

  await nextTick();
  // DOM 已更新
  console.log(document.getElementById('count').textContent); // 新值
}
```

**nextTick 的降级策略**（Vue2）：
1. `Promise.then`（微任务）
2. `MutationObserver`（微任务）
3. `setImmediate`（宏任务，仅 IE/Node）
4. `setTimeout(fn, 0)`（宏任务，兜底）

Vue3 中统一使用 `Promise.then` 实现。

---

## 12. Vue3 编译优化

> 面试题：Vue3 做了哪些编译优化？

**1. 静态提升（Static Hoisting）**

将静态节点提升到 render 函数之外，避免每次渲染重复创建。

```javascript
// 编译前
// <div>
//   <p>静态内容</p>
//   <p>{{ dynamic }}</p>
// </div>

// 编译后（静态节点被提升）
const _hoisted_1 = h('p', null, '静态内容');

function render(_ctx) {
  return h('div', null, [
    _hoisted_1,  // 复用，不重新创建
    h('p', null, _ctx.dynamic)
  ]);
}
```

**2. PatchFlags（补丁标记）**

为动态节点添加标记，Diff 时只比较有标记的部分。

```javascript
// PatchFlags 枚举（部分）
const PatchFlags = {
  TEXT: 1,         // 动态文本
  CLASS: 2,        // 动态 class
  STYLE: 4,        // 动态 style
  PROPS: 8,        // 动态 props
  FULL_PROPS: 16,  // 带有动态 key 的 props
  NEED_HYDRATION: 32,
  STABLE_FRAGMENT: 64,
};
```

**3. Block Tree（块树）**

将模板按照动态节点分块，配合 PatchFlags，在 Diff 时跳过整个静态子树，只对比动态节点数组。

**4. 缓存事件处理函数**

```javascript
// 编译前
// <button @click="handleClick">点击</button>

// 编译后：事件处理函数被缓存
render(_ctx, _cache) {
  return h('button', {
    onClick: _cache[0] || (_cache[0] = (...args) => _ctx.handleClick(...args))
  }, '点击');
}
```

---

## 13. Nuxt.js

> 面试题：Nuxt.js 的渲染模式有哪些？

Nuxt.js 是基于 Vue 的全栈框架，主要特性：

| 渲染模式 | 说明 |
|---------|------|
| SSR（服务端渲染） | 每次请求在服务端渲染 HTML，首屏快、SEO 友好 |
| SSG（静态站点生成） | 构建时预渲染所有页面为静态 HTML |
| SPA（单页应用） | 纯客户端渲染，传统 Vue 应用模式 |
| ISR（增量静态再生） | 结合 SSG 和 SSR，静态页面可按需更新 |
| Hybrid（混合渲染） | 不同路由使用不同的渲染策略 |

```javascript
// nuxt.config.ts
export default defineNuxtConfig({
  // 全局 SSR
  ssr: true,
  // 路由级别配置
  routeRules: {
    '/': { prerender: true },        // SSG
    '/blog/**': { isr: 3600 },       // ISR，每小时更新
    '/admin/**': { ssr: false },     // SPA
    '/api/**': { cors: true }        // API 路由
  }
});
```

Nuxt3 核心特性：
- 基于 Vue3 + Vite，支持 TypeScript
- 文件系统路由（pages 目录自动生成路由）
- 自动导入（组件、composables、工具函数）
- 服务端引擎 Nitro（支持部署到各种平台）
- 中间件系统（全局、路由级别）
- 数据获取（useFetch、useAsyncData）

---

## 14. 常见性能优化技巧

> 面试题：在 Vue 项目中你做过哪些性能优化？

1. **路由懒加载**：`component: () => import('./views/Page.vue')`
2. **组件异步加载**：`defineAsyncComponent(() => import('./Heavy.vue'))`
3. **v-show vs v-if**：频繁切换用 v-show，条件不常变用 v-if
4. **v-once**：只渲染一次的静态内容
5. **v-memo**：缓存子树，依赖不变时跳过更新
6. **keep-alive**：缓存组件实例
7. **computed 缓存**：避免模板中调用方法计算
8. **大列表虚拟滚动**：使用 vue-virtual-scroller
9. **事件销毁**：在 onUnmounted 中移除全局事件监听
10. **shallowRef / shallowReactive**：大数据对象避免深层响应式
11. **合理使用 key**：帮助 Diff 精确识别节点
12. **图片懒加载**：v-lazy 或 IntersectionObserver

# 前端性能优化面试指南

## 1. Web Vitals 核心指标

> 面试题：什么是 Core Web Vitals？各指标的含义和标准是什么？

**Core Web Vitals（核心 Web 指标）**

| 指标 | 全称 | 含义 | 良好 | 需改进 | 差 |
|------|------|------|------|--------|---|
| LCP | Largest Contentful Paint | 最大内容绘制，衡量加载性能 | ≤ 2.5s | ≤ 4.0s | > 4.0s |
| FID | First Input Delay | 首次输入延迟，衡量交互性 | ≤ 100ms | ≤ 300ms | > 300ms |
| CLS | Cumulative Layout Shift | 累计布局偏移，衡量视觉稳定性 | ≤ 0.1 | ≤ 0.25 | > 0.25 |
| INP | Interaction to Next Paint | 交互到下次绘制，FID 的替代指标 | ≤ 200ms | ≤ 500ms | > 500ms |

**其他关键性能指标**

| 指标 | 全称 | 含义 |
|------|------|------|
| FCP | First Contentful Paint | 首次内容绘制，页面首个内容元素渲染的时间 |
| TTFB | Time to First Byte | 首字节时间，从请求到收到第一个字节 |
| TTI | Time to Interactive | 可交互时间，页面完全可交互的时间 |
| TBT | Total Blocking Time | 总阻塞时间，FCP 到 TTI 之间长任务的阻塞总时长 |
| FMP | First Meaningful Paint | 首次有意义绘制（已弃用，被 LCP 替代） |

**指标采集**

```javascript
// 使用 web-vitals 库采集
import { onLCP, onFID, onCLS, onINP, onFCP, onTTFB } from 'web-vitals';

function reportMetric(metric) {
  console.log(metric.name, metric.value, metric.rating);
  // 上报到监控平台
  navigator.sendBeacon('/analytics', JSON.stringify(metric));
}

onLCP(reportMetric);
onFID(reportMetric);
onCLS(reportMetric);
onINP(reportMetric);
onFCP(reportMetric);
onTTFB(reportMetric);
```

```javascript
// 使用 PerformanceObserver 原生采集 LCP
const observer = new PerformanceObserver((entryList) => {
  const entries = entryList.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.startTime);
});
observer.observe({ type: 'largest-contentful-paint', buffered: true });
```

---

## 2. Lighthouse 性能审计

> 面试题：Lighthouse 的性能评分包含哪些指标？如何优化评分？

**Lighthouse 性能评分权重（v10+）**

| 指标 | 权重 |
|------|------|
| FCP（First Contentful Paint） | 10% |
| SI（Speed Index） | 10% |
| LCP（Largest Contentful Paint） | 25% |
| TBT（Total Blocking Time） | 30% |
| CLS（Cumulative Layout Shift） | 25% |

**常用优化建议**

1. **减少未使用的 JavaScript**：代码分割、Tree-shaking、按需加载
2. **减少未使用的 CSS**：PurgeCSS、CSS-in-JS 按需生成
3. **消除阻塞渲染的资源**：defer/async 加载 JS，关键 CSS 内联
4. **适当调整图片大小**：响应式图片、WebP/AVIF 格式
5. **预连接所需源**：`<link rel="preconnect">`、`<link rel="dns-prefetch">`

---

## 3. 加载性能优化

> 面试题：如何优化页面的加载性能？

**资源加载策略**

```html
<!-- 预加载关键资源 -->
<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/css/critical.css" as="style">

<!-- 预连接第三方域名 -->
<link rel="preconnect" href="https://cdn.example.com">
<link rel="dns-prefetch" href="https://analytics.example.com">

<!-- 预获取下一页资源 -->
<link rel="prefetch" href="/next-page.js">

<!-- 脚本加载策略 -->
<script src="critical.js"></script>                    <!-- 同步，阻塞渲染 -->
<script src="non-critical.js" defer></script>          <!-- 延迟，DOMContentLoaded 前执行 -->
<script src="analytics.js" async></script>             <!-- 异步，下载完立即执行 -->
<script type="module" src="app.js"></script>           <!-- 模块，天然 defer -->
```

**代码分割**

```javascript
// 路由懒加载
const routes = [
  {
    path: '/dashboard',
    component: () => import(
      /* webpackChunkName: "dashboard" */
      /* webpackPrefetch: true */
      './views/Dashboard.vue'
    ),
  },
];

// 组件懒加载
import { defineAsyncComponent } from 'vue';
const HeavyChart = defineAsyncComponent({
  loader: () => import('./components/HeavyChart.vue'),
  loadingComponent: LoadingSpinner,
  delay: 200,
  timeout: 10000,
});
```

**图片懒加载**

```javascript
// 原生懒加载
// <img src="photo.jpg" loading="lazy" alt="描述">

// IntersectionObserver 实现
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      observer.unobserve(img);
    }
  });
}, {
  rootMargin: '200px 0px', // 提前 200px 开始加载
});

document.querySelectorAll('img[data-src]').forEach((img) => {
  observer.observe(img);
});
```

---

## 4. 渲染性能优化

> 面试题：浏览器渲染流程是怎样的？如何避免回流和重绘？

**浏览器渲染流程（关键渲染路径）**

```
HTML → DOM 树
              → Render 树 → Layout（布局） → Paint（绘制） → Composite（合成）
CSS  → CSSOM
```

**回流（Reflow/Layout）与重绘（Repaint）**

| 类型 | 触发条件 | 性能影响 |
|------|---------|---------|  
| 回流 | 改变几何属性（尺寸、位置、显示状态） | 高（需重新计算布局） |
| 重绘 | 改变外观属性（颜色、背景、阴影） | 中（无需重新布局） |

**回流一定会触发重绘，重绘不一定触发回流。**

**优化策略**

```javascript
// 1. 批量 DOM 操作 — 使用 DocumentFragment
const fragment = document.createDocumentFragment();
for (let i = 0; i < 1000; i++) {
  const li = document.createElement('li');
  li.textContent = `Item ${i}`;
  fragment.appendChild(li);
}
document.getElementById('list').appendChild(fragment);

// 2. 批量样式修改 — 使用 class 或 cssText
element.className = 'new-class'; // 好：一次回流
// 避免逐条修改样式属性

// 3. 读写分离 — 避免强制同步布局
// 不好：读写交替导致多次回流
for (let i = 0; i < items.length; i++) {
  items[i].style.width = container.offsetWidth + 'px'; // 每次读都触发回流
}
// 好：先读后写
const width = container.offsetWidth; // 读一次
for (let i = 0; i < items.length; i++) {
  items[i].style.width = width + 'px'; // 只写
}

// 4. 使用 transform 替代 top/left（触发合成，跳过布局和绘制）
// 不好
element.style.left = newX + 'px';
// 好
element.style.transform = `translateX(${newX}px)`;

// 5. 使用 will-change 提示浏览器优化
.animated-element {
  will-change: transform, opacity;
}
```

**使用 requestAnimationFrame 优化动画**

```javascript
function animate() {
  // 在下一帧执行动画
  element.style.transform = `translateX(${position}px)`;
  position += speed;

  if (position < target) {
    requestAnimationFrame(animate);
  }
}
requestAnimationFrame(animate);
```

---

## 5. 图片优化

> 面试题：前端图片优化有哪些策略？

**图片格式选择**

| 格式 | 特点 | 适用场景 |
|------|------|---------|  
| JPEG/JPG | 有损压缩，文件小 | 照片、渐变丰富的图 |
| PNG | 无损压缩，支持透明 | 图标、需要透明的图 |
| WebP | 比 JPEG/PNG 更小，支持透明和动画 | 现代浏览器的通用选择 |
| AVIF | 比 WebP 更小，压缩率最高 | 最新浏览器，兼顾质量和体积 |
| SVG | 矢量，不失真，可编程 | 图标、简单图形 |

**响应式图片**

```html
<!-- srcset + sizes -->
<img
  src="photo-800w.jpg"
  srcset="
    photo-400w.jpg 400w,
    photo-800w.jpg 800w,
    photo-1200w.jpg 1200w
  "
  sizes="
    (max-width: 480px) 400px,
    (max-width: 960px) 800px,
    1200px
  "
  alt="响应式图片"
  loading="lazy"
>

<!-- picture 元素：格式协商 -->
<picture>
  <source srcset="photo.avif" type="image/avif">
  <source srcset="photo.webp" type="image/webp">
  <img src="photo.jpg" alt="多格式图片" loading="lazy">
</picture>
```

**其他图片优化手段**

1. **压缩**：使用 tinypng、imagemin 等工具压缩
2. **CDN 图片处理**：动态裁剪、格式转换、质量调整
3. **雪碧图/CSS Sprites**：合并小图标减少请求（现在更推荐 SVG Sprite 或 Icon Font）
4. **Base64 内联**：小于 4-8KB 的图片转为 Base64 内联到代码中
5. **渐进式加载**：先加载模糊缩略图，再加载原图（如 BlurHash）

---

## 6. 缓存策略

> 面试题：浏览器缓存机制有哪些？强缓存和协商缓存的区别？

**缓存优先级：Service Worker → Memory Cache → Disk Cache → 网络请求**

**强缓存（不发请求）**

| 头部 | 说明 |
|------|------|
| `Cache-Control: max-age=31536000` | 资源有效期（秒），优先级高 |
| `Cache-Control: no-cache` | 每次都需要协商验证 |
| `Cache-Control: no-store` | 完全不缓存 |
| `Expires: Wed, 09 Jun 2027 10:18:14 GMT` | 过期时间（绝对时间），优先级低于 Cache-Control |

**协商缓存（发请求验证）**

| 请求头 | 响应头 | 机制 |
|--------|--------|------|
| `If-None-Match` | `ETag` | 资源内容的哈希值 |
| `If-Modified-Since` | `Last-Modified` | 资源最后修改时间 |

命中协商缓存返回 **304 Not Modified**，未命中返回 **200** 和新资源。

**前端缓存最佳实践**

```
HTML 文件        → Cache-Control: no-cache（每次协商验证）
JS/CSS（带hash） → Cache-Control: max-age=31536000（一年强缓存）
API 数据         → Cache-Control: no-cache 或 max-age=0
字体文件         → Cache-Control: max-age=31536000
图片（带hash）   → Cache-Control: max-age=31536000
```

**Service Worker 缓存**

```javascript
// sw.js
const CACHE_NAME = 'app-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/main.css',
  '/js/app.js',
];

// 安装：预缓存静态资源
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

// 激活：清理旧缓存
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
});

// 拦截请求：Cache First 策略
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        return response;
      });
    })
  );
});
```

**常见缓存策略模式**

| 策略 | 说明 | 适用场景 |
|------|------|---------|  
| Cache First | 优先缓存，缓存无则网络 | 静态资源 |
| Network First | 优先网络，失败则缓存 | API 数据 |
| Stale While Revalidate | 先返回缓存，同时后台更新 | 频繁更新的非关键资源 |
| Cache Only | 只用缓存 | 离线资源 |
| Network Only | 只用网络 | 实时数据 |

---

## 7. 首屏优化

> 面试题：如何优化首屏加载速度？

**首屏优化清单**

1. **关键渲染路径优化**
   - 内联关键 CSS（Critical CSS），异步加载非关键 CSS
   - JS 加入 defer/async，避免阻塞渲染
   - 减少关键资源数量和大小

2. **资源体积优化**
   - Gzip / Brotli 压缩（Brotli 压缩率更高）
   - 代码分割，首屏只加载必要代码
   - Tree-shaking 去除无用代码
   - 图片压缩 + WebP/AVIF 格式

3. **网络优化**
   - CDN 加速静态资源分发
   - HTTP/2 多路复用
   - 资源预加载（preload）和预连接（preconnect）
   - DNS 预解析（dns-prefetch）

4. **渲染优化**
   - SSR/SSG 服务端渲染
   - 骨架屏（Skeleton Screen）占位
   - 首屏内容优先渲染，非首屏懒加载
   - 字体加载优化（font-display: swap）

```html
<!-- 关键 CSS 内联 + 非关键 CSS 异步 -->
<style>
  /* 首屏关键样式内联 */
  body { margin: 0; font-family: sans-serif; }
  .header { height: 64px; background: #1a1a2e; }
  .hero { min-height: 400px; }
</style>
<link rel="preload" href="/css/full.css" as="style" onload="this.onload=null;this.rel='stylesheet'">

<!-- 骨架屏 -->
<div id="app">
  <div class="skeleton">
    <div class="skeleton-header"></div>
    <div class="skeleton-content">
      <div class="skeleton-line"></div>
      <div class="skeleton-line short"></div>
    </div>
  </div>
</div>
```

---

## 8. 虚拟滚动

> 面试题：大数据量列表如何优化渲染性能？虚拟滚动的原理是什么？

**虚拟滚动原理**

虚拟滚动的核心思想是只渲染可视区域内的列表项，而不是渲染全部数据。通过监听滚动事件，动态计算当前应该渲染哪些数据项。

```javascript
// 虚拟滚动核心实现
class VirtualScroller {
  constructor({ container, itemHeight, totalItems, renderItem }) {
    this.container = container;
    this.itemHeight = itemHeight;
    this.totalItems = totalItems;
    this.renderItem = renderItem;
    this.visibleCount = Math.ceil(container.clientHeight / itemHeight);
    this.bufferSize = 5; // 上下缓冲区

    // 总高度占位
    this.phantom = document.createElement('div');
    this.phantom.style.height = `${totalItems * itemHeight}px`;
    container.appendChild(this.phantom);

    // 内容容器
    this.content = document.createElement('div');
    container.appendChild(this.content);

    container.addEventListener('scroll', () => this.onScroll());
    this.onScroll();
  }

  onScroll() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.max(0, Math.floor(scrollTop / this.itemHeight) - this.bufferSize);
    const endIndex = Math.min(
      this.totalItems,
      startIndex + this.visibleCount + 2 * this.bufferSize
    );

    // 偏移内容容器
    this.content.style.transform = `translateY(${startIndex * this.itemHeight}px)`;

    // 只渲染可视区域 + 缓冲区的项目
    this.content.innerHTML = '';
    for (let i = startIndex; i < endIndex; i++) {
      const item = this.renderItem(i);
      item.style.height = `${this.itemHeight}px`;
      this.content.appendChild(item);
    }
  }
}
```

**Vue 中使用虚拟滚动**

```html
<!-- 使用 vue-virtual-scroller -->
<template>
  <RecycleScroller
    class="scroller"
    :items="items"
    :item-size="50"
    key-field="id"
    v-slot="{ item }"
  >
    <div class="item">{{ item.name }}</div>
  </RecycleScroller>
</template>
```

**不定高度虚拟滚动**

处理不定高度的列表项更复杂，通常需要：
1. 预估每项高度
2. 渲染后测量实际高度并缓存
3. 动态更新总高度和偏移量
4. 使用二分查找快速定位 scrollTop 对应的起始索引

---

## 9. 内存泄漏检测与治理

> 面试题：前端常见的内存泄漏有哪些？如何检测和修复？

**常见内存泄漏场景**

```javascript
// 1. 未清除的定时器
export default {
  mounted() {
    this.timer = setInterval(() => {
      this.fetchData();
    }, 5000);
  },
  // 修复：组件卸载时清除
  unmounted() {
    clearInterval(this.timer);
  }
};

// 2. 未移除的事件监听
function setupListener() {
  const handler = () => { /* 处理逻辑 */ };
  window.addEventListener('resize', handler);

  // 修复：返回清理函数
  return () => window.removeEventListener('resize', handler);
}

// 3. 闭包引用 DOM
function setupClickHandler() {
  const element = document.getElementById('huge-data');
  const data = element.innerHTML; // 大量数据

  element.addEventListener('click', () => {
    // 闭包引用了 element 和 data，即使 element 从 DOM 移除也不会被回收
    console.log(data.length);
  });
}

// 4. 未清理的全局变量和 Map/Set
const cache = new Map();
function processData(key, value) {
  cache.set(key, value); // 只增不减，内存不断增长
}
// 修复：使用 WeakMap 或设置清理策略
const cache2 = new WeakMap(); // key 被回收时自动清理

// 5. console.log 保留对象引用（开发环境）
console.log(largeObject); // DevTools 保持引用，对象无法被 GC

// 6. 未取消的 AbortController
const controller = new AbortController();
fetch('/api/data', { signal: controller.signal });
// 组件卸载时应调用 controller.abort()
```

**Vue3 中的最佳实践**

```javascript
import { onMounted, onUnmounted, ref } from 'vue';

function useEventListener(target, event, handler) {
  onMounted(() => target.addEventListener(event, handler));
  onUnmounted(() => target.removeEventListener(event, handler));
}

function useInterval(callback, delay) {
  const id = ref(null);
  onMounted(() => {
    id.value = setInterval(callback, delay);
  });
  onUnmounted(() => {
    if (id.value) clearInterval(id.value);
  });
}
```

**Chrome DevTools 检测内存泄漏**

1. **Memory 面板 → Heap Snapshot**
   - 拍摄快照 A → 执行操作 → 拍摄快照 B
   - 对比两个快照，查看 Detached DOM 节点和增长的对象
   - 筛选 "Objects allocated between Snapshot 1 and Snapshot 2"

2. **Memory 面板 → Allocation Timeline**
   - 实时记录内存分配情况
   - 蓝色条表示仍然存活的分配，灰色表示已被 GC

3. **Performance Monitor**
   - 实时监控 JS Heap Size、DOM Nodes 数量
   - 如果随时间持续增长且不回落，说明存在泄漏

4. **Performance 面板录制**
   - 录制一段时间的性能数据
   - 查看 JS Heap 曲线是否持续上升

---

## 10. 网络请求优化

> 面试题：如何优化前端的网络请求？

**HTTP/2 优化**

HTTP/2 核心特性：
- **多路复用**：一个 TCP 连接上并行多个请求
- **头部压缩**：HPACK 算法压缩 HTTP 头
- **服务器推送**：服务器主动推送资源
- **二进制分帧**：更高效的数据传输

HTTP/2 环境下需要调整的优化策略：
- 不再需要域名分片（sharding）
- 不再需要合并 JS/CSS 文件（多路复用已解决）
- 小文件不需要内联（HTTP/2 请求开销很小）
- 仍然需要代码分割和压缩

**请求优化策略**

```javascript
// 1. 请求去重 — 相同请求只发一次
const pendingRequests = new Map();

async function dedupedFetch(url, options) {
  const key = `${url}-${JSON.stringify(options)}`;
  if (pendingRequests.has(key)) {
    return pendingRequests.get(key);
  }
  const promise = fetch(url, options).finally(() => {
    pendingRequests.delete(key);
  });
  pendingRequests.set(key, promise);
  return promise;
}

// 2. 请求取消
const controller = new AbortController();
fetch('/api/search?q=keyword', { signal: controller.signal });
// 用户输入变化时取消上一次请求
controller.abort();

// 3. 请求并发控制
async function concurrentFetch(urls, maxConcurrency = 5) {
  const results = [];
  const executing = new Set();

  for (const url of urls) {
    const promise = fetch(url).then((res) => res.json());
    results.push(promise);
    executing.add(promise);
    promise.finally(() => executing.delete(promise));

    if (executing.size >= maxConcurrency) {
      await Promise.race(executing);
    }
  }
  return Promise.all(results);
}

// 4. 接口数据缓存
const apiCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 分钟

async function cachedFetch(url) {
  const cached = apiCache.get(url);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  const data = await fetch(url).then((r) => r.json());
  apiCache.set(url, { data, timestamp: Date.now() });
  return data;
}
```

**数据传输优化**

1. **Gzip/Brotli 压缩**：服务端开启压缩，Brotli 压缩率比 Gzip 高 15-25%
2. **GraphQL**：按需请求字段，避免 over-fetching
3. **分页和增量加载**：大数据集分页返回
4. **WebSocket**：实时场景使用长连接替代轮询
5. **合并请求**：将多个小请求合并为一个批量请求

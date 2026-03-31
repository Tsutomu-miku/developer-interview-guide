# 移动端H5开发

> 本指南系统覆盖移动端H5开发的核心知识体系，包含适配方案、事件交互、Hybrid开发、小程序、跨端框架、性能优化及高频面试题，适合中高级前端面试准备。

---

## 一、移动端适配

### 1.1 Viewport 视口

移动端开发首先需要理解三个视口概念：

- **布局视口（Layout Viewport）**：浏览器默认的视口宽度，通常为 980px
- **视觉视口（Visual Viewport）**：用户当前看到的区域大小
- **理想视口（Ideal Viewport）**：设备屏幕的宽度

标准 viewport 设置：

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no, viewport-fit=cover">
```

各属性说明：

| 属性 | 说明 | 常用值 |
|------|------|--------|
| `width` | 视口宽度 | `device-width` |
| `initial-scale` | 初始缩放比例 | `1.0` |
| `maximum-scale` | 最大缩放比例 | `1.0` |
| `minimum-scale` | 最小缩放比例 | `1.0` |
| `user-scalable` | 是否允许用户缩放 | `no` |
| `viewport-fit` | 视口填充方式（刘海屏） | `cover` |

动态设置 viewport 实现缩放适配：

```javascript
(function () {
  const dpr = window.devicePixelRatio || 1;
  const scale = 1 / dpr;
  const metaEl = document.querySelector('meta[name="viewport"]');

  if (!metaEl) {
    const meta = document.createElement('meta');
    meta.setAttribute('name', 'viewport');
    meta.setAttribute('content',
      `width=device-width, initial-scale=${scale}, maximum-scale=${scale}, minimum-scale=${scale}, user-scalable=no`
    );
    document.head.appendChild(meta);
  }

  // 在 html 标签上设置 data-dpr 属性
  document.documentElement.setAttribute('data-dpr', dpr);
})();
```

### 1.2 rem 适配方案（flexible.js）

rem 方案的核心思想：根据屏幕宽度动态设置根元素 `font-size`，使所有使用 rem 单位的尺寸随之缩放。

**flexible.js 核心原理：**

```javascript
// 简化版 flexible.js 实现
(function flexible(window, document) {
  const docEl = document.documentElement;
  const dpr = window.devicePixelRatio || 1;

  // 设置 body 字体大小
  function setBodyFontSize() {
    if (document.body) {
      document.body.style.fontSize = 12 * dpr + 'px';
    } else {
      document.addEventListener('DOMContentLoaded', setBodyFontSize);
    }
  }
  setBodyFontSize();

  // 设置 1rem = viewWidth / 10
  function setRemUnit() {
    const rem = docEl.clientWidth / 10;
    docEl.style.fontSize = rem + 'px';
  }
  setRemUnit();

  // 监听 resize 和 pageshow 事件
  window.addEventListener('resize', setRemUnit);
  window.addEventListener('pageshow', function (e) {
    if (e.persisted) {
      setRemUnit();
    }
  });

  // 检测是否支持 0.5px 边框
  if (dpr >= 2) {
    const fakeBody = document.createElement('body');
    const testElement = document.createElement('div');
    testElement.style.border = '.5px solid transparent';
    fakeBody.appendChild(testElement);
    docEl.appendChild(fakeBody);
    if (testElement.offsetHeight === 1) {
      docEl.classList.add('hairlines');
    }
    docEl.removeChild(fakeBody);
  }
})(window, document);
```

**px 转 rem 的工具函数：**

```scss
// SCSS mixin - 设计稿宽度 750px
$designWidth: 750;

@function px2rem($px) {
  @return ($px / $designWidth * 10) * 1rem;
}

// 使用示例
.header {
  height: px2rem(88);       // 88px -> 对应 rem 值
  font-size: px2rem(28);    // 28px -> 对应 rem 值
  padding: px2rem(20) px2rem(30);
}
```

### 1.3 vw/vh 适配方案

vw/vh 方案相比 rem 方案无需 JavaScript，纯 CSS 即可实现：

```css
/* 设计稿宽度 750px，1vw = 7.5px */
/* 转换公式：目标值 / 7.5 = vw值 */

.container {
  width: 100vw;
  padding: 2.667vw;          /* 20 / 7.5 */
  font-size: 3.733vw;        /* 28 / 7.5 */
}

.banner {
  width: 100vw;
  height: 26.667vw;          /* 200 / 7.5 */
}

/* 结合 calc() 实现更灵活的布局 */
.content {
  width: calc(100vw - 5.333vw);   /* 100vw - 40px */
  min-height: calc(100vh - 13.333vw);
}
```

**PostCSS 插件 postcss-px-to-viewport 配置：**

```javascript
// postcss.config.js
module.exports = {
  plugins: {
    'postcss-px-to-viewport': {
      unitToConvert: 'px',        // 需要转换的单位
      viewportWidth: 750,         // 设计稿宽度
      unitPrecision: 5,           // 精确到小数点后几位
      propList: ['*'],            // 需要转换的属性列表
      viewportUnit: 'vw',         // 转换后的单位
      fontViewportUnit: 'vw',     // 字体使用的视口单位
      selectorBlackList: ['.ignore-'], // 不进行转换的选择器
      minPixelValue: 1,           // 最小转换值
      mediaQuery: false,          // 是否在媒体查询中也转换
      replace: true,              // 是否直接替换属性值
      exclude: [/node_modules/],  // 排除的文件
      include: undefined,
      landscape: false,           // 是否添加横屏媒体查询
      landscapeUnit: 'vw',
      landscapeWidth: 1334
    }
  }
};
```

### 1.4 postcss-pxtorem 配置

```javascript
// postcss.config.js
module.exports = {
  plugins: {
    'postcss-pxtorem': {
      rootValue: 75,               // 根字体大小（设计稿750 / 10）
      unitPrecision: 5,            // 精度
      propList: [
        '*',                       // 所有属性都转换
        '!border',                 // 排除 border
        '!border-width'            // 排除 border-width
      ],
      selectorBlackList: [
        '.norem-',                 // 以 .norem- 开头的选择器不转换
        ':root'
      ],
      replace: true,
      mediaQuery: false,
      minPixelValue: 2,            // 小于 2px 不转换
      exclude: /node_modules/i
    }
  }
};
```

**配合 amfe-flexible 使用的完整方案：**

```javascript
// main.js
import 'amfe-flexible';

// 或者自定义设置
(function () {
  const baseSize = 75; // 与 postcss-pxtorem 的 rootValue 保持一致
  function setRem() {
    const scale = document.documentElement.clientWidth / 750;
    document.documentElement.style.fontSize =
      baseSize * Math.min(scale, 2) + 'px';
  }
  setRem();
  window.addEventListener('resize', setRem);
})();
```

### 1.5 1px 问题（5种方案）

在 Retina 屏幕上，CSS 中的 1px 会被渲染成物理像素 2px 或 3px，导致边框看起来过粗。

**方案一：伪元素 + transform（推荐）**

```css
/* 通用 1px 边框方案 */
.border-1px {
  position: relative;
}

.border-1px::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 1px;
  background-color: #e5e5e5;
  transform: scaleY(0.5);
  transform-origin: 0 0;
}

/* 四边边框 */
.border-1px-all {
  position: relative;
}

.border-1px-all::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 200%;
  height: 200%;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  transform: scale(0.5);
  transform-origin: 0 0;
  box-sizing: border-box;
  pointer-events: none;
}

/* 根据 DPR 动态调整 */
@media (-webkit-min-device-pixel-ratio: 2), (min-resolution: 2dppx) {
  .border-1px::after {
    transform: scaleY(0.5);
  }
}

@media (-webkit-min-device-pixel-ratio: 3), (min-resolution: 3dppx) {
  .border-1px::after {
    transform: scaleY(0.333);
  }
}
```

**方案二：viewport + rem（动态缩放）**

```javascript
// 根据 dpr 设置 viewport 的 scale
const dpr = window.devicePixelRatio || 1;
const scale = 1 / dpr;
const viewport = document.querySelector('meta[name="viewport"]');
viewport.setAttribute('content',
  `width=device-width, initial-scale=${scale}, maximum-scale=${scale}, minimum-scale=${scale}`
);

// 此方案下直接写 1px 即可
// CSS 中的 1px 会被缩放到物理像素的 1px
```

**方案三：border-image**

```css
.border-image-1px {
  border-width: 0 0 1px 0;
  border-style: solid;
  border-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='1' height='1'><rect width='1' height='0.5' fill='%23e5e5e5'/></svg>") 0 0 1 0 stretch;
}
```

**方案四：box-shadow 模拟**

```css
.box-shadow-1px {
  box-shadow: inset 0px -1px 1px -1px #e5e5e5;
}

/* 四边 */
.box-shadow-1px-all {
  box-shadow:
    inset 0 1px 1px -1px #e5e5e5,
    inset 0 -1px 1px -1px #e5e5e5,
    inset 1px 0 1px -1px #e5e5e5,
    inset -1px 0 1px -1px #e5e5e5;
}
```

**方案五：SVG 背景图**

```css
.svg-1px {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100%25' height='1'%3E%3Crect width='100%25' height='0.5' fill='%23e5e5e5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: bottom;
}
```

### 1.6 安全区域适配（env() / constant()）

针对 iPhone X 及以上机型的刘海屏和底部 Home Indicator 区域适配：

```css
/* 安全区域适配 - 必须设置 viewport-fit=cover */

/* 底部固定导航栏适配 */
.fixed-bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50px;
  background: #fff;

  /* 兼容 iOS 11.0-11.2 */
  padding-bottom: constant(safe-area-inset-bottom);
  /* 兼容 iOS 11.2+ */
  padding-bottom: env(safe-area-inset-bottom);
}

/* 使用 calc() 结合安全区域 */
.safe-area-container {
  padding-top: calc(12px + constant(safe-area-inset-top));
  padding-top: calc(12px + env(safe-area-inset-top));
  padding-bottom: calc(12px + constant(safe-area-inset-bottom));
  padding-bottom: calc(12px + env(safe-area-inset-bottom));
  padding-left: calc(12px + constant(safe-area-inset-left));
  padding-left: calc(12px + env(safe-area-inset-left));
  padding-right: calc(12px + constant(safe-area-inset-right));
  padding-right: calc(12px + env(safe-area-inset-right));
}

/* 底部安全区域占位 */
.safe-area-placeholder {
  height: constant(safe-area-inset-bottom);
  height: env(safe-area-inset-bottom);
}

/* 全面屏适配的通用方案 */
@supports (bottom: env(safe-area-inset-bottom)) {
  .fullscreen-adaptive {
    padding-bottom: env(safe-area-inset-bottom);
  }
}
```

**JavaScript 获取安全区域：**

```javascript
// 获取安全区域数值
function getSafeAreaInsets() {
  const div = document.createElement('div');
  div.style.cssText = `
    position: fixed;
    top: env(safe-area-inset-top);
    left: env(safe-area-inset-left);
    right: env(safe-area-inset-right);
    bottom: env(safe-area-inset-bottom);
    pointer-events: none;
    visibility: hidden;
  `;
  document.body.appendChild(div);
  const rect = div.getBoundingClientRect();
  document.body.removeChild(div);

  return {
    top: rect.top,
    left: rect.left,
    right: window.innerWidth - rect.right,
    bottom: window.innerHeight - rect.bottom
  };
}
```

---

## 二、事件与交互

### 2.1 Touch 事件体系

移动端 Touch 事件的完整生命周期：

```javascript
const el = document.getElementById('touchArea');

// Touch 事件类型
el.addEventListener('touchstart', function (e) {
  // 手指按下
  const touch = e.touches[0];
  console.log('起始坐标:', touch.clientX, touch.clientY);
  console.log('触摸点数量:', e.touches.length);
}, false);

el.addEventListener('touchmove', function (e) {
  // 手指移动
  const touch = e.touches[0];
  console.log('移动坐标:', touch.clientX, touch.clientY);

  // 阻止默认行为（如页面滚动）
  e.preventDefault();
}, { passive: false });

el.addEventListener('touchend', function (e) {
  // 手指抬起（此时 e.touches 为空，需要用 changedTouches）
  const touch = e.changedTouches[0];
  console.log('结束坐标:', touch.clientX, touch.clientY);
}, false);

el.addEventListener('touchcancel', function (e) {
  // 触摸被中断（如来电、弹窗）
  console.log('触摸被取消');
}, false);

// Touch 对象属性
// e.touches        - 屏幕上所有触摸点
// e.targetTouches  - 当前元素上的触摸点
// e.changedTouches - 发生变化的触摸点

// 每个 Touch 对象包含：
// identifier  - 触摸点唯一标识
// clientX/Y   - 相对于视口的坐标
// pageX/Y     - 相对于页面的坐标
// screenX/Y   - 相对于屏幕的坐标
// target      - 触摸目标元素
```

### 2.2 300ms 延迟问题

浏览器为了判断用户是单击还是双击缩放，会在 `touchend` 后等待 300ms 才触发 `click` 事件。

**解决方案一：FastClick 库**

```javascript
// 引入 FastClick
import FastClick from 'fastclick';
FastClick.attach(document.body);

// FastClick 原理简析：
// 1. 在 touchend 时立即触发一个模拟的 click 事件
// 2. 取消浏览器在 300ms 后产生的原始 click 事件
class SimpleFastClick {
  constructor(el) {
    this.trackingClick = false;
    this.touchStartX = 0;
    this.touchStartY = 0;
    this.touchBoundary = 10; // 触摸移动阈值

    el.addEventListener('touchstart', this.onTouchStart.bind(this), true);
    el.addEventListener('touchend', this.onTouchEnd.bind(this), true);
    el.addEventListener('click', this.onClick.bind(this), true);
  }

  onTouchStart(e) {
    this.trackingClick = true;
    this.touchStartX = e.targetTouches[0].pageX;
    this.touchStartY = e.targetTouches[0].pageY;
  }

  onTouchEnd(e) {
    if (!this.trackingClick) return;

    // 检查是否移动超过阈值
    const touch = e.changedTouches[0];
    if (Math.abs(touch.pageX - this.touchStartX) > this.touchBoundary ||
        Math.abs(touch.pageY - this.touchStartY) > this.touchBoundary) {
      this.trackingClick = false;
      return;
    }

    // 创建并分发模拟的 click 事件
    const clickEvent = new MouseEvent('click', {
      bubbles: true,
      cancelable: true,
      view: window
    });
    e.target.dispatchEvent(clickEvent);

    e.preventDefault();
    this.trackingClick = false;
  }

  onClick(e) {
    // 如果正在追踪，阻止原生 click
    if (this.trackingClick) {
      e.stopImmediatePropagation();
      e.preventDefault();
    }
  }
}
```

**解决方案二：touch-action CSS**

```css
/* 现代浏览器推荐方案 */
html {
  touch-action: manipulation; /* 禁用双击缩放，消除 300ms 延迟 */
}
```

### 2.3 点击穿透问题

当上层元素使用 `touchstart` 或 `touchend` 关闭后，300ms 后触发的 `click` 事件会作用到下层元素。

```javascript
// 问题场景
const mask = document.getElementById('mask');
const link = document.getElementById('link'); // 遮罩下方的链接

mask.addEventListener('touchstart', function () {
  this.style.display = 'none';
  // 300ms 后 click 事件会穿透到下层的 link
});

// 解决方案一：使用 click 事件代替 touchstart
mask.addEventListener('click', function () {
  this.style.display = 'none';
});

// 解决方案二：延迟隐藏
mask.addEventListener('touchstart', function () {
  const self = this;
  setTimeout(function () {
    self.style.display = 'none';
  }, 350); // 超过 300ms
});

// 解决方案三：阻止默认事件
mask.addEventListener('touchstart', function (e) {
  e.preventDefault();
  this.style.display = 'none';
});

// 解决方案四：CSS pointer-events
mask.addEventListener('touchstart', function () {
  this.style.display = 'none';
  // 临时禁止下层点击
  document.body.style.pointerEvents = 'none';
  setTimeout(function () {
    document.body.style.pointerEvents = 'auto';
  }, 350);
});
```

### 2.4 手势识别

```javascript
class GestureRecognizer {
  constructor(el) {
    this.el = el;
    this.startX = 0;
    this.startY = 0;
    this.startTime = 0;
    this.prevTouchTime = 0;
    this.callbacks = {};

    this._bindEvents();
  }

  on(event, callback) {
    this.callbacks[event] = callback;
    return this;
  }

  _emit(event, data) {
    if (this.callbacks[event]) {
      this.callbacks[event](data);
    }
  }

  _bindEvents() {
    this.el.addEventListener('touchstart', (e) => {
      const touch = e.touches[0];
      this.startX = touch.clientX;
      this.startY = touch.clientY;
      this.startTime = Date.now();
    });

    this.el.addEventListener('touchend', (e) => {
      const touch = e.changedTouches[0];
      const endX = touch.clientX;
      const endY = touch.clientY;
      const endTime = Date.now();
      const deltaX = endX - this.startX;
      const deltaY = endY - this.startY;
      const duration = endTime - this.startTime;
      const distance = Math.sqrt(deltaX ** 2 + deltaY ** 2);

      // 判断手势类型
      if (distance < 10 && duration < 300) {
        // 检测双击（两次 tap 间隔 < 300ms）
        if (this.startTime - this.prevTouchTime < 300) {
          this._emit('doubleTap', { x: endX, y: endY });
        } else {
          // 延迟触发单击（等待可能的双击）
          setTimeout(() => {
            this._emit('tap', { x: endX, y: endY });
          }, 300);
        }
        this.prevTouchTime = this.startTime;
      } else if (duration < 500 && distance > 30) {
        // 滑动方向判断
        const angle = Math.atan2(deltaY, deltaX) * 180 / Math.PI;
        let direction;

        if (angle >= -45 && angle < 45) direction = 'right';
        else if (angle >= 45 && angle < 135) direction = 'down';
        else if (angle >= -135 && angle < -45) direction = 'up';
        else direction = 'left';

        this._emit('swipe', { direction, deltaX, deltaY, duration });
        this._emit(`swipe${direction.charAt(0).toUpperCase() + direction.slice(1)}`, {
          deltaX, deltaY, duration
        });
      } else if (duration >= 750 && distance < 10) {
        this._emit('longPress', { x: endX, y: endY });
      }
    });
  }
}

// 使用示例
const gesture = new GestureRecognizer(document.getElementById('app'));
gesture
  .on('tap', (e) => console.log('单击', e))
  .on('doubleTap', (e) => console.log('双击', e))
  .on('swipeLeft', (e) => console.log('左滑', e))
  .on('swipeRight', (e) => console.log('右滑', e))
  .on('longPress', (e) => console.log('长按', e));
```

### 2.5 滚动优化（passive 事件）

```javascript
// passive: true 告诉浏览器不会调用 preventDefault()
// 浏览器可以立即执行滚动，无需等待 JS 执行完毕
document.addEventListener('touchmove', function (e) {
  // 处理滚动逻辑（不能调用 e.preventDefault()）
}, { passive: true });

// 检测浏览器是否支持 passive
let supportsPassive = false;
try {
  const opts = Object.defineProperty({}, 'passive', {
    get() {
      supportsPassive = true;
      return true;
    }
  });
  window.addEventListener('testPassive', null, opts);
  window.removeEventListener('testPassive', null, opts);
} catch (e) {}

// 兼容写法
document.addEventListener('touchmove', handler,
  supportsPassive ? { passive: true } : false
);

// 滚动节流优化
function scrollThrottle(callback) {
  let ticking = false;
  return function () {
    if (!ticking) {
      requestAnimationFrame(function () {
        callback();
        ticking = false;
      });
      ticking = true;
    }
  };
}

window.addEventListener('scroll', scrollThrottle(function () {
  // 执行滚动处理逻辑
  const scrollTop = document.documentElement.scrollTop || document.body.scrollTop;
  console.log('当前滚动位置:', scrollTop);
}), { passive: true });

// iOS 弹性滚动优化
.scroll-container {
  -webkit-overflow-scrolling: touch; /* 开启惯性滚动 */
  overflow-y: auto;
}
```

### 2.6 键盘弹起适配

```javascript
// 键盘弹起检测
class KeyboardHandler {
  constructor() {
    this.originalHeight = window.innerHeight;
    this.isKeyboardVisible = false;
    this._init();
  }

  _init() {
    // Android 通过 resize 事件检测
    if (/Android/i.test(navigator.userAgent)) {
      window.addEventListener('resize', () => {
        const currentHeight = window.innerHeight;
        if (currentHeight < this.originalHeight * 0.75) {
          this._onKeyboardShow(this.originalHeight - currentHeight);
        } else {
          this._onKeyboardHide();
        }
      });
    }

    // iOS 通过 focus/blur 事件检测
    if (/iPhone|iPad/i.test(navigator.userAgent)) {
      const inputs = document.querySelectorAll('input, textarea');
      inputs.forEach(input => {
        input.addEventListener('focus', () => {
          setTimeout(() => this._onKeyboardShow(300), 300);
        });
        input.addEventListener('blur', () => {
          this._onKeyboardHide();
        });
      });
    }
  }

  _onKeyboardShow(keyboardHeight) {
    this.isKeyboardVisible = true;
    document.body.classList.add('keyboard-visible');

    // 滚动到输入框可见位置
    const activeElement = document.activeElement;
    if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
      setTimeout(() => {
        activeElement.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }, 100);
    }
  }

  _onKeyboardHide() {
    this.isKeyboardVisible = false;
    document.body.classList.remove('keyboard-visible');

    // iOS 键盘收起后页面可能不回弹，手动滚动修复
    if (/iPhone|iPad/i.test(navigator.userAgent)) {
      window.scrollTo(0, document.documentElement.scrollTop || document.body.scrollTop);
    }
  }
}

// 初始化
new KeyboardHandler();
```

```css
/* 键盘弹起时固定底部栏的处理 */
.keyboard-visible .fixed-bottom {
  position: static; /* 键盘弹起时取消固定定位 */
}

/* 或者调整位置 */
.keyboard-visible .chat-input {
  position: absolute;
  bottom: auto;
}
```

---

## 三、Hybrid 开发

### 3.1 JSBridge 原理

JSBridge 是 Native 和 Web 之间的通信桥梁，主要有三种实现方式。

**方式一：URL Scheme 拦截**

```javascript
// Web 端发送消息
function callNative(method, params, callback) {
  const callbackId = 'cb_' + Date.now() + '_' + Math.random().toString(36).substr(2);

  // 注册回调
  window.__nativeBridgeCallbacks = window.__nativeBridgeCallbacks || {};
  window.__nativeBridgeCallbacks[callbackId] = function (response) {
    callback && callback(response);
    delete window.__nativeBridgeCallbacks[callbackId];
  };

  // 构建 URL Scheme
  const url = `myapp://bridge/${method}?params=${encodeURIComponent(JSON.stringify(params))}&callback=${callbackId}`;

  // 方式1：通过 iframe 发送
  const iframe = document.createElement('iframe');
  iframe.style.display = 'none';
  iframe.src = url;
  document.body.appendChild(iframe);
  setTimeout(() => {
    document.body.removeChild(iframe);
  }, 200);

  // 方式2：通过 location.href（不推荐，连续调用会被覆盖）
  // window.location.href = url;
}

// Native 回调 Web
// Native 端拦截到 URL Scheme 后执行原生方法，
// 然后通过 evaluateJavaScript 调用回调：
// webView.evaluateJavaScript(
//   "window.__nativeBridgeCallbacks['cb_xxx']({code: 0, data: {...}})"
// )

// 使用示例
callNative('getDeviceInfo', {}, function (result) {
  console.log('设备信息:', result);
});
```

**方式二：postMessage 通信（WKWebView）**

```javascript
// Web -> Native（iOS WKWebView）
window.webkit.messageHandlers.nativeBridge.postMessage({
  method: 'share',
  params: {
    title: '分享标题',
    content: '分享内容',
    url: 'https://example.com'
  }
});

// Web -> Native（Android）
window.androidBridge.postMessage(JSON.stringify({
  method: 'share',
  params: { title: '分享标题' }
}));

// Native -> Web（通用）
// Native 调用 webView.evaluateJavaScript:
// "window.dispatchEvent(new CustomEvent('nativeMessage', {detail: {...}}))"
window.addEventListener('nativeMessage', function (e) {
  console.log('收到 Native 消息:', e.detail);
});
```

**方式三：注入全局 API**

```javascript
// Native 向 WebView 注入全局对象
// Android: webView.addJavascriptInterface(bridge, "NativeBridge")
// iOS: WKUserContentController 注入

// Web 端直接调用
function callNativeMethod(method, params) {
  return new Promise((resolve, reject) => {
    const callbackName = `__bridge_cb_${Date.now()}`;

    window[callbackName] = function (result) {
      delete window[callbackName];
      if (result.code === 0) {
        resolve(result.data);
      } else {
        reject(result.message);
      }
    };

    // 调用 Native 注入的方法
    if (window.NativeBridge) {
      window.NativeBridge.invoke(method, JSON.stringify(params), callbackName);
    } else {
      reject('NativeBridge not found');
    }
  });
}

// 完整的 JSBridge 封装
class JSBridge {
  static isReady = false;
  static readyCallbacks = [];
  static callbackId = 0;
  static callbacks = {};

  // 等待 Bridge 就绪
  static ready(fn) {
    if (this.isReady) {
      fn();
    } else {
      this.readyCallbacks.push(fn);
    }
  }

  // 初始化（Native 调用）
  static _init() {
    this.isReady = true;
    this.readyCallbacks.forEach(fn => fn());
    this.readyCallbacks = [];
  }

  // 调用 Native 方法
  static call(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.callbackId;
      this.callbacks[id] = { resolve, reject };

      const message = { id, method, params };

      // 多平台兼容
      if (window.webkit?.messageHandlers?.bridge) {
        window.webkit.messageHandlers.bridge.postMessage(message);
      } else if (window.NativeBridge) {
        window.NativeBridge.invoke(JSON.stringify(message));
      } else {
        reject(new Error('Bridge not available'));
      }
    });
  }

  // 处理 Native 回调
  static _handleCallback(id, error, data) {
    const cb = this.callbacks[id];
    if (cb) {
      error ? cb.reject(error) : cb.resolve(data);
      delete this.callbacks[id];
    }
  }

  // 注册供 Native 调用的方法
  static register(name, handler) {
    window.__bridgeHandlers = window.__bridgeHandlers || {};
    window.__bridgeHandlers[name] = handler;
  }
}

// 使用
JSBridge.ready(async () => {
  const deviceInfo = await JSBridge.call('getDeviceInfo');
  console.log(deviceInfo);
});
```

### 3.2 WebView 性能优化

```javascript
// 1. WebView 预创建（Native 侧）
// 在 App 启动时预创建 WebView 实例，放入对象池
// 打开 H5 页面时直接复用，减少 WebView 初始化耗时

// 2. 资源预加载 - 离线包方案
class OfflineManager {
  constructor() {
    this.cacheMap = new Map();
    this.DB_NAME = 'offline_resource';
    this.STORE_NAME = 'resources';
  }

  // 从 IndexedDB 加载缓存
  async loadFromDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, 1);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(this.STORE_NAME)) {
          db.createObjectStore(this.STORE_NAME, { keyPath: 'url' });
        }
      };
      request.onsuccess = (e) => {
        this.db = e.target.result;
        resolve();
      };
      request.onerror = reject;
    });
  }

  // 拦截网络请求，优先从本地读取
  async getResource(url) {
    const cached = await this._readFromDB(url);
    if (cached && !this._isExpired(cached)) {
      return cached.content;
    }
    // 缓存不存在或已过期，从网络获取
    const response = await fetch(url);
    const content = await response.text();
    await this._writeToDB(url, content);
    return content;
  }

  _isExpired(record) {
    const maxAge = 24 * 60 * 60 * 1000; // 24小时
    return Date.now() - record.timestamp > maxAge;
  }

  async _readFromDB(url) {
    return new Promise((resolve) => {
      const tx = this.db.transaction(this.STORE_NAME, 'readonly');
      const store = tx.objectStore(this.STORE_NAME);
      const req = store.get(url);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => resolve(null);
    });
  }

  async _writeToDB(url, content) {
    return new Promise((resolve) => {
      const tx = this.db.transaction(this.STORE_NAME, 'readwrite');
      const store = tx.objectStore(this.STORE_NAME);
      store.put({ url, content, timestamp: Date.now() });
      tx.oncomplete = resolve;
    });
  }
}
```

### 3.3 离线包方案

```javascript
// 离线包更新流程
class OfflinePackageManager {
  constructor(config) {
    this.serverUrl = config.serverUrl;
    this.currentVersion = config.currentVersion || '0';
    this.packageDir = config.packageDir;
  }

  // 检查更新
  async checkUpdate() {
    try {
      const response = await fetch(`${this.serverUrl}/api/offline/check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          appVersion: this.getAppVersion(),
          packageVersion: this.currentVersion,
          platform: this.getPlatform()
        })
      });

      const data = await response.json();

      if (data.needUpdate) {
        return {
          version: data.latestVersion,
          downloadUrl: data.downloadUrl,
          md5: data.md5,
          patchUrl: data.patchUrl, // 增量更新地址
          fullSize: data.fullSize,
          patchSize: data.patchSize
        };
      }
      return null;
    } catch (err) {
      console.error('检查离线包更新失败:', err);
      return null;
    }
  }

  // 下载并应用更新
  async applyUpdate(updateInfo) {
    try {
      // 优先使用增量更新
      const url = updateInfo.patchUrl || updateInfo.downloadUrl;
      const data = await this.download(url);

      // 验证 MD5
      if (this.verifyMD5(data, updateInfo.md5)) {
        await this.unzipAndReplace(data);
        this.currentVersion = updateInfo.version;
        this.saveVersion(updateInfo.version);
        return true;
      }
      return false;
    } catch (err) {
      console.error('更新离线包失败:', err);
      return false;
    }
  }

  // Service Worker 拦截请求
  registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/offline-sw.js')
        .then(registration => {
          console.log('SW 注册成功:', registration.scope);
        })
        .catch(err => {
          console.error('SW 注册失败:', err);
        });
    }
  }
}

// offline-sw.js - Service Worker 离线缓存策略
const CACHE_NAME = 'offline-v1';
const OFFLINE_URLS = [
  '/',
  '/index.html',
  '/static/js/main.js',
  '/static/css/main.css'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(OFFLINE_URLS))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then(cached => {
      // 缓存优先策略
      return cached || fetch(event.request).then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      });
    })
  );
});
```

---

## 四、小程序

### 4.1 双线程模型

小程序采用渲染层（Webview）+ 逻辑层（JSCore/V8）双线程架构：

```
┌──────────────────┐     ┌──────────────────┐
│   渲染层 Webview  │     │  逻辑层 JSCore    │
│                  │     │                  │
│  WXML + WXSS    │     │   App / Page     │
│  ↓              │     │   逻辑代码        │
│  Virtual DOM    │     │                  │
│  ↓              │     │                  │
│  Real DOM       │     │                  │
└────────┬─────────┘     └─────────┬────────┘
         │       通过 Native 中转       │
         └──────────┬──────────────┘
                    │
            ┌───────┴───────┐
            │  Native 层    │
            │  微信客户端    │
            └───────────────┘
```

**双线程通信流程：**

```javascript
// 逻辑层 -> 渲染层（setData 过程）
// 1. 逻辑层调用 setData({ text: 'hello' })
// 2. 数据经过序列化（JSON.stringify）
// 3. 通过 Native JSBridge 传输到渲染层
// 4. 渲染层反序列化，进行 VDOM diff
// 5. 更新真实 DOM

// setData 性能优化原则：
Page({
  data: {
    list: [],
    userInfo: {}
  },

  // 反模式：频繁 setData 大量数据
  badExample() {
    // 每次都传递完整的 list
    this.setData({ list: this.data.list }); // 差！
  },

  // 正确做法：路径更新
  goodExample() {
    // 只更新变化的部分
    this.setData({
      'list[2].name': '新名字',           // 精确路径
      'userInfo.avatar': 'new_url.jpg'    // 精确路径
    });
  },

  // 批量更新
  batchUpdate() {
    // 合并多次 setData 为一次
    const updates = {};
    this.data.list.forEach((item, index) => {
      if (item.needUpdate) {
        updates[`list[${index}].status`] = 'done';
      }
    });
    this.setData(updates); // 一次 setData 解决
  }
});
```

### 4.2 小程序生命周期

```javascript
// App 生命周期
App({
  onLaunch(options) {
    // 小程序初始化（全局只触发一次）
    console.log('启动场景值:', options.scene);
    console.log('启动参数:', options.query);
  },
  onShow(options) {
    // 小程序启动或从后台进入前台
  },
  onHide() {
    // 小程序从前台进入后台
  },
  onError(msg) {
    // 脚本错误或 API 调用失败
    console.error('全局错误:', msg);
  },
  onUnhandledRejection(res) {
    // 未处理的 Promise rejection
    console.error('未处理的 Promise 错误:', res.reason);
  }
});

// Page 生命周期
Page({
  onLoad(options) {
    // 页面加载（只触发一次）
    // options 为页面路由参数
    console.log('页面参数:', options);
  },
  onShow() {
    // 页面显示/切入前台
  },
  onReady() {
    // 页面初次渲染完成（只触发一次）
    // 可以与视图层进行交互
  },
  onHide() {
    // 页面隐藏/切入后台
  },
  onUnload() {
    // 页面卸载
    // 清除定时器、取消请求等
  }
});

// Component 生命周期
Component({
  lifetimes: {
    created() {
      // 组件实例被创建（不能调用 setData）
    },
    attached() {
      // 组件进入页面节点树（常用，类似 mounted）
    },
    ready() {
      // 组件在视图层布局完成
    },
    moved() {
      // 组件实例被移动到另一个位置
    },
    detached() {
      // 组件从页面节点树移除
    },
    error(err) {
      // 组件方法抛出错误
    }
  },
  // 组件所在页面的生命周期
  pageLifetimes: {
    show() {},
    hide() {},
    resize(size) {}
  }
});
```

### 4.3 Taro/uni-app 跨端原理

**Taro 3.x 编译原理：**

```javascript
// Taro 3 采用运行时适配方案
// 核心思路：在小程序端实现一套类 DOM/BOM API

// 1. 编译阶段：将 React/Vue 代码编译为可在小程序环境运行的代码
// 2. 运行时：通过 taro-runtime 提供 DOM/BOM API 模拟层

// Taro React 组件示例
import { Component } from 'react';
import { View, Text, Button } from '@tarojs/components';
import Taro from '@tarojs/taro';

class Index extends Component {
  state = {
    count: 0
  };

  componentDidMount() {
    // 等同于 onReady
    console.log('页面加载完成');
  }

  handleClick = () => {
    this.setState({ count: this.state.count + 1 });
    // Taro API 调用
    Taro.showToast({ title: '点击了按钮' });
  };

  render() {
    return (
      <View className="index">
        <Text>计数: {this.state.count}</Text>
        <Button onClick={this.handleClick}>点击+1</Button>
      </View>
    );
  }
}

export default Index;

// Taro 运行时核心 - 模拟 DOM 操作
// taro-runtime 内部简化版：
class TaroNode {
  constructor(nodeType) {
    this.nodeType = nodeType;
    this.childNodes = [];
    this.parentNode = null;
  }

  appendChild(child) {
    child.parentNode = this;
    this.childNodes.push(child);
    // 触发小程序 setData 更新视图
    this._enqueueUpdate();
  }

  _enqueueUpdate() {
    // 收集更新，批量调用 setData
    if (!this._updateTimer) {
      this._updateTimer = setTimeout(() => {
        const page = getCurrentPages().pop();
        if (page) {
          page.setData({
            root: this._serialize()
          });
        }
        this._updateTimer = null;
      }, 0);
    }
  }
}
```

**uni-app 跨端原理：**

```javascript
// uni-app 采用编译时 + 运行时结合的方案

// 编译时：将 Vue SFC 编译为各平台代码
// - H5: 标准 Vue 项目
// - 小程序: 转为 WXML/WXSS/JS
// - App: 编译为 weex/nvue 渲染

// 条件编译 - 平台差异处理
// #ifdef H5
console.log('仅在 H5 平台编译');
// #endif

// #ifdef MP-WEIXIN
console.log('仅在微信小程序编译');
// #endif

// #ifndef APP-PLUS
console.log('除 App 之外的平台');
// #endif

// uni-app 页面示例
export default {
  data() {
    return {
      list: []
    };
  },
  onLoad(options) {
    // 页面加载 - 小程序生命周期
    this.loadData();
  },
  mounted() {
    // Vue 生命周期 - 也可以使用
  },
  methods: {
    async loadData() {
      const res = await uni.request({
        url: 'https://api.example.com/list',
        method: 'GET'
      });
      this.list = res.data;
    }
  }
};
```

### 4.4 小程序性能优化

```javascript
// 1. 减少 setData 数据量
// 2. 长列表优化 - 使用 recycle-view
// 3. 图片懒加载
// 4. 分包加载

// app.json 分包配置
const appConfig = {
  "pages": [
    "pages/index/index",    // 主包
    "pages/user/user"
  ],
  "subpackages": [
    {
      "root": "packageA",   // 分包 A
      "pages": [
        "pages/detail/detail",
        "pages/list/list"
      ]
    },
    {
      "root": "packageB",   // 分包 B
      "pages": [
        "pages/cart/cart"
      ]
    }
  ],
  // 独立分包（可以独立于主包运行）
  "subpackages": [
    {
      "root": "independent",
      "pages": ["pages/landing/landing"],
      "independent": true
    }
  ],
  // 分包预下载
  "preloadRule": {
    "pages/index/index": {
      "network": "all",
      "packages": ["packageA"]
    }
  }
};

// 5. 自定义组件优化
Component({
  options: {
    pureDataPattern: /^_/  // 以 _ 开头的数据不参与渲染
  },
  data: {
    _rawData: [],       // 纯数据字段，不触发视图更新
    displayList: []     // 用于渲染的数据
  },
  methods: {
    processData(rawData) {
      this.setData({
        _rawData: rawData   // 不会触发渲染
      });
      // 只更新需要渲染的数据
      this.setData({
        displayList: rawData.slice(0, 20)
      });
    }
  }
});
```

---

## 五、跨端方案

### 5.1 React Native 新架构

React Native 新架构（0.68+）引入了三大核心改进：

```
旧架构:
  JS Thread ──── Bridge (JSON) ──── Native Thread

新架构:
  JS Thread ──── JSI ──── C++ Host Objects ──── Native Thread
                  │
                  ├── Fabric (新渲染引擎)
                  └── TurboModules (新原生模块系统)
```

**JSI（JavaScript Interface）：**

```javascript
// JSI 允许 JS 直接调用 C++ 对象，无需 JSON 序列化
// 旧架构：JS -> JSON 序列化 -> Bridge -> JSON 反序列化 -> Native
// 新架构：JS -> JSI -> C++ Host Object -> Native（同步调用）

// 旧架构调用原生方法
// NativeModules.DeviceInfo.getDeviceId((id) => {
//   console.log(id); // 异步回调
// });

// 新架构通过 JSI 同步调用
// const id = global.__DeviceInfo.getDeviceId(); // 同步返回

// TurboModule 定义示例（TypeScript 接口）
// NativeDeviceInfo.ts
import type { TurboModule } from 'react-native';
import { TurboModuleRegistry } from 'react-native';

export interface Spec extends TurboModule {
  getDeviceId(): string;                    // 同步方法
  getBatteryLevel(): Promise<number>;        // 异步方法
  getConstants(): {
    platform: string;
    osVersion: string;
  };
}

export default TurboModuleRegistry.getEnforcing<Spec>('DeviceInfo');
```

**Fabric 渲染引擎：**

```javascript
// Fabric 的核心改进：
// 1. 在 C++ 层创建 Shadow Tree（而非 Java/OC 层）
// 2. 支持同步渲染（消除异步通信导致的 UI 跳跃）
// 3. 支持多优先级渲染（与 React 18 的 Concurrent 特性对齐）

// Fabric 渲染流程:
// React Reconciler -> 生成 React Element Tree
// -> Fabric C++ 创建 Shadow Node Tree
// -> Yoga 布局引擎计算布局
// -> 生成 View Flattening 优化后的视图结构
// -> 提交到 Native 主线程渲染

// React Native 新架构组件写法
import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, FlatList } from 'react-native';

const App = () => {
  const [items, setItems] = useState(
    Array.from({ length: 100 }, (_, i) => ({
      id: String(i),
      title: `Item ${i}`
    }))
  );

  const renderItem = ({ item }) => (
    <View style={styles.item}>
      <Text style={styles.title}>{item.title}</Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        renderItem={renderItem}
        keyExtractor={item => item.id}
        windowSize={5}
        maxToRenderPerBatch={10}
        removeClippedSubviews={true}
        initialNumToRender={10}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  item: { padding: 16, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#eee' },
  title: { fontSize: 16, color: '#333' }
});

export default App;
```

### 5.2 Flutter 原理

```
Flutter 架构分层:

┌─────────────────────────────────┐
│        Dart Framework           │
│  ┌────────┐ ┌────────────────┐  │
│  │Material│ │   Cupertino    │  │
│  │Widgets │ │   Widgets      │  │
│  └────────┘ └────────────────┘  │
│  ┌───────────────────────────┐  │
│  │      Widgets Layer        │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │    Rendering Layer        │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │     Dart:ui / Engine      │  │
│  └───────────────────────────┘  │
├─────────────────────────────────┤
│        Engine (C++)             │
│  ┌──────┐ ┌──────┐ ┌────────┐  │
│  │Skia  │ │Dart  │ │Platform│  │
│  │      │ │VM    │ │Channel │  │
│  └──────┘ └──────┘ └────────┘  │
├─────────────────────────────────┤
│     Platform (iOS/Android)      │
└─────────────────────────────────┘
```

```dart
// Flutter Widget 示例
import 'package:flutter/material.dart';

class CounterPage extends StatefulWidget {
  @override
  _CounterPageState createState() => _CounterPageState();
}

class _CounterPageState extends State<CounterPage> {
  int _counter = 0;

  void _increment() {
    // setState 触发 Widget 重建
    // Flutter 通过 Element Tree diff 最小化更新
    setState(() {
      _counter++;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Flutter Counter')),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('计数:', style: TextStyle(fontSize: 18)),
            Text(
              '$_counter',
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _increment,
        child: Icon(Icons.add),
      ),
    );
  }
}

// Flutter 三棵树:
// Widget Tree -> Element Tree -> RenderObject Tree
// Widget: 不可变的 UI 配置描述
// Element: Widget 的实例化，管理生命周期
// RenderObject: 负责布局和绘制
```

### 5.3 Electron 原理

```javascript
// Electron = Chromium + Node.js + Native APIs
// 主进程(Main Process): Node.js 运行环境，管理窗口
// 渲染进程(Renderer Process): Chromium 运行 Web 页面

// main.js - 主进程
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

app.whenReady().then(() => {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,  // 上下文隔离
      nodeIntegration: false   // 禁止渲染进程直接访问 Node
    }
  });

  mainWindow.loadFile('index.html');
});

// IPC 通信 - 主进程监听
ipcMain.handle('read-file', async (event, filePath) => {
  const fs = require('fs').promises;
  return await fs.readFile(filePath, 'utf-8');
});

// preload.js - 预加载脚本（桥接主进程和渲染进程）
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  readFile: (path) => ipcRenderer.invoke('read-file', path),
  onUpdateAvailable: (callback) =>
    ipcRenderer.on('update-available', callback)
});

// renderer.js - 渲染进程
document.getElementById('openBtn').addEventListener('click', async () => {
  const content = await window.electronAPI.readFile('./data.json');
  console.log(content);
});
```

### 5.4 跨端方案对比

| 特性 | React Native | Flutter | 小程序 | Electron |
|------|-------------|---------|--------|----------|
| **渲染方式** | 原生组件 | Skia 自绘 | WebView | Chromium |
| **开发语言** | JavaScript/TS | Dart | JS/TS | JS/TS |
| **性能** | 接近原生 | 接近原生 | 一般 | 较低 |
| **包体积** | 较大 | 较大 | 小 | 很大(100MB+) |
| **热更新** | 支持 | 受限 | 天然支持 | 支持 |
| **生态** | 丰富(npm) | 增长中 | 各平台私有 | 丰富(npm+Node) |
| **学习成本** | 中(React) | 高(Dart) | 低 | 低(Web技术) |
| **适用场景** | 移动App | 高性能App | 轻量应用 | 桌面应用 |
| **动画性能** | 好 | 极好 | 一般 | 好 |
| **代码共享** | iOS/Android | iOS/Android/Web/桌面 | 多平台小程序 | Windows/Mac/Linux |

---

## 六、性能优化

### 6.1 首屏优化

**SSR（服务端渲染）：**

```javascript
// Next.js SSR 示例
// pages/index.js
export async function getServerSideProps(context) {
  const res = await fetch('https://api.example.com/data');
  const data = await res.json();

  return {
    props: {
      initialData: data,
      timestamp: Date.now()
    }
  };
}

export default function Home({ initialData }) {
  return (
    <div>
      <h1>首屏数据</h1>
      <ul>
        {initialData.map(item => (
          <li key={item.id}>{item.name}</li>
        ))}
      </ul>
    </div>
  );
}

// Vue 3 SSR 核心流程
// server.js
import { createSSRApp } from 'vue';
import { renderToString } from 'vue/server-renderer';
import App from './App.vue';

async function render(url) {
  const app = createSSRApp(App);
  // 数据预取
  const store = createStore();
  await store.dispatch('fetchInitialData');
  app.use(store);

  const html = await renderToString(app);
  const state = store.state;

  return `
    <!DOCTYPE html>
    <html>
      <head><title>SSR Page</title></head>
      <body>
        <div id="app">${html}</div>
        <script>
          window.__INITIAL_STATE__ = ${JSON.stringify(state)}
        </script>
        <script src="/client.js"></script>
      </body>
    </html>
  `;
}
```

**骨架屏方案：**

```html
<!-- 骨架屏 HTML，内联在 index.html 中 -->
<div id="app">
  <!-- 骨架屏内容，在 Vue/React 挂载后自动替换 -->
  <div class="skeleton">
    <div class="skeleton-header">
      <div class="skeleton-avatar skeleton-animate"></div>
      <div class="skeleton-title skeleton-animate"></div>
    </div>
    <div class="skeleton-content">
      <div class="skeleton-line skeleton-animate" style="width: 100%"></div>
      <div class="skeleton-line skeleton-animate" style="width: 80%"></div>
      <div class="skeleton-line skeleton-animate" style="width: 60%"></div>
    </div>
  </div>
</div>
```

```css
/* 骨架屏样式 */
.skeleton-animate {
  background: linear-gradient(
    90deg,
    #f2f2f2 25%,
    #e6e6e6 37%,
    #f2f2f2 63%
  );
  background-size: 400% 100%;
  animation: skeleton-loading 1.4s ease infinite;
}

@keyframes skeleton-loading {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}

.skeleton-header {
  display: flex;
  align-items: center;
  padding: 16px;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin-right: 12px;
}

.skeleton-title {
  width: 150px;
  height: 20px;
  border-radius: 4px;
}

.skeleton-line {
  height: 16px;
  border-radius: 4px;
  margin: 12px 16px;
}
```

### 6.2 图片优化

```javascript
// WebP 检测与降级
function checkWebpSupport() {
  return new Promise((resolve) => {
    const img = new Image();
    img.onload = function () {
      resolve(img.width > 0 && img.height > 0);
    };
    img.onerror = function () {
      resolve(false);
    };
    img.src = 'data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA==';
  });
}

// 图片懒加载 - Intersection Observer 方案
class LazyImageLoader {
  constructor(options = {}) {
    this.options = {
      rootMargin: '200px 0px', // 提前 200px 开始加载
      threshold: 0.01,
      ...options
    };
    this._init();
  }

  _init() {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this._loadImage(entry.target);
          this.observer.unobserve(entry.target);
        }
      });
    }, this.options);

    // 观察所有懒加载图片
    document.querySelectorAll('img[data-src]').forEach(img => {
      this.observer.observe(img);
    });
  }

  _loadImage(img) {
    const src = img.dataset.src;
    const srcset = img.dataset.srcset;

    if (src) {
      img.src = src;
      img.removeAttribute('data-src');
    }
    if (srcset) {
      img.srcset = srcset;
      img.removeAttribute('data-srcset');
    }

    img.classList.add('loaded');
  }

  destroy() {
    this.observer.disconnect();
  }
}

// 初始化
const lazyLoader = new LazyImageLoader();
```

```html
<!-- 响应式图片 + 懒加载 -->
<picture>
  <source
    data-srcset="image.webp"
    type="image/webp"
  >
  <source
    data-srcset="image.jpg"
    type="image/jpeg"
  >
  <img
    data-src="image.jpg"
    alt="描述"
    loading="lazy"
    class="lazy"
    width="300"
    height="200"
  >
</picture>
```

### 6.3 长列表虚拟滚动

```javascript
// 虚拟滚动核心实现
class VirtualList {
  constructor(container, options) {
    this.container = container;
    this.itemHeight = options.itemHeight;
    this.totalItems = options.totalItems;
    this.renderItem = options.renderItem;
    this.bufferSize = options.bufferSize || 5;

    this.totalHeight = this.itemHeight * this.totalItems;
    this.visibleCount = Math.ceil(container.clientHeight / this.itemHeight);

    this._init();
  }

  _init() {
    // 创建滚动占位容器
    this.phantom = document.createElement('div');
    this.phantom.style.height = `${this.totalHeight}px`;

    // 创建内容容器
    this.content = document.createElement('div');
    this.content.style.position = 'relative';

    this.container.style.overflow = 'auto';
    this.container.appendChild(this.phantom);
    this.container.appendChild(this.content);

    // 绑定滚动事件
    this.container.addEventListener('scroll', this._onScroll.bind(this), { passive: true });

    // 首次渲染
    this._render(0);
  }

  _onScroll() {
    const scrollTop = this.container.scrollTop;
    const startIndex = Math.floor(scrollTop / this.itemHeight);
    this._render(startIndex);
  }

  _render(startIndex) {
    // 计算可见范围（含缓冲区）
    const start = Math.max(0, startIndex - this.bufferSize);
    const end = Math.min(
      this.totalItems,
      startIndex + this.visibleCount + this.bufferSize
    );

    // 清空并重新渲染
    this.content.innerHTML = '';
    this.content.style.transform = `translateY(${start * this.itemHeight}px)`;

    const fragment = document.createDocumentFragment();
    for (let i = start; i < end; i++) {
      const item = this.renderItem(i);
      item.style.height = `${this.itemHeight}px`;
      fragment.appendChild(item);
    }
    this.content.appendChild(fragment);
  }
}

// 使用示例
const list = new VirtualList(document.getElementById('listContainer'), {
  itemHeight: 60,
  totalItems: 100000,
  bufferSize: 5,
  renderItem(index) {
    const div = document.createElement('div');
    div.className = 'list-item';
    div.textContent = `Item ${index}`;
    return div;
  }
});
```

**React 虚拟列表组件：**

```jsx
import React, { useState, useRef, useCallback, useMemo } from 'react';

function VirtualList({ items, itemHeight, containerHeight, renderItem }) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef(null);

  const visibleCount = Math.ceil(containerHeight / itemHeight);
  const buffer = 5;
  const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - buffer);
  const endIndex = Math.min(items.length, startIndex + visibleCount + 2 * buffer);
  const totalHeight = items.length * itemHeight;
  const offsetY = startIndex * itemHeight;

  const visibleItems = useMemo(() =>
    items.slice(startIndex, endIndex),
    [items, startIndex, endIndex]
  );

  const handleScroll = useCallback((e) => {
    setScrollTop(e.target.scrollTop);
  }, []);

  return (
    <div
      ref={containerRef}
      style={{ height: containerHeight, overflow: 'auto' }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div style={{ transform: `translateY(${offsetY}px)` }}>
          {visibleItems.map((item, i) => (
            <div key={startIndex + i} style={{ height: itemHeight }}>
              {renderItem(item, startIndex + i)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default React.memo(VirtualList);
```

### 6.4 弱网优化策略

```javascript
// 网络状态检测
class NetworkMonitor {
  constructor() {
    this.type = 'unknown';
    this.effectiveType = '4g';
    this.onchange = null;
    this._init();
  }

  _init() {
    const connection = navigator.connection ||
                       navigator.mozConnection ||
                       navigator.webkitConnection;

    if (connection) {
      this.type = connection.type;               // wifi, cellular 等
      this.effectiveType = connection.effectiveType; // slow-2g, 2g, 3g, 4g
      this.downlink = connection.downlink;        // 下行带宽 Mbps
      this.rtt = connection.rtt;                  // 往返时间 ms

      connection.addEventListener('change', () => {
        this.type = connection.type;
        this.effectiveType = connection.effectiveType;
        this.onchange && this.onchange(this);
      });
    }
  }

  isSlowNetwork() {
    return this.effectiveType === 'slow-2g' ||
           this.effectiveType === '2g' ||
           this.rtt > 500;
  }
}

// 弱网请求策略
class RequestManager {
  constructor() {
    this.networkMonitor = new NetworkMonitor();
    this.retryConfig = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 10000
    };
    this.pendingRequests = new Map();
  }

  // 带重试的请求
  async fetchWithRetry(url, options = {}, retryCount = 0) {
    const controller = new AbortController();
    const timeout = this.networkMonitor.isSlowNetwork() ? 15000 : 8000;

    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (!response.ok && retryCount < this.retryConfig.maxRetries) {
        return this._retry(url, options, retryCount);
      }
      return response;
    } catch (error) {
      clearTimeout(timeoutId);

      if (retryCount < this.retryConfig.maxRetries) {
        return this._retry(url, options, retryCount);
      }

      // 尝试从缓存读取
      const cached = await this._getFromCache(url);
      if (cached) {
        console.log('使用缓存数据:', url);
        return cached;
      }

      throw error;
    }
  }

  async _retry(url, options, retryCount) {
    // 指数退避
    const delay = Math.min(
      this.retryConfig.baseDelay * Math.pow(2, retryCount),
      this.retryConfig.maxDelay
    );
    await new Promise(resolve => setTimeout(resolve, delay));
    return this.fetchWithRetry(url, options, retryCount + 1);
  }

  async _getFromCache(url) {
    if ('caches' in window) {
      const cache = await caches.open('api-cache');
      return cache.match(url);
    }
    return null;
  }

  // 弱网降级策略
  getImageQuality() {
    switch (this.networkMonitor.effectiveType) {
      case 'slow-2g':
      case '2g':
        return 'thumbnail';  // 缩略图
      case '3g':
        return 'medium';     // 中等质量
      default:
        return 'high';       // 高质量
    }
  }

  // 请求优先级队列
  enqueueRequest(url, options, priority = 'normal') {
    return new Promise((resolve, reject) => {
      this.pendingRequests.set(url, {
        url, options, priority, resolve, reject
      });
      this._processQueue();
    });
  }

  _processQueue() {
    const sorted = [...this.pendingRequests.values()]
      .sort((a, b) => {
        const priorityMap = { high: 3, normal: 2, low: 1 };
        return priorityMap[b.priority] - priorityMap[a.priority];
      });

    // 弱网下限制并发数
    const concurrency = this.networkMonitor.isSlowNetwork() ? 2 : 6;
    const batch = sorted.slice(0, concurrency);

    batch.forEach(req => {
      this.fetchWithRetry(req.url, req.options)
        .then(req.resolve)
        .catch(req.reject)
        .finally(() => {
          this.pendingRequests.delete(req.url);
        });
    });
  }
}

// 使用
const reqManager = new RequestManager();
const data = await reqManager.fetchWithRetry('/api/data');
```

---

## 七、高频面试题

### 面试题 1：移动端 1px 问题的本质是什么？如何解决？

**答：** 1px 问题的本质是 CSS 像素与物理像素的比值差异。在 DPR=2 的设备上，CSS 的 1px 会用 2 个物理像素渲染，导致视觉上线条偏粗。

推荐方案是**伪元素 + transform: scaleY(0.5)**，兼容性好且不影响布局。

---

### 面试题 2：rem 和 vw 方案各自的优缺点？

**答：**

- **rem 方案**：需要 JS 动态计算根字体大小；可以设置最大宽度限制；兼容性好（IE9+）；但存在 JS 未加载时的闪烁问题。
- **vw 方案**：纯 CSS 实现，不依赖 JS；但无法方便地限制最大宽度；在 PC 端预览会过度放大；兼容性稍差（iOS 8+/Android 4.4+）。

现代项目推荐 **vw + rem** 混合方案：用 vw 设置根字体大小，用 rem 编写样式。

---

### 面试题 3：300ms 延迟的原因和最佳解决方案？

**答：** 浏览器为判断用户是否双击缩放，在 touchend 后等待 300ms 才触发 click。现代浏览器推荐使用 CSS `touch-action: manipulation` 解决，无需引入 FastClick。

---

### 面试题 4：什么是点击穿透？如何解决？

**答：** 上层元素在 touchend 中消失后，300ms 后触发的 click 事件落在了下层元素上。解决方案：(1) 统一使用 click 事件；(2) 使用 `e.preventDefault()`；(3) 延迟 350ms 隐藏上层元素；(4) 使用 `pointer-events: none` 临时禁用下层点击。

---

### 面试题 5：JSBridge 的三种实现方式及优缺点？

**答：**
1. **URL Scheme 拦截**：兼容性最好，但长度有限制，且调用有延迟（需创建 iframe）。
2. **postMessage**：WKWebView 原生支持，性能好，但仅 iOS 支持原生 API。
3. **注入全局 API**：通过 Native 向 WebView 注入全局对象，调用直接且支持同步，是目前最推荐的方案。

---

### 面试题 6：小程序双线程模型的优缺点？

**答：**
- **优点**：逻辑层和渲染层隔离，防止开发者直接操作 DOM（安全性）；渲染不受 JS 执行阻塞（渲染性能）。
- **缺点**：线程间通信需要序列化，setData 数据量大时性能差；无法直接操作 DOM，灵活性受限；不支持同步 DOM API（如 getBoundingClientRect 需异步查询）。

---

### 面试题 7：小程序 setData 的性能优化技巧？

**答：**
1. **减少数据量**：只传递变更的数据，使用路径更新 `this.setData({ 'list[0].name': 'xxx' })`
2. **减少频率**：合并多次 setData 为一次
3. **使用纯数据字段**：`pureDataPattern` 标记不参与渲染的数据
4. **避免后台页面 setData**：页面不可见时暂存数据，onShow 时再更新
5. **列表场景**：使用 recycle-view 组件实现虚拟列表

---

### 面试题 8：Taro 3 和 uni-app 的跨端原理有何区别？

**答：**
- **Taro 3** 采用**运行时适配**方案，在小程序端实现了一套类 DOM/BOM API（taro-runtime），React/Vue 代码通过这层运行时间接操作小程序视图。优点是框架兼容性好，缺点是运行时开销较大。
- **uni-app** 采用**编译时+运行时**混合方案，在编译阶段将 Vue SFC 转换为各平台原生代码（WXML/WXSS），运行时补充条件编译。编译产物更接近原生，性能更好，但框架绑定为 Vue。

---

### 面试题 9：React Native 新架构中 JSI 解决了什么问题？

**答：** 旧架构中 JS和 Native 通过 Bridge 通信，需要 JSON 序列化/反序列化，存在三个问题：(1) 序列化开销大；(2) 所有调用都是异步的；(3) 数据拷贝导致内存浪费。JSI 让 JS 直接持有 C++ Host Object 引用，可以同步调用 Native 方法，消除了序列化开销，是新架构的核心基础。

---

### 面试题 10：Flutter 为什么性能好？和 RN 有何本质区别？

**答：** Flutter 通过 Skia 引擎自绘 UI，不依赖平台原生组件，渲染链路更短且统一。RN 需要将 Virtual DOM 映射为原生组件，中间经过 Bridge/JSI 通信。Flutter 的 Dart AOT 编译为机器码，RN 的 JS 需要 JIT/解释执行。Flutter 的三棵树（Widget/Element/RenderObject）对应更直接的渲染流水线，而 RN 需要跨线程协调。

---

### 面试题 11：如何实现移动端首屏优化？

**答：** 多维度优化：
1. **网络层**：CDN、HTTP/2、资源预加载（preload/prefetch）、DNS 预解析
2. **资源层**：代码分割、Tree Shaking、图片 WebP、字体子集化
3. **渲染层**：SSR/SSG、骨架屏、关键 CSS 内联、异步加载非关键资源
4. **缓存层**：Service Worker、HTTP 强缓存/协商缓存、接口数据缓存
5. **体验层**：骨架屏过渡、渐进式加载、离线包方案

---

### 面试题 12：虚拟列表的原理是什么？

**答：** 虚拟列表的核心思想是**只渲染可视区域内的元素**。通过一个占位容器撑开滚动高度，监听 scroll 事件计算当前可见的起止索引，仅渲染该范围（加上缓冲区）内的 DOM 元素。当用户滚动时，动态替换渲染内容。这样无论数据量多大，DOM 节点数始终保持在常量级别。

---

### 面试题 13：移动端如何检测和优化弱网体验？

**答：**
1. **检测**：通过 `navigator.connection.effectiveType` 和 `rtt` 判断网络质量
2. **请求优化**：超时控制、指数退避重试、请求优先级队列、并发数限制
3. **资源降级**：弱网下加载低质量图片、简化动画、关闭非关键功能
4. **离线支持**：Service Worker 缓存关键资源、接口数据本地缓存
5. **用户反馈**：加载状态提示、离线状态提醒、手动重试入口

---

### 面试题 14：env(safe-area-inset-bottom) 和 constant() 有什么区别？

**答：** 两者功能相同，都是获取安全区域的间距值。`constant()` 是 iOS 11.0-11.2 的语法，`env()` 是 iOS 11.2+ 的标准语法。为了兼容，应同时书写两行，且 `constant()` 写在前面（CSS 后声明覆盖）。使用前必须设置 `viewport-fit=cover`。

---

### 面试题 15：passive 事件监听器的作用是什么？

**答：** 当添加 `{ passive: true }` 时，告知浏览器该事件处理器不会调用 `preventDefault()`。这样浏览器在等待 JS 执行的同时就可以开始滚动渲染，不需要等 JS 执行完毕确认是否阻止默认行为。对 touchmove/wheel 等高频事件，能显著提升滚动流畅度。Chrome 56+ 默认 `touchstart` 和 `touchmove` 为 passive。

---

### 面试题 16：Hybrid App 离线包方案的完整流程是什么？

**答：**
1. **构建阶段**：前端打包生成静态资源，按业务模块拆分，生成版本号和 MD5 校验
2. **发布阶段**：上传离线包到 CDN，下发配置（包含版本号、下载地址、增量/全量包）
3. **下载阶段**：App 启动时/定期检查更新，WiFi 下预下载，支持增量更新（bsdiff）
4. **加载阶段**：WebView 拦截请求，优先从本地离线包读取资源，miss 则走网络
5. **回退机制**：离线包校验失败或加载异常时，降级走线上 CDN

---

### 面试题 17：移动端 H5 如何处理键盘弹起导致的页面布局问题？

**答：**
- **Android**：键盘弹起会触发 `resize` 事件并改变 `window.innerHeight`，通过对比高度变化判断键盘状态，动态调整固定定位元素
- **iOS**：键盘弹起不改变视口高度，而是将页面整体上推。需要监听 `focus/blur` 事件，使用 `scrollIntoView` 确保输入框可见，键盘收起后手动触发 `window.scrollTo` 修复页面不回弹的问题
- **通用方案**：键盘弹起时将固定底部栏改为 `position: static`，使用 `visualViewport API` 精确获取可视区域

---

### 面试题 18：Vue/React 模板中的双花括号和 Liquid/Jekyll 模板冲突如何处理？

**答：** 使用 raw 标签包裹即可避免模板引擎解析冲突：

```html
{% raw %}
<div>{{ message }}</div>
<span>{{ count + 1 }}</span>
{% endraw %}
```

在 Vue 组件中示例：

```vue
{% raw %}
<template>
  <div class="app">
    <h1>{{ title }}</h1>
    <p>计数: {{ count }}</p>
    <button @click="count++">+1</button>
  </div>
</template>
{% endraw %}
```

React JSX 中使用花括号：

```jsx
{% raw %}
function App() {
  const [count, setCount] = useState(0);
  return (
    <div>
      <p>Count: {count}</p>
      <p>Double: {count * 2}</p>
    </div>
  );
}
{% endraw %}
```

---

> **总结**：移动端 H5 开发涉及适配、交互、通信、跨端、性能等多个维度。面试中需要深入理解每个方案的原理、优缺点和适用场景，并能结合实际项目经验给出最佳实践。建议重点掌握：(1) 适配方案的选型依据；(2) JSBridge 的通信原理；(3) 跨端框架的本质区别；(4) 性能优化的系统方法论。

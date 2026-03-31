# TypeScript 面试指南

## 一、基础类型

### 1.1 TypeScript 常见基础类型

> 面试题：TypeScript 有哪些基础类型？请列举并简要说明。

TypeScript 在 JavaScript 的基础上增加了静态类型系统，常见的基础类型包括：

```typescript
// 基本类型
let str: string = "hello";
let num: number = 42;
let bool: boolean = true;
let n: null = null;
let u: undefined = undefined;

// 数组
let arr1: number[] = [1, 2, 3];
let arr2: Array<string> = ["a", "b", "c"];

// 元组（Tuple）：固定长度和类型的数组
let tuple: [string, number] = ["hello", 42];

// 枚举（Enum）
enum Direction {
  Up,      // 默认从 0 开始
  Down,    // 1
  Left,    // 2
  Right    // 3
}

// 字符串枚举
enum Color {
  Red = "RED",
  Green = "GREEN",
  Blue = "BLUE"
}

// void：通常用于函数无返回值
function log(msg: string): void {
  console.log(msg);
}

// bigint 和 symbol
let big: bigint = 100n;
let sym: symbol = Symbol("key");
```

### 1.2 any、unknown 和 never 的区别

> 面试题：请详细说明 any、unknown 和 never 三者的区别及使用场景。

**any** 类型：

- 放弃了类型检查，允许赋值为任意类型
- 可以访问任意属性和调用任意方法，编译器不会报错
- 应尽量避免使用，使用 any 会丧失 TypeScript 的类型安全优势

```typescript
let a: any = 42;
a = "hello";       // OK
a.foo.bar;          // OK，编译器不报错（运行时可能出错）
a();                // OK
```

**unknown** 类型：

- 类型安全的 any，可以赋任意值，但在使用前必须进行类型收窄
- 不能直接访问属性或调用方法，需要先进行类型断言或类型守卫
- 推荐在不确定类型时使用 unknown 代替 any

```typescript
let b: unknown = 42;
b = "hello";        // OK，可以赋任意值

// b.toUpperCase(); // Error! 不能直接调用方法
// 必须先收窄类型
if (typeof b === "string") {
  b.toUpperCase();  // OK
}

// 或使用类型断言
(b as string).toUpperCase();
```

**never** 类型：

- 表示永远不会出现的值的类型，是所有类型的子类型
- 常见于：抛出异常的函数、永远不会返回的函数（死循环）、穷尽检查（exhaustive check）

```typescript
// 抛出异常
function throwError(msg: string): never {
  throw new Error(msg);
}

// 死循环
function infiniteLoop(): never {
  while (true) {}
}

// 穷尽检查
type Shape = "circle" | "square" | "triangle";

function getArea(shape: Shape) {
  switch (shape) {
    case "circle":
      return Math.PI * 10 * 10;
    case "square":
      return 10 * 10;
    case "triangle":
      return (10 * 10) / 2;
    default:
      // 如果所有 case 都已处理，shape 此时为 never
      const _exhaustiveCheck: never = shape;
      return _exhaustiveCheck;
  }
}
```

**三者对比总结：**

| 特性 | any | unknown | never |
|------|-----|---------|-------|
| 赋值给其他类型 | 可以 | 需要类型收窄 | 可以（是所有类型子类型） |
| 被其他类型赋值 | 可以 | 可以 | 不可以（除了 never 本身） |
| 访问属性/方法 | 可以 | 不可以（需收窄） | 不可以 |
| 类型安全性 | 无 | 有 | 有 |

---

## 二、interface 与 type 的区别

> 面试题：interface 和 type 有什么区别？什么时候用 interface，什么时候用 type？

### 2.1 相同点

两者都可以用来描述对象的形状或函数签名：

```typescript
// interface 定义对象
interface IUser {
  name: string;
  age: number;
}

// type 定义对象
type TUser = {
  name: string;
  age: number;
};

// interface 定义函数
interface IAdd {
  (a: number, b: number): number;
}

// type 定义函数
type TAdd = (a: number, b: number) => number;
```

### 2.2 不同点

**1. 声明合并（Declaration Merging）：**

interface 支持声明合并，同名 interface 会自动合并；type 不支持，重复定义会报错。

```typescript
interface IUser {
  name: string;
}
interface IUser {
  age: number;
}
// 合并为 { name: string; age: number }

// type TUser = { name: string; };
// type TUser = { age: number; }; // Error! 重复定义
```

**2. 扩展方式不同：**

interface 使用 `extends` 继承，type 使用 `&`（交叉类型）扩展。

```typescript
interface IAnimal {
  name: string;
}
interface IDog extends IAnimal {
  breed: string;
}

type TAnimal = { name: string };
type TDog = TAnimal & { breed: string };
```

**3. type 可以表示更多类型：**

type 可以定义联合类型、元组、基本类型别名、映射类型等，interface 不能。

```typescript
// 联合类型
type StringOrNumber = string | number;

// 元组
type Pair = [string, number];

// 基本类型别名
type Name = string;

// 映射类型
type Readonly<T> = { readonly [P in keyof T]: T[P] };

// 条件类型
type IsString<T> = T extends string ? true : false;
```

**4. interface 可以被类实现（implements）：**

```typescript
interface ICloneable {
  clone(): this;
}

class MyClass implements ICloneable {
  clone() {
    return Object.create(this);
  }
}
```

**使用建议：**
- 定义对象结构、类的契约时优先使用 interface
- 需要联合类型、交叉类型、条件类型、映射类型等高级特性时使用 type
- 需要声明合并（如第三方库类型扩展）时使用 interface

---

## 三、泛型（Generics）

> 面试题：什么是泛型？请举例说明泛型的常见使用场景。

泛型是 TypeScript 中实现代码复用和类型安全的核心机制，允许在定义函数、接口或类时使用类型参数，在使用时再指定具体类型。

### 3.1 泛型函数

```typescript
// 不使用泛型 —— 缺乏类型信息
function identity(arg: any): any {
  return arg;
}

// 使用泛型 —— 保留类型信息
function identity<T>(arg: T): T {
  return arg;
}

const result = identity<string>("hello"); // result: string
const result2 = identity(42);            // 类型推断：result2: number
```

### 3.2 泛型约束

```typescript
// 使用 extends 约束泛型
interface HasLength {
  length: number;
}

function logLength<T extends HasLength>(arg: T): number {
  return arg.length;
}

logLength("hello");     // OK
logLength([1, 2, 3]);   // OK
// logLength(42);        // Error! number 没有 length 属性
```

### 3.3 泛型接口与泛型类

```typescript
// 泛型接口
interface IRepository<T> {
  findById(id: string): T;
  save(entity: T): void;
}

// 泛型类
class Stack<T> {
  private items: T[] = [];
  
  push(item: T): void {
    this.items.push(item);
  }
  
  pop(): T | undefined {
    return this.items.pop();
  }
}

const numStack = new Stack<number>();
numStack.push(1);
numStack.push(2);
const top = numStack.pop(); // top: number | undefined
```

### 3.4 泛型中的 keyof 与索引访问

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: "Alice", age: 25 };
const name = getProperty(user, "name"); // string
const age = getProperty(user, "age");   // number
// getProperty(user, "email");           // Error! "email" 不在 keyof typeof user 中
```

### 3.5 泛型默认值

```typescript
interface IPagination<T = any> {
  data: T[];
  page: number;
  pageSize: number;
  total: number;
}

// 不传类型参数时使用默认值 any
const page1: IPagination = { data: [1, "2"], page: 1, pageSize: 10, total: 100 };
// 传入具体类型
const page2: IPagination<string> = { data: ["a", "b"], page: 1, pageSize: 10, total: 50 };
```

---

## 四、内置工具类型及实现原理

> 面试题：请列举 TypeScript 常用的内置工具类型，并手写其实现原理。

### 4.1 Partial\<T\> — 将所有属性变为可选

```typescript
type MyPartial<T> = {
  [P in keyof T]?: T[P];
};

interface IUser {
  name: string;
  age: number;
}
type PartialUser = MyPartial<IUser>;
// { name?: string; age?: number }
```

### 4.2 Required\<T\> — 将所有属性变为必选

```typescript
type MyRequired<T> = {
  [P in keyof T]-?: T[P];
};

// -? 表示移除可选修饰符
```

### 4.3 Readonly\<T\> — 将所有属性变为只读

```typescript
type MyReadonly<T> = {
  readonly [P in keyof T]: T[P];
};
```

### 4.4 Record\<K, T\> — 构造键为 K、值为 T 的对象类型

```typescript
type MyRecord<K extends keyof any, T> = {
  [P in K]: T;
};

type PageInfo = Record<"home" | "about" | "contact", { title: string }>;
```

### 4.5 Pick\<T, K\> — 从 T 中选取部分属性

```typescript
type MyPick<T, K extends keyof T> = {
  [P in K]: T[P];
};

type NameOnly = Pick<IUser, "name">;
// { name: string }
```

### 4.6 Omit\<T, K\> — 从 T 中排除部分属性

```typescript
type MyOmit<T, K extends keyof any> = Pick<T, Exclude<keyof T, K>>;

type WithoutAge = Omit<IUser, "age">;
// { name: string }
```

### 4.7 Exclude\<T, U\> — 从联合类型 T 中排除可以赋值给 U 的类型

```typescript
type MyExclude<T, U> = T extends U ? never : T;

type Result = Exclude<"a" | "b" | "c", "a" | "b">;
// "c"
```

### 4.8 Extract\<T, U\> — 从联合类型 T 中提取可以赋值给 U 的类型

```typescript
type MyExtract<T, U> = T extends U ? T : never;

type Result = Extract<"a" | "b" | "c", "a" | "b">;
// "a" | "b"
```

### 4.9 ReturnType\<T\> — 获取函数返回值类型

```typescript
type MyReturnType<T extends (...args: any) => any> = T extends (...args: any) => infer R
  ? R
  : any;

function fn() { return { x: 1, y: "hello" }; }
type FnReturn = MyReturnType<typeof fn>;
// { x: number; y: string }
```

### 4.10 Parameters\<T\> — 获取函数参数类型（元组）

```typescript
type MyParameters<T extends (...args: any) => any> = T extends (...args: infer P) => any
  ? P
  : never;

function greet(name: string, age: number): void {}
type GreetParams = MyParameters<typeof greet>;
// [name: string, age: number]
```

### 4.11 InstanceType\<T\> — 获取构造函数的实例类型

```typescript
type MyInstanceType<T extends abstract new (...args: any) => any> = T extends abstract new (
  ...args: any
) => infer R
  ? R
  : any;
```

### 4.12 NonNullable\<T\> — 从 T 中排除 null 和 undefined

```typescript
type MyNonNullable<T> = T extends null | undefined ? never : T;

type Result = NonNullable<string | null | undefined>;
// string
```

---

## 五、条件类型与 infer

> 面试题：什么是条件类型？请解释分布式条件类型和 infer 关键字的作用。

### 5.1 条件类型基本语法

条件类型的形式为 `T extends U ? X : Y`，类似于三元表达式，根据 T 是否可以赋值给 U 来决定类型。

```typescript
type IsString<T> = T extends string ? "yes" : "no";

type A = IsString<string>;  // "yes"
type B = IsString<number>;  // "no"
```

### 5.2 分布式条件类型（Distributive Conditional Types）

当条件类型的 T 是裸类型参数（即没有被包裹在其他类型中），且传入联合类型时，条件类型会对联合类型的每个成员分别进行计算，最终合并结果。

```typescript
type ToArray<T> = T extends any ? T[] : never;

// 分布式：联合类型的每个成员分别应用
type Result = ToArray<string | number>;
// string[] | number[]    而不是 (string | number)[]

// 如果想避免分布式行为，用元组包裹
type ToArrayNonDist<T> = [T] extends [any] ? T[] : never;
type Result2 = ToArrayNonDist<string | number>;
// (string | number)[]
```

**分布式条件类型在 Exclude 和 Extract 中的应用：**

```typescript
// Exclude 利用分布式特性逐个过滤
type Exclude<T, U> = T extends U ? never : T;

type Result = Exclude<"a" | "b" | "c", "a">;
// 展开过程：
// ("a" extends "a" ? never : "a") | ("b" extends "a" ? never : "b") | ("c" extends "a" ? never : "c")
// = never | "b" | "c"
// = "b" | "c"
```

### 5.3 infer 关键字

`infer` 用于在条件类型中声明一个待推断的类型变量，TypeScript 会根据实际传入的类型自动推断该变量的值。

```typescript
// 推断函数返回值类型
type GetReturnType<T> = T extends (...args: any[]) => infer R ? R : never;

type R1 = GetReturnType<() => string>;      // string
type R2 = GetReturnType<(x: number) => boolean>; // boolean

// 推断数组元素类型
type ElementType<T> = T extends (infer E)[] ? E : never;

type E1 = ElementType<number[]>;    // number
type E2 = ElementType<string[]>;    // string

// 推断 Promise 解包类型
type UnpackPromise<T> = T extends Promise<infer U> ? U : T;

type P1 = UnpackPromise<Promise<string>>;  // string
type P2 = UnpackPromise<number>;           // number

// 递归解包嵌套 Promise
type DeepUnpackPromise<T> = T extends Promise<infer U> ? DeepUnpackPromise<U> : T;

type P3 = DeepUnpackPromise<Promise<Promise<string>>>;  // string

// 推断元组第一个元素
type First<T extends any[]> = T extends [infer F, ...any[]] ? F : never;

type F1 = First<[1, 2, 3]>;   // 1
type F2 = First<[string]>;    // string

// 推断元组最后一个元素
type Last<T extends any[]> = T extends [...any[], infer L] ? L : never;

type L1 = Last<[1, 2, 3]>;    // 3
```

---

## 六、映射类型（Mapped Types）

> 面试题：什么是映射类型？如何使用映射类型实现类型转换？

映射类型通过遍历已有类型的键来创建新类型，语法为 `[P in K]: T`。

### 6.1 基本映射类型

```typescript
// 将所有属性变为可选
type Optional<T> = {
  [P in keyof T]?: T[P];
};

// 将所有属性变为只读
type Immutable<T> = {
  readonly [P in keyof T]: T[P];
};

// 将所有属性类型变为 boolean
type Flags<T> = {
  [P in keyof T]: boolean;
};

interface IUser {
  name: string;
  age: number;
  email: string;
}

type UserFlags = Flags<IUser>;
// { name: boolean; age: boolean; email: boolean }
```

### 6.2 映射修饰符（+/- 修饰符）

可以通过 `+` 或 `-` 前缀来添加或移除 `readonly` 和 `?` 修饰符。

```typescript
// 移除只读
type Mutable<T> = {
  -readonly [P in keyof T]: T[P];
};

// 移除可选（即变为必选）
type Concrete<T> = {
  [P in keyof T]-?: T[P];
};
```

### 6.3 Key Remapping（键重映射，TypeScript 4.1+）

使用 `as` 子句在映射类型中重命名键。

```typescript
// 给所有属性名加前缀
type Getters<T> = {
  [P in keyof T as `get${Capitalize<string & P>}`]: () => T[P];
};

interface IPerson {
  name: string;
  age: number;
}

type PersonGetters = Getters<IPerson>;
// {
//   getName: () => string;
//   getAge: () => number;
// }

// 过滤属性：通过 as never 移除键
type RemoveMethods<T> = {
  [P in keyof T as T[P] extends Function ? never : P]: T[P];
};

interface IMixed {
  name: string;
  age: number;
  greet(): void;
}

type DataOnly = RemoveMethods<IMixed>;
// { name: string; age: number }
```

---

## 七、模板字面量类型（Template Literal Types）

> 面试题：什么是模板字面量类型？有哪些内置的字符串操作类型？

TypeScript 4.1 引入了模板字面量类型，可以在类型系统中使用模板字符串语法，基于已有的字符串字面量类型生成新的字符串字面量类型。

```typescript
type World = "world";
type Greeting = `hello ${World}`; // "hello world"

// 联合类型会自动分布
type Color = "red" | "blue";
type Size = "small" | "large";
type Style = `${Size}-${Color}`;
// "small-red" | "small-blue" | "large-red" | "large-blue"
```

### 7.1 内置字符串操作类型

```typescript
// Uppercase —— 转大写
type Upper = Uppercase<"hello">; // "HELLO"

// Lowercase —— 转小写
type Lower = Lowercase<"HELLO">; // "hello"

// Capitalize —— 首字母大写
type Cap = Capitalize<"hello">;  // "Hello"

// Uncapitalize —— 首字母小写
type Uncap = Uncapitalize<"Hello">; // "hello"
```

### 7.2 实际应用：事件系统类型

```typescript
type EventName<T extends string> = `on${Capitalize<T>}`;

type ClickEvent = EventName<"click">;     // "onClick"
type ChangeEvent = EventName<"change">;   // "onChange"

// 完整的事件监听器类型
type EventHandlers<Events extends string> = {
  [E in Events as `on${Capitalize<E>}`]: (event: Event) => void;
};

type MouseEvents = EventHandlers<"click" | "mouseenter" | "mouseleave">;
// {
//   onClick: (event: Event) => void;
//   onMouseenter: (event: Event) => void;
//   onMouseleave: (event: Event) => void;
// }
```

### 7.3 模式匹配提取

```typescript
// 提取路由参数
type ExtractParams<T extends string> = T extends `${string}:${infer Param}/${infer Rest}`
  ? Param | ExtractParams<Rest>
  : T extends `${string}:${infer Param}`
  ? Param
  : never;

type Params = ExtractParams<"/user/:id/post/:postId">;
// "id" | "postId"
```

---

## 八、装饰器（Decorators）

> 面试题：TypeScript 中有哪几种装饰器？装饰器的执行顺序是什么？

装饰器是一种特殊声明，可以附加到类声明、方法、访问符、属性或参数上。使用 `@expression` 语法，`expression` 必须求值为一个函数。

### 8.1 四种装饰器

**1. 类装饰器：**

```typescript
function sealed(constructor: Function) {
  Object.seal(constructor);
  Object.seal(constructor.prototype);
}

@sealed
class Greeter {
  greeting: string;
  constructor(message: string) {
    this.greeting = message;
  }
}
```

**2. 方法装饰器：**

```typescript
function log(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
  const originalMethod = descriptor.value;
  descriptor.value = function (...args: any[]) {
    console.log(`调用 ${propertyKey}，参数：${JSON.stringify(args)}`);
    const result = originalMethod.apply(this, args);
    console.log(`返回值：${result}`);
    return result;
  };
  return descriptor;
}

class Calculator {
  @log
  add(a: number, b: number): number {
    return a + b;
  }
}
```

**3. 属性装饰器：**

```typescript
function defaultValue(value: any) {
  return function (target: any, propertyKey: string) {
    target[propertyKey] = value;
  };
}

class Settings {
  @defaultValue("zh-CN")
  language!: string;
}
```

**4. 参数装饰器：**

```typescript
function required(target: any, propertyKey: string, parameterIndex: number) {
  const requiredParams: number[] = Reflect.getOwnMetadata("required", target, propertyKey) || [];
  requiredParams.push(parameterIndex);
  Reflect.defineMetadata("required", requiredParams, target, propertyKey);
}

class UserService {
  getUser(@required id: string) {
    // ...
  }
}
```

### 8.2 装饰器工厂

装饰器工厂是一个返回装饰器函数的函数，允许传入参数自定义装饰器行为。

```typescript
function enumerable(value: boolean) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    descriptor.enumerable = value;
  };
}

class Person {
  @enumerable(false)
  greet() {
    return "Hello!";
  }
}
```

### 8.3 装饰器执行顺序

多个装饰器应用到同一声明时，执行顺序如下：

1. **参数装饰器** → **方法/访问器/属性装饰器** → **类装饰器**
2. 同一类型的多个装饰器：**从下往上**（从内到外）执行
3. 具体规则：
   - 实例成员：参数装饰器 → 方法装饰器（每个成员依次执行）
   - 静态成员：参数装饰器 → 方法装饰器
   - 构造函数：参数装饰器
   - 类装饰器：最后执行

```typescript
function classDecorator(name: string) {
  console.log(`类装饰器 ${name} 求值`);
  return function (constructor: Function) {
    console.log(`类装饰器 ${name} 执行`);
  };
}

function methodDecorator(name: string) {
  console.log(`方法装饰器 ${name} 求值`);
  return function (target: any, key: string, descriptor: PropertyDescriptor) {
    console.log(`方法装饰器 ${name} 执行`);
  };
}

@classDecorator("A")
@classDecorator("B")
class Example {
  @methodDecorator("C")
  @methodDecorator("D")
  method() {}
}

// 输出顺序：
// 方法装饰器 C 求值
// 方法装饰器 D 求值
// 方法装饰器 D 执行（从下往上）
// 方法装饰器 C 执行
// 类装饰器 A 求值
// 类装饰器 B 求值
// 类装饰器 B 执行（从下往上）
// 类装饰器 A 执行
```

---

## 九、类型守卫（Type Guards）

> 面试题：TypeScript 中有哪些类型守卫方式？

类型守卫用于在运行时缩小（收窄）类型范围，使 TypeScript 编译器在特定代码块中获得更精确的类型信息。

### 9.1 typeof 类型守卫

```typescript
function padLeft(value: string, padding: string | number): string {
  if (typeof padding === "number") {
    // 此处 padding 被收窄为 number
    return " ".repeat(padding) + value;
  }
  // 此处 padding 被收窄为 string
  return padding + value;
}
```

### 9.2 instanceof 类型守卫

```typescript
class Bird {
  fly() { console.log("flying"); }
}
class Fish {
  swim() { console.log("swimming"); }
}

function move(pet: Bird | Fish) {
  if (pet instanceof Bird) {
    pet.fly();   // OK
  } else {
    pet.swim();  // OK
  }
}
```

### 9.3 in 操作符类型守卫

```typescript
interface IAdmin {
  role: string;
  permissions: string[];
}
interface IUser {
  name: string;
  email: string;
}

function handlePerson(person: IAdmin | IUser) {
  if ("role" in person) {
    // person 被收窄为 IAdmin
    console.log(person.permissions);
  } else {
    // person 被收窄为 IUser
    console.log(person.email);
  }
}
```

### 9.4 自定义类型守卫（is 关键字）

```typescript
interface ICat {
  meow(): void;
}
interface IDog {
  bark(): void;
}

// 自定义类型守卫函数
function isCat(animal: ICat | IDog): animal is ICat {
  return (animal as ICat).meow !== undefined;
}

function handleAnimal(animal: ICat | IDog) {
  if (isCat(animal)) {
    animal.meow();  // OK
  } else {
    animal.bark();  // OK
  }
}
```

### 9.5 可辨识联合（Discriminated Unions）

```typescript
interface ICircle {
  kind: "circle";
  radius: number;
}
interface ISquare {
  kind: "square";
  sideLength: number;
}
interface ITriangle {
  kind: "triangle";
  base: number;
  height: number;
}

type Shape = ICircle | ISquare | ITriangle;

function getArea(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "square":
      return shape.sideLength ** 2;
    case "triangle":
      return (shape.base * shape.height) / 2;
  }
}
```

---

## 十、声明文件（Declaration Files）

> 面试题：什么是声明文件？.d.ts 文件有什么作用？如何为第三方库编写声明文件？

### 10.1 声明文件的作用

声明文件（`.d.ts`）为 JavaScript 代码提供类型信息，使 TypeScript 编译器能够对非 TypeScript 编写的代码进行类型检查。它只包含类型声明，不包含具体实现。

### 10.2 常见声明方式

```typescript
// global.d.ts — 全局声明文件

// 声明全局变量
declare const APP_VERSION: string;

// 声明全局函数
declare function sendAnalytics(event: string, data?: Record<string, any>): void;

// 声明全局接口
declare interface Window {
  __APP_CONFIG__: {
    apiUrl: string;
    debug: boolean;
  };
}

// 声明模块
declare module "my-library" {
  export function doSomething(input: string): number;
  export interface Options {
    timeout: number;
    retries: number;
  }
}

// 声明通配符模块（如处理 CSS/图片等非 JS 资源）
declare module "*.css" {
  const content: Record<string, string>;
  export default content;
}

declare module "*.png" {
  const value: string;
  export default value;
}

declare module "*.svg" {
  import React from "react";
  const SVGComponent: React.FC<React.SVGProps<SVGSVGElement>>;
  export default SVGComponent;
}
```

### 10.3 三斜线指令与 @types

```typescript
// 三斜线指令引用其他声明文件
/// <reference path="./global.d.ts" />
/// <reference types="node" />

// @types 包：DefinitelyTyped 社区维护的类型声明
// 安装方式：npm install @types/lodash -D
// TypeScript 会自动从 node_modules/@types 中查找类型
```

---

## 十一、tsconfig.json 重要配置

> 面试题：tsconfig.json 中有哪些重要的配置项？请列举并说明。

### 11.1 编译相关

```jsonc
{
  "compilerOptions": {
    // 目标 JS 版本
    "target": "ES2020",
    
    // 模块系统
    "module": "ESNext",
    
    // 模块解析策略：node（Node.js风格）或 bundler（打包工具风格，TS5.0+）
    "moduleResolution": "bundler",
    
    // 输出目录
    "outDir": "./dist",
    
    // 根目录
    "rootDir": "./src",
    
    // 启用所有严格类型检查
    "strict": true,
    
    // 严格的 null 检查（strict 包含此项）
    "strictNullChecks": true,
    
    // 不允许隐式 any（strict 包含此项）
    "noImplicitAny": true,
    
    // 允许导入 JSON 模块
    "resolveJsonModule": true,
    
    // 允许导入 .js 后缀（ESM 互操作）
    "allowImportingTsExtensions": false,
    
    // esModuleInterop：允许从 CommonJS 模块使用默认导入
    "esModuleInterop": true,
    
    // 跳过对声明文件的类型检查（加速编译）
    "skipLibCheck": true,
    
    // 强制文件名大小写一致
    "forceConsistentCasingInFileNames": true,
    
    // 生成声明文件
    "declaration": true,
    
    // 生成 source map
    "sourceMap": true,
    
    // 启用装饰器（实验性）
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    
    // 路径别名
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"]
    },
    
    // JSX 支持
    "jsx": "react-jsx",
    
    // 库文件
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    
    // 增量编译（加速二次编译）
    "incremental": true,
    
    // 隔离模块（确保每个文件可以独立转译，Babel 兼容）
    "isolatedModules": true,
    
    // 不输出文件（仅做类型检查，适合配合 Babel/esbuild/swc 使用）
    "noEmit": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "**/*.test.ts"]
}
```

### 11.2 strict 模式包含的选项

`"strict": true` 是一个便捷选项，等价于同时开启以下所有选项：

| 选项 | 说明 |
|------|------|
| strictNullChecks | null 和 undefined 不可以赋值给其他类型 |
| noImplicitAny | 禁止隐式 any 类型 |
| strictFunctionTypes | 函数参数类型双变检查（更严格） |
| strictBindCallApply | 严格检查 bind/call/apply 参数类型 |
| strictPropertyInitialization | 类属性必须在构造函数中初始化 |
| noImplicitThis | 禁止隐式 this 为 any |
| alwaysStrict | 文件中始终使用严格模式 |
| useUnknownInCatchVariables | catch 变量类型为 unknown 而非 any |

---

## 十二、协变与逆变

> 面试题：什么是协变和逆变？在 TypeScript 中如何体现？

协变（Covariance）和逆变（Contravariance）描述了类型之间的子类型关系在复合类型中的传递方式。

### 12.1 概念解释

假设 `Dog extends Animal`（Dog 是 Animal 的子类型）：

- **协变（Covariance）**：`F<Dog>` 也是 `F<Animal>` 的子类型，子类型关系方向**一致**
- **逆变（Contravariance）**：`F<Animal>` 是 `F<Dog>` 的子类型，子类型关系方向**相反**
- **不变（Invariance）**：两者之间没有子类型关系
- **双变（Bivariance）**：两个方向都兼容

### 12.2 协变 —— 返回值位置

在 TypeScript 中，类型在返回值位置上是协变的：

```typescript
class Animal {
  name: string = "";
}

class Dog extends Animal {
  breed: string = "";
}

// 函数返回值是协变的
type AnimalFactory = () => Animal;
type DogFactory = () => Dog;

let animalFactory: AnimalFactory;
let dogFactory: DogFactory = () => new Dog();

// Dog 是 Animal 的子类型
// () => Dog 也是 () => Animal 的子类型（协变）
animalFactory = dogFactory; // OK! 协变
// dogFactory = animalFactory; // Error! 返回 Animal 不一定是 Dog
```

### 12.3 逆变 —— 参数位置

在 `strictFunctionTypes` 开启时，函数参数类型是逆变的：

```typescript
type AnimalHandler = (animal: Animal) => void;
type DogHandler = (dog: Dog) => void;

let animalHandler: AnimalHandler = (animal) => {
  console.log(animal.name);
};
let dogHandler: DogHandler = (dog) => {
  console.log(dog.breed);
};

// 函数参数是逆变的（strictFunctionTypes 开启时）
// Animal 是 Dog 的父类型
// (animal: Animal) => void 是 (dog: Dog) => void 的子类型（逆变）
dogHandler = animalHandler; // OK! 逆变。处理 Animal 的函数自然能处理 Dog
// animalHandler = dogHandler; // Error! 处理 Dog 的函数不一定能处理所有 Animal
```

### 12.4 实际应用

```typescript
// 数组是协变的（readonly 数组在 TypeScript 中是协变的）
let dogs: readonly Dog[] = [new Dog()];
let animals: readonly Animal[] = dogs; // OK! 协变

// 但可变数组在概念上应该是不变的
// TypeScript 为了实用性允许可变数组协变（不够严格但很方便）
let mutableDogs: Dog[] = [new Dog()];
let mutableAnimals: Animal[] = mutableDogs; // OK（TypeScript 的设计取舍）

// 利用逆变实现精确的类型约束
interface Comparable<T> {
  compareTo(other: T): number;
}

// 由于参数逆变，Comparable<Animal> 是 Comparable<Dog> 的子类型
function sortAnimals<T extends Comparable<T>>(items: T[]): T[] {
  return items.sort((a, b) => a.compareTo(b));
}
```

### 12.5 总结口诀

- **协变（covariant）**：子类型关系保持一致，出现在**输出/返回值**位置
- **逆变（contravariant）**：子类型关系反转，出现在**输入/参数**位置
- **不变（invariant）**：既是输入又是输出时（如可变属性），理论上应该不变
- TypeScript 中：`strictFunctionTypes` 启用时参数逆变；不启用时参数双变（更宽松）

---

## 总结

TypeScript 的类型系统是图灵完备的，掌握以上核心概念不仅能帮助你通过面试，更能让你在实际项目中写出更安全、更可维护的代码。重点需要深入理解的知识点包括：

1. **any vs unknown vs never** 的本质区别和使用场景
2. **interface 和 type** 的选择策略
3. **泛型**及其约束、默认值、keyof 等高级用法
4. **工具类型**的实现原理（本质是映射类型 + 条件类型 + infer 的组合）
5. **条件类型**的分布式特性和 infer 推断
6. **协变与逆变**在函数类型中的体现

建议在准备面试时结合实际项目经验，理解每个特性在真实场景中解决了什么问题，这样才能在面试中游刃有余。

# Go语言基础面试指南

## 一、Go语言特点

Go（又称 Golang）是 Google 于 2009 年发布的开源编程语言，由 Robert Griesemer、Rob Pike 和 Ken Thompson 设计。其核心特点如下：

### 1.1 静态类型

Go 是静态类型语言，所有变量的类型在编译期确定。类型系统简洁但完备，支持类型推断（`:=`），在保证类型安全的前提下减少了样板代码。

### 1.2 编译型语言

Go 代码直接编译为机器码，无需虚拟机或解释器。编译速度极快，是 Go 设计的核心目标之一。交叉编译非常方便，通过 `GOOS` 和 `GOARCH` 环境变量即可编译不同平台的二进制文件。

### 1.3 垃圾回收（GC）

Go 内置垃圾回收器，开发者无需手动管理内存。GC 采用三色标记-清扫算法并持续优化，STW（Stop The World）时间已控制在亚毫秒级别。

### 1.4 原生并发支持

Go 通过 goroutine 和 channel 提供了语言级别的并发原语，goroutine 的创建成本极低（初始栈仅几 KB），可轻松创建数十万个并发任务。

### 1.5 简洁语法

Go 故意省略了继承、泛型（1.18 之前）、异常等复杂特性，推崇"少即是多"的设计哲学。代码风格统一（`gofmt`），减少了团队协作中的争论。

> **面试题：Go语言相比Java/C++有哪些优势和劣势？**

**优势：**
- 编译速度快，部署简单（单一二进制文件）
- 原生并发模型，goroutine 比线程更轻量
- 内置垃圾回收，无需手动内存管理
- 语法简洁，学习曲线低
- 强大的标准库（net/http、encoding/json 等）
- 交叉编译方便

**劣势：**
- 泛型支持较晚（1.18 才引入），且功能仍在完善
- 错误处理较为繁琐（大量 `if err != nil`）
- 没有传统面向对象的继承机制
- 包管理生态相对较新（Go Modules 从 1.11 开始）

---

## 二、基础数据类型

### 2.1 整型

```go
// 有符号: int8, int16, int32, int64, int
// 无符号: uint8, uint16, uint32, uint64, uint
// 特殊: uintptr(存放指针), byte(uint8别名), rune(int32别名)
var a int = 42
var b int64 = 100
```

`int` 和 `uint` 的大小取决于平台（32位系统为4字节，64位系统为8字节）。

### 2.2 浮点型

```go
var f1 float32 = 3.14
var f2 float64 = 3.141592653589793
```

默认浮点字面量为 `float64`。Go 没有 `double` 类型，`float64` 即为双精度浮点。

### 2.3 字符串 string

```go
s := "Hello, 世界"
fmt.Println(len(s))    // 13 (字节数，非字符数)
fmt.Println(utf8.RuneCountInString(s)) // 9 (字符数)
```

### 2.4 布尔 bool

```go
var b bool = true
// Go中布尔值不能与整型互转，不能用 0/1 代替
```

### 2.5 byte 与 rune

- `byte` 是 `uint8` 的别名，用于表示 ASCII 字符或原始字节
- `rune` 是 `int32` 的别名，用于表示 Unicode 码点

```go
s := "Go语言"
for i, r := range s {
    fmt.Printf("index=%d, rune=%c, unicode=%U\n", i, r, r)
}
```

---

## 三、复合数据类型

### 3.1 数组 Array

```go
var arr [5]int              // 零值初始化
arr2 := [3]int{1, 2, 3}    // 字面量初始化
arr3 := [...]int{1, 2, 3}  // 编译器自动推断长度
```

数组是**值类型**，赋值和传参都会复制整个数组。数组的长度是类型的一部分，`[3]int` 和 `[5]int` 是不同类型。

### 3.2 切片 Slice

```go
s := make([]int, 5, 10)  // len=5, cap=10
s2 := []int{1, 2, 3}
s3 := arr[1:3]           // 从数组创建切片
```

### 3.3 映射 Map

```go
m := make(map[string]int)
m["age"] = 25
value, ok := m["age"]  // 两值返回判断key是否存在
```

### 3.4 结构体 Struct

```go
type User struct {
    Name string
    Age  int
}
u := User{Name: "Alice", Age: 30}
```

---

## 四、Slice 底层原理

> **面试题：请详细描述 slice 的底层结构和扩容机制。**

### 4.1 底层数据结构

Slice 在 runtime 中对应 `reflect.SliceHeader`：

```go
type SliceHeader struct {
    Data uintptr  // 指向底层数组的指针
    Len  int      // 当前长度
    Cap  int      // 容量
}
```

Slice 本身是一个包含三个字段的结构体（24 字节在 64 位系统上），传递 slice 时传递的是这个结构体的拷贝（浅拷贝），但底层数组数据是共享的。

### 4.2 扩容机制

当 `append` 导致长度超过容量时，需要扩容：

**Go 1.18 之前的策略：**
- 如果新容量大于旧容量的 2 倍，则使用新容量
- 如果旧容量小于 1024，则新容量 = 旧容量 × 2
- 如果旧容量 >= 1024，则新容量 = 旧容量 × 1.25，直到满足需求

**Go 1.18+ 的策略（更平滑的过渡）：**
- 如果新容量大于旧容量的 2 倍，则使用新容量
- 如果旧容量小于 256，则新容量 = 旧容量 × 2
- 否则 `newcap = oldcap + (oldcap + 3*256) / 4`，直到满足需求

扩容后还会进行**内存对齐**，实际分配的容量可能比计算值稍大。

```go
s := make([]int, 0, 3)
fmt.Printf("len=%d, cap=%d, ptr=%p\n", len(s), cap(s), s) // cap=3
s = append(s, 1, 2, 3, 4)
fmt.Printf("len=%d, cap=%d, ptr=%p\n", len(s), cap(s), s) // cap=6, 地址已变
```

### 4.3 常见陷阱

```go
// 陷阱1：切片共享底层数组
a := []int{1, 2, 3, 4, 5}
b := a[1:3]   // b = [2, 3]
b[0] = 20     // a 也被修改！a = [1, 20, 3, 4, 5]

// 陷阱2：append 可能影响原切片
a := []int{1, 2, 3, 4, 5}
b := a[1:3]         // b = [2, 3], len=2, cap=4
b = append(b, 100)  // 修改了 a[3]！a = [1, 2, 3, 100, 5]

// 解决方案：使用完整切片表达式限制容量
b := a[1:3:3]       // len=2, cap=2, append 将触发扩容
```

---

## 五、Map 底层原理

> **面试题：Go 中 map 的底层实现是什么？为什么遍历是无序的？**

### 5.1 底层结构

Go 的 map 底层是**哈希表**，核心结构为 `runtime.hmap`：

```go
type hmap struct {
    count     int            // 元素个数
    flags     uint8
    B         uint8          // 桶的数量 = 2^B
    noverflow uint16         // 溢出桶的近似数量
    hash0     uint32         // 哈希种子
    buckets    unsafe.Pointer // 桶数组
    oldbuckets unsafe.Pointer // 扩容时的旧桶
    nevacuate  uintptr       // 扩容迁移进度
    extra *mapextra
}
```

每个桶（`bmap`）可以存储 **8 个键值对**。桶中使用 `tophash` 数组（存储哈希值的高 8 位）加速查找。当桶满时，会链接**溢出桶**。

### 5.2 负载因子与扩容

- **负载因子** = count / (2^B)，默认阈值为 **6.5**
- **等量扩容**：溢出桶过多时触发（整理数据但不增加桶数量）
- **翻倍扩容**：负载因子超过 6.5 时触发（桶数量翻倍）

扩容采用**渐进式**策略，每次访问 map 时迁移少量数据，避免一次性大量迁移导致的延迟。

### 5.3 遍历无序

Go 故意在 `range` 遍历 map 时引入随机起始位置（随机选择起始桶和桶内起始位置），这是为了防止开发者依赖遍历顺序。

### 5.4 并发安全

map 不是并发安全的。并发读写会导致 `fatal error: concurrent map read and map write`。解决方案：
1. 使用 `sync.RWMutex` 保护
2. 使用 `sync.Map`（读多写少场景更优）

---

## 六、String 底层原理

> **面试题：Go 中 string 是如何实现的？string 和 []byte 的转换有什么需要注意的？**

### 6.1 底层结构

```go
type StringHeader struct {
    Data uintptr  // 指向底层字节数组
    Len  int      // 字节长度
}
```

string 在 Go 中是**不可变**的，任何修改操作都会产生新的字符串。

### 6.2 UTF-8 编码

Go 的字符串默认采用 UTF-8 编码。中文字符通常占 3 个字节：

```go
s := "Hello, 世界"
fmt.Println(len(s))                    // 13
fmt.Println(utf8.RuneCountInString(s)) // 9
fmt.Println([]rune(s))                 // [72 101 108 108 111 44 32 19990 30028]
```

### 6.3 string 与 []byte 转换

```go
s := "hello"
b := []byte(s)   // 需要内存拷贝
s2 := string(b)  // 需要内存拷贝
```

标准转换涉及**内存拷贝**，因为 string 不可变而 []byte 可变。编译器在某些场景（如 map 查找、字符串比较）会优化避免拷贝。

高性能场景可通过 `unsafe` 实现零拷贝转换（需自行保证安全）：

```go
func StringToBytes(s string) []byte {
    return *(*[]byte)(unsafe.Pointer(&s))
}
```

### 6.4 字符串拼接效率

```go
// 方式1: + 拼接（每次产生新字符串，效率低）
s := "a" + "b" + "c"

// 方式2: fmt.Sprintf（使用反射，较慢）
s := fmt.Sprintf("%s%s%s", "a", "b", "c")

// 方式3: strings.Builder（推荐，内部用 []byte 缓冲）
var builder strings.Builder
builder.WriteString("a")
builder.WriteString("b")
result := builder.String()

// 方式4: strings.Join
s := strings.Join([]string{"a", "b", "c"}, "")
```

性能排序（从快到慢）：`strings.Builder` ≈ `bytes.Buffer` > `strings.Join` > `+` > `fmt.Sprintf`

---

## 七、指针

### 7.1 与 C 指针的区别

| 特性 | Go 指针 | C 指针 |
|------|---------|--------|
| 指针运算 | 不支持 | 支持 |
| 类型安全 | 强类型 | 可随意转换 |
| 空值 | nil | NULL |
| 垃圾回收 | GC 管理 | 手动管理 |

### 7.2 unsafe.Pointer

`unsafe.Pointer` 是 Go 中绕过类型安全的桥梁，可以在任意指针类型之间转换：

```go
// unsafe.Pointer 的合法转换:
// 1. 任意指针类型 <-> unsafe.Pointer
// 2. unsafe.Pointer <-> uintptr

// 通过 unsafe.Pointer 进行类型转换
func Float64bits(f float64) uint64 {
    return *(*uint64)(unsafe.Pointer(&f))
}

// 通过 unsafe 访问结构体私有字段
type Demo struct {
    a bool    // 偏移0
    b int32   // 偏移4（因为对齐）
    c int64   // 偏移8
}
d := Demo{a: true, b: 42, c: 100}
p := unsafe.Pointer(&d)
// 读取字段 b
bPtr := (*int32)(unsafe.Pointer(uintptr(p) + unsafe.Offsetof(d.b)))
fmt.Println(*bPtr) // 42
```

---

## 八、Interface 详解

> **面试题：Go 中 interface 的底层是怎么实现的？nil interface 和 nil 有什么区别？**

### 8.1 接口的隐式实现

Go 的接口是**隐式实现**的，不需要 `implements` 关键字：

```go
type Writer interface {
    Write([]byte) (int, error)
}

// os.File 实现了 Writer 接口，无需显式声明
type File struct { /* ... */ }
func (f *File) Write(b []byte) (int, error) { /* ... */ }
```

### 8.2 底层结构

**非空接口 `iface`：**
```go
type iface struct {
    tab  *itab          // 类型信息和方法表
    data unsafe.Pointer // 指向实际数据
}

type itab struct {
    inter *interfacetype // 接口类型
    _type *_type         // 具体类型
    hash  uint32         // 类型哈希值（用于快速类型断言）
    fun   [1]uintptr     // 方法表（变长数组）
}
```

**空接口 `eface`：**
```go
type eface struct {
    _type *_type         // 类型信息
    data  unsafe.Pointer // 数据指针
}
```

### 8.3 nil interface 陷阱

```go
var w io.Writer       // w = nil (tab=nil, data=nil)
var f *os.File        // f = nil
w = f                 // w != nil! (tab 不为 nil，data 为 nil)

// 判断时:
fmt.Println(w == nil) // false！
fmt.Println(f == nil) // true
```

接口值只有在**类型和值都为 nil** 时才等于 nil。

### 8.4 类型断言与类型选择

```go
// 类型断言
val, ok := i.(string)

// 类型选择
switch v := i.(type) {
case string:
    fmt.Println("string:", v)
case int:
    fmt.Println("int:", v)
default:
    fmt.Println("unknown")
}
```

---

## 九、Struct

### 9.1 结构体嵌入（组合）

Go 通过嵌入（embedding）替代继承：

```go
type Animal struct {
    Name string
}
func (a Animal) Speak() string { return a.Name + " speaks" }

type Dog struct {
    Animal   // 嵌入，Dog 自动获得 Animal 的字段和方法
    Breed string
}

d := Dog{Animal: Animal{Name: "Buddy"}, Breed: "Labrador"}
fmt.Println(d.Name)    // 直接访问
fmt.Println(d.Speak()) // 直接调用
```

### 9.2 值接收者 vs 指针接收者

```go
type Counter struct {
    count int
}

// 值接收者：不修改原对象
func (c Counter) GetCount() int { return c.count }

// 指针接收者：可修改原对象
func (c *Counter) Increment() { c.count++ }
```

**方法集规则：**
- `T` 类型的方法集包含所有**值接收者**方法
- `*T` 类型的方法集包含所有**值接收者 + 指针接收者**方法
- 这影响接口的实现：如果接口方法使用指针接收者实现，只有 `*T` 满足接口

```go
type Sayer interface {
    Say()
}
type Person struct{}
func (p *Person) Say() {} // 指针接收者

var s Sayer
// s = Person{}   // 编译错误！Person 的方法集不包含 Say()
s = &Person{}     // OK
```

---

## 十、错误处理

> **面试题：Go 的错误处理方式有什么优缺点？errors.Is 和 errors.As 有什么区别？**

### 10.1 error 接口

```go
type error interface {
    Error() string
}
```

### 10.2 自定义错误

```go
// 方式1: errors.New
var ErrNotFound = errors.New("not found")

// 方式2: fmt.Errorf（支持 %w 包装）
err := fmt.Errorf("query user: %w", ErrNotFound)

// 方式3: 自定义错误类型
type ValidationError struct {
    Field   string
    Message string
}
func (e *ValidationError) Error() string {
    return fmt.Sprintf("field %s: %s", e.Field, e.Message)
}
```

### 10.3 errors.Is 与 errors.As

```go
// errors.Is: 判断错误链中是否包含特定错误值
if errors.Is(err, ErrNotFound) {
    // 处理 not found
}

// errors.As: 判断错误链中是否包含特定错误类型，并提取
var ve *ValidationError
if errors.As(err, &ve) {
    fmt.Println(ve.Field) // 可以访问具体字段
}
```

`errors.Is` 比较的是**值**（类似 `==`），`errors.As` 比较的是**类型**（类似类型断言）。两者都会递归解包 `Unwrap()` 链。

---

## 十一、defer

> **面试题：以下代码输出什么？**

```go
func f() int {
    x := 0
    defer func() { x++ }()
    return x  // 返回 0（返回值已经确定为0，defer修改的是局部变量x）
}

func g() (x int) {
    defer func() { x++ }()
    return 0  // 返回 1（defer修改的是命名返回值x）
}
```

### 11.1 执行顺序：LIFO（后进先出）

```go
defer fmt.Println("1")
defer fmt.Println("2")
defer fmt.Println("3")
// 输出: 3, 2, 1
```

### 11.2 defer 与 return 的关系

执行顺序：**设置返回值 → 执行 defer → RET 返回**

### 11.3 defer 闭包陷阱

```go
// 陷阱：循环中的 defer
for i := 0; i < 5; i++ {
    defer fmt.Println(i) // 输出 4,3,2,1,0 — 参数在 defer 时求值
}

// 陷阱：defer 闭包捕获变量
for i := 0; i < 5; i++ {
    defer func() {
        fmt.Println(i) // 全部输出 5 — 闭包捕获的是变量引用
    }()
}

// 修正：通过参数传递
for i := 0; i < 5; i++ {
    defer func(n int) {
        fmt.Println(n) // 输出 4,3,2,1,0
    }(i)
}
```

---

## 十二、panic 与 recover

```go
func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic recovered: %v", r)
        }
    }()
    return a / b, nil
}
```

**关键规则：**
1. `recover()` 必须在 `defer` 函数中直接调用才有效
2. `recover()` 只能捕获当前 goroutine 的 panic
3. 不建议滥用 panic/recover，Go 推荐显式错误处理

---

## 十三、init 函数

```go
package main

import "fmt"

var x = initVar()

func initVar() int {
    fmt.Println("var init")
    return 1
}

func init() {
    fmt.Println("init 1")
}

func init() {
    fmt.Println("init 2")
}

func main() {
    fmt.Println("main")
}
// 输出: var init → init 1 → init 2 → main
```

**执行顺序：** 包级变量初始化 → init 函数（按源文件中的出现顺序） → main。  
如果有依赖包，则被导入的包先初始化。一个包中可以有多个 init 函数。

---

## 十四、包管理（Go Modules）

> **面试题：Go Modules 中 go.mod 和 go.sum 分别是什么作用？**

- **go.mod**：声明模块路径和依赖关系（module path、Go 版本、require、replace、exclude）
- **go.sum**：记录依赖的加密哈希值，确保构建的可重复性和安全性

```
// go.mod 示例
module github.com/myproject
go 1.21
require (
    github.com/gin-gonic/gin v1.9.1
    google.golang.org/grpc v1.58.0
)
```

常用命令：`go mod init`、`go mod tidy`、`go mod vendor`、`go mod download`。

---

## 十五、常见关键字

### 15.1 make vs new

```go
// make: 用于 slice、map、channel 的初始化，返回类型本身
s := make([]int, 0, 10)   // []int
m := make(map[string]int)  // map[string]int
ch := make(chan int, 5)     // chan int

// new: 分配内存并返回指针，适用于任意类型
p := new(int)    // *int, 值为 0
sp := new(User)  // *User, 零值初始化
```

### 15.2 select

select 用于多路 channel 复用，语法类似 switch：

```go
select {
case msg := <-ch1:
    fmt.Println(msg)
case ch2 <- data:
    fmt.Println("sent")
case <-time.After(3 * time.Second):
    fmt.Println("timeout")
default:
    fmt.Println("no channel ready")
}
```

### 15.3 range

```go
// range slice: index, value
for i, v := range slice {}
// range map: key, value（无序）
for k, v := range m {}
// range string: index, rune
for i, r := range "Hello, 世界" {}
// range channel: value（阻塞直到channel关闭）
for v := range ch {}
```

### 15.4 fallthrough

Go 的 switch 默认不会穿透，需要 `fallthrough` 显式声明：

```go
switch n {
case 1:
    fmt.Println("one")
    fallthrough
case 2:
    fmt.Println("two") // n=1 时也会执行
}
```

---

## 十六、反射（reflect）

> **面试题：Go 中反射的三大法则是什么？反射有哪些使用场景？**

### 16.1 三大法则

1. 从接口值可以获取反射对象：`reflect.TypeOf(i)` / `reflect.ValueOf(i)`
2. 从反射对象可以获取接口值：`v.Interface()`
3. 要修改反射对象，其值必须可设置（addressable）：需传指针

```go
x := 3.14
v := reflect.ValueOf(&x)
v.Elem().SetFloat(2.71) // 通过指针的 Elem() 才能修改
```

### 16.2 常见用法

```go
t := reflect.TypeOf(user)
for i := 0; i < t.NumField(); i++ {
    field := t.Field(i)
    fmt.Printf("Name: %s, Type: %s, Tag: %s\n",
        field.Name, field.Type, field.Tag.Get("json"))
}
```

### 16.3 反射的性能

反射操作比直接调用慢 **1~2 个数量级**，因为涉及类型查找、接口装箱/拆箱等开销。在性能敏感路径上应避免使用。

**适用场景：** JSON/XML 序列化、ORM 框架、依赖注入、通用工具函数。

---

## 经典综合面试题

> **面试题：`[]int` 能转换成 `[]interface{}` 吗？为什么？**

不能直接转换。因为 `[]int` 的内存布局是连续的 int 值，每个元素占 8 字节；`[]interface{}` 的每个元素是 16 字节（type + data），内存布局完全不同，无法简单的类型转换，必须逐个复制：

```go
ints := []int{1, 2, 3}
interfaces := make([]interface{}, len(ints))
for i, v := range ints {
    interfaces[i] = v
}
```

> **面试题：Go 函数参数传递是值传递还是引用传递？**

Go 中**所有参数传递都是值传递**。但需要理解不同类型"值"的含义：
- 基本类型：复制值本身
- 指针：复制指针地址（指向同一数据）
- slice：复制 SliceHeader（Data/Len/Cap），底层数组共享
- map：复制指针（底层 hmap 共享）
- channel：复制指针（底层 hchan 共享）

因此 slice、map、channel 虽然是值传递，但修改内容时可以影响原始数据。但如果在函数内部 append 导致 slice 扩容，原始 slice 将不受影响。

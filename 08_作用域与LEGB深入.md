# 08. 作用域与 LEGB 深入

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐ (高级) |
> | **前置知识** | [01 函数](01_函数篇.md)、[07 引用机制](07_引用与内存机制.md) |
> | **学习目标** | 掌握 LEGB 完整规则、理解闭包 cell 对象、能用 dis 看作用域指令、解释 UnboundLocalError |
> | **CPython 版本** | 3.12+ |
> | **规范 vs 实现** | LEGB 规则、global/nonlocal、闭包语义为语言规范；🔬 LOAD_FAST/LOAD_DEREF/cell 对象为 CPython 实现 |

---

> 名字（变量）查找是 Python 运行时的核心动作之一。  
> 理解作用域 = 理解闭包、装饰器、模块、类的运行机制。

---

## 8.0 知识地图

```
名字查找的四个层级（LEGB）：

  ┌──────────────────────────────┐
  │ Built-in   内置作用域         │  print, len, ...
  └──────────────────────────────┘
              ▲ 找不到再往这里找
  ┌──────────────────────────────┐
  │ Global     模块作用域         │  模块顶层定义的名字
  └──────────────────────────────┘
              ▲
  ┌──────────────────────────────┐
  │ Enclosing  外层函数作用域     │  外层函数的局部名字
  └──────────────────────────────┘
              ▲
  ┌──────────────────────────────┐
  │ Local      当前函数局部作用域 │  当前函数内定义的名字
  └──────────────────────────────┘
              ▲ 先找这里
              │
            访问 x
```

**本章要回答**：
1. 一个名字 `x` 是怎么被找到的？
2. `global` / `nonlocal` 到底改变了什么？
3. 闭包变量保存在哪里？
4. 类作用域为什么"诡异"？
5. 模块导入时发生了什么？

---

## 8.1 命名空间：作用域的实质

### 8.1.1 命名空间 = 字典

每个作用域底层是一个**字典**：键是名字，值是对象引用。

```python
# ─────────────────────────────────────
# 命名空间就是字典
# ─────────────────────────────────────
x = 100

print(globals())   
# 输出: {'__name__': '__main__', ..., 'x': 100}

def f():
    a = 1
    b = 2
    print(locals())   # 输出: {'a': 1, 'b': 2}

f()
```

### 8.1.2 🔬 字节码视角

```python
import dis

def f():
    x = 1
    print(x)

dis.dis(f)
```

```
  2           0 LOAD_CONST               1 (1)
              2 STORE_FAST               0 (x)        ← x 存入"快速本地变量"

  3           4 LOAD_GLOBAL              0 (print)    ← 全局查找 print
              6 LOAD_FAST                0 (x)        ← 本地查找 x
              8 CALL_FUNCTION            1
             10 POP_TOP
             12 LOAD_CONST               0 (None)
             14 RETURN_VALUE
```

**关键观察**：
- 局部变量用 `STORE_FAST` / `LOAD_FAST`：编译期就确定了"槽位"，访问极快
- 全局变量用 `LOAD_GLOBAL`：运行时查字典
- 内置函数 `print` 也是 `LOAD_GLOBAL`，但找不到时会去内置作用域

---

## 8.2 LEGB 查找规则

### 8.2.1 完整示例

```python
# ─────────────────────────────────────
# 同名变量 x 在四个层级
# ─────────────────────────────────────
x = "global"                       # G

def outer():
    x = "enclosing"                # E
    def inner():
        x = "local"                # L
        print(x)                   # → 输出: local
    inner()
    print(x)                       # → 输出: enclosing

outer()
print(x)                           # → 输出: global

# 内置作用域：B
# print 这个名字，前 3 层都找不到，最终在 builtins 找到
```

### 8.2.2 查找过程追踪

`inner()` 中查找 `x`：

```
1. 查 Local      → 找到 x="local"，停止查找
2. (不会再查上层)


print 查找过程（inner 内部）：

1. 查 Local      → 没有 print
2. 查 Enclosing  → outer 的局部名字中没有 print
3. 查 Global     → 模块顶层没有 print
4. 查 Built-in   → 找到了！
```

### 8.2.3 ⚠️ 仅在"使用"时查找，不在"赋值"时

```python
# ─────────────────────────────────────
# 函数中"赋值"会创建本地名字，即使在赋值之前
# ─────────────────────────────────────
x = "global"

def f():
    print(x)         # ❌ UnboundLocalError
    x = "local"      # ← 这一行让 x 成为本地变量

f()
```

**原因**：Python 在编译函数时**扫描所有赋值语句**，凡是被赋值的名字都标记为 local。运行时 `print(x)` 用 `LOAD_FAST` 查找 x，但本地槽位还没赋值 → `UnboundLocalError`。

🔬 **查看字节码验证**：

```python
import dis
dis.dis(f)
# 0 LOAD_FAST   0 (x)   ← x 被当作本地变量加载
```

---

## 8.3 global 关键字

### 8.3.1 为什么需要

```python
# ─────────────────────────────────────
# 没有 global，赋值会创建本地名字
# ─────────────────────────────────────
counter = 0

def increment():
    counter = counter + 1   # ❌ UnboundLocalError

increment()
```

### 8.3.2 用 global 声明

```python
counter = 0

def increment():
    global counter         # 声明 counter 是全局名字
    counter += 1

increment()
increment()
print(counter)             # 输出: 2
```

🔬 **字节码差异**：

```python
import dis

def f1():
    counter = counter + 1

def f2():
    global counter
    counter = counter + 1

dis.dis(f1)
# LOAD_FAST  counter   ← 本地查找
# STORE_FAST counter

dis.dis(f2)
# LOAD_GLOBAL  counter ← 全局查找
# STORE_GLOBAL counter
```

### 8.3.3 ⚠️ 只读全局变量不需要 global

```python
config = {"debug": True}

def show():
    print(config)         # ✅ 只读，不需要 global
    print(config["debug"]) # ✅
    config["debug"] = False # ✅ 修改对象，不是重新赋值

def change():
    config = {}            # ❌ 这是创建本地变量，不影响外部
```

**判断规则**：
- 只读访问：不需要 `global`
- 重新赋值（`=`）：需要 `global`
- 修改对象内容（`.append()` / `[k]=v`）：不需要 `global`

---

## 8.4 nonlocal 与闭包

### 8.4.1 闭包的形成

```python
# ─────────────────────────────────────
# 闭包：内层函数引用外层函数的变量
# ─────────────────────────────────────
def make_counter():
    count = 0
    
    def counter():
        nonlocal count
        count += 1
        return count
    
    return counter

c1 = make_counter()
print(c1())   # 输出: 1
print(c1())   # 输出: 2

c2 = make_counter()  # 独立的闭包，count 从头开始
print(c2())   # 输出: 1
print(c1())   # 输出: 3   ← c1 和 c2 不共享
```

### 8.4.2 🔬 闭包变量存在哪里：cell 对象

外层函数返回后，按理说 `count` 应该被销毁。但闭包要继续使用它，**Python 把它包装在 cell 对象里**。

```python
# ─────────────────────────────────────
# 查看闭包内部
# ─────────────────────────────────────
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c = make_counter()

print(c.__closure__)       
# 输出: (<cell at 0x...: int object at 0x...>,)

print(c.__closure__[0].cell_contents)
# 输出: 0   ← cell 中存的对象

c()
print(c.__closure__[0].cell_contents)
# 输出: 1   ← 调用后变了

# 函数代码对象记录了哪些自由变量来自闭包
print(c.__code__.co_freevars)   # 输出: ('count',)
```

**内存示意**：

```
make_counter() 调用结束后：

         ┌───────────────────┐
         │ counter (function)│
         │   __closure__:    │
         │   ┌────────────┐  │
         │   │ cell 对象  │──┼──► count 实际值
         │   └────────────┘  │
         └───────────────────┘
              ▲
              │
        变量 c 指向它
```

**结论**：闭包 = 函数对象 + cell 对象数组（保存外层变量）。

### 8.4.3 nonlocal 的作用

```python
# ─────────────────────────────────────
# 不加 nonlocal 会怎样？
# ─────────────────────────────────────
def outer():
    x = 0
    def inner():
        x = x + 1     # ❌ UnboundLocalError
    inner()

# 解决：声明 x 来自外层
def outer():
    x = 0
    def inner():
        nonlocal x
        x = x + 1     # ✅
    inner()
    return x

print(outer())   # 输出: 1
```

**对比**：

| 关键字 | 作用 | 找的范围 |
|--------|------|----------|
| `global` | 操作模块级变量 | 跳过 Enclosing，直接到 Global |
| `nonlocal` | 操作外层函数变量 | 仅 Enclosing（**不能**操作 Global） |

### 8.4.4 ⚠️ 闭包中的循环陷阱

```python
# ❌ 经典陷阱
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])
# 输出: [2, 2, 2]   ← 不是 [0, 1, 2]！
```

**原因**：所有 lambda 共享同一个 `i`（cell），循环结束后 `i = 2`。

🔬 **验证**：

```python
print(funcs[0].__closure__[0].cell_contents)  # 输出: 2
print(funcs[1].__closure__[0].cell_contents)  # 输出: 2
print(funcs[0].__closure__[0] is funcs[1].__closure__[0])
# 输出: True   ← 同一个 cell 对象！
```

**修复**：

```python
# ✅ 方法 1：默认参数（在定义时绑定值）
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])   # 输出: [0, 1, 2]

# ✅ 方法 2：用工厂函数（每次创建新闭包）
def make_func(i):
    return lambda: i

funcs = [make_func(i) for i in range(3)]
print([f() for f in funcs])   # 输出: [0, 1, 2]
```

**为什么默认参数法有效**：默认参数在 lambda **定义时**求值并存储，不是 cell。

---

## 8.5 类作用域的特殊性

### 8.5.1 ⚠️ 类作用域不是 Enclosing

```python
# ─────────────────────────────────────
# 类内方法看不到类作用域的名字
# ─────────────────────────────────────
class Foo:
    x = 1
    
    def method(self):
        print(x)        # ❌ NameError: name 'x' is not defined

Foo().method()
```

**正确做法**：

```python
class Foo:
    x = 1
    
    def method(self):
        print(self.x)    # ✅ 通过实例访问
        print(Foo.x)     # ✅ 通过类访问

Foo().method()
```

### 8.5.2 💡 为什么这样设计

类作用域只在**类定义时**短暂存在，用于收集类属性。一旦类创建完成，类作用域关闭，方法的查找直接跳过类作用域，从 Enclosing 开始。

如果类作用域是 Enclosing，会导致：
- 方法间共享类局部变量（混乱）
- 子类难以重写

### 8.5.3 ⚠️ 推导式和类作用域

```python
class Foo:
    x = 10
    items = [x] * 3              # ✅ 类定义时执行，能看到 x
    items2 = [x for _ in range(3)]   # ❌ NameError!  
    # 推导式有自己的作用域，看不到类作用域
```

**正确**：

```python
class Foo:
    x = 10
    items2 = [x for x in [x, x, x]]   # 用同名变量
    # 或
    _x = x   # 先存到本地
    items2 = [_x for _ in range(3)]
```

或者干脆把这种逻辑放到 `__init__` 中，避免类作用域陷阱。

---

## 8.6 模块作用域

### 8.6.1 模块就是一个对象

```python
# my_module.py
x = 100

def hello():
    print(x)
```

```python
import my_module
print(my_module.x)         # 输出: 100
print(type(my_module))     # 输出: <class 'module'>
print(my_module.__dict__)  # 模块的命名空间
```

🔬 **`globals()` 实际返回的是当前模块的 `__dict__`**。

### 8.6.2 from 与 import 的差异

```python
# 方式 A
import my_module
my_module.hello()        # 通过模块名访问

# 方式 B
from my_module import hello
hello()                  # 直接访问

# 方式 C（不推荐）
from my_module import *  # 把所有"公开"名字注入当前命名空间
```

**底层差异**：
- `import M`：将模块对象绑定到名字 `M`，加入当前 `globals()`
- `from M import x`：执行 M，然后把 M.x 绑定到当前 `globals()` 中的 `x`
- `from M import *`：受 M 的 `__all__` 控制，否则导入所有不以 `_` 开头的名字

### 8.6.3 ⚠️ 循环导入

```python
# a.py
from b import b_func
def a_func(): pass

# b.py
from a import a_func     # ❌ 此时 a 还没定义完
def b_func(): pass
```

**解决方案**：
1. **重构**：把共享的东西抽到第三个模块
2. **延迟导入**：在函数内部 import
3. **改成 import M 而不是 from M import x**

---

## 8.7 作用域与字节码：完整剖析

```python
# ─────────────────────────────────────
# 综合示例：观察字节码
# ─────────────────────────────────────
import dis

g = "global"

def outer():
    e = "enclosing"
    def inner():
        l = "local"
        print(l, e, g)
    return inner

dis.dis(outer().__code__)
```

输出（节选）：

```
  4           0 LOAD_CONST               1 ('local')
              2 STORE_FAST               0 (l)        ← 本地变量

  5           4 LOAD_GLOBAL              0 (print)    ← print 是全局/内置
              6 LOAD_FAST                0 (l)        ← LOAD_FAST: 本地
              8 LOAD_DEREF               0 (e)        ← LOAD_DEREF: 闭包变量
             10 LOAD_GLOBAL              1 (g)        ← LOAD_GLOBAL: 全局
             12 CALL_FUNCTION            3
```

四种加载指令：

| 指令 | 用途 |
|------|------|
| `LOAD_FAST` | 本地变量（数组索引） |
| `LOAD_DEREF` | 闭包变量（cell 对象） |
| `LOAD_GLOBAL` | 全局/内置变量 |
| `LOAD_NAME` | 类作用域中使用（按字典查找） |

**性能差异**：
- `LOAD_FAST`：O(1)，最快
- `LOAD_DEREF`：略慢（多一次解引用）
- `LOAD_GLOBAL`：查字典，最慢

**优化技巧**：把高频访问的全局名字"本地化"。

```python
# ❌ 慢
def hot_loop():
    for _ in range(1_000_000):
        math.sqrt(2)         # 每次都 LOAD_GLOBAL

# ✅ 快
def hot_loop():
    sqrt = math.sqrt          # 本地化
    for _ in range(1_000_000):
        sqrt(2)              # LOAD_FAST
```

---

## 8.8 实际开发场景

### 场景 1：用闭包创建私有状态

```python
def make_account(initial_balance):
    balance = initial_balance
    
    def deposit(amount):
        nonlocal balance
        balance += amount
        return balance
    
    def withdraw(amount):
        nonlocal balance
        if amount > balance:
            raise ValueError("余额不足")
        balance -= amount
        return balance
    
    def get_balance():
        return balance
    
    return deposit, withdraw, get_balance

deposit, withdraw, balance = make_account(100)
deposit(50)
print(balance())   # 输出: 150
```

外部无法直接访问 `balance` 变量——这就是闭包的封装能力。

### 场景 2：装饰器中的闭包

```python
def with_retry(max_attempts):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
        return wrapper
    return decorator

@with_retry(max_attempts=3)
def flaky():
    pass
```

`wrapper` 闭包持有 `max_attempts` 和 `func`。

### 场景 3：避免全局变量污染

```python
# ❌ 全局污染
_cache = {}
def lookup(key):
    if key not in _cache:
        _cache[key] = expensive(key)
    return _cache[key]

# ✅ 闭包封装
def make_lookup():
    cache = {}
    def lookup(key):
        if key not in cache:
            cache[key] = expensive(key)
        return cache[key]
    return lookup

lookup = make_lookup()
```

---

## 8.9 常见误区

### 误区 1：以为 if/for 形成作用域

```python
# Python 中 if/for/while 不形成作用域
for i in range(3):
    pass
print(i)   # 输出: 2  ← 循环变量在外部仍可见！

if True:
    x = 100
print(x)   # 输出: 100
```

只有**函数、类、推导式**形成作用域。

### 误区 2：用 global 修改对象内容

```python
config = {"a": 1}

def update():
    global config        # ❌ 多余！只是修改对象内容，不需要 global
    config["b"] = 2

# 简化
def update():
    config["b"] = 2      # ✅
```

### 误区 3：lambda 中误用循环变量

```python
# 见 8.4.4
```

### 误区 4：以为 import 是"复制"

```python
# a.py
x = 10

# b.py
from a import x
x = 20         # 只是改了 b 中 x 的绑定，a.x 不变

import a
print(a.x)     # 输出: 10
```

---

## 8.10 面试常问

### Q1：解释 LEGB 规则

**答**：Python 名字查找的四级顺序——
1. Local（当前函数）
2. Enclosing（外层函数，逐层向外）
3. Global（当前模块）
4. Built-in（内置名字）

找到即停。**赋值**默认创建 Local 名字，需要 `global`/`nonlocal` 改变。

### Q2：闭包变量保存在哪里？

**答**：保存在 **cell 对象**中，由内层函数的 `__closure__` 持有。这样即使外层函数返回，闭包变量也不会被回收。

### Q3：global 和 nonlocal 的区别？

**答**：
- `global`：声明变量来自模块作用域
- `nonlocal`：声明变量来自最近的外层函数作用域（不含模块）
- 都用于"赋值"时使用外层名字。只读访问不需要它们。

### Q4：为什么以下代码报错？

```python
x = 10
def f():
    print(x)
    x = 20
f()
```

**答**：函数编译时扫描赋值，将 `x` 标记为 local。运行时 `print(x)` 用 LOAD_FAST 查找，但 x 还未赋值 → `UnboundLocalError`。

### Q5：以下代码输出？

```python
def make_funcs():
    return [lambda: i for i in range(3)]

print([f() for f in make_funcs()])
```

**答**：`[2, 2, 2]`。所有 lambda 共享同一个 cell（指向 `i`），循环结束后 `i = 2`。

修复：`[lambda i=i: i for i in range(3)]`

### Q6：为什么类内方法不能直接访问类属性？

**答**：类作用域不是 Enclosing。类作用域只在类定义时短暂存在，方法定义后查找名字会跳过类作用域。必须通过 `self.x` 或 `ClassName.x` 访问。

---

## 8.11 练习题

### 练习 8.1（基础）

预测输出：

```python
x = 1

def f():
    x = 2
    def g():
        x = 3
        print(x)
    g()
    print(x)

f()
print(x)
```

<details>
<summary>答案</summary>

```
3
2
1
```
</details>

### 练习 8.2（基础）

修复以下代码：

```python
total = 0

def add(n):
    total += n

add(5)
print(total)
```

<details>
<summary>答案</summary>

```python
total = 0

def add(n):
    global total
    total += n

add(5)
print(total)   # 5
```
</details>

### 练习 8.3（中级）

实现一个 `make_multiplier` 工厂，返回相乘函数。要求每次调用 `make_multiplier(n)` 返回独立的函数：

```python
double = make_multiplier(2)
triple = make_multiplier(3)
print(double(5))   # 10
print(triple(5))   # 15
```

<details>
<summary>答案</summary>

```python
def make_multiplier(n):
    def multiply(x):
        return x * n     # n 来自闭包
    return multiply
```
</details>

### 练习 8.4（中级）

下面的代码哪里有问题？请用至少两种方法修复：

```python
callbacks = []
for i in range(5):
    callbacks.append(lambda: print(i))

for cb in callbacks:
    cb()
# 输出全是 4，期望 0 1 2 3 4
```

<details>
<summary>答案</summary>

**方法 1：默认参数**

```python
callbacks.append(lambda i=i: print(i))
```

**方法 2：工厂函数**

```python
def make_cb(i):
    return lambda: print(i)

for i in range(5):
    callbacks.append(make_cb(i))
```

**方法 3：用 functools.partial**

```python
from functools import partial
for i in range(5):
    callbacks.append(partial(print, i))
```
</details>

### 练习 8.5（高级）

实现一个 `once` 装饰器，让被装饰的函数只能被调用一次：

```python
@once
def init():
    print("初始化")
    return 42

print(init())   # 初始化  → 42
print(init())   # 直接返回 42，不再打印
```

<details>
<summary>答案</summary>

```python
def once(func):
    called = False
    result = None
    def wrapper(*args, **kwargs):
        nonlocal called, result
        if not called:
            result = func(*args, **kwargs)
            called = True
        return result
    return wrapper
```
</details>

### 练习 8.6（高级）

阅读以下代码并解释：

```python
class A:
    name = "A"
    method_name = name + ".method"
    print(name, method_name)
    
    def show(self):
        # print(name)        # 这一行能工作吗？
        print(self.name)
```

<details>
<summary>答案</summary>

类定义时（class 块内）能看到 `name`，所以 `method_name = name + ".method"` 工作正常，输出 `A A.method`。

但 `show` 方法**调用时**，类作用域已关闭，不能直接访问 `name`，必须用 `self.name` 或 `A.name`。

如果取消注释 `print(name)`，调用 `A().show()` 会得到 `NameError`（除非全局有 `name`）。
</details>

### 练习 8.7（综合）

实现一个简易的"作用域观察器"，打印当前函数所有 LEGB 层级的同名变量：

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        x = "local"
        observe("x")    # 期望输出: local=local, enclosing=enclosing, global=global, builtin=N/A
    inner()

outer()
```

<details>
<summary>答案</summary>

```python
import inspect, builtins

def observe(name):
    frame = inspect.currentframe().f_back
    print(f"local    = {frame.f_locals.get(name, 'N/A')}")
    
    # Enclosing 通过函数的 __closure__ 看不到当前 frame 的，需要爬栈
    enc = frame.f_back
    while enc and name not in enc.f_locals:
        enc = enc.f_back
    enc_val = enc.f_locals[name] if enc and name in enc.f_locals else 'N/A'
    print(f"enclosing= {enc_val}")
    
    print(f"global   = {frame.f_globals.get(name, 'N/A')}")
    print(f"builtin  = {getattr(builtins, name, 'N/A')}")
```

> 注意：实际项目中很少需要这么做，但写一遍能加深对帧（frame）和命名空间的理解。
</details>

---

## 本章总结

| 概念 | 一句话 |
|------|--------|
| LEGB | 名字查找四级：Local → Enclosing → Global → Built-in |
| 命名空间 | 本质是字典 |
| `global` | 声明操作模块级变量 |
| `nonlocal` | 声明操作外层函数变量 |
| 闭包 | 函数 + cell 对象（保存外层变量） |
| `LOAD_FAST` | 本地变量，最快 |
| 类作用域 | 不是 Enclosing，方法不能直接访问 |
| 推导式 | 有独立作用域 |
| 模块 | 也是对象，命名空间 = `__dict__` |

---

**上一章：[07_引用与内存机制](07_引用与内存机制.md)** | **下一章：[09_类型系统与typing](09_类型系统与typing.md)**

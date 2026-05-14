# 10. GIL 与 CPython 执行机制

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐⭐ (专家) |
> | **前置知识** | [01 函数](01_函数篇.md)、[07 引用机制](07_引用与内存机制.md)、[08 LEGB](08_作用域与LEGB深入.md) |
> | **学习目标** | 看懂字节码、理解栈式 VM、解释 GIL 存在原因和释放时机、解释为什么多线程不快 |
> | **CPython 版本** | 3.12+（含自适应解释器优化 PEP 659） |
> | **规范 vs 实现** | 🔬 **本章 90% 是 CPython 实现细节**。GIL 不在 Python 语言规范中，PyPy/Jython/IronPython 都没有 |

---

> 本章告诉你 Python 代码到底是怎么跑起来的。  
> 字节码、虚拟机、GIL —— 不理解这些，就解释不了为什么 Python 多线程"伪并行"。

---

## 10.0 知识地图

```
                       Python 源码 .py
                            │
                            ▼
                  ┌──────────────────┐
                  │  词法/语法分析    │
                  └──────┬───────────┘
                         ▼
                  ┌──────────────────┐
                  │  AST 抽象语法树  │
                  └──────┬───────────┘
                         ▼
                  ┌──────────────────┐
                  │  编译为字节码     │  → .pyc 文件
                  └──────┬───────────┘
                         ▼
                ┌────────────────────┐
                │  CPython 虚拟机    │
                │  (栈式执行字节码)   │
                └─────────┬──────────┘
                          ▼
                ┌─────────────────────┐
                │  GIL: 全局解释器锁   │  ← 保护 PyObject 内部状态
                └─────────────────────┘
```

**本章要回答**：
1. Python 是解释型还是编译型？
2. 字节码长什么样？
3. GIL 到底是什么？为什么存在？
4. 多线程真的"伪并行"吗？
5. CPython 怎么决定何时切换线程？

---

## 10.1 Python 不是"纯解释执行"

### 10.1.1 真相：编译 + 解释

Python 既编译也解释：
1. **编译阶段**：源码 → 字节码（.pyc）
2. **解释阶段**：CPython 虚拟机执行字节码

```python
# 验证：第一次运行模块时生成 .pyc
import os, py_compile

py_compile.compile("my_module.py")
# 生成 __pycache__/my_module.cpython-312.pyc  (CPython 3.12)
```

### 10.1.2 🔬 dis 模块：查看字节码

```python
import dis

def add(a, b):
    return a + b

dis.dis(add)
```

输出：

```
  2           0 RESUME                   0

  3           2 LOAD_FAST                0 (a)
              4 LOAD_FAST                1 (b)
              6 BINARY_OP                0 (+)
             10 RETURN_VALUE
```

每条指令包含：
- 行号（左侧 `2`/`3`）
- 字节偏移（`0`、`2`、`4`...）
- 指令名（`LOAD_FAST`）
- 参数

### 10.1.3 字节码与 .pyc 文件

```bash
$ python -c "import my_module"
$ ls __pycache__/
my_module.cpython-312.pyc
```

`.pyc` 文件包含：
- 魔数（Python 版本标识）
- 时间戳/哈希（用于检测源码是否变化）
- 序列化的 code 对象（含字节码）

**作用**：避免每次启动都重新编译，加快导入速度。

---

## 10.2 CPython 虚拟机：栈式执行

### 10.2.1 ★ 栈式机器模型

CPython 是**基于栈的虚拟机**。所有运算通过"操作数栈"完成。

```python
def f():
    return 1 + 2

dis.dis(f)
```

```
LOAD_CONST   1     # 把 1 压栈     栈: [1]
LOAD_CONST   2     # 把 2 压栈     栈: [1, 2]
BINARY_OP    +     # 弹出两个，相加，结果压栈   栈: [3]
RETURN_VALUE       # 弹出栈顶并返回
```

### 10.2.2 完整示例追踪

```python
import dis

def calc(x):
    y = x * 2
    return y + 1

dis.dis(calc)
```

```
  2           0 LOAD_FAST     0 (x)        栈: [x]
              2 LOAD_CONST    1 (2)        栈: [x, 2]
              4 BINARY_OP     5 (*)        栈: [x*2]
              8 STORE_FAST    1 (y)        栈: [],  局部变量 y = x*2

  3          10 LOAD_FAST     1 (y)        栈: [y]
             12 LOAD_CONST    2 (1)        栈: [y, 1]
             14 BINARY_OP     0 (+)        栈: [y+1]
             18 RETURN_VALUE               返回栈顶
```

### 10.2.3 局部变量：数组而非字典

函数的局部变量在编译期分配"槽位"，运行时通过索引访问：

```
LOAD_FAST    0 (x)    # 槽位 0 的值压栈
STORE_FAST   1 (y)    # 弹栈顶到槽位 1
```

这就是 LOAD_FAST 比 LOAD_GLOBAL 快的原因（数组索引 vs 字典查找）。

---

## 10.3 PyObject：Python 对象的 C 表示

### 10.3.1 🔬 每个 Python 对象都是 PyObject

C 层面每个对象的开头：

```c
typedef struct {
    Py_ssize_t ob_refcnt;     // 引用计数
    PyTypeObject *ob_type;    // 类型指针
} PyObject;
```

例如 `PyLongObject`（int）：

```c
typedef struct {
    PyObject_HEAD;            // ob_refcnt + ob_type
    Py_ssize_t ob_size;       // 数字位数
    digit ob_digit[1];        // 实际数字数据
} PyLongObject;
```

### 10.3.2 sys.getsizeof 验证

```python
import sys

# CPython 3.12（64 位 Linux）— 实际数值随版本与平台不同
print(sys.getsizeof(0))          # 24（CPython 3.12 紧凑 long 表示，单 digit 内嵌到 PyVarObject）
print(sys.getsizeof(1000))       # 28
print(sys.getsizeof(10**20))     # 36   (超过单 digit 容量)

print(sys.getsizeof([]))         # 56   (list 头 + 空 ob_item)
print(sys.getsizeof([1]))        # 64
```

> 🔬 **PEP 683（3.12+，immortal objects）** **只把 `ob_refcnt` 锁定为不变值**（避免 None/True/False/小整数因 refcount 抖动引起的 cache line 失效），**不改变对象大小**。3.12 中 `int(0)` 占 24 字节是另一个独立优化（GH-92356/GH-101291：单 digit 长整数内嵌到 `PyVarObject`），与 PEP 683 无关。**生产代码不要依赖具体大小**，要用 `sys.getsizeof` 实测。

**对比**：C 语言 `int` 是 4-8 字节，Python 整数最少 24+ 字节——这是 PyObject 头部（refcount + type 指针）的开销。

### 10.3.3 这就是 GIL 存在的根本原因

每个对象的 `ob_refcnt` 在多线程环境下被并发修改，必须保证原子性。  
两种解决方案：
1. **每个对象一个锁**：开销大、容易死锁
2. **一个全局锁**：简单粗暴 —— 这就是 **GIL**

---

## 10.4 ★ GIL：全局解释器锁

### 10.4.1 概念

**GIL（Global Interpreter Lock）**：CPython 解释器的一把全局互斥锁。

**核心规则**：**同一时刻，只有一个线程能执行 Python 字节码。**

```
线程 1: ████████        ████████
线程 2:         ████████        ████████   ← 单核：交替执行
                                              多核：依然交替！
```

### 10.4.2 💡 为什么需要 GIL

CPython 的内存管理依赖**引用计数**。引用计数的修改必须线程安全。

如果没有 GIL：

```python
# 假设多个线程同时执行：
x = some_object   # 涉及 some_object.ob_refcnt += 1
```

C 级别这个 `+= 1` 不是原子的：
1. 读取 ob_refcnt 到寄存器
2. 加 1
3. 写回内存

两个线程同时做这件事 → 引用计数错误 → 对象提前回收或永不回收 → 段错误。

GIL 是最简单的解决方案：**全局只有一个线程能动 PyObject**。

### 10.4.3 🔬 GIL 的实际行为

> ⚠️ **关键区分**：§10.4.2 说"GIL 保护 `ob_refcnt`"——这是**解释器内部**的引用计数操作。下面演示的 `count += 1` 是**用户代码层面**的整数加法，涉及**多条字节码**（LOAD → ADD → STORE）。GIL 可能在字节码边界释放——所以即使有 GIL，用户的 `count += 1` 仍然不安全。

```python
import threading
import time

count = 0

def increment():
    global count
    for _ in range(1_000_000):
        count += 1

t1 = threading.Thread(target=increment)
t2 = threading.Thread(target=increment)
t1.start(); t2.start()
t1.join(); t2.join()

print(count)
# 期望: 2_000_000
# 实际: 通常小于 2_000_000，因为 count += 1 不是原子的
```

⚠️ **GIL 保护的是解释器内部数据结构（如引用计数），不保护你的 Python 代码逻辑。**

`count += 1` 在字节码层面是：

```
LOAD_FAST   count
LOAD_CONST  1
BINARY_OP   +
STORE_FAST  count
```

GIL 可能在任何字节码之间释放 → 还是要用 `Lock`。

---

## 10.5 GIL 何时释放

### 10.5.1 切换时机（Python 3.2+）

GIL 不是按字节码数切换，而是按**时间间隔**：

```python
import sys
print(sys.getswitchinterval())   # 输出: 0.005  (默认 5ms)
```

每个线程持续运行约 5ms，然后释放 GIL，让其他线程竞争。

### 10.5.2 ★ I/O 操作时主动释放

```python
# C 实现的 I/O 函数（read、recv、sleep...）会主动释放 GIL
import time
time.sleep(1)         # 进入这个函数就释放 GIL，1 秒后竞争回来

# 文件读写、socket、subprocess 等 I/O 操作同样
with open("big.txt") as f:
    data = f.read()    # 读盘期间 GIL 被释放
```

**这就是为什么 Python 多线程对 I/O 密集型有效**——一个线程等 I/O，其他线程能跑。

### 10.5.3 实测：CPU 密集 vs I/O 密集

```python
import time, threading

# ─────── CPU 密集 ───────
def cpu_task():
    n = 0
    for _ in range(10_000_000):
        n += 1

# 单线程
start = time.time()
cpu_task(); cpu_task()
print(f"串行: {time.time() - start:.2f}s")

# 双线程
start = time.time()
t1 = threading.Thread(target=cpu_task)
t2 = threading.Thread(target=cpu_task)
t1.start(); t2.start(); t1.join(); t2.join()
print(f"双线程: {time.time() - start:.2f}s")

# 输出（典型）:
# 串行:   0.85s
# 双线程: 1.05s   ← 反而更慢！因为有 GIL 竞争开销
```

```python
# ─────── I/O 密集 ───────
def io_task():
    time.sleep(1)

start = time.time()
io_task(); io_task()
print(f"串行: {time.time() - start:.2f}s")    # 输出: 2.0s

start = time.time()
t1 = threading.Thread(target=io_task)
t2 = threading.Thread(target=io_task)
t1.start(); t2.start(); t1.join(); t2.join()
print(f"双线程: {time.time() - start:.2f}s")  # 输出: 1.0s ✅ 加速
```

---

## 10.6 突破 GIL 的方案

### 方案 1：多进程（multiprocessing）

每个进程有自己的解释器和 GIL，进程间真并行。

```python
from multiprocessing import Pool

def cpu_task(n):
    return sum(i*i for i in range(n))

if __name__ == "__main__":
    with Pool(4) as p:
        results = p.map(cpu_task, [10_000_000] * 4)
```

**代价**：
- 进程间通信慢（pickle 序列化）
- 内存占用大（每个进程独立）

### 方案 2：C 扩展释放 GIL

NumPy、Pandas、Pillow 等库的核心运算用 C 实现，**计算时释放 GIL**：

```python
import numpy as np

# NumPy 矩阵乘法在 C 层面执行，期间 GIL 释放
# 多线程做 NumPy 计算可以加速
```

### 方案 3：用 Cython / Numba

```python
# Numba 把 Python 函数编译为机器码，可释放 GIL
from numba import njit, prange

@njit(parallel=True)
def parallel_sum(arr):
    s = 0
    for i in prange(len(arr)):    # prange = 并行 range
        s += arr[i]
    return s
```

### 方案 4：异步编程（asyncio）

不真并行，但单线程内通过协作式调度处理大量 I/O。详见第 12 章。

### 方案 5：子解释器（PEP 684，Python 3.12+）

🔬 **每个子解释器拥有独立 GIL**，但共享同一进程内存。

```python
# 3.12+ 标准库 _xxsubinterpreters（实验性）
# 3.13+ 改名为 interpreters（仍为实验性模块）
import _xxsubinterpreters as interpreters

interp = interpreters.create()
interpreters.run_string(interp, "print('hello from sub-interpreter')")
interpreters.destroy(interp)
```

**与多进程对比**：

| | multiprocessing | 子解释器 (PEP 684) |
|--|---|---|
| GIL | 各进程独立 | 各解释器独立 |
| 内存隔离 | 完全隔离 | 共享进程地址空间（但 PyObject 不共享） |
| 通信 | pickle / Queue / pipe | 共享内存 / channel（PEP 554 进行中） |
| 启动开销 | 大（fork/spawn 整个进程） | 小（新建解释器状态即可） |
| C 扩展兼容 | 几乎全兼容 | **需要 C 扩展支持 PEP 630 multi-phase init** |

**限制**：
- 不能在子解释器间共享 Python 对象（没有引用传递）
- 需要 C 扩展（NumPy 等）适配 PEP 630；未适配的扩展会报 `ImportError`
- 3.12/3.13 仍标为实验性 API，接口可能变

**适用场景**：同一进程内需要真并行 Python 代码，且通信数据量大（共享内存比 pickle 快几个数量级）。

---

### 方案 6：免 GIL Python（PEP 703，Python 3.13+）

3.13 引入 **free-threaded build**（`python3.13t`）：编译时完全移除 GIL。

```bash
# 安装 free-threaded build（需要专门编译或 deadsnakes PPA）
python3.13t -c "import sys; print(sys.flags.no_gil)"  # True
```

**代价（3.13 实测）**：
- 单线程性能退化 ~10-40%（需要更多原子操作 / per-object lock）
- C 扩展必须声明 `Py_mod_gil = Py_MOD_GIL_NOT_USED`，否则回退到有 GIL 模式
- NumPy 等大库仍在适配中

**何时用**：
- 你有大量 CPU 密集纯 Python 代码需要真并行
- 你愿意承受单线程退化 + 等待生态成熟

**与子解释器的关系**：两个方案不冲突——子解释器在 free-threaded build 中仍然有用（隔离状态 / 安全沙箱）。

---

### 方案 7：实验性 JIT（PEP 744，Python 3.13+）

3.13 引入 **copy-and-patch JIT**（需编译时 `--enable-experimental-jit`）：

- 在 PEP 659 自适应解释器基础上，对"热"专用指令编译为机器码
- 3.13 首版加速有限（~5%），但为后续迭代（tier 2 optimizer）打下基础
- **用户无需改代码**——全自动，但默认关闭

```bash
# 3.13 编译时启用
./configure --enable-experimental-jit
make
```

> 🔬 **演进方向**：3.14+ 计划持续优化 JIT，目标是逐步追上 PyPy 的 JIT 加速效果。

---

## 10.6.1 GIL 切换的底层机制：eval breaker

🔬 **CPython 实现**：GIL 切换不是"定时器中断"，而是 **eval breaker 标志位轮询**。

```c
// Python/ceval.c（简化）
_PyEval_EvalFrameDefault(frame) {
    for (;;) {
        // ★ 每条字节码执行前检查 eval_breaker
        if (_Py_atomic_load(&tstate->interp->ceval.eval_breaker)) {
            // 可能是：GIL drop request / signal / async exception / gc
            if (drop_gil_requested) {
                drop_gil(tstate);
                take_gil(tstate);   // 重新竞争
            }
            if (pending_signal) handle_signal();
            if (pending_calls) make_pending_calls();
        }
        
        // 正常 dispatch 字节码
        DISPATCH();
    }
}
```

**eval_breaker 被设置的时机**：
1. 另一个线程请求 GIL（`_PyEval_SignalAsyncExc`）
2. `sys.setswitchinterval` 定时器到期
3. 收到 OS signal（SIGINT 等）
4. `gc.collect()` 请求
5. `sys.settrace` / `sys.monitoring` 回调

→ 这就是为什么 GIL 切换只在"字节码边界"发生——不是真正的抢占，而是每条指令前的协作式检查。

---

## 10.7 frame、code、function 三种对象

### 10.7.1 三者关系

```python
def f(x):
    return x + 1

# code 对象：函数的编译结果（字节码 + 元信息）
print(f.__code__)
# <code object f at 0x..., file "...", line N>

# function 对象：code + 闭包 + 默认值 + 名字
# 一个 code 可以被多个 function 共享

# frame 对象：调用 function 时创建，含执行状态（栈、局部变量）
import inspect

def show_frame():
    print(inspect.currentframe())
    print(inspect.currentframe().f_locals)

show_frame()
```

### 10.7.2 调用过程详解

```
1. 调用 f(10)
2. 创建新 frame
   - frame.f_code = f.__code__
   - frame.f_locals = {'x': 10}
   - frame.f_globals = 模块的全局命名空间
3. 解释器执行 frame 中的字节码
4. 函数返回，frame 销毁（除非被 traceback / generator 持有）
```

### 10.7.3 traceback 的本质

异常时 Python 保留调用栈上每一层的 frame，组成 traceback：

```python
import traceback

try:
    1/0
except ZeroDivisionError:
    traceback.print_exc()
    # 每一行对应一个 frame
```

---

## 10.8 性能优化思路

### 10.8.1 减少全局查找

```python
# ❌ 慢
def hot():
    for _ in range(10**7):
        math.sqrt(2)        # LOAD_GLOBAL 每次

# ✅ 快
def hot():
    sqrt = math.sqrt        # LOAD_FAST
    for _ in range(10**7):
        sqrt(2)
```

实测可快 10-30%。

### 10.8.2 用内置函数

```python
# ❌
total = 0
for x in items:
    total += x

# ✅
total = sum(items)        # C 实现，速度快几倍
```

### 10.8.3 避免无谓的属性访问

```python
# ❌
for _ in range(10**6):
    obj.method()

# ✅
m = obj.method
for _ in range(10**6):
    m()
```

详见第 14 章性能优化。

---

## 10.9 常见误区

### 误区 1：以为 GIL 让多线程毫无用处

**错**：I/O 密集型多线程依然有效。GIL 只影响 CPU 密集场景。

### 误区 2：以为 GIL = Python 慢

**错**：Python 慢的主要原因是动态类型 + 解释执行 + 对象开销，GIL 只是其中一环。

### 误区 3：以为 GIL 能保证线程安全

**错**：GIL 保护的是解释器内部数据结构，不保护用户代码。`count += 1` 仍需要 `Lock`。

### 误区 4：以为 multiprocessing 完全免费

**错**：进程间通信、启动、内存复制都有成本。短任务用进程池可能反而慢。

---

## 10.10 面试常问

### Q1：什么是 GIL？

**答**：CPython 解释器的全局互斥锁，保证同一时刻只有一个线程执行 Python 字节码。其存在是为了简化 PyObject 引用计数的线程安全。

### Q2：为什么 Python 多线程跑 CPU 密集任务不快？

**答**：GIL 限制同一时刻只有一个线程执行 Python 代码。多线程在 CPU 密集任务上无法真并行，反而有 GIL 竞争开销。CPU 密集应该用多进程或 C 扩展。

### Q3：GIL 何时释放？

**答**：
- 每隔 `sys.getswitchinterval()`（默认 5ms）主动释放
- 执行 I/O 操作（文件、网络、sleep）时释放
- 调用释放 GIL 的 C 扩展（NumPy 等）时释放

### Q4：如何绕过 GIL？

**答**：
1. **multiprocessing**：每个进程独立 GIL
2. **C 扩展**：NumPy 等核心计算时释放 GIL
3. **asyncio**：单线程协作式并发
4. **Jython/IronPython**：基于 JVM/.NET，无 GIL（但生态差）

### Q5：Python 是编译型还是解释型？

**答**：**两者都有**。
1. 源码先**编译**为字节码（保存在 `.pyc`）
2. 字节码由 CPython 虚拟机**解释执行**

### Q6：解释一下 Python 函数调用时发生了什么。

**答**：
1. 创建 frame 对象（含局部变量、栈、字节码引用）
2. 设置 frame 的 globals 和 closure（如有）
3. 解释器执行 frame 中的字节码
4. 通过操作数栈完成所有运算
5. 返回时销毁 frame（除非被 generator/traceback 持有）

### Q7：以下代码线程安全吗？

```python
class Counter:
    def __init__(self):
        self.n = 0
    def incr(self):
        self.n += 1
```

**答**：**不安全**。`self.n += 1` 在字节码层面是多步操作（LOAD_ATTR / BINARY_OP / STORE_ATTR），GIL 可能在中间释放。需要用 `threading.Lock`。  
⚠️ 注意 `itertools.count()` 单独用是原子的，但配合 `self.n = next(c) + 1` **不是**——`STORE_ATTR` 仍是独立字节码，两线程仍会相互覆盖。详见练习 10.3。

---

## 10.11 练习题

### 练习 10.1（基础）

用 dis 模块查看以下函数的字节码，并解释每条指令：

```python
def f(x, y):
    z = x + y * 2
    return z
```

<details>
<summary>答案</summary>

```python
import dis
dis.dis(f)
```

```
LOAD_FAST    x       栈: [x]
LOAD_FAST    y       栈: [x, y]
LOAD_CONST   2       栈: [x, y, 2]
BINARY_OP    *       栈: [x, y*2]
BINARY_OP    +       栈: [x + y*2]
STORE_FAST   z       栈: []
LOAD_FAST    z       栈: [z]
RETURN_VALUE
```
</details>

### 练习 10.2（中级）

写一个实验，证明 Python 多线程对 CPU 密集任务无加速：

<details>
<summary>答案</summary>

```python
import threading, time

def busy(n):
    while n > 0:
        n -= 1

N = 50_000_000

# 串行
start = time.time()
busy(N); busy(N)
print(f"串行: {time.time()-start:.2f}s")

# 并行
start = time.time()
t1 = threading.Thread(target=busy, args=(N,))
t2 = threading.Thread(target=busy, args=(N,))
t1.start(); t2.start(); t1.join(); t2.join()
print(f"双线程: {time.time()-start:.2f}s")
```

典型结果：双线程约等于或慢于串行。
</details>

### 练习 10.3（高级）

下面代码线程安全吗？说明原因，给出修复方案。

```python
class Counter:
    def __init__(self):
        self.n = 0
    def incr(self):
        self.n += 1

c = Counter()
threads = [threading.Thread(target=lambda: [c.incr() for _ in range(10000)])
           for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
print(c.n)   # 期望 100000
```

<details>
<summary>答案</summary>

不安全。`self.n += 1` 是非原子的（LOAD/ADD/STORE 三步）。GIL 可能在中间切换。

**修复方案**：

```python
import threading

class Counter:
    def __init__(self):
        self.n = 0
        self._lock = threading.Lock()
    def incr(self):
        with self._lock:
            self.n += 1
```

> ⚠️ **常见伪修复**：用 `itertools.count()` 配合 `self.n = next(self._counter) + 1` —— **依然不安全**！  
> `next(count)` 在 C 层确实原子，但接下来的 `self.n = X` 是独立的 `STORE_ATTR` 字节码：两个线程可能同时拿到 `next` 然后乱序写入 `self.n`，仍然丢更新。  
> 如果要避开锁，只能让"递增"和"读取"是同一次原子调用：
> ```python
> from itertools import count
> class Counter:
>     def __init__(self):
>         self._counter = count(1)
>     def value(self):
>         return next(self._counter)   # 每次调用返回递增后的值，没有"中间状态"可被打断
> ```
> 这才是真正绕过锁的方式。
</details>

### 练习 10.4（综合）

判断以下场景该用线程、进程还是异步：

a) 同时下载 100 个网页  
b) 对 10GB 数据做矩阵运算  
c) Web 服务器处理 1000 个并发请求  
d) 视频转码  
e) 解析多个 JSON 文件并入库

<details>
<summary>答案</summary>

| 场景 | 推荐 | 理由 |
|------|------|------|
| a | 异步（asyncio + aiohttp）或线程池 | I/O 密集，asyncio 更省资源 |
| b | NumPy / 多进程 | CPU 密集，需绕过 GIL |
| c | 异步框架（FastAPI/Sanic） | 高并发 I/O |
| d | 多进程 / 调用 ffmpeg | CPU 密集，且常常通过 C 库 |
| e | 异步 + 数据库连接池 | I/O 密集（读文件 + 网络写库） |
</details>

---

## 本章总结

| 概念 | 一句话 |
|------|--------|
| 编译 + 解释 | 源码 → 字节码 → 虚拟机解释 |
| 字节码 | dis 模块可查 |
| 栈式机器 | 通过操作数栈做运算 |
| PyObject | 每个对象 28+ 字节，含引用计数和类型指针 |
| GIL | 全局互斥锁，保护引用计数 |
| GIL 释放 | 时间片、I/O、C 扩展 |
| 多线程 | 适合 I/O，不适合 CPU |
| 多进程 | 突破 GIL，但有通信成本 |

---

**上一章：[09_类型系统与typing](09_类型系统与typing.md)** | **下一章：[11_并发编程深入](11_并发编程深入.md)**

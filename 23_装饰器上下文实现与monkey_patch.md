# 23. 装饰器、上下文管理器底层实现 + Monkey Patch

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐ (高级) |
> | **前置知识** | [03 装饰器](03_装饰器篇.md)、[05 with](05_控制流与异常处理篇.md)、[22 描述符与元类](22_描述符与元类深入.md) |
> | **学习目标** | 理解 @ 语法的字节码语义、自己实现 contextmanager、知道 monkey patch 的代价 |
> | **CPython 版本** | 3.12+ |
> | **规范 vs 实现** | 装饰器/with 语义是 Python 规范；具体字节码（CALL/COPY 指令）是 CPython 实现 |

---

## 23.0 知识地图

```
@ 装饰器
   语法糖 → func = decorator(func)
                                                
with 语句
   语义 → __enter__ + __exit__
                                                
@contextmanager
   生成器 + try/finally → 上下文管理器
                                                
Monkey Patch
   运行时替换函数/方法/属性
   原理：Python 一切可变（除少数 builtin）
```

---

## 23.1 装饰器的字节码语义

### 23.1.1 @ 等价于赋值

```python
@deco
def f():
    pass

# 等价于
def f():
    pass
f = deco(f)
```

### 23.1.2 🔬 字节码差异

```python
import dis

source1 = """
@deco
def f(): pass
"""

source2 = """
def f(): pass
f = deco(f)
"""

dis.dis(compile(source1, "<>", "exec"))
dis.dis(compile(source2, "<>", "exec"))
```

3.12 中 `@` 用更紧凑的指令序列，但语义完全等价。

### 23.1.3 多个装饰器

```python
@A
@B
@C
def f(): pass

# 等价于
f = A(B(C(f)))
```

→ **从下往上**应用，从外往内调用。

### 23.1.4 带参数装饰器

```python
@deco(arg)
def f(): pass

# 等价于
f = deco(arg)(f)
```

`deco(arg)` 先调用，返回真正的装饰器。

---

## 23.2 装饰器的 5 种实现形态

### 形态 1：函数装饰器（最常见）

```python
from functools import wraps

def log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"call {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

### 形态 2：带参数的装饰器（三层）

```python
def repeat(n):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator
```

### 形态 3：类装饰器（用 __call__）

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0
        wraps(func)(self)            # 让 wraps 把元信息复制到实例
    
    def __call__(self, *args, **kwargs):
        self.count += 1
        return self.func(*args, **kwargs)

@CountCalls
def hello(): pass
```

⚠️ 类装饰器作用于**方法**时有问题（self 不会自动绑定）：

```python
class Foo:
    @CountCalls
    def method(self):    # CountCalls 实例不是描述符
        pass

Foo().method()    # ❌ TypeError: missing self
```

修复：实现 `__get__`（变成描述符）。

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    def __get__(self, instance, owner):
        if instance is None: return self
        return functools.partial(self, instance)
```

### 形态 4：类作为被装饰对象

```python
def add_repr(cls):
    def __repr__(self):
        return f"{cls.__name__}({self.__dict__})"
    cls.__repr__ = __repr__
    return cls

@add_repr
class User:
    def __init__(self, name): self.name = name
```

### 形态 5：dataclass / functools.cache 等内置装饰器

它们都是上述形态的组合。

---

## 23.3 functools.wraps 原理

```python
WRAPPER_ASSIGNMENTS = ('__module__', '__name__', '__qualname__',
                       '__annotations__', '__doc__')
WRAPPER_UPDATES = ('__dict__',)

def wraps(wrapped, ...):
    return partial(update_wrapper, wrapped=wrapped, ...)

def update_wrapper(wrapper, wrapped, ...):
    for attr in WRAPPER_ASSIGNMENTS:
        try:
            value = getattr(wrapped, attr)
        except AttributeError:
            pass
        else:
            setattr(wrapper, attr, value)
    for attr in WRAPPER_UPDATES:
        getattr(wrapper, attr).update(getattr(wrapped, attr, {}))
    wrapper.__wrapped__ = wrapped       # 保留原函数引用
    return wrapper
```

→ 简单的属性复制，没有魔法。

---

## 23.4 上下文管理器底层

### 23.4.1 with 的字节码语义

```python
with cm as x:
    body

# 等价于（简化）
mgr = cm
exit_func = type(mgr).__exit__   # 注意是从类取，不是实例
value = type(mgr).__enter__(mgr)
exc = True
try:
    try:
        x = value
        body
    except:
        exc = False
        if not exit_func(mgr, *sys.exc_info()):
            raise
finally:
    if exc:
        exit_func(mgr, None, None, None)
```

**关键细节**：
- `__enter__` / `__exit__` 从**类**取，不从实例（PEP 343）
- `__exit__` 返回 True 抑制异常；返回 False/None 让异常继续抛

### 23.4.2 类形式

```python
class Timer:
    def __enter__(self):
        import time
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.perf_counter() - self.start
        print(f"耗时 {self.elapsed:.4f}s")
        return False    # 不抑制异常
```

### 23.4.3 ★ @contextmanager 实现原理

```python
# contextlib.py 简化版
from functools import wraps

class _GeneratorCM:
    def __init__(self, gen):
        self.gen = gen
    
    def __enter__(self):
        try:
            return next(self.gen)
        except StopIteration:
            raise RuntimeError("生成器没有 yield")
    
    def __exit__(self, type, value, traceback):
        if type is None:
            try:
                next(self.gen)
            except StopIteration:
                return False
            else:
                raise RuntimeError("生成器 yield 了多次")
        else:
            try:
                self.gen.throw(type, value, traceback)
            except StopIteration as exc:
                return exc is not value
            except:
                if sys.exc_info()[1] is value:
                    return False
                raise

def contextmanager(func):
    @wraps(func)
    def helper(*args, **kwargs):
        return _GeneratorCM(func(*args, **kwargs))
    return helper
```

**核心思路**：
- `__enter__` = `next(gen)`，拿到 yield 的值
- `__exit__` = 再 `next(gen)`，让生成器走完
- 有异常 = `gen.throw(...)`，把异常注入回 yield 处，让 except 块能捕获

### 23.4.4 实战：理解 try/finally 与 yield

```python
from contextlib import contextmanager

@contextmanager
def transaction(conn):
    try:
        yield conn
        conn.commit()
    except:
        conn.rollback()
        raise

# 等价的类实现
class Transaction:
    def __init__(self, conn): self.conn = conn
    def __enter__(self): return self.conn
    def __exit__(self, exc_type, exc_val, tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        return False
```

### 23.4.5 contextlib.ExitStack（动态上下文）

```python
from contextlib import ExitStack

with ExitStack() as stack:
    files = [stack.enter_context(open(f)) for f in filenames]
    # 所有文件会按反向顺序关闭
```

适合"数量不定的资源"。

### 23.4.6 异步上下文管理器

```python
class AsyncResource:
    async def __aenter__(self):
        await self.connect()
        return self
    async def __aexit__(self, *args):
        await self.close()

# 用 @asynccontextmanager
from contextlib import asynccontextmanager

@asynccontextmanager
async def session():
    s = await create()
    try:
        yield s
    finally:
        await s.close()

async with session() as s:
    ...
```

---

## 23.5 Monkey Patch

### 23.5.1 概念

**运行时替换**模块/类/对象的属性。

```python
import requests

# 原 requests.get
def fake_get(url, **kw):
    return MockResponse(...)

requests.get = fake_get   # 全局替换！
```

### 23.5.2 💡 为什么 Python 允许 monkey patch

Python 的设计哲学：**一切都是对象**，**对象的属性默认可变**。模块、类、实例都是字典（或类字典），可以随意改。

代价：
- 灵活性 → 可测试性（mock）
- 但也 → 隐式行为难追踪、bug 难定位

### 23.5.3 典型场景

#### 测试中替换依赖

```python
import pytest
from unittest.mock import patch

@patch("mymodule.requests.get")
def test_fetch(mock_get):
    mock_get.return_value.json.return_value = {"id": 1}
    result = fetch_user(1)
    assert result["id"] == 1
```

#### 运行时打补丁修 bug

```python
# 第三方库有 bug，自己修不了源码
import buggy_lib

original = buggy_lib.broken_func
def fixed(arg):
    if arg is None: return None
    return original(arg)

buggy_lib.broken_func = fixed
```

#### gevent 的协作式 monkey patch

```python
from gevent import monkey
monkey.patch_all()        # 替换 socket / threading 等为协作式版本
```

### 23.5.4 ⚠️ 哪些不能 patch

```python
# 大多数 builtin 不可改
int.foo = 42              # ❌ TypeError: cannot set 'foo' attribute of int

# 内置类型方法不可换
list.append = my_append   # ❌
```

但你**自己定义的类**可以：
```python
class Foo: pass
Foo.bar = 42              # ✅
Foo().bar                 # 42
```

### 23.5.5 ⚠️ Monkey Patch 的代价

1. **隐式**：阅读代码看不出来
2. **顺序敏感**：patch 必须在使用前完成
3. **作用域**：是全局的，影响所有 import
4. **难调试**：traceback 显示 patch 后的函数
5. **不兼容**：库升级后行为变了

**经验法则**：
- 测试中：用 `unittest.mock.patch`（自动恢复）
- 修第三方 bug：临时方案，长远应该 PR 上游
- 业务逻辑：禁用！用依赖注入代替

---

## 23.6 高级：unittest.mock 的实现

```python
from unittest.mock import patch

with patch("os.getcwd", return_value="/fake"):
    print(os.getcwd())     # /fake

print(os.getcwd())          # 真实目录（patch 已恢复）
```

🔬 **原理**（极简）：

```python
class patch:
    def __init__(self, target, new):
        self.target = target           # "os.getcwd"
        self.new = new
    
    def __enter__(self):
        module_name, attr = self.target.rsplit(".", 1)
        self.module = importlib.import_module(module_name)
        self.original = getattr(self.module, attr)
        setattr(self.module, attr, self.new)
    
    def __exit__(self, *args):
        setattr(self.module, self.attr, self.original)
```

→ 上下文管理器 + monkey patch 的经典组合。

---

## 23.7 实战：写一个事务装饰器

```python
from contextlib import contextmanager
from functools import wraps

@contextmanager
def transaction(session):
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise

def transactional(get_session):
    """装饰器版本"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            session = get_session()
            with transaction(session):
                kwargs["session"] = session
                return func(*args, **kwargs)
        return wrapper
    return decorator

@transactional(get_session=lambda: SessionLocal())
def create_user(name, *, session):
    session.add(User(name=name))
```

→ 装饰器 + 上下文管理器组合的真实场景。

---

## 23.8 常见误区

### ❌ 装饰器忘记 @wraps

```python
def deco(func):
    def wrapper(*args, **kw):
        return func(*args, **kw)
    return wrapper      # 没用 @wraps：__name__/__doc__ 丢失
```

### ❌ 在 finally 里 raise

```python
try:
    ...
except SomeError:
    raise
finally:
    raise OtherError       # 会替换原异常的上下文
```

### ❌ 多个 with 不用复合形式

```python
# 啰嗦
with a() as x:
    with b() as y:
        ...

# 简洁（PEP 617）
with (
    a() as x,
    b() as y,
):
    ...
```

### ❌ 滥用 monkey patch

业务代码里改第三方库 → 排雷无门。

---

## 23.9 面试常问

### Q1：@deco 等价于什么？

**答**：`func = deco(func)`。带参数装饰器是 `func = deco(arg)(func)`。

### Q2：with 语句怎么实现？

**答**：调用 `__enter__` 拿到值，try 块执行 body，finally 调用 `__exit__`。`__exit__` 返回 True 可抑制异常。

### Q3：@contextmanager 怎么用生成器实现 with？

**答**：见 23.4.3。`__enter__` = `next(gen)`，`__exit__` = 再 `next` 或 `gen.throw(exc)`。

### Q4：什么是 monkey patch？什么时候用？

**答**：运行时修改对象属性。测试中替换依赖（用 mock.patch），临时修第三方 bug。**业务代码避免**。

### Q5：类装饰器作用于方法时为什么会出问题？

**答**：类的实例不是描述符，不会自动绑定 self。需要实现 `__get__` 让它变成描述符。

---

## 23.10 练习题

### 练习 23.1（中级）

实现一个 `@retry(times=3, exceptions=(Exception,))` 装饰器，支持 sync 和 async。

<details><summary>答案</summary>

```python
import asyncio
from functools import wraps

def retry(times=3, exceptions=(Exception,)):
    def deco(func):
        @wraps(func)
        async def async_wrapper(*args, **kw):
            for i in range(times):
                try: return await func(*args, **kw)
                except exceptions:
                    if i == times - 1: raise
        @wraps(func)
        def sync_wrapper(*args, **kw):
            for i in range(times):
                try: return func(*args, **kw)
                except exceptions:
                    if i == times - 1: raise
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return deco
```
</details>

### 练习 23.2（高级）

不用 contextlib，自己实现 `@contextmanager`。

<details><summary>答案</summary>

见 23.4.3 的 `_GeneratorCM` 实现。
</details>

### 练习 23.3（专家）

实现 `mock.patch` 的简化版，作为上下文管理器使用。

<details><summary>答案</summary>

```python
import importlib

class patch:
    def __init__(self, target, new):
        self.target = target
        self.new = new
    def __enter__(self):
        mod_name, _, attr = self.target.rpartition(".")
        self.mod = importlib.import_module(mod_name)
        self.attr = attr
        self.orig = getattr(self.mod, attr)
        setattr(self.mod, attr, self.new)
        return self.new
    def __exit__(self, *args):
        setattr(self.mod, self.attr, self.orig)
```
</details>

---

**上一章：[22 描述符与元类](22_描述符与元类深入.md)** | **回到 [README](README.md)**

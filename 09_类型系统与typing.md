# 09. 类型系统与 typing

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐ (中级) |
> | **前置知识** | [01 函数](01_函数篇.md)、[02 OOP](02_类与面向对象篇.md) |
> | **学习目标** | 掌握类型注解、TypeVar/Generic/Protocol、能配合 mypy 检查、知道 Pydantic 与静态类型的关系 |
> | **CPython 版本** | 3.12+（含 PEP 695 新泛型语法） |
> | **规范 vs 实现** | 类型注解语法、typing 模块语义为语言规范；mypy/pyright 等检查器是独立工具 |

---

> Python 是动态类型语言，但**好的工程项目必须使用类型注解**。  
> 类型注解能让 IDE 智能提示、让 mypy 提前发现 bug、让团队协作更顺畅。

---

## 9.0 知识地图

```
Python 类型系统的两面性
├── 运行时 ────── 动态类型，类型不强制
│   └── 鸭子类型：能 .quack() 就是鸭子
│
└── 静态时 ────── 类型注解 + 类型检查器（mypy/pyright）
    ├── 基础类型注解
    ├── typing 模块（List, Dict, Optional, Union...）
    ├── 泛型 (TypeVar, Generic)
    ├── Protocol（结构化子类型）
    ├── TypedDict（字典字段类型）
    └── Literal / Final / NewType / Annotated
```

**本章要回答**：
1. 动态类型究竟是什么？为什么 Python 这样设计？
2. 类型注解会影响运行时吗？
3. 怎么写出"类型正确"的代码？
4. 泛型是什么？为什么需要它？
5. Protocol 和继承有什么区别？

---

## 9.1 动态类型 vs 静态类型

### 9.1.1 概念区分

| | 静态类型（C/Java/Rust） | 动态类型（Python/JS） |
|--|--|--|
| 类型检查时机 | 编译期 | 运行时 |
| 变量是否有类型 | 是 | **不是**（对象有类型，变量没有） |
| 类型错误 | 编译失败 | 运行时报错 |

### 9.1.2 ★ Python：变量没有类型，对象才有

```python
# ─────────────────────────────────────
# 同一个变量名可以指向任意类型的对象
# ─────────────────────────────────────
x = 1            # x 指向 int 对象
print(type(x))   # 输出: <class 'int'>

x = "hello"      # x 现在指向 str 对象
print(type(x))   # 输出: <class 'str'>

x = [1, 2]       # x 又指向 list 对象
print(type(x))   # 输出: <class 'list'>
```

**关键认知**：在 Python 里说"变量是 int 类型"是错的。准确说法是"变量当前指向的对象是 int 类型"。

### 9.1.3 💡 鸭子类型

```python
# ─────────────────────────────────────
# 不在乎对象的类型，只在乎它能做什么
# ─────────────────────────────────────
def make_noise(animal):
    animal.speak()      # 只要有 speak 方法就行

class Dog:
    def speak(self): print("Woof!")

class Cat:
    def speak(self): print("Meow!")

class Robot:
    def speak(self): print("Beep!")

for a in [Dog(), Cat(), Robot()]:
    make_noise(a)
# 输出:
# Woof!
# Meow!
# Beep!
```

Robot 不是动物，但能 speak —— 在 Python 中就够了。

**好处**：高度灵活，代码复用容易。  
**代价**：bug 可能要等到运行时才暴露。

---

## 9.2 类型注解基础

### 9.2.1 基本语法

```python
# 变量注解
age: int = 25
name: str = "Alice"
scores: list = [85, 92, 78]

# 函数参数和返回值
def greet(name: str, age: int = 0) -> str:
    return f"Hello {name}, age {age}"

# 类属性
class User:
    name: str
    age: int
    
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
```

### 9.2.2 ⚠️ 注解不会强制类型

```python
def add(a: int, b: int) -> int:
    return a + b

print(add(1, 2))        # 输出: 3
print(add("a", "b"))    # 输出: ab   ← 没报错！
```

**类型注解只是"建议"**，运行时不检查。需要 mypy 等工具静态检查：

```bash
$ mypy script.py
script.py:5: error: Argument 1 to "add" has incompatible type "str"; expected "int"
```

### 9.2.3 🔬 注解保存在哪里

```python
def add(a: int, b: int) -> int:
    return a + b

print(add.__annotations__)
# 输出: {'a': <class 'int'>, 'b': <class 'int'>, 'return': <class 'int'>}
```

注解保存在函数对象的 `__annotations__` 属性中，本质就是个字典。可以反射读取（FastAPI 等框架就是这样工作的）。

---

## 9.3 typing 模块（基础）

### 9.3.1 容器类型

```python
from typing import List, Dict, Tuple, Set
# Python 3.9+ 可以直接用内置类型

# 旧写法
def process(items: List[int]) -> Dict[str, int]:
    return {"count": len(items)}

# Python 3.9+ 新写法（推荐）
def process(items: list[int]) -> dict[str, int]:
    return {"count": len(items)}

# 元组：固定长度，每个位置类型可能不同
def get_point() -> tuple[int, int]:
    return (3, 4)

# 元组：变长，元素同类型
def get_numbers() -> tuple[int, ...]:
    return (1, 2, 3, 4, 5)
```

### 9.3.2 Optional 和 Union

```python
from typing import Optional, Union

# Optional[X] 等同于 Union[X, None] 或 X | None
def find_user(user_id: int) -> Optional[str]:
    """返回用户名或 None"""
    db = {1: "Alice", 2: "Bob"}
    return db.get(user_id)

# Python 3.10+
def find_user(user_id: int) -> str | None:
    return db.get(user_id)

# Union：可能是多种类型之一
def parse(x: Union[int, str]) -> int:
    return int(x)

# Python 3.10+
def parse(x: int | str) -> int:
    return int(x)
```

### 9.3.3 ⚠️ Optional 不是"参数可选"

```python
# Optional 表示"可以是 None"，不是"参数可以省略"
def foo(x: Optional[int]):    # x 必须传，但可以是 None
    pass

foo(1)
foo(None)
# foo()       # ❌ TypeError: missing argument

# "可省略" 用默认值
def bar(x: int | None = None):    # 可省略，默认 None
    pass

bar()
bar(1)
```

### 9.3.4 Callable

```python
from typing import Callable

# Callable[[参数类型...], 返回类型]
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

apply(lambda x, y: x + y, 1, 2)   # 输出: 3

# 任意签名
def register(handler: Callable):
    pass
```

### 9.3.5 Any（万能类型，慎用）

```python
from typing import Any

def parse_json(s: str) -> Any:    # 不知道是什么类型
    import json
    return json.loads(s)

# Any 关闭类型检查 → 失去注解的意义
# 尽量用 Union 或 object 代替
```

---

## 9.4 泛型 TypeVar

### 9.4.1 为什么需要泛型

```python
# ❌ 不用泛型：返回类型丢失
def first(items: list) -> object:
    return items[0]

x = first([1, 2, 3])    # x 的类型被 mypy 推断为 object
x.bit_length()          # mypy 报错！
```

**问题**：函数参数和返回类型有关联（输入 list[int] 应该返回 int），但 `list -> object` 表达不出来。

### 9.4.2 用 TypeVar 解决

```python
from typing import TypeVar

T = TypeVar('T')

def first(items: list[T]) -> T:
    return items[0]

x = first([1, 2, 3])    # mypy 知道 x: int
x.bit_length()          # ✅
y = first(["a", "b"])   # mypy 知道 y: str
y.upper()               # ✅
```

`T` 是占位符——调用时由实参类型决定。

### 9.4.3 有约束的 TypeVar

```python
from typing import TypeVar

# 限定 T 必须是 int 或 float
Number = TypeVar('Number', int, float)

def double(x: Number) -> Number:
    return x * 2

double(5)       # ✅ Number = int
double(5.0)     # ✅ Number = float
double("a")     # ❌ mypy 报错
```

### 9.4.4 边界 TypeVar

```python
from typing import TypeVar

# T 必须是 Comparable 或其子类
class Comparable:
    def __lt__(self, other) -> bool: ...

T = TypeVar('T', bound=Comparable)

def maximum(items: list[T]) -> T:
    return max(items)
```

---

## 9.5 泛型：TypeVar 与 Generic

> ⚠️ **如果你的项目已用 Python 3.12+，直接跳到 §9.5b 看新语法**——更短、更清晰。  
> 本节保留旧写法作为"兼容参考"（3.9-3.11 项目仍需要）。

### 9.5.1 旧写法（3.9-3.11 兼容）

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []
    
    def push(self, item: T) -> None:
        self._items.append(item)
    
    def pop(self) -> T:
        return self._items.pop()
    
    def peek(self) -> T:
        return self._items[-1]

# 使用
int_stack: Stack[int] = Stack()
int_stack.push(1)
int_stack.push(2)
n: int = int_stack.pop()    # mypy 知道是 int
# int_stack.push("a")       # mypy 报错

str_stack: Stack[str] = Stack()
str_stack.push("hello")
```

---

## 9.5b ★ PEP 695：新泛型语法（3.12+，推荐）

> **本节是 3.12 的旗舰特性**。如果你的项目已 3.12+，**强烈推荐用新语法**——更短、更清晰、不需要 import TypeVar。

### 9.5b.1 泛型函数

```python
# 旧（仍可用）
from typing import TypeVar
T = TypeVar('T')
def first(items: list[T]) -> T:
    return items[0]

# 新（PEP 695，3.12+）
def first[T](items: list[T]) -> T:
    return items[0]
```

### 9.5b.2 泛型类

```python
# 旧
from typing import TypeVar, Generic
T = TypeVar('T')
class Stack(Generic[T]):
    def push(self, x: T): ...
    def pop(self) -> T: ...

# 新（3.12+）
class Stack[T]:
    def push(self, x: T): ...
    def pop(self) -> T: ...
```

### 9.5b.3 类型别名

```python
# 旧
from typing import TypeAlias
Vector: TypeAlias = list[float]

# 新（3.12+）：type 是软关键字
type Vector = list[float]
type Tree[T] = T | list[Tree[T]]   # 泛型别名 + 自递归
```

### 9.5b.4 约束与边界

```python
# 边界（必须是 Comparable 子类）
class SortedList[T: Comparable]:
    ...

# 多约束
def f[T: (int, float)](x: T) -> T:    # T 只能是 int 或 float
    return x * 2
```

### 9.5b.5 🔬 底层差异

```python
# PEP 695 创建的 TypeVar 是真正"作用域局部"的
class Stack[T]:
    pass

print(Stack.__type_params__)   # (T,)  ← 类有 __type_params__
# 旧 TypeVar 是模块级全局，可能跨类共享
```

→ 新语法的 TypeVar 仅在该类/函数内可见，避免全局污染。

---

## 9.5c PEP 563/649：注解的延迟求值

### 注解默认是"立即求值"

```python
# 默认行为：注解在 class/def 定义时求值
class Tree:
    def __init__(self, parent: Tree):    # ❌ NameError: Tree 还没定义完
        pass
```

### 解决 1：from __future__ import annotations（PEP 563）

```python
from __future__ import annotations    # ★ 所有注解变成字符串

class Tree:
    def __init__(self, parent: Tree):   # ✅ 不再求值，仅当字符串保存
        pass

# 副作用：__annotations__ 变成字符串
print(Tree.__init__.__annotations__)
# {'parent': 'Tree'}    ← 注意是字符串

# 框架要拿到真实类型需用 typing.get_type_hints()
import typing
print(typing.get_type_hints(Tree.__init__))
# {'parent': <class '__main__.Tree'>}
```

### 解决 2：字符串注解（手动）

```python
class Tree:
    def __init__(self, parent: "Tree"):    # ✅ 字符串始终是延迟的
        pass
```

### PEP 649（3.13+，规划中）

3.13 计划用 PEP 649（lazy annotations via descriptors）替代 PEP 563。届时注解默认延迟求值，但访问时返回真实对象——既解决前向引用，又保持类型对象可用。

→ **3.12 项目推荐**：在每个 .py 文件顶部加 `from __future__ import annotations`，性能更好（注解不求值），所有注解自动变字符串。

---

## 9.6 Protocol（结构化子类型）

### 9.6.1 鸭子类型 + 类型检查

```python
from typing import Protocol

class Speaks(Protocol):
    def speak(self) -> None: ...

class Dog:                       # 不需要继承 Speaks
    def speak(self) -> None:
        print("Woof!")

class Robot:                     # 也不需要继承
    def speak(self) -> None:
        print("Beep!")

def make_noise(thing: Speaks) -> None:
    thing.speak()

make_noise(Dog())     # ✅
make_noise(Robot())   # ✅
make_noise(42)        # ❌ mypy: int 没有 speak 方法
```

### 9.6.2 💡 Protocol vs ABC（抽象基类）

| | ABC | Protocol |
|--|-----|----------|
| 关系 | 必须显式继承 | **隐式**：有方法即可 |
| 风格 | 名义子类型 | 结构化子类型 |
| 类比 | "我是鸭子" | "你像鸭子就够了" |

**何时用 Protocol**：
- 兼容已有代码（不能修改其继承）
- 做"插件式"接口
- 鸭子类型的代码补上类型检查

**何时用 ABC**：
- 需要提供默认实现
- 要强制子类必须重写某些方法

### 9.6.3 运行时检查（@runtime_checkable）

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Closable(Protocol):
    def close(self) -> None: ...

f = open("test.txt")
print(isinstance(f, Closable))   # 输出: True
```

注意：运行时检查只看方法存不存在，不检查签名。

---

## 9.7 TypedDict（结构化字典）

### 9.7.1 给字典加字段类型

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int
    email: str

# 使用
user: User = {"name": "Alice", "age": 30, "email": "a@b.c"}

# 错误用法
# user2: User = {"name": "Bob"}      # mypy: 缺少 age, email
# user["age"] = "thirty"             # mypy: 期望 int
```

### 9.7.2 可选字段

```python
class User(TypedDict, total=False):    # total=False：所有字段可选
    name: str
    age: int

# 或者细粒度控制
from typing import NotRequired

class User(TypedDict):
    name: str                    # 必需
    age: NotRequired[int]        # 可选
```

**使用场景**：JSON API 返回值、配置字典。

---

## 9.8 Literal（字面量类型）

```python
from typing import Literal

def set_mode(mode: Literal["read", "write", "append"]) -> None:
    pass

set_mode("read")        # ✅
set_mode("delete")      # ❌ mypy 报错

# 数字字面量
def http_status(code: Literal[200, 404, 500]) -> str:
    pass
```

**使用场景**：枚举式参数（避免拼写错误）。

---

## 9.9 NewType（语义化类型）

```python
from typing import NewType

UserId = NewType('UserId', int)
ProductId = NewType('ProductId', int)

def get_user(uid: UserId) -> str:
    pass

uid = UserId(42)
pid = ProductId(42)

get_user(uid)       # ✅
get_user(pid)       # ❌ mypy 报错（虽然底层都是 int）
get_user(42)        # ❌ 必须是 UserId
```

**意义**：底层都是 int，但语义不同——避免 user_id 和 product_id 混用。

---

## 9.10 Final（不可重赋值）

```python
from typing import Final

MAX_SIZE: Final = 100
MAX_SIZE = 200    # ❌ mypy 报错

class Config:
    MAX: Final[int] = 100

class SubConfig(Config):
    # MAX = 200    # ❌ Final 不可被子类覆盖
    pass
```

---

## 9.11 类型守卫（类型缩窄）

```python
from typing import Union

def process(x: int | str) -> str:
    if isinstance(x, int):
        # 这里 mypy 知道 x: int
        return str(x * 2)
    else:
        # 这里 mypy 知道 x: str
        return x.upper()
```

mypy 会根据 `isinstance` 自动缩窄类型。

### TypeGuard（自定义类型守卫）

```python
from typing import TypeGuard

def is_str_list(items: list[object]) -> TypeGuard[list[str]]:
    return all(isinstance(x, str) for x in items)

def process(items: list[object]):
    if is_str_list(items):
        # mypy 知道 items: list[str]
        return [s.upper() for s in items]
```

---

## 9.12 实际项目实践

### 9.12.1 使用 mypy 检查

```bash
pip install mypy
mypy your_module.py
```

`mypy.ini` 配置：

```ini
[mypy]
python_version = 3.11
strict = true
warn_return_any = true
warn_unused_ignores = true
```

### 9.12.2 渐进式类型化

```python
# 旧代码
def legacy_func(data):
    return data["key"]

# 第一步：加上参数类型
def legacy_func(data: dict) -> object:
    return data["key"]

# 第二步：精确化
def legacy_func(data: dict[str, int]) -> int:
    return data["key"]

# 第三步：用 TypedDict
class Data(TypedDict):
    key: int

def legacy_func(data: Data) -> int:
    return data["key"]
```

### 9.12.3 dataclass + 类型注解

```python
from dataclasses import dataclass

@dataclass
class User:
    name: str
    age: int
    email: str = ""
    
    def is_adult(self) -> bool:
        return self.age >= 18
```

`@dataclass` 利用注解自动生成 `__init__`、`__repr__`、`__eq__`。

### 9.12.4 Pydantic（运行时类型验证）

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# 自动验证
u = User(name="Alice", age=30)            # ✅
# u = User(name="Alice", age="thirty")    # ❌ ValidationError

# JSON 反序列化
u = User.model_validate_json('{"name":"Alice","age":30}')
```

**Pydantic 是运行时检查，mypy 是静态检查**——常常配合使用。

---

## 9.13 常见误区

### 误区 1：以为类型注解会影响运行时

```python
def add(a: int, b: int) -> int:
    return a + b

add("1", "2")    # 不会报错，输出 "12"
```

类型注解只是"标签"，运行时不检查。要检查得用 `isinstance` 或 Pydantic。

### 误区 2：滥用 Any

```python
def process(data: Any) -> Any:    # 等于没注解
    pass
```

尽量用具体类型或泛型。

### 误区 3：用旧的 typing 容器

```python
# Python 3.9+ 不要这样写
from typing import List, Dict
def f(x: List[int]) -> Dict[str, int]: ...

# 直接用内置类型
def f(x: list[int]) -> dict[str, int]: ...
```

### 误区 4：忘记 forward reference

```python
class Tree:
    def __init__(self, parent: Tree):    # ❌ Tree 还没定义完
        pass

# 解决 1：字符串
class Tree:
    def __init__(self, parent: "Tree"):
        pass

# 解决 2：from __future__ import annotations
from __future__ import annotations

class Tree:
    def __init__(self, parent: Tree):    # ✅
        pass
```

---

## 9.14 面试常问

### Q1：Python 是动态类型还是静态类型？类型注解有什么用？

**答**：Python 是动态类型——变量没有类型，对象才有。运行时类型可变。

类型注解是**静态类型工具**，不影响运行时行为，但能：
- 让 IDE 智能提示
- 让 mypy 静态检查
- 给协作者看（自文档化）
- 一些框架（FastAPI/Pydantic）用注解做运行时检查

### Q2：Optional[X] 等价于什么？

**答**：等价于 `Union[X, None]`，Python 3.10+ 也可以写 `X | None`。

### Q3：泛型 TypeVar 解决了什么问题？

**答**：让函数/类的输入输出类型有关联。例如 `def first(items: list[T]) -> T`，调用 `first([1,2,3])` 时 `T` 自动绑定为 `int`。

### Q4：Protocol 和 ABC 的区别？

**答**：
- ABC 是**名义子类型**：必须显式 `class Foo(BaseABC)`
- Protocol 是**结构化子类型**：只要有对应方法就视为符合

Protocol 让鸭子类型有了类型检查。

### Q5：以下注解会报错吗？

```python
def f(x: list = []):
    pass
```

**答**：mypy 不会因为类型报错，但代码本身有可变默认参数陷阱。建议：

```python
def f(x: list | None = None):
    if x is None:
        x = []
```

---

## 9.15 练习题

### 练习 9.1（基础）

为以下函数加上完整类型注解：

```python
def process_users(users, min_age):
    return [u for u in users if u["age"] >= min_age]
```

<details>
<summary>答案</summary>

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int

def process_users(users: list[User], min_age: int) -> list[User]:
    return [u for u in users if u["age"] >= min_age]
```
</details>

### 练习 9.2（中级）

实现一个泛型缓存类，能存任意类型的 key 和 value：

```python
cache: Cache[str, int] = Cache()
cache.set("a", 1)
n: int = cache.get("a")    # 类型检查器应当推断为 int
```

<details>
<summary>答案</summary>

```python
from typing import TypeVar, Generic

K = TypeVar('K')
V = TypeVar('V')

class Cache(Generic[K, V]):
    def __init__(self) -> None:
        self._store: dict[K, V] = {}
    
    def set(self, key: K, value: V) -> None:
        self._store[key] = value
    
    def get(self, key: K) -> V | None:
        return self._store.get(key)
```
</details>

### 练习 9.3（中级）

用 Protocol 定义"可比较"接口，并实现一个 max 函数：

<details>
<summary>答案</summary>

```python
from typing import Protocol, TypeVar

class Comparable(Protocol):
    def __lt__(self, other) -> bool: ...

T = TypeVar('T', bound=Comparable)

def my_max(items: list[T]) -> T:
    if not items:
        raise ValueError("empty list")
    result = items[0]
    for item in items[1:]:
        if result < item:
            result = item
    return result

my_max([3, 1, 4])      # ✅
my_max(["b", "a"])     # ✅
```
</details>

### 练习 9.4（高级）

将以下 dict 改为 TypedDict，并加上类型守卫：

```python
def get_response():
    return {"status": "ok", "data": [1, 2, 3], "error": None}
```

<details>
<summary>答案</summary>

```python
from typing import TypedDict, Literal, NotRequired, TypeGuard

class OkResponse(TypedDict):
    status: Literal["ok"]
    data: list[int]
    error: None

class ErrorResponse(TypedDict):
    status: Literal["error"]
    data: None
    error: str

Response = OkResponse | ErrorResponse

def is_ok(r: Response) -> TypeGuard[OkResponse]:
    return r["status"] == "ok"

def handle(r: Response):
    if is_ok(r):
        # 这里 mypy 知道 r: OkResponse
        for n in r["data"]:
            print(n)
    else:
        # 这里 r: ErrorResponse
        print(r["error"])
```
</details>

---

## 本章总结

| 概念 | 一句话 |
|------|--------|
| 动态类型 | 变量无类型，对象有类型 |
| 鸭子类型 | 不看类型看能力 |
| 类型注解 | 不影响运行时，靠 mypy 检查 |
| Optional[X] | X 或 None |
| TypeVar | 函数级别的类型参数 |
| Generic | 类级别的类型参数 |
| Protocol | 结构化子类型，鸭子类型 + 类型检查 |
| TypedDict | 给字典字段加类型 |
| Literal | 枚举式字面量类型 |
| NewType | 同底层不同语义的类型 |

---

**上一章：[08_作用域与LEGB深入](08_作用域与LEGB深入.md)** | **下一章：[10_GIL与CPython执行机制](10_GIL与CPython执行机制.md)**

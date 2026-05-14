# Python 进阶基础速查手册

> 第一册学完后，接着看这份。补全所有基础阶段缺失的知识点。

---

## 学习顺序总览

```
第一册已覆盖：
  ① 数据类型 → ② 变量 → ③ 字符串 → ④ 列表 → ⑤ 元组
  → ⑥ 字典 → ⑦ 集合 → ⑧ 条件判断 → ⑨ 循环
  → ⑩ 函数 → ⑪ 内置函数 → ⑫ 文件操作
  → ⑬ 异常处理 → ⑭ 模块导入 → ⑮ 运算符 → ⑯ 技巧

本册补充（按学习顺序）：
  ⑰ 作用域与命名空间 → ⑱ 深拷贝与浅拷贝
  → ⑲ 装饰器 → ⑳ 生成器与迭代器
  → ㉑ 面向对象（类与对象） → ㉒ 继承与多态
  → ㉓ 魔术方法 → ㉔ 正则表达式
  → ㉕ 常用标准库 → ㉖ 虚拟环境与包管理
  → ㉗ 程序调试技巧
```

---

## 十七、作用域与命名空间（LEGB 规则）

```python
# Python 查找变量的顺序: L → E → G → B
# L: Local      局部作用域（函数内部）
# E: Enclosing  外层函数作用域（闭包）
# G: Global     全局作用域（模块级别）
# B: Built-in   内置作用域（Python 自带）

x = "全局"          # G: 全局

def outer():
    x = "外层"      # E: 外层函数
    
    def inner():
        x = "局部"  # L: 局部
        print(x)    # 打印 "局部"
    
    inner()

outer()
print(x)            # 打印 "全局"
```

### global 和 nonlocal

```python
# global —— 在函数内修改全局变量
count = 0

def increment():
    global count    # 声明要修改全局变量
    count += 1

increment()
print(count)  # 1

# nonlocal —— 在内层函数修改外层函数变量
def outer():
    msg = "hello"
    
    def inner():
        nonlocal msg    # 声明要修改外层变量
        msg = "world"
    
    inner()
    print(msg)  # "world"

outer()
```

---

## 十八、深拷贝与浅拷贝

```python
import copy

# 原始数据
original = [[1, 2, 3], [4, 5, 6]]

# 浅拷贝 —— 只复制第一层，内部对象还是共享的
shallow = copy.copy(original)
# 或者: shallow = original[:]
# 或者: shallow = list(original)

shallow[0].append(99)
print(original)  # [[1, 2, 3, 99], [4, 5, 6]]  原始也变了!

# 深拷贝 —— 完全独立的副本，互不影响
original = [[1, 2, 3], [4, 5, 6]]
deep = copy.deepcopy(original)

deep[0].append(99)
print(original)  # [[1, 2, 3], [4, 5, 6]]  原始不受影响!

# ⚠️ 记住:
# 赋值 (=)    → 不是复制，只是多了一个标签
# 浅拷贝       → 只复制外壳，内部还是共享
# 深拷贝       → 完全独立，递归复制所有层
```

---

## 十九、装饰器

```python
# 装饰器 = 一个接收函数、返回函数的函数
# 用途：在不修改原函数的情况下，给它加功能

# 基本装饰器
def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 耗时: {end - start:.4f}秒")
        return result
    return wrapper

# 使用 @ 语法
@timer
def slow_function():
    import time
    time.sleep(1)
    print("执行完毕")

slow_function()
# 输出:
# 执行完毕
# slow_function 耗时: 1.0012秒

# 上面的 @timer 等价于:
# slow_function = timer(slow_function)
```

### 常用装饰器场景

```python
# 1. 日志记录
def log(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}，参数: {args}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"返回: {result}")
        return result
    return wrapper

@log
def add(a, b):
    return a + b

add(1, 2)
# 调用 add，参数: (1, 2), {}
# 返回: 3

# 2. 带参数的装饰器
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def say_hi():
    print("Hi!")

say_hi()  # 打印 3 次 "Hi!"
```

---

## 二十、生成器与迭代器

### 20.1 迭代器

```python
# 迭代器 = 实现了 __iter__ 和 __next__ 的对象
# 所有 for 循环底层都在用迭代器

lst = [1, 2, 3]
it = iter(lst)      # 获取迭代器
next(it)            # 1
next(it)            # 2
next(it)            # 3
# next(it)          # StopIteration 异常!

# for 循环的本质:
# for x in lst:  等价于:
it = iter(lst)
while True:
    try:
        x = next(it)
        print(x)
    except StopIteration:
        break
```

### 20.2 生成器（重点!）

```python
# 生成器 = 用 yield 的函数（惰性求值，省内存）

def count_up(n):
    """从 1 数到 n"""
    i = 1
    while i <= n:
        yield i     # 暂停，返回值，下次从这里继续
        i += 1

# 使用
for num in count_up(5):
    print(num)      # 1 2 3 4 5

# 生成器表达式（类似列表推导式，但用圆括号）
squares = (x**2 for x in range(1000000))  # 不占内存!
# 对比: [x**2 for x in range(1000000)]   # 占大量内存!

next(squares)  # 0
next(squares)  # 1
next(squares)  # 4

# ⚠️ 生成器只能遍历一次!
gen = (x for x in range(3))
list(gen)   # [0, 1, 2]
list(gen)   # []  ← 第二次为空!
```

### 20.3 yield 实际应用

```python
# 读取大文件（不会一次加载到内存）
def read_large_file(filepath):
    with open(filepath, "r") as f:
        for line in f:
            yield line.strip()

# 无限序列
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fibonacci()
[next(fib) for _ in range(10)]
# [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

---

## 二十一、面向对象（类与对象）

```python
# 类 = 模板/蓝图
# 对象 = 根据模板创建的实例

class Dog:
    # 类属性（所有实例共享）
    species = "犬科"
    
    # 初始化方法（构造函数）
    def __init__(self, name, age):
        # 实例属性（每个实例独立）
        self.name = name
        self.age = age
    
    # 实例方法
    def bark(self):
        return f"{self.name}: 汪汪!"
    
    def info(self):
        return f"{self.name}, {self.age}岁, {self.species}"

# 创建实例
dog1 = Dog("旺财", 3)
dog2 = Dog("小白", 5)

print(dog1.bark())   # "旺财: 汪汪!"
print(dog2.info())   # "小白, 5岁, 犬科"

# self 是什么？
# self = 当前实例本身，Python 自动传入，不用手动传
```

### 类方法与静态方法

```python
class MyClass:
    count = 0  # 类属性
    
    def __init__(self):
        MyClass.count += 1
    
    # 实例方法 → 操作实例 (self)
    def instance_method(self):
        return f"实例方法，self={self}"
    
    # 类方法 → 操作类本身 (cls)
    @classmethod
    def class_method(cls):
        return f"类方法，count={cls.count}"
    
    # 静态方法 → 不操作实例也不操作类
    @staticmethod
    def static_method():
        return "静态方法，和类没直接关系"

obj = MyClass()
obj.instance_method()       # 实例调用
MyClass.class_method()      # 类调用
MyClass.static_method()     # 都能调用
```

---

## 二十二、继承与多态

```python
# 继承 = 子类获得父类的所有属性和方法

class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        return "..."

class Cat(Animal):          # Cat 继承 Animal
    def speak(self):        # 重写父类方法
        return f"{self.name}: 喵~"

class Dog(Animal):
    def speak(self):
        return f"{self.name}: 汪!"

# 多态 = 同一方法，不同对象有不同行为
animals = [Cat("咪咪"), Dog("旺财"), Cat("橘子")]
for animal in animals:
    print(animal.speak())
# 咪咪: 喵~
# 旺财: 汪!
# 橘子: 喵~

# super() —— 调用父类方法
class Puppy(Dog):
    def __init__(self, name, toy):
        super().__init__(name)  # 调用 Dog 的 __init__
        self.toy = toy
    
    def play(self):
        return f"{self.name} 在玩 {self.toy}"

p = Puppy("小黄", "球")
print(p.speak())   # "小黄: 汪!"（继承自 Dog）
print(p.play())    # "小黄 在玩 球"

# 检查继承关系
isinstance(p, Puppy)   # True
isinstance(p, Dog)     # True
isinstance(p, Animal)  # True
issubclass(Dog, Animal)  # True
```

---

## 二十三、魔术方法（双下划线方法）

```python
class Vector:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    
    # 字符串表示
    def __repr__(self):     # 给开发者看（调试用）
        return f"Vector({self.x}, {self.y})"
    
    def __str__(self):      # 给用户看（print 用）
        return f"({self.x}, {self.y})"
    
    # 运算符重载
    def __add__(self, other):       # +
        return Vector(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other):       # -
        return Vector(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar):      # *
        return Vector(self.x * scalar, self.y * scalar)
    
    # 比较
    def __eq__(self, other):        # ==
        return self.x == other.x and self.y == other.y
    
    # 长度
    def __len__(self):              # len()
        return int((self.x**2 + self.y**2) ** 0.5)
    
    # 可以用 [] 访问
    def __getitem__(self, index):   # obj[i]
        if index == 0: return self.x
        if index == 1: return self.y
        raise IndexError

v1 = Vector(1, 2)
v2 = Vector(3, 4)
print(v1 + v2)    # (4, 6)
print(v1 * 3)     # (3, 6)
print(v1 == v2)   # False
print(v1[0])      # 1
```

### 常用魔术方法速查

```python
# 创建与销毁
__init__(self)          # 初始化
__del__(self)           # 销毁时调用

# 字符串
__str__(self)           # str() / print()
__repr__(self)          # repr() / 交互式环境

# 比较
__eq__(self, other)     # ==
__lt__(self, other)     # <
__gt__(self, other)     # >
__le__(self, other)     # <=
__ge__(self, other)     # >=

# 算术
__add__  __sub__  __mul__  __truediv__  # + - * /
__floordiv__  __mod__  __pow__          # // % **

# 容器
__len__(self)           # len()
__getitem__(self, key)  # obj[key]
__setitem__(self, key, value)  # obj[key] = value
__contains__(self, item)       # in 运算符

# 调用
__call__(self, ...)     # 让对象可以像函数一样调用 obj()

# 上下文管理
__enter__(self)         # with 开始
__exit__(self, ...)     # with 结束
```

---

## 二十四、正则表达式

```python
import re

text = "我的手机号是 13812345678，邮箱是 test@example.com"

# 常用函数
re.search(pattern, text)    # 找第一个匹配
re.findall(pattern, text)   # 找所有匹配（返回列表）
re.sub(pattern, repl, text) # 替换
re.match(pattern, text)     # 从开头匹配
re.split(pattern, text)     # 按模式分割
```

### 常用模式

```python
# 基础
.       # 任意字符（除换行）
\d      # 数字 [0-9]
\D      # 非数字
\w      # 字母/数字/下划线 [a-zA-Z0-9_]
\W      # 非 \w
\s      # 空白字符（空格、tab、换行）
\S      # 非空白

# 量词
*       # 0次或多次
+       # 1次或多次
?       # 0次或1次
{n}     # 恰好n次
{n,m}   # n到m次

# 位置
^       # 开头
$       # 结尾
\b      # 单词边界

# 分组
()      # 分组捕获
|       # 或

# 实际例子
phone = re.findall(r"1[3-9]\d{9}", text)
# ['13812345678']

email = re.findall(r"[\w.]+@[\w]+\.[\w]+", text)
# ['test@example.com']

# 提取分组
m = re.search(r"(\d{3})(\d{4})(\d{4})", "13812345678")
m.group(0)  # '13812345678'  完整匹配
m.group(1)  # '138'          第一组
m.group(2)  # '1234'         第二组

# 替换
result = re.sub(r"\d", "*", "手机: 13812345678")
# "手机: ***********"
```

---

## 二十五、常用标准库

### 25.1 os 和 pathlib（文件/路径操作）

```python
import os
from pathlib import Path

# os 模块
os.getcwd()              # 当前工作目录
os.listdir(".")          # 列出目录内容
os.path.exists("file")   # 文件是否存在
os.path.join("a", "b")   # 拼接路径: "a/b"
os.makedirs("a/b/c", exist_ok=True)  # 创建多级目录

# pathlib（更现代，推荐!）
p = Path(".")
list(p.glob("*.py"))     # 当前目录所有 .py 文件
p.exists()               # 是否存在
p.is_file()              # 是不是文件
p.is_dir()               # 是不是目录
p / "sub" / "file.txt"   # 拼接路径（用 /）
```

### 25.2 datetime（日期时间）

```python
from datetime import datetime, timedelta

# 获取当前时间
now = datetime.now()
print(now)  # 2025-01-01 12:30:45.123456

# 格式化
now.strftime("%Y-%m-%d %H:%M:%S")  # "2025-01-01 12:30:45"
now.strftime("%Y年%m月%d日")        # "2025年01月01日"

# 解析字符串为日期
dt = datetime.strptime("2025-01-01", "%Y-%m-%d")

# 时间运算
tomorrow = now + timedelta(days=1)
week_ago = now - timedelta(weeks=1)
diff = datetime(2025, 12, 31) - now
print(diff.days)  # 剩余天数
```

### 25.3 json（数据交换）

```python
import json

# Python 对象 → JSON 字符串
data = {"name": "小明", "age": 18, "scores": [90, 85, 92]}
json_str = json.dumps(data, ensure_ascii=False, indent=2)
print(json_str)

# JSON 字符串 → Python 对象
obj = json.loads(json_str)
print(obj["name"])  # "小明"

# 读写 JSON 文件
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

with open("data.json", "r", encoding="utf-8") as f:
    loaded = json.load(f)
```

### 25.4 random（随机数）

```python
import random

random.random()           # 0~1 之间的随机小数
random.randint(1, 100)    # 1~100 之间的随机整数
random.choice([1, 2, 3])  # 随机选一个
random.sample([1,2,3,4,5], 3)  # 随机取3个（不重复）
random.shuffle(lst)       # 原地打乱列表

# 设置随机种子（结果可复现）
random.seed(42)
```

### 25.5 collections（高级容器）

```python
from collections import Counter, defaultdict, deque

# Counter —— 计数器
words = ["apple", "banana", "apple", "cherry", "apple"]
c = Counter(words)
c.most_common(2)  # [('apple', 3), ('banana', 1)]

# defaultdict —— 带默认值的字典
dd = defaultdict(list)
dd["fruits"].append("apple")   # 不用先判断键是否存在
dd["fruits"].append("banana")
# {'fruits': ['apple', 'banana']}

# deque —— 双端队列（两头都能快速操作）
dq = deque([1, 2, 3])
dq.appendleft(0)   # deque([0, 1, 2, 3])
dq.popleft()       # 0
```

---

## 二十六、虚拟环境与包管理

```python
# 为什么需要虚拟环境？
# → 不同项目可能需要不同版本的库，互不干扰

# 创建虚拟环境
# 终端执行:
# python -m venv myenv

# 激活虚拟环境
# Windows:  myenv\Scripts\activate
# Mac/Linux: source myenv/bin/activate

# 退出虚拟环境
# deactivate

# pip 包管理
# pip install requests          安装
# pip install requests==2.28.0  指定版本
# pip uninstall requests        卸载
# pip list                      查看已安装
# pip freeze > requirements.txt 导出依赖
# pip install -r requirements.txt 安装依赖

# ⚠️ 好习惯：
# 1. 每个项目都用虚拟环境
# 2. 项目根目录放一个 requirements.txt
# 3. 不要用 sudo pip install（会污染系统环境）
```

---

## 二十七、程序调试技巧

```python
# 1. print 大法（最简单）
def buggy(x):
    print(f"DEBUG: x = {x}")    # 加调试信息
    result = x * 2
    print(f"DEBUG: result = {result}")
    return result

# 2. assert 断言（快速检查）
def divide(a, b):
    assert b != 0, "除数不能为零!"
    return a / b

# 3. breakpoint()（Python 3.7+ 内置调试器）
def complex_function(data):
    result = []
    for item in data:
        breakpoint()      # 程序会在这里暂停，进入调试模式
        result.append(item * 2)
    return result

# 调试器常用命令:
# n (next)     → 下一行
# s (step)     → 进入函数
# c (continue) → 继续执行
# p variable   → 打印变量
# q (quit)     → 退出调试

# 4. try/except 定位错误
try:
    risky_code()
except Exception as e:
    print(f"错误类型: {type(e).__name__}")
    print(f"错误信息: {e}")
    import traceback
    traceback.print_exc()  # 打印完整错误栈
```

---

## 完整学习路线图

```
▶ 第一阶段（第一册）—— 语法基础
  数据类型 → 变量 → 字符串 → 列表 → 元组 → 字典 → 集合
  → 条件 → 循环 → 函数 → 内置函数 → 文件 → 异常 → 模块 → 运算符

▶ 第二阶段（本册）—— 进阶基础
  作用域 → 深浅拷贝 → 装饰器 → 生成器/迭代器
  → 类与对象 → 继承多态 → 魔术方法 → 正则表达式
  → 标准库 → 虚拟环境 → 调试技巧

▶ 第三阶段（未来）—— 实战应用
  项目实战 → 设计模式 → 网络编程 → 数据库操作
  → Web 开发 → 爬虫 → 数据分析 → 自动化脚本
```

---

## 速记对比表

| 概念 | 关键词 | 一句话 |
|------|--------|--------|
| 作用域 | LEGB | 局部→外层→全局→内置 |
| 浅拷贝 | copy() | 只复制外壳 |
| 深拷贝 | deepcopy() | 完全独立 |
| 装饰器 | @decorator | 不改原函数加功能 |
| 生成器 | yield | 惰性求值省内存 |
| 类 | class | 模板/蓝图 |
| 对象 | instance | 模板造出来的实例 |
| 继承 | class A(B) | 子类继承父类 |
| 多态 | 同方法不同行为 | 一个接口多种实现 |
| 魔术方法 | __xx__ | 自定义对象行为 |
| 正则 | re模块 | 文本模式匹配 |

---

> **建议：先把第一册吃透，再来看这份。每天一个章节，配合敲代码，两周搞定全部基础。**

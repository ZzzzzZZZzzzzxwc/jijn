# Python 基础知识速查手册

> 随时翻阅，反复记忆，直到刻进脑子里。

---

## 一、数据类型

### 1.1 基本类型

```python
# 整数 int —— 无限精度
age = 25
big = 10 ** 100  # Python 整数不会溢出

# 浮点数 float —— 有精度限制
pi = 3.14159
price = 0.1 + 0.2  # 结果是 0.30000000000000004（浮点陷阱!）

# 布尔 bool —— True / False（本质是 int 的子类）
is_valid = True
print(True + True)  # 输出 2

# 字符串 str —— 不可变序列
name = "Python"
name[0]      # 'P'
# name[0] = 'J'  # 报错! 字符串不可变

# 空值 None —— 表示"什么都没有"
result = None
```

### 1.2 类型转换

```python
int("123")      # 123      字符串 → 整数
float("3.14")   # 3.14     字符串 → 浮点
str(100)        # "100"    整数 → 字符串
bool(0)         # False    0 为假
bool("")        # False    空字符串为假
bool([])        # False    空列表为假
bool(None)      # False    None 为假
# 记住：0, 0.0, "", [], {}, (), set(), None → 都是 False
# 其余都是 True
```

### 1.3 类型检查

```python
type(123)           # <class 'int'>
isinstance(123, int)  # True（推荐用这个）
isinstance(True, int) # True! bool 是 int 的子类
```

---

## 二、变量与赋值

```python
# 变量只是"标签"，贴在对象上
a = [1, 2, 3]
b = a          # b 和 a 指向同一个列表!
b.append(4)
print(a)       # [1, 2, 3, 4]  —— a 也变了!

# 要复制，用 .copy() 或切片
c = a.copy()   # 浅拷贝
d = a[:]       # 浅拷贝

# 多重赋值
x, y, z = 1, 2, 3
x, y = y, x   # 交换值（Python 特色）

# 链式赋值
a = b = c = 0  # 三个变量都指向 0
```

### 身份与相等

```python
a = [1, 2]
b = [1, 2]
a == b   # True  值相等
a is b   # False 不是同一个对象

c = a
a is c   # True  是同一个对象

# 用 id() 查看对象地址
id(a), id(c)  # 相同
```

---

## 三、字符串操作（重点!）

### 3.1 创建与基本操作

```python
s = "Hello, Python!"

# 索引（从 0 开始，负数从末尾）
s[0]     # 'H'
s[-1]    # '!'
s[7]     # 'P'

# 切片 [start:stop:step]  包含 start，不包含 stop
s[0:5]   # 'Hello'
s[7:]    # 'Python!'
s[:5]    # 'Hello'
s[::2]   # 'Hlo yhn'  每隔一个取
s[::-1]  # '!nohtyP ,olleH'  反转字符串

# 长度
len(s)   # 14
```

### 3.2 常用方法（必须背熟）

```python
s = "  Hello, World!  "

# 去空白
s.strip()       # "Hello, World!"
s.lstrip()      # "Hello, World!  "
s.rstrip()      # "  Hello, World!"

# 大小写
s.strip().upper()    # "HELLO, WORLD!"
s.strip().lower()    # "hello, world!"
s.strip().title()    # "Hello, World!"
s.strip().capitalize()  # "Hello, world!"

# 查找与替换
"hello".find("ll")      # 2（返回索引，找不到返回 -1）
"hello".index("ll")     # 2（找不到会报错!）
"hello".count("l")      # 2
"hello".replace("l", "L")  # "heLLo"

# 判断
"hello".startswith("he")  # True
"hello".endswith("lo")    # True
"123".isdigit()           # True
"abc".isalpha()           # True
"abc123".isalnum()        # True
"   ".isspace()           # True

# 分割与连接
"a,b,c".split(",")       # ['a', 'b', 'c']
"hello world".split()    # ['hello', 'world']（默认空白分割）
",".join(['a', 'b', 'c'])  # "a,b,c"
```

### 3.3 格式化（三种方式）

```python
name = "小明"
age = 18

# 方式1: f-string（推荐! Python 3.6+）
f"我叫{name}，今年{age}岁"

# 方式2: .format()
"我叫{}，今年{}岁".format(name, age)

# 方式3: % 格式化（老式）
"我叫%s，今年%d岁" % (name, age)

# f-string 高级用法
pi = 3.14159
f"{pi:.2f}"       # "3.14"  保留2位小数
f"{1000000:,}"    # "1,000,000"  千位分隔
f"{42:08d}"       # "00000042"  补零
f"{'hi':>10}"     # "        hi"  右对齐
f"{'hi':<10}"     # "hi        "  左对齐
f"{'hi':^10}"     # "    hi    "  居中
```

---

## 四、列表 List（最常用的容器）

### 4.1 创建与访问

```python
# 创建
nums = [1, 2, 3, 4, 5]
mixed = [1, "hello", True, [1, 2]]  # 可以混合类型
empty = []

# 访问
nums[0]     # 1
nums[-1]    # 5
nums[1:3]   # [2, 3]
```

### 4.2 增删改查

```python
lst = [1, 2, 3]

# 增
lst.append(4)        # [1, 2, 3, 4]      尾部添加
lst.insert(0, 0)     # [0, 1, 2, 3, 4]   指定位置插入
lst.extend([5, 6])   # [0, 1, 2, 3, 4, 5, 6]  扩展

# 删
lst.pop()            # 返回 6，lst = [0, 1, 2, 3, 4, 5]
lst.pop(0)           # 返回 0，lst = [1, 2, 3, 4, 5]
lst.remove(3)        # lst = [1, 2, 4, 5]（删除第一个值为3的元素）
del lst[0]           # lst = [2, 4, 5]
lst.clear()          # lst = []

# 改
lst = [1, 2, 3]
lst[0] = 10          # [10, 2, 3]
lst[0:2] = [20, 30]  # [20, 30, 3]  切片赋值

# 查
nums = [3, 1, 4, 1, 5]
nums.index(4)        # 2（第一次出现的索引）
nums.count(1)        # 2（出现次数）
4 in nums            # True
```

### 4.3 排序与反转

```python
nums = [3, 1, 4, 1, 5, 9]

# 原地排序（修改原列表）
nums.sort()              # [1, 1, 3, 4, 5, 9]
nums.sort(reverse=True)  # [9, 5, 4, 3, 1, 1]

# 生成新列表（不修改原列表）
sorted(nums)             # 返回新列表
sorted(nums, reverse=True)

# 反转
nums.reverse()           # 原地反转
nums[::-1]               # 返回新列表

# 按自定义规则排序
words = ["banana", "apple", "cherry"]
words.sort(key=len)      # 按长度排序: ['apple', 'banana', 'cherry']
words.sort(key=str.lower)  # 忽略大小写排序
```

### 4.4 列表推导式（必须掌握!）

```python
# 基本形式: [表达式 for 变量 in 可迭代对象]
squares = [x**2 for x in range(10)]
# [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

# 带条件: [表达式 for 变量 in 可迭代对象 if 条件]
evens = [x for x in range(20) if x % 2 == 0]
# [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# 嵌套
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat = [num for row in matrix for num in row]
# [1, 2, 3, 4, 5, 6, 7, 8, 9]

# 带 if-else
labels = ["偶数" if x % 2 == 0 else "奇数" for x in range(5)]
# ['偶数', '奇数', '偶数', '奇数', '偶数']
```

---

## 五、元组 Tuple（不可变列表）

```python
# 创建
t = (1, 2, 3)
single = (1,)    # 注意逗号! 没有逗号就是普通括号
empty = ()

# 访问（和列表一样）
t[0]     # 1
t[-1]    # 3
t[1:]    # (2, 3)

# 不可变!
# t[0] = 10  # 报错!

# 解包
a, b, c = (1, 2, 3)
first, *rest = (1, 2, 3, 4, 5)  # first=1, rest=[2,3,4,5]

# 常见用途
# 1. 函数返回多个值
def get_point():
    return (3, 4)  # 返回元组

# 2. 字典的键（列表不能当键）
d = {(0, 0): "origin"}

# 3. 不希望被修改的数据
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
```

---

## 六、字典 Dict（键值对容器）

### 6.1 创建与访问

```python
# 创建
person = {"name": "小明", "age": 18, "city": "北京"}
empty = {}
from_pairs = dict([("a", 1), ("b", 2)])

# 访问
person["name"]        # "小明"
person.get("name")    # "小明"
person.get("phone", "未知")  # "未知"（键不存在时返回默认值）
# person["phone"]    # 报错 KeyError!（所以推荐用 get）
```

### 6.2 增删改查

```python
d = {"a": 1, "b": 2}

# 增/改
d["c"] = 3          # {"a": 1, "b": 2, "c": 3}
d["a"] = 10         # {"a": 10, "b": 2, "c": 3}
d.update({"d": 4, "e": 5})  # 批量更新

# 删
d.pop("a")          # 返回 10，删除键 "a"
d.pop("z", None)    # 键不存在返回 None，不报错
del d["b"]          # 删除键 "b"
d.clear()           # 清空

# 查
d = {"a": 1, "b": 2, "c": 3}
"a" in d            # True（检查键是否存在）
d.keys()            # dict_keys(['a', 'b', 'c'])
d.values()          # dict_values([1, 2, 3])
d.items()           # dict_items([('a', 1), ('b', 2), ('c', 3)])
```

### 6.3 遍历字典

```python
d = {"name": "小明", "age": 18, "city": "北京"}

# 遍历键
for key in d:
    print(key)

# 遍历键值对（最常用）
for key, value in d.items():
    print(f"{key}: {value}")

# 字典推导式
squares = {x: x**2 for x in range(5)}
# {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}
```

---

## 七、集合 Set（无序、不重复）

```python
# 创建
s = {1, 2, 3, 3, 3}  # {1, 2, 3}  自动去重
empty = set()         # 注意! {} 是空字典!

# 添加和删除
s.add(4)        # {1, 2, 3, 4}
s.discard(2)    # {1, 3, 4}  不存在不报错
s.remove(3)     # {1, 4}     不存在会报错!

# 集合运算（核心!）
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a | b    # {1, 2, 3, 4, 5, 6}  并集
a & b    # {3, 4}              交集
a - b    # {1, 2}              差集（a有b没有）
a ^ b    # {1, 2, 5, 6}        对称差集（不同时在两个集合中）

# 常见用途：去重
lst = [1, 2, 2, 3, 3, 3]
unique = list(set(lst))  # [1, 2, 3]（注意顺序可能变）
```

---

## 八、条件判断

```python
# 基本形式
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "D"

# 三元表达式
result = "成年" if age >= 18 else "未成年"

# 常见陷阱
# 判断是否为 None，用 is 不用 ==
if x is None:
    pass

# 判断列表是否为空
if not lst:       # Pythonic 方式
    print("空列表")
# 不要写 if len(lst) == 0:

# 链式比较
if 0 <= x <= 100:   # Python 特色!
    print("有效范围")
```

---

## 九、循环

### 9.1 for 循环

```python
# 遍历列表
for item in [1, 2, 3]:
    print(item)

# range() 生成数字序列
range(5)        # 0, 1, 2, 3, 4
range(2, 5)     # 2, 3, 4
range(0, 10, 2) # 0, 2, 4, 6, 8
range(5, 0, -1) # 5, 4, 3, 2, 1

# enumerate() 同时获取索引和值（常用!）
fruits = ["苹果", "香蕉", "橘子"]
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
# 0: 苹果
# 1: 香蕉
# 2: 橘子

# zip() 并行遍历多个序列
names = ["小明", "小红", "小刚"]
scores = [90, 85, 95]
for name, score in zip(names, scores):
    print(f"{name}: {score}分")
```

### 9.2 while 循环

```python
count = 0
while count < 5:
    print(count)
    count += 1

# 死循环 + break
while True:
    user_input = input("输入 q 退出: ")
    if user_input == "q":
        break
```

### 9.3 break / continue / else

```python
# break —— 立即退出循环
for i in range(10):
    if i == 5:
        break       # 跳出，不再执行后面的迭代
    print(i)        # 打印 0 1 2 3 4

# continue —— 跳过本次，继续下一次
for i in range(10):
    if i % 2 == 0:
        continue    # 跳过偶数
    print(i)        # 打印 1 3 5 7 9

# for...else —— 循环正常结束(没有break)时执行 else
for i in range(10):
    if i == 99:
        break
else:
    print("循环正常结束，没有触发break")  # 会打印
```

---

## 十、函数

### 10.1 定义与调用

```python
# 基本定义
def greet(name):
    """向某人打招呼（这是文档字符串）"""
    return f"你好，{name}!"

# 调用
print(greet("小明"))  # "你好，小明!"

# 无返回值的函数（默认返回 None）
def say_hello():
    print("Hello!")
```

### 10.2 参数类型（重点!）

```python
# 1. 位置参数
def add(a, b):
    return a + b
add(1, 2)  # 3

# 2. 默认参数（必须放在后面）
def greet(name, greeting="你好"):
    return f"{greeting}，{name}!"
greet("小明")           # "你好，小明!"
greet("小明", "早上好")  # "早上好，小明!"

# ⚠️ 默认参数陷阱：不要用可变对象做默认值!
# 错误示范：
def bad(lst=[]):    # 所有调用共享同一个列表!
    lst.append(1)
    return lst
# 正确做法：
def good(lst=None):
    if lst is None:
        lst = []
    lst.append(1)
    return lst

# 3. 关键字参数
def info(name, age, city):
    print(f"{name}, {age}岁, {city}")
info(age=18, city="北京", name="小明")  # 顺序随意

# 4. *args —— 接收任意数量的位置参数（打包为元组）
def total(*args):
    return sum(args)
total(1, 2, 3, 4)  # 10

# 5. **kwargs —— 接收任意数量的关键字参数（打包为字典）
def show(**kwargs):
    for key, value in kwargs.items():
        print(f"{key} = {value}")
show(name="小明", age=18)

# 参数顺序规则：
# def func(位置参数, *args, 默认参数, **kwargs):
```

### 10.3 返回值

```python
# 返回多个值（本质是返回元组）
def min_max(lst):
    return min(lst), max(lst)

lo, hi = min_max([3, 1, 4, 1, 5])
# lo = 1, hi = 5
```

### 10.4 匿名函数 lambda

```python
# lambda 参数: 表达式
square = lambda x: x ** 2
square(5)  # 25

# 常用于排序
students = [("小明", 90), ("小红", 85), ("小刚", 95)]
students.sort(key=lambda s: s[1])  # 按分数排序
# [('小红', 85), ('小明', 90), ('小刚', 95)]
```

---

## 十一、常用内置函数

```python
# 数学
abs(-5)         # 5
max(1, 2, 3)    # 3
min(1, 2, 3)    # 1
sum([1, 2, 3])  # 6
round(3.14159, 2)  # 3.14
pow(2, 10)      # 1024
divmod(17, 5)   # (3, 2)  商和余数

# 类型转换
int(), float(), str(), bool(), list(), tuple(), dict(), set()

# 序列操作
len([1, 2, 3])          # 3
sorted([3, 1, 2])       # [1, 2, 3]（返回新列表）
reversed([1, 2, 3])     # 迭代器（需要 list() 转换）
enumerate(["a", "b"])   # [(0, 'a'), (1, 'b')]
zip([1, 2], [3, 4])     # [(1, 3), (2, 4)]

# 判断
all([True, True, False])   # False（全部为真才True）
any([True, False, False])  # True（有一个真就True）
isinstance(123, int)       # True

# 高阶函数
map(str, [1, 2, 3])           # ['1', '2', '3']
filter(lambda x: x > 2, [1, 2, 3, 4])  # [3, 4]

# 输入输出
print("hello", end="")    # 不换行
input("请输入: ")          # 接收用户输入（返回字符串）
```

---

## 十二、文件操作

```python
# 写文件
with open("test.txt", "w", encoding="utf-8") as f:
    f.write("第一行\n")
    f.write("第二行\n")

# 读文件
with open("test.txt", "r", encoding="utf-8") as f:
    content = f.read()        # 读取全部内容
    # 或
    lines = f.readlines()     # 读取所有行（列表）
    # 或
    for line in f:            # 逐行读取（内存友好）
        print(line.strip())

# 追加
with open("test.txt", "a", encoding="utf-8") as f:
    f.write("追加的内容\n")

# 模式总结:
# "r"  只读（默认）
# "w"  写入（覆盖）
# "a"  追加
# "rb" 二进制读
# "wb" 二进制写

# ⚠️ 永远使用 with 语句! 自动关闭文件，不会忘记
```

---

## 十三、异常处理

```python
# 基本结构
try:
    result = 10 / 0
except ZeroDivisionError:
    print("不能除以零!")
except (TypeError, ValueError) as e:
    print(f"类型或值错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
else:
    print("没有异常时执行")
finally:
    print("无论如何都会执行")

# 主动抛出异常
def set_age(age):
    if age < 0:
        raise ValueError("年龄不能为负数!")
    return age

# 常见异常类型：
# TypeError      —— 类型错误
# ValueError     —— 值错误
# IndexError     —— 索引越界
# KeyError       —— 字典键不存在
# FileNotFoundError —— 文件不存在
# ZeroDivisionError —— 除以零
# AttributeError —— 属性不存在
# ImportError    —— 导入错误
# NameError      —— 变量名未定义
```

---

## 十四、模块与导入

```python
# 导入整个模块
import math
math.sqrt(16)    # 4.0
math.pi          # 3.14159...

# 导入特定函数
from math import sqrt, pi
sqrt(16)         # 4.0

# 导入并重命名
import numpy as np

# 导入所有（不推荐!）
from math import *

# 自定义模块
# 文件: my_utils.py
def add(a, b):
    return a + b

# 另一个文件中使用:
from my_utils import add
```

---

## 十五、常见运算符速查

```python
# 算术运算符
+   -   *   /     # 加 减 乘 除
//                 # 整除 (7 // 2 = 3)
%                  # 取余 (7 % 2 = 1)
**                 # 幂   (2 ** 3 = 8)

# 比较运算符
==  !=  >  <  >=  <=

# 逻辑运算符
and   or   not
# 短路特性:
# x and y → x为假返回x，否则返回y
# x or y  → x为真返回x，否则返回y
0 and "hello"   # 0
1 and "hello"   # "hello"
0 or "hello"    # "hello"
1 or "hello"    # 1

# 成员运算符
in     not in
"a" in "abc"        # True
1 in [1, 2, 3]      # True
"key" in {"key": 1} # True（检查键）

# 身份运算符
is     is not
# 判断是否是同一个对象（不是值相等）
```

---

## 十六、必背口诀与技巧

### Python 之禅（import this）

```
优美胜于丑陋
明了胜于晦涩
简洁胜于复杂
扁平胜于嵌套
可读性很重要
```

### 常见 Pythonic 写法

```python
# 1. 交换变量
a, b = b, a

# 2. 判断空
if not lst:    # 而不是 if len(lst) == 0

# 3. 多值判断
if x in (1, 2, 3):   # 而不是 if x == 1 or x == 2 or x == 3

# 4. 字典取值
d.get("key", default)  # 而不是 if "key" in d: ... else: ...

# 5. 连接字符串
result = "".join(str_list)  # 而不是 循环 +=

# 6. 遍历带索引
for i, item in enumerate(lst):  # 而不是 range(len(lst))

# 7. 列表推导式
[x*2 for x in range(10)]  # 而不是 循环 append

# 8. 解包
first, *middle, last = [1, 2, 3, 4, 5]
# first=1, middle=[2,3,4], last=5

# 9. 用 with 管理资源
with open("file.txt") as f:  # 而不是手动 open/close

# 10. 三元表达式
value = a if condition else b
```

---

## 速记卡片

| 类型 | 有序 | 可变 | 重复 | 符号 |
|------|------|------|------|------|
| list | ✅ | ✅ | ✅ | `[]` |
| tuple | ✅ | ❌ | ✅ | `()` |
| dict | ✅(3.7+) | ✅ | 键不可重复 | `{}` |
| set | ❌ | ✅ | ❌ | `{}` |
| str | ✅ | ❌ | ✅ | `""` |

---

> **记住：每天看一遍，不懂就敲代码验证，一周后这些内容会变成你的直觉。**

# Python 速记卡片

> 每张卡片一个知识点，5 秒看完，适合碎片时间刷。
> 用法：随机翻开一张，能说出答案就过，说不出就标记复习。

---

## 使用方法

```
1. 看「问题」→ 心里想答案 → 翻看「答案」
2. 答对了 → 跳过
3. 答错了 → 标记 ⭐，明天再看
4. 每天刷 10-20 张，重复直到全会
```

---

## 一、数据类型速记

### 卡片 001：哪些值是 False？
```
❓ bool() 为 False 的值有哪些？

✅ 0, 0.0, "", [], {}, (), set(), None, False
   口诀：零空无 → 全是假
```

### 卡片 002：可变 vs 不可变
```
❓ 哪些类型可变？哪些不可变？

✅ 可变:   list, dict, set
   不可变: int, float, str, tuple, frozenset
   口诀：列字集能变，数串元不变
```

### 卡片 003：容器特征
```
❓ 有序+可变+可重复 是什么类型？

✅ list
   记忆表：
   list  → 有序 可变 可重复
   tuple → 有序 不可变 可重复
   dict  → 有序(3.7+) 可变 键唯一
   set   → 无序 可变 不重复
```

### 卡片 004：is 和 == 的区别
```
❓ a == b 和 a is b 有什么区别？

✅ ==  比较「值」是否相等
   is  比较「是否同一个对象」（内存地址）
   记住：None 用 is，其他用 ==
```

### 卡片 005：int 的特殊性
```
❓ True + True = ?    bool([0]) = ?

✅ True + True = 2    （bool 是 int 的子类）
   bool([0]) = True   （非空列表就是 True）
```

---

## 二、字符串速记

### 卡片 006：切片规则
```
❓ s[start:stop:step] 包含 start 还是 stop？

✅ 包含 start，不包含 stop
   口诀：左闭右开
   s[::-1] → 反转
```

### 卡片 007：去空白三兄弟
```
❓ strip / lstrip / rstrip 分别去哪边？

✅ strip  → 两边都去
   lstrip → 去左边 (left)
   rstrip → 去右边 (right)
```

### 卡片 008：find vs index
```
❓ find() 和 index() 找不到时有什么区别？

✅ find()  → 返回 -1（安全）
   index() → 抛出 ValueError（会崩）
   结论：优先用 find()
```

### 卡片 009：split 和 join
```
❓ "a,b,c".split(",") 和 ",".join(["a","b","c"]) 结果？

✅ split → ['a', 'b', 'c']  （字符串拆成列表）
   join  → "a,b,c"          （列表合成字符串）
   口诀：split 拆，join 合
```

### 卡片 010：f-string 格式化
```
❓ 保留 2 位小数怎么写？千位分隔怎么写？

✅ f"{3.14159:.2f}"   → "3.14"
   f"{1000000:,}"     → "1,000,000"
   f"{42:08d}"        → "00000042"
```

---

## 三、列表速记

### 卡片 011：append vs extend
```
❓ [1,2].append([3,4]) 和 [1,2].extend([3,4]) 结果？

✅ append → [1, 2, [3, 4]]   （整体加入）
   extend → [1, 2, 3, 4]     （展开加入）
   口诀：append 加一个，extend 加一批
```

### 卡片 012：pop vs remove
```
❓ pop() 和 remove() 有什么区别？

✅ pop(index)  → 按索引删，返回被删的值
   remove(value) → 按值删，不返回
   del lst[i]  → 按索引删，不返回
```

### 卡片 013：sort vs sorted
```
❓ sort() 和 sorted() 有什么区别？

✅ lst.sort()   → 原地排序，返回 None，修改原列表
   sorted(lst)  → 返回新列表，原列表不变
   口诀：带 ed 的不改原来的
```

### 卡片 014：列表推导式模板
```
❓ 列表推导式的两种形式？

✅ [表达式 for x in 序列 if 条件]      ← 过滤
   [A if 条件 else B for x in 序列]    ← 转换
   注意 if 位置不同！
```

### 卡片 015：列表复制陷阱
```
❓ b = a 和 b = a[:] 有什么区别？

✅ b = a    → 同一个对象，改 b 就是改 a
   b = a[:] → 浅拷贝，b 是新列表（但内部元素还是共享）
   完全独立 → import copy; b = copy.deepcopy(a)
```

---

## 四、字典速记

### 卡片 016：取值安全
```
❓ d["key"] 和 d.get("key") 有什么区别？

✅ d["key"]     → 键不存在时 KeyError（崩溃）
   d.get("key") → 键不存在时返回 None（安全）
   d.get("key", 默认值) → 更好
```

### 卡片 017：字典遍历
```
❓ 遍历字典键值对怎么写？

✅ for key, value in d.items():
       print(key, value)
   
   d.keys()   → 所有键
   d.values() → 所有值
   d.items()  → 所有键值对
```

### 卡片 018：删除键的方法
```
❓ 删除字典中的键有几种方式？

✅ d.pop("key")       → 删除并返回值，键不存在可设默认值
   del d["key"]       → 删除，键不存在会报错
   d.pop("key", None) → 最安全
```

---

## 五、函数速记

### 卡片 019：参数顺序
```
❓ 函数参数的正确顺序是什么？

✅ def func(位置参数, *args, 默认参数, **kwargs)
   口诀：位 星 默 双星
```

### 卡片 020：默认参数陷阱
```
❓ def f(lst=[]): 有什么问题？

✅ 可变默认参数会被所有调用共享！
   正确写法:
   def f(lst=None):
       if lst is None:
           lst = []
```

### 卡片 021：*args 和 **kwargs
```
❓ *args 和 **kwargs 分别收到什么？

✅ *args   → 元组 tuple  (1, 2, 3)
   **kwargs → 字典 dict   {"a": 1, "b": 2}
   口诀：一星元组，双星字典
```

### 卡片 022：lambda
```
❓ lambda 怎么写？常用在哪？

✅ lambda 参数: 表达式
   常用于 sort/sorted 的 key:
   lst.sort(key=lambda x: x[1])
```

---

## 六、控制流速记

### 卡片 023：三元表达式
```
❓ Python 的三元表达式格式？

✅ 值1 if 条件 else 值2
   例: "成年" if age >= 18 else "未成年"
```

### 卡片 024：for...else
```
❓ for 循环的 else 什么时候执行？

✅ 循环正常结束（没有 break）时执行 else
   有 break 退出 → else 不执行
```

### 卡片 025：range 三种用法
```
❓ range 的三种形式？

✅ range(5)        → 0,1,2,3,4
   range(2, 5)     → 2,3,4
   range(0, 10, 2) → 0,2,4,6,8
   range(5, 0, -1) → 5,4,3,2,1
```

### 卡片 026：enumerate 和 zip
```
❓ 怎么同时拿到索引和值？怎么并行遍历两个列表？

✅ for i, x in enumerate(lst):     ← 索引+值
   for a, b in zip(lst1, lst2):    ← 并行遍历
```

---

## 七、面向对象速记

### 卡片 027：类的基本结构
```
❓ 定义一个类的最小结构？

✅ class Dog:
       def __init__(self, name):
           self.name = name
       def bark(self):
           return f"{self.name}: 汪!"
```

### 卡片 028：self 是什么
```
❓ self 是什么？需要手动传吗？

✅ self = 当前实例本身
   Python 自动传入，调用时不用写
   dog.bark() 实际上是 Dog.bark(dog)
```

### 卡片 029：三种方法
```
❓ 实例方法、类方法、静态方法的区别？

✅ def method(self):        → 操作实例
   @classmethod
   def method(cls):         → 操作类
   @staticmethod
   def method():            → 和类无关的工具函数
```

### 卡片 030：继承
```
❓ 继承怎么写？怎么调用父类？

✅ class Cat(Animal):       ← 继承
       def __init__(self, name):
           super().__init__(name)  ← 调用父类
```

---

## 八、高频易错速记

### 卡片 031：可变对象做函数参数
```
❓ 下面代码输出什么？
   def add(lst):
       lst.append(1)
   a = [0]
   add(a)
   print(a)

✅ [0, 1]  ← 列表是可变对象，函数内修改会影响外部！
```

### 卡片 032：字符串不可变
```
❓ s = "hello"; s[0] = "H" 会怎样？

✅ TypeError! 字符串不可变
   正确做法: s = "H" + s[1:]  或  s.replace("h", "H")
```

### 卡片 033：浅拷贝陷阱
```
❓ a = [[1,2],[3,4]]; b = a[:]; b[0].append(9)
   a 变了吗？

✅ a = [[1,2,9],[3,4]]  ← 变了!
   浅拷贝只复制外层，内层还是共享
   要完全独立: copy.deepcopy(a)
```

### 卡片 034：== vs is
```
❓ a = [1,2]; b = [1,2]
   a == b?   a is b?

✅ a == b → True  （值相同）
   a is b → False （不是同一个对象）
```

### 卡片 035：全局变量修改
```
❓ 函数内怎么修改全局变量？

✅ x = 10
   def change():
       global x    ← 必须声明 global
       x = 20
```

---

## 九、Pythonic 写法速记

### 卡片 036：判断空容器
```
❓ 判断列表为空的 Pythonic 写法？

✅ if not lst:        ← 正确
   if len(lst) == 0:  ← 不够 Pythonic
```

### 卡片 037：多值判断
```
❓ 判断 x 是 1 或 2 或 3 的 Pythonic 写法？

✅ if x in (1, 2, 3):            ← 正确
   if x == 1 or x == 2 or x == 3:  ← 啰嗦
```

### 卡片 038：交换变量
```
❓ 交换 a 和 b 的值？

✅ a, b = b, a      ← 一行搞定
   不需要临时变量！
```

### 卡片 039：字符串拼接
```
❓ 大量字符串拼接用什么？

✅ "".join(str_list)     ← 高效
   循环 += 拼接          ← 低效（每次创建新字符串）
```

### 卡片 040：with 管理资源
```
❓ 打开文件为什么用 with？

✅ with open("f.txt") as f:
       data = f.read()
   # 自动关闭，即使出异常也不会忘
   # 永远不要手动 f.close()
```

---

## 十、内置函数速记

### 卡片 041：map 和 filter
```
❓ map 和 filter 分别做什么？

✅ map(func, 序列)    → 对每个元素执行 func
   filter(func, 序列) → 保留 func 返回 True 的元素
   
   list(map(str, [1,2,3]))         → ['1','2','3']
   list(filter(lambda x: x>2, [1,2,3,4])) → [3,4]
```

### 卡片 042：all 和 any
```
❓ all 和 any 的规则？

✅ all([...]) → 全部为 True 才返回 True
   any([...]) → 有一个 True 就返回 True
   口诀：all 全真，any 有真
```

### 卡片 043：zip 的行为
```
❓ zip([1,2,3], [4,5]) 结果？

✅ [(1,4), (2,5)]  ← 以短的为准，多余的丢弃
   想保留全部: itertools.zip_longest
```

### 卡片 044：enumerate 起始值
```
❓ enumerate 怎么从 1 开始？

✅ for i, x in enumerate(lst, start=1):
       print(i, x)   # 1, 2, 3...
```

### 卡片 045：divmod
```
❓ 同时得到商和余数用什么？

✅ divmod(17, 5)  → (3, 2)
   等价于: (17 // 5, 17 % 5)
```

---

## 十一、文件与异常速记

### 卡片 046：文件模式
```
❓ "r" "w" "a" 的区别？

✅ "r" → 只读（文件不存在报错）
   "w" → 写入（覆盖原内容，文件不存在则创建）
   "a" → 追加（不覆盖，在末尾写入）
   加 "b" → 二进制模式 ("rb", "wb")
```

### 卡片 047：异常处理结构
```
❓ try 的完整结构？各部分何时执行？

✅ try:        → 尝试执行
   except:     → 出错时执行
   else:       → 没出错时执行
   finally:    → 无论如何都执行
```

### 卡片 048：常见异常
```
❓ 快速对应：类型错、键不存在、索引越界

✅ TypeError       → 类型错误
   KeyError        → 字典键不存在
   IndexError      → 索引越界
   ValueError      → 值不对
   AttributeError  → 属性不存在
   NameError       → 变量没定义
```

---

## 十二、装饰器与生成器速记

### 卡片 049：装饰器本质
```
❓ @decorator 等价于什么？

✅ @decorator
   def func():
       pass

   等价于: func = decorator(func)
   本质：接收函数，返回新函数
```

### 卡片 050：yield vs return
```
❓ yield 和 return 的区别？

✅ return → 函数结束，返回值，下次从头开始
   yield  → 暂停，返回值，下次从暂停处继续
   有 yield 的函数 → 生成器函数
   调用后返回 → 生成器对象（用 next() 驱动）
```

---

## 复习打卡表

| 日期 | 刷了几张 | 错了哪些 | 签名 |
|------|----------|----------|------|
|      |          |          |      |
|      |          |          |      |
|      |          |          |      |
|      |          |          |      |
|      |          |          |      |

---

> **记忆诀窍：不求一次记住，求重复次数够多。每天 5 分钟，连续 7 天，比一次看 1 小时强 10 倍。**

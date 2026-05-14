# 20. AST 与字节码深入

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐⭐ (高级) |
> | **前置知识** | [10 GIL 与 CPython](10_GIL与CPython执行机制.md)、[01 函数](01_函数篇.md) |
> | **学习目标** | 理解从源码到执行的完整链路、能用 ast 模块改造代码、读懂字节码、知道 PEP 657 改进 |
> | **CPython 版本** | 3.12+（含自适应解释器优化） |
> | **规范 vs 实现** | AST 节点定义（ast 模块）相对稳定；字节码指令是 **CPython 实现细节**，每个版本都可能变 |

---

## 20.0 知识地图

```
源码 .py
   │  词法分析 (tokenize)
   ▼
Tokens
   │  语法分析 (PEG parser, 3.9+)
   ▼
AST (抽象语法树)        ← ast 模块可读写
   │  编译
   ▼
Bytecode (字节码)        ← dis 模块可查看
   │  优化（3.11+ 帧改造、3.12 自适应）
   ▼
CPython 虚拟机执行       ← ceval.c
```

---

## 20.1 完整链路示例

```python
import ast, dis, tokenize, io

source = "x = 1 + 2"

# 1. 词法分析
tokens = list(tokenize.tokenize(io.BytesIO(source.encode()).readline))
for t in tokens:
    print(t)
# TokenInfo(type=NAME, string='x', ...)
# TokenInfo(type=OP, string='=', ...)
# TokenInfo(type=NUMBER, string='1', ...)
# TokenInfo(type=OP, string='+', ...)
# TokenInfo(type=NUMBER, string='2', ...)

# 2. 语法分析（生成 AST）
tree = ast.parse(source)
print(ast.dump(tree, indent=2))
# Module(body=[
#   Assign(targets=[Name(id='x', ...)], value=BinOp(left=Constant(value=1),
#                                                   op=Add(),
#                                                   right=Constant(value=2)))
# ])

# 3. 编译为字节码
code = compile(tree, "<string>", "exec")

# 4. 反汇编查看字节码
dis.dis(code)
```

---

## 20.2 AST 模块

### 20.2.1 解析

```python
import ast

tree = ast.parse("x = a + b * 2")
print(ast.dump(tree))
```

### 20.2.2 常见节点

| 节点 | 含义 |
|------|------|
| `Module` | 整个文件 |
| `FunctionDef` / `AsyncFunctionDef` | 函数定义 |
| `ClassDef` | 类定义 |
| `Assign` / `AugAssign` | `=` / `+=` |
| `Name` | 变量名 |
| `Constant` | 字面量（数字、字符串） |
| `BinOp` / `UnaryOp` / `BoolOp` | 二元/一元/布尔运算 |
| `Call` | 函数调用 |
| `If` / `For` / `While` / `Try` | 控制流 |
| `Return` / `Raise` / `Yield` | 返回/抛错/yield |
| `Import` / `ImportFrom` | 导入 |

### 20.2.3 遍历：NodeVisitor

```python
class FunctionCollector(ast.NodeVisitor):
    def __init__(self):
        self.funcs = []
    
    def visit_FunctionDef(self, node):
        self.funcs.append(node.name)
        self.generic_visit(node)        # 递归子节点

tree = ast.parse(open("module.py").read())
collector = FunctionCollector()
collector.visit(tree)
print(collector.funcs)
```

### 20.2.4 改造：NodeTransformer

```python
class AddDocstring(ast.NodeTransformer):
    """给所有函数自动加 docstring"""
    def visit_FunctionDef(self, node):
        if not (node.body and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
            doc = ast.Expr(value=ast.Constant(value=f"自动生成: {node.name}"))
            node.body.insert(0, doc)
        return self.generic_visit(node)

tree = ast.parse(source)
new_tree = AddDocstring().visit(tree)
ast.fix_missing_locations(new_tree)         # 补行号
exec(compile(new_tree, "<gen>", "exec"))
```

### 20.2.5 实际应用

- **代码审计**：扫描所有 `eval`/`exec`/SQL 字符串拼接
- **代码格式化**：black、autopep8 基于 AST
- **静态分析**：pylint、mypy
- **DSL 实现**：sympy、pytest 的 assert 重写
- **代码迁移**：2to3、自动重构

### 20.2.6 ast.unparse（3.9+）

```python
tree = ast.parse("x = 1 + 2")
print(ast.unparse(tree))   # 'x = 1 + 2'
```

AST → 源码，便于代码生成。

---

## 20.3 字节码

### 20.3.1 dis 模块基础

```python
import dis

def f(x):
    return x * 2 + 1

dis.dis(f)
```

```
  2           0 RESUME                   0

  3           2 LOAD_FAST                0 (x)
              4 LOAD_CONST               1 (2)
              6 BINARY_OP                5 (*)
             10 LOAD_CONST               2 (1)
             12 BINARY_OP                0 (+)
             16 RETURN_VALUE
```

### 20.3.2 ⚠️ 字节码不是 Python 规范的一部分

> **CPython 实现细节**：每个版本字节码指令都可能变。
>
> - 3.11：引入 specializing adaptive interpreter (PEP 659)
> - 3.12：进一步优化、加速 11%
> - 3.13：no-GIL 实验、JIT 引入

→ 不要在生产代码里依赖具体字节码。

### 20.3.3 code 对象的属性

```python
def f(x, y=10):
    z = x + y
    return z

c = f.__code__

c.co_name          # 'f'
c.co_argcount      # 2
c.co_varnames      # ('x', 'y', 'z')      局部变量名
c.co_consts        # (None, 10, ...)       常量池
c.co_names         # ()                   全局/属性名
c.co_freevars      # ()                   闭包变量
c.co_cellvars      # ()                   被内层引用的变量
c.co_code          # b'\x97\x00...'      字节码
c.co_lnotab        # 行号表（旧）
c.co_lines()       # 行号迭代器（PEP 626，3.10+）
c.co_positions()   # 精确位置（PEP 657，3.11+）
```

### 20.3.4 PEP 657：精确错误位置（3.11+）

```python
# 旧版报错
TypeError: ...
  at line 5

# 新版报错（3.11+）
TypeError: ...
  at line 5
    result = data["users"][0].name + 10
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

精确指出表达式中哪部分出错。靠的就是 `co_positions()` 提供的字符级位置信息。

### 20.3.5 自适应解释器（PEP 659，3.11+）

🔬 **CPython 优化**：

```
LOAD_ATTR  →  运行几次后 → LOAD_ATTR_INSTANCE_VALUE   (specialized)
                                                       (10x 更快)
```

热点指令运行时根据实际类型替换为专用版本。**用户无感知**，但意味着字节码不再是静态的。

---

## 20.4 编译三种模式

```python
compile(source, filename, mode)
# mode: 'exec' / 'eval' / 'single'
```

| mode | 用途 |
|------|------|
| `exec` | 整个模块/多语句 |
| `eval` | 单个表达式（返回值） |
| `single` | 交互式单语句 |

```python
expr = compile("a + b", "<>", "eval")
print(eval(expr, {"a": 1, "b": 2}))   # 3

mod = compile("x = 1\ny = 2", "<>", "exec")
ns = {}
exec(mod, ns)
print(ns["x"], ns["y"])
```

---

## 20.5 实战案例

### 案例 1：简易公式求值器（安全 eval）

```python
import ast

ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
           ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub)

def safe_eval(expr):
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise ValueError(f"禁止的语法: {type(node).__name__}")
    return eval(compile(tree, "<safe>", "eval"))

print(safe_eval("1 + 2 * 3"))    # 7
# print(safe_eval("__import__('os').system('ls')"))  # ❌ 禁止
```

### 案例 2：自动给函数加日志

```python
class LogAdder(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        log_call = ast.parse(
            f'print("calling {node.name}")', mode="exec"
        ).body[0]
        node.body.insert(0, log_call)
        return self.generic_visit(node)

source = """
def hello(name):
    return f"Hi {name}"
"""

tree = ast.parse(source)
new = LogAdder().visit(tree)
ast.fix_missing_locations(new)
exec(compile(new, "<gen>", "exec"))
hello("Alice")
# 输出:
# calling hello
```

### 案例 3：分析代码复杂度

```python
class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity = 1
    
    def visit_If(self, node):  self.complexity += 1; self.generic_visit(node)
    def visit_For(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_While(self, node): self.complexity += 1; self.generic_visit(node)
    def visit_BoolOp(self, node):
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

def cyclomatic_complexity(func):
    tree = ast.parse(inspect.getsource(func))
    v = ComplexityVisitor()
    v.visit(tree)
    return v.complexity
```

---

## 20.6 常见误区

### ❌ 误区 1：以为 .pyc 是机器码

`.pyc` 是字节码，仍然由解释器执行，**不是机器码**。机器码需要 JIT（PyPy / 3.13+ 实验性 JIT）。

### ❌ 误区 2：依赖具体字节码

```python
# 错的：假设字节码长度恒定
assert len(f.__code__.co_code) == 20
```

3.12 优化可能改变长度。

### ❌ 误区 3：滥用 exec/eval

```python
# ❌ SQL 注入式风险
exec(f"x = {user_input}")
```

只在沙箱场景使用，且必须用 AST 白名单。

---

## 20.7 面试常问

### Q1：Python 是编译型还是解释型？

**答**：两者都有。源码 → 字节码（编译） → 虚拟机解释执行。字节码缓存在 `.pyc`。

### Q2：AST 在哪些工具里被用？

**答**：black、ruff、mypy、pylint、pytest（assert 重写）、Jupyter（autoreload）、Django（template 编译）等。

### Q3：CPython 3.11/3.12 加速的原理？

**答**：
- PEP 659：自适应专用解释器，运行时根据实际类型把通用指令换成专用指令
- 帧栈优化：减少 frame 对象分配
- 启动加速：MARSHAL 优化、import 路径优化
- 整体 3.12 比 3.10 快 25-60%

### Q4：什么时候需要直接操作 AST？

**答**：写 linter、formatter、转换器、DSL、代码生成、安全沙箱、profiling 工具时。

---

## 20.8 练习题

### 练习 20.1（基础）

写函数 `count_calls(source)`：用 AST 统计源码中所有函数调用次数。

<details><summary>答案</summary>

```python
import ast
from collections import Counter

def count_calls(source):
    tree = ast.parse(source)
    c = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            c[node.func.id] += 1
    return c
```
</details>

### 练习 20.2（中级）

写一个简易的"自动 print 调试"装饰器：在函数每条语句前后加 print。

<details><summary>答案</summary>

```python
import ast, inspect

class StmtPrinter(ast.NodeTransformer):
    def visit_FunctionDef(self, node):
        new_body = []
        for stmt in node.body:
            new_body.append(ast.Expr(value=ast.Constant(value=f"[trace] {ast.unparse(stmt)}")))
            new_body.append(stmt)
        node.body = new_body
        return self.generic_visit(node)

# 实际用还需要把 Constant 改成 print(...)
```
</details>

---

**上一章：[19 Redis 与消息队列](19_Redis与消息队列.md)** | **下一章：[21 import 源码机制](21_import源码机制.md)**

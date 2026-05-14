# 21. import 源码机制

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐ (高级) |
> | **前置知识** | [06 模块与高级特性](06_模块与高级特性篇.md)、[08 LEGB](08_作用域与LEGB深入.md) |
> | **学习目标** | 理解 import 完整流程、能写自定义 finder/loader、解决循环导入、看懂 sys.path 机制 |
> | **CPython 版本** | 3.12+ |
> | **规范 vs 实现** | importlib 接口（PEP 451 ModuleSpec）是规范；__pycache__、字节码格式是 CPython 实现 |

---

## 21.0 知识地图

```
import foo.bar
   │
   ▼
sys.modules["foo.bar"] 已缓存？───── 是 → 直接返回
   │ 否
   ▼
遍历 sys.meta_path 中的 Finder
   │
   ▼
Finder.find_spec("foo.bar")  → ModuleSpec
   │
   ▼
ModuleSpec.loader.create_module() → 模块对象
   │
   ▼
ModuleSpec.loader.exec_module(module) → 执行模块代码
   │
   ▼
sys.modules["foo.bar"] = module
   │
   ▼
返回模块
```

---

## 21.1 import 的完整流程

### 21.1.1 入口：__import__

```python
# import foo.bar
# 等价于：
foo_bar = __import__("foo.bar", fromlist=["bar"])
```

`__import__` 是 builtin 函数，源码在 CPython 的 `Lib/importlib/_bootstrap.py`。

### 21.1.2 三层缓存

```python
import sys

print(sys.modules.keys())     # ① 已加载模块缓存（最快）
print(sys.path)               # ② 模块搜索路径
print(sys.path_importer_cache) # ③ 路径 → finder 的缓存
```

### 21.1.3 完整流程（简化）

```python
def import_module(name):
    # 1. 查 sys.modules
    if name in sys.modules:
        return sys.modules[name]
    
    # 2. 遍历 meta_path
    for finder in sys.meta_path:
        spec = finder.find_spec(name, ...)
        if spec is not None:
            break
    else:
        raise ModuleNotFoundError(name)
    
    # 3. 创建模块
    module = spec.loader.create_module(spec)
    if module is None:
        module = types.ModuleType(spec.name)
    
    # 4. 注册（必须在 exec 之前，处理循环导入）
    sys.modules[name] = module
    
    # 5. 执行模块代码
    spec.loader.exec_module(module)
    
    return module
```

---

## 21.2 sys.meta_path：finder 链

```python
import sys
print(sys.meta_path)
# [
#   <class '_frozen_importlib.BuiltinImporter'>,    # 内置模块
#   <class '_frozen_importlib.FrozenImporter'>,     # 冻结模块（importlib 自身）
#   <class '_frozen_importlib_external.PathFinder'>, # 文件系统模块
# ]
```

### Finder 协议（PEP 451）

```python
class MyFinder:
    @classmethod
    def find_spec(cls, name, path, target=None):
        """返回 ModuleSpec 或 None"""
        if name == "magic":
            return importlib.machinery.ModuleSpec("magic", MyLoader())
        return None

sys.meta_path.insert(0, MyFinder)
```

---

## 21.3 自定义 Loader 实战

### 案例：从字符串加载模块

```python
import sys, types
import importlib.machinery, importlib.util

class StringLoader:
    def __init__(self, source):
        self.source = source
    
    def create_module(self, spec):
        return None  # 用默认
    
    def exec_module(self, module):
        exec(self.source, module.__dict__)

class StringFinder:
    modules = {}  # name -> source
    
    @classmethod
    def add(cls, name, source):
        cls.modules[name] = source
    
    @classmethod
    def find_spec(cls, name, path, target=None):
        if name in cls.modules:
            return importlib.util.spec_from_loader(
                name, StringLoader(cls.modules[name])
            )
        return None

sys.meta_path.insert(0, StringFinder)

# 注册一个虚拟模块
StringFinder.add("greeting", "def hello(): print('hi from memory')")

import greeting
greeting.hello()         # hi from memory
```

### 实际应用

- `__pyx_loader`：Cython
- `pyimod_archiver`：PyInstaller 打包
- IPython 的 magic command
- 远程模块加载（极少见，安全风险）

---

## 21.4 sys.path：模块搜索路径

```python
import sys
print(sys.path)
# ['',                            # 当前脚本目录
#  '/usr/lib/python3.12',
#  '/usr/lib/python3.12/lib-dynload',
#  '/usr/lib/python3.12/site-packages',
#  ...]
```

### 21.4.1 sys.path 的来源

1. 脚本文件所在目录（`""`）
2. `PYTHONPATH` 环境变量
3. 安装相关的默认路径
4. site-packages（通过 site.py 添加）

### 21.4.2 ⚠️ 与 src/ 布局的关系

```
project/
├── src/
│   └── mypkg/
│       └── __init__.py
└── tests/
    └── test_x.py
```

直接 `python tests/test_x.py` 时，`src/mypkg` 可能不在 sys.path。
解决方法：
- 用 `pip install -e .` 装到 site-packages
- 或 `pytest` 自动加 src 到 path（配 `conftest.py` / `pyproject.toml`）

---

## 21.5 包（package）的特殊处理

### 21.5.1 普通包

```
mypkg/
├── __init__.py     # 必须有（Python 2 强制；3 推荐）
├── module_a.py
└── sub/
    ├── __init__.py
    └── module_b.py
```

### 21.5.2 命名空间包（PEP 420，3.3+）

```
mypkg/                  # 没有 __init__.py
├── module_a.py
```

不同位置的同名命名空间包会**自动合并**：

```
path1/mypkg/a.py
path2/mypkg/b.py

# import mypkg.a 和 import mypkg.b 都能成功
# mypkg.__path__ 会含两个目录
```

### 21.5.3 __init__.py 的执行时机

```python
# mypkg/__init__.py
print("mypkg loaded")
from .module_a import ClassA
```

执行 `import mypkg.module_b` 时：
1. 先执行 `mypkg/__init__.py`（包初始化）
2. 再执行 `mypkg/module_b.py`

---

## 21.6 ★ 循环导入

### 问题示例

```python
# a.py
from b import b_func
def a_func():
    return b_func()

# b.py
from a import a_func
def b_func():
    return a_func()
```

`import a` 时：
1. 创建 a 模块对象，加入 sys.modules
2. 执行 a.py：`from b import b_func`
3. 创建 b 模块对象，加入 sys.modules
4. 执行 b.py：`from a import a_func`
5. a 在 sys.modules 中，但 a 模块还没执行完！`a_func` 还没定义
6. ❌ ImportError

### 解决方案

**方案 1：模块级 import（不要 from）**

```python
# a.py
import b
def a_func():
    return b.b_func()    # 调用时再访问

# b.py
import a
def b_func():
    return a.a_func()
```

✅ 因为只是引用模块对象，不需要立即取属性。

**方案 2：延迟 import**

```python
# a.py
def a_func():
    from b import b_func
    return b_func()
```

**方案 3：重构**

把共享代码抽到第三个模块，破除循环。**最推荐**。

---

## 21.7 __pycache__ 与字节码缓存

### 21.7.1 缓存机制

```
mypkg/
├── module_a.py
└── __pycache__/
    └── module_a.cpython-312.pyc
```

- 文件名含 Python 版本，避免冲突
- import 时若 .pyc 比 .py 新且魔数匹配，直接用 .pyc

### 21.7.2 .pyc 文件结构

```
[16 字节 header]
  - 4 字节魔数（版本标识）
  - 4 字节 flags（PEP 552）
  - 8 字节时间戳或源码 hash
[marshal 序列化的 code 对象]
```

### 21.7.3 hash-based vs timestamp-based（PEP 552）

3.7+ 默认时间戳，但可改为 hash：

```bash
python -m compileall --invalidation-mode checked-hash mypkg/
```

适合：
- 容器化部署（时间戳因构建被改动）
- 文件系统时间戳不可靠

---

## 21.8 importlib 实用 API

```python
import importlib

# 动态导入
m = importlib.import_module("os.path")

# 强制重新加载（开发期用）
importlib.reload(m)

# 检查模块是否存在但不加载
spec = importlib.util.find_spec("numpy")
if spec is not None:
    np = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(np)

# 资源访问（PEP 302/451）
from importlib.resources import files
config = files("mypkg").joinpath("config.json").read_text()
```

---

## 21.9 import 钩子（hook）

```python
import sys

class Tracer:
    @classmethod
    def find_spec(cls, name, path, target=None):
        print(f"importing {name}")
        return None       # 让后续 finder 继续

sys.meta_path.insert(0, Tracer)

import json    # 输出: importing json
```

实际应用：
- 测试覆盖率工具（coverage.py）
- 性能分析（PyInstrument）
- 加密 .pyc 解密

---

## 21.10 常见误区

### ❌ 误区 1：以为 from X import Y 比 import X 快

两种都执行整个 X 模块。`from X import Y` 只是把 Y 绑定到当前命名空间。

### ❌ 误区 2：以为重启进程才能 reload

```python
import importlib
importlib.reload(mymodule)
```

但注意：旧引用不会更新（已绑定到 `from mymodule import f` 的 f 还是旧的）。

### ❌ 误区 3：相对导入要 `..xxx` 总能工作

相对导入只能在**包内**。直接运行脚本时 `__name__ == "__main__"`，相对导入会失败。

```bash
# ❌ python mypkg/sub/module.py
# ✅ python -m mypkg.sub.module
```

---

## 21.11 面试常问

### Q1：sys.modules 的作用？

**答**：缓存已加载的模块，避免重复执行模块代码。同时是循环导入"半成品模块"的来源。

### Q2：finder 和 loader 的区别？

**答**：
- finder：查找模块在哪（返回 ModuleSpec）
- loader：加载并执行模块
- PEP 451 之前两者合一，之后分离，更灵活

### Q3：import 一个模块时实际发生了什么？

**答**：见 21.1.3 的完整流程。

### Q4：怎么解决循环导入？

**答**：
1. 用 `import x` 而非 `from x import y`
2. 把 import 移到函数内（延迟）
3. 重构：抽出共同依赖到第三方模块（最佳）

---

## 21.12 练习题

### 练习 21.1（基础）

观察 `sys.modules` 在 import 前后的变化。

<details><summary>答案</summary>

```python
import sys
before = set(sys.modules.keys())
import json
after = set(sys.modules.keys())
print(after - before)
# {'json', 'json.decoder', 'json.encoder', 'json.scanner', ...}
```
</details>

### 练习 21.2（高级）

实现一个 finder，让 `import http_<URL>` 自动从 URL 下载并执行 Python 代码（仅用于学习，**生产严禁**）。

<details><summary>答案要点</summary>

```python
class URLFinder:
    @classmethod
    def find_spec(cls, name, path, target=None):
        if name.startswith("http_"):
            url = "https://" + name[5:].replace("_", "/")
            return spec_from_loader(name, URLLoader(url))
        return None

class URLLoader:
    def __init__(self, url): self.url = url
    def create_module(self, spec): return None
    def exec_module(self, module):
        import urllib.request
        source = urllib.request.urlopen(self.url).read()
        exec(source, module.__dict__)

# ⚠️ 极度危险，仅作教学
```
</details>

---

**上一章：[20 AST 与字节码](20_AST与字节码深入.md)** | **下一章：[22 描述符与元类深入](22_描述符与元类深入.md)**

# 17. Web 框架深入：Flask 与 FastAPI

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐ (中高级) |
> | **前置知识** | [03 装饰器](03_装饰器篇.md)、[12 异步编程](12_异步编程深入.md)、[13 网络编程](13_网络编程.md)、[09 typing](09_类型系统与typing.md) |
> | **学习目标** | 理解 WSGI/ASGI 协议、能解释 Flask 路由原理、掌握 FastAPI 依赖注入与 Pydantic 验证机制、能从源码角度回答"装饰器如何注册路由"|
> | **CPython 版本** | 3.12+ |
> | **规范 vs 实现** | WSGI/ASGI 是 PEP 规范；Flask/FastAPI 是具体实现。🔬 标注的为框架内部实现细节 |

---

## 17.0 知识地图

```
HTTP 请求
   │
   ▼
WSGI/ASGI 服务器 (gunicorn / uvicorn)
   │  调用 application(environ, start_response)
   ▼
Web 框架 (Flask / FastAPI)
   ├── 路由匹配
   ├── 中间件链
   ├── 依赖注入 (FastAPI)
   ├── 数据验证 (FastAPI/Pydantic)
   └── 视图函数 → 返回 Response
```

**本章要回答**：
1. WSGI 和 ASGI 是什么？为什么需要标准协议？
2. `@app.route("/")` 装饰器底层在做什么？
3. Flask 的 `request` 全局对象怎么做到线程安全？
4. FastAPI 的依赖注入是如何实现的？
5. Pydantic 怎么把字典自动转成对象？

---

## 17.1 WSGI：同步 Web 应用规范

### 17.1.1 概念（PEP 3333 规范）

**WSGI（Web Server Gateway Interface）** 是 Python 同步 Web 应用的标准接口：

```python
def application(environ, start_response):
    """这就是一个最简 WSGI 应用"""
    status = "200 OK"
    headers = [("Content-Type", "text/plain")]
    start_response(status, headers)
    return [b"Hello, World!"]
```

### 17.1.2 💡 为什么这样设计

设计目标：**解耦 Web 服务器和应用框架**。

- 服务器（gunicorn/uWSGI）只需懂 WSGI 协议
- 框架（Flask/Django）只需实现 WSGI 协议
- 两者能任意组合

类比：USB 接口让任何键盘连任何电脑。

### 17.1.3 environ 字典

```python
def application(environ, start_response):
    print(environ["REQUEST_METHOD"])    # GET
    print(environ["PATH_INFO"])         # /api/users
    print(environ["QUERY_STRING"])      # id=42
    print(environ["wsgi.input"])        # 请求体（文件类对象）
    # ...
    start_response("200 OK", [("Content-Type", "text/html")])
    return [b"<h1>Hi</h1>"]
```

### 17.1.4 WSGI 的局限

- ❌ **同步阻塞**：一个请求占用一个线程/进程
- ❌ **不支持长连接**（WebSocket、SSE）
- ❌ **不支持流式响应**（虽然返回值是迭代器，但语义上仍是同步）

→ 这正是 ASGI 出现的原因。

---

## 17.2 ASGI：异步 Web 应用规范

### 17.2.1 概念

**ASGI（Asynchronous Server Gateway Interface）** 是 WSGI 的异步继任者：

```python
async def application(scope, receive, send):
    """最简 ASGI 应用"""
    assert scope["type"] == "http"
    
    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [(b"content-type", b"text/plain")],
    })
    await send({
        "type": "http.response.body",
        "body": b"Hello, World!",
    })
```

### 17.2.2 三个参数

| 参数 | 含义 |
|------|------|
| `scope` | 请求元信息（method/path/headers...） |
| `receive` | 异步函数：从客户端**接收**消息 |
| `send` | 异步函数：向客户端**发送**消息 |

### 17.2.3 💡 为什么不复用 WSGI

WSGI 的 `start_response + return [body]` 模型无法表达：
- WebSocket 双向通信
- HTTP/2 服务端推送
- 流式响应（如 ChatGPT 那种 token-by-token）

ASGI 用**消息队列模型**（receive/send）天然支持这些场景。

### 17.2.4 三种 scope 类型

```python
scope["type"] in ("http", "websocket", "lifespan")
```

- **http**：普通 HTTP 请求
- **websocket**：WebSocket 连接
- **lifespan**：应用启动/关闭事件

---

## 17.3 Flask 核心机制

### 17.3.1 一个最小 Flask 应用

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return jsonify({"id": user_id, "name": "Alice"})

if __name__ == "__main__":
    app.run(debug=True)
```

### 17.3.2 🔬 `@app.route()` 装饰器原理

```python
# Flask 内部简化版
class Flask:
    def __init__(self, name):
        self.url_map = Map()           # werkzeug 的路由映射
        self.view_functions = {}        # endpoint → view_func
    
    def route(self, rule, **options):
        def decorator(f):
            endpoint = options.pop("endpoint", None) or f.__name__
            self.add_url_rule(rule, endpoint, f, **options)
            return f               # ← 注意：原样返回函数
        return decorator
    
    def add_url_rule(self, rule, endpoint, view_func, **options):
        self.url_map.add(Rule(rule, endpoint=endpoint, **options))
        self.view_functions[endpoint] = view_func
```

**关键点**：
- 装饰器**不修改函数行为**，只做"注册"
- 路由表存在 `app.url_map`（werkzeug 的 `Map`）
- 视图函数本身不变，所以加 `@app.route` 后还能直接调用测试

### 17.3.3 🔬 请求处理流程

```
1. WSGI 服务器调用 app(environ, start_response)
2. Flask 创建 RequestContext + AppContext，压入栈
3. 路由匹配：url_map.bind(...).match(path) → endpoint, args
4. 调用 view_functions[endpoint](**args)
5. 视图返回值 → make_response → Response 对象
6. Response 转为 WSGI 响应
7. 弹出 RequestContext / AppContext
```

### 17.3.4 ★ 全局对象 `request` 怎么做到线程安全

Flask 的 `request` 是个**全局变量**，但每个请求看到的是不同的：

```python
from flask import request   # 看似全局
print(request.method)       # 但每个请求得到自己的值
```

🔬 **原理：上下文本地变量**（contextvars，Python 3.7+）：

```python
# Flask 2.0+ 的实现（简化）
from contextvars import ContextVar

_request_ctx_stack = ContextVar("request_ctx_stack")

class _RequestProxy:
    def __getattr__(self, name):
        ctx = _request_ctx_stack.get()
        return getattr(ctx.request, name)

request = _RequestProxy()
```

`ContextVar` 在 asyncio 任务/线程间隔离，不同请求互不干扰。

> **💡 为什么这样设计**：让用户写代码像访问全局变量一样简洁，但底层保证隔离。这是 Flask 的"魔法"之一。代价：增加了理解成本，新人会困惑"这个全局变量怎么会线程安全"。

### 17.3.5 蓝图（Blueprint）

```python
from flask import Blueprint

users_bp = Blueprint("users", __name__, url_prefix="/users")

@users_bp.route("/<int:id>")
def detail(id):
    return f"user {id}"

app.register_blueprint(users_bp)
```

蓝图本质是"延迟注册"：装饰器先记录在 Blueprint 内部，调用 `register_blueprint` 才真正注册到 app。

---

## 17.4 FastAPI 核心机制

### 17.4.1 一个最小 FastAPI 应用

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    age: int

@app.post("/users", status_code=201)
async def create_user(payload: UserCreate, db = Depends(get_db)):
    return {"id": 1, **payload.model_dump()}
```

启动：`uvicorn main:app --reload`

### 17.4.2 ★ 类型注解驱动的设计

FastAPI 最大的创新：**用 Python 类型注解作为接口定义**。

```python
@app.get("/items/{item_id}")
def read_item(
    item_id: int,           # 路径参数（int 自动转换+验证）
    q: str | None = None,   # 查询参数（可选）
    body: ItemModel = Body(...),  # 请求体
):
    ...
```

🔬 **实现原理**：FastAPI 在启动时通过 `inspect.signature(func)` 读取参数注解，结合参数默认值（`Query()`/`Path()`/`Body()`/`Depends()`），构建一个 `Dependant` 对象树。

```python
# 简化版
def analyze_param(name, annotation, default):
    if isinstance(default, Depends):
        return DependsField(name, default.dependency)
    if name in path_params:
        return PathField(name, annotation)
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return BodyField(name, annotation)
    return QueryField(name, annotation, default)
```

### 17.4.3 ★ 依赖注入（Depends）

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Header(...), db = Depends(get_db)):
    return db.query(User).filter_by(token=token).first()

@app.get("/me")
async def me(user = Depends(get_current_user)):
    return user
```

🔬 **原理**：每个请求 FastAPI 维护一个**依赖缓存**（dict）。同一请求内多次依赖相同的 `get_db` 只解析一次。生成器形式的依赖，`yield` 后的代码在响应发出后执行（清理）。

### 17.4.4 💡 依赖注入的设计动机

- **解耦**：视图函数不直接 import 数据库代码，便于测试时替换
- **复用**：认证、分页、限流等横切逻辑作为依赖
- **可测试**：`app.dependency_overrides[get_db] = lambda: mock_db`

### 17.4.5 Pydantic：数据验证引擎

```python
from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=0, le=150)
    email: str
    
    @field_validator("email")
    @classmethod
    def email_must_contain_at(cls, v):
        if "@" not in v:
            raise ValueError("invalid email")
        return v

# 自动验证
u = User(name="Alice", age=30, email="a@b.c")    # ✅
# u = User(name="", age=-1, email="x")           # ❌ ValidationError
```

🔬 **Pydantic v2 原理**：用 Rust 实现的核心（pydantic-core），从类型注解生成验证 schema。性能比 v1 快 5-50 倍。

### 17.4.6 自动 OpenAPI

FastAPI 把所有路由的类型信息汇总成 OpenAPI 3.1 文档：

- `/docs`：Swagger UI
- `/redoc`：ReDoc
- `/openapi.json`：原始 schema

→ 接口文档零成本同步。

---

## 17.5 Flask vs FastAPI 对比

| 维度 | Flask | FastAPI |
|------|-------|---------|
| 协议 | WSGI（同步） | ASGI（异步） |
| 类型注解 | 不强制 | 核心驱动力 |
| 自动文档 | 需插件 | 内置 OpenAPI |
| 数据验证 | 手动 | Pydantic 自动 |
| 依赖注入 | 无（手动） | 内置 Depends |
| 性能 | 中等 | 接近 Node.js |
| 生态 | 巨大、成熟 | 较新、增长快 |
| 学习曲线 | 平 | 中（需懂 typing） |

**选型建议**：
- 新项目、需要高并发 I/O → FastAPI
- 已有 Flask 生态、不需要异步 → Flask
- 简单脚本/管理后台 → Flask（更灵活）

---

## 17.6 中间件

### Flask（基于 WSGI）

```python
class TimingMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        import time
        start = time.time()
        result = self.app(environ, start_response)
        print(f"{environ['PATH_INFO']}: {time.time()-start:.3f}s")
        return result

app.wsgi_app = TimingMiddleware(app.wsgi_app)
```

### FastAPI（基于 ASGI）

```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        import time
        start = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = f"{time.time()-start:.3f}"
        return response

app.add_middleware(TimingMiddleware)
```

---

## 17.7 实际部署

### Flask + Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 myapp:app
# -w 4: 4 个 worker 进程
```

### FastAPI + Uvicorn

```bash
uvicorn myapp:app --host 0.0.0.0 --port 8000 --workers 4
```

### 生产组合

```
Nginx (反向代理 / TLS / 静态资源)
   │
   ▼
Gunicorn / Uvicorn (多 worker)
   │
   ▼
应用进程 (Flask / FastAPI)
   │
   ▼
PostgreSQL / Redis / ...
```

---

## 17.8 常见误区

### ❌ 误区 1：在 FastAPI 同步路由里调阻塞代码

```python
@app.get("/")
def slow():
    time.sleep(5)        # 阻塞整个事件循环
```

✅ 应该 `async def` + `await asyncio.sleep(5)`，或同步函数被丢到线程池：FastAPI 对 `def`（非 async）的视图自动用线程池跑。

### ❌ 误区 2：Flask 全局变量当存储

```python
counter = 0

@app.route("/incr")
def incr():
    global counter
    counter += 1         # 多 worker 时各 worker 有自己的 counter
```

→ 用 Redis 或数据库。

### ❌ 误区 3：用 Pydantic 做 ORM

Pydantic 是数据验证；ORM 是 SQLAlchemy。混用会很乱。

---

## 17.9 面试常问

### Q1：WSGI 和 ASGI 的区别？

**答**：WSGI 是同步规范，应用是 `def app(environ, start_response)`，每请求占一个线程。ASGI 是异步规范，应用是 `async def app(scope, receive, send)`，单线程处理大量并发，且支持 WebSocket。

### Q2：FastAPI 为什么快？

**答**：
1. 基于 ASGI（异步，I/O 不阻塞）
2. Starlette 路由（高性能）
3. Pydantic v2（Rust 内核）
4. 类型注解直接生成验证代码（无运行时反射开销）

### Q3：Flask 的 g、request、session 是怎么实现的？

**答**：用 `contextvars.ContextVar` 实现的代理对象。每个请求/任务有独立的 context，跨请求隔离。

### Q4：FastAPI 依赖注入与 Spring 的依赖注入区别？

**答**：
- Spring：基于反射 + 容器，全局单例为主
- FastAPI：基于函数签名 + 请求作用域缓存，更轻量

---

## 17.10 练习题

### 练习 17.1（基础）

写一个最小 WSGI 应用，返回 "Hello, {name}"，name 来自查询字符串。

<details><summary>答案</summary>

```python
from urllib.parse import parse_qs

def app(environ, start_response):
    qs = parse_qs(environ.get("QUERY_STRING", ""))
    name = qs.get("name", ["World"])[0]
    body = f"Hello, {name}".encode()
    start_response("200 OK", [("Content-Type", "text/plain"),
                              ("Content-Length", str(len(body)))])
    return [body]
```
</details>

### 练习 17.2（中级）

用 FastAPI 实现一个 `/items` POST 接口，接收 JSON `{name: str, price: float}`，price 必须 > 0。

<details><summary>答案</summary>

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class Item(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)

@app.post("/items", status_code=201)
async def create(item: Item):
    return {"id": 1, **item.model_dump()}
```
</details>

### 练习 17.3（高级）

用 Flask 实现一个简易的 `@require_auth` 装饰器，从 header 读 token，无效返回 401。

<details><summary>答案</summary>

```python
from functools import wraps
from flask import request, jsonify

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if token != "secret":
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

@app.get("/me")
@require_auth
def me():
    return jsonify({"user": "alice"})
```
</details>

---

**上一章：[16 面试陷阱](16_面试陷阱与高频考点.md)** | **下一章：[18 数据库与 ORM](18_数据库与ORM.md)**

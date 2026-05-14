# 18. 数据库与 ORM

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐⭐ (中高级) |
> | **前置知识** | [02 OOP](02_类与面向对象篇.md)、[09 typing](09_类型系统与typing.md)、[12 异步](12_异步编程深入.md)、SQL 基础 |
> | **学习目标** | 掌握 DB-API 2.0 规范、连接池原理、SQLAlchemy 两层 API、N+1 问题、事务隔离级别 |
> | **CPython 版本** | 3.12+ |
> | **规范 vs 实现** | DB-API 2.0 (PEP 249) 是规范；sqlite3/psycopg/PyMySQL 是实现 |

---

## 18.0 知识地图

```
应用代码
   │
   ▼
ORM 层 (SQLAlchemy ORM)              ← 对象 ↔ 表
   │
   ▼
SQL 层 (SQLAlchemy Core)              ← SQL 表达式
   │
   ▼
DB-API 2.0 (PEP 249 规范)             ← Python 连接数据库的统一接口
   │
   ├── sqlite3       (内置)
   ├── psycopg       (PostgreSQL)
   ├── PyMySQL       (MySQL)
   └── asyncpg       (异步 PG)
   │
   ▼
数据库 (PostgreSQL / MySQL / SQLite)
```

---

## 18.1 DB-API 2.0：所有驱动的统一接口

### 18.1.1 PEP 249 规范

```python
import sqlite3   # 任何 DB-API 2.0 驱动都长这样

conn = sqlite3.connect("test.db")        # 连接
cur = conn.cursor()                       # 游标
cur.execute("SELECT * FROM users WHERE id = ?", (42,))    # 参数化查询
rows = cur.fetchall()
conn.commit()
conn.close()
```

### 18.1.2 ⚠️ 永远用参数化查询（防 SQL 注入）

```python
# ❌ 危险
name = request.args["name"]
cur.execute(f"SELECT * FROM users WHERE name = '{name}'")
# 如果 name = "x'; DROP TABLE users--"，灾难

# ✅ 安全
cur.execute("SELECT * FROM users WHERE name = ?", (name,))
```

### 18.1.3 不同驱动的占位符差异（坑）

| 数据库 | 占位符风格 |
|--------|-----------|
| sqlite3 | `?` (qmark) 或 `:name` (named) |
| psycopg | `%s` (format) |
| PyMySQL | `%s` (format) |

> 这就是 ORM 存在的理由之一：抹平差异。

---

## 18.2 连接池

### 18.2.1 为什么需要

每次新建数据库连接都要：
1. TCP 三次握手
2. TLS 握手（如有）
3. 认证
4. 进程/线程分配

成本高，约 10-100ms。Web 应用每秒上千请求，每次都建连必崩。

**连接池**：预先建好 N 个连接，复用。

### 18.2.2 SQLAlchemy 自带连接池

```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://user:pass@host/db",
    pool_size=10,           # 常驻连接数
    max_overflow=20,        # 高峰允许临时增加
    pool_pre_ping=True,     # 用前 ping 一下，避免死连接
    pool_recycle=3600,      # 1小时回收（避免被 DB/代理超时关闭）
)
```

### 18.2.3 💡 设计要点

- **pool_pre_ping**：解决"DB 重启后旧连接变僵尸"的问题
- **pool_recycle**：MySQL 默认 8 小时空闲超时，必须 < 8 小时
- **pool_size 取多少**：一般 = CPU 核数 × 2 + 1（旧经验），或按实测调

---

## 18.3 SQLAlchemy Core（SQL 表达式层）

```python
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, select

engine = create_engine("sqlite:///test.db")
metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50)),
    Column("age", Integer),
)
metadata.create_all(engine)

with engine.connect() as conn:
    # 插入
    conn.execute(users.insert().values(name="Alice", age=30))
    conn.commit()
    
    # 查询
    stmt = select(users).where(users.c.age >= 18)
    for row in conn.execute(stmt):
        print(row)
```

**特点**：
- 用 Python 表达式构造 SQL
- 比手写字符串安全（自动参数化）
- 不涉及对象映射

---

## 18.4 SQLAlchemy ORM（对象映射层）

### 18.4.1 现代写法（2.0+）

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    age: Mapped[int]
    
    posts: Mapped[list["Post"]] = relationship(back_populates="author")

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    author: Mapped[User] = relationship(back_populates="posts")
```

### 18.4.2 Session：工作单元

```python
from sqlalchemy.orm import Session

with Session(engine) as session:
    # 创建
    alice = User(name="Alice", age=30)
    session.add(alice)
    session.commit()
    
    # 查询
    user = session.get(User, 1)
    users = session.scalars(select(User).where(User.age >= 18)).all()
    
    # 修改
    user.age = 31
    session.commit()       # SQLAlchemy 自动检测变化
    
    # 删除
    session.delete(user)
    session.commit()
```

### 18.4.3 🔬 ORM 内部机制

**Identity Map**：同一 Session 中，同一主键的对象只有一个实例。

```python
u1 = session.get(User, 1)
u2 = session.get(User, 1)
print(u1 is u2)   # True
```

**Unit of Work**：Session 跟踪所有修改，commit 时一次性 flush。

**Lazy/Eager Loading**：默认 lazy（用到关系时才查询），可配置 eager。

---

## 18.5 ★ N+1 查询问题

### 问题

```python
users = session.scalars(select(User)).all()    # 1 条 SQL
for u in users:
    print(u.posts)        # 每个 user 触发 1 条 SQL → N 条
# 总共 N+1 条
```

### 解决：joinedload / selectinload

```python
from sqlalchemy.orm import selectinload

users = session.scalars(
    select(User).options(selectinload(User.posts))
).all()
# 总共 2 条 SQL：一条查 users，一条 IN 查所有 posts
```

> **💡 设计要点**：
> - `selectinload`：用 IN 二次查询（推荐，多对多/一对多）
> - `joinedload`：用 LEFT OUTER JOIN（一对一/多对一）
> - 默认 lazy 是为了简单；生产环境必须显式指定加载策略

---

## 18.6 事务与隔离级别

### 18.6.1 ACID 与隔离级别

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---------|------|-----------|------|
| READ UNCOMMITTED | ❌ | ❌ | ❌ |
| READ COMMITTED | ✅ | ❌ | ❌ |
| REPEATABLE READ | ✅ | ✅ | (见下) |
| SERIALIZABLE | ✅ | ✅ | ✅ |

> 📌 **标准 SQL 规定 RR 允许幻读**，但实际：
> - **MySQL InnoDB**：RR + next-key locking → 大部分场景已避免幻读
> - **PostgreSQL**：RR 实际是 Snapshot Isolation → 避免幻读，但仍有 write skew 等快照异常
> - **SERIALIZABLE**：才能避免所有快照异常（PG 用 SSI；MySQL 用纯锁）

### 18.6.2 SQLAlchemy 中使用

```python
with engine.connect() as conn:
    conn = conn.execution_options(isolation_level="SERIALIZABLE")
    with conn.begin():
        conn.execute(...)
```

### 18.6.3 乐观锁

```python
class User(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    version: Mapped[int] = mapped_column(default=0)
    
    __mapper_args__ = {"version_id_col": version}

# 并发更新时，第二个 commit 会抛 StaleDataError
```

### 18.6.4 悲观锁

```python
user = session.scalars(
    select(User).where(User.id == 1).with_for_update()
).one()
# SELECT ... FOR UPDATE：锁定该行直到事务结束
```

---

## 18.7 异步：SQLAlchemy 2.0 Async

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("postgresql+asyncpg://user:pass@host/db")

async with AsyncSession(engine) as session:
    user = await session.get(User, 1)
    users = (await session.scalars(select(User))).all()
    await session.commit()
```

**注意**：
- 必须用支持异步的驱动（asyncpg / aiomysql）
- 不能在 async session 中用 lazy loading（要么 eager，要么 `await session.refresh(...)`）

---

## 18.8 数据库迁移：Alembic

```bash
pip install alembic
alembic init migrations
# 修改 alembic.ini 与 env.py
alembic revision --autogenerate -m "create users table"
alembic upgrade head
```

**核心思想**：迁移文件放 git，团队共享 schema 演进历史。

---

## 18.9 常见误区

### ❌ 误区 1：在循环里 commit

```python
for item in items:
    session.add(Foo(item=item))
    session.commit()      # 一次 commit 一行，慢
```

✅ 一次 commit 多个：
```python
session.add_all([Foo(item=x) for x in items])
session.commit()
```

### ❌ 误区 2：不关 session

```python
session = Session(engine)
# ... 用完不 close → 连接不归还池
```

✅ 用 `with Session(engine) as session:`

### ❌ 误区 3：过度 ORM

复杂报表、批量操作（如 `UPDATE ... WHERE ...`）应直接写 SQL：

```python
session.execute(update(User).where(User.age < 18).values(blocked=True))
```

### ❌ 误区 4：把 ORM 模型当 DTO

API 输出最好用 Pydantic 模型，避免序列化时触发 lazy load。

---

## 18.10 面试常问

### Q1：ORM 的优缺点？

**答**：
- 优：抽象 SQL 差异、防注入、面向对象、自动迁移、关系导航
- 缺：性能开销、学习成本、复杂查询不直观、容易写出 N+1

### Q2：什么是 N+1 问题？

**答**：见 18.5。本质是 lazy loading 在循环中触发额外查询。用 selectinload/joinedload 解决。

### Q3：连接池的关键参数？

**答**：pool_size（常驻数）、max_overflow（高峰增量）、pool_pre_ping（避免死连接）、pool_recycle（自动重建）。

### Q4：事务隔离级别？

**答**：见 18.6.1 表格。MySQL InnoDB 默认 RR，PostgreSQL 默认 RC。

---

## 18.11 练习题

### 练习 18.1（基础）

用原生 sqlite3 实现 CRUD。

<details><summary>答案</summary>

```python
import sqlite3

with sqlite3.connect("test.db") as conn:
    conn.execute("CREATE TABLE IF NOT EXISTS u (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("INSERT INTO u (name) VALUES (?)", ("Alice",))
    conn.commit()
    
    rows = conn.execute("SELECT * FROM u").fetchall()
    print(rows)
```
</details>

### 练习 18.2（中级）

用 SQLAlchemy ORM 写一个一对多关系（用户-订单），并避免 N+1。

<details><summary>答案</summary>

```python
from sqlalchemy.orm import selectinload

users = session.scalars(
    select(User).options(selectinload(User.orders))
).all()
for u in users:
    print(u.name, len(u.orders))   # 已加载，无额外 SQL
```
</details>

---

**上一章：[17 Web 框架](17_Web框架深入.md)** | **下一章：[19 Redis 与消息队列](19_Redis与消息队列.md)**

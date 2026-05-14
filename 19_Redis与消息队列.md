# 19. Redis 与消息队列

> ## 📋 章节元信息
> | | |
> |---|---|
> | **难度** | ⭐⭐⭐ (中级) |
> | **前置知识** | [13 网络](13_网络编程.md)、[18 数据库](18_数据库与ORM.md)、基本分布式概念 |
> | **学习目标** | 掌握 Redis 数据结构与典型场景、理解 MQ 设计动机、能选型 Celery/Kafka |
> | **CPython 版本** | 3.12+ |
> | **规范 vs 实现** | RESP 协议是规范；redis-py / aioredis 是实现 |

---

## 19.0 知识地图

```
应用层
  ├── 缓存          → Redis (内存 KV)
  ├── 会话          → Redis
  ├── 限流/计数      → Redis (原子操作)
  ├── 分布式锁       → Redis (SETNX)
  ├── 排行榜         → Redis (ZSET)
  ├── 消息广播       → Redis (Pub/Sub)
  │
  └── 任务队列        → Celery + Redis/RabbitMQ
                       Kafka (大数据流处理)
```

---

## 19.1 Redis 是什么

**键值数据库**，全部数据在内存（持久化到磁盘），单线程模型 + I/O 多路复用，性能 ~10万 QPS。

**核心数据结构**：

| 类型 | 用途 |
|------|------|
| String | 简单缓存、计数器 |
| Hash | 对象存储（字段级访问） |
| List | 队列、栈、最新消息 |
| Set | 去重、关系计算 |
| ZSet | 排行榜、延迟队列 |
| Stream | 持久化消息流（5.0+） |
| HyperLogLog | 基数估算 |
| Bitmap | 位操作（签到、布隆过滤器） |
| Geo | 地理位置 |

---

## 19.2 redis-py 基础

```python
import redis

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# String
r.set("name", "Alice", ex=60)        # 60 秒过期
r.get("name")                         # 'Alice'
r.incr("counter")                     # 计数器（原子）

# Hash
r.hset("user:1", mapping={"name": "Alice", "age": 30})
r.hget("user:1", "name")
r.hgetall("user:1")

# List (左进右出 = 队列)
r.lpush("queue", "task1", "task2")
r.brpop("queue", timeout=5)          # 阻塞弹出

# Set
r.sadd("tags", "python", "web")
r.smembers("tags")

# ZSet
r.zadd("leaderboard", {"alice": 100, "bob": 80})
r.zrevrange("leaderboard", 0, 9, withscores=True)  # top 10
```

### 异步：redis.asyncio

```python
import redis.asyncio as redis

r = redis.Redis.from_url("redis://localhost")

async def main():
    await r.set("key", "value")
    print(await r.get("key"))
```

---

## 19.3 典型场景

### 19.3.1 缓存（Cache-Aside 模式）

```python
def get_user(user_id):
    key = f"user:{user_id}"
    cached = r.get(key)
    if cached:
        return json.loads(cached)
    
    user = db.query(User).get(user_id)
    if user:
        r.setex(key, 300, json.dumps(user.to_dict()))   # 5 分钟过期
    return user
```

### 19.3.2 限流（令牌桶 / 滑动窗口）

```python
def is_allowed(user_id, limit=10, window=60):
    """每分钟最多 limit 次"""
    key = f"rate:{user_id}:{int(time.time() // window)}"
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    return count <= limit
```

### 19.3.3 分布式锁

```python
def acquire_lock(key, ttl=10):
    token = str(uuid.uuid4())
    if r.set(key, token, nx=True, ex=ttl):
        return token
    return None

def release_lock(key, token):
    # Lua 保证原子性
    script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """
    r.eval(script, 1, key, token)
```

> **⚠️ 注意**：单 Redis 锁不防主从切换时的脑裂。生产用 Redlock 或 Redis Sentinel/Cluster。

### 19.3.4 排行榜

```python
r.zincrby("leaderboard", 10, "alice")          # alice +10 分
r.zrevrange("leaderboard", 0, 9, withscores=True)
r.zrevrank("leaderboard", "alice")             # 名次
```

### 19.3.5 Pub/Sub

```python
# 发布
r.publish("news", "hello")

# 订阅
sub = r.pubsub()
sub.subscribe("news")
for msg in sub.listen():
    print(msg)
```

⚠️ Pub/Sub 不持久化、不重发。需要持久化用 **Stream**。

### 19.3.6 Stream（推荐做轻量 MQ）

```python
# 生产
r.xadd("events", {"type": "login", "user": "alice"})

# 消费组
r.xgroup_create("events", "group1", id="0", mkstream=True)
msgs = r.xreadgroup("group1", "consumer1", {"events": ">"}, count=10, block=5000)
```

---

## 19.4 持久化策略

### RDB（快照）
- 定期 fork 子进程写快照
- 启动快、占空间小
- 可能丢最近几分钟数据

### AOF（追加日志）
- 每写操作记录到日志
- 数据安全（最多丢 1 秒）
- 日志体积大，重写时压缩

**生产推荐**：RDB + AOF 都开。

---

## 19.5 消息队列

### 19.5.1 为什么需要 MQ

- **解耦**：生产者不需要知道消费者
- **削峰**：高并发请求先排队，慢慢处理
- **异步**：耗时任务（发邮件、生成报表）不阻塞主流程
- **可靠性**：消息持久化，失败重试

### 19.5.2 Python 生态选型

| 方案 | 适用场景 |
|------|---------|
| **Redis List/Stream** | 轻量任务，<10万 QPS |
| **Celery + Redis/RabbitMQ** | 通用异步任务，最流行 |
| **RQ** | 极简，轻量替代 Celery |
| **Kafka (confluent-kafka)** | 大数据、流处理、事件溯源 |
| **NATS** | 高性能云原生 |
| **Dramatiq** | Celery 的现代替代 |

### 19.5.3 Celery 入门

```python
# tasks.py
from celery import Celery

app = Celery("myapp", broker="redis://localhost:6379/0",
             backend="redis://localhost:6379/1")

@app.task
def send_email(to, subject):
    # ... 实际发邮件
    return f"sent to {to}"
```

```python
# 调用方
from tasks import send_email

# 异步发送
result = send_email.delay("alice@x.com", "Hi")
print(result.get(timeout=10))      # 阻塞等结果

# 定时任务
send_email.apply_async(args=["a@b"], countdown=60)   # 60 秒后执行
```

启动 worker：
```bash
celery -A tasks worker --loglevel=info
```

### 19.5.4 Celery 关键概念

- **Broker**：消息中间件（Redis/RabbitMQ）
- **Backend**：结果存储（Redis/DB）
- **Worker**：执行任务的进程
- **Task**：被装饰的函数
- **Beat**：定时调度器（cron 替代）

### 19.5.5 ⚠️ 任务幂等性

任务可能重试，必须幂等：

```python
@app.task(bind=True, max_retries=3)
def charge_user(self, user_id, amount, idempotency_key):
    if Charge.objects.filter(key=idempotency_key).exists():
        return  # 已处理过，直接跳过
    try:
        do_charge(user_id, amount)
    except (ConnectionError, TimeoutError) as e:   # 替换为你自己的瞬态异常基类（Celery 没有内置 TransientError）
        raise self.retry(exc=e, countdown=60)
```

---

## 19.6 Kafka 简介（流处理）

```python
from confluent_kafka import Producer, Consumer

# 生产
p = Producer({"bootstrap.servers": "localhost:9092"})
p.produce("topic1", key="k", value="hello")
p.flush()

# 消费
c = Consumer({"bootstrap.servers": "localhost:9092",
              "group.id": "g1",
              "auto.offset.reset": "earliest"})
c.subscribe(["topic1"])
while True:
    msg = c.poll(1.0)
    if msg and not msg.error():
        print(msg.value())
```

**Kafka vs Celery**：
- Kafka 关注**数据流**（高吞吐、可重放、长保存）
- Celery 关注**任务执行**（一次性、有结果）

---

## 19.7 常见误区

### ❌ 用 Redis 做主存储

Redis 是缓存，DB 是真相。即使开 AOF 也可能丢数据。

### ❌ Celery 任务里用 ORM 实例当参数

ORM 对象 pickle 后可能版本不一致。传 ID，让 worker 自己查。

```python
# ❌
send_email.delay(user)
# ✅
send_email.delay(user.id)
```

### ❌ Pub/Sub 用于关键消息

不持久化、消费者掉线就丢。用 Stream/Kafka/RabbitMQ。

---

## 19.8 面试常问

### Q1：Redis 为什么这么快？

**答**：
1. 纯内存
2. 单线程避免锁
3. I/O 多路复用（epoll）
4. 高效数据结构（跳表、压缩列表）
5. 简单的 RESP 协议

### Q2：Redis 单线程为什么不慢？

**答**：瓶颈是网络/内存而非 CPU。单线程避免了上下文切换、锁竞争。Redis 6.0 把 I/O 多线程化但命令处理仍单线程。

### Q3：缓存击穿/穿透/雪崩？

**答**：
- **击穿**：热点 key 过期 → 大量请求打到 DB → 用互斥锁/永不过期
- **穿透**：查不存在的 key → 缓存空值 / 布隆过滤器
- **雪崩**：大量 key 同时过期 → 过期时间加随机抖动

### Q4：Celery 最佳实践？

**答**：
- 任务幂等
- 任务粒度合适（不要太大/太小）
- 设置 task time limit
- 分队列（critical/default/low）
- 监控（Flower）

---

## 19.9 练习题

### 练习 19.1（基础）

实现一个分布式计数器（多进程并发安全）。

<details><summary>答案</summary>

```python
import redis
r = redis.Redis()

def incr_counter():
    return r.incr("counter")        # INCR 是原子的
```
</details>

### 练习 19.2（中级）

实现"防重提交"装饰器：5 秒内同 user 不能重复请求。

<details><summary>答案</summary>

```python
from functools import wraps

def dedupe(window=5):
    def deco(func):
        @wraps(func)
        def wrapper(user_id, *args, **kwargs):
            key = f"dedupe:{func.__name__}:{user_id}"
            if not r.set(key, "1", nx=True, ex=window):
                raise RuntimeError("请求过于频繁")
            return func(user_id, *args, **kwargs)
        return wrapper
    return deco
```
</details>

---

**上一章：[18 数据库与 ORM](18_数据库与ORM.md)** | **下一章：[20 AST 与字节码深入](20_AST与字节码深入.md)**

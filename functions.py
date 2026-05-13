# Python 函数示例

# 1. 基本函数
def greet(name):
    """打招呼函数"""
    return f"你好, {name}! 欢迎学习Python!"

print(greet("小明"))

# 2. 默认参数
def power(base, exp=2):
    """计算幂次方"""
    return base ** exp

print(f"3的平方: {power(3)}")
print(f"2的10次方: {power(2, 10)}")

# 3. 可变参数
def calculate_avg(*numbers):
    """计算平均值"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

print(f"平均值: {calculate_avg(85, 90, 78, 92, 88)}")

# 4. 递归函数
def fibonacci(n):
    """斐波那契数列"""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(f"\n斐波那契数列前10项:")
for i in range(10):
    print(fibonacci(i), end=" ")
print()

# 5. Lambda 表达式
numbers = [3, 1, 4, 1, 5, 9, 2, 6]
sorted_nums = sorted(numbers)
sorted_desc = sorted(numbers, key=lambda x: -x)
print(f"\n原始列表: {numbers}")
print(f"升序排列: {sorted_nums}")
print(f"降序排列: {sorted_desc}")

# 6. 装饰器
def timer(func):
    """简单计时装饰器"""
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[{func.__name__}] 执行耗时: {end - start:.4f}秒")
        return result
    return wrapper

@timer
def slow_sum(n):
    """计算1到n的和（故意用循环）"""
    total = 0
    for i in range(1, n + 1):
        total += i
    return total

result = slow_sum(1000000)
print(f"1到1000000的和: {result}")

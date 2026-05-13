# Python 面向对象编程示例

# 1. 基本类定义
class Animal:
    """动物基类"""
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def speak(self):
        return "..."

    def info(self):
        return f"{self.name}, {self.age}岁"

# 2. 继承
class Dog(Animal):
    """狗类"""
    def __init__(self, name, age, breed):
        super().__init__(name, age)
        self.breed = breed

    def speak(self):
        return "汪汪汪!"

    def fetch(self):
        return f"{self.name}去捡球了!"

class Cat(Animal):
    """猫类"""
    def speak(self):
        return "喵喵喵~"

    def climb(self):
        return f"{self.name}爬上了树!"

# 3. 使用类
dog = Dog("旺财", 3, "金毛")
cat = Cat("咪咪", 2)

print(f"狗: {dog.info()}, 品种: {dog.breed}")
print(f"  叫声: {dog.speak()}")
print(f"  {dog.fetch()}")
print()
print(f"猫: {cat.info()}")
print(f"  叫声: {cat.speak()}")
print(f"  {cat.climb()}")

# 4. 特殊方法 (魔术方法)
class Vector:
    """二维向量类"""
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f"Vector({self.x}, {self.y})"

    def __abs__(self):
        return (self.x**2 + self.y**2) ** 0.5

v1 = Vector(3, 4)
v2 = Vector(1, 2)
v3 = v1 + v2

print(f"\n--- 向量运算 ---")
print(f"v1 = {v1}")
print(f"v2 = {v2}")
print(f"v1 + v2 = {v3}")
print(f"|v1| = {abs(v1)}")

# 5. 属性装饰器
class Circle:
    """圆形类"""
    import math

    def __init__(self, radius):
        self._radius = radius

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("半径不能为负数!")
        self._radius = value

    @property
    def area(self):
        import math
        return math.pi * self._radius ** 2

    @property
    def perimeter(self):
        import math
        return 2 * math.pi * self._radius

circle = Circle(5)
print(f"\n--- 圆形 ---")
print(f"半径: {circle.radius}")
print(f"面积: {circle.area:.2f}")
print(f"周长: {circle.perimeter:.2f}")

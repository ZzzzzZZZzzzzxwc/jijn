# Python 基础语法示例

# 1. 变量与数据类型
name = "小明"
age = 20
height = 1.75
is_student = True

print(f"姓名: {name}, 年龄: {age}, 身高: {height}m, 是否学生: {is_student}")

# 2. 条件判断
score = 85
if score >= 90:
    grade = "优秀"
elif score >= 80:
    grade = "良好"
elif score >= 60:
    grade = "及格"
else:
    grade = "不及格"
print(f"成绩: {score}分, 等级: {grade}")

# 3. 循环
print("\n--- for 循环 ---")
fruits = ["苹果", "香蕉", "橙子", "葡萄"]
for fruit in fruits:
    print(f"我喜欢吃{fruit}")

print("\n--- while 循环 ---")
count = 0
while count < 5:
    print(f"计数: {count}")
    count += 1

# 4. 列表推导式
squares = [x**2 for x in range(1, 11)]
print(f"\n1到10的平方: {squares}")

# 5. 字典操作
student = {
    "name": "小红",
    "age": 18,
    "courses": ["数学", "英语", "物理"]
}
print(f"\n学生信息: {student['name']}, 选课: {', '.join(student['courses'])}")

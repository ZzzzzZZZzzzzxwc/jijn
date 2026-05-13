# Python 小游戏集合

import random

# 1. 猜数字游戏（自动演示版）
def guess_number_demo():
    """猜数字游戏演示"""
    print("=== 猜数字游戏 ===")
    secret = random.randint(1, 100)
    attempts = 0

    # 用二分法模拟猜测
    low, high = 1, 100
    while True:
        guess = (low + high) // 2
        attempts += 1
        print(f"第{attempts}次猜测: {guess}", end=" -> ")

        if guess == secret:
            print(f"猜对了! 答案就是 {secret}, 共猜了 {attempts} 次")
            break
        elif guess < secret:
            print("太小了!")
            low = guess + 1
        else:
            print("太大了!")
            high = guess - 1

# 2. 石头剪刀布
def rock_paper_scissors():
    """石头剪刀布模拟"""
    print("\n=== 石头剪刀布 (模拟10局) ===")
    choices = ["石头", "剪刀", "布"]
    wins = {"石头": "剪刀", "剪刀": "布", "布": "石头"}

    player_score = 0
    computer_score = 0

    for i in range(10):
        player = random.choice(choices)
        computer = random.choice(choices)

        if player == computer:
            result = "平局"
        elif wins[player] == computer:
            result = "玩家胜"
            player_score += 1
        else:
            result = "电脑胜"
            computer_score += 1

        print(f"  第{i+1}局: 玩家={player} vs 电脑={computer} -> {result}")

    print(f"\n  最终比分 - 玩家: {player_score}, 电脑: {computer_score}")
    if player_score > computer_score:
        print("  恭喜玩家获胜!")
    elif computer_score > player_score:
        print("  电脑获胜!")
    else:
        print("  平局!")

# 3. 简易密码生成器
def generate_password(length=12):
    """生成随机密码"""
    import string
    chars = string.ascii_letters + string.digits + "!@#$%&*"
    password = ''.join(random.choice(chars) for _ in range(length))
    return password

def password_demo():
    """密码生成器演示"""
    print("\n=== 密码生成器 ===")
    for i in range(5):
        pwd = generate_password(16)
        print(f"  密码{i+1}: {pwd}")

# 4. 简易抽奖程序
def lottery():
    """抽奖程序"""
    print("\n=== 幸运抽奖 ===")
    participants = ["小明", "小红", "小华", "小李", "小张", "小王", "小赵", "小刘"]
    prizes = ["一等奖", "二等奖", "三等奖"]

    random.shuffle(participants)
    print(f"  参与者: {', '.join(participants)}")
    print("  开始抽奖...")
    print()

    for prize in prizes:
        winner = participants.pop()
        print(f"  {prize}: {winner}")

    print(f"\n  未中奖: {', '.join(participants)}")

# 运行所有演示
if __name__ == "__main__":
    guess_number_demo()
    rock_paper_scissors()
    password_demo()
    lottery()

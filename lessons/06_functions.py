# =============================================
# 6강. 함수(function): 코드에 이름 붙여 재사용하기
# 실행 방법: python3 06_functions.py
# =============================================

# --- 1. 함수 만들기(def)와 부르기 ---
def say_hello():
    print("안녕하세요!")
    print("오늘도 코딩해 봐요.")

say_hello()   # 함수 이름 + () 로 실행
say_hello()   # 몇 번이든 다시 쓸 수 있어요

# --- 2. 매개변수(parameter): 함수에 값 전달하기 ---
def greet(name):
    print(f"{name}님, 반가워요!")

greet("영희")
greet("민수")

# --- 3. return: 함수가 결과값을 돌려주기 ---
def add(a, b):
    return a + b

result = add(3, 5)
print("3 + 5 =", result)

# --- 4. 조금 더 쓸모 있는 함수 ---
def is_even(n):
    """n이 짝수면 True, 홀수면 False를 돌려줍니다."""
    return n % 2 == 0

for n in range(1, 6):
    print(n, "짝수" if is_even(n) else "홀수")

def average(numbers):
    return sum(numbers) / len(numbers)

print("평균:", average([80, 90, 100]))

# ---------------------------------------------
# ✏️ 연습문제
# 1) 원의 반지름을 받아 넓이를 돌려주는 함수 circle_area(r)을 만들어 보세요.
#    (넓이 = 3.14 * r * r)
# 2) 리스트를 받아 가장 긴 단어를 돌려주는 함수를 만들어 보세요.
# 3) 점수를 받아 "A"/"B"/"C"/"F"를 돌려주는 함수 grade(score)를 만들어 보세요.
# ---------------------------------------------

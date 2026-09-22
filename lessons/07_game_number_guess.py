# =============================================
# 7강. 🎮 종합 실습: 숫자 맞히기 게임
# 실행 방법: python3 07_game_number_guess.py
#
# 지금까지 배운 것을 전부 사용합니다:
#   변수, 입력/출력, 조건문, 반복문, 리스트, 함수
# =============================================

import random  # 파이썬에 들어 있는 "무작위 숫자" 도구를 불러오기


def ask_number(prompt):
    """숫자를 입력할 때까지 계속 물어봅니다."""
    while True:
        text = input(prompt)
        if text.isdigit():      # 문자열이 숫자로만 이루어졌는지 확인
            return int(text)
        print("숫자만 입력해 주세요!")


def play_round(max_number, max_tries):
    """게임 한 판을 진행하고, 이겼으면 시도 횟수를, 졌으면 None을 돌려줍니다."""
    answer = random.randint(1, max_number)  # 1 ~ max_number 중 하나
    guesses = []

    print(f"\n1부터 {max_number} 사이의 숫자를 생각했어요. 기회는 {max_tries}번!")

    while len(guesses) < max_tries:
        guess = ask_number(f"[{len(guesses) + 1}/{max_tries}] 추측: ")
        guesses.append(guess)

        if guess == answer:
            print(f"🎉 정답! {len(guesses)}번 만에 맞혔어요.")
            return len(guesses)
        elif guess < answer:
            print("⬆️  더 큰 숫자예요.")
        else:
            print("⬇️  더 작은 숫자예요.")

    print(f"😢 기회를 모두 썼어요. 정답은 {answer}였습니다.")
    print("내가 추측한 숫자들:", guesses)
    return None


def main():
    print("=== 숫자 맞히기 게임 ===")
    print("난이도를 고르세요: 1) 쉬움  2) 보통  3) 어려움")
    level = ask_number("선택: ")

    if level == 1:
        max_number, max_tries = 10, 5
    elif level == 3:
        max_number, max_tries = 100, 7
    else:
        max_number, max_tries = 50, 7

    records = []  # 이긴 판의 시도 횟수를 모아 두는 리스트
    while True:
        tries = play_round(max_number, max_tries)
        if tries is not None:
            records.append(tries)

        again = input("\n한 판 더 할까요? (y/n): ")
        if again != "y":
            break

    print("\n=== 게임 종료 ===")
    if records:
        print(f"이긴 판: {len(records)}번, 최고 기록: {min(records)}번 만에 정답")
    else:
        print("다음엔 꼭 이겨 봐요!")


main()

# ---------------------------------------------
# ✏️ 도전 과제
# 1) 정답과의 차이가 5 이하일 때 "아주 가까워요! 🔥"를 출력해 보세요.
# 2) 이미 입력했던 숫자를 또 입력하면 기회를 차감하지 않고 알려 주세요.
#    (힌트: if guess in guesses:)
# 3) 가위바위보 게임을 처음부터 직접 만들어 보세요!
#    (힌트: random.choice(["가위", "바위", "보"]))
# ---------------------------------------------

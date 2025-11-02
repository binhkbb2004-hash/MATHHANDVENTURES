# Tên file: game_logic.py

import random

def generate_math_problem():
    """Tạo bài toán CỘNG hoặc TRỪ."""
    operator = random.choice(['+', '-'])
    if operator == '+':
        num1 = random.randint(0, 10)
        num2 = random.randint(0, 10 - num1)
        answer = num1 + num2
        question = f"{num1} + {num2} = ?"
    else:
        num1 = random.randint(1, 10)
        num2 = random.randint(0, num1)
        answer = num1 - num2
        question = f"{num1} - {num2} = ?"
    return question, answer

def generate_counting_problem():
    """Tạo bài toán ĐẾM ĐỒ VẬT."""
    number_of_objects = random.randint(1, 10)
    question = number_of_objects
    answer = number_of_objects
    return question, answer

def generate_missing_number_problem():
    """Tạo bài toán "Tìm số còn thiếu"."""
    operator = random.choice(['+', '-'])
    if operator == '+':
        # Dạng a + ? = c
        num1 = random.randint(1, 9)
        answer = random.randint(1, 10 - num1) # Số cần tìm
        result = num1 + answer
        question = f"{num1} + ? = {result}"
    else:
        # Dạng a - ? = c
        num1 = random.randint(2, 10)
        answer = random.randint(1, num1 - 1) # Số cần tìm
        result = num1 - answer
        question = f"{num1} - ? = {result}"
    return question, answer

def generate_random_challenge():
    """
    Chọn ngẫu nhiên một trong ba loại câu đố cho Game 3.
    :return: (loại câu đố, câu hỏi, đáp án)
    """
    game_type = random.choice(['Math', 'Counting', 'MissingNumber'])
    
    if game_type == 'Math':
        question, answer = generate_math_problem()
        return 'Math', question, answer
    elif game_type == 'Counting':
        question, answer = generate_counting_problem()
        return 'Counting', question, answer
    else: # MissingNumber
        question, answer = generate_missing_number_problem()
        return 'MissingNumber', question, answer

def check_answer(user_answer, correct_answer):
    """Kiểm tra đáp án."""
    return user_answer == correct_answer

# --- Phần chạy thử ---
if __name__ == "__main__":
    print("--- Chay thu Module Logic Tro Choi ---")
    
    print("\n--- TEST CHUC NANG CHON CAU HOI NGAU NHIEN (GAME 3) ---")
    for i in range(5):
        q_type, question, answer = generate_random_challenge()
        print(f"Loai: {q_type}, Cau hoi: {question} (Dap an: {answer})")
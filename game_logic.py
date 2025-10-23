# Tên file: game_logic.py

import random

def generate_math_problem():
    """
    Tạo ngẫu nhiên một bài toán CỘNG hoặc TRỪ.
    - Phép cộng có tổng không quá 10.
    - Phép trừ có kết quả không âm.
    :return: Một tuple chứa (chuỗi câu hỏi, đáp án đúng bằng số).
    """
    operator = random.choice(['+', '-'])

    if operator == '+':
        num1 = random.randint(0, 10)
        num2 = random.randint(0, 10 - num1)
        answer = num1 + num2
        question = f"{num1} + {num2} = ?"
    else: # Phép toán '-'
        num1 = random.randint(1, 10)
        num2 = random.randint(0, num1)
        answer = num1 - num2
        question = f"{num1} - {num2} = ?"

    return question, answer

def generate_counting_problem():
    """
    Tạo ngẫu nhiên một bài toán ĐẾM SỐ LƯỢNG.
    :return: Một tuple chứa (số lượng đồ vật, đáp án đúng).
             Ví dụ: (7, 7) -> hiển thị 7 đồ vật và đáp án đúng là 7.
    """
    # Chọn một số ngẫu nhiên từ 1 đến 10
    number_of_objects = random.randint(1, 10)
    
    # Trong game này, "câu hỏi" chính là số lượng đồ vật cần hiển thị,
    # và đáp án cũng chính là con số đó.
    question = number_of_objects
    answer = number_of_objects
    
    return question, answer

def check_answer(user_answer, correct_answer):
    """
    Kiểm tra xem câu trả lời của người dùng có đúng không.
    :param user_answer: Số người dùng trả lời (từ module nhận diện tay).
    :param correct_answer: Đáp án đúng của bài toán.
    :return: True nếu đúng, False nếu sai.
    """
    return user_answer == correct_answer

# --- Phần code để chạy thử Module này một cách độc lập ---
if __name__ == "__main__":
    print("--- Chay thu Module Logic Tro Choi ---")

    print("\n--- GAME 1: TINH TOAN ---")
    # Tạo ra 3 bài toán tính toán để kiểm tra
    for i in range(3):
        question, answer = generate_math_problem()
        print(f"Cau hoi: {question} (Dap an: {answer})")

    print("\n--- GAME 2: DEM SO LUONG ---")
    # Tạo ra 3 bài toán đếm để kiểm tra
    for i in range(3):
        question, answer = generate_counting_problem()
        print(f"Yeu cau: Hien thi {question} do vat. (Dap an: {answer})")
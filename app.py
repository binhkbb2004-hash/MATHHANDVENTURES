# Tên file: app.py

import os
import cv2
import numpy as np
import base64
from flask import Flask, request
from flask_socketio import SocketIO, emit

# Import các module đã tạo
from demngontay import HandDetector
from game_logic import generate_math_problem, generate_counting_problem, check_answer
from database import init_db, save_game_result, get_player_history

# --- KHỞI TẠO SERVER ---
app = Flask(__name__)
# Cấu hình CORS để cho phép tất cả các nguồn kết nối
socketio = SocketIO(app, cors_allowed_origins="*")

# Khởi tạo database khi server chạy
init_db()

# Khởi tạo bộ nhận diện tay một lần duy nhất
detector = HandDetector(max_hands=2, detection_con=0.8)
print(">>> Hand Detector da khoi tao. Server san sang.")

# --- QUẢN LÝ TRẠNG THÁI GAME ---
# Dictionary để lưu trạng thái của từng người chơi
game_states = {}

# --- HÀM TIỆN ÍCH ---
def base64_to_image(base64_string):
    """Chuyển đổi chuỗi base64 thành ảnh OpenCV."""
    if "," in base64_string:
        base64_string = base64_string.split(',')[1]
    img_bytes = base64.b64decode(base64_string)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image

# --- CÁC SỰ KIỆN WEBSOCKET ---
@socketio.on('connect')
def handle_connect():
    """Xử lý khi một client mới kết nối."""
    client_id = request.sid
    game_states[client_id] = {
        'state': 'MainMenu', 'score': 0, 'question_count': 0,
        'correct_answer': None, 'last_finger_count': 0
    }
    print(f">>> Client da ket noi: {client_id}")

@socketio.on('disconnect')
def handle_disconnect():
    """Xử lý khi một client ngắt kết nối."""
    client_id = request.sid
    if client_id in game_states:
        del game_states[client_id]
    print(f">>> Client da ngat ket noi: {client_id}")

@socketio.on('process_frame')
def handle_process_frame(data):
    """Nhận diện tay từ frame video và cập nhật số ngón tay."""
    client_id = request.sid
    if client_id not in game_states: return

    frame = base64_to_image(data['image'])
    frame = detector.find_hands(frame, draw=False)
    
    total_finger_count = 0
    if detector.results.multi_hand_landmarks:
        for i in range(len(detector.results.multi_hand_landmarks)):
            handedness = detector.results.multi_handedness[i].classification[0].label
            landmarks = detector.get_landmarks(frame, hand_no=i)
            if landmarks:
                total_finger_count += detector.count_fingers(landmarks, handedness)
    
    game_states[client_id]['last_finger_count'] = total_finger_count
    emit('finger_count_update', {'count': total_finger_count})


@socketio.on('start_game')
def handle_start_game(data):
    """Bắt đầu và quản lý toàn bộ một lượt chơi 10 câu hỏi."""
    client_id = request.sid
    game_mode = data.get('game_mode')
    player_name = data.get('name')

    if not (player_name and client_id in game_states):
        return

    # Tạo/Reset trạng thái game cho lượt chơi
    state = game_states[client_id]
    state['player_name'] = player_name
    state['game_mode'] = game_mode
    state['score'] = 0
    state['question_count'] = 0
    state['state'] = f"Playing{game_mode}"

    for q_num in range(10):
        state['question_count'] = q_num + 1
        
        # 1. Tạo câu hỏi
        if game_mode == 'Math':
            question, answer = generate_math_problem()
        else:
            question, answer = generate_counting_problem()
        
        state['correct_answer'] = answer
        
        # 2. Gửi câu hỏi cho client
        emit('new_question', {'question_text': question, 'question_count': state['question_count']})
        
        # 3. Bắt đầu đếm ngược 10 giây trên server
        for i in range(10, -1, -1):
            emit('timer_update', {'time': i})
            socketio.sleep(1)

        # 4. Hết giờ, chốt đáp án
        user_answer = state['last_finger_count']
        is_correct = check_answer(user_answer, state['correct_answer'])
        
        if is_correct:
            state['score'] += 10
        
        # 5. Gửi kết quả về cho client
        emit('show_result', {
            'is_correct': is_correct, 'correct_answer': state['correct_answer'], 'new_score': state['score']
        })
        socketio.sleep(3) # Chờ 3 giây để client hiển thị kết quả



    # 6. Game kết thúc, lưu kết quả và gửi lại lịch sử
    final_score = state['score']
    save_game_result(player_name, final_score, game_mode)
    history = get_player_history(player_name)

    emit('game_over', {'final_score': final_score, 'history': history})
    state['state'] = 'MainMenu'

# --- CHẠY SERVER (Phiên bản cho Cloud) ---
if __name__ == '__main__':
    # Lấy PORT từ biến môi trường của Railway, nếu không có thì mặc định dùng 5000
    port = int(os.environ.get("PORT", 5000))
    print(f">>> Server se chay tren cong {port}...")
    # Chạy server với các cấu hình cho cloud
    socketio.run(app, host='0.0.0.0', port=port)
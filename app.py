# Tên file: app.py (Phiên bản Admin Panel, đã sửa lỗi)

import os
import cv2
import numpy as np
import base64
from flask import Flask, request
from flask_socketio import SocketIO, emit

# Import các hàm từ các module khác
from demngontay import HandDetector
from game_logic import generate_math_problem, generate_counting_problem, check_answer
from database import (
    init_db,
    find_or_create_user,
    save_game_result,
    get_player_history,
    get_all_users,
    update_user_name,
    delete_user_and_history
)

# --- KHỞI TẠO SERVER ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin123' # Mật khẩu admin
socketio = SocketIO(app, cors_allowed_origins="*")

init_db()
detector = HandDetector(max_hands=2, detection_con=0.8)
game_states = {}

def base64_to_image(base64_string):
    if "," in base64_string:
        base64_string = base64_string.split(',')[1]
    img_bytes = base64.b64decode(base64_string)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return image

# --- CÁC SỰ KIỆN WEBSOCKET CỦA NGƯỜI CHƠI ---
@socketio.on('connect')
def handle_connect():
    print(f">>> Client da ket noi: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in game_states:
        del game_states[request.sid]
    print(f">>> Client da ngat ket noi: {request.sid}")

@socketio.on('process_frame')
def handle_process_frame(data):
    # (Hàm này giữ nguyên, không thay đổi)
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
    client_id = request.sid
    game_mode = data.get('game_mode')
    
    # --- THAY ĐỔI DUY NHẤT NẰM Ở ĐÂY ---
    # Thêm .strip() để xóa khoảng trắng thừa ở đầu và cuối tên
    player_name = data.get('name', '').strip() 

    if not player_name: return

    user_id = find_or_create_user(player_name)

    game_states[client_id] = {
        'user_id': user_id, 'game_mode': game_mode, 'score': 0,
        'question_count': 0, 'correct_answer': None, 'last_finger_count': 0
    }
    state = game_states[client_id]

    for q_num in range(10):
        state['question_count'] = q_num + 1
        if game_mode == 'Math':
            question, answer = generate_math_problem()
        else:
            question, answer = generate_counting_problem()
        state['correct_answer'] = answer
        emit('new_question', {'question_text': question, 'question_count': state['question_count']})
        for i in range(10, -1, -1):
            emit('timer_update', {'time': i})
            socketio.sleep(1)
        user_answer = state['last_finger_count']
        is_correct = check_answer(user_answer, state['correct_answer'])
        if is_correct:
            state['score'] += 10
        emit('show_result', {'is_correct': is_correct, 'correct_answer': state['correct_answer'], 'new_score': state['score']})
        socketio.sleep(3)

    final_score = state['score']
    save_game_result(user_id, final_score, game_mode)
    history = get_player_history(user_id)
    emit('game_over', {'final_score': final_score, 'history': history})

# --- CÁC SỰ KIỆN DÀNH CHO ADMIN ---
@socketio.on('admin_login')
def handle_admin_login(data):
    password = data.get('password')
    if password == app.config['SECRET_KEY']:
        emit('admin_login_success')
        print(">>> Admin da dang nhap thanh cong.")
    else:
        emit('admin_login_fail')
        print(">>> Co nguoi dang nhap Admin that bai.")

@socketio.on('admin_get_all_users')
def handle_admin_get_all_users():
    users = get_all_users()
    emit('admin_user_list', {'users': users})

@socketio.on('admin_get_user_history')
def handle_admin_get_user_history(data):
    user_id = data.get('user_id')
    if user_id:
        history = get_player_history(user_id)
        emit('admin_user_history_data', {'history': history})

@socketio.on('admin_update_user_name')
def handle_admin_update_user_name(data):
    user_id = data.get('user_id')
    new_name = data.get('new_name')
    if user_id and new_name:
        success = update_user_name(user_id, new_name)
        emit('admin_update_user_response', {'success': success})

@socketio.on('admin_delete_user')
def handle_admin_delete_user(data):
    user_id = data.get('user_id')
    if user_id:
        delete_user_and_history(user_id)
        emit('admin_delete_user_response', {'success': True})

# --- CHẠY SERVER ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False)
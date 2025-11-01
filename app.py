# Tên file: app.py (Phiên bản Client-Side AI - Không cv2)

import os
# --- KHÔNG CÓ import cv2, numpy, base64 ---
from flask import Flask, request
from flask_socketio import SocketIO, emit

# --- KHÔNG IMPORT demngontay ---
from game_logic import (
    generate_math_problem, 
    generate_counting_problem, 
    generate_missing_number_problem, 
    generate_random_challenge,
    check_answer
)
from database import (
    init_db, find_or_create_user, save_game_result, get_player_history,
    get_all_users, update_user_name, delete_user_and_history, update_user_avatar,
    get_total_users_count, get_game_statistics_by_mode
)

# --- KHỞI TẠO SERVER ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'admin123' 
socketio = SocketIO(app, cors_allowed_origins="*")

init_db()
# --- KHÔNG CẦN HandDetector ---
game_states = {} # Dùng để lưu trạng thái của client

# --- KHÔNG CẦN HÀM base64_to_image ---

# --- HÀM MỚI: TÁCH RIÊNG VÒNG LẶP GAME ---
def run_game_loop(client_id, game_mode, user_id):
    """Hàm này chạy trong một tác vụ nền (background task)"""
    state = game_states[client_id]
    final_score = 0
    
    try:
        if game_mode == 'Math' or game_mode == 'Counting':
            for q_num in range(10):
                if state.get('exit_requested', False):
                    final_score = state['score']
                    break
                    
                state['question_count'] = q_num + 1
                if game_mode == 'Math':
                    question, answer = generate_math_problem()
                    q_type = 'Math'
                else:
                    question, answer = generate_counting_problem()
                    q_type = 'Counting'
                state['correct_answer'] = answer
                socketio.emit('new_question', {'question_type': q_type, 'question_text': question, 'question_count': state['question_count']}, to=client_id)
                
                for i in range(10, -1, -1):
                    socketio.emit('timer_update', {'time': i}, to=client_id)
                    socketio.sleep(1) 
                    if state.get('exit_requested', False):
                        break
                
                if state.get('exit_requested', False):
                    final_score = state['score']
                    break 
                    
                user_answer = state['last_finger_count']
                is_correct = check_answer(user_answer, state['correct_answer'])
                if is_correct: state['score'] += 10
                
                socketio.emit('show_result', {'is_correct': is_correct, 'correct_answer': state['correct_answer'], 'new_score': state['score']}, to=client_id)
                socketio.sleep(3)
            
            if not state.get('exit_requested', False):
                final_score = state['score']
        
        elif game_mode == 'Obstacle':
            state['current_milestone'] = 1
            state['highest_milestone'] = 1
            
            while state['current_milestone'] <= 20:
                if state.get('exit_requested', False):
                    final_score = state['highest_milestone']
                    break
                    
                q_type, question, answer = generate_random_challenge()
                state['correct_answer'] = answer
                socketio.emit('new_question', {'question_type': q_type, 'question_text': question, 'milestone': state['current_milestone']}, to=client_id)
                if state['current_milestone'] in [10, 15, 20]:
                    socketio.emit('reward_unlocked', {'milestone': state['current_milestone']}, to=client_id)
                    socketio.sleep(1)
                for i in range(10, -1, -1):
                    socketio.emit('timer_update', {'time': i}, to=client_id)
                    socketio.sleep(1)
                    if state.get('exit_requested', False): break
                if state.get('exit_requested', False):
                    final_score = state['highest_milestone']
                    break
                user_answer = state['last_finger_count']
                is_correct = check_answer(user_answer, state['correct_answer'])
                if is_correct:
                    state['current_milestone'] += 1
                    if state['current_milestone'] > state['highest_milestone']:
                        state['highest_milestone'] = state['current_milestone']
                else:
                    state['current_milestone'] = max(1, state['current_milestone'] - 2)
                socketio.emit('show_result', {'is_correct': is_correct, 'correct_answer': state['correct_answer'], 'new_milestone': state['current_milestone']}, to=client_id)
                socketio.sleep(3)
            
            if not state.get('exit_requested', False):
                final_score = state['highest_milestone']
                if state['current_milestone'] > 20: final_score = 20
        
        save_game_result(user_id, final_score, game_mode)
        history = get_player_history(user_id)
        socketio.emit('game_over', {'final_score': final_score, 'history': history}, to=client_id)
        
        state['state'] = 'MainMenu'
        state['exit_requested'] = False
        
    except Exception as e:
        print(f"Loi trong game loop cho {client_id}: {e}")
        if client_id in game_states:
            state['state'] = 'MainMenu'
        socketio.emit('game_over', {'final_score': final_score, 'history': []}, to=client_id)


# --- CÁC SỰ KIỆN WEBSOCKET CỦA NGƯOI CHƠI ---
@socketio.on('connect')
def handle_connect():
    print(f">>> Client da ket noi: {request.sid}")
    game_states[request.sid] = {'state': 'Connected'}

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in game_states:
        del game_states[request.sid]
    print(f">>> Client da ngat ket noi: {request.sid}")

@socketio.on('player_login')
def handle_player_login(data):
    client_id = request.sid
    player_name = data.get('name', '').strip()
    if not player_name:
        emit('login_fail', {'message': 'Tên không hợp lệ.'})
        return

    user_info = find_or_create_user(player_name)
    game_states[client_id] = {
        'user_id': user_info['user_id'],
        'avatar_id': user_info['avatar_id'],
        'player_name': player_name,
        'state': 'MainMenu'
    }
    emit('player_info_updated', {'name': player_name, 'avatar_id': user_info['avatar_id']})

@socketio.on('player_logout')
def handle_player_logout():
    client_id = request.sid
    if client_id in game_states:
        game_states[client_id] = {'state': 'Connected'}
    emit('logout_success')

@socketio.on('client_finger_count')
def handle_client_finger_count(data):
    """Nhận SỐ ĐẾM (count) trực tiếp từ client và cập nhật state."""
    client_id = request.sid
    if client_id not in game_states: return
    count = data.get('count', 0)
    if game_states[client_id].get('state') == 'Playing':
        game_states[client_id]['last_finger_count'] = count

@socketio.on('start_game')
def handle_start_game(data):
    """Bắt đầu tác vụ nền cho game loop."""
    client_id = request.sid
    game_mode = data.get('game_mode')
    
    if client_id not in game_states or 'user_id' not in game_states[client_id]:
        emit('game_over', {'final_score': 0, 'history': []})
        return

    state = game_states[client_id]
    user_id = state['user_id']
    
    state.update({
        'game_mode': game_mode, 'score': 0, 'question_count': 0, 
        'correct_answer': None, 'last_finger_count': 0, 'state': 'Playing',
        'exit_requested': False
    })
    
    socketio.start_background_task(run_game_loop, client_id, game_mode, user_id)

@socketio.on('player_update_avatar')
def handle_player_update_avatar(data):
    client_id = request.sid
    if client_id not in game_states or 'user_id' not in game_states[client_id]:
        emit('avatar_update_fail', {'message': 'Bạn cần đăng nhập trước.'})
        return
    user_id = game_states[client_id]['user_id']
    avatar_id = data.get('avatar_id')
    if avatar_id is not None:
        success = update_user_avatar(user_id, avatar_id)
        if success:
            game_states[client_id]['avatar_id'] = avatar_id
            emit('avatar_update_success', {'avatar_id': avatar_id})
        else:
            emit('avatar_update_fail', {'message': 'Không thể cập nhật avatar.'})
    else:
        emit('avatar_update_fail', {'message': 'Dữ liệu không hợp lệ.'})
        
@socketio.on('player_exit_game')
def handle_player_exit_game():
    """Hàm này giờ sẽ hoạt động ngay lập tức vì server không bị block."""
    client_id = request.sid
    if client_id in game_states and game_states[client_id]['state'] == 'Playing':
        print(f">>> Client {client_id} yeu cau thoat game.")
        game_states[client_id]['exit_requested'] = True

# --- CÁC SỰ KIỆN ADMIN (Đầy đủ) ---
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

@socketio.on('admin_get_statistics')
def handle_admin_get_statistics():
    total_users = get_total_users_count()
    game_stats = get_game_statistics_by_mode()
    
    print(f">>> Admin yeu cau thong ke: {total_users} users, stats: {game_stats}")
    
    emit('admin_statistics_data', {
        'total_users': total_users,
        'game_stats': game_stats
    })

# --- CHẠY SERVER ---
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False)
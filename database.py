# Tên file: database.py

import sqlite3
from datetime import datetime

DATABASE_FILE = "game_data.db"

def init_db():
    """
    Tạo DB và các bảng Users, GameHistory nếu chưa tồn tại.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        avatar_id INTEGER DEFAULT 0,
        created_at DATETIME NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GameHistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        game_mode TEXT NOT NULL,
        score INTEGER NOT NULL,
        timestamp DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE
    )
    """)
    
    conn.commit()
    conn.close()
    print(">>> Co so du lieu 'game_data.db' da duoc khoi tao hoac da ton tai.")

def find_or_create_user(name):
    """
    Tìm một người dùng bằng tên. Nếu không tồn tại, tạo mới.
    :return: Một dictionary chứa {'user_id': id, 'avatar_id': id}
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, avatar_id FROM Users WHERE name = ?", (name,))
    user = cursor.fetchone()
    
    if user:
        user_id = user['id']
        avatar_id = user['avatar_id']
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO Users (name, created_at, avatar_id) VALUES (?, ?, 0)", (name, timestamp))
        user_id = cursor.lastrowid
        avatar_id = 0 
        print(f">>> Da tao nguoi dung moi: {name} (ID: {user_id})")
        
    conn.commit()
    conn.close()
    return {'user_id': user_id, 'avatar_id': avatar_id}

def save_game_result(user_id, score, game_mode):
    """
    Lưu kết quả một lượt chơi và chỉ giữ lại 10 lượt gần nhất.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("INSERT INTO GameHistory (user_id, game_mode, score, timestamp) VALUES (?, ?, ?, ?)", 
                   (user_id, game_mode, score, timestamp))
    
    cursor.execute("""
        DELETE FROM GameHistory 
        WHERE id NOT IN (
            SELECT id FROM GameHistory 
            WHERE user_id = ? AND game_mode = ? 
            ORDER BY timestamp DESC 
            LIMIT 10
        ) AND user_id = ? AND game_mode = ?
    """, (user_id, game_mode, user_id, game_mode))
    
    conn.commit()
    conn.close()
    print(f">>> Da luu ket qua cho User ID: {user_id} - Diem: {score}")

def get_player_history(user_id):
    """
    Lấy lịch sử chơi của một người dùng dựa vào user_id.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT game_mode, score, timestamp FROM GameHistory WHERE user_id = ? ORDER BY game_mode, timestamp DESC", (user_id,))
    history_rows = cursor.fetchall()
    conn.close()
    return [{'mode': row['game_mode'], 'score': row['score'], 'time': row['timestamp']} for row in history_rows]

# --- CÁC HÀM DÀNH CHO ADMIN ---

def get_all_users():
    """
    Lấy danh sách tất cả người dùng (bao gồm cả avatar_id).
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, avatar_id, created_at FROM Users ORDER BY name ASC")
    users_rows = cursor.fetchall()
    conn.close()
    return [{'id': row['id'], 'name': row['name'], 'avatar_id': row['avatar_id'], 'created_at': row['created_at']} for row in users_rows]

def update_user_name(user_id, new_name):
    """
    Cập nhật tên của một người dùng.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Users SET name = ? WHERE id = ?", (new_name, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError: 
        return False
    finally:
        conn.close()

def delete_user_and_history(user_id):
    """
    Xóa một người dùng và toàn bộ lịch sử chơi của họ.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_avatar(user_id, avatar_id):
    """
    Cập nhật avatar_id cho một người dùng.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Users SET avatar_id = ? WHERE id = ?", (avatar_id, user_id))
        conn.commit()
        print(f">>> User {user_id} da cap nhat avatar thanh {avatar_id}")
        return True
    except sqlite3.Error as e:
        print(f"Lỗi khi cap nhat avatar: {e}")
        return False
    finally:
        conn.close()

# --- HÀM MỚI DÀNH CHO THỐNG KÊ ---

def get_total_users_count():
    """
    Đếm tổng số người dùng đã đăng ký.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(id) FROM Users").fetchone()[0]
    conn.close()
    return count

def get_total_games_played_count():
    """
    Đếm tổng số lượt chơi đã diễn ra trên toàn hệ thống.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(id) FROM GameHistory").fetchone()[0]
    conn.close()
    return count

# --- Chỉ chạy khi thực thi file này trực tiếp ---
if __name__ == "__main__":
    init_db()
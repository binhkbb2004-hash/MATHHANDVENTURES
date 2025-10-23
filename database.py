# Tên file: database.py (Phiên bản Admin Panel)

import sqlite3
from datetime import datetime

DATABASE_FILE = "game_data.db"

def init_db():
    """
    Tạo DB và các bảng Users, GameHistory nếu chưa tồn tại.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Bật khóa ngoại để đảm bảo liên kết dữ liệu
    cursor.execute("PRAGMA foreign_keys = ON")

    # Bảng mới để quản lý người dùng
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at DATETIME NOT NULL
    )
    """)

    # Bảng GameHistory được cập nhật để liên kết với Users
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
    print(">>> Co so du lieu da duoc khoi tao voi cau truc moi (Users & GameHistory).")

def find_or_create_user(name):
    """
    Tìm một người dùng bằng tên. Nếu không tồn tại, tạo mới.
    :return: ID của người dùng.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Thử tìm user bằng tên
    cursor.execute("SELECT id FROM Users WHERE name = ?", (name,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
    else:
        # Nếu không có, tạo user mới
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO Users (name, created_at) VALUES (?, ?)", (name, timestamp))
        user_id = cursor.lastrowid
        print(f">>> Da tao nguoi dung moi: {name} (ID: {user_id})")
        
    conn.commit()
    conn.close()
    return user_id

def save_game_result(user_id, score, game_mode):
    """
    Lưu kết quả một lượt chơi dựa vào user_id.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("INSERT INTO GameHistory (user_id, game_mode, score, timestamp) VALUES (?, ?, ?, ?)", 
                   (user_id, game_mode, score, timestamp))
    
    # Xóa các kết quả cũ, chỉ giữ lại 10 lượt mới nhất
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
    cursor = conn.cursor()
    
    cursor.execute("SELECT game_mode, score, timestamp FROM GameHistory WHERE user_id = ? ORDER BY game_mode, timestamp DESC", (user_id,))
    history = cursor.fetchall()
    conn.close()
    # Chuyển đổi định dạng để dễ dùng hơn ở Front-end
    return [{'mode': row[0], 'score': row[1], 'time': row[2]} for row in history]

# --- CÁC HÀM MỚI DÀNH CHO ADMIN ---

def get_all_users():
    """
    Lấy danh sách tất cả người dùng.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, created_at FROM Users ORDER BY name ASC")
    users = cursor.fetchall()
    conn.close()
    return [{'id': row[0], 'name': row[1], 'created_at': row[2]} for row in users]

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
    except sqlite3.IntegrityError: # Lỗi nếu tên mới đã tồn tại
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

# --- Chỉ chạy khi thực thi file này trực tiếp ---
if __name__ == "__main__":
    init_db()
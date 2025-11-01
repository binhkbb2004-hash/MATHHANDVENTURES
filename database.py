# Tên file: database.py (Phiên bản Admin Panel + Avatar)

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

    # Bảng Users: Thêm cột avatar_id
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        avatar_id INTEGER DEFAULT 0,
        created_at DATETIME NOT NULL
    )
    """)

    # Bảng GameHistory (giữ nguyên, chỉ liên kết bằng user_id)
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
    print(">>> Co so du lieu da duoc khoi tao voi cau truc moi (Users & GameHistory + Avatar).")

def find_or_create_user(name):
    """
    Tìm một người dùng bằng tên. Nếu không tồn tại, tạo mới.
    :return: Một dictionary chứa {'user_id': id, 'avatar_id': id}
    """
    conn = sqlite3.connect(DATABASE_FILE)
    # Thiết lập để trả về kết quả dạng dictionary
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Thử tìm user bằng tên
    cursor.execute("SELECT id, avatar_id FROM Users WHERE name = ?", (name,))
    user = cursor.fetchone()
    
    if user:
        user_id = user['id']
        avatar_id = user['avatar_id']
    else:
        # Nếu không có, tạo user mới
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO Users (name, created_at, avatar_id) VALUES (?, ?, 0)", (name, timestamp))
        user_id = cursor.lastrowid
        avatar_id = 0 # Avatar mặc định khi tạo mới
        print(f">>> Da tao nguoi dung moi: {name} (ID: {user_id})")
        
    conn.commit()
    conn.close()
    return {'user_id': user_id, 'avatar_id': avatar_id}

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
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT game_mode, score, timestamp FROM GameHistory WHERE user_id = ? ORDER BY game_mode, timestamp DESC", (user_id,))
    history_rows = cursor.fetchall()
    conn.close()
    # Chuyển đổi định dạng để dễ dùng hơn ở Front-end
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
    cursor.execute("PRAGMA foreign_keys = ON") # Bật khóa ngoại để xóa liên đới
    cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

# --- HÀM MỚI DÀNH CHO AVATAR ---

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

# --- Chỉ chạy khi thực thi file này trực tiếp ---
if __name__ == "__main__":
    init_db()
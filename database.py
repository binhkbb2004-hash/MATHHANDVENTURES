# Tên file: database.py

import sqlite3
from datetime import datetime

DATABASE_FILE = "game_data.db"

def init_db():
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
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT game_mode, score, timestamp FROM GameHistory WHERE user_id = ? ORDER BY game_mode, timestamp DESC", (user_id,))
    history_rows = cursor.fetchall()
    conn.close()
    return [{'mode': row['game_mode'], 'score': row['score'], 'time': row['timestamp']} for row in history_rows]

def get_all_users():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, avatar_id, created_at FROM Users ORDER BY name ASC")
    users_rows = cursor.fetchall()
    conn.close()
    return [{'id': row['id'], 'name': row['name'], 'avatar_id': row['avatar_id'], 'created_at': row['created_at']} for row in users_rows]

def update_user_name(user_id, new_name):
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
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM Users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_avatar(user_id, avatar_id):
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

# --- HÀM THỐNG KÊ ĐÃ CẬP NHẬT ---

def get_total_users_count():
    """Đếm tổng số người dùng đã đăng ký."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    count = cursor.execute("SELECT COUNT(id) FROM Users").fetchone()[0]
    conn.close()
    return count

def get_game_statistics_by_mode():
    """Đếm tổng số lượt chơi VÀ phân loại theo từng game mode."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Query để lấy số lượt chơi, nhóm theo game_mode
    cursor.execute("SELECT game_mode, COUNT(id) FROM GameHistory GROUP BY game_mode")
    stats = cursor.fetchall() # Trả về list, ví dụ: [('Math', 5), ('Counting', 2)]
    conn.close()
    
    # Chuyển đổi sang dạng dictionary (từ điển) và đặt giá trị mặc định là 0
    stats_dict = {
        'Math': 0,
        'Counting': 0,
        'Obstacle': 0
    }
    # Cập nhật số đếm từ database
    for mode, count in stats:
        if mode in stats_dict:
            stats_dict[mode] = count
            
    return stats_dict

if __name__ == "__main__":
    init_db()
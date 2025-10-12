# Tên file: database.py

import sqlite3
from datetime import datetime

DATABASE_FILE = "game_data.db" # Tên file database

def init_db():
    """
    Hàm này sẽ tạo file database và bảng GameHistory nếu chúng chưa tồn tại.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Bảng để lưu lịch sử các lần chơi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS GameHistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        game_mode TEXT NOT NULL,
        score INTEGER NOT NULL,
        timestamp DATETIME NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print(">>> Co so du lieu 'game_data.db' da duoc khoi tao hoac da ton tai.")

def save_game_result(name, score, game_mode):
    """
    Lưu kết quả một lượt chơi và chỉ giữ lại 5 lượt gần nhất cho người chơi đó ở chế độ đó.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Thêm kết quả mới vào DB
    cursor.execute("INSERT INTO GameHistory (name, game_mode, score, timestamp) VALUES (?, ?, ?, ?)", 
                   (name, game_mode, score, timestamp))
    
    # 2. Xóa các kết quả cũ hơn, chỉ giữ lại 5 lượt mới nhất
    cursor.execute("""
        DELETE FROM GameHistory 
        WHERE id NOT IN (
            SELECT id FROM GameHistory 
            WHERE name = ? AND game_mode = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        ) AND name = ? AND game_mode = ?
    """, (name, game_mode, name, game_mode))
    
    conn.commit()
    conn.close()
    print(f">>> Da luu ket qua cho: {name} - Che do: {game_mode} - Diem: {score}")

def get_player_history(name):
    """
    Lấy toàn bộ lịch sử chơi (tối đa 5 lượt cho mỗi chế độ) của một người chơi.
    :param name: Tên người chơi cần lấy lịch sử.
    :return: Một danh sách các tuple chứa (game_mode, score).
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Lấy tất cả các lượt chơi của người đó, sắp xếp theo chế độ và thời gian mới nhất
    cursor.execute("SELECT game_mode, score FROM GameHistory WHERE name = ? ORDER BY game_mode, timestamp DESC", (name,))
    
    history = cursor.fetchall()
    
    conn.close()
    return history

# --- Phần code này chỉ chạy khi bạn thực thi trực tiếp file database.py ---
# Mục đích là để khởi tạo file database lần đầu tiên.
if __name__ == "__main__":
    print("--- Khoi tao Co so du lieu ---")
    init_db()
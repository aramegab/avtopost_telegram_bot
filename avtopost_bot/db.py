import sqlite3
from datetime import datetime

class UsersDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                        (id INTEGER PRIMARY KEY, telegram_id INT, username TEXT, avatar TEXT, registration_time TEXT, is_moder INT)''')
        self.conn.commit()
    
    def add_user(self,telegram_id,username, avatar, resgistration_time):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO users (telegram_id, username, avatar, registration_time, is_moder) VALUES (?,?,?,?,?)', (telegram_id,username, avatar, resgistration_time, 0,))
        self.conn.commit()
    
    def add_moder(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_moder = ? WHERE telegram_id = ?',(1, telegram_id,))
        self.conn.commit()
    
    def get_user(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?",(telegram_id,))
        self.conn.commit()
        return cursor.fetchone()

    def delete_moder(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_moder = ? WHERE telegram_id = ?',(0, telegram_id,))
        self.conn.commit()
    
    def get_moderators(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE is_moder = ?",(1,))
        self.conn.commit()
        return cursor.fetchall()

    def check_client_in_db(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM users WHERE telegram_id = ?''', (telegram_id,))
        self.conn.commit()
        if cursor.fetchone() is None:
            return False
        else:
            return True
    
    def get_all_ads(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ads WHERE user_id = ? AND status=?",(telegram_id,'Одобрен'))
        self.conn.commit()
        return cursor.fetchone()[0]
    
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT telegram_id FROM users')
        self.conn.commit()
        return cursor.fetchall()
    
    def get_all_users_count(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT count(telegram_id) FROM users')
        self.conn.commit()
        return cursor.fetchone()[0]
    
    def get_ads_pending(self,telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ads WHERE user_id = ? AND status=?",(telegram_id,'Ожидание'))
        self.conn.commit()
        return cursor.fetchone()[0]

class AdDB:
    def __init__(self):
        self.conn = sqlite3.connect('database/data.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS ads
                        (id INTEGER PRIMARY KEY, user_id INT, text TEXT, photo_id TEXT, status TEXT, created_at TEXT)''')
        self.conn.commit()
    
    def add_ad(self, user_id, text, photo_id, status):
        cursor = self.conn.cursor()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('INSERT INTO ads (user_id, text, photo_id, status, created_at) VALUES (?,?,?,?,?)', (user_id, text, photo_id, status, now))
        self.conn.commit()
    
    def get_ads_for_moderation(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ads WHERE status = 'Ожидание'")
        self.conn.commit()
        return cursor.fetchall()
    
    def get_ad(self, ad_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM ads WHERE id = ?', (ad_id,))
        self.conn.commit()
        return cursor.fetchone()

    def get_ad_by_tg_id(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM ads WHERE user_id = ? AND status=?', (telegram_id,'Ожидание',))
        self.conn.commit()
        return cursor.fetchone()

    def get_ad_by_photo_id(self, photo_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM ads WHERE photo_id = ?', (photo_id,))
        self.conn.commit()
        return cursor.fetchone()

    def update_ad_status(self, ad_id, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE ads SET status = ? WHERE id = ?", (status, ad_id,))
        self.conn.commit()
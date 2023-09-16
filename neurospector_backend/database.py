import sqlite3


class Database:
    def __init__(self, db_name='database.sqlite'):
        self.connection = sqlite3.connect(db_name)
        self.connection.row_factory = sqlite3.Row

    def __del__(self):
        self.connection.close()

    def initialize_database(self):
        table_create_expressions = [
            '''
            CREATE TABLE "detections" ("uid" TEXT NOT NULL UNIQUE, "photo_uid" TEXT NOT NULL, "angle" REAL NOT NULL,
            "x1" INTEGER NOT NULL, "x2" INTEGER NOT NULL, "y1" INTEGER NOT NULL, "y2" INTEGER NOT NULL, 
            "lamp_count" INTEGER NOT NULL, PRIMARY KEY("uid"))
            ''',
            '''
            CREATE TABLE "lightning_objects" ("sg_uid" TEXT NOT NULL UNIQUE, "latitude" REAL NOT NULL, 
            "longitude" REAL NOT NULL, "lamp_count" INTEGER NOT NULL, "additional" BLOB, PRIMARY KEY("sg_uid"))
            ''',
            '''
            CREATE TABLE "locations" ("photo_uid" TEXT NOT NULL, "longitude" REAL NOT NULL, "latitude" REAL NOT NULL, 
            "speed" REAL NOT NULL, "course" REAL NOT NULL, "timestamp" REAL, PRIMARY KEY("photo_uid"))
            ''',
            '''
            CREATE TABLE "photos" ("uid" TEXT NOT NULL UNIQUE, "file_path" TEXT NOT NULL, "timestamp" REAL NOT NULL,
            "processed" INTEGER NOT NULL DEFAULT 0, PRIMARY KEY("uid"))
            ''',
            '''
            CREATE TABLE "vectors" ("uid" TEXT NOT NULL UNIQUE, "photo_uid" TEXT NOT NULL, "location_uid" TEXT,
            "detection_uid" TEXT NOT NULL, PRIMARY KEY("uid"))
            '''
        ]
        cursor = self.connection.cursor()
        for expression in table_create_expressions:
            cursor.execute(expression)
        self.connection.commit()
        cursor.close()
        return

    def get_photo(self, uid):
        sql = "SELECT * from photos WHERE uid LIKE ?"
        params = (uid,)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        ret = cursor.fetchall()
        cursor.close()
        return ret

    def get_unprocessed_photos(self):
        sql = "SELECT * from photos WHERE processed LIKE 0"
        cursor = self.connection.cursor()
        cursor.execute(sql)
        ret = cursor.fetchall()
        cursor.close()
        return ret

    def get_location(self, photo_uid):
        sql = "SELECT * from locations WHERE photo_uid LIKE ?"
        params = (photo_uid,)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        ret = cursor.fetchall()
        cursor.close()
        return ret

    def add_photo(self, uid, file_path, timestamp):
        sql = "INSERT into photos (uid, file_path, timestamp) VALUES (?, ?, ?)"
        params = (uid, file_path, timestamp)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        cursor.close()
        return

    def add_location_to_photo(self, photo_uid, location):
        sql = ("INSERT into locations (photo_uid, longitude, latitude, speed, course, timestamp) "
               "VALUES (?, ?, ?, ?, ?, ?)")
        params = (
            photo_uid, location["longitude"], location["latitude"],
            location["speed"], location["course"], location["timestamp"]
        )
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        cursor.close()
        return

    def add_detection(self, uid, photo_uid, angle, x1, x2, y1, y2, lamp_count):
        sql = "INSERT into detections (uid, photo_uid, angle, x1, x2, y1, y2, lamp_count) VALUES (?,?,?,?,?,?,?,?)"
        params = (uid, photo_uid, angle, x1, x2, y1, y2, lamp_count)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        cursor.close()
        return

    def mark_photo_as_done(self, photo_uid):
        sql = "UPDATE photos SET processed = 1 WHERE uid LIKE ?"
        params = (photo_uid,)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        cursor.close()
        return

    def add_vector(self, uid, photo_uid, detection_uid):
        sql = "INSERT INTO vectors (uid, photo_uid, detection_uid) VALUES (?, ?, ?)"
        params = (uid, photo_uid, detection_uid)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        self.connection.commit()
        cursor.close()
        return

    def get_vector(self, vector_uid):
        sql = "SELECT * from vectors WHERE uid LIKE ?"
        params = (vector_uid,)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        ret = cursor.fetchall()
        cursor.close()
        return ret

    def get_vectors(self):
        sql = "SELECT * from vectors"
        cursor = self.connection.cursor()
        cursor.execute(sql)
        ret = cursor.fetchall()
        cursor.close()
        return ret

    def get_detection(self, detection_uid):
        sql = "SELECT * from detections WHERE uid LIKE ?"
        params = (detection_uid,)
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        ret = cursor.fetchall()
        cursor.close()
        return ret

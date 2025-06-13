from datetime import datetime

from clients.db_client import SQLiteClient


class UserActions:
    def __init__(self, database_client: SQLiteClient):
        self.database_client = database_client

    def setup(self):
        self.database_client.create_conn()

    def shutdown(self):
        self.database_client.close_conn()

    # ---------------------------------------------------------
    # SETTERS
    NEW_USER = """
        INSERT INTO USERS (CHAT_ID, USER_ID, TITLE, USERNAME) VALUES (?, ?, ?, ?);
    """

    def set_new_user(self, chat_id: int, user_id: int, title: str, username: str):
        self.database_client.execute_command(self.NEW_USER, (chat_id, user_id, title, username))

    # UPDATE_EXIST ---------------------------------------------------------
    UPDATE_EXIST_USER = """ UPDATE USERS SET TITLE = ?, USERNAME = ? WHERE CHAT_ID = ? AND USER_ID = ?; """
    UPDATE_EXIST_REMIND = """ UPDATE REMIND SET TITLE = ?, USERNAME = ? WHERE CHAT_ID = ? AND USER_ID = ?; """

    def update_exist_user(self, chat_id: int, user_id: int, title: str, username: str):
        self.database_client.execute_command(self.UPDATE_EXIST_USER, (title, username, chat_id, user_id))
        self.database_client.execute_command(self.UPDATE_EXIST_REMIND, (title, username, chat_id, user_id))

    # UPDATE_TITLE ---------------------------------------------------------
    UPDATE_TITLE_USER = """ UPDATE USERS SET TITLE = ? WHERE CHAT_ID = ?; """
    UPDATE_TITLE_REMIND = """ UPDATE REMIND SET TITLE = ? WHERE CHAT_ID = ?; """

    def update_title_group(self, chat_id: int, title: str):
        self.database_client.execute_command(self.UPDATE_TITLE_USER, (title, chat_id))
        self.database_client.execute_command(self.UPDATE_TITLE_REMIND, (title, chat_id))

    # NEW ---------------------------------------------------------
    DELETE_EVENT = """ DELETE FROM REMIND WHERE USER_ID = ? AND STATUS in ('NEW', 'TEXT', 'PERIOD', 'FACTOR'); """

    INSERT_NEW_EVENT = """ INSERT INTO REMIND (CHAT_ID, USER_ID, TITLE, USERNAME, STATUS) 
                SELECT CHAT_ID, USER_ID, TITLE, USERNAME, 'NEW' FROM USERS WHERE CHAT_ID = ? AND USER_ID = ?; """

    UPDATE_EDIT = """ UPDATE REMIND SET EDIT = NULL 
                    WHERE EDIT in ('EDIT_DATE', 'EDIT_PERIOD', 'EDIT_TEXT', 'PERIOD', 'FACTOR') AND USER_ID = ?; """

    def set_new_event(self, chat_id: int, user_id: int):
        self.database_client.execute_command(self.DELETE_EVENT, (user_id,))
        self.database_client.execute_command(self.INSERT_NEW_EVENT, (chat_id, user_id))

    # DELETE ---------------------------------------------------------
    def delete_update_event(self, user_id: int):
        self.database_client.execute_command(self.DELETE_EVENT, (user_id,))
        self.database_client.execute_command(self.UPDATE_EDIT, (user_id,))

    # ---------------------------------------------------------
    DELETE_EVENT_BY_ID = """ DELETE FROM REMIND WHERE ID = ?; """

    def delete_event_by_id(self, db_id: int):
        self.database_client.execute_command(self.DELETE_EVENT_BY_ID, (db_id,))

    # ---------------------------------------------------------
    DELETE_ALL_BY_USER_ID = """ DELETE FROM REMIND WHERE USER_ID = ?; """

    def delete_all_by_user_id(self, user_id: int):
        self.database_client.execute_command(self.DELETE_ALL_BY_USER_ID, (user_id,))

    # ---------------------------------------------------------
    DELETE_ALL_BY_CHAT_ID = """ DELETE FROM REMIND WHERE CHAT_ID = ?; """

    def delete_all_by_chat_id(self, chat_id: int):
        self.database_client.execute_command(self.DELETE_ALL_BY_CHAT_ID, (chat_id,))

    # SET -- TEXT -------------------------------------------------------
    SET_TEXT = """ UPDATE REMIND SET MESSAGE = ?, STATUS = 'TEXT' WHERE ID = ?; """

    def set_text(self, message: str, db_id: int):
        self.database_client.execute_command(self.SET_TEXT, (message, db_id))

    # UPDATE -- TEXT -------------------------------------------------------
    EDIT_TEXT = """ UPDATE REMIND SET MESSAGE = ?, STATUS = 'ACTIVE', EDIT = NULL WHERE ID = ?; """

    def set_edit_text(self, message: str, db_id: int):
        self.database_client.execute_command(self.EDIT_TEXT, (message, db_id))

    # UPDATE -- CHAT_ID SUPERGROUP--------------------------------------------
    EDIT_REMIND_CHAT_ID = """ UPDATE REMIND SET CHAT_ID = ? WHERE CHAT_ID = ?; """
    EDIT_USERS_CHAT_ID = """ UPDATE USERS SET CHAT_ID = ? WHERE CHAT_ID = ?; """

    def edit_group_chat_id(self, new_chat_id: int, old_chat_id: int):
        self.database_client.execute_command(self.EDIT_REMIND_CHAT_ID, (new_chat_id, old_chat_id))
        self.database_client.execute_command(self.EDIT_USERS_CHAT_ID, (new_chat_id, old_chat_id))

    # PERIOD ---------------------------------------------------------
    SET_DATE = """ UPDATE REMIND SET LAST_UP = ?, NEXT_UP = ?, STATUS = 'PERIOD' WHERE ID = ?; """

    def set_date(self, last_up: int, next_up: datetime, db_id: int):
        self.database_client.execute_command(self.SET_DATE, (last_up, next_up, db_id))

    # ---------------------------------------------------------
    EDIT_DATE = """ UPDATE REMIND SET LAST_UP = ?, NEXT_UP = ?, STATUS = 'ACTIVE', EDIT = NULL WHERE ID = ?; """

    def set_edit_date(self, last_up: int, next_up: datetime, db_id: int):
        self.database_client.execute_command(self.EDIT_DATE, (last_up, next_up, db_id))

    # FACTOR ---------------------------------------------------------
    SET_PERIOD = """ UPDATE REMIND SET PERIOD = ?, 
                        EDIT = CASE WHEN STATUS = 'PAUSE' THEN 'EDIT_FACTOR' END,
                        STATUS = CASE WHEN STATUS = 'PERIOD' THEN 'FACTOR' ELSE 'PAUSE' END
                        WHERE ID = ?; """

    def set_period(self, period: str, db_id: int):
        self.database_client.execute_command(self.SET_PERIOD, (period, db_id))

    # ACTIVE ---------------------------------------------------------
    SET_ACTIVE = """ UPDATE REMIND SET STATUS = 'ACTIVE', EDIT = NULL, FACTOR = ? WHERE ID = ?; """

    def set_active(self, factor: int, db_id: int):
        self.database_client.execute_command(self.SET_ACTIVE, (factor, db_id))

    # ---------------------------------------------------------
    SET_STATUS_UPDATE = """ UPDATE REMIND SET LAST_UP = ?, NEXT_UP = ? WHERE ID = ?; """

    def set_status_update(self, last_up: datetime, next_up: datetime, db_id: int):
        self.database_client.execute_command(self.SET_STATUS_UPDATE, (last_up, next_up, db_id))

    # ---------------------------------------------------------
    SET_LAST_MESS_ID = """ UPDATE USERS SET MESS_ID = ? WHERE USER_ID = ?; """

    def set_last_mess_id(self, mess_id: int, user_id: int):
        self.database_client.execute_command(self.SET_LAST_MESS_ID, (mess_id, user_id))

    # ---------------------------------------------------------
    SET_STATUS_BY_ID = """ UPDATE REMIND SET STATUS = ?, EDIT = ? WHERE ID = ?; """

    def set_status_by_id(self, status: str, edit: str, db_id: int):
        self.database_client.execute_command(self.SET_STATUS_BY_ID, (status, edit, db_id))

    # ---------------------------------------------------------
    SET_STATUS_BY_CHAT_ID = """ UPDATE REMIND SET STATUS = ?, EDIT = ? WHERE CHAT_ID = ?; """

    def set_status_by_chat_id(self, status: str, edit: str, chat_id: int):
        self.database_client.execute_command(self.SET_STATUS_BY_CHAT_ID, (status, edit, chat_id))

    # GETTERS --
    # SELECT ------------------------------------------
    GET_GROUPS = """ SELECT CHAT_ID, TITLE FROM USERS WHERE USER_ID = ?; """

    def get_groups(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_GROUPS, (user_id,))
        return result if result else []

    # ---------------------------------------------------------
    GET_ACTUAL_QUEUE = """
        SELECT ID, CHAT_ID, LAST_UP, NEXT_UP, PERIOD, FACTOR, MESSAGE FROM REMIND WHERE NEXT_UP = 
        (SELECT MIN(NEXT_UP) FROM REMIND WHERE NEXT_UP > datetime('now', 'localtime') AND STATUS = 'ACTIVE')  
        AND STATUS = 'ACTIVE'; """

    def get_actual_queue(self):
        return self.database_client.execute_select_command(self.GET_ACTUAL_QUEUE, ())

    # ---------------------------------------------------------
    GET_UPDATE_QUEUE = """
        SELECT ID, CHAT_ID, LAST_UP, NEXT_UP, PERIOD, FACTOR, MESSAGE 
        FROM REMIND WHERE NEXT_UP < datetime('now', 'localtime') AND STATUS = 'ACTIVE';
    """

    def get_update_queue(self):
        return self.database_client.execute_select_command(self.GET_UPDATE_QUEUE, ())

    # ---------------------------------------------------------
    GET_LAST_EDIT_STATUS = """ SELECT MAX(ID), STATUS FROM REMIND 
                                WHERE STATUS IN ('NEW', 'TEXT', 'FACTOR', 'PAUSE') AND USER_ID = ?; """

    def get_last_edit_status(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_LAST_EDIT_STATUS, (user_id,))
        return result

    GET_LAST_SUB_STEP = """ SELECT EDIT FROM REMIND WHERE ID = ?; """

    def get_sub_step(self, db_id: int):
        return self.database_client.execute_select_command(self.GET_LAST_SUB_STEP, (db_id,))[0][0]

    # ---------------------------------------------------------
    GET_ALL_ACTIVE = """ SELECT ID, MESSAGE, NEXT_UP, STATUS, EDIT FROM REMIND 
                WHERE STATUS in ('ACTIVE', 'PAUSE', 'ERROR') AND USER_ID = ?; """

    def get_all_active(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_ALL_ACTIVE, (user_id,))
        return result if result else []

    # Проверка на повторное создание пользователя --------------
    GET_CHAT_ID = """ SELECT CHAT_ID FROM USERS WHERE USER_ID = ? """

    def check_create_user(self, user_id: int, chat_id: int):
        result = self.database_client.execute_select_command(self.GET_CHAT_ID, (user_id,))
        groups_list = [i[0] for i in result]
        return False if chat_id in groups_list else True

    # ---------------------------------------------------------
    GET_MAX_MESS_ID = """ SELECT MAX(MESS_ID) FROM USERS WHERE USER_ID = ?; """

    def get_last_mess_id(self, user_id: int):
        return self.database_client.execute_select_command(self.GET_MAX_MESS_ID, (user_id,))[0][0]

    # ---------------------------------------------------------
    GET_COUNT_MESS = """ SELECT COUNT(ID) FROM REMIND WHERE STATUS='ACTIVE'; """

    def get_count_mess(self):
        return self.database_client.execute_select_command(self.GET_COUNT_MESS, ())[0][0]

    # ---------------------------------------------------------
    GET_ERROR_MESS = """ SELECT COUNT(ID) FROM REMIND WHERE STATUS='ERROR'; """

    def get_error_mess(self):
        return self.database_client.execute_select_command(self.GET_ERROR_MESS, ())[0][0]

    # ---------------------------------------------------------
    GET_ALL_USERS = """ SELECT DISTINCT(USERNAME) FROM USERS; """

    def get_all_users(self):
        users = self.database_client.execute_select_command(self.GET_ALL_USERS, ())
        result = []
        for user in users:
            username = user[0]
            if username.isdigit():
                result.append(f'<a href="https://t.me/@id{username}">{username}</a>')
            else:
                result.append(f'@{username}')
        return result

    # ---------------------------------------------------------
    GET_ACTIVE_USERS = """ SELECT COUNT(DISTINCT(USERNAME)) FROM REMIND; """

    def get_active_users(self):
        return self.database_client.execute_select_command(self.GET_ACTIVE_USERS, ())[0][0]

    # ---------------------------------------------------------
    GET_MESSAGE_BY_ID = """ SELECT * FROM REMIND WHERE ID =?; """

    def get_message_by_id(self, db_id: int):
        result = self.database_client.execute_select_command(self.GET_MESSAGE_BY_ID, (db_id,))
        return result[0] if result else 0
    # ---------------------------------------------------------


# if __name__ == '__main__':
#     user_action = UserActions(SQLiteClient('db/remind.db'))
#     user_action.setup()
#
#     user_action.set_edit_chat_id(6826849219, 6826849219)

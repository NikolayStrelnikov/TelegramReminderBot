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

    # NEW ---------------------------------------------------------
    INSERT_NEW_EVENT = """
        INSERT INTO REMIND (CHAT_ID, USER_ID, TITLE, USERNAME, STATUS) 
        SELECT CHAT_ID, USER_ID, TITLE, USERNAME, 'NEW' FROM USERS WHERE CHAT_ID = ? AND USER_ID = ?;
    """

    def set_new_event(self, chat_id: int, user_id: int):
        self.database_client.execute_command(self.INSERT_NEW_EVENT, (chat_id, user_id))

    # DELETE ---------------------------------------------------------
    DELETE_EVENT = """
        DELETE FROM REMIND WHERE USER_ID = ? AND STATUS in ('NEW', 'TEXT', 'PERIOD', 'FACTOR');
    """

    def delete_event(self, user_id: int):
        self.database_client.execute_command(self.DELETE_EVENT, (user_id,))

    # ---------------------------------------------------------
    DELETE_EVENT_BY_ID = """ DELETE FROM REMIND WHERE ID = ?; """

    def delete_event_by_id(self, base_id: int):
        self.database_client.execute_command(self.DELETE_EVENT_BY_ID, (base_id,))

    # ---------------------------------------------------------
    DELETE_ALL_BY_USER_ID = """ DELETE FROM REMIND WHERE USER_ID = ?; """

    def delete_all_by_user_id(self, user_id: int):
        self.database_client.execute_command(self.DELETE_ALL_BY_USER_ID, (user_id,))

    # ---------------------------------------------------------
    DELETE_ALL_BY_CHAT_ID = """ DELETE FROM REMIND WHERE CHAT_ID = ?; """

    def delete_all_by_chat_id(self, chat_id: int):
        self.database_client.execute_command(self.DELETE_ALL_BY_CHAT_ID, (chat_id,))

    # UPDATE -- TEXT -------------------------------------------------------
    SET_TEXT = """ UPDATE REMIND SET MESSAGE = ?, STATUS = 'TEXT' WHERE STATUS = 'NEW' AND USER_ID = ?; """

    def set_text(self, message: str, user_id: int):
        self.database_client.execute_command(self.SET_TEXT, (message, user_id))

    # PERIOD ---------------------------------------------------------
    SET_DATE = """
        UPDATE REMIND SET LAST_UP = ?, NEXT_UP = ?, STATUS = 'PERIOD' WHERE STATUS = 'TEXT' AND USER_ID = ?;
    """

    def set_date(self, last_up: int, next_up: datetime, user_id: int):
        self.database_client.execute_command(self.SET_DATE, (last_up, next_up, user_id))

    # FACTOR ---------------------------------------------------------
    SET_PERIOD = """ UPDATE REMIND SET PERIOD = ?, STATUS = 'FACTOR' WHERE STATUS = 'PERIOD' AND USER_ID = ?; """

    def set_period(self, period: str, user_id: int):
        self.database_client.execute_command(self.SET_PERIOD, (period, user_id))

    # ACTIVE ---------------------------------------------------------
    SET_ACTIVE = """ UPDATE REMIND SET STATUS = 'ACTIVE', FACTOR = ? WHERE STATUS = 'FACTOR' AND USER_ID = ?; """

    def set_active(self, factor: int, user_id: int):
        self.database_client.execute_command(self.SET_ACTIVE, (factor, user_id))

    # ---------------------------------------------------------
    SET_STATUS_UPDATE = """ UPDATE REMIND SET LAST_UP = ?, NEXT_UP = ? WHERE ID = ?; """

    def set_status_update(self, last_up: datetime, next_up: datetime, base_id: int):
        self.database_client.execute_command(self.SET_STATUS_UPDATE, (last_up, next_up, base_id))

    # ---------------------------------------------------------
    SET_LAST_MESS_ID = """ UPDATE USERS SET MESS_ID = ? WHERE USER_ID = ?; """

    def set_last_mess_id(self, mess_id: int, user_id: int):
        self.database_client.execute_command(self.SET_LAST_MESS_ID, (mess_id, user_id))

    # GETTERS -- SELECT ------------------------------------------
    GET_GROUPS = """ SELECT CHAT_ID, TITLE FROM USERS WHERE USER_ID = ?; """

    def get_groups(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_GROUPS, (user_id,))
        return result if result else []

    # ---------------------------------------------------------
    GET_ACTUAL_QUEUE = """
        SELECT ID, CHAT_ID, LAST_UP, NEXT_UP, PERIOD, FACTOR, MESSAGE FROM REMIND WHERE NEXT_UP = 
        (SELECT MIN(NEXT_UP) FROM REMIND WHERE NEXT_UP > datetime('now', 'localtime') AND STATUS = 'ACTIVE'); """

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
    GET_CURRENT_STATUS = """ SELECT MAX(ID), STATUS FROM REMIND WHERE USER_ID = ?; """

    def get_current_status(self, user_id: int):
        return self.database_client.execute_select_command(self.GET_CURRENT_STATUS, (user_id,))[0][1]

    # ---------------------------------------------------------
    GET_PERIOD = """ SELECT PERIOD FROM REMIND WHERE STATUS = 'FACTOR' AND USER_ID = ?; """

    def get_period(self, user_id: int):
        return self.database_client.execute_select_command(self.GET_PERIOD, (user_id,))[0][0]

    # ---------------------------------------------------------
    GET_ALL_ACTIVE = """ SELECT ID, MESSAGE FROM REMIND WHERE STATUS = 'ACTIVE' AND USER_ID = ?; """

    def get_all_active(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_ALL_ACTIVE, (user_id,))
        return result if result else []

    # ---------------------------------------------------------
    GET_CHAT_ID = """ SELECT CHAT_ID FROM USERS WHERE USER_ID = ? """

    def create_new(self, user_id: int, chat_id: int):
        result = self.database_client.execute_select_command(self.GET_CHAT_ID, (user_id,))
        groups_list = [i[0] for i in result]
        return False if chat_id in groups_list else True

    # ---------------------------------------------------------
    GET_LAST_MESS_ID = """ SELECT MAX(MESS_ID) FROM USERS WHERE USER_ID = ?; """

    def get_last_mess_id(self, user_id: int):
        return self.database_client.execute_select_command(self.GET_LAST_MESS_ID, (user_id,))[0][0]

    # ---------------------------------------------------------
    GET_COUNT_MESS = """ SELECT COUNT(ID) FROM REMIND WHERE STATUS='ACTIVE'; """

    def get_count_mess(self):
        return self.database_client.execute_select_command(self.GET_COUNT_MESS, ())[0][0]

    # ---------------------------------------------------------
    GET_ALL_USERS = """ SELECT DISTINCT(USERNAME) FROM USERS; """

    def get_all_users(self):
        result = self.database_client.execute_select_command(self.GET_ALL_USERS, ())
        users = [f'@{item[0]}' for item in result]
        return users

    # ---------------------------------------------------------
    GET_ACTIVE_USERS = """ SELECT COUNT(DISTINCT(USERNAME)) FROM REMIND; """

    def get_active_users(self):
        return self.database_client.execute_select_command(self.GET_ACTIVE_USERS, ())[0][0]
    # ---------------------------------------------------------


# if __name__ == '__main__':
#     user_action = UserActions(SQLiteClient('db/remind.db'))
#     user_action.setup()
#     print(
#         user_action.get_active_users()
#     )

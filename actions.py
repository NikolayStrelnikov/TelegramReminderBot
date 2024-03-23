from clients.db_client import SQLiteClient
from datetime import datetime


class UserActions:
    # ---------------------------------------------------------
    # SETTERS INSERT
    INSERT_REGISTER = """
        INSERT INTO reminders (CHAT_ID, USER_ID, USERNAME, STATUS, TITLE) VALUES (?, ?, ?, ?, ?);
    """

    INSERT_EVENT = """
        INSERT INTO reminders (CHAT_ID, USER_ID, TITLE, USERNAME, STATUS) 
        SELECT CHAT_ID, USER_ID, TITLE, USERNAME, 'NEW' FROM reminders WHERE STATUS = 'REGISTER' AND CHAT_ID = ?;
    """

    # SETTERS DELETE
    DELETE_EVENT = """
        DELETE FROM reminders WHERE USER_ID = ? AND STATUS in ('NEW', 'TEXT', 'TIME', 'PERIOD', 'FACTOR');
    """

    DELETE_EVENT_BY_ID = """
        DELETE FROM reminders WHERE ID = ?;
    """

    # SETTERS UPDATE
    SET_DATE = """
        UPDATE reminders SET LAST_UP = ?, NEXT_UP = ?, STATUS = 'PERIOD' WHERE STATUS = 'TEXT' AND USER_ID = ?;
    """
    SET_PERIOD = """
        UPDATE reminders SET PERIOD = ?, STATUS = 'FACTOR' WHERE STATUS = 'PERIOD' AND USER_ID = ?;
    """

    SET_TIME = """
        UPDATE reminders SET STATUS = 'PERIOD' WHERE STATUS = 'TIME' AND USER_ID = ?;
    """

    SET_ACTIVE = """
        UPDATE reminders SET STATUS = 'ACTIVE', FACTOR = ? WHERE STATUS = 'FACTOR' AND USER_ID = ?;
    """

    SET_REMIND = """
        UPDATE reminders SET MESSAGE = ?, STATUS = 'TEXT' WHERE STATUS = 'NEW' AND USER_ID = ?;
    """

    SET_STATUS_UPDATE = """
        UPDATE reminders SET LAST_UP = ?, NEXT_UP = ? WHERE ID = ?;
    """

    # ---------------------------------------------------------
    # GETTERS
    GET_GROUPS = """
        SELECT CHAT_ID, TITLE FROM reminders WHERE STATUS = 'REGISTER' AND USER_ID = ?;
    """

    GET_PERIOD = """
        SELECT PERIOD FROM reminders WHERE STATUS = 'FACTOR' AND USER_ID = ?;
    """

    GET_ALL_ACTIVE = """
        SELECT ID, MESSAGE FROM reminders WHERE STATUS = 'ACTIVE' AND USER_ID = ?;
    """

    GET_ALL_COUNT_STATUS = """
        SELECT count(*) FROM reminders WHERE USER_ID = ? AND STATUS in ('NEW', 'TEXT', 'TIME', 'PERIOD', 'FACTOR' );
    """

    GET_COUNT_STATUS = """
        SELECT count(*) FROM reminders WHERE USER_ID = ? AND STATUS = ?;
    """

    GET_ACTUAL_QUEUE = """
        SELECT ID, CHAT_ID, LAST_UP, NEXT_UP, PERIOD, FACTOR, MESSAGE 
        FROM reminders WHERE NEXT_UP = (
        SELECT MIN(NEXT_UP) FROM reminders WHERE NEXT_UP > datetime('now', 'localtime') AND STATUS = 'ACTIVE'
        ) AND STATUS = 'ACTIVE';
    """

    GET_UPDATE_QUEUE = """
        SELECT ID, CHAT_ID, LAST_UP, NEXT_UP, PERIOD, FACTOR, MESSAGE 
        FROM reminders WHERE NEXT_UP < datetime('now', 'localtime') AND STATUS = 'ACTIVE';
    """

    GET_CHAT_ID = """
        SELECT CHAT_ID FROM reminders WHERE STATUS = ? AND USER_ID = ?
    """

    def __init__(self, database_client: SQLiteClient):
        self.database_client = database_client

    def setup(self):
        self.database_client.create_conn()

    def shutdown(self):
        self.database_client.close_conn()

    # ---------------------------------------------------------
    # SETTERS
    def set_register(self, chat_id: int, user_id: int, username: str, status: str, title: str):
        self.database_client.execute_command(self.INSERT_REGISTER, (chat_id, user_id, username, status, title))

    def set_new_event(self, chat_id: int):
        self.database_client.execute_command(self.INSERT_EVENT, (chat_id,))

    def delete_event(self, user_id: int):
        self.database_client.execute_command(self.DELETE_EVENT, (user_id,))

    def delete_event_by_id(self, base_id: int):
        self.database_client.execute_command(self.DELETE_EVENT_BY_ID, (base_id,))

    def set_date(self, last_up: str, next_up: datetime, user_id: int):
        self.database_client.execute_command(self.SET_DATE, (last_up, next_up, user_id))

    def set_period(self, period: str, user_id: int):
        self.database_client.execute_command(self.SET_PERIOD, (period, user_id))

    def set_remind(self, message: str, user_id: int):
        self.database_client.execute_command(self.SET_REMIND, (message, user_id))

    def set_status_update(self, last_up: datetime, next_up: datetime, base_id: int):
        self.database_client.execute_command(self.SET_STATUS_UPDATE, (last_up, next_up, base_id))

    def set_time(self, user_id: int):
        self.database_client.execute_command(self.SET_TIME, (user_id,))

    def set_active(self, factor: str, user_id: int):
        self.database_client.execute_command(self.SET_ACTIVE, (factor, user_id))

    # ---------------------------------------------------------
    # GETTERS
    def get_groups(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_GROUPS, (user_id,))
        return result if result else []

    def get_actual_queue(self):
        return self.database_client.execute_select_command(self.GET_ACTUAL_QUEUE, ())

    def get_update_queue(self):
        return self.database_client.execute_select_command(self.GET_UPDATE_QUEUE, ())

    def get_count_status(self, user_id: int, status: str):
        return self.database_client.execute_select_command(self.GET_COUNT_STATUS, (user_id, status))[0][0]

    def get_period(self, user_id: int):
        return self.database_client.execute_select_command(self.GET_PERIOD, (user_id,))[0][0]

    def get_all_count_status(self, user_id: int):
        return self.database_client.execute_select_command(self.GET_ALL_COUNT_STATUS, (user_id,))[0][0]

    def get_all_active(self, user_id: int):
        result = self.database_client.execute_select_command(self.GET_ALL_ACTIVE, (user_id,))
        return result if result else []

    def create_new(self, status: str, user_id: int, chat_id: int):
        result = self.database_client.execute_select_command(self.GET_CHAT_ID, (status, user_id))
        groups_list = [i[0] for i in result]
        return False if chat_id in groups_list else True

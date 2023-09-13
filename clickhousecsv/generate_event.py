import datetime
import time
import uuid
from copy import deepcopy

from sqlalchemy import Sequence

from app.database import SessionLocalPostgres, session_scope
from app.models.audit import AuditCmd, AuditFile, AuditGraphic, AuditSQL

audit_cmd_tmp = {
    "server_name": "10.10.1.94",
    "client_user": "admin",
    "id": 1,
    "department_id": 3,
    "client_name": "admin",
    "cmdline": "ls",
    "event_time": 1611299218972,
    "client_ip": "10.11.201.201",
    "loglevel": 0,
    "event_type": 336,
    "server_uid": 1,
    "action": 0,
    "session_type": 1,
    "server_user": "root",
    "acl": "",
    "session_protocol": 2,
    "server_hid": 1,
    "approver": "",
    "session_version": "1.1",
    "event_id": 1868686747934214016,
    "client_uid": 5,
    "server_ip": "10.10.1.94",
    "session_rid": "b9de0b34600a79910000000103000005",
    "acl_tag": {},
    "approver_id": 0,
}
audit_sql_tmp = {
    "server_appid": 0,
    "exec_result": "SQL exec succeed!",
    "client_name": "cy",
    "sql_len": 8,
    "action": 0,
    "department_id": 3,
    "affect_rows": 0,
    "sql_type": 0,
    "client_ip": "192.168.3.123",
    "sql_text": "CMD_QUIT",
    "acl": "",
    "event_time": 1678066678273,
    "audit_rows": 0,
    "server_uid": 3023,
    "affect_table": "",
    "event_type": 819,
    "db_name": "",
    "server_user": "root",
    "affect_tables": 0,
    "session_type": 13,
    "app_name": "MySQLWorkbench",
    "loglevel": 0,
    "server_hid": 3003,
    "is_auto_cmd": 0,
    "event_id": 2428772791167096192,
    "session_protocol": 9,
    "acl_tag": {},
    "server_ip": "10.10.1.211",
    "sql_result": 1,
    "session_version": "1.1",
    "session_rid": "bb8b92e4640543dd00000bbb03000005",
    "id": 76,
    "server_name": "多个linux账号",
    "status_code": 0,
    "client_uid": 5,
    "sql_process_time": 0,
    "datekey": datetime.date(2023, 3, 6),
    "client_user": "admin",
}
audit_graphic_tmp = {
    "client_uid": 5,
    "x": 11,
    "department_id": 3,
    "client_user": "admin",
    "y": 27,
    "event_time": 1611105337736,
    "client_name": "admin",
    "width": 30,
    "event_type": 385,
    "client_ip": "10.11.33.56",
    "height": 12,
    "session_type": 5,
    "server_uid": 1,
    "command": "文件 (F)  编辑 (E)  格式 (O)  查看 (V)  帮助 (H)\r\n",
    "session_protocol": 5,
    "server_user": "administrator",
    "session_version": "1.1",
    "server_hid": 1,
    "event_id": 1867060351251609474,
    "session_rid": "106bfc20600783de0000000103000005",
    "id": 6,
    "server_ip": "10.11.88.79",
    "server_name": "88.79",
}

audit_file_tmp = {
    "event_id": None,
    "session_version": None,
    "server_ip": "10.11.88.64",
    "result": 0,
    "session_rid": "edc8c7936002a0c70000000203000005",
    "file_descriptor": 1,
    "server_name": "10.11.88.64win",
    "elapsed": 30,
    "client_uid": 5,
    "start_time": 1610784967,
    "department_id": 3,
    "copied": 0,
    "client_user": "admin",
    "err_msg": "",
    "event_time": 1610784997000,
    "speed": 0,
    "client_name": "",
    "new_filename": "",
    "event_type": 515,
    "hash": "",
    "client_ip": "10.11.201.201",
    "work_dir": None,
    "session_type": None,
    "flag": None,
    "filename": "ocr.txt",
    "server_uid": 2,
    "session_protocol": None,
    "server_user": "admin",
    "id": 55,
    "server_hid": 2,
}
tmp_dict = {
    AuditCmd: audit_cmd_tmp,
    AuditFile: audit_file_tmp,
    AuditSQL: audit_sql_tmp,
    AuditGraphic: audit_graphic_tmp,
}
seq_dict = {
    AuditCmd: "cmd_id_seq",
    AuditFile: "file_id_seq",
    AuditSQL: "sql_id_seq",
    AuditGraphic: "graphic_id_seq",
}


class EventGenerator:
    def __init__(self, db, days=1800, day_count=10000, days_offset=0):
        """
        比如days为30,day_count为1W, 那生成总数为30W
        :param db:
        :param days: 生成的天数,对应datakey
        :param day_count: 每天生成的数量
        :param days_offset: 生成日期偏移的天数,比如填100,表示开始时间是100天以后; -100表示生成时间是100天以前;
        """
        self.db = db
        self.days = days
        self.day_count = day_count
        self.write_batch_size = 1000
        self.now_date = (datetime.datetime.now() + datetime.timedelta(days=days_offset)).date()

    def generate_sql_event(self):
        return self.event_multi_write(AuditSQL)

    def generate_cmd_event(self):
        return self.event_multi_write(AuditCmd)

    def generate_graphic_event(self):
        return self.event_multi_write(AuditGraphic)

    def generate_file_event(self):
        return self.event_multi_write(AuditFile)

    def event_multi_write(self, model):
        write_counter, write_total = 0, self.days * self.day_count

        # 事件审计的id不是自增的,需要手动指定
        seq = Sequence(seq_dict[model])
        for day in range(self.days):
            write_date = self.now_date - datetime.timedelta(days=day)
            write_ts = time.mktime(write_date.timetuple())
            for index in range(self.day_count):
                next_id = self.db.execute(seq)
                temp = deepcopy(tmp_dict[model])
                item = model(**temp)
                item.id = next_id
                item.event_time = int(write_ts * 1000)
                item.datekey = write_date
                # 填写uuid4的字段用于标记不同的数据
                item.session_rid = uuid.uuid4().hex + str(next_id)
                item.client_name = uuid.uuid4().hex
                self.db.add(item)
                write_counter += 1
                if write_counter % self.write_batch_size == 0:
                    self.db.commit()
                    print(
                        "\rwrite process: {:.2%}".format(write_counter / write_total),
                        end="",
                        flush=True,
                    )
        self.db.commit()


if __name__ == "__main__":
    with session_scope(SessionLocalPostgres) as pg_db:
        result = pg_db.execute
        generator = EventGenerator(pg_db, days=100, day_count=1000, days_offset=0)
        generator.generate_sql_event()

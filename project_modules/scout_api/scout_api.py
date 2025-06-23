
import time
import json
from ..data_base_func.db_worker import (
    custom_init_bd,
    write_db_many,
    read_db_many,
    close_db,
)


class ScoutAPI:
    def __init__(self, *, max_delay=15):
        self.api_id = None
        self.connect = None
        self.cursor = None
        self.db_name = None
        self.table_name = None
        self.scheme = None
        self.max_delay = max_delay
        self.answer_list = [
            'Нет данных от Scout, проверьте соединение!',
            'Превышено ожидание новых данных из Scout!',
        ]

    def get_config_api(self, ):
        config = {
            'api_id': self.api_id,
            'db_name': self.db_name,
            'table_name': self.table_name,
            'scheme': self.scheme,
        }
        if None in config.values():
            err = True
            msg = f'Данные "api_config" не полные: {config}'
            return err, msg, dict()
        try:
            config = json.dumps(config)
        except Exception as e:
            err = True
            msg = f'Данные "scout_config" не формата json: {e}'
            return err, msg, dict()
        err = False
        msg = 'ok'
        return err, msg, config

    def set_config_api(self, *, config, config_type='dict'):
        if config_type == 'json':
            try:
                config = json.loads(config)
            except Exception as e:
                err = True
                msg = f'Данные "scout_config" не формата json: {e}'
                return err, msg
        if type(config) is not dict:
            err = True
            msg = f'Данные "scout_config" не прошли проверку!'
            return err, msg
        api_id = config.get('api_id')
        db_name = config.get('db_name')
        table_name = config.get('table_name')
        scheme = config.get('scheme')
        valid_data = [api_id, db_name, table_name, scheme, ]
        if None in valid_data:
            err = True
            msg = f'Данные "scout_config" не полные: {valid_data}'
            return err, msg

        self.api_id = api_id
        self.db_name = db_name
        self.table_name = table_name
        self.scheme = scheme
        err = False
        msg = f'"scout_config" - обновлен!'
        return err, msg

    def open_connect_api(self, ):
        self.close_connect_api()
        err, self.connect, self.cursor = custom_init_bd(
            db_name=self.db_name,
            table_name=self.table_name,
            scheme=self.scheme,
            check_schemas=True,
        )
        if err:
            self.connect = None
            self.cursor = None
            self.db_name = None
            self.table_name = None
            self.scheme = None
            err = f'Подключение не установленно. {err}'
            return err
        return err

    def read_api(self, ):
        if self.api_id is None:
            return True, 'Неуказан "api_id"!', list()

        err, res, _ = read_db_many(
            cur=self.cursor,
            table_name=self.table_name,
            other_query=f'where api_id={self.api_id}',
            is_dict=True,
        )
        return err, res

    def write_api(self, is_signal=None, bet_stop=None, bet_start=None, datafeed=None):
        if self.api_id is None:
            return True, 'Неуказан "api_id"!', dict()
        structure = {
            'api_id': self.api_id,
            'timestamp': time.time(),
        }
        if not (is_signal is None):
            structure['is_signal'] = is_signal
        if not (bet_stop is None):
            structure['bet_stop'] = bet_stop
        if not (bet_start is None):
            structure['bet_start'] = bet_start
        if not (datafeed is None):
            structure['datafeed'] = json.dumps(datafeed)
        err = write_db_many(
            cur=self.cursor,
            table_name=self.table_name,
            data=structure,
            is_update=True,
        )
        return err, structure

    def drop_signal(self, ):
        if self.api_id is None:
            return True, 'Неуказан "api_id"!', dict()
        structure = {
            'api_id': self.api_id,
            'timestamp': 0,
            'is_signal': False,
            'bet_stop': int(time.time()),
            'datafeed': '{}',
        }
        err = write_db_many(
            cur=self.cursor,
            table_name=self.table_name,
            data=structure,
            is_update=True,
        )
        return err, structure

    def update_datafeed(self, *, structure):
        if self.api_id is None:
            return True, False, structure
        now_timestamp = time.time()
        bet_stop_timestamp = int(now_timestamp * 10)
        err, res = self.read_api()
        signal = True
        if err or not res:
            if structure['msg'] != self.answer_list[0]:
                structure['bet_stop'] = bet_stop_timestamp
                structure['msg'] = self.answer_list[0]
            err = True
            signal = False
            return err, signal, structure

        timestamp = res[0]['timestamp']
        is_signal = res[0]['is_signal']
        bet_stop = res[0]['bet_stop']
        bet_start = res[0]['bet_start']
        datafeed = res[0]['datafeed']

        if int(now_timestamp - timestamp) > self.max_delay:
            if structure['msg'] != self.answer_list[1]:
                structure['bet_stop'] = bet_stop_timestamp
                structure['msg'] = self.answer_list[1]
            err = True
            signal = False
            return err, signal, structure
        try:
            structure['timestamp'] = timestamp
            structure['bet_stop'] = bet_stop
            structure['bet_start'] = bet_start
            structure['datafeed'] = json.loads(datafeed)
            if structure['msg'] in self.answer_list:
                structure['msg'] = 'Соединение установлено!'
            else:
                structure['msg'] = None
            err = False
        except:
            structure['bet_stop'] = bet_stop_timestamp
            structure['msg'] = 'Ошибка в данных из Scout!'
            err = True
        return err, signal, structure

    def close_connect_api(self, ):
        close_db(cur=self.cursor, conn=self.connect)

    def print_settings(self):
        config = {
            'api_id': self.api_id,
            'db_name': self.db_name,
            'table_name': self.table_name,
            'scheme': self.scheme,
        }
        return config


def structure_scout_api():
    res = dict()
    # Передаваемые данные
    res['timestamp'] = None
    res['bet_stop'] = 0
    res['bet_start'] = 0
    res['datafeed'] = dict()
    # Проверочные данные
    res['msg'] = None
    res['error_num'] = 0
    res['error_max'] = 3
    res['switch_bet_status'] = 'n/a'
    res['bet_stop_buffer'] = 0
    res['bet_start_buffer'] = 0
    res['datafeed_buffer'] = dict()
    return res


def settings_database_scout_api(*, db_name):
    settings_database = {
        'api_id': int(time.time() * 10),
        'db_name': db_name,
        'table_name': 'events',
        'scheme': {
            'api_id': 'INT PRIMARY KEY NOT NULL',
            'timestamp': 'REAL',
            'is_signal': 'INT',
            'bet_stop': 'INT DEFAULT (0)',
            'bet_start': 'INT DEFAULT (0)',
            'datafeed': 'TEXT',
        },
    }
    return settings_database


def default_datafeed_scout_api():
    datafeed = {
        'format': None,
        'info': None,
        'match_name': None,
        'time_sec': None,
        'match_part': None,
        'current_serve': None,
        'match_score': list(),
        'parts_score': list(),
        'over_time_score': list(),
        'penalty_score': list(),
        'game_score': dict(),
        'goals': None,
        'comment': None,
        'status': None,
        'state_comment': str(),
    }
    return datafeed


if __name__ == '__main__':
    pass

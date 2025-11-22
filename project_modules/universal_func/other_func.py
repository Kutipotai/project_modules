import time
import json
# import orjson as json
import hashlib


def get_hash_id(keys: list = None):
    if not keys:
        return None
    token = '_'.join([str(k) for k in keys])
    return hashlib.sha1(token.encode()).hexdigest()


def write_file_text(*, file_name, data, typ='w', enc='utf-8', **kwargs):
    with open(f'{file_name}', typ, encoding=enc) as f:
        f.write(f'{data}\n')


def read_file_text(*, file_name, typ='r', enc='utf-8', rl=False, **kwargs):
    with open(f'{file_name}', typ, encoding=enc) as f:
        if rl:
            res = f.read().splitlines()
        else:
            res = f.read()
    return res


def set_tsv(*, data, file_name, is_col_name=True):
    col_name = list()
    text = str()
    for d in data:
        _t = str()
        for k, v in d.items():
            if not (k in col_name):
                col_name.append(k)
            # _t += f'{v if not (v is None) else ""}\t'
            _t += f'{v}\t'
        if _t:
            text += f'{_t}\n'
    if is_col_name:
        _t = '\t'.join([str(x) for x in col_name])
        text = f'{_t}\n{text}'
    write_file_text(file_name=file_name, data=text)
    return


def get_json_file(*, file_name, enc='utf-8', print_err=True):
    if file_name is None:
        return dict()
    try:
        return json.loads(read_file_text(file_name=file_name, enc=enc))
    except Exception as e:
        if print_err:
            print('get_json_file:', e)
        return dict()


def set_json_file(
        *,
        file_name=None,
        data=None,
        ensure_ascii=None,
        indent=None,
        print_err=True,
):
    if data is None:
        return False
    if file_name is None:
        file_name = f'{int(time.time() * 100)}-data.json'
    try:
        write_file_text(
            file_name=file_name,
            data=json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
        )
    except Exception as e:
        if print_err:
            print('set_json_file:', e)
        return False
    return True


def logger(*, msg, file_name='logs.txt', time_log=True, print_err=True):
    if time_log:
        msg = f"{time_now_humanized()} --> {msg}"
    try:
        write_file_text(file_name=file_name, data=f'{msg}', typ='a')
    except Exception as e:
        if print_err:
            print('logger', e)


class CustomTimer:
    def __init__(self, last_timestamp_time_sec: float = .0, time_sec: int = 0, is_paused: bool = True, ):
        self.last_timestamp_time_sec = last_timestamp_time_sec
        self.time_sec = time_sec
        self.is_paused = is_paused

    def start_timer(self, ):
        if self.is_paused is True:
            self.is_paused = False
            self.last_timestamp_time_sec = int(time.time() - self.time_sec)

    def stop_timer(self, ):
        if self.is_paused is False:
            self.is_paused = True
            self.time_sec = int(time.time() - self.last_timestamp_time_sec)

    def correct_timer(self, *, cor_sec: int):
        __now_time_sec = self.get_now_time()
        if __now_time_sec + cor_sec < 0:
            cor_sec = -__now_time_sec
        self.time_sec += cor_sec
        self.last_timestamp_time_sec -= cor_sec

    def get_now_time(self, ):
        if self.is_paused:
            return self.time_sec
        else:
            return int(time.time() - self.last_timestamp_time_sec)

    def set_now_time(self, *, new_sec: int):
        if self.is_paused:
            self.time_sec = new_sec
        else:
            self.last_timestamp_time_sec = int(time.time() - new_sec)
        pass


def normal_calendar_list(*, offset=1, now_day=1, _format='%Y-%m-%d', _sec_offset=0):
    date_list = list()
    for d in range(offset, - (now_day + 1), -1):  # for d in range(-offset, - (now_day + 1), -1):
        _date = time.strftime(f'{_format} %H:%M:%S', time.localtime(time.time() - d * 86400 + _sec_offset))
        date_list.append(_date[:-9])
    return date_list


def normal_calendar_list_v2(*, dn=0, up=0, is_straight=True, _format='%Y-%m-%d', _sec_offset=0):
    date_list = list()
    up += dn
    if dn > up:
        up = dn
    is_straight_value = 1 if is_straight else -1
    for d in list(range(dn, (up + 1)))[::is_straight_value]:  # for d in range(-up, - (-dn + 1), -1):
        _date = time.strftime(f'{_format} %H:%M:%S', time.localtime(time.time() + d * 86400 + _sec_offset))
        date_list.append(_date[:-9])
    return date_list


def timestamp_data(*, datetime_str, time_zone_sec=0, _format="%Y-%m-%d %H:%M"):
    return int(time.mktime(time.strptime(f'{datetime_str}', f'{_format}')) - time.timezone - time_zone_sec)


def datetime_str_data(*, timestamp, time_zone_sec=0, _format="%Y-%m-%d %H:%M"):
    return time.strftime(_format, time.gmtime(timestamp + time_zone_sec))


def time_now_humanized(msec=None, _format='%Y-%m-%d %H:%M:%S'):
    match msec:
        case int() | float():
            return f"{time.strftime(f'{_format}.{int(time.time() % 1 * 10 ** int(msec)):{int(msec):02}}')}"
        case _:
            return f"{time.strftime(_format)}"


def convert_timer_universal(*, sec_time=None, text_time=None, min_value=None, sec_value=None):
    if not (sec_time is None):
        min_value = int(sec_time / 60)
        sec_value = int(sec_time % 60)
        text_time = f'{min_value}:{sec_value:02}'
        return sec_time, text_time, min_value, sec_value
    if not (text_time is None):
        v = text_time.split(':')
        min_value = int(v[0])
        sec_value = int(v[1])
        sec_time = int(min_value * 60 + sec_value)
        return sec_time, text_time, min_value, sec_value
    if not (min_value is None or sec_value is None):
        if min_value is None:
            min_value = 0
        if sec_value is None:
            sec_value = 0
        _min_value = int(sec_value / 60)
        min_value = int(min_value) + int(_min_value)
        sec_value = int(sec_value % 60)
        text_time = f'{min_value}:{sec_value:02}'
        sec_time = int(min_value * 60 + sec_value)
    return sec_time, text_time, min_value, sec_value


def validation_json_value(
        value: str | dict | list,
        value_type='str',
        indent=None,
        ensure_ascii=None,
        _dv=None,
        print_err=True,
):
    if not value:
        return _dv
    try:
        match value_type:
            case 'str':
                value = json.loads(value)
                # value = json.loads(value.encode('utf-8'))
            case 'dict':
                value = json.dumps(value, indent=indent, ensure_ascii=ensure_ascii)
                # if indent:
                #     value = json.dumps(value, option=json.OPT_INDENT_2).decode('utf-8')
                # else:
                #     value = json.dumps(value).decode('utf-8')
            case _:
                value = _dv
    except Exception as e:
        value = _dv
        if print_err:
            print('validation_json_value:', e)
    return value


def validation_float_value(value, _dv=0.0, print_err=True):
    if value == '' or value is None:
        value = _dv
        return value
    try:
        value = float(value)
    except Exception as e:
        value = _dv
        if print_err:
            print('validation_float_value:', e)
    return value


def validation_int_value(value, _dv=0, dirty=True, print_err=True):
    if value == '' or value is None:
        value = _dv
        return value
    try:
        if dirty:
            value = int(''.join([x for x in str(value) if x in '1234567890']))
        else:
            value = int(value)
    except Exception as e:
        value = _dv
        if print_err:
            print('validation_int_value:', e)
    return value


def get_score(*, score_str, p=' ', t='-', print_err=True):
    try:
        if p is None:
            score = [int(x.strip()) for x in score_str.split(t)]
        else:
            score = [[j.strip() for j in x.split(t) if j] for x in score_str.split(p)]
            score = [[int(j) for j in x] for x in score if x]
    except Exception as e:
        score = list()
        if print_err:
            print('get_score:', e, score_str)
    return score


def get_clt(*, value: str, replace_list: None | list = None):
    if not value:
        return value
    value = str(value).lower()
    if replace_list:
        for rl in replace_list:
            value = value.replace(rl, '')
    return ' '.join(value.strip().split())


def fix_ru_or_en_letters(text: str, lang='en') -> str:
    if not text:
        return text
    chars_map = {
        'en': {
            'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y', 'х': 'x',
            'в': 'b', 'н': 'h', 'к': 'k', 'м': 'm', 'т': 't', 'п': 'n',
        },
        'ru': {
            'a': 'а', 'b': 'в', 'c': 'с', 'e': 'е', 'h': 'н', 'k': 'к', 'm': 'м',
            'o': 'о', 'p': 'р', 't': 'т', 'x': 'х', 'y': 'у', 'n': 'п',
        }
    }
    return ''.join(chars_map.get(lang, dict()).get(str(char), str(char)) for char in text)


if __name__ == '__main__':
    pass

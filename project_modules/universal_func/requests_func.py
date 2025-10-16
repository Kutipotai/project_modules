import time
import requests
import urllib.parse
import urllib.request
import random
import uuid
import threading
from fake_useragent import UserAgent

# import ssl
# ssl._create_default_https_context = ssl._create_stdlib_context
# pip install -U 'requests[socks]'


def _get_proxy(*, proxies, **kwargs):
    _proxies = dict()
    if proxies:
        _host = proxies.get('host')
        _port = proxies.get('port')
        _protocol = proxies.get('protocol', 'http')
        if _host and _port:
            _proxy = f'{_protocol}://'
            _login = proxies.get('login')
            _password = proxies.get('password')
            if _login and _password:
                _proxy += f'{_login}:{_password}@'
            _proxy += f'{_host}:{_port}'
            _proxies = {'http': _proxy, 'https': _proxy, }
    return _proxies


def params_to_data_urllib(*, params):
    data = '&'.join([f'{k}={urllib.parse.quote(str(v))}' for k, v in params.items()])
    return data


def get_content_urllib(
        *,
        url: str | None = None,
        headers: dict | None = None,
        params: dict | None = None,
        proxies: dict | None = None,
        update_url: bool = True,
        _dv: list | dict | bool | None = False,
        print_err: bool = True,
        **kwargs,
):
    err, res = None, _dv
    if not url:
        return f'url={url}', _dv
    if not headers:
        headers = dict()
    data = None
    if params:
        if update_url:
            url += f'?{params_to_data_urllib(params=params)}'
        else:
            data = urllib.parse.urlencode(params)
            data = data.encode('ascii')
    try:
        proxy_support = urllib.request.ProxyHandler()
        if proxies:
            if _proxies := _get_proxy(proxies=proxies):
                proxy_support = urllib.request.ProxyHandler(_proxies)
        opener = urllib.request.build_opener(proxy_support)
        urllib.request.install_opener(opener)
        req = urllib.request.Request(url=url, data=data, headers=headers) #, method=method)
        with urllib.request.urlopen(req) as _res:
            res = _res.read().decode('utf-8')
    except Exception as e:
        if print_err:
            print('get_content_urllib:', e)
        return f'err={e}', _dv
    return err, res


def get_content(
        *,
        url,
        connect=None,
        type_content=None,
        params=None,
        headers=None,
        proxies=None,
        timeout=None,
        verify=True,
        _dv=None,
        print_err=True,
        **kwargs
):
##    connect.auth = ('user', 'pass')
##    connect.verify = '/path/to/certfile' / False
    err, res = None, _dv
    if timeout:
        timeout = tuple(timeout)
    if not headers:
        headers = dict()
    if not params:
        params = dict()
    try:
        if connect:
            res = connect.get(
                url, params=params, headers=headers,
                timeout=timeout, verify=verify,
                proxies=_get_proxy(proxies=proxies),
            )
        else:
            cookies = kwargs.get('cookies')
            if not cookies:
                cookies = None
            res = requests.get(
                url, params=params, headers=headers,
                timeout=timeout, verify=verify,
                proxies=_get_proxy(proxies=proxies),
                cookies=cookies,
            )
        res.encoding = 'utf-8'
        if type_content:
            match type_content:
                case 'text':
                    return err, res.text
                case 'json':
                    return err, res.json()
                case _:
                    return f"Not found type_content! --> {url}", _dv
    except Exception as e:
        if print_err:
            print('get_content:', e)
        return f"Error! --> {url}", _dv
    return err, res


def post_content(
        *,
        url,
        connect=None,
        type_content=None,
        params=None,
        headers=None,
        proxies=None,
        timeout=None,
        verify=True,
        allow_redirects=None,
        params_key='json',
        _dv=None,
        print_err=True,
        **kwargs
):
    err, res = None, _dv
    if timeout:
        timeout = tuple(timeout)
    if not headers:
        headers = dict()
    if not params:
        params = dict()
    try:
        _kwargs = {params_key: params}  # 'json', 'data'
        if connect:
            res = connect.post(
                url, headers=headers, timeout=timeout,
                verify=verify, allow_redirects=allow_redirects,
                proxies=_get_proxy(proxies=proxies),
                **_kwargs,
            )
        else:
            res = requests.post(
                url, headers=headers, timeout=timeout,
                verify=verify, allow_redirects=allow_redirects,
                proxies=_get_proxy(proxies=proxies),
                **_kwargs,
            )
        res.encoding = 'utf-8'
        if type_content:
            match type_content:
                case 'text':
                    return err, res.text
                case 'json':
                    return err, res.json()
                case _:
                    return f"Not found type_content! --> {url}", _dv
    except Exception as e:
        if print_err:
            print('post_content:', e)
        return f"Error! --> {url}", _dv
    return err, res


def init_connect_requests(*, proxies=None, headers=None):
    connect = requests.Session()
    if headers:
        connect.headers.update(headers)
    if proxies:
        if _proxies := _get_proxy(proxies=proxies):
            connect.proxies.update(_proxies)
    return connect


def close_connect(*, connect, print_err=True):
    try:
        connect.close()
    except Exception as e:
        if print_err:
            print('close_connect():', e)
    return


def get_google_sheets_data(
        *,
        api_key,
        sheet_name,
        gid,
        protocol,
        verify,
        method=None,
        keys_for_dict=None,
        skip_line=None,
        format_tsv=False,
        print_err=True,
        **kwargs,
):
    data_feed = list()
    split_char = ','
    if not skip_line:
        skip_line = list()
    try:
        url = f'{protocol}://docs.google.com/spreadsheet/ccc?key={api_key}&output=csv&gid={gid}'
        match method:
            case 1:
                url = f'{protocol}://docs.google.com/spreadsheet/ccc?key={api_key}&output=csv&gid={gid}'
            case 2:
                if format_tsv:
                    url = f'{protocol}://docs.google.com/spreadsheets/d/{api_key}/export?format=tsv&gid={gid}'
                    split_char = f'\t'
                else:
                    url = f'{protocol}://docs.google.com/spreadsheets/d/{api_key}/export?format=csv&gid={gid}'
            case 3:
                url = f'{protocol}://spreadsheets.google.com/feeds/download/spreadsheets/Export?key={api_key}&exportFormat=csv&gid={gid}'
            case 4:
                # не забирает скрытые диапазоны
                url = f'{protocol}://docs.google.com/spreadsheets/d/{api_key}/gviz/tq?tqx=out:csv&sheet={sheet_name}'  # csv / json

        req = requests.get(url=url, verify=verify, )
        raw_data = req.content.decode('utf-8')
        if method in [3, 4, ]:
            raw_data = raw_data.replace('"', '')
        if keys_for_dict:
            kfd = keys_for_dict
            kl = len(keys_for_dict)
            for i, rd in enumerate(raw_data.splitlines()):
                if i in skip_line:
                    continue
                data_feed.append({kfd[i]: v for i, v in enumerate(rd.split(split_char)[:kl]) if kfd[i]})
        else:
            for i, rd in enumerate(raw_data.splitlines()):
                if i in skip_line:
                    continue
                data_feed.append(rd.split(split_char))
    except Exception as e:
        if print_err:
            print('get_google_sheets_data:', e)
        data_feed = list()
    return data_feed


def send_message_telegram(*, msg, chat_id, token, **kwargs):
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    params = {
        'chat_id': f'{chat_id}',
        'text': f'{msg}',
        'disable_notification': kwargs.get('disable_notification', False),
        'parse_mode': kwargs.get('parse_mode', 'html'),
    }
    headers = {
        "Content-Type": "application/json"
    }
    timeout = kwargs.get('timeout', (15, 15))
    err, res = post_content(
        url=url, type_content='text',
        params=params, headers=headers,
        timeout=tuple(timeout) if timeout else None,
        verify=kwargs.get('verify', True),
        proxies=kwargs.get('proxies'),
    )
    return err, res


def send_message_discord(*, msg, chat_id, token, **kwargs):
    url = f'https://discord.com/api/v10/channels/{chat_id}/messages'
    params = {'content': f'{msg}'}
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    timeout = kwargs.get('timeout', (15, 15))
    err, res = post_content(
        url=url, type_content='text',
        params=params, headers=headers,
        timeout=tuple(timeout) if timeout else None,
        verify=kwargs.get('verify', True),
        proxies=kwargs.get('proxies'),
    )
    return err, res


def response_to_data(response, type_content, _dv=None):
    err = None
    try:
        response.encoding = 'utf-8'
        match type_content:
            case 'text':
                return err, response.text
            case 'json':
                return err, response.json()
            case _:
                return err, response
    except:
        err = f'response_to_data: data not {type_content} error!'
    return err, _dv


def get_check_connect(proxies=None, timeout=10):
    try:
        for url in ['https://www.google.com', 'https://api.ipify.org/?format=json', 'https://ipinfo.io/json']:
            r = requests.get(url, proxies=proxies, timeout=timeout)
            if r.status_code == 200:
                return True
        return False
    except:
        return False


class FingerprintGenerator:
    def __init__(self):
        self.ua = UserAgent()

        # Минимальные реальные значения
        self.platforms = ["Win32", "Linux x86_64", "MacIntel"]
        self.device_memory = [2, 4, 8, 16, 24, 32, 64]
        self.hardware_threads = [2, 4, 8, 6, 12, 18, 24, 32]
        self.timezones = [
            "Europe/Moscow", "UTC", "America/New_York", "Asia/Tokyo", "Europe/Berlin", "America/Los_Angeles"
        ]
        self.viewports = ["1920x1080", "1440x900", "1366x768", "1536x864", "1280x720", "2560x1440"]
        self.languages = {
            "en-US": "en-US,en;q=0.9",
            "ru-RU": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "fr-FR": "fr-FR,fr;q=0.9,en;q=0.8",
        }
        self.user_agent_keywords = {
            "Win32": ["Windows NT", "Win64"],
            "Linux x86_64": ["X11; Linux x86_64", "Linux; Android"],
            "MacIntel": ["Macintosh"],
        }

    def _find_user_agent(self, platform):
        keywords = self.user_agent_keywords.get(platform)
        try:
            for _ in range(100):  # max attempts
                ua = self.ua.random
                if any(k in ua for k in keywords):
                    return ua
        except Exception:
            pass
        # fallback
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"

    def generate(self, platform=None, lang="en-US", timezone=None, viewport=None):
        platform = platform if platform else random.choice(self.platforms)
        user_agent = self._find_user_agent(platform=platform)
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": self.languages.get(lang, "en-US,en;q=0.9"),
            "DNT": "1",
            "Referer": "https://www.google.com",
            "X-Request-ID": str(uuid.uuid4()),

            # Расширенный fingerprint
            "X-Platform": platform,
            "X-Device-Memory": str(random.choice(self.device_memory)),
            "X-HardwareConcurrency": str(random.choice(self.hardware_threads)),
            "X-Viewport": viewport if viewport else random.choice(self.viewports),
            "X-Timezone": timezone if timezone else random.choice(self.timezones),
            "X-Requested-With": "XMLHttpRequest"
        }
        return headers


class ProxyManager:
    def __init__(
            self, workers,
            not_work_timeout=300,
            no_internet_timeout=60,
            request_timeout=5,
            limit_errors=3,
            platform=None,  # "Win32",
            lang=None,  # "ru-RU",
            timezone=None,  # "Europe/Moscow"
            viewport=None,
    ):

        self.fingerprint_generator = FingerprintGenerator()
        self.platform = platform
        self.lang = lang
        self.timezone = timezone
        self.viewport = viewport

        self.min_timeout = 0
        self.internet_blocked_until = int(not get_check_connect()) * (int(time.time()) + no_internet_timeout)
        self.not_work_timeout = not_work_timeout
        self.no_internet_timeout = no_internet_timeout
        self.request_timeout = request_timeout
        self.limit_errors = limit_errors
        self.proxies = dict()
        for worker in workers:
            proxies = _get_proxy(proxies=worker.get('proxies'))
            headers = self.fingerprint_generator.generate(
                platform=platform,
                lang=lang,
                timezone=timezone,
                viewport=viewport,
            )
            session = requests.Session()
            session.proxies.update(proxies)
            session.headers.update(headers)
            name = proxies.get('http')
            if not name:
                name = 'main'

            self.proxies[name] = {
                'session': session,
                'headers': headers,
                'proxies': proxies,
                'timeout_until': 0,
                'errors': 0,
            }

    def refresh_fingerprint(self, proxy):
        headers = self.fingerprint_generator.generate(self.platform, self.lang, self.viewport, self.timezone)
        session = self.proxies[proxy]['session']
        session.headers.update(headers)
        self.proxies[proxy]['headers'] = headers

    def get_proxy(self):
        uts = int(time.time())
        available = [p for p, data in self.proxies.items() if data['timeout_until'] < uts]
        if not available:
            return None
        return random.choice(available)

    def get_min_timeout(self):
        uts = int(time.time())
        min_timeout = 0
        min_timeout_list = [
            data['timeout_until'] - uts for p, data in self.proxies.items()
            if data['timeout_until'] >= uts
        ]
        if min_timeout_list:
            min_timeout = min(min_timeout_list)
        return max(min_timeout, self.internet_blocked_until)

    def request(self, url, retries=3, type_content='raw', method='get', _dv=None, **kwargs):
        err = None
        res = _dv
        uts = int(time.time())
        print_err = kwargs.pop('print_err', None)
        post_params_key = kwargs.pop('post_params_key', 'json')  # 'json', 'data'
        if self.internet_blocked_until > uts:
            err = f'$1$ ProxyManager.request: internet_blocked_until={self.internet_blocked_until - uts}'
            res = _dv
            return err, res
        if self.internet_blocked_until > 0:
            if not get_check_connect():
                if print_err:
                    print("[!] Потеряно соединение с интернетом.")
                self.internet_blocked_until = uts + self.no_internet_timeout
                err = f'$1$ ProxyManager.request: internet_blocked_until={self.internet_blocked_until - uts}'
                res = _dv
                return err, res
            self.internet_blocked_until = 0
        [kwargs.pop(_dkk, None) for _dkk in ['connect', 'print_err']]
        for attempt in range(1, retries + 1):
            uts = int(time.time())
            proxy = self.get_proxy()
            if not proxy:
                err = f'$1$ ProxyManager.request: нет рабочих proxy 0/{len(self.proxies)}'
                res = _dv
                break
            proxy_data = self.proxies[proxy]
            session = proxy_data['session']
            proxy_data['timeout_until'] = uts + self.request_timeout
            try:
                response = None
                match method:
                    case 'post':
                        if 'params' in kwargs:
                            kwargs[post_params_key] = kwargs.pop('params', None)
                        response = session.post(url, **kwargs)
                    case _:
                        response = session.get(url, **kwargs)
                if response is None or not (response.status_code in [200]):
                    response = None
            except Exception:
                response = None
            if response is None:
                err = f'$2$ ProxyManager.request: Ошибка запроса через proxy || [{proxy}]'
                res = _dv
                proxy_data['errors'] += 1
                proxy_data['timeout_until'] = uts + self.request_timeout * 2
            else:
                if proxy_data['errors'] > 1:
                    proxy_data['errors'] -= 1

            if proxy_data['errors'] > self.limit_errors:
                if not self.internet_blocked_until + uts < 0:
                    if not get_check_connect():
                        if print_err:
                            print("[!] Потеряно соединение с интернетом.")
                        self.internet_blocked_until = uts + self.no_internet_timeout
                        err = f'$1$ ProxyManager.request: internet_blocked_until={self.internet_blocked_until - uts}'
                        res = _dv
                        return err, res
                    else:
                        self.internet_blocked_until = -(uts + self.no_internet_timeout * 2)
                if not get_check_connect(proxies=proxy_data['proxies']):
                    if print_err:
                        print(f"[!] Прокси {proxy} не работает. Тайм-аут {self.not_work_timeout} сек.")
                    proxy_data['timeout_until'] = uts + self.not_work_timeout
                    self.refresh_fingerprint(proxy)
                else:
                    proxy_data['errors'] = 0

            if response:
                _err, res = response_to_data(response=response, type_content=type_content, _dv=_dv)
                if _err:
                    err = f'$3$ ProxyManager.{_err} || [{proxy}]'
                    res = _dv
                return err, res
        if not self.internet_blocked_until + uts < 0:
            if not get_check_connect():
                if print_err:
                    print("[!] Потеряно соединение с интернетом.")
                self.internet_blocked_until = uts + self.no_internet_timeout
                err = f'$1$ ProxyManager.request: internet_blocked_until={self.internet_blocked_until - uts}'
                res = _dv
                return err, res
            else:
                if print_err:
                    print("[!] Всё ок с интернетом.")
                self.internet_blocked_until = -(uts + self.no_internet_timeout * 2)
        return err, res


if __name__ == '__main__':
    pass

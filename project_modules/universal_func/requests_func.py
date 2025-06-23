import time

import requests
import urllib.parse
import urllib.request

# import ssl
# ssl._create_default_https_context = ssl._create_stdlib_context
# pip install -U 'requests[socks]'


def _get_proxy(*, proxies):
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
        default_value: list | dict | bool | None = False,
        print_err: bool = True,
        **kwargs,
):
    err, res = None, default_value
    if not url:
        return f'url={url}', default_value
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
        return f'err={e}', default_value
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
        default_value=None,
        print_err=True,
        **kwargs
):
##    connect.auth = ('user', 'pass')
##    connect.verify = '/path/to/certfile' / False
    err, res = None, default_value
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
            res = requests.get(
                url, params=params, headers=headers,
                timeout=timeout, verify=verify,
                proxies=_get_proxy(proxies=proxies),
            )
        res.encoding = 'utf-8'
        if type_content:
            match type_content:
                case 'text':
                    return err, res.text
                case 'json':
                    return err, res.json()
                case _:
                    return f"Not found type_content! --> {url}", default_value
    except Exception as e:
        if print_err:
            print('get_content:', e)
        return f"Error! --> {url}", default_value
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
        default_value=None,
        print_err=True,
        **kwargs
):
    err, res = None, default_value
    if timeout:
        timeout = tuple(timeout)
    if not headers:
        headers = dict()
    if not params:
        params = dict()
    try:
        if connect:
            res = connect.post(
                url, json=params, headers=headers, timeout=timeout,
                verify=verify, allow_redirects=allow_redirects,
                proxies=_get_proxy(proxies=proxies),
            )
        else:
            res = requests.post(
                url, json=params, headers=headers, timeout=timeout,
                verify=verify, allow_redirects=allow_redirects,
                proxies=_get_proxy(proxies=proxies),
            )
        res.encoding = 'utf-8'
        if type_content:
            match type_content:
                case 'text':
                    return err, res.text
                case 'json':
                    return err, res.json()
                case _:
                    return f"Not found type_content! --> {url}", default_value
    except Exception as e:
        if print_err:
            print('post_content:', e)
        return f"Error! --> {url}", default_value
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
            case _:
                url = f'{protocol}://docs.google.com/spreadsheet/ccc?key={api_key}&output=csv&gid={gid}'
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
    err, res = post_content(
        url=url, type_content='text',
        params=params, headers=headers,
        timeout=(5, 5), verify=True,
    )
    return err, res


def send_message_discord(*, msg, chat_id, token):
    url = f'https://discord.com/api/v9/channels/{chat_id}/messages'
    params = {'content': f'{msg}'}
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    err, res = post_content(
        url=url, type_content='text',
        params=params, headers=headers,
        timeout=(5, 5), verify=True,
    )
    return err, res


if __name__ == '__main__':
    pass

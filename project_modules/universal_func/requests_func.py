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
    url = 'https://lds-api-sites.ligastavok.ru/rest/events/v8/eventsList'
    # url = 'https://match-storage-parsed.top-parser.com/matches/list?data=%7B%22lang%22:%22ru%22,%22localeId%22:1,%22service%22:%22prematch%22,%22categoryId%22:989,%22onlyOutrights%22:false%7D'
    headers = {
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Connection': 'keep-alive',
            'Content-Length': '112',
            'Host': 'lds-api-sites.ligastavok.ru',
            'Origin': 'https://www.ligastavok.ru',
            'Referer': 'https://www.ligastavok.ru/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
            'accept': 'application/json',
            'content-type': 'application/json',
            'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'x-api-cred': '',
            'x-application-name': 'mobile',
            'x-req-id': '-',
            'x-user': '',
        }
    # headers = {
    #     'Accept-Encoding': 'gzip, deflate, br, zstd',
    #     'Accept-Language': 'ru-RU,ru;q=0.9',
    #     'Connection': 'keep-alive',
    #     'Origin': 'https://1wzjvm.top',
    #     'Referer': 'https://1wzjvm.top/',
    #     'Sec-Fetch-Dest': 'empty',
    #     'Sec-Fetch-Mode': 'cors',
    #     'Sec-Fetch-Site': 'same-site',
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
    #     'accept': 'application/json, text/plain, */*',
    #     'content-type': 'application/json',
    #     # 'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
    #     # 'sec-ch-ua-mobile': '?0',
    #     # 'sec-ch-ua-platform': '"Windows"',
    #     # "x-origin": "1wzjvm.top",
    # }
    param = {
        "limit": 20, "gameId": [], "ns": "live", "topEvents": False,
        "widgetVideo": False, "proposedTypes": ["MAINOFFER"]
    }
    # param = {'data': {"lang":"ru","localeId":1,"service":"prematch","categoryId":989,"onlyOutrights":False}}

    err, res = post_content(
        url=url,
        type_content='json',
        headers=headers,
        params=param,
        timeout=(10, 10)
    )
    print(res)
# if __name__ == '__main__':
#     connect = init_connect_requests()
#     headers = {
#         'Accept': 'text/plain',
#         'Content-Type': 'application/json',
#     }
#     host = 'https://partners.xsportzone.com'
#     api_auth = '/api/v1/account/auth'
#     param = {
#       "Login": "USSR1/2/ACL",
#       "Password": "M5Fg1b8s"
#     }
#     # err, res = post_content(
#     #     url=f'{host}{api_auth}',
#     #     type_content='json',
#     #     headers=headers,
#     #     params=param,
#     # )
#     # print(err, res)
#     access_token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJodHRwOi8vc2NoZW1hcy54bWxzb2FwLm9yZy93cy8yMDA1LzA1L2lkZW50aXR5L2NsYWltcy9uYW1lIjoiVVNTUjEvMi9BQ0wiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL3JvbGUiOiI3IiwiaHR0cDovL3NjaGVtYXMueG1sc29hcC5vcmcvd3MvMjAwNS8wNS9pZGVudGl0eS9jbGFpbXMvbmFtZWlkZW50aWZpZXIiOiIxNTc2IiwibmJmIjoxNzMzMzM5ODI4LCJleHAiOjE3MzM5NDQ2MjgsImlzcyI6IlNwb3J0V29ya0JlbmNoIiwiYXVkIjoiQ2xpZW50In0.bKah-1sHB6gHAWmwXoRl8LhvEi-DnwlD3VlucpLQcYk'
#     headers['Authorization'] = f'Bearer {access_token}'
#     api_operator = '/api/v1/games/operator/'
#     operator_id = 1570
#     # for _ in range(50):
#     #     err, res = get_content(
#     #         url=f'{host}{api_operator}{operator_id}',
#     #         connect=connect,
#     #         # url=f'{host}{api_matches}',
#     #         type_content='json',
#     #         headers=headers,
#     #     )
#     #     # print(err, res)
#     #     data = res.get('Data', dict())
#     #     # print(data)
#     #     print(
#     #         data.get('Score1'),
#     #         data.get('Score2'),
#     #         f"{int(data.get('Time')/60)}:{int(data.get('Time')%60)}",
#     #     )
#     #     time.sleep(0.5)
#
#     api_matches = '/api/v1/games'
#     match_id = 3361185
#     for _ in range(50):
#         err, res = get_content(
#             url=f'{host}{api_matches}',
#             connect=connect,
#             type_content='json',
#             headers=headers,
#         )
#         # print(err, res)
#         data = res.get('Data', list())
#         data = {d.get('Id'): d for d in data}
#         # print(data)
#         data = data.get(match_id, dict())
#         print(
#             data.get('Score1'),
#             data.get('Score2'),
#             f"{int(data.get('Time') / 60)}:{int(data.get('Time') % 60)}",
#         )
#         time.sleep(0.5)
#     close_connect(connect=connect)
#     pass


# if __name__ == '__main__':
#
#
#     headers = {
#         'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
#         'Connection': 'keep-alive',
#         'Host': 'www.tipsport.cz',
#         'Origin': 'https://www.tipsport.cz',
#         'Referer': 'https://www.tipsport.cz/live/esporty-188',
#         'Sec-Fetch-Dest': 'empty',
#         'Sec-Fetch-Mode': 'cors',
#         'Sec-Fetch-Site': 'same-origin',
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
#         'accept': 'application/json',
#         'sec-ch-ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#         'sec-ch-ua-arch': '"x86"',
#         'sec-ch-ua-bitness': '"64"',
#         'sec-ch-ua-full-version': '"131.0.2903.99"',
#         'sec-ch-ua-full-version-list': '"Microsoft Edge";v="131.0.2903.99", "Chromium";v="131.0.6778.140", "Not_A Brand";v="24.0.0.0"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-model': '""',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-ch-ua-platform-version': '"15.0.0"',
#     }
#     connect = init_connect_requests(
#         headers=headers,
#         proxies={"name":"proxy - 15 (MiniBoss)","login":"ESSqUwUq","password":"CngaRLeC","host":"194.58.43.137","port":"62484","protocol":"http"},
#
#     )
#     url = 'https://www.tipsport.cz/live/esporty-188'
#     err, res = get_content(
#         connect=connect,
#         url=url,
#         headers={
#             'Accept-Encoding': 'gzip, deflate, br, zstd',
#             'Accept-Language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
#             'Connection': 'keep-alive',
#             'Host': 'www.tipsport.cz',
#             'Sec-Fetch-Dest': 'document',
#             'Sec-Fetch-Mode': 'navigate',
#             'Sec-Fetch-Site': 'none',
#             'Sec-Fetch-User': '?1',
#             'Upgrade-Insecure-Requests': '1',
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
#             'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
#         }
#     )
#     print(res.headers.get('Set-Cookie'))
#     # headers['cookie'] = res.headers.get('Set-Cookie')
#
#     # url = 'https://www.tipsport.cz/rest/common/v1/init-web'
#     # params = {
#     #     "parameters": ["CLIENT_ANALYSIS__SHOW_LIVE_MATCHES", "LIVE_COMMUNITY_ENABLED", "COMMUNITY_BETS_ON",
#     #         "LOYALTY_PROGRAM_FRONTEND_ENABLED", "LOYALTY_PROGRAM_ONBOARDING_WEB_ENABLED",
#     #         "PARTICIPATION_IN_GAMBLING_WARNING_TIMER", "ZHH_2023_CZ_FAZE_ONE_ENABLE", "ZHH_2023_CZ_FAZE_TWO_ENABLE",
#     #         "CLIENT_TICKET_SUCCESS_RATE_ENABLED", "MARKDOWN_MULTIPLE_CHARS_COUNT", "MIN_BLOG_UPDATE_TEXT_LENGTH",
#     #         "MAX_BLOG_UPDATE_TEXT_LENGTH", "MIN_DAYS_FOR_BLOG_TO_EXPIRE", "MAX_DAYS_FOR_BLOG_TO_EXPIRE",
#     #         "MAX_IDENTIFICATION_DOCUMENT_FILE_SIZE_MB", "SOCIAL_ACTIVE_CLIENT_SUGGESTIONS_MULTISEARCH_MAX_COUNT",
#     #         "MAX_IDENTIFICATION_DOCUMENT_FILE_RESOLUTION", "WEBTIP_ADMINISTRATION_EMAIL", "WEBTIP_ADMINISTRATION_PHONE",
#     #         "TOP_MATCHES_SUBSET_COUNT", "TICKET_DETAIL_REFRESH_TIME", "CASHOUT_AUTO_REFRESH_INTERVAL_SECONDS",
#     #         "CASHOUT_PERCENTAGE_SLIDER_DELTA_POINTS", "CASHOUT_PERCENTAGE_SLIDER_MAXIMUM_POINTS",
#     #         "WEBTIP_TICKET_CANCEL_TIME", "CLIENT_EVENTS_SUCCESSRATE_SHARE", "GOOGLE_MAPS_API_KEY",
#     #         "CASINO_GAMBLE_ENABLED", "LOTTERY_OPT_OUT_ENABLED", "TICKET_MINUTES_TO_CANCEL", "KORUNKA_URL",
#     #         "KORUNKA_GAME_TYPE_ORDER", "KORUNKA_GAME_TYPE_TILE_ORDER", "TICKET_BUILDER_BET_ADDITION_ENABLED",
#     #         "TICKET_BUILDER_BET_BUILDER_LIVE_ENABLED", "LIVE_MULTIVIEW_ENABLED", "WEBTIP_LIVEODDS_FORUM_ENABLED",
#     #         "START_BONUS__MAX_AMOUNT", "CASINO_ENABLED", "CASINO_LIVE_GAME_ENABLED", "FREE_SPIN_BONUS_AMOUNT",
#     #         "CASINO_SOCKET_IO_CASINO_NAMESPACE_ENABLED", "WEBTIP_SK_NEW_PAGE_DEPOSIT_WITHDRAWALS_ENABLED_SPA",
#     #         "FLOWPLAYER_LICENCE_KEY", "CLIENT_ANALYZE_V2_ODD_FIXATION_MINUTES",
#     #         "CLIENT_ANALYZE_V2_ODD_FIX_FE_COLOR_CHANGE_MINUTES", "CLIENT_ANALYZE_TEXT_MIN_LENGTH",
#     #         "CLIENT_ANALYZE_TEXT_MAX_LENGTH", "WEBTIP_PRODUCTION_SERVER_ADDRESS", "CHAMPIONSHIP_COMPONENT_ENABLED",
#     #         "BANKID_ORIGIN", "BANKID_CLIENT_ID", "BANKID_AUTH_QUERY_PARAMS", "BANKID_REDIRECT_URI",
#     #         "LIME_WS_ADDRESS_PUBLIC", "WEBTIP_CHAT_FRONTSTAGE_ENABLED", "FRONTSTAGE_CHAT_API_URL",
#     #         "MARKETING_NEWS_WEBTIP_ENABLED", "ODDS_TOURNAMENT_TREE_AUTO_REFRESH_INTERVAL",
#     #         "CLIENTS_SOURCE_FINANCES_VISIBLE", "SEO_FB_APP_ID", "LOGO_FILENAME_POSTFIX", "NO_DEPOSIT_BONUS_AMOUNT",
#     #         "PEP_FRONTEND_2022_ENABLED", "SOURCES_OF_FINANCE_SK_ENABLED_2023", "WEBTIP_MOBILE_SERVER_ADDRESS",
#     #         "PRODUCTION_WEB_ADDRESS_ALTERNATE", "START_CASINO_BONUS__MAX_AMOUNT",
#     #         "SELF_RESTRICTION_COUNT_DAYS_LIMIT_UP", "SELF_RESTRICTION_COUNT_DAYS_LIMIT_DOWN",
#     #         "SELF_RESTRICTION_COUNT_DAYS_LIMIT_UP_BETS", "SELF_RESTRICTION_COUNT_DAYS_LIMIT_DOWN_BETS",
#     #         "SELF_RESTRICTION_ACCOUNT_ENABLED", "SELF_RESTRICTION_BETTING_ENABLED", "SELF_RESTRICTION_CASINO_ENABLED",
#     #         "SELF_RESTRICTION_BETTING_DAYS_LIMITS_ENABLED", "SELF_RESTRICTION_CASINO_DAYS_LIMITS_ENABLED",
#     #         "SELF_LIMIT_MAX_TICKET_BET_ENABLED", "LIVE_FEEDBACK_TEXT_MAX_LENGTH", "TC_FROZEN_SCORE_ENABLED",
#     #         "GDPR_AGREEMENTS_ENABLE", "WEBTIP_FORUM_MAX_COMMENTS_ON_THE_PAGE", "ODDS_INITIAL_MATCH_LOAD_NUMBER",
#     #         "ODDS_MATCH_LOAD_NUMBER", "COM_LAYER_CTA_TEXT", "ZOHH_SK_CASINO_ENABLE", "PYRAMID_EXPIRATION",
#     #         "CONTESTS_NEW_DASHBOARD_ENABLED", "MULTICONVERSATION_MAX_MEMBERS_COUNT", "CASINO_TRANSACTIONS_X_LAST_DAYS",
#     #         "PYRAMID_ENABLED", "MARATON_V2_ENABLED", "BLOG_MIN_TEXT_LENGTH", "BLOG_VIP_MIN_TEXT_LENGTH",
#     #         "BLOG_MAX_TEXT_LENGTH", "BLOG_MAX_UPDATE_COUNT", "STREAM_LOG_WT_ENABLED", "STREAM_LBX_URL_ANALYTICS",
#     #         "STREAM_AUGMENTED_DEFAULT", "BONUS_CURRENCY_CONVERSION_VISIBLE", "WEBTIP_PAY_ACCOUNT_LOW_ATTENTION",
#     #         "GDPR_INFO_OBLIGATION_HELP_URL", "PRIVATE_MESSAGE_MAX_LENGTH", "FORUM_ENABLED", "MIN_IMPROPER_TEXT_LENGHT",
#     #         "MAX_IMPROPER_TEXT_LENGHT", "AML_SK_FINANCIAL_SOURCES_ENABLED", "IMG_GOLF_WIDGET_VERSION",
#     #         "IMG_MMA_WIDGET_VERSION", "PRIVATE_MESSAGES_CHAT_PANEL_ENABLED", "CLIENT_PROFILE_MAX_DISPLAYED_TICKETS",
#     #         "CASINO_BANNERS_LATENCY", "CASINO_AMOUNT_FOR_DOTATION_REQUEST", "CASINO_CONTINUOUS_PLAYTIME_LIMIT",
#     #         "CASINO_CONTINUOUS_LIVE_DEALER_PLAYTIME_LIMIT", "CASINO_LEGISLATION_PLAYTIME_BREAK_LIMIT",
#     #         "CASINO_LEGISLATION_LIVE_DEALER_PLAYTIME_BREAK_LIMIT", "CASINO_BONUSES_REFRESH_TIMEOUT",
#     #         "CASINO_LOTTIE_INTRO_FRAMES_COUNT", "CASINO_JACKPOT_LEVEL_MAXIMUM_AMOUNT", "BONUS_ENGINE_SB_ENABLED",
#     #         "EMOTICONS_RELOAD_INTERVAL_MINUTES", "INTERNATIONAL_MAIN_FORUM_CATEGORY_ID",
#     #         "SR_COUNT_LOGIN_MONTH_RECOMMENDED", "SR_PERIOD_DAY_LOGIN_RECOMMENDED", "SR_EXCLUSION_TIME_RECOMMENDED",
#     #         "SR_AMOUNT_BET_DAY_RECOMMENDED", "SR_AMOUNT_LOST_DAY_RECOMMENDED", "SR_AMOUNT_BET_MONTH_RECOMMENDED",
#     #         "SR_AMOUNT_LOST_MONTH_RECOMMENDED", "SR_AMOUNT_BET_DAY_RECOMMENDED_CASINO",
#     #         "SR_AMOUNT_LOST_DAY_RECOMMENDED_CASINO", "SR_AMOUNT_BET_MONTH_RECOMMENDED_CASINO",
#     #         "SR_AMOUNT_LOST_MONTH_RECOMMENDED_CASINO", "MAX_SURVEY_QUESTIONS_FOR_BLOG_COUNT",
#     #         "WEBTIP_RESULTS_HISTORY_IN_DAYS", "FOLLOWERS_NOTIFICATION_ARCHIVE_INIT", "DATA_USE_CONSENT_INFO",
#     #         "REGISTRATION_REDESIGN_CZ_ENABLED_2021_WEBTIP", "TICKET_BUILDER_NEW_KOMBI_DRAG_DROP_ENABLED",
#     #         "TICKET_BUILDER_NEW_KOMBI_SORT_ENABLED", "ENTRY_BONUS_CASINO_BONUS_ENABLED",
#     #         "LIVE_MATCH_DETAIL_INSPIRATION_ENABLED", "TIPPAY_ENABLED", "PLATBA_MOBILOM_CODE_WORD",
#     #         "PLATBA_MOBILOM_DEFAULT_AMOUNT", "PLATBA_MOBILOM_POSSIBLE_AMOUNTS", "PLATBA_MOBILOM_PHONE_NUMBER",
#     #         "BLOG_CLIENT_TIPCAST", "VOICE_COMMENTARY_ENABLED", "WEBTIP_BET_BONUS_COEFFICIENT",
#     #         "PERSONAL_BLOG_MIN_NUMBER_OF_CHARACTERS", "PERSONAL_BLOG_MIN_VIDEO_DURATION_IN_SECONDS",
#     #         "CLIENT_ACCOUNT_CANCELLATION_ENABLED", "INFORMATION_OBLIGATION_RVO_LINK",
#     #         "CLIENT_ACCOUNT_CANCELLATION_URL_RESPONSIBLE_GAMING",
#     #         "CLIENT_ACCOUNT_CANCELLATION_EMAIL_RESPONSIBLE_GAMING", "CLIENT_ACCOUNT_CANCELLATION_URL_RVO",
#     #         "FANTASY_THEMATIC_FORUM_ID", "BLOG_PEREX_MIN_LENGTH", "BLOG_PEREX_MAX_LENGTH", "MAP_NG", "AGORA_APP_ID",
#     #         "BOOSTER_ENABLED", "SHOW_NHL_LOGOS", "AFFILIATE_WEB_SERVER_ADDRESS", "DVACET_ZA_20_DEFAULT_TIPS_COUNT",
#     #         "TICKET_ARENA_PM_MIN_INSPIRATIONS", "IMG_PROXY_ENABLED", "IMG_PROXY_HOSTNAMES", "THREATMARK_ENABLED",
#     #         "REGISTRATION_GEOBLOCATION", "MOBILE_APP_DOWNLOAD_GEOBLOCATION", "SMARTLOOK_KEY", "CONTACT_CRYPTO_EMAIL",
#     #         "CONTACT_CRYPTO_PHONE", "RECOMMENDED_MATCH_FORUMS_ENABLED", "DAY_FILTER_HOUR_OVER",
#     #         "SHOW_HISTORIC_DOCUMENTS", "COOL_OFF_DAYS_MAX", "COOL_OFF_EXTENSION_ENABLED", "MFA_PROJECT",
#     #         "SUPER_ODD_MAX_AMOUNT_PAID_PER_CLIENT", "PREMATCH_SERIES_ENABLED", "BINGO_ENABLED",
#     #         "PAYMENT_CHANNEL_CARD_DELETE_FORM_ENABLED", "PAYOUTS_UNDER_LIMIT_INFO_ENABLED", "SR_AMOUNT_BET_DAY_MAX",
#     #         "SR_AMOUNT_BET_DAY_MIN", "SR_AMOUNT_BET_MONTH_MAX", "SR_AMOUNT_BET_MONTH_MIN", "SR_AMOUNT_LOST_DAY_MAX",
#     #         "SR_AMOUNT_LOST_DAY_MIN", "SR_AMOUNT_LOST_MONTH_MAX", "SR_AMOUNT_LOST_MONTH_MIN",
#     #         "SR_COUNT_LOGIN_MONTH_MAX", "SR_COUNT_LOGIN_MONTH_MIN", "SR_EXCLUSION_TIME_MAX", "SR_EXCLUSION_TIME_MIN",
#     #         "SR_PERIOD_DAY_LOGIN_MAX", "SR_PERIOD_DAY_LOGIN_MIN", "SELF_RESTRICTION_DISPLAY_MS",
#     #         "BONUS_TILE_ACTION_CODE_INFORMATION", "MOBILE_APP_APPLE_URL", "MOBILE_APP_GOOGLE_URL",
#     #         "MOBILE_APP_HUAWEI_URL", "DOWNLOAD_APP_FROM_GOOGLE_PLAY_ENABLED", "SPORTSBOOK_HOMEPAGE_2_ENABLED",
#     #         "MATCH_DETAIL_UNITED", "WEBTIP_GOOGLE_TAG_MANAGER_4_ID", "BLOG_MAX_SURVERY_NAME_LENGTH",
#     #         "BLOG_MAX_POLL_NAME_LENGTH", "KORUNKA_SCRATCHCARD_PAGE", "CLIENT_EVENTS_SUCCESSRATE_YEAR_NUMBER",
#     #         "AIRCASH_HOMEPAGE_URL"], "restartSession": False, "platform": "WEB", "consents": {}
#     # }
#     # err, res = post_content(
#     #     connect=connect,
#     #     url=url,
#     #     type_content='json',
#     #     params=params,
#     # )
#     # print(res.get('sessionUuid'))
#
#     url = 'https://www.tipsport.cz/rest/offer/v1/live/in-play/entities'
#     err, res = get_content(
#         connect=connect,
#         url=url,
#         type_content='json',
#     )
#     print(res)
#
#     url = 'https://www.tipsport.cz/rest/offer/v1/live/in-play/event-groups/odds'
#     err, res = get_content(
#         connect=connect,
#         url=url,
#         type_content='json',
#     )
#     print(res)
#
#     # headers['Content-Length'] = '160'
#
#     params = {
#         "section": "IN_PLAY", "filter": {
#             "tracker": False, "audioStream": False, "videoStream": False, "tipbankContest": False, "voiceChannel": False
#         }, "order": "COMPETITION_SPORT"
#     }
#     url = 'https://www.tipsport.cz/rest/offer/v1/live/event-groups/matches'
#     err, res = post_content(
#         connect=connect,
#         url=url,
#         type_content='json',
#         params=params
#     )
#     print(res)

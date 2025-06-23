import time
import zipfile
import os.path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common.exceptions import InvalidArgumentException

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions

from selenium.webdriver import Edge
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions


def get_plugin_file(*, plugin_file=None, host, port, login, password):
    if not plugin_file:
        plugin_file = 'proxy_auth_plugin.zip'
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
            singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
            },
            bypassList: ["localhost"]
            }
        };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (host, port, login, password)

    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr('manifest.json', manifest_json)
        zp.writestr('background.js', background_js)
    return plugin_file


def get_chrome_driver(*, exe_path=None, proxy=None, is_security=False, is_visible=True, load_strategy='normal'):
    driver = None
    settings = dict()
    try:
        service = ChromeService(executable_path=exe_path)
        options = ChromeOptions()
        options.page_load_strategy = load_strategy  # normal / eager / none
        if not is_visible:
            options.add_argument('--headless')  # Скрытый режим
            # options.add_argument('--disable-gpu')
            pass

        if is_security:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            # options.add_argument(f'--user-agent={user_agent}')
            options.add_argument(f'--accept-language=en-US,en;q=0.5')
            options.add_argument('--Content-Language=en')
            # options.add_argument('--lang=en_US.UTF-8')
            options.add_argument('--disable-gpu')
            options.add_argument('--lang=en')
            # options.add_argument('--lang=en-US,en')
            options.add_argument('--timezone=Europe/London')

            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # options.add_argument('--disable-system-timezone-automatic-detection')

            # 'отключает загрузку картинок'
            # options.experimental_options['prefs'] = {'profile.managed_default_content_settings.images': 2, }

        if proxy:
            host = proxy.get('host')
            port = proxy.get('port')
            login = proxy.get('login')
            password = proxy.get('password')
            if login and password:
                plugin_file = get_plugin_file(host=host, port=port, login=login, password=password, )
                options.add_extension(plugin_file)
            else:
                options.add_argument(f'--proxy-server={host}:{port}')  # proxy = '143.198.228.250'
            pass

        settings['service'] = service
        settings['options'] = options
        driver = Chrome(**settings, )
    except Exception as e:
        driver = None
        print('_get_chrome_wd():', e)
    return driver


def get_firefox_driver(*, exe_path=None, proxy=None, is_security=False, is_visible=True, load_strategy='normal'):
    driver = None
    settings = dict()
    try:
        service = FirefoxService(executable_path=exe_path)
        options = FirefoxOptions()
        options.page_load_strategy = load_strategy  # normal / eager / none
        if not is_visible:
            options.add_argument('--headless')  # Скрытый режим
            # options.log.level = "trace"
            # options.add_argument("--log-level=OFF")

        if is_security:
            user_agent = 'Firefox: Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0'
            options.add_argument(f'user-agent={user_agent}')
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("dom.push.enabled", False)
            options.set_preference("dom.webdriver.enabled", False)
            options.set_preference('useAutomationExtension', False)

        if not (proxy is None) and proxy:
            print(proxy)
            host = proxy.get('host')
            port = proxy.get('port')
            login = proxy.get('login')
            password = proxy.get('password')

            options.set_preference("network.proxy.type", 1)
            options.set_preference("network.proxy.http", host)
            options.set_preference("network.proxy.http_port", int(port))
            options.set_preference('network.proxy.socks', host)
            options.set_preference('network.proxy.socks_port', int(port))
            options.set_preference('network.proxy.socks_remote_dns', False)
            options.set_preference("network.proxy.ssl", host)
            options.set_preference("network.proxy.ssl_port", int(port))

        settings['options'] = options
        settings['service'] = service

        driver = Firefox(**settings, )
    except Exception as e:
        driver = None
        print('_get_chrome_wd():', e)
    return driver


def get_edge_driver(*, exe_path=None, proxy=None, is_security=False, is_visible=True, load_strategy='normal'):
    driver = None
    settings = dict()
    try:
        service = EdgeService(executable_path=exe_path)
        options = EdgeOptions()
        options.page_load_strategy = load_strategy  # normal / eager / none
        if not is_visible:
            options.add_argument('--headless')  # Скрытый режим
            # options.add_argument('--disable-gpu')
            pass

        if is_security:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            # options.add_argument(f'--user-agent={user_agent}')
            options.add_argument(f'--accept-language=en-US,en;q=0.5')
            options.add_argument('--Content-Language=en')
            # options.add_argument('--lang=en_US.UTF-8')
            options.add_argument('--disable-gpu')
            options.add_argument('--lang=en')
            # options.add_argument('--lang=en-US,en')
            options.add_argument('--timezone=Europe/London')

            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--autoplay-policy=no-user-gesture-required')
            options.add_experimental_option('excludeSwitches', ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)

            # options.add_argument('--disable-system-timezone-automatic-detection')
            # options.add_experimental_option('--disable-system-timezone-automatic-detection', '--local-timezone')

            # 'отключает загрузку картинок'
            # options.experimental_options['prefs'] = {'profile.managed_default_content_settings.images': 2, }

        if proxy:
            host = proxy.get('host')
            port = proxy.get('port')
            login = proxy.get('login')
            password = proxy.get('password')
            if login and password:
                plugin_file = get_plugin_file(host=host, port=port, login=login, password=password, )
                options.add_extension(plugin_file)
            else:
                options.add_argument(f'--proxy-server={host}:{port}')  # proxy = '143.198.228.250'
            pass

        settings['service'] = service
        settings['options'] = options
        driver = Edge(**settings, )
    except Exception as e:
        driver = None
        print('_get_chrome_wd():', e)
    return driver


class BrowserWD:
    def __init__(self, directory=None, ):
        self.wd_paths = dict()
        wd_dict = {
            'chrome': 'chromedriver.exe',
            'firefox': 'geckodriver.exe',
            'edge': 'msedgedriver.exe',
        }
        for wd_name in wd_dict:
            self.wd_paths[wd_name] = None
            if directory:
                file_path = f'{directory}{wd_dict[wd_name]}'
                if os.path.exists(file_path):
                    self.wd_paths[wd_name] = file_path

        self.driver_obj = None

    def set_web_drivers(self, name_browser, proxies=None, is_security=False, is_visible=True, load_strategy='normal'):
        self.quit_web_drivers()
        exe_path = self.wd_paths[name_browser]
        match name_browser:
            case 'chrome':
                self.driver_obj = get_chrome_driver(
                    exe_path=exe_path,
                    proxy=proxies,
                    is_security=is_security,
                    is_visible=is_visible,
                    load_strategy=load_strategy,
                )
            case 'firefox':
                self.driver_obj = get_firefox_driver(
                    exe_path=exe_path,
                    proxy=proxies,
                    is_security=is_security,
                    is_visible=is_visible,
                    load_strategy=load_strategy,
                )
            case 'edge':
                self.driver_obj = get_edge_driver(
                    exe_path=exe_path,
                    proxy=proxies,
                    is_security=is_security,
                    is_visible=is_visible,
                    load_strategy=load_strategy,
                )
            case _:
                return True, f'set_web_drivers - не валидный [name_browser]={name_browser}!'

        if self.driver_obj is None:
            return True, 'Не удалось создать подключение к веб-драйверу!'
        return False, 'Ok'

    def go_path(self, path):
        err, msg, res = False, 'Ok', None
        if self.driver_obj is None:
            return True, 'driver_obj = None', None
        if path is None:
            return True, 'path = None', None
        try:
            res = self.driver_obj.get(f'{path}')
            # self.driver_obj.execute_script("document.body.style.zoom='75%'")
            # self.driver_obj.set_window_size(1400, 1000)
        except InvalidArgumentException as e:
            print('go_path():', e)
            err, msg, res = True, 'Не удалось перейти по ссылке!', None
        except Exception as e:
            print('go_path():', e)
            err, msg, res = True, 'Перезапустите браузер!', False
        return err, msg, res

    def get_all(self, ):
        res = None
        try:
            res = self.driver_obj.page_source
        except Exception as e:
            print('get_all():', e)
        return res

    def get_url_page(self, ):
        return self.driver_obj.current_url

    def wait_page_source(self, *, xpath_req, time_err=10):
        try:
            WebDriverWait(self.driver_obj, time_err).until(
                expected_conditions.presence_of_element_located((By.XPATH, xpath_req))
            )
        except Exception as e:
            print('wait_page_source(self, *, xpath_req, time_err=10):', e)
            return False
        return True

    def _close_browser_win(self, ):
        if self.driver_obj is None:
            return
        try:
            self.driver_obj.close()
        except Exception as e:
            print('close_browser_win():', e)
        return

    def _quit_driver(self, ):
        if self.driver_obj is None:
            return
        try:
            self.driver_obj.quit()
        except Exception as e:
            print('quit_driver():', e)
        return

    def quit_web_drivers(self, ):
        self._close_browser_win()
        self._quit_driver()


if __name__ == '__main__':
    protocol = 'https'
    host = 'winline.ru'
    web_driver_obj = BrowserWD()
    err, msg = web_driver_obj.set_web_drivers(
        name_browser='firefox',
        proxy=None,
        is_security=False,
        is_visible=True,
        load_strategy='eager',
    )
    print(err, msg)
    web_driver_obj.go_path(path=f'{protocol}://{host}/stavki/sport/kiber_fifa')
    # input()
    time.sleep(6)
    contents = web_driver_obj.get_all()
    web_driver_obj.quit_web_drivers()
    from project_modules.universal_func.soup_func import get_soup_contents

    err, msg, soup = get_soup_contents(contents=contents)



    '''
    
    name='ww-feature-block-sport-dsk' ---> sport
        name='div', class='block-sport-header__title' ---> sport_name
    
    name='ww-feature-block-tournament-dsk' ---> tour
        name='span', class='block-tournament-header__title' ---> tour_name
        
    name='ww-feature-block-event-dsk' ---> match
        name='a' ---> match_name
        name='a'.get('href') ---> match_href
        name='span', class='header-left__time' ---> 2 items timer
        
        name='div', class='card__scoreboard' ---> sores
        name='div', class='coeffs-wrapper' ---> line
        
        name='div', class='card__body'
            if class='match-row-label' == 'матч'
            name='div', class='card__coeffs'
        OR
    
    
    '''
    matches_data_feed = list()
    match_num = 0
    for sports_soup in soup.find_all(name='ww-feature-block-sport-dsk'):
        sport_name_soup = sports_soup.find(name='div', attrs={'class': 'block-sport-header__title'})
        sport_name = sport_name_soup.get_text('|', strip=True) if sport_name_soup else None
        for tours_soup in sports_soup.find_all(name='ww-feature-block-tournament-dsk'):
            tour_name_soup = tours_soup.find(name='span', attrs={'class': 'block-tournament-header__title'})
            tour_name = tour_name_soup.get_text('|', strip=True) if tour_name_soup else None
            for i, match_raw_soup in enumerate(tours_soup.find_all(name='ww-feature-block-event-dsk')):  # , attrs={'class': ''})):
                _match_info_soup = match_raw_soup.find(name='a')
                match_name = _match_info_soup.get_text('|', strip=True).split('|')
                home_name, away_name, *_ = match_name + [None, None, None, ]
                match_href = _match_info_soup.get('href')
                match_id = None
                if match_href:
                    match_id = match_href.split('/')[-1]
                _match_line_info_soup = match_raw_soup.find_all(name='div', attrs={'class': 'card__body'})
                for _mlis in _match_line_info_soup:
                    part_name_soup = _mlis.find(name='div', attrs={'class': 'match-row-label'})
                    if part_name_soup:
                        part_name = part_name_soup.get_text(strip=True)
                        raw_markets_soup = _mlis.find_all(name='ww-feature-event-market-dsk')
                        raw_markets_list = list()
                        for raw_market_soup in raw_markets_soup:
                            raw_odds_soup = raw_market_soup.find_all(name='span', attrs={'class': 'ng-star-inserted'})
                            raw_odds = [ro.get_text('|', strip=True) for ro in raw_odds_soup]
                            raw_markets_list.append(raw_odds)
                        mdf = {
                            'match_id': match_id,
                            'sport_name': sport_name,
                            'tour_name': tour_name,
                            'home_name': home_name,
                            'away_name': away_name,
                            'odds_feed': {part_name: raw_markets_list},
                        }
                        matches_data_feed.append(mdf)
                        match_num += 1
                        print(match_num, mdf)
    pass



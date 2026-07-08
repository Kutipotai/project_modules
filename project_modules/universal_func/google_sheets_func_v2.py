import gspread
from gspread import (
    Client,
    Spreadsheet,
    Worksheet,
    service_account,
    service_account_from_dict,
)
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import time
import os
import contextlib

logger = logging.getLogger(__name__)


def _get_proxy(*, proxies, **kwargs):
    """
    Формирует словарь прокси из структурированных данных.
    """
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
            _proxies = {'http': _proxy, 'https': _proxy}
            logger.info(f"🔒 Прокси настроен: {_protocol}://{_host}:{_port}")

    return _proxies


def _create_session_with_proxy(proxies=None, max_retries=3):
    """
    Создает сессию requests с прокси и повторными попытками.
    """
    session = requests.Session()

    # Настраиваем повторные попытки
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=2,  # Увеличил для более долгих пауз
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "PUT", "POST", "PATCH", "DELETE"]
    )

    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Настраиваем прокси
    if proxies:
        proxy_dict = _get_proxy(proxies=proxies)
        if proxy_dict:
            session.proxies = proxy_dict
            logger.info(f"✅ Прокси применен к сессии")

    # Увеличиваем таймауты
    session.timeout = 120

    return session


def _get_client(
        client_filename=None,
        client_dict=None,
        timeout: None | tuple[float | int, float | int] = None,
        proxies=None,
        max_retries=3,
        **kwargs
):
    """
    Создает клиент для работы с Google Sheets.
    """
    client = None

    # СОЗДАЕМ СЕССИЮ С ПРОКСИ (она будет жить вместе с клиентом)
    session = _create_session_with_proxy(proxies=proxies, max_retries=max_retries)

    try:
        # Пытаемся создать клиент с сессией
        if client_filename:
            # Пробуем передать session как http_session
            try:
                client = service_account(filename=client_filename, http_session=session)
            except TypeError:
                # Если не поддерживается, создаем обычный клиент
                client = service_account(filename=client_filename)
                # И потом подменяем сессию
                if hasattr(client, 'session'):
                    client.session = session
                elif hasattr(client, '_session'):
                    client._session = session

        elif client_dict:
            try:
                client = service_account_from_dict(client_dict, http_session=session)
            except TypeError:
                client = service_account_from_dict(client_dict)
                if hasattr(client, 'session'):
                    client.session = session
                elif hasattr(client, '_session'):
                    client._session = session
        else:
            logger.error("❌ Не передан ни client_filename, ни client_dict")
            return None

    except Exception as e:
        logger.error(f"❌ Ошибка при создании клиента: {e}")
        return None

    if client is None:
        return None

    # Настраиваем таймауты
    if timeout:
        timeout = tuple(timeout)
    else:
        timeout = (60, 120)  # Увеличенные таймауты

    client.set_timeout(timeout)

    logger.info(f"✅ Клиент Google Sheets создан (таймаут: {timeout}, max_retries: {max_retries})")
    return client


def get_table_by_url(client: Client, table_url, **kwargs):
    """Получение таблицы из Google Sheets по ссылке."""
    return client.open_by_url(table_url)


def get_table_by_id(client: Client, table_url, **kwargs):
    """Получение таблицы из Google Sheets по ID таблицы."""
    return client.open_by_key(table_url)


def get_worksheet_info(table: Spreadsheet, **kwargs) -> dict:
    """Возвращает количество листов в таблице и их названия."""
    worksheets = table.worksheets()
    worksheet_info = {
        "count": len(worksheets),
        "names": [worksheet.title for worksheet in worksheets]
    }
    return worksheet_info


def get_gs_tables(
        *,
        table_id,
        _range='A1',
        proxies=None,
        max_retries=3,
        **kwargs,
):
    """Получение списка листов в таблице."""
    err = None
    res = list()
    try:
        client = _get_client(proxies=proxies, max_retries=max_retries, **kwargs)
        if client is None:
            err = f'get_gs_tables: client is None'
            return err, res

        table = get_table_by_id(client, table_id)
        worksheet_info = get_worksheet_info(table=table)
        res = worksheet_info['names']
    except Exception as e:
        err = f'get_gs_tables: {e}'
        logger.error(err)
    return err, res


def get_gs_data(
        *,
        table_id,
        sheet_name,
        _range='A1',
        cols_name=None,
        skip_line=None,
        proxies=None,
        max_retries=3,
        **kwargs,
):
    """Получение данных из Google Sheets."""
    err = None
    df = list()
    if skip_line is None:
        skip_line = list()

    try:
        client = _get_client(proxies=proxies, max_retries=max_retries, **kwargs)
        if client is None:
            err = f'get_gs_data: client is None'
            return err, df

        table = get_table_by_id(client, table_id)
        sheet = table.worksheet(sheet_name)
        data_gs = sheet.get(_range)

        if cols_name is None:
            cols_name = {k: i for i, k in enumerate(data_gs[0])}
            data_gs = data_gs[1:]

        for n, d in enumerate(data_gs):
            if n in skip_line:
                continue
            df.append({k: (d[i] if len(d) > i else None) for k, i in cols_name.items()})

    except Exception as e:
        err = f'get_gs_data: {e}'
        logger.error(err)

    return err, df


def _update_with_retry(sheet, data, range_name, max_retries=5):
    """
    Обновление с повторными попытками при ошибках соединения.
    """
    errors = list()

    for attempt in range(max_retries):
        try:
            logger.info(f"🔄 Попытка обновления {attempt + 1}/{max_retries}, строк: {len(data)}")
            sheet.update(data, range_name)
            logger.info(f"✅ Обновление успешно")
            return errors

        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                ConnectionResetError,
                gspread.exceptions.APIError) as e:

            error_str = str(e)
            if "10054" in error_str or "Connection" in error_str or "timeout" in error_str.lower():
                wait_time = 2 ** attempt * 3  # 3, 6, 12, 24, 48 секунд
                msg = f"⚠️ Ошибка соединения (попытка {attempt + 1}): {e}"
                errors.append(msg)
                logger.warning(msg)

                if attempt < max_retries - 1:
                    logger.info(f"⏳ Ожидание {wait_time} сек перед повторной попыткой...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Все попытки не удались")
            else:
                errors.append(f"❌ Критическая ошибка: {e}")
                logger.error(f"❌ Критическая ошибка: {e}")
                break

    return errors


def _update_large_data(sheet, data, range_name, chunk_size=200, max_retries=5):
    """
    Обновление больших данных по частям с увеличенными задержками.
    """
    all_errors = list()
    total_rows = len(data)

    if total_rows == 0:
        return all_errors

    cols_count = len(data[0]) if data else 0

    # Определяем стартовую букву колонки
    if ':' in range_name and '!' in range_name:
        range_part = range_name.split('!')[-1]
        start_letter = range_part.split(':')[0][0]
    else:
        start_letter = 'A'

    for start_row in range(0, total_rows, chunk_size):
        end_row = min(start_row + chunk_size, total_rows)
        chunk = data[start_row:end_row]

        start_col_letter = start_letter
        end_col_letter = chr(ord(start_col_letter) + cols_count - 1)

        chunk_range = f"{start_col_letter}{start_row + 1}:{end_col_letter}{end_row}"

        try:
            logger.info(f"📦 Обновление чанка {start_row // chunk_size + 1}: строки {start_row + 1}-{end_row}")

            errors = _update_with_retry(
                sheet=sheet,
                data=chunk,
                range_name=chunk_range,
                max_retries=max_retries
            )

            if errors:
                all_errors.extend(errors)
                logger.warning(f"⚠️ Чанк {start_row // chunk_size + 1} обновлен с ошибками")
            else:
                logger.info(f"✅ Чанк {start_row // chunk_size + 1} обновлен")

            # Увеличенная пауза между чанками
            if start_row + chunk_size < total_rows:
                delay = 3  # 3 секунды между чанками
                logger.info(f"⏳ Пауза {delay} сек перед следующим чанком...")
                time.sleep(delay)

        except Exception as e:
            msg = f"❌ Ошибка при обновлении чанка {start_row // chunk_size + 1}: {e}"
            all_errors.append(msg)
            logger.error(msg)

    return all_errors


def set_gs_data(
        *,
        data,
        table_id,
        sheet_name,
        _range='A1',
        is_colum_name=True,
        need_keys=None,
        is_clear=False,
        is_clean_range=False,
        proxies=None,
        max_retries=5,
        chunk_size=200,  # Уменьшил до 200
        **kwargs,
):
    """
    Обновление данных в Google Sheets с поддержкой прокси и повторных попыток.
    """
    errors = list()

    if not data:
        logger.warning("⚠️ Нет данных для записи")
        return errors

    try:
        # Клиент создается с прокси, который остается активным
        client = _get_client(
            proxies=proxies,
            max_retries=max_retries,
            **kwargs
        )

        if client is None:
            msg = f'set_gs_data: client is None'
            errors.append(msg)
            logger.error(msg)
            return errors

        table = get_table_by_id(client, table_id)

        # Подготавливаем данные
        match_keys = [k for k in data[0]]
        if need_keys:
            match_keys = need_keys

        mdf = list()
        for d in data:
            mdf.append([d.get(k) for k in match_keys])

        if is_colum_name:
            res_df = [match_keys] + mdf
        else:
            res_df = mdf

        sheet = table.worksheet(sheet_name)

        if is_clear:
            logger.info("🗑️ Очистка всего листа")
            sheet.clear()
        if is_clean_range:
            logger.info(f"🗑️ Очистка диапазона {_range}")
            sheet.batch_clear([_range])

        if len(res_df) > chunk_size:
            logger.info(f"📊 Разбиваем обновление на чанки по {chunk_size} строк (всего {len(res_df)} строк)")
            errors = _update_large_data(
                sheet=sheet,
                data=res_df,
                range_name=_range,
                chunk_size=chunk_size,
                max_retries=max_retries
            )
        else:
            errors = _update_with_retry(
                sheet=sheet,
                data=res_df,
                range_name=_range,
                max_retries=max_retries
            )

    except Exception as e:
        msg = f'set_gs_data: {e}'
        errors.append(msg)
        logger.error(msg)

    return errors


def test_proxy(proxies=None):
    """
    Тестирует работу прокси.
    """
    if not proxies:
        logger.warning("⚠️ Прокси не передан для теста")
        return False

    proxy_dict = _get_proxy(proxies=proxies)
    if not proxy_dict:
        logger.error("❌ Не удалось сформировать прокси")
        return False

    try:
        logger.info("🔍 Тестируем прокси...")
        response = requests.get(
            'https://api.ipify.org?format=json',
            proxies=proxy_dict,
            timeout=15
        )
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✅ Прокси работает! Ваш IP через прокси: {data.get('ip')}")
            return True
        else:
            logger.error(f"❌ Прокси ответил с кодом: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании прокси: {e}")
        return False

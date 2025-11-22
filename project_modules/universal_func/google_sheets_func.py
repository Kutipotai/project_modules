from gspread import (
    Client,
    Spreadsheet,
    Worksheet,
    service_account,
)

def get_table_by_url(client: Client, table_url):
    """Получение таблицы из Google Sheets по ссылке."""
    return client.open_by_url(table_url)


def get_table_by_id(client: Client, table_url):
    """Получение таблицы из Google Sheets по ID таблицы."""
    return client.open_by_key(table_url)


def get_worksheet_info(table: Spreadsheet) -> dict:
    """Возвращает количество листов в таблице и их названия."""
    worksheets = table.worksheets()
    worksheet_info = {
        "count": len(worksheets),
        "names": [worksheet.title for worksheet in worksheets]
    }
    return worksheet_info


def get_gs_data(
        *,
        client_filename,
        table_id,
        sheet_name,
        _range='A1',
        cols_name=None,
        skip_line=None,
):
    err = None
    df = list()
    if skip_line is None:
        skip_line = list()
    try:
        client = service_account(filename=client_filename)
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
            # df.append({k: v for k, v in zip_longest(cols_name, d, fillvalue=None)})
    except Exception as e:
        err = f'get_gs_data: {e}'
    return err, df


def set_gs_data(
        *,
        data,
        client_filename,
        table_id,
        sheet_name,
        _range='A1',
        is_colum_name=True,
        need_keys=None,
        is_clear=False,
        is_clean_range=False,
):
    errors = list()
    try:
        if not data:
            return errors
        client = service_account(filename=client_filename)
        table = get_table_by_id(client, table_id)
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
            sheet.clear()
        if is_clean_range:
            sheet.batch_clear([_range])
        sheet.update(res_df, _range)
    except Exception as e:
        msg = f'set_gs_data: {e}'
        errors.append(msg)
    return errors


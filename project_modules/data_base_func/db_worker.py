import sqlite3
import psycopg2
from psycopg2.extras import DictCursor, DictRow


def close_db(*, cur, conn, print_err=True, **kwargs):
    try:
        cur.close()
    except Exception as e:
        if print_err:
            print(f'close_db:', e)
    try:
        conn.close()
    except Exception as e:
        if print_err:
            print(f'close_db:', e)
    return


def delete_db(*, cur=None, table_name=None, other_query=None, **kwargs):
    err = None
    if not table_name:
        err = f'delete_db: {table_name} --> error arg:[table_name = str]'
        return err
    if cur is None:
        if settings_connect := kwargs.get('settings_connect'):
            err, conn, cur = custom_init_bd(**settings_connect)
            if err:
                close_db(cur=cur, conn=conn, print_err=False)
                return err
            err = delete_db(cur=cur, table_name=table_name, other_query=other_query, **kwargs)
            close_db(cur=cur, conn=conn, print_err=False)
            return err
        else:
            err = f'delete_db: {table_name} --> error empty settings_connect'
            return err
    if other_query is None:
        other_query = ''  # 'WHERE True'
    try:
        query = f'DELETE FROM {table_name} {other_query};'
        if kwargs.get('query'):
            query = kwargs.get('query')
        cur.execute(query)
    except sqlite3.Error as e:
        return f'delete_db: {table_name} --> {e}'
    return err


def delete_db_old(*, cur, table_name=None, data=None, primary_id=None, other_query=None, **kwargs):
    err = None
    if not table_name:
        err = f'delete_db: {table_name} --> error arg:[table_name = str]'
        return err
    if cur is None:
        if settings_connect := kwargs.get('settings_connect'):
            err, conn, cur = custom_init_bd(**settings_connect)
            if err:
                close_db(cur=cur, conn=conn, print_err=False)
                return err
            err = delete_db(
                cur=cur,
                table_name=table_name,
                data=data,
                primary_id=primary_id,
                other_query=other_query,
                **kwargs
            )
            close_db(cur=cur, conn=conn, print_err=False)
            return err
        else:
            err = f'delete_db: {table_name} --> error empty settings_connect'
            return err
    if other_query is None:
        other_query = ''  # 'WHERE True'
    try:
        if data:
            cur.execute(f'DELETE FROM {table_name} WHERE {primary_id}=:{primary_id};', data)
        else:
            cur.execute(f'DELETE FROM {table_name} {other_query};')
    except sqlite3.Error as e:
        return f'delete_db: {table_name} --> {e}'
    return err


def write_db_many(*, cur=None, table_name=None, data=None, other_query=None, is_update=False, ignor_keys=None, **kwargs):
    err = None
    if not data:
        return err
    if not table_name:
        err = f'write_db_many: {table_name} --> error arg:[table_name = str]'
        return err
    if cur is None:
        if settings_connect := kwargs.get('settings_connect'):
            err, conn, cur = custom_init_bd(**settings_connect)
            if err:
                close_db(cur=cur, conn=conn, print_err=False)
                return err
            err = write_db_many(
                cur=cur,
                table_name=table_name,
                data=data,
                other_query=other_query,
                is_update=is_update,
                ignor_keys=ignor_keys,
                **kwargs
            )
            close_db(cur=cur, conn=conn, print_err=False)
            return err
        else:
            err = f'write_db_many: {table_name} --> error empty settings_connect'
            return err
    if ignor_keys is None:
        ignor_keys = list()
    if other_query is None:
        other_query = ''  # 'WHERE True'
    arg_list = ','.join([f'{x}' for x in data[0]])
    query_insert = ','.join([f':{x}' for x in data[0]])
    query_update = ','.join([f'{x}=:{x}' for x in data[0] if not (x in ignor_keys)])
    query = f'INSERT INTO {table_name} ({arg_list}) VALUES({query_insert}) ON CONFLICT '
    if is_update:
        query += f'DO UPDATE SET {query_update} {other_query};'
    else:
        query += f'DO NOTHING;'
    try:
        if kwargs.get('query'):
            query = kwargs.get('query')
        cur.executemany(query, data)
    # except sqlite3.Error as e:
    #     err = f'write_db_meny: {table_name} --> {e}'
    except Exception as e:
        err = f'write_db_meny: {table_name} --> {e}'
    return err


def read_db_many(*, cur=None, table_name=None, many_query=None, other_query=None, keys=None, is_dict=True, **kwargs):
    err = None
    def_value = list()
    if is_dict:
        def_value = dict()
    if not table_name:
        err = f'read_db_many: {table_name} --> error arg:[table_name = str]'
        return err, def_value, list()
    if cur is None:
        if settings_connect := kwargs.get('settings_connect'):
            err, conn, cur = custom_init_bd(**settings_connect)
            if err:
                close_db(cur=cur, conn=conn, print_err=False)
                return err, def_value, list()
            err, res_df, res_keys = read_db_many(
                cur=cur,
                table_name=table_name,
                many_query=many_query,
                other_query=other_query,
                keys=keys,
                is_dict=is_dict,
                **kwargs
            )
            close_db(cur=cur, conn=conn, print_err=False)
            return err, res_df, res_keys
        else:
            err = f'read_db_many: {table_name} --> error empty settings_connect'
            return err, def_value, list()
    if other_query is None:
        other_query = ''  # 'WHERE True'
    try:
        keys_item = f"{', '.join(str(x) for x in keys)}" if keys else '*'
        if many_query:
            kq = many_query.get('k')
            vq = many_query.get('v')
            if not all([kq, vq]):
                err = f'read_db_many: {table_name} --> error arg:[data = dict(k=str, v=list)]'
                return err, def_value, list()
            if other_query and 'where' in other_query.lower():
                other_query = other_query.lower().replace('where', 'and')
            other_query = f"where {kq} in ({','.join(['?' for _ in vq])}) {other_query}"
            query = f'SELECT {keys_item} FROM {table_name} {other_query};'
            output_obj = cur.execute(query, vq)
        else:
            query = f'SELECT {keys_item} FROM {table_name} {other_query};'
            if kwargs.get('query'):
                query = kwargs.get('query')
            output_obj = cur.execute(query)
        res_keys = [tup[0] for tup in output_obj.description]
        res_df = cur.fetchall()
        if is_dict:
            res_df = [{res_keys[i]: v for i, v in enumerate(row)} for row in res_df]
    except sqlite3.Error as e:
        res_df = def_value
        res_keys = list()
        err = f'read_db_many: {table_name} --> {e}'
    return err, res_df, res_keys


def update_db(*, cur, table_name, data, primary_id, ignor_keys=None):
    err, msg = False, 'Ok'
    if ignor_keys is None:
        ignor_keys = list()
    ignor_keys.append(primary_id)
    event_update = ','.join([f'{x}=:{x}' for x in data if not (x in ignor_keys)])
    try:
        cur.execute(f'UPDATE OR IGNORE {table_name} SET {event_update} WHERE {primary_id}=:{primary_id};', data)
    except sqlite3.Error as e:
        return True, f'update_db: {e}'
    return err, msg


def write_db(*, cur, table_name, data, option='update', primary_id='id', ignor_keys=None):
    err, msg = False, 'Ok'
    # if not data:
    #     return err, msg
    # match data:
    #     case list():
    #         data_key = list(data[0])
    #     case _:
    #         data_key = list(data)
    event_insert_into = ','.join([f':{x}' for x in data])
    event_insert_values = ','.join(data)
    try:
        if option == 'update':
            err, msg = update_db(
                cur=cur, table_name=table_name, data=data, primary_id=primary_id, ignor_keys=ignor_keys,
            )
            cur.execute(
                f'INSERT OR IGNORE INTO {table_name} ({event_insert_values}) VALUES ({event_insert_into});', data
            )
            return err, msg
        if option == 'replace':
            cur.execute(
                f'INSERT OR REPLACE INTO {table_name} ({event_insert_values}) VALUES ({event_insert_into});', data
            )
            return err, msg
        if option == 'insert':
            cur.execute(
                f'INSERT OR IGNORE INTO {table_name} ({event_insert_values}) VALUES ({event_insert_into});', data
            )
            return err, msg
    except sqlite3.Error as e:
        return True, f'write_db: {e}'
    return err, msg


def read_db(*, cur, table_name, data=None, primary_id='id', other_query='', keys=None):
    err, msg, res = False, 'Ok', list()
    try:
        if data is None:
            cur.execute(f'SELECT * FROM {table_name} {other_query};')
        elif keys:
            keys_item = ', '.join(keys)
            cur.execute(f'SELECT ({keys_item}) FROM {table_name} {other_query};')
        else:
            cur.execute(f'SELECT * FROM {table_name} WHERE {primary_id}=:{primary_id} {other_query};', data)

        res = cur.fetchall()
    except sqlite3.Error as e:
        return True, f'read_db: {e}', list()
    return err, msg, res


def keys_db(*, cur, table_name, **kwargs):
    err, res = None, dict()
    try:
        cur.execute(f"PRAGMA table_info({table_name})")
        res = {v[1]: i for i, v in enumerate(cur.fetchall())}
    except Exception as e:
        res = dict()
        err = f'keys_db: {table_name} --> {e}'
    return err, res


def custom_default_option_db(*, cur, table_name, scheme, wal=False, **kwargs):
    err = None
##    cur.execute('''PRAGMA synchronous = OFF''') # EXTRA
##    cur.execute('''PRAGMA journal_mode = OFF''') # WAL
    if wal:
        cur.execute('''PRAGMA journal_mode=wal''')
    scheme_info = ','.join([f"{x} {scheme[x]}" for x in scheme])
    try:
        cur.execute(f'CREATE TABLE IF NOT EXISTS {table_name}({scheme_info});') #WITHOUT ROWID
    except sqlite3.Error as e:
        err = f'custom_default_option_db: {table_name} --> error --> {e}'
    return err


def custom_init_bd(*, db_name=None, table_name=None, scheme=None, check_schemas=False, isolation_level=None, **kwargs):
    err, conn, cur = None, None, None
    if db_name is None:
        err = f'custom_init_bd: {db_name} --> {table_name} --> Неуказан "db_name"!'
        return err, conn, cur
    if check_schemas and (not scheme or not table_name):
        err = f'custom_init_bd: {db_name} --> {table_name} --> Неуказанна "scheme"!'
        return err, conn, cur
    try:
        conn = sqlite3.connect(f'{db_name}', isolation_level=isolation_level)
        cur = conn.cursor()
        if check_schemas:
            if not custom_default_option_db(cur=cur, table_name=table_name, scheme=scheme, wal=True):
                conn.commit()
            else:
                close_db(cur=cur, conn=conn)
                err = f'custom_init_bd: {db_name} --> {table_name} --> Ошибка подключения к БД!'
    except Exception as e:
        close_db(cur=cur, conn=conn)
        err = f'custom_init_bd: {db_name} --> {table_name} --> Ошибка подключения к БД! {e}'
    return err, conn, cur


def first_start_db(*, setting_database, print_err=True, **kwargs):
    err = None
    db_name = setting_database.get('db_name')
    tables = setting_database.get('tables', list())
    for table in tables:
        err, conn, cur = custom_init_bd(db_name=db_name, check_schemas=True, **table)
        close_db(cur=cur, conn=conn, print_err=False)
        if err and print_err:
            print(f'first_start_db: {db_name} --> ', err)
    return err


def write_db_many_pg(
        *,
        cursor=None,
        table_name,
        pid=None,
        data: list | dict,
        other_query=None,
        is_update=True,
        ignor_keys=None,
        **kwargs
):
    err = None
    try:
        if cursor is None:
            if settings_connect := kwargs.get('settings_connect'):
                with psycopg2.connect(**settings_connect) as conn:
                    with conn.cursor(cursor_factory=DictCursor) as cursor:
                        err = write_db_many_pg(
                            cursor=cursor,
                            table_name=table_name,
                            pid=pid,
                            data=data,
                            other_query=other_query,
                            is_update=is_update,
                            ignor_keys=ignor_keys,
                            **kwargs
                        )
                        conn.commit()
                        return err
            else:
                return f'write_db_postgresql: {table_name} --> error empty settings_connect; {is_update=}; {pid=}'
        if ignor_keys is None:
            ignor_keys = list()
        if other_query is None:
            other_query = ''  # 'WHERE True'
        match data:
            case list() as df if df and type(df[0]) is list:
                if is_update or not pid:
                    return f'write_db_postgresql: {table_name} --> error data type list([list()]); {is_update=}; {pid=}'
                data_keys = None
                val_sim = ', '.join(['%s' for _ in data[0]])
                keys_item = ''
            case list() as df if df and type(df[0]) is dict:
                data_keys = list(data[0])
                val_sim = ', '.join([f'%({k})s' for k in data_keys])
                keys_item = f"({', '.join(data_keys)})"
            case _:
                return f'write_db_postgresql: {table_name} --> error data type'
        query = f"INSERT INTO {table_name} {keys_item} VALUES ({val_sim}) ON CONFLICT "
        if is_update and data_keys and pid:
            ignor_keys.append(pid)
            keys_item_update = ', '.join([f"{dk}=EXCLUDED.{dk}" for dk in data_keys if not (dk in ignor_keys)])
            query += f'({pid}) DO UPDATE SET {keys_item_update} {other_query};'
        else:
            query += f'DO NOTHING;'
        cursor.executemany(query, data)
    except Exception as e:
        err = f'write_db_many_pg: {table_name} --> except: {e}'
        if kwargs.get('print_err'):
            print(err)
    return err


def read_db_many_pg(*, cursor=None, table_name, other_query=None, keys=None, is_dict=True, **kwargs):
    result = None
    try:
        if cursor is None:
            if settings_connect := kwargs.get('settings_connect'):
                with psycopg2.connect(**settings_connect) as conn:
                    with conn.cursor(cursor_factory=DictCursor) as cursor:
                        return read_db_many_pg(
                            cursor=cursor,
                            table_name=table_name,
                            other_query=other_query,
                            keys=keys,
                            is_dict=is_dict,
                            **kwargs
                        )
            else:
                print(f'read_db_postgresql: {table_name} --> error empty settings_connect')
                return list()
        if other_query is None:
            other_query = ''  # 'WHERE True'
        keys_item = f"({', '.join(str(x) for x in keys)})" if keys else '*'
        query = f'SELECT {keys_item} FROM {table_name} {other_query};'
        cursor.execute(query)
        result = cursor.fetchall()
        if is_dict:
            columns = list(cursor.description)
            return [{columns[i].name: v for i, v in enumerate(row)} for row in result]
    except Exception as e:
        err = f'read_db_many_pg: {table_name} --> except: {e}'
        if kwargs.get('print_err'):
            print(err)
    return result


def del_db_many_pg(*, cursor=None, table_name, other_query=None, **kwargs):
    err = None
    try:
        if cursor is None:
            if settings_connect := kwargs.get('settings_connect'):
                with psycopg2.connect(**settings_connect) as conn:
                    with conn.cursor(cursor_factory=DictCursor) as cursor:
                        err = del_db_many_pg(
                            cursor=cursor,
                            table_name=table_name,
                            other_query=other_query,
                            **kwargs
                        )
                        conn.commit()
                        return err
            else:
                err = f'del_db_many_pg: {table_name} --> error empty settings_connect'
                return err
        if other_query is None:
            other_query = ''  # 'WHERE True'
        query = f'DELETE FROM {table_name} {other_query};'
        cursor.execute(query)
    except Exception as e:
        err = f'del_db_many_pg: {table_name} --> except: {e}'
        if kwargs.get('print_err'):
            print(err)
    return err


if __name__ == '__main__':
    pass

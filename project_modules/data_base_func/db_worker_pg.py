import psycopg2
from psycopg2.extras import DictCursor, DictRow


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

        data_keys = None
        val_sim = ''
        keys_item = ''
        match data:
            case list() as df if df and type(df[0]) is list:
                if is_update or not pid:
                    return f'write_db_postgresql: {table_name} --> error data type list([list()]); {is_update=}; {pid=}'
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

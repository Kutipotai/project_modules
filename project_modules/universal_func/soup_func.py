
from bs4 import BeautifulSoup


def get_soup_contents(*, contents, parser='lxml'):
    err, msg, res = False, 'Ok', None
    try:
        res = BeautifulSoup(contents, parser)  # 'lxml' / 'html.parser'
    except Exception as e:
        print('get_soup_contents:', e)
        err, msg, res = True, 'get_soup_contents: Нет данных или они повреждены!', None
    return err, msg, res


if __name__ == '__main__':
    pass







































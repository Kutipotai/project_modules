
from bs4 import BeautifulSoup


def get_soup_contents(*, contents, parser='lxml'):
    err, res = None, None
    try:
        res = BeautifulSoup(contents, parser)  # 'lxml' / 'html.parser'
    except Exception as e:
        print('get_soup_contents:', e)
        err, res = 'get_soup_contents: Нет данных или они повреждены!', None
    return err, res


if __name__ == '__main__':
    pass







































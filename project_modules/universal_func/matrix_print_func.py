
from tabulate import tabulate


def print_matrix(matrix, range_matrix=50):
    res = list()
    try:
        headers = [''] + list(range(range_matrix))
        res = tabulate(transform_float(matrix), headers=headers)
    except Exception as e:
        print('print_matrix:', e)
        pass
    return res


def transform_float(arry):
    res = list()
    num = 0
    for ar in arry:
        part = [num]
        for i in ar:
            try:
                part.append(f'{i:.3f}')
                # if i == 0:
                #     part.append(f'0')
                # elif abs(i) > 1:
                #     part.append(f'{i}')
                # else:
                #     part.append(f'{1 / (i + 0.027):.2f}')
            except:
                part.append(f'{i}')
        res.append(part)
        num += 1
    return res


if __name__ == '__main__':
    pass

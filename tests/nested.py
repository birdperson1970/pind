


def func_A():
    x = 5
    b = func_B(x)
    return b


def func_B(x):
    print(x)
    return x + 1

func_A()
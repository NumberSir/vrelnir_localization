import execjs
from src.consts import *


if __name__ == '__main__':
    # with open(DIR_GAME_ROOT_COMMON / "Degrees of Lewdity VERSION.html", "r", encoding='utf-8') as fp:
    #     content = fp.read()
    # with open("degrees-of-lewdity-20230828-200601.save", "r", encoding="utf-8") as fp:
    #     save = fp.read()
    # ctx = execjs.compile(content)
    # ctx.call(f'window.DeserializeGame("{save}")')
    execjs.get().name

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

btnStartParsing = KeyboardButton('Начать сбор данных.')
profileKeyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(btnStartParsing)


def showBtns():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)

    btn_100 = KeyboardButton(text="По 100 постам")
    btn_500 = KeyboardButton(text="По 500 постам")
    btn_all = KeyboardButton(text="Вся группа")

    keyboard.add(btn_100, btn_500)
    keyboard.insert(btn_all)
    return keyboard

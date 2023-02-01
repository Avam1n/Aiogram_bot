import os
import config
import logging
import markups
import send_emile
from time import sleep
import aiogram.utils.markdown as md
from aiogram.utils import executor
from aiogram.types import ParseMode
from aiogram.dispatcher import FSMContext
from config import bot_token as API_TOKEN
from aiogram import Bot, Dispatcher, types
from asyncio.exceptions import TimeoutError
from aiogram.dispatcher.filters import Text
from check_active import main as group_check
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

logging.basicConfig(level=logging.INFO,
                    filename="mylog.log",
                    filemode="w",
                    format="%(asctime)-15s - %(pathname)s - %(funcName)-8s: Line: %(lineno)d.(%(message)s)",
                    datefmt='%d-%b-%y %H:%M:%S')
bot = Bot(API_TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


def TimeoutErrorHandler(func):
    def wrap(*args, **kwargs):
        while True:
            try:
                func(*args, **kwargs)
            except TimeoutError:
                print(f'TimeoutError excepted, wait 1 second')
                sleep(1)

    return wrap


class Form(StatesGroup):
    group_id = State()
    number_of_posts = State()


def id_verification(some_id: int) -> bool:
    """
    Проверяем на ликвидность ID юзера, у которого будет доступ к функциям бота.
    """
    if not some_id in config.list_id:
        print(f'Пользователь с ID: {some_id} попытался воспользоваться ботом.')
        return False
    else:
        print(f'Пользователь с ID: {some_id} юзает бота.')
        return True


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    if message.chat.type == 'private':
        if id_verification(message.from_user.id):
            await bot.send_message(message.chat.id, md.text("Привет! Давай начнем."),
                                   reply_markup=markups.profileKeyboard,
                                   parse_mode=ParseMode.MARKDOWN)
        else:
            await bot.send_message(message.chat.id, f"Прошу прощения, {message.from_user.username}, "
                                                    f"но у Вас нет прав пользоваться моими функциями.\n"
                                                    f"По всем вопросам можете написать сюда: <a>@avix1n</a>"
                                                    f"Ваш ID: {message.from_user.id}",
                                   parse_mode='HTML')


@dp.message_handler()
async def communication(message: types.Message):
    if message.chat.type == 'private':
        if id_verification(message.from_user.id):
            if message.text.upper() == 'НАЧАТЬ СБОР ДАННЫХ.':
                await Form.group_id.set()

                await message.reply(f"Введи ID группы.\n"
                                    f"(пример: \"cybersportby\" или \"78017410\")\n"
                                    f"Для отмены напиши \"стоп\"")




        else:
            await bot.send_message(message.chat.id, f"Прошу прощения, {message.from_user.username}, "
                                                    f"но у Вас нет прав пользоваться моими функциями.\n"
                                                    f"По всем вопросам можете написать сюда: <a>@avam1n</a>",
                                   parse_mode='HTML')


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='стоп', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)

    await state.finish()
    await message.reply('Остановил. Для того, чтобы начать сначала нажми кнопку ниже.',
                        reply_markup=markups.profileKeyboard)


@dp.message_handler(state=Form.group_id)
async def process_group_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['group_id'] = message.text

    await Form.next()
    await message.reply("Сколько постов просмотреть?", reply_markup=markups.showBtns())


@dp.message_handler(lambda message: message.text not in ["По 100 постам", "По 500 постам", "Вся группа"],
                    state=Form.number_of_posts)
async def process_number_of_posts_invalid(message: types.Message):
    return await message.reply("Похоже что Вы ввели сообщение вместо того, чтобы нажать на кнопку.")


async def send_doc(file_name, chat_id):
    with open(f'{file_name}.html', 'rb') as file:
        await bot.send_document(chat_id, file)
    os.remove(f'{file_name}.html')


@TimeoutErrorHandler
@dp.message_handler(state=Form.number_of_posts)
async def result(message: types.Message, state: FSMContext):
    try:
        async with state.proxy() as data:
            data['number_of_posts'] = message.text

            if data['number_of_posts'] == "По 100 постам":
                data['number_of_posts'] = 100
                await message.reply(f"Ищу по {data['number_of_posts']} постам в группе: "
                                    f"{data['group_id']}")
                await bot.send_message(message.chat.id, "Примерное время ожидания 3 минуты!")
                logging.info(f"Группа --> {data['group_id']} по количеству постов --> {data['number_of_posts']}")
                group_check(data['group_id'], 100)

                await send_doc(file_name=data['group_id'], chat_id=message.chat.id)


            elif data['number_of_posts'] == "По 500 постам":
                data['number_of_posts'] = 500
                await message.reply(f"Ищу по {data['number_of_posts']} постам в группе: "
                                    f"{data['group_id']}")
                await bot.send_message(message.chat.id, "Примерное время ожидания 6 минут!")
                logging.info(f"Группа --> {data['group_id']} по количеству постов --> {data['number_of_posts']}")
                group_check(data['group_id'], 500)

                await send_doc(file_name=data['group_id'], chat_id=message.chat.id)

            elif data['number_of_posts'] == "Вся группа":
                data['number_of_posts'] = 0
                await message.reply(f"Ищу по всем постам в группе: "
                                    f"{data['group_id']}")
                await bot.send_message(message.chat.id, md.text("Если постов много, то ждать тоже много. :-)\n"
                                                                "Если есть возможность напиши отпиши по времени "
                                                                "сюда: ", md.bold('@avix1n')),
                                       parse_mode=ParseMode.MARKDOWN)
                logging.info(f"Группа --> {data['group_id']} по всем постам.")
                group_check(data['group_id'], 0)

                await send_doc(file_name=data['group_id'], chat_id=message.chat.id)

        await state.finish()
        await bot.send_message(message.chat.id, "Для продолжения ты знаешь что делать.",
                               reply_markup=markups.profileKeyboard)
    except Exception as err:
        await state.finish()
        await bot.send_message(message.chat.id, "Что-то пошло не так, проверь правильность ввода данных!",
                               reply_markup=markups.profileKeyboard)
        logging.error(f'{err}')
        send_emile.main(f'Ошибка в "result"\n{err}')


if __name__ == "__main__":
    try:
        print("Бот запущен!")
        logging.info(f'Bot - запущен!')
        executor.start_polling(dp, skip_updates=False)
    except Exception as err:
        print(err)
        logging.error(f'{err}')
        send_emile.main('Ошибка в {{{{executor.start_polling}}}}')
        executor.start_polling(dp, skip_updates=True)

"""
Модуль бота
"""

import asyncio
import os
import uuid
from datetime import datetime

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from dotenv import load_dotenv

from database import Database
from image_processor import ImageProcessor
from logger import logger
from pinterest_worker import PinterestWorker

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DB = os.getenv("DB")

os.makedirs("downloads", exist_ok=True)

db = Database(DB)
processor = ImageProcessor()
pinterest = PinterestWorker()


dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    Обработчик команды /start

    :param message: Сообщение от бота
    :return:
    """
    db.add_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )

    await message.answer(
        f"Привет, {html.bold(message.from_user.full_name)}!\n\n"
        "Жду фото с артикулами с WB или link с Pinterest\n\n"
        "или /help"
    )


@dp.message(Command("help"))
async def help_handler(message: Message) -> None:
    """
    Обработчик команды /help

    :param message: Сообщение от бота
    :return:
    """
    await message.answer(
        "Помощь по боту:\n\n"
        "Отправь мне изображение c артикулами WB как фото или link с Pinterest\n\n"
        "Команды:\n"
        "/start - Начать работу, регистрация в боте\n"
        "/help - Эта справка\n\n"
        "После загрузки изображение обрабатывается 5-10 секунд\n"
    )


@dp.message(F.photo)
async def handle_photo(message: Message, bot: Bot) -> None:
    """
    Обработка изображений отправленных как фото

    :param message: Сообщение от бота
    :param bot: Экземпляр бота
    :return:
    """
    try:
        processing_msg = await message.answer("Загружаем изображения")
        photo = message.photo[-1]
        file_id = photo.file_id
        file_info = await bot.get_file(file_id)
        file_path = file_info.file_path

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        filename = f"photo_{timestamp}_{unique_id}.jpg"
        download_path = f"downloads/{filename}"

        await bot.download_file(file_path, download_path)
        await processing_msg.edit_text("Достаем артикулы\n\n")
        asyncio.create_task(processor.run(download_path, processing_msg))
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Ошибка загрузки фото: %s", e)
        await message.answer("Произошла ошибка при загрузке изображения")


@dp.message()
async def handle_other_messages(message: Message) -> None:
    """
    Обработчик остальных сообщений

    :param message: Сообщение от бота
    :return:
    """
    if "https://pin.it/" in message.text:
        processing_msg = await message.answer("Смотрю этот пин")
        url = message.text.split(" ")[-1]
        asyncio.create_task(pinterest.run(url, processing_msg))
    else:
        await message.answer(
            "Жду фотку с артикулами с WB, или link на Pinterest другого не умею сори...\n\n"
            "Либо /help"
        )


async def main() -> None:
    """
    Точка входа в приложение

    :return:
    """
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logger.info("Bot is running...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("Bot caused stop")

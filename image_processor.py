"""
Модуль для обработки изображения
"""

import os
import re
from typing import List

# Для видеокарты, иначе бот крашится
# import easyocr

from PIL import Image
from aiogram.client.session import aiohttp
from pytesseract import pytesseract

from logger import logger

WB_URL_TEMPLATE = "https://www.wildberries.ru/catalog/{art}/detail.aspx"
WB_URL_CHECKER = "https://rec-ins.wildberries.ru/api/v1/recommendations?nm={art}"
MARKET_URL_TEMPLATE = (
    "https://market.yandex.ru/search?text={art}"
    "&cvredirect=1&businessId=191278432&searchContext=sins_ctx"
)


class ImageProcessor:
    """
    Класс для обработки изображения
    """

    @staticmethod
    def get_text(img_path: str) -> List[str]:
        """
        Получение текста с изображения

        :param img_path: Путь до изображения
        :return: Список извлеченных слов
        """
        result = []
        try:
            result = pytesseract.image_to_string(
                Image.open(img_path), lang="rus+eng"
            ).split()
            # reader = easyocr.Reader(["ch_sim", "en"])
            # result = reader.readtext(img_path, detail=0)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(e)
        return result

    @staticmethod
    def research_text(text: List[str]) -> List[str]:
        """
        Отбор артикулов

        :param text: Список извлеченных слов
        :return: отфильтрованный список
        """
        result = []
        pattern = "[0-9]{8,}"
        for word in text:
            search = re.search(pattern, word)
            if search is not None:
                result.append(search.group(0))
        return result

    @staticmethod
    async def create_urls(list_of_arts: List[str]) -> List[str]:
        """
        Создание и проверка ссылки

        :param list_of_arts: Список артикулов
        :return: Список ссылок
        """
        result = []
        for art in list_of_arts:
            url_wb = WB_URL_CHECKER.format(art=art)
            async with aiohttp.ClientSession() as session:
                async with session.get(url_wb) as response:
                    if response.status == 200:
                        response = await response.json()
                        if len(response.get("nms", [])):
                            result.append(WB_URL_TEMPLATE.format(art=art))
            url_market = MARKET_URL_TEMPLATE.format(art=art)
            async with aiohttp.ClientSession() as session:
                async with session.get(url_market) as response:
                    if response.status == 200:
                        text = await response.text()
                        if "Здесь такого нет" not in text:
                            result.append(url_market)
        return result

    async def run(self, path: str, message) -> List[str]:
        """
        Запуск обработки изображения

        :param path: Путь до изображения
        :param message: Сообщение от бота
        :return: Список ссылок
        """
        text = self.get_text(path)
        clean_text = self.research_text(text)
        await message.edit_text(f"Найдено {len(clean_text)} артикулов")
        urls = await self.create_urls(clean_text)
        logger.info(urls)
        if urls:
            await message.edit_text(f"Найдено {len(urls)} карточек товаров")
            for url in urls:
                await message.answer(url)
        else:
            await message.edit_text("Не найдено страниц по артикулам с фото")
        os.remove(path)
        return urls

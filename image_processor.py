"""
Модуль для обработки изображения
"""

import os
import re
from typing import List

# Для видеокарты, иначе бот крашится
# import easyocr

from PIL import Image
from pytesseract import pytesseract

from logger import logger

WB_URL_TEMPLATE = "https://www.wildberries.ru/catalog/{art}/detail.aspx"
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
    async def create_urls(list_of_arts: List[str], platform: str = "WB") -> List[str]:
        """
        Создание и проверка ссылки

        :param list_of_arts: Список артикулов
        :param platform: Тип площадки
        :return: Список ссылок
        """
        result = []
        for art in list_of_arts:
            if platform == "WB":
                result.append(WB_URL_TEMPLATE.format(art=art))
            elif platform == "YM":
                result.append(MARKET_URL_TEMPLATE.format(art=art))
        return result

    async def run(self, path: str, message, platform: str) -> List[str]:
        """
        Запуск обработки изображения

        :param path: Путь до изображения
        :param message: Сообщение от бота
        :param platform: Тип площадки
        :return: Список ссылок
        """
        text = self.get_text(path)
        clean_text = self.research_text(text)
        await message.edit_text(f"Найдено {len(clean_text)} артикулов")
        urls = await self.create_urls(clean_text, platform)
        logger.info(urls)
        if urls:
            await message.edit_text(f"Найдено {len(urls)} карточек товаров")
            for url in urls:
                await message.answer(url)
        else:
            await message.edit_text("Не найдено страниц по артикулам с фото")
        os.remove(path)
        return urls

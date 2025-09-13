"""
Модуль для обработки изображения
"""

import os
import re
from typing import List

import easyocr

from logger import logger

WB_URL_TEMPLATE = "https://www.wildberries.ru/catalog/{art}/detail.aspx"


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
            reader = easyocr.Reader(["ch_sim", "en"])
            result = reader.readtext(img_path, detail=0)
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
    def create_urls(list_of_arts: List[str]) -> List[str]:
        """
        Создание и проверка ссылки

        :param list_of_arts: Список артикулов
        :return: Список ссылок
        """
        result = []
        for art in list_of_arts:
            url = WB_URL_TEMPLATE.format(art=art)
            result.append(url)
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
        urls = self.create_urls(clean_text)
        logger.info(urls)
        if urls:
            await message.edit_text(f"Найдено {len(urls)} артикулов")
            for url in urls:
                await message.answer(url)
        else:
            await message.edit_text("Не найдено артикулов на фото")
        os.remove(path)
        return urls

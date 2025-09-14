"""
Модуль для взаимодействия с Pinterest
"""

import os
import uuid
from datetime import datetime

import aiofiles
import aiohttp
from aiogram.types import Message
from bs4 import BeautifulSoup

from image_processor import ImageProcessor
from logger import logger


class PinterestWorker:
    """
    Класс для взаимодействия с Pinterest
    """

    def __init__(
        self,
        download_dir: str = "downloads",
        processor: ImageProcessor = ImageProcessor(),
    ) -> None:
        """
        Инициализация класса

        :param download_dir: Директория для временного сохранения изображений
        :param processor:
        """
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.processor = processor

    async def download_from_url(self, image_url: str) -> str:
        """
        Скачивание изображения по URL

        :param image_url: Ссылка на изображение
        :return: Путь на скаченное изображение
        """
        download_path = ""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            if "." in image_url.split("/")[-1]:
                ext = image_url.split(".")[-1].split("?")[0]
                if ext not in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
                    ext = "jpg"
            else:
                ext = "jpg"
            filename = f"url_image_{timestamp}_{unique_id}.{ext}"
            download_path = os.path.join(self.download_dir, filename)

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        # pylint: disable-next=broad-exception-raised
                        raise Exception(f"HTTP ошибка: {response.status}")
                    content_type = response.headers.get("content-type", "")
                    if not content_type.startswith("image/"):
                        # pylint: disable-next=broad-exception-raised
                        raise Exception("URL не ведет на изображение")
                    async with aiofiles.open(download_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(1024):
                            await f.write(chunk)

            return download_path
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(e)
            return download_path

    @staticmethod
    async def parse_to_find_photo(url: str) -> str:
        """

        :param url: Ссылка на изображение от пользователя
        :return: ссылка для скачивания изображения
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                hcl_divs = soup.find("img", class_=lambda x: x and "hCL" in x.split())
                return hcl_divs.get("src")

    async def run(self, url, message: Message) -> None:
        """
        Запуск обработки ссылки с пинтерест

        :param url: Ссылка
        :param message: сообщение от пользователя
        :return:
        """
        link_photo = await self.parse_to_find_photo(url)
        if link_photo:
            await message.edit_text("Изображение найдено")
            path = await self.download_from_url(link_photo)
            if path:
                await message.edit_text("Достаем артикулы")
                await self.processor.run(path, message)
        else:
            await message.edit_text("Изображение не найдено")

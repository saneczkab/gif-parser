import os
import logging
import zlib
import struct
from datetime import datetime

class GifFramesExporter:
    def __init__(self, gif_parser):
        self.gif_parser = gif_parser
        self.output_dir = self.create_output_directory()

    @staticmethod
    def create_output_directory():
        """
        Создание папки, куда будут экспортированы кадры.
        :return: Путь к папке.
        """
        now = datetime.now()
        folder_name = now.strftime("%d-%m-%Y %H-%M-%S")
        path = os.path.join("Frames", folder_name)
        os.makedirs(path)
        return path

    def export_all_frames(self):
        """
        Экспорт всех кадров в PNG-файлы.
        """
        for idx, frame in enumerate(self.gif_parser.frames, start=1):
            self.export_frame(frame, idx)
        logging.info(f"Кадры экспортированы в {self.output_dir}")

    def export_selected_frames(self, frame_numbers):
        """
        Экспорт выбранных кадров в PNG-файлы.
        :param frame_numbers: Список номеров кадров.
        """
        for frame_number in frame_numbers:
            if 1 <= frame_number <= len(self.gif_parser.frames):
                frame = self.gif_parser.frames[frame_number - 1]
                self.export_frame(frame, frame_number)
            else:
                logging.warning(f"Кадр {frame_number} не существует и будет пропущен.")
        logging.info(f"Кадры экспортированы в {self.output_dir}")

    def export_frame(self, frame, frame_number):
        """
        Экспорт кадра в PNG-файл.
        :param frame: Кадр анимации.
        :param frame_number: Номер кадра.
        """
        width = frame.image_descriptor.width
        height = frame.image_descriptor.height
        indices = frame.image_data
        color_table = frame.local_color_table if frame.local_color_table else self.gif_parser.global_color_table
        transparency = None
        if frame.graphic_control_extension and frame.graphic_control_extension.transparency_flag:
            transparency_index = frame.graphic_control_extension.transparent_color_index
            transparency = color_table.colors[transparency_index]

        pixels = self.transform_pixels(frame, width, height, indices, color_table, transparency)
        png_data = self.get_png_data(pixels, width, height)

        filename = os.path.join(self.output_dir, f"{frame_number}.png")
        with open(filename, 'wb') as png_file:
            png_file.write(png_data)

    @staticmethod
    def transform_pixels(frame, width, height, indices, color_table, transparency):
        """
        Преобразование индексов цветов в RGBA пиксели.
        :param frame: Кадр анимации.
        :param width: Ширина изображения.
        :param height: Высота изображения.
        :param indices: Индексы цветов.
        :param color_table: Таблица цветов.
        :param transparency: Индекс прозрачности.
        :return: Пиксели в формате RGBA.
        """
        pixels = []
        for i in range(height):
            row = []
            for j in range(width):
                idx = i * width + j
                color_idx = indices[idx]
                r, g, b = color_table.colors[color_idx]
                a = 255
                if transparency and color_idx == frame.graphic_control_extension.transparent_color_index:
                    a = 0
                row.extend([r, g, b, a])
            pixels.append(b'\x00' + bytes(row))

        return pixels

    def get_png_data(self, pixels, width, height):
        """
        Инициализация структуры PNG-файла.
        :param pixels: Пиксели в формате RGBA.
        :param width: Ширина изображения.
        :param height: Высота изображения.
        :return: Структура PNG-файла в байтах.
        """
        image_data = b''.join(pixels)
        compressed_data = zlib.compress(image_data)

        png_data = b'\x89PNG\r\n\x1a\n'
        png_data += self.get_png_chunk(b'IHDR', self.get_idhr_chunk(width, height))
        png_data += self.get_png_chunk(b'IDAT', compressed_data)
        png_data += self.get_png_chunk(b'IEND', b'')

        return png_data

    @staticmethod
    def get_png_chunk(chunk_type, data):
        """
        Создание PNG-чанка.
        :param chunk_type: Тип чанка в байтах.
        :param data: Данные для записи в чанк.
        :return: Чанк в байтах.
        """
        chunk = struct.pack(">I", len(data))
        chunk += chunk_type
        chunk += data
        crc = zlib.crc32(chunk_type + data) & 0xffffffff
        chunk += struct.pack(">I", crc)
        return chunk

    @staticmethod
    def get_idhr_chunk(width, height, depth=8, color_type=6, compression=0, filter_method=0, interlace=0):
        """
        Создание IHDR-чанка.
        :param depth: Глубина цвета.
        :param color_type: Тип цветности.
        :param compression: Метод сжатия.
        :param filter_method: Метод фильтрации.
        :param interlace: Интерлейс.
        :param width: Ширина изображения.
        :param height: Высота изображения.
        :return: IHDR-чанк в байтах.
        """
        return struct.pack(">IIBBBBB", width, height, depth, color_type, compression, filter_method, interlace)

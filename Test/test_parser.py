import argparse
import unittest
from unittest.mock import patch, MagicMock
import sys
import io

from GifParser.parser import GifParser
from GifStructs.GifExtensions.application_extension import GifApplicationExtension
from GifStructs.GifExtensions.comment_extension import GifCommentExtension
from GifStructs.GifExtensions.graphic_control_extension import GifGraphicControlExtension
from GifStructs.GifExtensions.plain_text_extension import GifPlainTextExtension
from GifStructs.gif_frame import GifFrame
from GifStructs.gif_header import GifHeader
from GifStructs.global_color_table import GifGlobalColorTable
from GifStructs.image_descriptor import GifImageDescriptor
from GifStructs.local_color_table import GifLocalColorTable
from GifStructs.logical_screen_descriptor import GifLogicalScreenDescriptor
from gif_parser import main


class TestGifParser(unittest.TestCase):
    def test_parse_header(self):
        expected = GifHeader("GIF", "89a")
        header = GifParser.parse_header(b"\x47\x49\x46\x38\x39\x61")
        self.assertEqual(expected, header)

    def test_parse_logical_screen_descriptor(self):
        expected = GifLogicalScreenDescriptor(300, 300, 0b10000000, 1, 0)
        logical_screen_descriptor = GifParser.parse_logical_screen_descriptor(b"\x2C\x01\x2C\x01\x80\x01\x00")
        self.assertEqual(expected, logical_screen_descriptor)

    def test_parse_global_color_table(self):
        expected = GifGlobalColorTable([(76, 0, 0), (255, 255, 255)])
        global_color_table = GifParser.parse_global_color_table(
            GifLogicalScreenDescriptor(300, 300, 0b10000000, 1, 0),
            b"\x4C\x00\x00\xFF\xFF\xFF")
        self.assertEqual(expected, global_color_table)

    def test_parse_graphic_control_extension(self):
        expected = GifGraphicControlExtension(0, 0, 1, 4, 0)
        gce = GifParser.parse_graphic_control_extension(b"\x01\x04\x00\x00")
        self.assertEqual(expected, gce)

    def test_parse_application_extension(self):
        expected = GifApplicationExtension("NETSCAPE", "2.0\x03", b"\x01\x00\x00")
        app_ext = GifParser.parse_application_extension(
            b"\x4E\x45\x54\x53\x43\x41\x50\x45\x32\x2E\x30\x03", b"\x01\x00\x00")
        self.assertEqual(expected, app_ext)

    def text_parse_comment_extension(self):
        expected = GifCommentExtension(b"comment")
        comment_ext = GifParser.parse_comment_extension(b"\x74\x65\x73\x74\x20\x63\x6F\x6D\x6D\x65\x6E\x74")
        self.assertEqual(expected, comment_ext)

    def test_parse_plain_text_extension(self):
        expected = GifPlainTextExtension(
            0, 0, 300, 300, 10, 10, 42, 24, "test")
        plain_text_ext = GifParser.parse_plain_text_extension(
            b"\x00\x00\x00\x00\x2c\x01\x2c\x01\x0a\x0a\x2a\x18", b"\x74\x65\x73\x74")
        self.assertEqual(expected, plain_text_ext)

    @patch('argparse.ArgumentParser.parse_args')
    @patch('logging.info')
    def test_parse_small_gif(self, mock_logging_info, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            input='Images/small.gif',
            descriptor=False,
            headers=True,
            animate=False
        )

        main()
        all_output = mock_logging_info.call_args[0]
        self.assertEqual(1, len(all_output))
        output = all_output[0]

        self.assertEqual(1, output.count("Заголовок: GIF89a"))
        self.assertEqual(3, output.count("Ширина: 1 px\n  Высота: 1 px"))
        self.assertEqual(2, output.count("Кадр"))
        self.assertTrue("Кадр 1:" in output and "Кадр 2:" in output)
        self.assertEqual(2, output.count("Метод обработки: 0 (Без применения обработки)"))
        self.assertEqual(2, output.count("Время задержки в анимации: 40 мс"))
        self.assertEqual(2, output.count("Нет локальной таблицы цветов"))
        self.assertEqual(2, output.count("Есть расширение управления графикой"))
        self.assertEqual(2, output.count("Нет расширения простого текста"))
        self.assertEqual(2, output.count("Нет расширения приложения"))
        self.assertEqual(2, output.count("Нет расширения комментария"))

    @patch('argparse.ArgumentParser.parse_args')
    @patch('logging.info')
    def test_static_gif(self, mock_logging_info, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            input='Images/image.gif',
            descriptor=False,
            headers=True,
            animate=False
        )

        main()
        all_output = mock_logging_info.call_args[0]
        self.assertEqual(1, len(all_output))
        output = all_output[0]

        self.assertEqual(2, output.count("Ширина: 300 px\n  Высота: 300 px"))
        self.assertEqual(1, output.count("Кадр"))
        self.assertTrue("Кадр 1:" in output)
        self.assertEqual(1, output.count("Комментарий: test comment"))
        self.assertEqual(1, output.count("Нет локальной таблицы цветов"))
        self.assertEqual(1, output.count("Нет расширения управления графикой"))
        self.assertEqual(1, output.count("Нет расширения простого текста"))
        self.assertEqual(1, output.count("Нет расширения приложения"))
        self.assertEqual(1, output.count("Есть расширение комментария"))

    @patch('argparse.ArgumentParser.parse_args')
    @patch('logging.info')
    def test_big_gif_descriptor(self, mock_logging_info, mock_parse_args):
        mock_parse_args.return_value = argparse.Namespace(
            input='Images/big_image.gif',
            descriptor=True,
            headers=False,
            animate=False
        )

        main()
        all_output = mock_logging_info.call_args[0]
        self.assertEqual(1, len(all_output))
        output = all_output[0]
        expected = ("Заголовок: GIF87a\n"
                    "Логический дескриптор экрана:\n"
                    "  Ширина: 4000 px\n"
                    "  Высота: 2662 px\n"
                    "  Флаг использования глобальной таблицы цветов: 1\n"
                    "  Флаг Color resolution: 7\n"
                    "  Флаг сортировки: 0\n"
                    "  Размер общей таблицы цветов: 256\n"
                    "  Индекс цвета фона: 243\n"
                    "  Соотношение сторон: 0\n"
                    "Глобальная таблица цветов:\n"
                    "  Число цветов: 256\n")
        self.assertEqual(expected, output)


if __name__ == '__main__':
    unittest.main()

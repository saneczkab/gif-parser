import os
import unittest
from unittest.mock import patch

from GifParser.gif_frames_exporter import GifFramesExporter
from GifParser.gif_parser import GifParser


class TestFramesExporter(unittest.TestCase):
    def tearDown(self):
        if os.path.isdir("Frames"):
            for root, dirs, files in os.walk("Frames", topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir("Frames")

    def test_transform_pixels(self):
        gif_parser = GifParser("Images/small.gif")
        gif_parser.parse()
        exporter = GifFramesExporter(gif_parser)

        frame = gif_parser.frames[0]
        width = frame.image_descriptor.width
        height = frame.image_descriptor.height
        indices = frame.image_data
        color_table = gif_parser.global_color_table
        transparency = None

        pixels = exporter.transform_pixels(frame, width, height, indices, color_table, transparency)
        self.assertEqual([b'\x00\xb8\x00\x00\xff'], pixels)

    def test_get_png_data(self):
        gif_parser = GifParser("Images/small.gif")
        gif_parser.parse()
        exporter = GifFramesExporter(gif_parser)

        pixels = [b'\x00\xb8\x00\x00\xff']
        width = 1
        height = 1

        png_data = exporter.get_png_data(pixels, width, height)
        self.assertEqual(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xd8\xc1\xc0\xf0'
            b'\x1f\x00\x03\xe4\x01\xb8m>\x16\xcc\x00\x00\x00\x00IEND\xaeB`\x82',
            png_data)

    def test_export_frame(self):
        gif_parser = GifParser("Images/small.gif")
        gif_parser.parse()
        exporter = GifFramesExporter(gif_parser)
        exporter.export_frame(gif_parser.frames[0], 1)
        self.assertTrue(os.path.isfile(f"{exporter.output_dir}\\1.png"))

    @patch.object(GifFramesExporter, "export_frame")
    def test_export_all_frames(self, mock_export_frame):
        gif_parser = GifParser("Images/small.gif")
        gif_parser.parse()
        exporter = GifFramesExporter(gif_parser)
        exporter.export_all_frames()
        self.assertEqual(2, mock_export_frame.call_count)

    @patch.object(GifFramesExporter, "export_frame")
    @patch('logging.warning')
    def test_export_selected_frames(self, mock_logging_warning, mock_export_frame):
        gif_parser = GifParser("Images/small.gif")
        gif_parser.parse()
        exporter = GifFramesExporter(gif_parser)

        exporter.export_selected_frames([1, 2, 3])
        self.assertEqual(2, mock_export_frame.call_count)
        self.assertEqual(1, mock_logging_warning.call_count)

if __name__ == '__main__':
    unittest.main()

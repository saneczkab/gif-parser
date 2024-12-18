from GifParser.parser import GifParser

import tkinter as tk


class GifViewer:
    def __init__(self, root, gif_parser: GifParser):
        self.root = root
        self.gif_parser = gif_parser
        self.label = tk.Label(root)
        self.label.pack()
        self.current_frame = 0

        self.width = gif_parser.logical_screen_descriptor.width
        self.height = gif_parser.logical_screen_descriptor.height
        self.tile_size = 10

        self.checkerboard = self.create_checkerboard(self.width, self.height, self.tile_size)

        self.photo = tk.PhotoImage(width=self.width, height=self.height)
        self.label.config(image=self.photo)

        rows_str = ["{" + " ".join(row) + "}" for row in self.checkerboard]
        self.photo.put("\n".join(rows_str))

        self.base_image = [row.copy() for row in self.checkerboard]
        self.previous_images_stack = []

        self.animate()

    @staticmethod
    def create_checkerboard(width, height, tile_size=10):
        color1 = "#C8C8C8"
        color2 = "#646464"
        checkerboard = []
        for y in range(height):
            row = []
            for x in range(width):
                if ((x // tile_size) + (y // tile_size)) % 2 == 0:
                    row.append(color1)
                else:
                    row.append(color2)
            checkerboard.append(row)
        return checkerboard

    def animate(self):
        if not self.gif_parser.frames:
            return

        frame = self.gif_parser.frames[self.current_frame]
        delay = (
            frame.graphic_control_extension.delay_time / 100.0
            if frame.graphic_control_extension else 0.1
        )
        disposal = (
            frame.graphic_control_extension.disposal_method
            if frame.graphic_control_extension else 0
        )

        if self.current_frame > 0:
            prev_frame = self.gif_parser.frames[self.current_frame - 1]
            prev_disposal = (
                prev_frame.graphic_control_extension.disposal_method
                if prev_frame.graphic_control_extension else 0
            )
            if prev_disposal == 2:
                self.clear_region(prev_frame.image_descriptor)
            elif prev_disposal == 3:
                if self.previous_images_stack:
                    self.base_image = self.previous_images_stack.pop()
                    self.update_photo()

        if disposal == 3:
            self.previous_images_stack.append([row.copy() for row in self.base_image])

        self.apply_frame(frame)

        self.update_photo()

        self.current_frame = (self.current_frame + 1) % len(self.gif_parser.frames)
        self.root.after(int(delay * 10), self.animate)

    def clear_region(self, image_descriptor):
        left = image_descriptor.left
        top = image_descriptor.top
        width = image_descriptor.width
        height = image_descriptor.height

        for y in range(top, top + height):
            if y >= self.height:
                continue
            for x in range(left, left + width):
                if x >= self.width:
                    continue
                tile_x = x // self.tile_size
                tile_y = y // self.tile_size
                color = "#C8C8C8" if (tile_x + tile_y) % 2 == 0 else "#646464"
                self.base_image[y][x] = color

    def apply_frame(self, frame):
        left = frame.image_descriptor.left
        top = frame.image_descriptor.top
        width = frame.image_descriptor.width
        height = frame.image_descriptor.height
        color_table = (
            frame.local_color_table.colors
            if frame.local_color_table else
            self.gif_parser.global_color_table.colors
        )
        transparent_index = (
            frame.graphic_control_extension.transparent_color_index
            if frame.graphic_control_extension and frame.graphic_control_extension.transparency_flag else
            None
        )

        for y in range(height):
            if (top + y) >= self.height:
                continue
            for x in range(width):
                if (left + x) >= self.width:
                    continue
                idx = y * width + x
                if idx >= len(frame.image_data):
                    continue
                color_idx = frame.image_data[idx]
                if color_idx >= len(color_table):
                    continue
                if transparent_index is not None and color_idx == transparent_index:
                    continue
                rgb = color_table[color_idx]
                color = self.rgb_to_hex(rgb)
                self.base_image[top + y][left + x] = color

    def update_photo(self):
        rows_str = ["{" + " ".join(row) + "}" for row in self.base_image]
        self.photo.put("\n".join(rows_str))

    @staticmethod
    def rgb_to_hex(rgb):
        return f'#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}'

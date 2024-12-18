class LZWDecompressor:
    def __init__(self, min_code_size, data):
        self.min_code_size = min_code_size
        self.data = data

    def decode(self):
        """
        Декодирование данных из LZW.
        :return: Список декодированных числовых данных.
        """
        params = self.initialize_parameters()
        dictionary = {i: [i] for i in range(params['clear_code'])}
        bit_buffer, bits_in_buffer = 0, 0
        data_iter = iter(self.data)
        codes = []
        old_code = None

        while True:
            current_code, bit_buffer, bits_in_buffer = self.read_next_code(
                bit_buffer, bits_in_buffer, params['code_size'], data_iter)

            if current_code is None:
                break

            if current_code == params['clear_code']:
                dictionary = {i: [i] for i in range(params['clear_code'])}
                params = self.reset_parameters()
                old_code = None
                continue
            elif current_code == params['end_code']:
                break

            entry, dictionary, params, old_code = self.process_code(current_code, dictionary, old_code, codes, params)

        return codes

    def initialize_parameters(self):
        """
        Инициализация основных параметров.
        :return: Словарь с инициализированными параметрами.
        """
        clear_code = 1 << self.min_code_size
        end_code = clear_code + 1
        code_size = self.min_code_size + 1
        next_code = end_code + 1
        max_code_size = 12

        return {
            'clear_code': clear_code,
            'end_code': end_code,
            'code_size': code_size,
            'next_code': next_code,
            'max_code_size': max_code_size
        }

    def reset_parameters(self):
        """
        Сброс параметров после достижения метки clear_code.
        :return: Словарь со сброшенными параметрами.
        """
        clear_code = 1 << self.min_code_size
        end_code = (1 << self.min_code_size) + 1
        code_size = self.min_code_size + 1
        next_code = (1 << self.min_code_size) + 2
        max_code_size = 12

        return {
            'clear_code': clear_code,
            'end_code': end_code,
            'code_size': code_size,
            'next_code': next_code,
            'max_code_size': max_code_size
        }

    @staticmethod
    def read_next_code(bit_buffer, bits_in_buffer, code_size, data_iter):
        """
        Чтение следующего кода из блока данных.

        :param bit_buffer: Буфер битов.
        :param bits_in_buffer: Количество битов в буфере.
        :param code_size: Размер кода.
        :param data_iter: Данные (итератор).
        :return: Обновленные данные о коде, буфере и количестве битов.
        """
        while bits_in_buffer < code_size:
            try:
                byte = next(data_iter)
                bit_buffer |= byte << bits_in_buffer
                bits_in_buffer += 8
            except StopIteration:
                break

        if bits_in_buffer < code_size:
            return None, bit_buffer, bits_in_buffer

        current_code = bit_buffer & ((1 << code_size) - 1)
        bit_buffer >>= code_size
        bits_in_buffer -= code_size

        return current_code, bit_buffer, bits_in_buffer

    @staticmethod
    def process_code(current_code, dictionary, old_code, codes, params):
        """
        Обновление словаря и добавление данных к выходу.
        :param current_code: Код.
        :param dictionary: Словарь.
        :param old_code: Предыдущий код.
        :param codes: Список декодированных данных.
        :param params: Параметры декодера.
        :return: Обновленные данные о коде, словаре и параметрах.
        """
        if current_code in dictionary:
            entry = dictionary[current_code][:]
        elif old_code is not None:
            entry = dictionary[old_code] + [dictionary[old_code][0]]
        else:
            entry = None

        codes.extend(entry)

        if old_code is not None:
            dictionary[params['next_code']] = dictionary[old_code] + [entry[0]]
            params['next_code'] += 1

            if params['next_code'] >= (1 << params['code_size']) and params['code_size'] < params['max_code_size']:
                params['code_size'] += 1

        old_code = current_code
        return entry, dictionary, params, old_code

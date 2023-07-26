from collections import OrderedDict
import struct


# Define a Header class to represent the header structure
class Header:
    def __init__(self):
        self.magic = b'RESTBL'
        self.version = 0
        self.string_block_size = 0
        self.crc_table_num = 0
        self.name_table_num = 0


# Define a HashEntry class to represent a hash entry
class HashEntry:
    def __init__(self):
        self.hash = 0
        self.size = 0


# Define a NameEntry class to represent a name entry
class NameEntry:
    def __init__(self):
        self.name = b''
        self.size = 0


# Define the RESTBL class
class RESTBL:
    def __init__(self, data: bytes):
        self.m_crc_table = OrderedDict()
        self.m_name_table = OrderedDict()
        self.m_version = 0
        self.m_string_block_size = 0

        # Read the binary data
        self.from_binary(data)

    def from_binary(self, data: bytes):
        # Read the header data
        header = Header()
        header_data = data[:0x16]
        header_values = struct.unpack('<6sIIII', header_data)
        header.magic = header_values[0]
        header.version = header_values[1]
        header.string_block_size = header_values[2]
        header.crc_table_num = header_values[3]
        header.name_table_num = header_values[4]

        if header.magic != b'RESTBL':
            raise ValueError("Invalid RESTBL magic")

        self.m_version = header.version
        self.m_string_block_size = header.string_block_size

        # Read the CRC table data
        offset = 0x16
        for _ in range(header.crc_table_num):
            entry_data = data[offset:offset + 8]
            entry_values = struct.unpack('<II', entry_data)
            self.m_crc_table[entry_values[0]] = entry_values[1]
            offset += 8

        # Read the Name table data
        for _ in range(header.name_table_num):
            entry_data = data[offset:offset + 0xA4]
            name = entry_data[:160].split(b'\x00', 1)[0]
            entry_values = struct.unpack('<I', entry_data[160:])
            self.m_name_table[name.decode()] = entry_values[0]
            offset += 0xA4

    def to_binary(self) -> bytes:
        header: Header = Header()
        header.version = self.m_version
        header.string_block_size = self.m_string_block_size
        header.crc_table_num = len(self.m_crc_table)
        header.name_table_num = len(self.m_name_table)

        header_data = struct.pack('<6sIIII', header.magic, header.version,
                                  header.string_block_size, header.crc_table_num,
                                  header.name_table_num)

        crc_table_entries: list[bytes] = []
        for hash_value, size in self.m_crc_table.items():
            crc_entry_data = struct.pack('<II', hash_value, size)
            crc_table_entries.append(crc_entry_data)
        crc_table_data = b''.join(crc_table_entries)

        name_table_entries: list[bytes] = []
        for name, size in self.m_name_table.items():
            name_entry_data = struct.pack('<160sI', name.encode(), size)
            name_table_entries.append(name_entry_data)
        name_table_data = b''.join(name_table_entries)

        return header_data + crc_table_data + name_table_data

    @staticmethod
    def from_binary_data(data: bytes) -> 'RESTBL':
        return RESTBL(data)

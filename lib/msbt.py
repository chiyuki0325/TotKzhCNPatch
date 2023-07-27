from io import BytesIO

Groups = {0: "System"}
Tags = {"System": {0: "Ruby", 1: "Font", 2: "Size", 3: "Color", 4: "PageBreak"}}

# Unpack the Groups and Tags for later use.
Groups_Bytes = {}
for group in Groups:
    Groups_Bytes[Groups[group]] = chr(group)
Tag_Bytes = {}
for group_name in Tags:
    for tag_name in Tags[group_name]:
        Tag_Bytes[Tags[group_name][tag_name]] = Groups_Bytes[group_name] + chr(tag_name)


class UnmatchedCodeError(Exception):
    pass


def parse_msbt_string(string, encoding):  # Represent control codes in a readable format.
    string = string.decode(encoding)
    string_len = len(string)
    ind = 0
    parsed_string = ""
    while ind < string_len:
        match string[ind]:
            case '\x0E':  # Escape code.
                ind += 1
                group = ord(string[ind])  # First uint16.
                ind += 1
                tag = ord(string[ind])  # Second uint16.
                ind += 2
                extra = ind + (ord(string[ind - 1]) >> 1)  # Remaining bytes to read after.
                attr_bytes = string[ind:extra]
                if attr_bytes == "":  # If none, no representation is needed.
                    new_tag = f"<unk[{group}:{tag}]>"
                else:
                    attr = ' '.join([str(ord(i)) for i in attr_bytes])
                    new_tag = f"<unk[{group}:{tag}:{attr}]>"
                if group in Groups:
                    group = Groups[group]
                    if group in Tags:
                        if tag in Tags[group]:
                            tag = Tags[group][tag]
                            if attr_bytes == "":
                                new_tag = f"<{tag}>"
                            else:
                                match tag:
                                    case "Ruby":
                                        attr = "{" + ':'.join([str(ord(i)) for i in attr_bytes[:2]]) + "}" + attr_bytes[
                                                                                                             2:]
                                    case "Color":
                                        attr = '#' + ''.join(
                                            [(hex(i))[2:].zfill(2) for i in attr_bytes.encode(encoding)])
                                    case _:
                                        attr = ' '.join([str(ord(i)) for i in attr_bytes])
                                new_tag = f"<{tag}=\"{attr}\">"
                        else:
                            if attr_bytes == "":
                                new_tag = f"<[{group}:{tag}]>"
                            else:
                                new_tag = f"<[{group}:{tag}:{attr}]>"

                ind = extra - 1
                parsed_string += new_tag
            case '\x0F':  # Indicates the end of a particular code's affect, always 6 bytes.
                ind += 1
                group = ord(string[ind])
                ind += 1
                tag = ord(string[ind])
                new_tag = f"</unk[{group}:{tag}]>"
                if group in Groups:
                    group = Groups[group]
                    if group in Tags:
                        if tag in Tags[group]:
                            tag = Tags[group][tag]
                            new_tag = f"</{tag}>"
                        else:
                            new_tag = f"</[{group}:{tag}]>"
                parsed_string += new_tag
            case "\\" | "<":  # Backslash replacments.
                parsed_string += "\\" + string[ind]
            case '\x00':  # End of string.
                parsed_string += "</eos>"
                break
            case '\x0A':
                parsed_string += "</br>"
            case _:
                parsed_string += string[ind]
        ind += 1
    return parsed_string


def compile_msbt_string(parsed_string, encoding):
    string_len = len(parsed_string)
    ind = 0
    compiled_string = ""
    while ind < string_len:
        if parsed_string[ind] == "<":
            if "<" in parsed_string[ind + 1:]:
                next_code_pos = parsed_string.index("<", ind + 1)
            else:
                next_code_pos = string_len
            if ">" in parsed_string[ind:next_code_pos]:
                ind += 1
                cur_code = parsed_string[ind:parsed_string.index(">", ind)]
                ind = parsed_string.index(">", ind)
                code_ind = 0
                compiled_code = ""
                if cur_code[code_ind] == "/":
                    escape_char = '\x0F'
                    code_ind += 1
                else:
                    escape_char = '\x0E'

                if "[" in cur_code:
                    if "]" in cur_code:
                        end_ind = cur_code.index("]")

                        code_ind = cur_code.index("[") + 1
                        info = []
                        info_section = cur_code[code_ind:end_ind].split(":")
                        for i in range(len(info_section)):
                            if i < 2:
                                is_int = True
                                for char in info_section[i]:
                                    if not 47 < ord(char) < 58:
                                        is_int = False
                                        break
                                if is_int == True:
                                    info += [''.join([chr(int(j)) for j in info_section[i].split(" ")])]
                                else:
                                    if i == 1:
                                        info += [Groups_Bytes[info_section[i]]]
                                    else:
                                        info += [Tag_Bytes[info_section[i]][-1]]

                            else:
                                info += [''.join([chr(int(j)) for j in info_section[i].split(" ")])]

                        if len(info) == 3:
                            compiled_code = escape_char + ''.join(info[:2]) + chr(len(info[2]) << 1) + info[2]
                        else:
                            compiled_code = escape_char + ''.join(info)
                            if escape_char == '\x0E':
                                compiled_code += '\x00'
                    else:
                        raise UnmatchedCodeError("The control code has no end marker for the info section. \"]\"")


                elif cur_code == '/eos':
                    compiled_code = "\x00"

                elif cur_code == "/br":
                    compiled_code = "\x0A"


                else:
                    if "=" in cur_code:
                        if cur_code.count('"') != 2:
                            raise UnmatchedCodeError("The attribute info is not quoted properly.")
                        equal_index = cur_code.index("=")
                        attr_info_start = cur_code.index('"', equal_index) + 1
                        attr_info_end = cur_code.index('"', attr_info_start)
                        tag = cur_code[code_ind:equal_index]
                        attr_info = cur_code[attr_info_start:attr_info_end]
                        match tag:
                            case "Ruby":
                                if not ("{" in attr_info and ":" in attr_info and "}" in attr_info):
                                    raise UnmatchedCodeError(
                                        "The Ruby code must contain 2 16-bit integers within braces before the string.")
                                attr_ind = attr_info.index("{") + 1
                                attr_end = attr_info.index(":", attr_ind)
                                attr = chr(int(attr_info[attr_ind:attr_end]))
                                attr_ind = attr_end + 1
                                attr_end = attr_info.index("}", attr_ind)
                                attr += chr(int(attr_info[attr_ind:attr_end]))
                                attr_ind = attr_end + 1
                                attr += attr_info[attr_ind:]
                            case "Color":
                                attr = bytes.fromhex(attr_info[attr_info.index("#") + 1:]).decode(encoding)
                            case _:
                                attr = ''.join(chr(int(i)) for i in attr_info.split(" "))

                        compiled_code = escape_char + Tag_Bytes[tag] + chr(len(attr) << 1) + attr

                    else:
                        compiled_code = escape_char + Tag_Bytes[cur_code[code_ind:]]
                        if escape_char == '\x0E':
                            compiled_code += '\x00'

                compiled_string += compiled_code

            else:
                raise UnmatchedCodeError("The control code has no end marker. \">\"")

        elif parsed_string[ind] == "\\":
            ind += 1
            compiled_string += parsed_string[ind]

        else:
            compiled_string += parsed_string[ind]
        ind += 1
    return compiled_string.encode(encoding)


class reader():
    def __init__(self, byte_order):
        self.byte_order = byte_order

    def ReadUInt16(self, file):
        if self.byte_order == 'le':
            return int(''.join([file.read(1).hex() for i in range(2)][::-1]), 16)
        elif self.byte_order == 'be':
            return int(''.join([file.read(1).hex() for i in range(2)]), 16)

    def ReadUInt32(self, file):
        if self.byte_order == 'le':
            return int(''.join([file.read(1).hex() for i in range(4)][::-1]), 16)
        elif self.byte_order == 'be':
            return int(''.join([file.read(1).hex() for i in range(4)]), 16)

    def ReadLong(self, file):
        if self.byte_order == 'le':
            val = int(''.join([file.read(1).hex() for i in range(4)][::-1]), 16)
        elif self.byte_order == 'be':
            val = int(''.join([file.read(1).hex() for i in range(4)]), 16)
        if (val & 0x8000000000000000) == 0x8000000000000000:
            val = - ((val ^ 0xFFFFFFFFFFFFFFFF) + 1)
        return val


class header():
    def __init__(self, msbt_file):
        self.identifier = msbt_file.read(8).decode()
        if self.identifier != 'MsgStdBn':
            raise InvalidMsbtError("This is not a valid msbt file.")
        self.byte_order_mark = msbt_file.read(2)
        self.byte_order = 'le' if self.byte_order_mark[0] > self.byte_order_mark[1] else 'be'
        self.int_read = reader(self.byte_order)
        self.unknown1 = self.int_read.ReadUInt16(msbt_file)
        self.encoding_byte = msbt_file.read(1)
        self.file_encoding = 'utf-8' if self.encoding_byte == b'\x00' else 'utf-16-' + self.byte_order
        self.unknown2 = msbt_file.read(1)
        self.number_of_sections = self.int_read.ReadUInt16(msbt_file)
        self.unknown3 = self.int_read.ReadUInt16(msbt_file)
        self.filesize_offset = msbt_file.tell()
        self.filesize = self.int_read.ReadUInt32(msbt_file)
        self.unknown4 = msbt_file.read(10)
        self.last_pos = msbt_file.tell()
        msbt_file.seek(0, 2)
        if self.filesize != msbt_file.tell():
            raise InvalidMsbtError('This is not a valid msbt file.')


class LBL1():
    def __init__(self, msbt_file, int_read):
        self.identifier = msbt_file.read(4).decode()
        self.section_size = int_read.ReadUInt32(msbt_file)
        self.padding1 = msbt_file.read(8)
        self.start_of_labels = msbt_file.tell()
        self.number_of_groups = int_read.ReadUInt32(msbt_file)
        self.Groups = [Group(msbt_file, int_read) for i in range(self.number_of_groups)]

        self.Labels = []
        for grp in self.Groups:
            msbt_file.seek(self.start_of_labels + grp.offset, 0)
            for i in range(grp.number_of_labels):
                lbl = Label()
                lbl.length = int(msbt_file.read(1).hex(), 16)
                lbl.name = msbt_file.read(lbl.length).decode()
                lbl.Index = int_read.ReadUInt32(msbt_file)
                lbl.checksum = self.Groups.index(grp)
                self.Labels += (lbl,)

        for lbl in self.Labels:
            previous_checksum = lbl.checksum
            lbl.checksum = label_checksum(lbl.name, self.number_of_groups)
            if previous_checksum != lbl.checksum:
                self.Groups[previous_checksum].number_of_labels -= 1
                self.Groups[lbl.checksum].number_of_labels += 1


def label_checksum(label, number_of_groups):
    group = 0
    for i in range(len(label)):
        group *= 0x492
        group += ord(label[i])
        group &= 0xFFFFFFFF
    return group % number_of_groups


class Group():
    def __init__(self, msbt_file, int_read):
        self.number_of_labels = int_read.ReadUInt32(msbt_file)
        self.offset = int_read.ReadUInt32(msbt_file)


class Label():
    pass


class NLI1():
    def __init__(self, msbt_file, int_read):
        self.identifier = msbt_file.read(4).decode()
        self.section_size = int_read.ReadUInt32(msbt_file)
        self.padding1 = msbt_file.read(8)
        self.unknown2 = msbt_file.read(self.section_size)


class ATO1():
    def __init__(self, msbt_file, int_read):
        self.identifier = msbt_file.read(4).decode()
        self.section_size = int_read.ReadUInt32(msbt_file)
        self.padding1 = msbt_file.read(8)
        self.unknown2 = msbt_file.read(self.section_size)


class ATR1():
    def __init__(self, msbt_file, int_read):
        self.identifier = msbt_file.read(4).decode()
        self.section_size = int_read.ReadUInt32(msbt_file)
        self.padding1 = msbt_file.read(8)
        self.number_of_attributes = int_read.ReadUInt32(msbt_file)
        self.unknown2 = msbt_file.read(self.section_size - 4)


class TSY1():
    def __init__(self, msbt_file, int_read):
        self.identifier = msbt_file.read(4).decode()
        self.section_size = int_read.ReadUInt32(msbt_file)
        self.padding1 = msbt_file.read(8)
        self.unknown2 = msbt_file.read(self.section_size)


class TXT2():
    def __init__(self, msbt_file, parent, int_read):
        self.identifier = msbt_file.read(4).decode()
        self.section_size = int_read.ReadUInt32(msbt_file)
        self.padding1 = msbt_file.read(8)
        self.start_of_strings = msbt_file.tell()
        self.number_of_strings = int_read.ReadUInt32(msbt_file)
        self.offsets = [int_read.ReadUInt32(msbt_file) for i in range(self.number_of_strings)]

        self.Original_Strings = []
        for i in range(self.number_of_strings):
            next_offset = self.start_of_strings + self.offsets[i + 1] if i + 1 < len(
                self.offsets) else self.start_of_strings + self.section_size
            msbt_file.seek(self.start_of_strings + self.offsets[i], 0)
            result = b""
            while msbt_file.tell() < next_offset and msbt_file.tell() < parent.header.filesize:
                if parent.header.encoding_byte == b'\x00':
                    result += msbt_file.read(1)
                else:
                    result += msbt_file.read(2)

            #
            self.Original_Strings += (parse_msbt_string(result, parent.header.file_encoding),)
        self.Strings = self.Original_Strings.copy()
        # ((UInt32)startOfStrings + offsets[i + 1]) : ((UInt32)startOfStrings + TXT2.SectionSize)

        for lbl in parent.lbl1.Labels:
            lbl.string = self.Strings[lbl.Index]


class msbt():
    def __init__(self, msbt_dir):
        self.has_labels = False
        self.padding_char = b'\xAB'
        self.msbt_file = open(msbt_dir, 'rb')
        self.header = header(self.msbt_file)
        self.int_read = self.header.int_read
        self.msbt_file.seek(self.header.last_pos, 0)
        self.Section_Order = []
        for i in range(self.header.number_of_sections):
            section_name = self.msbt_file.read(4).decode()
            self.msbt_file.seek(-4, 1)
            match section_name:
                case "LBL1":
                    self.lbl1 = LBL1(self.msbt_file, self.int_read)
                    if len(self.lbl1.Labels) > 0:
                        self.has_labels = True
                    self.padding_seek()
                case "NLI1":
                    self.nli1 = NLI1(self.msbt_file, self.int_read)
                    self.padding_seek()
                case "ATO1":
                    self.ato1 = ATO1(self.msbt_file, self.int_read)
                case "ATR1":
                    self.atr1 = ATR1(self.msbt_file, self.int_read)
                    self.padding_seek()
                case "TSY1":
                    self.tsy1 = TSY1(self.msbt_file, self.int_read)
                    self.padding_seek()
                case "TXT2":
                    self.txt2 = TXT2(self.msbt_file, self, self.int_read)
                    # print(self.txt2.Original_Strings)
                    self.padding_seek()
            self.Section_Order += (section_name,)

        # self.save()

    def padding_seek(self):
        remainder = self.msbt_file.tell() % 16
        if remainder > 0:
            self.padding_char = self.msbt_file.read(1)
            self.msbt_file.seek(-1, 1)
            self.msbt_file.seek(16 - remainder, 1)

    def add_label(self, name):
        nstr = ""
        self.txt2.Strings += (nstr,)
        self.txt2.Original_Strings += (nstr,)

        nlbl = Label()
        nlbl.length = len(name)
        nlbl.name = name
        nlbl.Index = self.txt2.Strings.index(nstr, )
        nlbl.checksum = label_checksum(name, self.lbl1.number_of_groups)
        nlbl.string = nstr
        self.lbl1.Labels += (nlbl,)

        self.lbl1.Groups[nlbl.checksum].number_of_labels += 1
        if hasattr(self, "atr1"):
            self.atr1.number_of_attributes += 1
        self.txt2.number_of_strings += 1

        return nlbl

    def rename_label(self, lbl, new_name):
        lbl.length = len(new_name)
        lbl.name = new_name
        self.lbl1.Groups[lbl.checksum].number_of_labels -= 1
        lbl.checksum = label_checksum(new_name, self.lbl1.number_of_groups)
        self.lbl1.Groups[lbl.checksum].number_of_labels += 1

    def remove_label(self, lbl):
        text_index = self.txt2.Strings.index(lbl.string)
        for i in range(self.txt2.number_of_strings):
            if self.lbl1.Labels[i].Index > text_index:
                self.lbl1.Labels[i].Index -= 1
        self.lbl1.Groups[lbl.checksum].number_of_labels -= 1
        self.lbl1.Labels.remove(lbl)
        if hasattr(self, "atr1"):
            self.atr1.number_of_attributes -= 1
        self.txt2.Strings = self.txt2.Strings[:lbl.Index] + self.txt2.Strings[lbl.Index + 1:]
        self.txt2.Original_Strings = self.txt2.Original_Strings[:lbl.Index] + self.txt2.Original_Strings[lbl.Index + 1:]
        self.txt2.number_of_strings -= 1

    def save(self, save_dir):
        # result = False
        self.new_file = BytesIO()
        self.new_file.write(self.header.identifier.encode("ascii"))
        self.new_file.write(self.header.byte_order_mark)
        self.new_file.write(self.header.unknown1.to_bytes(2, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.header.encoding_byte)
        self.new_file.write(self.header.unknown2)
        self.new_file.write(
            self.header.number_of_sections.to_bytes(2, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.header.unknown3.to_bytes(2, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.header.filesize.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.header.unknown4)
        for section in self.Section_Order:
            match section:
                case "LBL1":
                    self.write_LBL1()
                case "NLI1":
                    self.write_NLI1()
                case "ATO1":
                    self.write_ATO1()
                case "ATR1":
                    self.write_ATR1()
                case "TSY1":
                    self.write_TSY1()
                case "TXT2":
                    self.write_TXT2()

        file_size = self.new_file.tell()

        self.new_file.seek(self.header.filesize_offset, 0)
        self.new_file.write(file_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))

        self.new_file.seek(0)
        new_bytes = self.new_file.read()
        final_file = open(save_dir, 'wb')

        final_file.write(new_bytes)
        final_file.close()

    def write_LBL1(self):
        new_size = 4
        new_size += 8 * len(self.lbl1.Groups)

        for lbl in self.lbl1.Labels:
            new_size += (5 + len(lbl.name))
        offsets_length = self.lbl1.number_of_groups * 8 + 4
        running_total = 0

        for i in range(len(self.lbl1.Groups)):
            self.lbl1.Groups[i].offset = offsets_length + running_total
            for lbl in self.lbl1.Labels:
                if lbl.checksum == i:
                    running_total += 5 + len(lbl.name)

        self.new_file.write(self.lbl1.identifier.encode('ascii'))
        self.new_file.write(new_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.lbl1.padding1)
        self.new_file.write(
            self.lbl1.number_of_groups.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))

        for grp in self.lbl1.Groups:
            self.new_file.write(grp.number_of_labels.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
            self.new_file.write(grp.offset.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))

        for grp in self.lbl1.Groups:
            for lbl in self.lbl1.Labels:
                if lbl.checksum == self.lbl1.Groups.index(grp):
                    self.new_file.write(bytes([lbl.length]))
                    self.new_file.write(lbl.name.encode('ascii'))
                    self.new_file.write(lbl.Index.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))

        self.padding_write(self.new_file)

    def write_NLI1(self):
        self.new_file.write(self.nli1.identifier.encode('ascii'))
        self.new_file.write(self.nli1.section_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.nli1.padding1)
        self.new_file.write(self.nli1.unknown2)

        self.padding_write(self.new_file)

    def write_ATO1(self):
        self.new_file.write(self.ato1.identifier.encode('ascii'))
        self.new_file.write(self.ato1.section_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.ato1.padding1)
        self.new_file.write(self.ato1.unknown2)

    def write_ATR1(self):
        self.new_file.write(self.atr1.identifier.encode('ascii'))
        self.new_file.write(self.atr1.section_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.atr1.padding1)
        self.new_file.write(
            self.atr1.number_of_attributes.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.atr1.unknown2)

        self.padding_write(self.new_file)

    def write_TSY1(self):
        self.new_file.write(self.tsy1.identifier.encode('ascii'))
        self.new_file.write(self.tsy1.section_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.tsy1.padding1)
        self.new_file.write(self.tsy1.unknown2)

        self.padding_write(self.new_file)

    def write_TXT2(self):
        new_size = self.txt2.number_of_strings * 4 + 4

        for i in range(self.txt2.number_of_strings):
            new_size += len(compile_msbt_string(self.txt2.Strings[i], self.header.file_encoding))

        self.new_file.write(self.txt2.identifier.encode('ascii'))
        self.new_file.write(new_size.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        self.new_file.write(self.txt2.padding1)
        start_of_strings = self.new_file.tell()
        self.new_file.write(
            self.txt2.number_of_strings.to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))

        Offsets = []
        offsets_length = self.txt2.number_of_strings * 4 + 4
        running_total = 0
        for i in range(self.txt2.number_of_strings):
            Offsets += (offsets_length + running_total,)
            running_total += len(compile_msbt_string(self.txt2.Strings[i], self.header.file_encoding))

        for i in range(self.txt2.number_of_strings):
            self.new_file.write(Offsets[i].to_bytes(4, 'little' if self.header.byte_order == 'le' else 'big'))
        for i in range(self.txt2.number_of_strings):

            for j in range(len(self.txt2.Strings)):
                self.txt2.Original_Strings[i] = self.txt2.Strings[i]

            self.new_file.write(compile_msbt_string(self.txt2.Strings[i], self.header.file_encoding))

        self.padding_write(self.new_file)

    def padding_write(self, file):
        remainder = file.tell() % 16
        if remainder > 0:
            for i in range(16 - remainder):
                file.write(self.padding_char)


class InvalidMsbtError(Exception):
    pass

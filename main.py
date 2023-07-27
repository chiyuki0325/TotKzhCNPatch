#!/usr/bin/env python3

# 《塞尔达传说：王国之泪》汉化优化补丁

import yaml
from pathlib import Path
from subprocess import run as run_command
import shutil

from lib.restbl import RESTBL
from lib.msbt_wrapper import MSBT
from lib.hash import compute_crc32
from lib import sarc_tool

# 补丁文件
FONT_PATCH_PATH: Path = Path('./patches/Font_CNzh.Nin_NX_NVN.bfarc.xdelta')
REPLACEMENTS_PATH: Path = Path('./replacements/default_replacements.yml')

# 来自游戏本体的二进制文件
ZSTD_DICT_PATH: Path = Path('./binaries/zs.zsdic')
DEFAULT_ZSDIC_PACK_PATH = Path('./binaries/romfs/Pack/ZsDic.pack.zs')
DEFAULT_RSIZETABLE_PATH: Path = Path('./binaries/romfs/System/Resource/ResourceSizeTable.Product.110.rsizetable.zs')
DEFAULT_FONT_PATH = Path('./binaries/romfs/Font/Font_CNzh.Nin_NX_NVN.bfarc.zs')
DEFAULT_MESSAGE_PACK_PATH = Path('./binaries/romfs/Mals/CNzh.Product.110.sarc.zs')

# 文件夹
OUTPUT_DIR: Path = Path('./output')
WORKING_DIR: Path = Path('./working')

print('正在创建文件夹...')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
WORKING_DIR.mkdir(parents=True, exist_ok=True)
for folder in ['Mals', 'Font', 'System/Resource']:
    (OUTPUT_DIR / folder).mkdir(parents=True, exist_ok=True)
print('')

# 准备 zsdic
if not ZSTD_DICT_PATH.exists():
    print('正在准备 Zstd 字典...')
    unpacked_zsdic_pack_path: Path = WORKING_DIR / 'ZsDic.pack'
    unpacked_zsdic_path: Path = WORKING_DIR / 'ZsDic'
    unpacked_zsdic_path.mkdir(parents=True, exist_ok=True)
    run_command(['zstd', '-d', DEFAULT_ZSDIC_PACK_PATH, '-o', unpacked_zsdic_pack_path])

    sarc_tool.extract(
        unpacked_zsdic_pack_path.__str__(),
        unpacked_zsdic_path.__str__()
    )

    Path(unpacked_zsdic_path / 'zs.zsdic').rename(ZSTD_DICT_PATH)

# 资源表

dest_rsizetable_path: Path = OUTPUT_DIR / 'System/Resource/ResourceSizeTable.Product.110.rsizetable.zs'
if not dest_rsizetable_path.exists():

    print('正在解压资源表...')
    unpacked_rsizetable_path: Path = WORKING_DIR / 'ResourceSizeTable.Product.110.rsizetable'
    run_command(['zstd', '-d', DEFAULT_RSIZETABLE_PATH, '-o', unpacked_rsizetable_path])
    print('')

    print('正在扩容资源表...')
    rsizetable: RESTBL = RESTBL.from_binary_data(unpacked_rsizetable_path.read_bytes())
    for item in [
        'Mals/CNzh.Product.110.sarc',
        'Font/Font_CNzh.Nin_NX_NVN.bfarc'
    ]:
        item_hash: int = compute_crc32(item)
        print('-', item)
        original_size: int = rsizetable.m_crc_table[item_hash]
        print('  原始大小: ', original_size)
        rsizetable.m_crc_table[item_hash] = original_size * 2
        print('  ... 扩容完毕')
    print('')

    print('正在打包资源表...')
    with open(unpacked_rsizetable_path, 'wb') as f:
        f.write(rsizetable.to_binary())
    run_command(['zstd', '-19', '-r', '-o', dest_rsizetable_path, unpacked_rsizetable_path])
    unpacked_rsizetable_path.unlink()
    print('')

# 字体

dest_font_path: Path = OUTPUT_DIR / 'Font/Font_CNzh.Nin_NX_NVN.bfarc.zs'
if not dest_font_path.exists():
    print('正在解压字体...')
    unpacked_font_path: Path = WORKING_DIR / 'Font_CNzh.Nin_NX_NVN.original.bfarc'
    patched_font_path: Path = WORKING_DIR / 'Font_CNzh.Nin_NX_NVN.bfarc'
    run_command(['zstd', '-D', ZSTD_DICT_PATH, '-d', DEFAULT_FONT_PATH, '-o', unpacked_font_path])
    print('')

    print('正在给字体打补丁...')
    run_command(['xdelta3', '-d', '-s', unpacked_font_path, FONT_PATCH_PATH, patched_font_path])
    print('')

    print('正在打包字体...')
    run_command(['zstd', '-19', '-D', ZSTD_DICT_PATH, '-r', '-o', dest_font_path, patched_font_path])
    unpacked_font_path.unlink()
    patched_font_path.unlink()
    print('')

# 字符串

dest_message_pack_path: Path = OUTPUT_DIR / 'Mals/CNzh.Product.110.sarc.zs'
if not dest_message_pack_path.exists():
    print('正在解压字符串包...')
    unpacked_message_pack_path: Path = WORKING_DIR / 'CNzh.Product.110.sarc'
    run_command(['zstd', '-D', ZSTD_DICT_PATH, '-d', DEFAULT_MESSAGE_PACK_PATH, '-o', unpacked_message_pack_path])
    unpacked_messages_dir: Path = WORKING_DIR / 'messages'
    sarc_tool.extract(
        unpacked_message_pack_path.__str__(),
        unpacked_messages_dir.__str__()
    )
    unpacked_message_pack_path.unlink()
    print('')

    print('正在汉化字符串...')
    with open(REPLACEMENTS_PATH, "r") as f:
        replacements: dict[str, str] = yaml.safe_load(f)
    print(replacements)
    for file in unpacked_messages_dir.glob('**/*.msbt'):
        print('-', file.relative_to(unpacked_messages_dir))
        msbt: MSBT = MSBT(file)
        this_file_replacements_count: int = 0
        for i in range(len(msbt.texts)):
            original_text: str = msbt.texts[i]
            new_text: str = original_text
            for original, replacement in replacements.items():
                new_text = new_text.replace(original, replacement)
            if original_text != new_text:
                print('  ID:', msbt.labels[i].name)
                print('  原始:', original_text)
                print('  订正:', new_text)
                this_file_replacements_count += 1
                msbt.texts[i] = new_text
        if this_file_replacements_count != 0:
            msbt.save(file)
    print('')

    print('正在打包字符串包...')
    packed_message_pack_path: Path = WORKING_DIR / 'CNzh.Product.110.sarc'
    sarc_tool.pack(
        root=unpacked_messages_dir.__str__(),
        endianness='<',  # Switch 是小端序
        level=-1,  # 不使用 Yaz0 压缩，而是使用 Zstd 压缩
        outname=packed_message_pack_path.__str__()
    )
    run_command(['zstd', '-19', '-D', ZSTD_DICT_PATH, '-r', '-o', dest_message_pack_path, packed_message_pack_path])
    packed_message_pack_path.unlink()
    print('')

dist_dir: Path = Path('./dist')

dist_romfs_dir: Path = dist_dir / '汉化优化补丁/romfs'
dist_romfs_dir.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR.rename(dist_romfs_dir)

shutil.rmtree(WORKING_DIR)

print('补丁生成完毕！')
print('请将 "dist/汉化优化补丁" 文件夹复制到模拟器的 mod 目录。')

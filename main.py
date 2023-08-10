#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 《塞尔达传说：王国之泪》汉化优化补丁
# 当前版本:
PATCH_VERSION: str = '20230810-1'

import yaml
from pathlib import Path
from subprocess import run as run_command
import shutil
import os

from lib.restbl import RESTBL
from lib.msbt_wrapper import MSBT
from lib.hash import compute_crc32
from lib import sarc_tool

os.putenv('PYTHONUNBUFFERED', '1')

print('《塞尔达传说：王国之泪》汉化优化补丁')
print('版本:', PATCH_VERSION)
print('By 是一刀斩哒')
print('https://github.com/YidaozhanYa/TotKzhCNPatch')
print('')
print('--------------------------------------------')
print('')

# 询问是否使用额外补丁
print('在打补丁之前，请选择是否替换如下的条目:')
print('这些条目为日文原文的变动，导致中文名发生了变化。')
print('如果你想使用这些译名，请输入 "y"。')
print('如果你想使用原版译名，请直接按回车。')
print('')
for item in [
    ['王国之泪', '旷野之息:'],
    ['初始之剑', '长剑'],
    ['海风盾', '勇者盾'],
    ['天空的白刃剑', '女神的白刃剑'],
    ['异次元恶灵套装', '幻影盖侬套装']
]:
    print(item[0], '->', item[1])
if input('> ').lower().strip()[0] == 'y':
    use_additional_replacements: bool = True
else:
    use_additional_replacements: bool = False

print('获取游戏版本...')
file_name = list(Path('.').glob('./binaries/romfs/Mals/CNzh.Product.*.sarc.zs'))[0].name
messages_version = file_name.split('.sarc.zs')[0].split('.')[-1]
file_name = list(Path('.').glob('./binaries/romfs/System/Resource/ResourceSizeTable.Product.*.rsizetable.zs'))[0].name
game_version = file_name.split('.rsizetable.zs')[0].split('.')[-1]
print('游戏字符串版本:', messages_version)
print('游戏版本:', game_version)
print('')

# 补丁文件
FONT_PATCH_PATH: Path = Path('./patches/Font_CNzh.Nin_NX_NVN.bfarc.xdelta')
DEFAULT_REPLACEMENTS_PATH: Path = Path('./replacements/default.yml')
ADDITIONAL_REPLACEMENTS_PATH: Path = Path('./replacements/additional.yml')

# 来自游戏本体的二进制文件
ZSTD_DICT_PATH: Path = Path('./binaries/zs.zsdic')  # 从 pack 文件中解包
DEFAULT_ZSDIC_PACK_PATH = Path('./binaries/romfs/Pack/ZsDic.pack.zs')
DEFAULT_RSIZETABLE_PATH: Path = Path(
    f'./binaries/romfs/System/Resource/ResourceSizeTable.Product.{game_version}.rsizetable.zs')
DEFAULT_FONT_PATH = Path('./binaries/romfs/Font/Font_CNzh.Nin_NX_NVN.bfarc.zs')
DEFAULT_MESSAGE_PACK_PATH = Path(f'./binaries/romfs/Mals/CNzh.Product.{messages_version}.sarc.zs')

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

dest_rsizetable_path: Path = OUTPUT_DIR / f'System/Resource/ResourceSizeTable.Product.{game_version}.rsizetable.zs'
if not dest_rsizetable_path.exists():

    print('正在解压资源表...')
    unpacked_rsizetable_path: Path = WORKING_DIR / f'ResourceSizeTable.Product.{game_version}.rsizetable'
    run_command(['zstd', '-d', DEFAULT_RSIZETABLE_PATH, '-o', unpacked_rsizetable_path])
    print('')

    print('正在扩容资源表...')
    rsizetable: RESTBL = RESTBL.from_binary_data(unpacked_rsizetable_path.read_bytes())
    for item in [
        f'Mals/CNzh.Product.{messages_version}.sarc',
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

dest_message_pack_path: Path = OUTPUT_DIR / f'Mals/CNzh.Product.{messages_version}.sarc.zs'
if not dest_message_pack_path.exists():
    print('正在解压字符串包...')
    unpacked_message_pack_path: Path = WORKING_DIR / f'CNzh.Product.{messages_version}.sarc'
    run_command(['zstd', '-D', ZSTD_DICT_PATH, '-d', DEFAULT_MESSAGE_PACK_PATH, '-o', unpacked_message_pack_path])
    unpacked_messages_dir: Path = WORKING_DIR / 'messages'
    sarc_tool.extract(
        unpacked_message_pack_path.__str__(),
        unpacked_messages_dir.__str__()
    )
    unpacked_message_pack_path.unlink()
    print('')

    print('正在汉化字符串...')

    replacement_files: list[Path] = [
        DEFAULT_REPLACEMENTS_PATH
    ]
    if use_additional_replacements:
        replacement_files.append(ADDITIONAL_REPLACEMENTS_PATH)
        print('(使用额外补丁)')

    for replacement_file in replacement_files:
        with open(replacement_file, "rb") as f:
            yaml_str: str = f.read().decode('utf-8')
            replacements: dict[str, str] = yaml.safe_load(yaml_str)
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
    packed_message_pack_path: Path = WORKING_DIR / f'CNzh.Product.{messages_version}.sarc'
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

folder_name: str = '汉化优化补丁 ' + PATCH_VERSION + ' (' + game_version + ')'
if use_additional_replacements:
    folder_name += ' (FULL)'

dist_romfs_dir: Path = dist_dir / f'{folder_name}/romfs'
dist_romfs_dir.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR.rename(dist_romfs_dir)

shutil.rmtree(WORKING_DIR)

print('补丁生成完毕！')
print(f'请将 "dist/{folder_name}" 文件夹复制到模拟器的 mod 目录。')

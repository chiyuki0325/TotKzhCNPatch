## 《塞尔达传说：王国之泪》汉化优化补丁

在本作，游戏内的译名出现了“繁吃简”的情况，《旷野之息》中繁体中文的译名被用于本作的简体译名，比如“阿陨”被修改为“阿沅”，“璐菊”被修改为“露珠”等。

中文字体也被修改，在《旷野之息》的简体中文语言中，统一使用华康黑体，而本作中的中英文字体不统一，导致了观感上的不和谐。

本补丁旨在修复上述问题，使游戏内的译名与《旷野之息》保持一致，同时统一中英文字体，并且修复部分错误翻译，让《旷野之息》的老玩家能够更好地适应本作。

本补丁分标准版和完全版两个版本，完全版还把一些王国之泪日文原文就更改的名称（如幻影盖侬套装 -> 异次元恶灵套装）修改回旧名称。

当前版本: **20230810-1**

### 预览

![1](./preview/1.png)

![2](./preview/2.png)

![3](./preview/3.png)

### 如何使用

本补丁理论上适用于所有版本的游戏，已经在 1.0.0 1.1.0 和 1.2.0上测试通过。

1、安装 [msys2](https://www.msys2.org)。

2、获取《塞尔达传说：王国之泪》的 romfs 文件夹。romfs 可以从模拟器或 NS 破解系统中解包。

- 如果使用 Yuzu 模拟器，则在模拟器的主菜单对《塞尔达传说：王国之泪》点击右键。选择“转储 RomFS”->“转储 RomFS”，点击确定，等待转储完成后，会打开生成的 romfs 文件夹。

- 如果是 NS 上玩的，可以用 DBI 导出这几个文件：

  - romfs/Pack/ZsDic.pack.zs
  - romfs/System/Resource/ResourceSizeTable.Product.(游戏版本号，比如 110).rsizetable.zs
  - romfs/Font/Font_CNzh.Nin_NX_NVN.bfarc.zs
  - romfs/Mals/CNzh.Product.110.sarc.zs

3、打开 msys2 并执行以下命令。

```bash
# 安装所需要的软件包
pacman -Syu git python python-pip zstd xdelta3 --needed

# 克隆补丁项目
cd "$USERPROFILE/Downloads"
git clone https://github.com/YidaozhanYa/TotKzhCNPatch.git
cd TotKzhCNPatch

# 创建 Python 虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 放入 romfs 文件夹
mkdir -p binaries
# 之后把 romfs 文件夹放入“资源管理器左侧「下载」文件夹”->“TotKzhCNPatch”->“binaries”中

# 执行补丁
python main.py
# 此时可以选择打标准版还是完全版
# 打好的补丁位于“资源管理器左侧「下载」文件夹”->“TotKzhCNPatch”->“dist”中
# 之后可以删除 TotKzhCNPatch 文件夹
```

待补丁操作完成后，你可以在 *dist* 目录中找到“*汉化优化补丁*”文件夹。
打好的补丁是 LayeredFS 格式。

### 如何在模拟器上使用

 如果你使用模拟器游玩，就把它放到模拟器的 mod 数据文件夹中，就可以在游戏中看到汉化效果了。

### 如何在破解的 Switch 上使用

补丁可以在破解的 Switch 上使用。你需要更新到 [atmosphere](https://github.com/Atmosphere-NX/Atmosphere) 的最新版本。

这里使用 [DBI](https://github.com/rashevskyv/dbi) 来操作。首先，在 hbmenu 启动 DBI ，以 DBI551-en 为例，选择 `Browse installed applications` - `塞尔达传说 王国之泪` - `Application` - 对着 `romfs` 文件夹按下+，copy 出来，同上面的使用方法，运行脚本。

接着 将其放入 `SD卡/atmosphere/contents/0100F2C0115B6000/romfs` 下，启动游戏，enjoy。

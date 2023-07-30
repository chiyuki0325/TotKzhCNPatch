## 《塞尔达传说：王国之泪》汉化优化补丁

在本作，游戏内的译名出现了“繁吃简”的情况，《旷野之息》中繁体中文的译名被用于本作的简体译名，比如“阿陨”被修改为“阿沅”，“璐菊”被修改为“露珠”等。

中文字体也被修改，在《旷野之息》的简体中文语言中，统一使用华康黑体，而本作中的中英文字体不统一，导致了观感上的不和谐。

本补丁旨在修复上述问题，使游戏内的译名与《旷野之息》保持一致，同时统一中英文字体，并且修复部分错误翻译，让《旷野之息》的老玩家能够更好地适应本作。

当前版本: **20230730-1**

### 预览

![1](./preview/1.png)

![2](./preview/2.png)

![3](./preview/3.png)

### 如何使用

本补丁理论上适用于所有版本的游戏，已经在 1.0.0 1.1.0 和 1.2.0上测试通过。

为规避版权风险，本补丁需要你自行提供游戏的 romfs 文件，之后在 romfs 之上打补丁，生成一个 mod。romfs 可以从模拟器或 NS 自制系统中解包。

首先，你需要安装 Python 3.10 或以上版本，之后获取《塞尔达传说：王国之泪》的 romfs 文件夹。

以 Yuzu 模拟器为例，在模拟器的主菜单对《塞尔达传说：王国之泪》点击右键。选择“转储 RomFS”->“转储 RomFS”，点击确定，等待转储完成后，会打开生成的 romfs 文件夹。

如果是 NS 上玩的，可以只用 DBI 导出这几个文件，这样就省点时间：
- romfs/Pack/ZsDic.pack.zs
- romfs/System/Resource/ResourceSizeTable.Product.(游戏版本号，比如 110).rsizetable.zs
- romfs/Font/Font_CNzh.Nin_NX_NVN.bfarc.zs
- romfs/Mals/CNzh.Product.110.sarc.zs

在项目文件夹下创建名为 binaries 的文件夹，把这个 romfs 文件夹移动到其中，然后在命令行中执行以下命令：

```bash
# 创建并激活 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 执行补丁
python3 main.py
```

待补丁操作完成后，你可以在 dist 目录中找到“汉化优化补丁”文件夹，把它放到模拟器的 mod 数据文件夹中，就可以在游戏中看到汉化效果了。

### 如何在破解的 Switch 上使用

补丁可以在破解的 Switch 上使用。你需要更新到 [atmosphere](https://github.com/Atmosphere-NX/Atmosphere) 的最新版本。

这里使用 [DBI](https://github.com/rashevskyv/dbi) 来操作。首先，在 hbmenu 启动 DBI ，以 DBI551-en 为例，选择 `Browse installed applications` - `塞尔达传说 王国之泪` - `Application` - 对着 `romfs` 文件夹按下+，copy 出来，同上面的使用方法，运行脚本。

接着 将其放入 `SD卡/atmosphere/contents/0100F2C0115B6000/romfs` 下，启动游戏，enjoy。

# RMMV-Toolkit ⚒️ 施工中...
帮助修改/提取 RMMV 所作 RPG 的一些小脚本

仅支持明文，如果您打开 Json 文件是乱码，则不支持。



<hr> 

character_name_modifier.py 一键修改角色名称

mtool_translation_replacer.py 针对 Mtool 工具翻译文件的关键字修改

rmmv_event_extractor.py 提取游戏事件（对话、分支、变量）


## ❓ 如何使用
 - 确保您的电脑已配置 Python 运行环境
 - 确保您的游戏的 Data 文件夹中的 Json 文件不是乱码

1. 按照上方功能描述，找到您需要的脚本，下载 .py 结尾的 Python 文件。
2. 在脚本所在文件夹右键运行 CMD，输入 python / python3 （空格）
3. 将脚本拖入 CMD 或是手动输入路径
4. 回车，按照脚本提示输入

## 📕 常见问题
推荐按照报错信息上网搜寻，或是直接反馈。
### 脚本无法运行

更新至 Python 最新版本。

按照报错信息进行查询，安装相应依赖。

### 脚本输出内容为空

确保路径准确：

根目录下的 data 文件夹，或 www 目录下的 data 文件夹。

确保 Json 文件是明文：

打开其中一个，确保其中不是乱码，脚本仅支持明文保存的游戏。

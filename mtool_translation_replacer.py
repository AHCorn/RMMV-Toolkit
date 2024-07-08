import re
import os

def replace_json_content(file_path, old_value, new_value):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件 '{file_path}' 不存在")

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        pattern = f': "([^"]*{re.escape(old_value)}[^"]*)"'
        
        def replacer(match):
            full_string = match.group(1)
            return f': "{full_string.replace(old_value, new_value)}"'

        updated_content, count = re.subn(pattern, replacer, content)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

        return count

    except FileNotFoundError as e:
        print(f"错误：{e}")
        return 0
    except PermissionError:
        print(f"错误：没有权限访问文件 '{file_path}'")
        return 0
    except UnicodeDecodeError:
        print(f"错误：无法以 UTF-8 编码读取文件 '{file_path}'，请确保文件编码正确")
        return 0
    except Exception as e:
        print(f"发生未预期的错误：{e}")
        return 0

# 主程序
if __name__ == "__main__":
    file_path = input("请输入JSON文件的路径：")
    
    while True:
        old_value = input("请输入要替换的内容（只替换译文部分），或直接按回车退出：")
        if not old_value:
            break

        new_value = input("请输入新的内容：")

        total_replacements = replace_json_content(file_path, old_value, new_value)

        if total_replacements > 0:
            print(f"替换完成。总共进行了 {total_replacements} 处替换。")
            print(f"将包含 '{old_value}' 的部分替换为 '{new_value}'")
        else:
            print("未进行任何替换。请检查文件中是否包含需要替换的内容。")

        print("\n是否继续替换？")

    print("替换结束。！")

import json
import os
import re

def read_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            return json.load(file)
    except json.JSONDecodeError:
        # 编码
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

def write_json_file(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def count_occurrences_in_object(obj, name):
    count = 0
    if isinstance(obj, dict):
        for value in obj.values():
            if isinstance(value, str):
                count += len(re.findall(re.escape(name), value))
            elif isinstance(value, (dict, list)):
                count += count_occurrences_in_object(value, name)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                count += len(re.findall(re.escape(name), item))
            elif isinstance(item, (dict, list)):
                count += count_occurrences_in_object(item, name)
    return count

def find_and_replace_in_object(obj, old_name, new_name):
    count = 0
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                new_value, replacements = re.subn(re.escape(old_name), new_name, value)
                if replacements > 0:
                    obj[key] = new_value
                    count += replacements
            elif isinstance(value, (dict, list)):
                count += find_and_replace_in_object(value, old_name, new_name)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                new_item, replacements = re.subn(re.escape(old_name), new_name, item)
                if replacements > 0:
                    obj[i] = new_item
                    count += replacements
            elif isinstance(item, (dict, list)):
                count += find_and_replace_in_object(item, old_name, new_name)
    return count

def main():
    input_path = input("请输入游戏data文件夹的路径（拖动进来即可）: ").strip('"')  # 去引号
    actors_file = os.path.join(input_path, "Actors.json")
    actors_data = read_json_file(actors_file)

    # 过滤掉为空的角色名
    character_names = [
        actor["name"]
        for actor in actors_data
        if actor and actor.get("name") and actor["name"].strip()
    ]

    character_counts = {name: 0 for name in character_names}

    for file in os.listdir(input_path):
        if file.lower().endswith(".json"):
            file_path = os.path.join(input_path, file)
            try:
                json_data = read_json_file(file_path)
                for name in character_names:
                    character_counts[name] += count_occurrences_in_object(json_data, name)
            except Exception as e:
                print(f"处理文件 {file} 时出错: {str(e)}")

    sorted_characters = sorted(
        character_counts.items(), key=lambda x: x[1], reverse=True
    )

    print("主要角色列表 (按出现次数排序):")
    for index, (character, count) in enumerate(sorted_characters, 1):
        print(f"{index}. {character} (出现 {count} 次)")
    print("0. 自定义替换内容")

    selected_index = int(input("请输入要修改的角色的编号 (0 为自定义替换): "))

    if selected_index == 0:
        old_name = input("请输入要替换的内容: ")
        new_name = input("请输入新的内容: ")
    elif 1 <= selected_index <= len(sorted_characters):
        old_name = sorted_characters[selected_index - 1][0]
        new_name = input("请输入新的角色名称: ")
    else:
        print("无效的选择。")
        return

    total_replacements = 0
    files_modified = 0

    # 遍历data文件夹中的所有JSON文件
    for file in os.listdir(input_path):
        if file.lower().endswith(".json"):
            file_path = os.path.join(input_path, file)
            try:
                json_data = read_json_file(file_path)
                replacements = find_and_replace_in_object(
                    json_data, old_name, new_name
                )
                if replacements > 0:
                    write_json_file(file_path, json_data)
                    print(f"{file}: 替换了 {replacements} 处")
                    total_replacements += replacements
                    files_modified += 1
            except Exception as e:
                print(f"处理文件 {file} 时出错: {str(e)}")

    print("替换完成!")
    print(f"总共修改了 {files_modified} 个文件")
    print(f"总共替换了 {total_replacements} 处")

if __name__ == "__main__":
    main()

import json
import os
import re
from collections import defaultdict
import logging

# 日志
logging.basicConfig(filename='story_extractor.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def load_actor_names(directory):
    actor_names = {}
    actors_file = os.path.join(directory, "Actors.json")
    try:
        with open(actors_file, 'r', encoding='utf-8-sig') as file:
            actors_data = json.load(file)
            for actor in actors_data:
                if actor:
                    actor_names[actor['id']] = actor['name']
        logging.info(f"成功加载 {len(actor_names)} 个角色名称")
    except Exception as e:
        logging.error(f"加载角色名称时出错: {e}")
    return actor_names

def load_map_names(directory):
    map_names = {}
    map_infos_file = os.path.join(directory, "MapInfos.json")
    try:
        with open(map_infos_file, 'r', encoding='utf-8-sig') as file:
            map_infos = json.load(file)
            if isinstance(map_infos, list):
                for map_info in map_infos:
                    if map_info:
                        map_names[map_info['id']] = map_info.get('name', f"地图 {map_info['id']}")
            elif isinstance(map_infos, dict):
                for map_id, map_info in map_infos.items():
                    if map_info:
                        map_names[int(map_id)] = map_info.get('name', f"地图 {map_id}")
        logging.info(f"成功加载 {len(map_names)} 个地图名称")
    except Exception as e:
        logging.error(f"加载地图名称时出错: {e}")
    return map_names

def load_item_names(directory):
    item_names = {}
    items_file = os.path.join(directory, "Items.json")
    try:
        with open(items_file, 'r', encoding='utf-8-sig') as file:
            items_data = json.load(file)
            for item in items_data:
                if item:
                    item_names[item['id']] = item['name']
        logging.info(f"成功加载 {len(item_names)} 个物品名称")
    except Exception as e:
        logging.error(f"加载物品名称时出错: {e}")
    return item_names

def load_variable_names(directory):
    variable_names = {}
    system_file = os.path.join(directory, "System.json")
    try:
        with open(system_file, 'r', encoding='utf-8-sig') as file:
            system_data = json.load(file)
            variables = system_data.get('variables', [])
            for i, name in enumerate(variables):
                if name:
                    variable_names[i] = name
        logging.info(f"成功加载 {len(variable_names)} 个变量名称")
    except Exception as e:
        logging.error(f"加载变量名称时出错: {e}")
    return variable_names

def load_switch_names(directory):
    switch_names = {}
    system_file = os.path.join(directory, "System.json")
    try:
        with open(system_file, 'r', encoding='utf-8-sig') as file:
            system_data = json.load(file)
            switches = system_data.get('switches', [])
            for i, name in enumerate(switches):
                if name:
                    switch_names[i] = name
        logging.info(f"成功加载 {len(switch_names)} 个开关名称")
    except Exception as e:
        logging.error(f"加载开关名称时出错: {e}")
    return switch_names

def clean_text(text, actor_names):
    text = re.sub(r'\\[^N]', '', text)
    text = re.sub(r'\\N\[(\d+)\]', lambda m: actor_names.get(int(m.group(1)), ''), text)
    return text.strip()

def extract_event_info(event, actor_names, map_names, switch_names, variable_names, item_names):
    info = {
        'name': event.get('name', ''),
        'trigger': {
            'type': event.get('trigger', 0),
            'condition': event.get('condition', {})
        },
        'dialogue': [],
        'choices': [],
        'choice_outcomes': [],
        'conditions': [],
        'transfers': [],
        'variable_changes': [],
        'trigger_conditions': []
    }
    
    current_speaker = ""
    choice_outcomes = defaultdict(list)
    
    pages = event.get('pages', [event])  # 公共事件和地图事件
    
    for page_index, page in enumerate(pages, start=1):
        branch_id = 1
        choice_stack = []
        for command in page.get('list', []):
            if command['code'] in [101, 401]:  # 对话
                if command['code'] == 101:
                    current_speaker = clean_text(command['parameters'][4], actor_names) if len(command['parameters']) > 4 else ""
                else:
                    text = clean_text(command['parameters'][0], actor_names)
                    info['dialogue'].append((current_speaker, text))
                    logging.debug(f"提取对话: {current_speaker}: {text}")
            elif command['code'] == 102:  # 选项
                choices = [clean_text(choice, actor_names) for choice in command['parameters'][0]]
                info['choices'].extend(choices)
                choice_stack.append(choices)
                branch_id += 1
                logging.debug(f"提取选项: {choices}")
            elif command['code'] == 402:  # 选项分支
                if choice_stack:
                    current_choice = choice_stack[-1][command['parameters'][0]]
                    choice_outcomes[current_choice].append(f"分支 {page_index}-{branch_id}")
            elif command['code'] == 111:  # 条件分支
                condition = str(command['parameters'][0])
                if condition.strip() and condition not in ["0", "1"]:
                    info['conditions'].append(f"条件: {condition}")
                    logging.debug(f"提取条件: {condition}")
            elif command['code'] == 201:  # 场景转换
                map_id = command['parameters'][1]
                map_name = map_names.get(map_id, f"地图 {map_id}")
                info['transfers'].append(f"转移至 {map_name}")
                logging.debug(f"提取场景转换: 转移至 {map_name}")
            elif command['code'] == 122:  # 变量操作
                variable_name = variable_names.get(command['parameters'][0], f"变量 {command['parameters'][0]}")
                info['variable_changes'].append(f"{variable_name} 发生变化")
                logging.debug(f"提取变量变化: {variable_name} 发生变化")
            elif command['code'] == 0:  # 分支结束
                if choice_stack:
                    choice_stack.pop()
    
    for choice, outcomes in choice_outcomes.items():
        info['choice_outcomes'].append((choice, " -> ".join(outcomes)))
    
    return info

def extract_map_info(map_data, actor_names, map_names, switch_names, variable_names, item_names):
    events = []
    for event_id, event in enumerate(map_data.get('events', [])):
        if event:
            event_info = extract_event_info(event, actor_names, map_names, switch_names, variable_names, item_names)
            if any(event_info.values()):
                events.append((event_id, event_info))
    return events

def extract_all_info(directory):
    all_info = {}
    actor_names = load_actor_names(directory)
    map_names = load_map_names(directory)
    item_names = load_item_names(directory)
    variable_names = load_variable_names(directory)
    switch_names = load_switch_names(directory)
    
    # 地图事件
    for filename in os.listdir(directory):
        if filename.startswith("Map") and filename.endswith(".json") and filename != "MapInfos.json":
            try:
                map_id = int(re.search(r'Map(\d+)\.json', filename).group(1))
                file_path = os.path.join(directory, filename)
                with open(file_path, 'r', encoding='utf-8-sig') as file:
                    json_data = json.load(file)
                    if isinstance(json_data, list) and len(json_data) > 0:
                        json_data = json_data[0]
                    map_info = extract_map_info(json_data, actor_names, map_names, switch_names, variable_names, item_names)
                    if map_info:
                        all_info[map_id] = {
                            'name': map_names.get(map_id, f"地图 {map_id}"),
                            'events': map_info
                        }
                        logging.info(f"成功提取地图 {map_id} 的信息")
            except Exception as e:
                logging.error(f"处理 {filename} 时出错: {e}")
    
    # 公共事件
    common_events_file = os.path.join(directory, "CommonEvents.json")
    if os.path.exists(common_events_file):
        try:
            with open(common_events_file, 'r', encoding='utf-8-sig') as file:
                common_events_data = json.load(file)
                for event in common_events_data:
                    if event:
                        event_info = extract_event_info(event, actor_names, map_names, switch_names, variable_names, item_names)
                        if any(event_info.values()):
                            event_id = event.get('id', 0)
                            all_info[f"CommonEvent_{event_id}"] = {
                                'name': event_info['name'] or f"公共事件 {event_id}",
                                'events': [(event_id, event_info)]
                            }
                            logging.info(f"成功提取公共事件 {event_id} 的信息")
        except Exception as e:
            logging.error(f"处理 CommonEvents.json 时出错: {e}")
    
    return all_info

def merge_events(events):
    merged_events = defaultdict(list)
    for event_id, event_info in events:
        key = json.dumps(event_info['dialogue'])
        merged_events[key].append((event_id, event_info))
    
    result = []
    for dialogue_key, event_group in merged_events.items():
        if len(event_group) > 1:
            merged_info = event_group[0][1].copy()
            merged_info['trigger_conditions'] = [cond for e in event_group for cond in e[1]['trigger_conditions']]
            result.append((f"事件 {event_group[0][0]} + {len(event_group) - 1}", merged_info))
        else:
            result.append((f"事件 {event_group[0][0]}", event_group[0][1]))
    
    return result

def merge_dialogues(dialogues):
    merged = []
    current_dialogue = None
    count = 1

    for dialogue in dialogues:
        if current_dialogue == dialogue:
            count += 1
        else:
            if current_dialogue is not None:
                if count > 1:
                    merged.append((current_dialogue[0], f"{current_dialogue[1]} +{count}"))
                else:
                    merged.append(current_dialogue)
            current_dialogue = dialogue
            count = 1

    if current_dialogue is not None:
        if count > 1:
            merged.append((current_dialogue[0], f"{current_dialogue[1]} +{count}"))
        else:
            merged.append(current_dialogue)

    return merged

def sort_events(all_info):
    sorted_events = []
    for map_id, map_data in all_info.items():
        if isinstance(map_id, int):
            merged_events = merge_events(map_data['events'])
        else:
            merged_events = map_data['events']  # 公共事件不需要合并
        for event_name, event_info in merged_events:
            sorted_events.append((map_id, event_name, event_info))
    
    return sorted_events

def filter_flashback_events(sorted_events, map_names):
    def is_flashback(map_id, event_name):
        if isinstance(map_id, int):
            map_name = map_names.get(map_id, "")
        else:
            map_name = str(map_id)
        return "回想" in map_name.lower() if map_name else False or "回想" in event_name.lower()

    return [(map_id, event_name, event_info) for map_id, event_name, event_info in sorted_events
            if not is_flashback(map_id, event_name)]

def get_user_preferences():
    print("\n高级配置:")
    output_trigger = input("是否输出触发条件？(是/否): ").lower().strip() in ['是', 'y', 'yes']
    output_variable_changes = input("是否输出变量变化？(是/否): ").lower().strip() in ['是', 'y', 'yes']
    output_transfers = input("是否输出场景转换？(是/否): ").lower().strip() in ['是', 'y', 'yes']
    output_choice_outcomes = input("是否输出选项的后续分支？(是/否): ").lower().strip() in ['是', 'y', 'yes']
    
    if output_trigger:
        print("\n触发条件输出设置:")
        output_player_condition = input("是否输出玩家条件（触碰、自动执行等）？(是/否): ").lower().strip() in ['是', 'y', 'yes']
        output_touch_details = input("是否输出触碰内容（地图位置、图像）？(是/否): ").lower().strip() in ['是', 'y', 'yes']
    else:
        output_player_condition = False
        output_touch_details = False
    
    return {
        'output_trigger': output_trigger,
        'output_variable_changes': output_variable_changes,
        'output_transfers': output_transfers,
        'output_choice_outcomes': output_choice_outcomes,
        'output_player_condition': output_player_condition,
        'output_touch_details': output_touch_details
    }

def format_trigger_description(trigger_info):
    trigger_types = {
        0: "自动执行",
        1: "玩家触碰",
        2: "事件触碰",
        3: "自动执行",
        4: "并行处理"
    }
    trigger_type = trigger_types.get(trigger_info['type'], "未知触发类型")
    condition = trigger_info['condition']
    condition_str = ""
    if condition:
        if 'switch1Id' in condition:
            condition_str += f"开关 {condition['switch1Id']} 为真"
        if 'switch2Id' in condition:
            condition_str += f" 且 开关 {condition['switch2Id']} 为真"
        if 'variableId' in condition:
            condition_str += f" 且 变量 {condition['variableId']} >= {condition['variableValue']}"
        if 'selfSwitchCh' in condition:
            condition_str += f" 且 自开关 {condition['selfSwitchCh']} 为真"
        if 'itemId' in condition:
            condition_str += f" 且 拥有物品 ID {condition['itemId']}"
        if 'actorId' in condition:
            condition_str += f" 且 角色 ID {condition['actorId']} 在队伍中"
    return f"{trigger_type}{': ' + condition_str if condition_str else ''}"

def format_choice_outcomes(choice, outcomes, preferences):
    if preferences['output_choice_outcomes']:
        return f"{choice} - 选择后触发: {outcomes}"
    else:
        return choice

def validate_data_directory(directory):
    required_files = ['Actors.json', 'MapInfos.json', 'Items.json', 'System.json']
    missing_files = []
    for file in required_files:
        if not os.path.isfile(os.path.join(directory, file)):
            missing_files.append(file)
    return missing_files

def find_data_directory(base_path):
    if validate_data_directory(base_path) == []:
        return base_path
    
    data_path = os.path.join(base_path, "data")
    if os.path.isdir(data_path) and validate_data_directory(data_path) == []:
        return data_path
    
    return None

def main():
    try:
        while True:
            directory = input("请输入游戏目录的路径: ").strip().strip('"')
            directory = os.path.normpath(directory)
            
            data_dir = find_data_directory(directory)
            if data_dir:
                print(f"找到有效的数据目录: {data_dir}")
                directory = data_dir
                break
            else:
                missing_files = validate_data_directory(directory)
                if missing_files:
                    print(f"在指定目录中缺少以下文件: {', '.join(missing_files)}")
                else:
                    print("无法找到有效的数据目录。")
                print("请确保您输入的是游戏的主目录，或者直接指向 'data' 文件夹。")

        output_file = input("请输入输出文件名（默认为 comprehensive_story.txt）: ").strip()
        if not output_file:
            output_file = "comprehensive_story.txt"
        
        all_info = extract_all_info(directory)
        sorted_events = sort_events(all_info)
    
        filter_flashbacks = input("是否要过滤掉回想相关的事件和地图？(是(y)/否): ").lower().strip() in ['是', 'y', 'yes']
    
        if filter_flashbacks:
            map_names = {}
            for map_id, data in all_info.items():
                if isinstance(map_id, (int, str)):
                    map_names[map_id] = data['name']
                else:
                    logging.warning(f"Unexpected map_id type: {type(map_id)}")
            sorted_events = filter_flashback_events(sorted_events, map_names)

        advanced_config = input("是否进行高级配置？(是(y)/否): ").lower().strip() in ['是', 'y', 'yes']
    
        if advanced_config:
            preferences = get_user_preferences()
        else:
            preferences = {
                'output_trigger': True,
                'output_variable_changes': True,
                'output_transfers': True,
                'output_choice_outcomes': True,
                'output_player_condition': True,
                'output_touch_details': True
            }
    
        dialogue_count = 0
        event_count = 0
        map_count = len(set(map_id for map_id, _, _ in sorted_events if isinstance(map_id, int)))
        common_event_count = len(set(map_id for map_id, _, _ in sorted_events if isinstance(map_id, str) and map_id.startswith("CommonEvent_")))

        with open(output_file, 'w', encoding='utf-8') as file:
            for map_id, event_name, event_info in sorted_events:
                event_count += 1
                if isinstance(map_id, (int, str)):
                    map_name = all_info[map_id]['name']
                else:
                    map_name = f"未知地图 ({type(map_id)})"
                    logging.warning(f"Unexpected map_id type: {type(map_id)}")
                file.write(f"=== {map_name} - {event_info['name'] or event_name} ===\n\n")
            
                if preferences['output_trigger']:
                    trigger_desc = format_trigger_description(event_info['trigger'])
                    file.write(f"触发条件: {trigger_desc}\n\n")
            
                merged_dialogues = merge_dialogues(event_info['dialogue'])
                if merged_dialogues:
                    file.write("对话:\n")
                    for speaker, line in merged_dialogues:
                        dialogue_count += 1
                        if speaker:
                            file.write(f"  {speaker}: {line}\n")
                        else:
                            file.write(f"  {line}\n")
                    file.write("\n")
            
                if event_info['choices']:
                    file.write("选项:\n")
                    for choice, outcome in event_info['choice_outcomes']:
                        formatted_choice = format_choice_outcomes(choice, outcome, preferences)
                        file.write(f"  - {formatted_choice}\n")
                    file.write("\n")
            
                if event_info['conditions']:
                    file.write("条件:\n")
                    for condition in event_info['conditions']:
                        file.write(f"  {condition}\n")
                    file.write("\n")
            
                if preferences['output_transfers'] and event_info['transfers']:
                    file.write("场景转换:\n")
                    for transfer in event_info['transfers']:
                        file.write(f"  {transfer}\n")
                    file.write("\n")
            
                if preferences['output_variable_changes'] and event_info['variable_changes']:
                    file.write("变量变化:\n")
                    for change in event_info['variable_changes']:
                        file.write(f"  {change}\n")
                    file.write("\n")
            
                file.write("\n")

        print(f"提取完成。总共提取了 {map_count} 个地图，{common_event_count} 个公共事件，")
        print(f"{event_count} 个事件，{dialogue_count} 段对话。")
        print(f"综合剧情信息已保存到 {output_file}")
        logging.info(f"提取完成。总共提取了 {map_count} 个地图，{common_event_count} 个公共事件，")
        logging.info(f"{event_count} 个事件，{dialogue_count} 段对话。")

    except Exception as e:
        print(f"处理过程中出错: {e}")
        logging.error(f"处理过程中出错: {e}", exc_info=True)
        print("请确保您有权限访问该路径下的文件，或是否为明文 JSON 格式。")

if __name__ == "__main__":
    main()

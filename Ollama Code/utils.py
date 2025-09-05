import json
import re
import os
from datetime import datetime

def extract_planning(trajectories_json_file_path):
    with open(trajectories_json_file_path) as f:
        traj = json.load(f)

    save_path = "/home/supriyo/Desktop/Project/traj.txt"
    with open(save_path, "w") as f:
        f.write(json.dumps(traj, indent=2) + "\n")

    context_lst = []
    for turn in traj:
        if turn['role'] == 'assistant':
            content = turn['content']
            if "</think>" in content:
                content = content.split("</think>")[-1].strip()
            context_lst.append(content)

    return context_lst[:3]

def content_to_json(data):
    clean_data = re.sub(r'\[CONTENT\]|\[/CONTENT\]', '', data).strip()
    clean_data = re.sub(r'(\".*?\"),\s*#.*', r'\1,', clean_data)
    clean_data = re.sub(r',\s*\]', ']', clean_data)
    clean_data = re.sub(r'\n\s*', '', clean_data)

    save_path = "/home/supriyo/Desktop/Project/clean_1.txt"
    with open(save_path, "w") as f:
        f.write(clean_data + "\n")

    try:
        return json.loads(clean_data)
    except json.JSONDecodeError:
        return content_to_json2(data)

def content_to_json2(data):
    clean_data = re.sub(r'\[CONTENT\]|\[/CONTENT\]', '', data).strip()
    clean_data = re.sub(r'(\".*?\"),\s*#.*', r'\1,', clean_data)
    clean_data = re.sub(r'(\".*?\")\s*#.*', r'\1', clean_data)
    clean_data = re.sub(r',\s*\]', ']', clean_data)
    clean_data = re.sub(r'\n\s*', '', clean_data)

    save_path = "/home/supriyo/Desktop/Project/clean_2.txt"
    with open(save_path, "w") as f:
        f.write(clean_data + "\n")

    try:
        return json.loads(clean_data)
    except json.JSONDecodeError:
        return content_to_json3(data)

def content_to_json3(data):
    clean_data = re.sub(r'\[CONTENT\]|\[/CONTENT\]', '', data).strip()
    clean_data = re.sub(r'(\".*?\"),\s*#.*', r'\1,', clean_data)
    clean_data = re.sub(r'(\".*?\")\s*#.*', r'\1', clean_data)
    clean_data = re.sub(r',\s*\]', ']', clean_data)
    clean_data = re.sub(r'\n\s*', '', clean_data)
    clean_data = re.sub(r'"""', '"', clean_data)
    clean_data = re.sub(r"'''", "'", clean_data)
    clean_data = re.sub(r"\\", "'", clean_data)

    save_path = "/home/supriyo/Desktop/Project/clean_3.txt"
    with open(save_path, "w") as f:
        f.write(clean_data + "\n")

    try:
        return json.loads(f"""{clean_data}""")
    except json.JSONDecodeError:
        return content_to_json4(data)

def content_to_json4(data):
    pattern = r'"Logic Analysis":\s*(\[[\s\S]*?\])\s*,\s*"Task list":\s*(\[[\s\S]*?\])'
    match = re.search(pattern, data)

    save_path = "/home/supriyo/Desktop/Project/4_pattern.txt"
    save_path_1 = "/home/supriyo/Desktop/Project/4_match.txt"
    with open(save_path, "w") as f:
        f.write(pattern + "\n")
    with open(save_path_1, "w") as f:
        f.write(str(type(match)) + "\n")

    if match:
        logic_analysis = json.loads(match.group(1))
        task_list = json.loads(match.group(2))

        with open("/home/supriyo/Desktop/Project/4_logic_analysis.txt", "w") as f:
            f.write(json.dumps(logic_analysis, indent=2) + "\n")
        with open("/home/supriyo/Desktop/Project/4_task_list.txt", "w") as f:
            f.write(json.dumps(task_list, indent=2) + "\n")

        result = {"Logic Analysis": logic_analysis, "Task list": task_list}
        with open("/home/supriyo/Desktop/Project/4_result.txt", "w") as f:
            f.write(json.dumps(result, indent=2) + "\n")
    else:
        result = {}
    return result

def extract_code_from_content(content):
    pattern = r'^```(?:\w+)?\s*\n(.*?)(?=^```)?```'
    code = re.findall(pattern, content, re.DOTALL | re.MULTILINE)
    return code[0] if code else ""

def extract_code_from_content2(content):
    pattern = r'```python\s*(.*?)```'
    result = re.search(pattern, content, re.DOTALL)
    return result.group(1).strip() if result else ""

def format_json_data(data):
    formatted_text = ""
    for key, value in data.items():
        formatted_text += "-" * 40 + "\n"
        formatted_text += f"[{key}]\n"
        if isinstance(value, list):
            formatted_text += "\n".join([f"- {item}" for item in value]) + "\n"
        else:
            formatted_text += str(value) + "\n"
    return formatted_text

def extract_json_from_string(text):
    match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
    return match.group(1) if match else ""

def get_now_str():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def read_all_files(directory, allowed_ext, is_print=True):
    all_files_content = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            relative_path = os.path.relpath(os.path.join(root, filename), directory)
            _file_name, ext = os.path.splitext(filename)

            is_skip = any(dirname.startswith(".") for dirname in os.path.relpath(root, directory).split("/"))
            if filename.startswith(".") or "requirements.txt" in filename or ext == "" or is_skip:
                continue
            if ext not in allowed_ext and _file_name.lower() != "readme":
                continue

            try:
                filepath = os.path.join(root, filename)
                with open(filepath, "r", encoding="utf-8") as file:
                    all_files_content[relative_path] = file.read()
            except Exception:
                continue
    return all_files_content

def read_python_files(directory):
    python_files_content = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".py"):
                relative_path = os.path.relpath(os.path.join(root, filename), directory)
                with open(os.path.join(root, filename), "r", encoding="utf-8") as file:
                    python_files_content[relative_path] = file.read()
    return python_files_content

def print_response(completion_json, is_llm=False):
    print("============================================")
    print(completion_json['text'] if is_llm else completion_json['choices'][0]['message']['content'])
    print("============================================\n")




def num_tokens_from_messages(messages, model="gpt-4o"):
    import tiktoken
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("o200k_base")

    tokens_per_message = 3
    tokens_per_name = 1

    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3
    return num_tokens


def print_log_cost(completion_json, gpt_version, current_stage, output_dir, total_accumulated_cost):
    print("\n" + "=" * 40)
    print(f"📊 {current_stage}")
    print(f"💬 Model: {gpt_version}")
    print(f"🔍 Tokens (approx.): {completion_json['usage']['prompt_tokens']} prompt + {completion_json['usage']['completion_tokens']} completion")
    print(f"✅ Done. No cost calculated for local models.")
    print("=" * 40 + "\n")
    return total_accumulated_cost

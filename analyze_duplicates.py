import re
import sys

def analyze_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find all function definitions
    function_pattern = r"function\s+(\w+)\s*\("
    functions = re.finditer(function_pattern, content)
    
    function_positions = {}
    for match in functions:
        func_name = match.group(1)
        line_num = content[:match.start()].count("\n") + 1
        if func_name not in function_positions:
            function_positions[func_name] = []
        function_positions[func_name].append(line_num)
    
    # Find duplicates
    print("=== 重复的函数定义 ===")
    duplicates = {k: v for k, v in function_positions.items() if len(v) > 1}
    for func_name, positions in sorted(duplicates.items()):
        print(f"{func_name}: {len(positions)}次 - 行号: {positions}")
    
    # Find loadUserInfo() calls
    print("\n=== loadUserInfo() 调用 ===")
    loaduser_pattern = r"loadUserInfo\s*\(\s*\)"
    calls = re.finditer(loaduser_pattern, content)
    call_positions = []
    for match in calls:
        line_num = content[:match.start()].count("\n") + 1
        call_positions.append(line_num)
    print(f"总共调用: {len(call_positions)}次 - 行号: {call_positions}")
    
    # Find duplicate IDs
    print("\n=== 重复的 HTML ID ===")
    id_pattern = r"id=[\"']([^\"']*)[\"']"
    ids = re.findall(id_pattern, content)
    from collections import Counter
    id_counts = Counter(ids)
    duplicates_ids = {k: v for k, v in id_counts.items() if v > 1}
    for id_name, count in sorted(duplicates_ids.items()):
        print(f"{id_name}: {count}次")
    
    return function_positions, call_positions, duplicates_ids

if __name__ == "__main__":
    analyze_html("static/app.html")

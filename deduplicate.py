import re
import sys

def find_function_blocks(content):
    """找到所有函数定义的完整代码块"""
    lines = content.split("\n")
    function_blocks = {}
    
    i = 0
    while i < len(lines):
        line = lines[i]
        # 匹配函数定义
        match = re.match(r"\s*function\s+(\w+)\s*\(", line)
        if match:
            func_name = match.group(1)
            start_line = i
            
            # 找到函数结束位置（匹配大括号）
            brace_count = line.count("{") - line.count("}")
            end_line = i
            
            for j in range(i + 1, len(lines)):
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count == 0:
                    end_line = j
                    break
            
            if func_name not in function_blocks:
                function_blocks[func_name] = []
            function_blocks[func_name].append((start_line, end_line))
            
            i = end_line + 1
        else:
            i += 1
    
    return function_blocks

def deduplicate_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    
    # 找到所有函数块
    function_blocks = find_function_blocks(content)
    
    # 标记要删除的行
    lines_to_delete = set()
    
    print("=== 处理重复函数 ===")
    for func_name, positions in function_blocks.items():
        if len(positions) > 1:
            # 保留最后一个，删除前面的
            for start, end in positions[:-1]:
                print(f"删除 {func_name} (行 {start+1}-{end+1})")
                for line_num in range(start, end + 1):
                    lines_to_delete.add(line_num)
    
    # 处理 loadUserInfo() 调用
    print("\n=== 处理 loadUserInfo() 调用 ===")
    loaduser_calls = []
    for i, line in enumerate(lines):
        if re.search(r"loadUserInfo\s*\(\s*\)", line) and "function" not in line:
            loaduser_calls.append(i)
    
    if len(loaduser_calls) > 1:
        # 保留第一个调用，删除其他
        for call_line in loaduser_calls[1:]:
            print(f"删除 loadUserInfo() 调用 (行 {call_line+1})")
            lines_to_delete.add(call_line)
    
    # 处理重复的 HTML ID
    print("\n=== 处理重复的 HTML ID ===")
    id_positions = {}
    for i, line in enumerate(lines):
        id_matches = re.findall(r"id=[\"']([^\"']+)[\"']", line)
        for id_name in id_matches:
            if id_name not in id_positions:
                id_positions[id_name] = []
            id_positions[id_name].append(i)
    
    # 对于重复的ID，需要找到完整的元素块并删除
    for id_name, positions in id_positions.items():
        if len(positions) > 1 and id_name.strip():
            # 保留最后一个，删除前面的
            for pos in positions[:-1]:
                # 找到这个元素的开始和结束
                start = pos
                # 向上找到标签开始
                while start > 0 and "<" not in lines[start]:
                    start -= 1
                
                # 向下找到标签结束
                end = pos
                tag_match = re.search(r"<(\w+)", lines[start])
                if tag_match:
                    tag_name = tag_match.group(1)
                    # 简单处理：如果是自闭合标签或单行，只删除这一行
                    if "/>" in lines[pos] or f"</{tag_name}>" in lines[pos]:
                        print(f"删除重复 ID {id_name} (行 {pos+1})")
                        lines_to_delete.add(pos)
    
    # 生成新内容
    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
    new_content = "\n".join(new_lines)
    
    return new_content, len(lines), len(new_lines)

if __name__ == "__main__":
    new_content, old_lines, new_lines = deduplicate_html("static/app.html")
    
    with open("static/app.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"\n=== 完成 ===")
    print(f"原始行数: {old_lines}")
    print(f"新行数: {new_lines}")
    print(f"删除行数: {old_lines - new_lines}")

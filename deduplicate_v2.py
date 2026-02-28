import re

def deduplicate_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    
    # 找到所有函数定义及其完整代码块
    function_ranges = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r"\s*function\s+(\w+)\s*\(", line)
        if match:
            func_name = match.group(1)
            start_line = i
            
            # 计算大括号匹配
            brace_count = line.count("{") - line.count("}")
            end_line = i
            
            for j in range(i + 1, len(lines)):
                brace_count += lines[j].count("{") - lines[j].count("}")
                if brace_count == 0:
                    end_line = j
                    break
            
            function_ranges.append({
                "name": func_name,
                "start": start_line,
                "end": end_line
            })
            
            i = end_line + 1
        else:
            i += 1
    
    # 找到重复的函数
    func_dict = {}
    for func in function_ranges:
        name = func["name"]
        if name not in func_dict:
            func_dict[name] = []
        func_dict[name].append(func)
    
    # 标记要删除的行
    lines_to_delete = set()
    
    print("=== 删除重复函数（保留最后一个）===")
    for func_name, occurrences in func_dict.items():
        if len(occurrences) > 1:
            # 删除前面的，保留最后一个
            for func in occurrences[:-1]:
                print(f"删除 {func_name} (行 {func['start']+1}-{func['end']+1})")
                for line_num in range(func["start"], func["end"] + 1):
                    lines_to_delete.add(line_num)
    
    # 生成新内容
    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
    new_content = "\n".join(new_lines)
    
    return new_content, len(lines), len(new_lines)

if __name__ == "__main__":
    # 先恢复备份
    import shutil
    shutil.copy("static/app.html.bak.dedup", "static/app.html")
    print("已恢复备份文件\n")
    
    new_content, old_lines, new_lines = deduplicate_html("static/app.html")
    
    with open("static/app.html", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"\n=== 完成 ===")
    print(f"原始行数: {old_lines}")
    print(f"新行数: {new_lines}")
    print(f"删除行数: {old_lines - new_lines}")

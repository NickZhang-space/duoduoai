import re

def find_function_end(lines, start_idx):
    """从函数开始位置找到函数结束位置"""
    brace_count = lines[start_idx].count("{") - lines[start_idx].count("}")
    
    for j in range(start_idx + 1, len(lines)):
        brace_count += lines[j].count("{") - lines[j].count("}")
        if brace_count == 0:
            return j
    
    return start_idx

def deduplicate_html(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    
    # 目标函数列表
    target_functions = [
        "loadSmartRecommendations",
        "displayRecommendations", 
        "predictTrend",
        "displayTrendPrediction",
        "askQuestion",
        "askQuickQuestion",
        "addChatMessage",
        "checkRisks",
        "displayRisks",
        "toggleAutoRefresh",
        "switchSmartTab"
    ]
    
    # 找到所有函数定义
    function_positions = {func: [] for func in target_functions}
    
    for i, line in enumerate(lines):
        for func_name in target_functions:
            # 匹配 function funcName( 或 async function funcName(
            pattern = r"^\s*(async\s+)?function\s+" + re.escape(func_name) + r"\s*\("
            if re.match(pattern, line):
                end_idx = find_function_end(lines, i)
                function_positions[func_name].append({
                    "start": i,
                    "end": end_idx
                })
    
    # 标记要删除的行
    lines_to_delete = set()
    
    print("=== 删除重复函数（保留最后一个）===")
    for func_name, occurrences in function_positions.items():
        if len(occurrences) > 1:
            print(f"\n{func_name}: 发现 {len(occurrences)} 个定义")
            # 删除前面的，保留最后一个
            for idx, func in enumerate(occurrences[:-1]):
                print(f"  删除第 {idx+1} 个 (行 {func['start']+1}-{func['end']+1})")
                for line_num in range(func["start"], func["end"] + 1):
                    lines_to_delete.add(line_num)
            print(f"  保留第 {len(occurrences)} 个 (行 {occurrences[-1]['start']+1}-{occurrences[-1]['end']+1})")
    
    # 处理 loadUserInfo() 调用
    print("\n=== 处理 loadUserInfo() 调用 ===")
    loaduser_calls = []
    for i, line in enumerate(lines):
        # 查找调用（不是定义）
        if re.search(r"loadUserInfo\s*\(\s*\)", line) and "function" not in line and i not in lines_to_delete:
            loaduser_calls.append(i)
    
    print(f"发现 {len(loaduser_calls)} 个 loadUserInfo() 调用: {[i+1 for i in loaduser_calls]}")
    
    if len(loaduser_calls) > 1:
        # 保留第一个，删除其他
        for call_line in loaduser_calls[1:]:
            print(f"  删除调用 (行 {call_line+1})")
            lines_to_delete.add(call_line)
    
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

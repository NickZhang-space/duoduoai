from fastapi import FastAPI
import sys

# 读取 main.py 找到所有路由定义
with open('main.py', 'r') as f:
    lines = f.readlines()

in_ab_section = False
for i, line in enumerate(lines, 1):
    if 'A/B测试 API' in line:
        in_ab_section = True
        print(f'Line {i}: Found AB test section')
    if in_ab_section and '@app.' in line:
        print(f'Line {i}: {line.strip()}')
    if in_ab_section and i > 1850:
        break

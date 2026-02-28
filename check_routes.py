import sys
sys.path.insert(0, '.')

# 只导入必要的模块来检查路由
from fastapi import FastAPI

# 创建一个测试app
test_app = FastAPI()

# 读取main.py找到所有@app装饰的路由
with open('main.py', 'r') as f:
    content = f.read()
    
import re
routes = re.findall(r'@app\.(get|post|put|delete)\(["'\''](.*?)["'\'']', content)
print('Total routes found:', len(routes))
print('AB test routes:')
for method, path in routes:
    if 'ab-test' in path:
        print(f'  {method.upper()} {path}')

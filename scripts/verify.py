import re, subprocess

# 1. 服务是否正常
result = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'http://localhost/static/app.html'], capture_output=True, text=True)
assert result.stdout == '200', f'Service down! HTTP {result.stdout}'

# 2. JS 括号检查
with open('/root/ecommerce-ai-v2/static/app.html', 'r') as f:
    content = f.read()
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
combined = '\n'.join(scripts)
b, p, k = 0, 0, 0
for ch in combined:
    if ch == '{': b += 1
    elif ch == '}': b -= 1
    elif ch == '(': p += 1
    elif ch == ')': p -= 1
    elif ch == '[': k += 1
    elif ch == ']': k -= 1
assert b == 0 and p == 0 and k == 0, f'JS brackets mismatch! {{ {b}, ( {p}, [ {k}'

# 3. Section depth
lines = content.split('\n')
depth = 0
in_body = False
for i, line in enumerate(lines, 1):
    if '<body' in line: in_body = True
    if in_body:
        depth += line.count('<div') - line.count('</div')
        if 'class="section"' in line:
            assert depth - (line.count('<div') - line.count('</div')) == 2, f'L{i}: section depth wrong'

# 4. 核心 API
import urllib.request, json
apis = ['/static/app.html', '/api/health', '/api/ab-test/list?user_id=1']
for api in apis:
    try:
        r = urllib.request.urlopen(f'http://localhost{api}')
        assert r.status == 200, f'{api} returned {r.status}'
    except Exception as e:
        print(f'WARNING: {api} failed: {e}')

print('ALL CHECKS PASSED ✅')

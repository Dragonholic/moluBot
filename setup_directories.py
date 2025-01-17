import os

# 필요한 디렉토리 생성
directories = [
    'features',
    'chat_logs',
    'rankings'
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)

# __init__.py 파일 생성
with open('features/__init__.py', 'w') as f:
    pass 
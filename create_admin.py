# 创建管理员账号脚本

import sys
sys.path.append('/root/.openclaw-claude/workspace/ecommerce-ai-v2')

from database import SessionLocal, Admin, get_password_hash

def create_admin():
    db = SessionLocal()
    
    # 检查是否已存在管理员
    existing = db.query(Admin).filter(Admin.username == "admin").first()
    if existing:
        print("管理员账号已存在")
        return
    
    # 创建管理员
    admin = Admin(
        username="admin",
        hashed_password=get_password_hash("admin123456")
    )
    
    db.add(admin)
    db.commit()
    
    print("管理员账号创建成功！")
    print("用户名: admin")
    print("密码: admin123456")
    print("请登录后立即修改密码！")
    
    db.close()

if __name__ == "__main__":
    create_admin()

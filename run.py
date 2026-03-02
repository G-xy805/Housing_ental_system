"""
应用启动脚本
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from app import create_app, db
from app.models import User, House, Contract, Payment

# 创建应用
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Flask shell 上下文"""
    return {
        'db': db,
        'User': User,
        'House': House,
        'Contract': Contract,
        'Payment': Payment
    }


if __name__ == '__main__':
    # 获取配置
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"启动房屋租赁系统...")
    print(f"环境：{os.getenv('FLASK_ENV', 'development')}")
    print(f"地址：http://{host}:{port}")
    print(f"调试模式：{debug}")
    
    app.run(host=host, port=port, debug=debug)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
房屋租赁系统 - 一键构建脚本

功能：
    1. 清理旧的构建产物
    2. 构建前端（npm run build）
    3. 运行 PyInstaller 打包
    4. 创建交付文件夹结构
    5. 生成 README.txt 使用说明
    6. 生成增量更新包（--update）

使用方法：
    python build_exe.py                    # 完整构建
    python build_exe.py --skip-frontend    # 跳过前端构建
    python build_exe.py --clean            # 仅清理构建产物
    python build_exe.py --no-clean         # 不清理直接构建
    python build_exe.py --update           # 生成增量更新包
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path

# ==================== 配置常量 ====================

# 应用信息
APP_NAME = "HousingRentalSystem"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Housing Rental System Team"

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.resolve()

# 构建相关目录
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"
BUILD_OUTPUT_DIR = PROJECT_ROOT / "build_output"
RELEASE_DIR = PROJECT_ROOT / "release"
OUTPUT_DIR = RELEASE_DIR / APP_NAME

# 前端目录
FRONTEND_DIR = PROJECT_ROOT / "src"

# 密钥目录
KEYS_DIR = PROJECT_ROOT / "keys"

# 资源目录
RESOURCE_DIR = PROJECT_ROOT / "resource"

# 默认管理员账号
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123"
}

# ==================== 颜色输出工具 ====================

class Colors:
    """终端颜色常量"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.END}\n")


def print_step(step: int, total: int, text: str):
    """打印步骤"""
    print(f"{Colors.CYAN}[{step}/{total}] {text}{Colors.END}")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}  [OK] {text}{Colors.END}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}  [WARN] {text}{Colors.END}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}  [ERROR] {text}{Colors.END}")


def print_info(text: str):
    """打印普通信息"""
    print(f"  {text}")


# ==================== 构建步骤函数 ====================

def clean_build_artifacts():
    """
    步骤1：清理旧的构建产物
    
    清理目录：
        - dist/HousingRentalSystem/
        - build/
        - build_output/
    注意：保留前端构建产物 dist/index.html 等
    """
    print_step(1, 5, "清理旧的构建产物...")
    
    dirs_to_clean = [
        ("PyInstaller 输出", BUILD_OUTPUT_DIR),
        ("build 目录", BUILD_DIR),
        ("release 目录", RELEASE_DIR),
    ]
    
    for name, path in dirs_to_clean:
        if path.exists():
            try:
                shutil.rmtree(path)
                print_success(f"已删除 {name}: {path}")
            except Exception as e:
                print_error(f"删除 {name} 失败: {e}")
                return False
        else:
            print_info(f"{name} 不存在，跳过")
    
    print_success("清理完成")
    return True


def build_frontend():
    """
    步骤2：构建前端
    
    执行命令：
        npm run build
    
    输出：
        dist/ (前端构建产物)
    """
    print_step(2, 5, "构建前端...")
    
    # 检查 package.json 是否存在
    package_json = PROJECT_ROOT / "package.json"
    if not package_json.exists():
        print_error(f"package.json 不存在: {package_json}")
        return False
    
    # 检查 node_modules 是否存在
    node_modules = PROJECT_ROOT / "node_modules"
    if not node_modules.exists():
        print_info("node_modules 不存在，正在安装依赖...")
        try:
            result = subprocess.run(
                ["npm", "install"],
                cwd=PROJECT_ROOT,
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            print_success("依赖安装完成")
        except subprocess.CalledProcessError as e:
            print_error(f"依赖安装失败: {e.stderr}")
            return False
    
    # 执行 npm run build
    print_info("正在执行 npm run build...")
    try:
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=PROJECT_ROOT,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        # 检查构建输出
        frontend_dist = PROJECT_ROOT / "dist"
        if frontend_dist.exists() and (frontend_dist / "index.html").exists():
            print_success(f"前端构建完成: {frontend_dist}")
            return True
        else:
            print_error("前端构建产物不存在")
            return False
            
    except subprocess.CalledProcessError as e:
        print_error(f"前端构建失败: {e.stderr}")
        return False


def run_pyinstaller():
    """
    步骤3：运行 PyInstaller 打包
    
    执行命令：
        pyinstaller build.spec
    
    输出：
        dist/HousingRentalSystem/ (打包产物)
    """
    print_step(3, 5, "运行 PyInstaller 打包...")
    
    # 检查 HousingRentalSystem.spec 是否存在
    build_spec = PROJECT_ROOT / "HousingRentalSystem.spec"
    if not build_spec.exists():
        print_error(f"HousingRentalSystem.spec 不存在: {build_spec}")
        return False
    
    # 检查 PyInstaller 是否安装
    try:
        result = subprocess.run(
            ["pyinstaller", "--version"],
            shell=True,
            capture_output=True,
            text=True
        )
        print_info(f"PyInstaller 版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print_error("PyInstaller 未安装，请运行: pip install pyinstaller")
        return False
    
    # 执行 PyInstaller
    print_info("正在执行 pyinstaller HousingRentalSystem.spec...")
    try:
        result = subprocess.run(
            ["pyinstaller", "HousingRentalSystem.spec", "--noconfirm", "--distpath", str(RELEASE_DIR)],
            cwd=PROJECT_ROOT,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        # PyInstaller 默认输出到 release/{app_name}/
        exe_path = RELEASE_DIR / APP_NAME / f"{APP_NAME}.exe"
        if exe_path.exists():
            print_success(f"打包完成: {exe_path}")
            return True
        else:
            print_error(f"可执行文件不存在: {exe_path}")
            return False
            
    except subprocess.CalledProcessError as e:
        print_error(f"PyInstaller 打包失败")
        print_info(f"错误输出: {e.stderr}")
        return False


def create_delivery_structure():
    """
    步骤4：创建交付文件夹结构
    
    在 PyInstaller 输出目录中创建必要的子目录
    
    最终目录结构：
        dist/HousingRentalSystem/
        ├── HousingRentalSystem.exe
        ├── _internal/        (PyInstaller 运行时文件)
        ├── data/             (数据库目录)
        ├── uploads/          (上传目录)
        ├── logs/             (日志目录)
        ├── keys/             (密钥目录)
        ├── backups/          (备份目录)
        └── README.txt
    """
    print_step(4, 5, "创建交付文件夹结构...")
    
    # PyInstaller 输出目录就是最终交付目录
    pyinstaller_output = RELEASE_DIR / APP_NAME
    
    # 检查 PyInstaller 输出是否存在
    if not pyinstaller_output.exists():
        print_error(f"PyInstaller 输出目录不存在: {pyinstaller_output}")
        return False
    
    # 需要创建的空目录
    empty_dirs = [
        "data",
        "uploads",
        "logs",
        "backups",
    ]
    
    # 创建空目录
    for dir_name in empty_dirs:
        dir_path = pyinstaller_output / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # 创建 .gitkeep 文件保持目录
            gitkeep = dir_path / ".gitkeep"
            gitkeep.touch(exist_ok=True)
            
            print_success(f"创建目录: {dir_name}/")
        except Exception as e:
            print_error(f"创建目录失败 {dir_name}: {e}")
            return False
    
    # 复制密钥文件（如果 _internal 中没有）
    target_keys = pyinstaller_output / "_internal" / "keys"
    if KEYS_DIR.exists() and not target_keys.exists():
        try:
            shutil.copytree(KEYS_DIR, target_keys)
            print_success(f"复制密钥文件: keys/")
        except Exception as e:
            print_warning(f"复制密钥文件失败: {e}")
    
    # 检查必要文件
    required_items = [
        ("可执行文件", pyinstaller_output / f"{APP_NAME}.exe"),
        ("静态文件", pyinstaller_output / "_internal" / "static"),
        ("资源文件", pyinstaller_output / "_internal" / "resource"),
    ]
    
    for name, path in required_items:
        if path.exists():
            print_success(f"{name}: 存在")
        else:
            print_warning(f"{name} 不存在: {path}")
    
    print_success("交付文件夹结构创建完成")
    return True


def generate_readme():
    """
    步骤5：生成 README.txt 使用说明
    """
    print_step(5, 5, "生成 README.txt...")
    
    readme_content = f"""{'=' * 60}
                    {APP_NAME} 使用说明
{'=' * 60}

【系统信息】
    系统名称：{APP_NAME}
    版本号：{APP_VERSION}
    发布日期：{datetime.now().strftime('%Y-%m-%d')}
    开发团队：{APP_AUTHOR}

{'=' * 60}
                      快速开始
{'=' * 60}

【启动方法】
    1. 双击运行 HousingRentalSystem.exe
    2. 等待系统启动完成（控制台窗口会显示启动日志）
    3. 打开浏览器访问 http://localhost:5000
    4. 使用默认管理员账号登录

【默认管理员账号】
    用户名：{DEFAULT_ADMIN['username']}
    密码：{DEFAULT_ADMIN['password']}
    
    ⚠️ 重要提示：首次登录后请立即修改默认密码！

{'=' * 60}
                      目录说明
{'=' * 60}

【用户数据目录】（更新时保留，请勿删除）
    data/       - 数据库文件（重要！包含所有业务数据）
    uploads/    - 上传文件目录（图片、文档等）
    logs/       - 日志文件（运行日志、错误日志）
    backups/    - 数据备份目录（自动/手动备份）
    keys/       - 加密密钥（重要！数据加密密钥）

【程序文件目录】（更新时替换）
    HousingRentalSystem.exe  - 主程序（双击启动）
    _internal/               - 程序依赖文件（运行时库）
    static/                  - 前端静态文件（网页文件）
    resource/                - 资源文件（合同模板等）

{'=' * 60}
                      更新指南
{'=' * 60}

【如何更新程序】
    1. 停止正在运行的程序
    2. 备份用户数据目录（data/, uploads/, keys/）
    3. 下载新的更新包（HousingRentalSystem_Update.zip）
    4. 解压更新包到程序目录，覆盖同名文件
    5. 重新启动程序

【注意事项】
    ✓ 更新包仅包含程序文件，不会覆盖用户数据
    ✓ 更新前建议备份重要数据
    ✓ 如遇问题，可从备份恢复

{'=' * 60}
                      功能说明
{'=' * 60}

【核心功能】
    ✓ 房源管理：添加、编辑、删除房源信息
    ✓ 房东管理：房东信息维护和合同管理
    ✓ 租客管理：租客信息录入和信用评估
    ✓ 合同管理：租赁合同的创建和续签
    ✓ 收款管理：租金收取和欠款提醒
    ✓ 数据备份：自动备份和手动备份
    ✓ 系统监控：性能监控和健康检查

【用户角色】
    - 管理员：拥有所有功能权限
    - 员工：房源、租客、合同管理权限
    - 访客：仅查看公开房源

{'=' * 60}
                      常见问题
{'=' * 60}

【Q1：双击 exe 后闪退怎么办？】
    A：请检查以下项目：
       1. 确保没有其他程序占用 5000 端口
       2. 检查 keys/ 目录下是否有加密密钥文件
       3. 查看 logs/app.log 日志文件获取错误信息
       4. 尝试以管理员身份运行

【Q2：无法访问 http://localhost:5000？】
    A：请检查：
       1. 确认程序正在运行（控制台窗口未关闭）
       2. 检查防火墙是否阻止了访问
       3. 尝试使用 http://127.0.0.1:5000

【Q3：忘记密码怎么办？】
    A：管理员可以重置其他用户密码。
       如果忘记管理员密码，需要：
       1. 停止程序
       2. 删除 data/housing_rental.db 数据库
       3. 重新启动程序（将创建新的默认管理员账号）
       注意：此操作会清空所有数据！

【Q4：如何修改端口？】
    A：创建 .env 文件在程序目录下，添加：
       PORT=8080
       然后重启程序

【Q5：如何备份数据？】
    A：两种方式：
       1. 登录系统，在"数据备份"页面点击"立即备份"
       2. 手动复制 data/housing_rental.db 文件

【Q6：数据库文件在哪里？】
    A：数据库文件位于 data/housing_rental.db
       这是 SQLite 数据库文件，可用工具查看

【Q7：如何迁移到其他电脑？】
    A：复制整个 HousingRentalSystem 文件夹到新电脑即可
       重要：确保包含 data/ 和 keys/ 目录

【Q8：程序启动很慢？】
    A：首次启动需要初始化数据库，可能需要几秒钟
       后续启动会更快

{'=' * 60}
                      安全建议
{'=' * 60}

    1. 首次登录后立即修改默认管理员密码
    2. 定期备份 data/ 目录下的数据库文件
    3. 不要删除 keys/ 目录下的密钥文件
    4. 定期检查 logs/ 目录下的日志文件
    5. 不要将程序暴露在公网环境
    6. 定期更新系统和依赖

{'=' * 60}
                      技术支持
{'=' * 60}

    如遇问题，请检查：
    1. logs/app.log - 应用日志
    2. 控制台输出 - 启动日志
    
    项目地址：{PROJECT_ROOT.name}
    构建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 60}
                      版权声明
{'=' * 60}

    本软件仅供内部使用，未经授权不得传播或商用。

{'=' * 60}
"""
    
    readme_path = OUTPUT_DIR / "README.txt"
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print_success(f"README.txt 已生成: {readme_path}")
        return True
    except Exception as e:
        print_error(f"生成 README.txt 失败: {e}")
        return False


def generate_update_readme():
    """
    生成 UPDATE_README.txt 更新说明文件
    """
    update_readme_content = f"""{'=' * 60}
                    {APP_NAME} 更新说明
{'=' * 60}

【版本信息】
    系统名称：{APP_NAME}
    版本号：{APP_VERSION}
    发布日期：{datetime.now().strftime('%Y-%m-%d')}

{'=' * 60}
                      更新步骤
{'=' * 60}

【重要提示】
    本更新包仅包含程序文件，不包含用户数据。
    更新前请务必备份重要数据！

【更新步骤】
    1. 停止正在运行的程序（关闭控制台窗口）
    
    2. 备份用户数据（强烈建议）
       - 复制 data/ 目录（数据库文件）
       - 复制 uploads/ 目录（上传文件）
       - 复制 keys/ 目录（加密密钥）
    
    3. 解压更新包
       - 将更新包中的所有文件解压到程序目录
       - 覆盖同名文件
    
    4. 启动程序
       - 双击运行 HousingRentalSystem.exe
       - 检查是否正常运行

【注意事项】
    ✓ 更新不会影响用户数据（数据库、上传文件等）
    ✓ 如果更新后出现问题，可以从备份恢复
    ✓ 建议在更新前创建系统还原点

{'=' * 60}
                      目录说明
{'=' * 60}

【用户数据目录】（更新时保留）
    data/       - 数据库文件（重要！）
    uploads/    - 上传的图片和文件
    logs/       - 日志文件
    backups/    - 备份文件
    keys/       - 加密密钥（重要！）

【程序文件目录】（更新时替换）
    HousingRentalSystem.exe  - 主程序
    _internal/               - 程序依赖文件
    static/                  - 前端静态文件
    resource/                - 资源文件

{'=' * 60}
                      常见问题
{'=' * 60}

【Q1：更新后无法启动？】
    A：请检查：
       1. 确保完整解压了更新包
       2. 确保 _internal/ 目录完整
       3. 检查 keys/ 目录是否存在

【Q2：更新后数据丢失？】
    A：更新包不包含用户数据，不会覆盖数据目录
       如果数据丢失，请从备份恢复

【Q3：如何回滚到旧版本？】
    A：如果有旧版本的完整备份：
       1. 停止程序
       2. 删除程序文件（保留用户数据目录）
       3. 解压旧版本程序文件
       4. 启动程序

{'=' * 60}
                      技术支持
{'=' * 60}

    如遇问题，请检查：
    1. logs/app.log - 应用日志
    2. 控制台输出 - 启动日志

    构建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 60}
"""
    return update_readme_content


def create_update_package():
    """
    创建增量更新包
    
    只包含程序文件，不包含用户数据目录：
    - HousingRentalSystem.exe
    - _internal/（已包含 static 和 resource）
    - UPDATE_README.txt
    """
    print_header("创建增量更新包")
    
    # 检查完整构建是否存在
    if not OUTPUT_DIR.exists():
        print_error(f"完整构建不存在，请先运行完整构建: python build_exe.py")
        return False
    
    exe_path = OUTPUT_DIR / f"{APP_NAME}.exe"
    if not exe_path.exists():
        print_error(f"可执行文件不存在: {exe_path}")
        return False
    
    # 用户数据目录（不包含在更新包中）
    user_data_dirs = ['data', 'uploads', 'logs', 'backups', 'keys']
    
    # 更新包路径
    update_zip_path = RELEASE_DIR / f"{APP_NAME}_Update.zip"
    
    print_info(f"正在创建更新包: {update_zip_path}")
    
    try:
        with zipfile.ZipFile(update_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加可执行文件
            print_info(f"添加: {APP_NAME}.exe")
            zipf.write(exe_path, f"{APP_NAME}.exe")
            
            # 添加 _internal 目录（已包含 static 和 resource）
            internal_dir = OUTPUT_DIR / "_internal"
            if internal_dir.exists():
                print_info("添加: _internal/（包含 static 和 resource）")
                for root, dirs, files in os.walk(internal_dir):
                    # 排除用户数据目录
                    dirs[:] = [d for d in dirs if d not in user_data_dirs]
                    for file in files:
                        file_path = Path(root) / file
                        arcname = f"_internal/{file_path.relative_to(internal_dir)}"
                        zipf.write(file_path, arcname)
            else:
                print_error("_internal/ 目录不存在")
                return False
            
            # 添加更新说明文件
            print_info("添加: UPDATE_README.txt")
            update_readme = generate_update_readme()
            zipf.writestr("UPDATE_README.txt", update_readme)
        
        # 获取更新包大小
        zip_size = update_zip_path.stat().st_size
        size_mb = zip_size / (1024 * 1024)
        
        print_success(f"更新包创建成功: {update_zip_path}")
        print_info(f"更新包大小: {size_mb:.2f} MB")
        print()
        print_info("更新包内容:")
        print_info(f"  ├── {APP_NAME}.exe")
        print_info("  ├── _internal/")
        print_info("  │   ├── static/     (前端静态文件)")
        print_info("  │   ├── resource/   (资源文件)")
        print_info("  │   └── ...         (其他程序依赖)")
        print_info("  └── UPDATE_README.txt")
        print()
        print_info("不包含的用户数据目录:")
        for dir_name in user_data_dirs:
            print_info(f"  ✗ {dir_name}/")
        
        return True
        
    except Exception as e:
        print_error(f"创建更新包失败: {e}")
        return False


# ==================== 主构建流程 ====================

def build_all(skip_frontend: bool = False, no_clean: bool = False):
    """
    执行完整构建流程
    
    Args:
        skip_frontend: 是否跳过前端构建
        no_clean: 是否跳过清理步骤
    """
    start_time = time.time()
    
    print_header(f"{APP_NAME} v{APP_VERSION} 构建脚本")
    print_info(f"项目目录: {PROJECT_ROOT}")
    print_info(f"输出目录: {OUTPUT_DIR}")
    print_info(f"构建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤1：清理构建产物
    if not no_clean:
        if not clean_build_artifacts():
            print_error("构建失败：清理步骤出错")
            return False
    else:
        print_info("跳过清理步骤")
    
    # 步骤2：构建前端
    if not skip_frontend:
        if not build_frontend():
            print_error("构建失败：前端构建步骤出错")
            return False
    else:
        print_info("跳过前端构建步骤")
    
    # 步骤3：PyInstaller 打包
    if not run_pyinstaller():
        print_error("构建失败：PyInstaller 打包步骤出错")
        return False
    
    # 步骤4：创建交付文件夹结构
    if not create_delivery_structure():
        print_error("构建失败：创建交付文件夹步骤出错")
        return False
    
    # 步骤5：生成 README.txt
    if not generate_readme():
        print_error("构建失败：生成 README.txt 步骤出错")
        return False
    
    # 计算构建时间
    elapsed_time = time.time() - start_time
    
    # 打印构建成功信息
    print_header("构建成功！")
    print_info(f"输出目录: {OUTPUT_DIR}")
    print_info(f"可执行文件: {OUTPUT_DIR / APP_NAME}.exe")
    print_info(f"构建耗时: {elapsed_time:.2f} 秒")
    print()
    print_info("交付文件夹结构:")
    print_info(f"  {OUTPUT_DIR}/")
    print_info(f"  ├── {APP_NAME}.exe")
    print_info("  ├── data/")
    print_info("  ├── uploads/")
    print_info("  ├── logs/")
    print_info("  ├── keys/")
    print_info("  ├── backups/")
    print_info("  ├── resource/")
    print_info("  ├── static/")
    print_info("  └── README.txt")
    print()
    print_success("可以压缩 release/HousingRentalSystem 文件夹进行交付")
    
    return True


def clean_only():
    """仅执行清理操作"""
    print_header(f"清理 {APP_NAME} 构建产物")
    
    if clean_build_artifacts():
        print_success("清理完成")
        return True
    else:
        print_error("清理失败")
        return False


# ==================== 命令行入口 ====================

def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description=f"{APP_NAME} 一键构建脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python build_exe.py                    # 完整构建
    python build_exe.py --skip-frontend    # 跳过前端构建
    python build_exe.py --clean            # 仅清理构建产物
    python build_exe.py --no-clean         # 不清理直接构建
        """
    )
    
    parser.add_argument(
        '--skip-frontend',
        action='store_true',
        help='跳过前端构建步骤（适用于前端已构建的情况）'
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='仅清理构建产物，不执行构建'
    )
    
    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='不清理旧的构建产物，直接构建'
    )
    
    parser.add_argument(
        '--update',
        action='store_true',
        help='生成增量更新包（仅包含程序文件，不包含用户数据）'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'{APP_NAME} Builder v{APP_VERSION}'
    )
    
    args = parser.parse_args()
    
    # 执行相应操作
    if args.clean:
        success = clean_only()
    elif args.update:
        success = create_update_package()
    else:
        success = build_all(
            skip_frontend=args.skip_frontend,
            no_clean=args.no_clean
        )
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

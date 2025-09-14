#!/usr/bin/env python3
"""
Web界面启动脚本
一键启动前后端服务
"""
import os
import sys
import subprocess
import time
import webbrowser
import threading
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WebServerManager:
    def __init__(self):
        self.web_dir = Path(__file__).parent
        self.backend_dir = self.web_dir / "backend"
        self.frontend_dir = self.web_dir / "frontend"
        self.data_dir = self.web_dir / "data"
        
        self.backend_process = None
        self.frontend_process = None
        
    def check_dependencies(self):
        """检查依赖是否安装"""
        logger.info("检查依赖...")
        
        # 检查Python依赖
        try:
            import fastapi
            import uvicorn
            logger.info("✅ Python后端依赖已安装")
        except ImportError as e:
            logger.error(f"❌ Python依赖缺失: {e}")
            logger.info("请运行: pip install -r requirements-web.txt")
            return False
        
        # 检查Node.js
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js 已安装: {result.stdout.strip()}")
            else:
                raise FileNotFoundError()
        except FileNotFoundError:
            logger.error("❌ Node.js 未安装，请先安装 Node.js")
            return False
        
        # 检查前端依赖
        node_modules = self.frontend_dir / "node_modules"
        if not node_modules.exists():
            logger.info("前端依赖未安装，正在安装...")
            try:
                subprocess.run(['npm', 'install'], cwd=self.frontend_dir, check=True)
                logger.info("✅ 前端依赖安装完成")
            except subprocess.CalledProcessError:
                logger.error("❌ 前端依赖安装失败")
                return False
        else:
            logger.info("✅ 前端依赖已安装")
        
        return True
    
    def init_data_directory(self):
        """初始化数据目录"""
        logger.info("初始化数据目录...")
        
        # 确保数据目录存在
        self.data_dir.mkdir(exist_ok=True)
        
        # 初始化存储管理器（会自动创建必要文件）
        sys.path.insert(0, str(self.backend_dir))
        try:
            from storage import storage
            logger.info("✅ 数据目录初始化完成")
            
            # 显示数据目录信息
            configs_dir = self.data_dir / "configs"
            if configs_dir.exists():
                config_files = list(configs_dir.glob("*.ini"))
                logger.info(f"📁 配置文件: {len(config_files)} 个")
                for config_file in config_files:
                    logger.info(f"   - {config_file.name}")
            
        except Exception as e:
            logger.error(f"❌ 数据目录初始化失败: {e}")
            return False
        
        return True
    
    def start_backend(self, host="127.0.0.1", port=8080):
        """启动后端服务"""
        logger.info(f"启动后端服务: http://{host}:{port}")
        
        try:
            # 添加后端目录到Python路径
            env = os.environ.copy()
            python_path = str(self.backend_dir)
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = python_path
            
            # 启动FastAPI服务
            cmd = [
                sys.executable, "-m", "uvicorn", 
                "main:app", 
                "--host", host, 
                "--port", str(port),
                "--reload"
            ]
            
            self.backend_process = subprocess.Popen(
                cmd,
                cwd=self.backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 监控后端输出
            def monitor_backend():
                for line in iter(self.backend_process.stdout.readline, ''):
                    if line:
                        print(f"[后端] {line.rstrip()}")
                        if "Uvicorn running on" in line:
                            logger.info("✅ 后端服务启动成功")
            
            threading.Thread(target=monitor_backend, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 后端服务启动失败: {e}")
            return False
    
    def start_frontend(self, port=3000):
        """启动前端开发服务器"""
        logger.info(f"启动前端服务: http://localhost:{port}")
        
        try:
            # 检查前端是否已构建
            dist_dir = self.frontend_dir / "dist"
            if dist_dir.exists():
                logger.info("检测到前端构建文件，将通过后端服务提供静态文件")
                return True
            
            # 启动开发服务器
            env = os.environ.copy()
            env['VITE_API_BASE_URL'] = 'http://127.0.0.1:8080'
            
            self.frontend_process = subprocess.Popen(
                ['npm', 'run', 'dev', '--', '--port', str(port)],
                cwd=self.frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # 监控前端输出
            def monitor_frontend():
                for line in iter(self.frontend_process.stdout.readline, ''):
                    if line:
                        print(f"[前端] {line.rstrip()}")
                        if "Local:" in line and "localhost" in line:
                            logger.info("✅ 前端服务启动成功")
            
            threading.Thread(target=monitor_frontend, daemon=True).start()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 前端服务启动失败: {e}")
            return False
    
    def open_browser(self, url="http://localhost:3000", delay=3):
        """延迟打开浏览器"""
        def open_delayed():
            time.sleep(delay)
            try:
                webbrowser.open(url)
                logger.info(f"🌐 已打开浏览器: {url}")
            except Exception as e:
                logger.warning(f"无法自动打开浏览器: {e}")
                logger.info(f"请手动访问: {url}")
        
        threading.Thread(target=open_delayed, daemon=True).start()
    
    def start(self, auto_open_browser=True):
        """启动完整的Web服务"""
        logger.info("🚀 启动 Dify ChatFlow Batch Tool Web界面")
        logger.info("=" * 50)
        
        # 检查依赖
        if not self.check_dependencies():
            return False
        
        # 初始化数据目录
        if not self.init_data_directory():
            return False
        
        # 启动后端
        if not self.start_backend():
            return False
        
        # 等待后端启动
        time.sleep(2)
        
        # 启动前端
        if not self.start_frontend():
            return False
        
        # 打开浏览器
        if auto_open_browser:
            # 检查是否有构建文件，决定访问地址
            dist_dir = self.frontend_dir / "dist"
            if dist_dir.exists():
                self.open_browser("http://127.0.0.1:8080")
            else:
                self.open_browser("http://localhost:3000")
        
        logger.info("=" * 50)
        logger.info("🎉 Web服务启动完成！")
        logger.info("📖 API文档: http://127.0.0.1:8080/docs")
        logger.info("🛑 按 Ctrl+C 停止服务")
        logger.info("=" * 50)
        
        return True
    
    def stop(self):
        """停止所有服务"""
        logger.info("正在停止服务...")
        
        if self.backend_process:
            self.backend_process.terminate()
            logger.info("✅ 后端服务已停止")
        
        if self.frontend_process:
            self.frontend_process.terminate()
            logger.info("✅ 前端服务已停止")

def main():
    """主函数"""
    manager = WebServerManager()
    
    try:
        if manager.start():
            # 等待用户中断
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n收到停止信号...")
    except Exception as e:
        logger.error(f"启动失败: {e}")
    finally:
        manager.stop()

if __name__ == "__main__":
    main()
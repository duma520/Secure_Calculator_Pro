import sys
import json
import math
import re
import logging
import os
import yaml
import base64
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QTabWidget, QLabel, QMessageBox, QFileDialog,
                             QComboBox, QCheckBox, QGroupBox, QScrollArea, 
                             QSpinBox, QFrame, QSizePolicy, QDockWidget, QToolBar, QGridLayout)
from PySide6.QtCore import Qt, QTimer, QSettings, QThread, Signal, QSize, QRect, QByteArray
from PySide6.QtGui import (QFont, QTextCursor, QClipboard, QTextOption, 
                         QColor, QPalette, QFontMetrics, QResizeEvent, QIcon, QAction)

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('calculator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ==================== 项目信息元数据 ====================
class ProjectInfo:
    """项目信息元数据（集中管理所有项目相关信息）"""
    VERSION = "2.0"  # 版本号
    BUILD_DATE = "2026-08-20"  # 构建日期
    AUTHOR = "杜玛"  # 作者
    LICENSE = "GNU Affero General Public License v3.0"  # 许可证
    COPYRIGHT = "© 2024-2026 杜玛"  # 版权声明
    URL = "https://github.com/duma520/Secure_Calculator_Pro"  # 项目主页
    MAINTAINER_EMAIL = "不提供"  # 维护者邮箱
    NAME = "安全公式计算器"  # 程序名称
    DESCRIPTION = "安全公式计算器 Secure_Calculator_Pro 是一个功能强大且安全的数学计算工具，支持广泛的数学函数和表达式评估，适用于各种计算需求。"  # 描述
    
    # 字体配置
    DEFAULT_FONT = "Microsoft YaHei"  # 默认字体
    DEFAULT_RESULT_FONT_SIZE = 10  # 默认结果字体大小
    DEFAULT_INPUT_FONT_SIZE = 14  # 默认输入字体大小
    DEFAULT_PANEL_FONT_SIZE = 10  # 默认面板字体大小
    
    # 窗口配置
    DEFAULT_WINDOW_WIDTH = 900  # 默认窗口宽度
    DEFAULT_WINDOW_HEIGHT = 700  # 默认窗口高度
    
    # 计算配置
    DEFAULT_DECIMALS = "6"  # 默认小数位数
    DEFAULT_EXPR_LIMIT = 1000  # 默认表达式长度限制
    
    @classmethod
    def get_full_name(cls) -> str:
        """获取完整的程序名称（带版本）"""
        return f"{cls.NAME} v{cls.VERSION}"
    
    @classmethod
    def get_full_title(cls, username: str = None) -> str:
        """获取完整的窗口标题"""
        base = f"{cls.get_full_name()} 构建:{cls.BUILD_DATE}"
        if username:
            return f"{base} - 当前用户: {username}"
        return base
    
    @classmethod
    def get_about_text(cls) -> str:
        """获取关于信息文本（HTML格式）"""
        return f"""
        <h2>{cls.NAME} v{cls.VERSION}</h2>
        <p><b>版本:</b> {cls.VERSION}</p>
        <p><b>构建日期:</b> {cls.BUILD_DATE}</p>
        <p><b>作者:</b> {cls.AUTHOR}</p>
        <p><b>版权:</b> {cls.COPYRIGHT}</p>
        <p><b>许可证:</b> {cls.LICENSE}</p>
        <p><b>项目主页:</b> <a href='{cls.URL}' style='color: #0078D7;'>{cls.URL}</a></p>
        <p><b>描述:</b> {cls.DESCRIPTION}</p>
        <hr>
        <p><b>功能特点:</b></p>
        <ul>
            <li>支持复杂数学表达式计算</li>
            <li>支持变量定义和管理</li>
            <li>完整的历史记录功能</li>
            <li>多种主题和字体选择</li>
            <li>安全的表达式评估</li>
            <li>可定制的显示设置</li>
            <li>右侧可折叠控制面板</li>
            <li>输入历史导航</li>
            <li>支持异步计算，防止UI冻结</li>
            <li>自动保存计算结果和历史记录</li>
        </ul>
        <p><b>联系方式:</b> {cls.MAINTAINER_EMAIL}</p>
        """
    
    @classmethod
    def get_help_text(cls) -> str:
        """获取帮助信息文本"""
        return f"""安全公式计算器 v{cls.VERSION} 帮助:

基本运算: + - * / // % ** 
比较运算: == != > >= < <=
位运算: & | ^ ~ << >>
括号: ( )

数学函数:
abs, round, min, max, pow, sqrt, exp, log, log10, log2
factorial, ceil, floor, trunc, gcd, lcm

三角函数:
sin, cos, tan, asin, acos, atan, atan2
sinh, cosh, tanh, asinh, acosh, atanh
degrees, radians

常数: pi, e, tau, inf, nan

变量赋值:
a = 5  # 定义变量a
b = a * 2  # 使用变量

其他功能:
- 支持历史记录保存和导出
- 可定义和管理变量
- 可调整显示字体和大小
- 自动保存计算结果
- 右侧可折叠控制面板
- 多种主题选择
- 输入历史导航
- 变量和历史记录搜索
- 异步计算防止UI冻结

快捷键:
Enter - 计算当前表达式
Up/Down - 导航输入历史
Ctrl+C - 复制结果
Ctrl+S - 保存结果
Ctrl+P - 显示/隐藏控制面板

作者: {cls.AUTHOR}
版权: {cls.COPYRIGHT}
许可证: {cls.LICENSE}
项目主页: {cls.URL}
"""


class SafeEvaluator:
    """安全表达式评估器，采用防御性编程和严格输入验证"""
    def __init__(self):
        # 定义允许的数学函数和常量
        self.safe_dict = self._create_safe_dict()
        self.max_expr_length = ProjectInfo.DEFAULT_EXPR_LIMIT  # 最大表达式长度限制
        self.max_recursion_depth = 50  # 最大递归深度限制
    
    def _create_safe_dict(self) -> Dict[str, Any]:
        """创建安全的数学函数字典"""
        safe_dict = {
            # 基本数学运算
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'pow': pow,
            
            # 数学函数
            'sqrt': math.sqrt,
            'exp': math.exp,
            'log': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'factorial': math.factorial,
            
            # 三角函数
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'asin': math.asin,
            'acos': math.acos,
            'atan': math.atan,
            'atan2': math.atan2,
            'sinh': math.sinh,
            'cosh': math.cosh,
            'tanh': math.tanh,
            'asinh': math.asinh,
            'acosh': math.acosh,
            'atanh': math.atanh,
            
            # 角度转换
            'degrees': math.degrees,
            'radians': math.radians,
            
            # 常数
            'pi': math.pi,
            'e': math.e,
            'tau': math.tau,
            'inf': math.inf,
            'nan': math.nan,
            
            # 位运算
            'ceil': math.ceil,
            'floor': math.floor,
            'trunc': math.trunc,
            'gcd': math.gcd,
            'lcm': lambda a, b: abs(a*b) // math.gcd(a, b) if a and b else 0,
            
            # 禁用内置函数
            '__builtins__': None,
        }
        return safe_dict
    
    def evaluate(self, expr: str, variables: Optional[Dict[str, Any]] = None) -> Any:
        """安全评估数学表达式，包含全面的错误检查和防御性编程"""
        try:
            # 输入验证
            if not expr or not isinstance(expr, str):
                raise ValueError("表达式不能为空且必须是字符串")
                
            if len(expr) > self.max_expr_length:
                raise ValueError(f"表达式过长(>{self.max_expr_length}字符)")
            
            # 预处理表达式
            expr = self.sanitize_input(expr)
            
            # 检查表达式安全性
            if not self.is_safe_expression(expr):
                raise ValueError("表达式包含不安全字符")
            
            # 设置递归限制
            sys.setrecursionlimit(self.max_recursion_depth)
            
            # 合并变量字典
            eval_dict = self.safe_dict.copy()
            if variables:
                if not isinstance(variables, dict):
                    raise ValueError("变量必须是字典类型")
                eval_dict.update(variables)
            
            # 评估表达式
            result = eval(expr, {'__builtins__': None}, eval_dict)
            
            # 检查结果有效性
            if isinstance(result, (int, float, complex)):
                if math.isinf(result):
                    raise ValueError("计算结果超出数值范围")
                if math.isnan(result):
                    raise ValueError("计算结果不是数字")
            
            return result
        except RecursionError:
            raise ValueError("表达式递归深度过大")
        except MemoryError:
            raise ValueError("计算过程中内存不足")
        except Exception as e:
            logger.error(f"计算错误: {str(e)}", exc_info=True)
            raise ValueError(f"计算错误: {str(e)}")
        finally:
            # 恢复默认递归限制
            sys.setrecursionlimit(1000)
    
    def sanitize_input(self, expr: str) -> str:
        """清理输入表达式，防止注入攻击"""
        if not expr:
            return expr
            
        # 移除所有空白字符
        expr = ''.join(expr.split())
        # 替换中文括号和符号为英文
        expr = (expr.replace('（', '(').replace('）', ')')
                .replace('【', '[').replace('】', ']')
                .replace('「', '{').replace('」', '}'))
        return expr
    
    def is_safe_expression(self, expr: str) -> bool:
        """严格检查表达式是否只包含安全字符"""
        if not expr:
            return False
            
        # 允许的字符: 数字、基本运算符、括号、字母(用于函数名)、点、逗号
        safe_pattern = r'^[\d+\-*/%().,a-zA-Z!^&=<>|~_]+$'
        return re.match(safe_pattern, expr) is not None


class CalculationWorker(QThread):
    """异步计算工作线程，防止UI冻结"""
    calculation_done = Signal(object, bool)  # (result, is_success)
    
    def __init__(self, evaluator: SafeEvaluator, expr: str, variables: Dict[str, Any]):
        super().__init__()
        self.evaluator = evaluator
        self.expr = expr
        self.variables = variables
        self._is_running = True
    
    def run(self):
        """执行计算任务"""
        try:
            result = self.evaluator.evaluate(self.expr, self.variables)
            self.calculation_done.emit(result, True)
        except Exception as e:
            self.calculation_done.emit(str(e), False)
    
    def stop(self):
        """停止计算"""
        self._is_running = False
        self.terminate()
        self.wait()


class SettingsManager:
    """管理应用程序设置，使用多种文件格式存储不同类型的数据"""
    def __init__(self):
        # 初始化QSettings，使用注册表存储
        self.qsettings = QSettings("DumaSoft", "SecureCalculatorPro")
        
        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        
        # 结果文件路径 - 新增
        self.results_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results.json')
        
        # 设置文件路径映射
        self.settings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings')
        self.settings_files = {
            'app_settings': os.path.join(self.settings_dir, 'app_settings.ini'),
            'history': os.path.join(self.settings_dir, 'history.json'),
            'variables': os.path.join(self.settings_dir, 'variables.yaml'),
            'ui_state': os.path.join(self.settings_dir, 'ui_state.json')
        }
        
        # 确保配置文件存在
        self.ensure_config_file()
        
        # 兼容旧版本的设置迁移
        self.migrate_from_files()
    
    def ensure_config_file(self):
        """确保配置文件存在，不存在则创建"""
        if not os.path.exists(self.config_file):
            default_config = {
                "font_size": str(ProjectInfo.DEFAULT_RESULT_FONT_SIZE),
                "input_font_size": str(ProjectInfo.DEFAULT_INPUT_FONT_SIZE), 
                "panel_font_size": str(ProjectInfo.DEFAULT_PANEL_FONT_SIZE),
                "theme": "默认",
                "font": ProjectInfo.DEFAULT_FONT,
                "autosave": True,
                "always_on_top": False,
                "decimals": ProjectInfo.DEFAULT_DECIMALS,
                "force_decimal": False,
                "scientific": False,
                "expr_limit": ProjectInfo.DEFAULT_EXPR_LIMIT,
                "panel_visible": True
            }
            try:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4)
            except Exception as e:
                logger.error(f"创建默认配置文件失败: {str(e)}")

    def load_config(self):
        """从配置文件加载设置"""
        config = {}
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")
        return config

    def migrate_from_files(self):
        """从旧版文件存储迁移到注册表"""
        old_settings_dir = os.path.dirname(os.path.abspath(__file__))
        old_files = {
            'app_settings': os.path.join(old_settings_dir, 'app_settings.ini'),
            'history': os.path.join(old_settings_dir, 'history.json'),
            'variables': os.path.join(old_settings_dir, 'variables.yaml'),
            'ui_state': os.path.join(old_settings_dir, 'ui_state.json')
        }
        
        # 如果注册表中没有设置但文件中有设置，则迁移
        if not self.qsettings.contains("settings/migrated"):
            try:
                # 迁移app_settings
                if os.path.exists(old_files['app_settings']):
                    file_settings = QSettings(old_files['app_settings'], QSettings.Format.IniFormat)
                    for key in file_settings.allKeys():
                        self.qsettings.setValue(f"settings/{key}", file_settings.value(key))
                
                # 迁移历史记录
                if os.path.exists(old_files['history']):
                    with open(old_files['history'], 'r', encoding='utf-8') as f:
                        history = json.load(f)
                        self.qsettings.setValue("data/history", history)
                
                # 迁移变量
                if os.path.exists(old_files['variables']):
                    with open(old_files['variables'], 'r', encoding='utf-8') as f:
                        variables = yaml.safe_load(f) or {}
                        self.qsettings.setValue("data/variables", variables)
                
                # 迁移UI状态
                if os.path.exists(old_files['ui_state']):
                    with open(old_files['ui_state'], 'r', encoding='utf-8') as f:
                        ui_state = json.load(f)
                        if 'window_state' in ui_state and isinstance(ui_state['window_state'], str):
                            self.qsettings.setValue("ui/window_state", ui_state['window_state'])
                        if 'window_position' in ui_state:
                            self.qsettings.setValue("ui/window_position", ui_state['window_position'])
                        if 'geometry' in ui_state:
                            self.qsettings.setValue("ui/geometry", ui_state['geometry'])
                
                # 标记已完成迁移
                self.qsettings.setValue("settings/migrated", True)
                
                # 删除旧文件
                for file_path in old_files.values():
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
                        
            except Exception as e:
                logger.error(f"设置迁移失败: {str(e)}")

    def ensure_settings_dir(self):
        """确保设置目录存在"""
        if not os.path.exists(self.settings_dir):
            try:
                os.makedirs(self.settings_dir)
            except Exception as e:
                logger.error(f"创建设置目录失败: {str(e)}")
                self.settings_dir = os.getcwd()
    
    def save_app_settings(self, settings: dict):
        """保存应用程序设置到注册表"""
        try:
            for key, value in settings.items():
                # 将布尔值转换为字符串"true"/"false"
                if isinstance(value, bool):
                    self.qsettings.setValue(f"settings/{key}", "true" if value else "false")
                else:
                    self.qsettings.setValue(f"settings/{key}", str(value))
            self.qsettings.sync()
        except Exception as e:
            logger.error(f"保存应用程序设置失败: {str(e)}")

    
    def load_app_settings(self) -> dict:
        """从注册表加载应用程序设置"""
        settings = {}
        try:
            self.qsettings.beginGroup("settings")
            for key in self.qsettings.allKeys():
                settings[key] = self.qsettings.value(key)
            self.qsettings.endGroup()
        except Exception as e:
            logger.error(f"加载应用程序设置失败: {str(e)}")
        return settings
    
    def save_history(self, history: list):
        """保存历史记录到注册表"""
        try:
            self.qsettings.setValue("data/history", history)
            self.qsettings.sync()
        except Exception as e:
            logger.error(f"保存历史记录失败: {str(e)}")
    
    def load_history(self) -> list:
        """从注册表加载历史记录"""
        try:
            history = self.qsettings.value("data/history", [])
            # PySide6中QSettings.value可能返回QVariant，需要转换
            if history is None:
                return []
            return history
        except Exception as e:
            logger.error(f"加载历史记录失败: {str(e)}")
        return []

    def save_variables(self, variables: dict):
        """保存变量到注册表"""
        try:
            self.qsettings.setValue("data/variables", variables)
            self.qsettings.sync()
        except Exception as e:
            logger.error(f"保存变量失败: {str(e)}")
    
    def load_variables(self) -> dict:
        """从注册表加载变量"""
        try:
            variables = self.qsettings.value("data/variables", {})
            if variables is None:
                return {}
            return variables
        except Exception as e:
            logger.error(f"加载变量失败: {str(e)}")
        return {}
    
    def _convert_bytearray_to_json(self, state: dict) -> dict:
        """将QByteArray转换为可JSON序列化的格式"""
        converted = {}
        for key, value in state.items():
            if isinstance(value, QByteArray):
                converted[key] = bytes(value.toHex()).decode('ascii')
            else:
                converted[key] = value
        return converted


    def save_ui_state(self, state: dict):
        """保存UI状态到注册表"""
        try:
            # 将QByteArray转换为base64字符串
            if 'window_state' in state and isinstance(state['window_state'], QByteArray):
                self.qsettings.setValue("ui/window_state", state['window_state'].toBase64().data().decode('utf-8'))
            
            # 添加窗口位置信息
            if 'geometry' in state:
                self.qsettings.setValue("ui/geometry", state['geometry'])
                self.qsettings.setValue("ui/window_position", [state['geometry'][0], state['geometry'][1]])
            self.qsettings.sync()
        except Exception as e:
            logger.error(f"保存UI状态失败: {str(e)}")

    def load_ui_state(self) -> dict:
        """从注册表加载UI状态"""
        state = {}
        try:
            window_state = self.qsettings.value("ui/window_state")
            if window_state and isinstance(window_state, str):
                state['window_state'] = QByteArray.fromBase64(window_state.encode('utf-8'))
            
            geometry = self.qsettings.value("ui/geometry")
            if geometry:
                state['geometry'] = geometry
            
            window_position = self.qsettings.value("ui/window_position")
            if window_position:
                state['window_position'] = window_position
            
            return state
        except Exception as e:
            logger.error(f"加载UI状态失败: {str(e)}")
        return {}

    def save_results(self, results: list):
        """保存计算结果到文件"""
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到 {self.results_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")

    def load_results(self) -> list:
        """从文件加载计算结果"""
        try:
            if os.path.exists(self.results_file):
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                logger.info(f"从 {self.results_file} 加载了 {len(results)} 条结果")
                return results
        except Exception as e:
            logger.error(f"加载结果失败: {str(e)}")
        return []



class FormulaCalculator(QMainWindow):
    """主窗口类，实现所有计算器功能"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle(ProjectInfo.get_full_title())
        
        # 尝试设置窗口图标（如果存在）
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 初始化设置管理器
        self.settings_manager = SettingsManager()
        
        # 加载配置
        self.config = self.settings_manager.load_config()

        # 设置默认大小（如果设置加载失败则使用这个）
        self.default_width = ProjectInfo.DEFAULT_WINDOW_WIDTH
        self.default_height = ProjectInfo.DEFAULT_WINDOW_HEIGHT
        self.resize(self.default_width, self.default_height)
        
        # 居中显示（如果设置加载失败则使用这个）
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.default_width) // 2
        y = (screen_geometry.height() - self.default_height) // 2
        self.move(x, y)
        
        self.evaluator = SafeEvaluator()
        self.variables = {}  # 用户定义的变量
        self.history = []     # 计算历史记录
        self.saved_results = []  # 新增：保存的结果列表
        self.current_worker = None  # 当前计算线程
        self.window_size_before_dock = None  # 记录控制面板展开前的窗口大小
        
        # 初始化UI
        self.init_ui()
        
        # 加载历史记录、变量和保存的结果
        self.load_saved_results()  # 这个现在会同时加载结果和历史记录
        self.load_history()  # 这个现在只加载变量
        self.load_settings()
        
        # 自动保存计时器
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)  # 每30秒自动保存
        
        # 启动后自动聚焦输入框
        QTimer.singleShot(0, self.input_area.setFocus)
    
    def init_ui(self):
        """初始化用户界面"""
        # 检查配置文件是否存在，如果不存在则创建默认配置
        if not os.path.exists(self.settings_manager.config_file):
            self.create_default_config()

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        
        # 结果区
        self.init_result_area()
        
        # 输入区
        self.init_input_area()
        
        # 初始化右侧控制面板
        self.init_right_panel()
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪")
        
        # 应用主题和字体
        self.apply_theme()
        self.apply_font()
    
    def init_result_area(self):
        """初始化结果区域，增加字体大小调整功能"""
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout()
        
        # 结果显示区
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        # 修改这里：结果区域使用独立的字体对象
        self.result_font = QFont(ProjectInfo.DEFAULT_FONT, ProjectInfo.DEFAULT_RESULT_FONT_SIZE)
        self.result_area.setFont(self.result_font)
        self.result_area.setMinimumHeight(200)  # 合理的结果显示区域高度
        
        # 设置文本右对齐
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.result_area.document().setDefaultTextOption(text_option)
    
        # 新增：连接文本变化信号，实现实时保存
        self.result_area.textChanged.connect(self.on_result_changed)
        
        # 结果区工具栏
        result_toolbar = QHBoxLayout()
        
        # 复制按钮
        self.copy_btn = QPushButton("复制结果")
        self.copy_btn.clicked.connect(self.copy_results)
        self.copy_btn.setToolTip("将计算结果复制到剪贴板")
        
        # 清除按钮 - 修改提示文本
        self.clear_btn = QPushButton("清除结果")
        self.clear_btn.clicked.connect(self.clear_results)
        self.clear_btn.setToolTip("清除所有计算结果（不可恢复）")
        
        # 保存按钮
        self.save_btn = QPushButton("保存到文件")
        self.save_btn.clicked.connect(self.save_results_to_file)
        self.save_btn.setToolTip("将计算结果保存到文件")
        
        # 字体大小调整 - 支持更大字体，使用QSpinBox替代QComboBox
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 200)  # 字体大小范围8-200
        self.font_size_spin.setValue(ProjectInfo.DEFAULT_RESULT_FONT_SIZE)
        self.font_size_spin.setSuffix(" 像素")
        self.font_size_spin.valueChanged.connect(self.change_font_size)
        self.font_size_spin.setToolTip("调整结果字体大小(8-200像素)")
        
        # 输入区字体大小调整
        self.input_font_size_spin = QSpinBox()
        self.input_font_size_spin.setRange(8, 200)
        self.input_font_size_spin.setValue(ProjectInfo.DEFAULT_INPUT_FONT_SIZE)
        self.input_font_size_spin.setSuffix(" 像素")
        self.input_font_size_spin.valueChanged.connect(self.change_input_font_size)
        self.input_font_size_spin.setToolTip("调整输入区字体大小(8-200像素)")
        
        result_toolbar.addWidget(self.copy_btn)
        result_toolbar.addWidget(self.clear_btn)
        result_toolbar.addWidget(self.save_btn)
        result_toolbar.addStretch()
        result_toolbar.addWidget(QLabel("结果字体:"))
        result_toolbar.addWidget(self.font_size_spin)
        result_toolbar.addWidget(QLabel("输入字体:"))
        result_toolbar.addWidget(self.input_font_size_spin)
        
        result_layout.addLayout(result_toolbar)
        result_layout.addWidget(self.result_area)
        result_group.setLayout(result_layout)
        
        self.main_layout.addWidget(result_group)
    
    def init_right_panel(self):
        """初始化右侧控制面板，使用QDockWidget实现可停靠面板"""
        self.dock = QDockWidget("控制面板", self)
        self.dock.setObjectName("ControlPanelDockWidget")  # 设置objectName
        self.dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                              QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.dock.visibilityChanged.connect(self.handle_dock_visibility_changed)
        
        # 创建面板内容
        panel_widget = QWidget()
        panel_layout = QVBoxLayout()
        panel_widget.setLayout(panel_layout)
        
        # 控制面板字体设置
        self.panel_font_size_spin = QSpinBox()
        self.panel_font_size_spin.setRange(8, 200)
        self.panel_font_size_spin.setValue(ProjectInfo.DEFAULT_PANEL_FONT_SIZE)
        self.panel_font_size_spin.setSuffix(" 像素")
        self.panel_font_size_spin.valueChanged.connect(self.change_panel_font_size)
        
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("面板字体:"))
        font_layout.addWidget(self.panel_font_size_spin)
        font_layout.addStretch()
        panel_layout.addLayout(font_layout)
        
        # 标签控制面板
        self.tab_panel = QTabWidget()
        
        # 计算标签页
        self.init_calculation_tab()
        
        # 变量标签页
        self.init_variables_tab()
        
        # 历史记录标签页
        self.init_history_tab()
        
        # 设置标签页
        self.init_settings_tab()
        
        # 关于标签页
        self.init_about_tab()
        
        panel_layout.addWidget(self.tab_panel)
        panel_widget.setLayout(panel_layout)
        
        self.dock.setWidget(panel_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        
        # 添加显示/隐藏面板的工具栏按钮
        self.toggle_panel_action = self.dock.toggleViewAction()
        self.toggle_panel_action.setText("显示/隐藏控制面板")
        self.toggle_panel_action.setShortcut("Ctrl+P")
        self.toolbar = self.addToolBar("控制面板")
        self.toolbar.setObjectName("ControlPanelToolBar")  # 设置objectName
        self.toolbar.addAction(self.toggle_panel_action)
    
    def create_default_config(self):
        """创建默认配置文件"""
        default_config = {
            "settings/font_size": str(ProjectInfo.DEFAULT_RESULT_FONT_SIZE),
            "settings/input_font_size": str(ProjectInfo.DEFAULT_INPUT_FONT_SIZE),
            "settings/panel_font_size": str(ProjectInfo.DEFAULT_PANEL_FONT_SIZE),
            "settings/theme": "默认",
            "settings/font": ProjectInfo.DEFAULT_FONT,
            "settings/autosave": "true",
            "settings/always_on_top": "false",
            "settings/decimals": ProjectInfo.DEFAULT_DECIMALS,
            "settings/force_decimal": "false",
            "settings/scientific": "false",
            "settings/expr_limit": ProjectInfo.DEFAULT_EXPR_LIMIT,
            "settings/panel_visible": "true"
        }
        
        try:
            with open(self.settings_manager.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {str(e)}")


    def handle_dock_visibility_changed(self, visible):
        """处理控制面板可见性变化"""
        if visible:
            # 记录当前窗口大小
            self.window_size_before_dock = self.size()
        else:
            # 恢复之前记录的窗口大小
            if self.window_size_before_dock:
                self.resize(self.window_size_before_dock)
        
        # 自动保存设置
        self.save_settings()
    
    def init_calculation_tab(self):
        """初始化计算标签页，增加更多数学函数"""
        calc_tab = QWidget()
        self.tab_panel.addTab(calc_tab, "计算")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 常用函数按钮组
        func_group = QGroupBox("常用函数")
        func_group.setFlat(True)
        func_layout = QGridLayout()
        func_layout.setSpacing(3)
        
        # 数学函数按钮
        math_funcs = [
            "sqrt()", "sin()", "cos()", "tan()", 
            "log()", "log10()", "log2()", "exp()",
            "asin()", "acos()", "atan()", "atan2()",
            "sinh()", "cosh()", "tanh()", "asinh()",
            "acosh()", "atanh()", "degrees()", "radians()",
            "ceil()", "floor()", "trunc()", "round()",
            "abs()", "gcd()", "lcm()", "factorial()"
        ]
        
        for i, func in enumerate(math_funcs):
            btn = QPushButton(func)
            btn.setMaximumWidth(80)
            btn.clicked.connect(lambda _, f=func: self.insert_function(f))
            btn.setToolTip(f"插入 {func} 函数")
            func_layout.addWidget(btn, i//4, i%4)
        
        func_group.setLayout(func_layout)
        layout.addWidget(func_group)
        
        # 常数按钮组
        const_group = QGroupBox("常数")
        const_group.setFlat(True)
        const_layout = QHBoxLayout()
        const_layout.setSpacing(3)
        
        constants = ["π", "e", "τ", "inf", "nan"]
        for const in constants:
            btn = QPushButton(const)
            btn.setMaximumWidth(60)
            btn.clicked.connect(lambda _, c=const: self.insert_constant(c))
            btn.setToolTip(f"插入常数 {const}")
            const_layout.addWidget(btn)
        
        const_group.setLayout(const_layout)
        layout.addWidget(const_group)
        
        # 运算符按钮组
        op_group = QGroupBox("运算符")
        op_group.setFlat(True)
        op_layout = QGridLayout()
        op_layout.setSpacing(3)
        
        operators = [
            "+", "-", "*", "/", 
            "%", "^", "(", ")", 
            "=", "!=", "<", ">", 
            "<=", ">=", "!", "&", 
            "|", "~", "**", "//"
        ]
        
        for i, op in enumerate(operators):
            btn = QPushButton(op)
            btn.setMaximumWidth(40)
            btn.clicked.connect(lambda _, o=op: self.insert_operator(o))
            btn.setToolTip(f"插入运算符 {op}")
            op_layout.addWidget(btn, i//5, i%5)
        
        op_group.setLayout(op_layout)
        layout.addWidget(op_group)
        
        calc_tab.setLayout(layout)
    
    def init_variables_tab(self):
        """初始化变量标签页，增加变量搜索功能"""
        var_tab = QWidget()
        self.tab_panel.addTab(var_tab, "变量")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 变量管理区
        var_group = QGroupBox("变量管理")
        var_group.setFlat(True)
        var_layout = QVBoxLayout()
        var_layout.setSpacing(5)
        
        # 变量搜索框
        self.var_search_edit = QLineEdit()
        self.var_search_edit.setPlaceholderText("搜索变量...")
        self.var_search_edit.textChanged.connect(self.filter_variables)
        
        # 变量表格区域
        self.var_display = QTextEdit()
        self.var_display.setReadOnly(True)
        self.var_display.setFont(QFont(ProjectInfo.DEFAULT_FONT, ProjectInfo.DEFAULT_PANEL_FONT_SIZE))
        self.var_display.setMaximumHeight(200)
        self.update_var_display()
        
        # 变量操作按钮
        var_btn_layout = QHBoxLayout()
        var_btn_layout.setSpacing(3)
        
        self.var_name_edit = QLineEdit()
        self.var_name_edit.setPlaceholderText("变量名")
        self.var_name_edit.setToolTip("输入变量名(字母开头，可包含数字和下划线)")
        
        self.var_value_edit = QLineEdit()
        self.var_value_edit.setPlaceholderText("值")
        self.var_value_edit.setToolTip("输入变量值(数字或数学表达式)")
        
        add_var_btn = QPushButton("添加")
        add_var_btn.clicked.connect(self.add_variable)
        add_var_btn.setToolTip("添加新变量")
        
        del_var_btn = QPushButton("删除")
        del_var_btn.clicked.connect(self.delete_variable)
        del_var_btn.setToolTip("删除指定变量")
        
        clear_vars_btn = QPushButton("清除")
        clear_vars_btn.clicked.connect(self.clear_all_variables)
        clear_vars_btn.setToolTip("清除所有变量")
        
        var_btn_layout.addWidget(self.var_name_edit)
        var_btn_layout.addWidget(self.var_value_edit)
        var_btn_layout.addWidget(add_var_btn)
        var_btn_layout.addWidget(del_var_btn)
        var_btn_layout.addWidget(clear_vars_btn)
        
        var_layout.addWidget(self.var_search_edit)
        var_layout.addWidget(self.var_display)
        var_layout.addLayout(var_btn_layout)
        var_group.setLayout(var_layout)
        
        layout.addWidget(var_group)
        var_tab.setLayout(layout)
    
    def init_history_tab(self):
        """初始化历史记录标签页，增加搜索和过滤功能"""
        hist_tab = QWidget()
        self.tab_panel.addTab(hist_tab, "历史")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 历史记录管理
        hist_group = QGroupBox("历史记录")
        hist_group.setFlat(True)
        hist_layout = QVBoxLayout()
        hist_layout.setSpacing(5)
        
        # 历史搜索框
        self.hist_search_edit = QLineEdit()
        self.hist_search_edit.setPlaceholderText("搜索历史记录...")
        self.hist_search_edit.textChanged.connect(self.filter_history)
        
        # 历史记录显示
        self.history_list = QTextEdit()
        self.history_list.setReadOnly(True)
        self.history_list.setFont(QFont(ProjectInfo.DEFAULT_FONT, ProjectInfo.DEFAULT_PANEL_FONT_SIZE))
        self.history_list.setMaximumHeight(200)
        
        # 设置文本右对齐
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.history_list.document().setDefaultTextOption(text_option)
        
        # 历史操作按钮
        hist_btn_layout = QHBoxLayout()
        hist_btn_layout.setSpacing(3)
        
        load_hist_btn = QPushButton("加载")
        load_hist_btn.clicked.connect(self.load_history)
        load_hist_btn.setToolTip("从磁盘加载历史记录")
        
        clear_hist_btn = QPushButton("清除")
        clear_hist_btn.clicked.connect(self.clear_history)
        clear_hist_btn.setToolTip("清除所有历史记录")
        
        export_hist_btn = QPushButton("导出")
        export_hist_btn.clicked.connect(self.export_history)
        export_hist_btn.setToolTip("导出历史记录到文件")
        
        import_hist_btn = QPushButton("导入")
        import_hist_btn.clicked.connect(self.import_history)
        import_hist_btn.setToolTip("从文件导入历史记录")
        
        hist_btn_layout.addWidget(load_hist_btn)
        hist_btn_layout.addWidget(clear_hist_btn)
        hist_btn_layout.addWidget(export_hist_btn)
        hist_btn_layout.addWidget(import_hist_btn)
        
        hist_layout.addWidget(self.hist_search_edit)
        hist_layout.addWidget(self.history_list)
        hist_layout.addLayout(hist_btn_layout)
        hist_group.setLayout(hist_layout)
        
        layout.addWidget(hist_group)
        hist_tab.setLayout(layout)
    
    def init_settings_tab(self):
        """初始化设置标签页，增加更多自定义选项"""
        settings_tab = QWidget()
        self.tab_panel.addTab(settings_tab, "设置")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 外观设置
        appear_group = QGroupBox("外观设置")
        appear_group.setFlat(True)
        appear_layout = QVBoxLayout()
        appear_layout.setSpacing(5)
        
        # 主题选择
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "深色", "浅色", "蓝色", "绿色"])
        self.theme_combo.currentTextChanged.connect(self.apply_theme)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        # 字体选择
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体:"))
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Microsoft YaHei", "Consolas", "Courier New", "Arial", "Times New Roman"])
        self.font_combo.setCurrentText(ProjectInfo.DEFAULT_FONT)
        self.font_combo.currentTextChanged.connect(self.apply_font)
        font_layout.addWidget(self.font_combo)
        font_layout.addStretch()
        
        # 自动保存
        self.autosave_check = QCheckBox("启用自动保存")
        self.autosave_check.setChecked(True)
        self.autosave_check.setToolTip("自动保存计算历史和设置")
        
        # 窗口置顶
        self.always_on_top_check = QCheckBox("窗口置顶")
        self.always_on_top_check.setChecked(False)
        self.always_on_top_check.stateChanged.connect(self.toggle_always_on_top)
        
        appear_layout.addLayout(theme_layout)
        appear_layout.addLayout(font_layout)
        appear_layout.addWidget(self.autosave_check)
        appear_layout.addWidget(self.always_on_top_check)
        appear_group.setLayout(appear_layout)
        
        # 计算设置
        calc_group = QGroupBox("计算设置")
        calc_group.setFlat(True)
        calc_layout = QVBoxLayout()
        calc_layout.setSpacing(5)
        
        # 小数位数
        decimal_layout = QHBoxLayout()
        decimal_layout.addWidget(QLabel("小数位数:"))
        
        self.decimal_spin = QComboBox()
        self.decimal_spin.addItems(["0", "1", "2", "3", "4", "5", "6", "8", "10", "15"])
        self.decimal_spin.setCurrentText(ProjectInfo.DEFAULT_DECIMALS)
        self.decimal_spin.currentTextChanged.connect(lambda: self.save_settings())
        decimal_layout.addWidget(self.decimal_spin)
        decimal_layout.addStretch()
        
        # 强制显示小数位数
        self.force_decimal_check = QCheckBox("强制显示小数位数")
        self.force_decimal_check.setChecked(False)
        self.force_decimal_check.setToolTip("即使小数部分为零也显示指定位数")
        self.force_decimal_check.stateChanged.connect(lambda: self.save_settings())
        
        # 科学计数法
        self.sci_check = QCheckBox("使用科学计数法显示大数")
        self.sci_check.setChecked(False)
        self.sci_check.stateChanged.connect(lambda: self.save_settings())
        
        # 表达式长度限制
        expr_limit_layout = QHBoxLayout()
        expr_limit_layout.addWidget(QLabel("表达式长度限制:"))
        
        self.expr_limit_spin = QSpinBox()
        self.expr_limit_spin.setRange(100, 10000)
        self.expr_limit_spin.setValue(ProjectInfo.DEFAULT_EXPR_LIMIT)
        self.expr_limit_spin.valueChanged.connect(lambda: self.save_settings())
        expr_limit_layout.addWidget(self.expr_limit_spin)
        expr_limit_layout.addWidget(QLabel("字符"))
        expr_limit_layout.addStretch()
        
        calc_layout.addLayout(decimal_layout)
        calc_layout.addWidget(self.force_decimal_check)
        calc_layout.addWidget(self.sci_check)
        calc_layout.addLayout(expr_limit_layout)
        calc_group.setLayout(calc_layout)
        
        # 恢复默认设置
        reset_settings_btn = QPushButton("恢复默认设置")
        reset_settings_btn.clicked.connect(self.reset_settings)
        reset_settings_btn.setToolTip("恢复所有默认设置")
        
        layout.addWidget(appear_group)
        layout.addWidget(calc_group)
        layout.addWidget(reset_settings_btn)
        layout.addStretch()
        
        settings_tab.setLayout(layout)
    
    def init_about_tab(self):
        """初始化关于标签页"""
        about_tab = QWidget()
        self.tab_panel.addTab(about_tab, "关于")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 关于信息
        about_group = QGroupBox(f"关于{ProjectInfo.NAME}")
        about_group.setFlat(True)
        about_layout = QVBoxLayout()
        
        about_text = QLabel()
        about_text.setText(ProjectInfo.get_about_text())
        about_text.setWordWrap(True)
        about_text.setOpenExternalLinks(True)
        
        # 版本信息标签
        version_label = QLabel(f"<b>程序版本:</b> {ProjectInfo.VERSION} | <b>构建日期:</b> {ProjectInfo.BUILD_DATE}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 更新检查按钮
        check_update_btn = QPushButton("检查更新")
        check_update_btn.clicked.connect(self.check_for_updates)
        
        about_layout.addWidget(version_label)
        about_layout.addWidget(about_text)
        about_layout.addWidget(check_update_btn)
        about_group.setLayout(about_layout)
        
        layout.addWidget(about_group)
        layout.addStretch()
        
        about_tab.setLayout(layout)
    
    def init_input_area(self):
        """初始化输入区域，增加输入历史导航"""
        input_group = QGroupBox("输入")
        input_layout = QVBoxLayout()
        
        # 表达式输入框
        self.input_area = QLineEdit()
        self.input_area.setPlaceholderText("输入数学表达式，按Enter计算 (例如: 2+3*5, sin(pi/2), a=5)")
        self.input_area.returnPressed.connect(self.calculate)
        self.input_history = []  # 输入历史记录
        self.history_index = -1  # 当前历史记录索引
        
        # 输入辅助按钮
        input_btn_layout = QHBoxLayout()
        
        calc_btn = QPushButton("计算")
        calc_btn.clicked.connect(self.calculate)
        calc_btn.setToolTip("计算当前表达式")
        
        clear_input_btn = QPushButton("清空")
        clear_input_btn.clicked.connect(self.clear_input)
        clear_input_btn.setToolTip("清空输入框")
        
        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help)
        help_btn.setToolTip("显示帮助信息")
        
        prev_hist_btn = QPushButton("上一条")
        prev_hist_btn.clicked.connect(self.prev_history)
        prev_hist_btn.setToolTip("查看上一条输入历史")
        
        next_hist_btn = QPushButton("下一条")
        next_hist_btn.clicked.connect(self.next_history)
        next_hist_btn.setToolTip("查看下一条输入历史")
        
        input_btn_layout.addWidget(calc_btn)
        input_btn_layout.addWidget(clear_input_btn)
        input_btn_layout.addWidget(help_btn)
        input_btn_layout.addWidget(prev_hist_btn)
        input_btn_layout.addWidget(next_hist_btn)
        
        input_layout.addWidget(self.input_area)
        input_layout.addLayout(input_btn_layout)
        input_group.setLayout(input_layout)
        
        self.main_layout.addWidget(input_group)
    
    def resizeEvent(self, event: QResizeEvent):
        """重写resizeEvent以保持字体大小"""
        super().resizeEvent(event)
        # 确保窗口大小改变时字体不会重置
        self.change_font_size(self.font_size_spin.value())
        self.change_input_font_size(self.input_font_size_spin.value())
        self.change_panel_font_size(self.panel_font_size_spin.value())
    
    def calculate(self):
        """计算输入的公式，使用异步工作线程防止UI冻结"""
        expr = self.input_area.text().strip()
        if not expr:
            self.status_bar.showMessage("输入不能为空", 3000)
            return
        
        # 添加到输入历史
        if not self.input_history or expr != self.input_history[-1]:
            self.input_history.append(expr)
        self.history_index = -1
        
        # 取消之前的计算线程
        if self.current_worker and self.current_worker.isRunning():
            self.current_worker.stop()
        
        # 创建新的计算线程
        self.current_worker = CalculationWorker(self.evaluator, expr, self.variables)
        self.current_worker.calculation_done.connect(self.handle_calculation_result)
        self.current_worker.start()
        
        # 显示计算中状态
        self.status_bar.showMessage("计算中...")
    
    def handle_calculation_result(self, result, is_success):
        """处理计算结果"""
        expr = self.input_area.text().strip()
        
        if is_success:
            try:
                # 检查是否是变量赋值
                if '=' in expr:
                    var_parts = expr.split('=', 1)
                    var_name = var_parts[0].strip()
                    var_expr = var_parts[1].strip()
                    
                    if not var_name.isidentifier():
                        raise ValueError("无效的变量名")
                    
                    # 计算变量值
                    var_value = result
                    self.variables[var_name] = var_value
                    self.update_var_display()
                    
                    result_text = f"{var_name} = {self.format_number(var_value)}"
                    self.result_area.append(result_text)
                    self.history.append(result_text)
                else:
                    # 普通表达式计算
                    result_text = f"{expr} = {self.format_number(result)}"
                    self.result_area.append(result_text)
                    self.history.append(result_text)
                
                # 滚动到最后
                self.result_area.moveCursor(QTextCursor.MoveOperation.End)
                self.input_area.clear()
                self.status_bar.showMessage("计算成功", 3000)
                
                # 新增：自动保存当前结果
                if self.autosave_check.isChecked():
                    self.save_current_results()
                
            except ValueError as e:
                QMessageBox.warning(self, "计算错误", str(e))
                self.status_bar.showMessage("计算失败", 3000)
                logger.error(f"计算处理错误: {str(e)}", exc_info=True)
        else:
            QMessageBox.warning(self, "计算错误", str(result))
            self.status_bar.showMessage("计算失败", 3000)
            logger.error(f"计算错误: {str(result)}")
    
    def format_number(self, num: Union[int, float, complex]) -> str:
        """格式化数字显示，根据设置显示小数位数和科学计数法"""
        if isinstance(num, complex):
            return f"{num.real}{'+' if num.imag >= 0 else ''}{num.imag}j"
        
        decimal_places = int(self.decimal_spin.currentText())
        use_scientific = self.sci_check.isChecked()
        force_decimal = self.force_decimal_check.isChecked()
        
        if use_scientific and (abs(num) >= 1e6 or abs(num) <= 1e-6 and num != 0):
            return f"{num:.{decimal_places}e}"
        else:
            if decimal_places == 0:
                return f"{int(round(num))}"
            else:
                if force_decimal:
                    return f"{num:.{decimal_places}f}"
                else:
                    # 去除多余的零
                    formatted = f"{num:.{decimal_places}f}"
                    if '.' in formatted:
                        formatted = formatted.rstrip('0').rstrip('.') if '.' in formatted else formatted
                        if formatted.endswith('.'):
                            formatted = formatted[:-1]
                    return formatted
    
    def insert_function(self, func: str):
        """插入函数到输入框"""
        self.input_area.insert(func)
        self.input_area.setFocus()
    
    def insert_constant(self, const: str):
        """插入常数到输入框"""
        const_map = {
            "π": "pi",
            "e": "e",
            "τ": "tau",
            "inf": "math.inf",
            "nan": "math.nan"
        }
        self.input_area.insert(const_map.get(const, const))
        self.input_area.setFocus()
    
    def insert_operator(self, op: str):
        """插入运算符到输入框"""
        op_map = {
            "^": "**",
            "=": "=="
        }
        self.input_area.insert(op_map.get(op, op))
        self.input_area.setFocus()
    
    def add_variable(self):
        """添加变量，包含严格的输入验证"""
        var_name = self.var_name_edit.text().strip()
        var_value = self.var_value_edit.text().strip()
        
        if not var_name or not var_value:
            QMessageBox.warning(self, "错误", "变量名和值不能为空")
            return
        
        if not var_name.isidentifier():
            QMessageBox.warning(self, "错误", "无效的变量名(必须以字母开头，只能包含字母、数字和下划线)")
            return
        
        try:
            # 使用异步计算
            worker = CalculationWorker(self.evaluator, var_value, self.variables)
            worker.calculation_done.connect(lambda result, success: self.handle_add_variable_result(result, success, var_name))
            worker.start()
        except Exception as e:
            QMessageBox.warning(self, "错误", str(e))
            logger.error(f"添加变量错误: {str(e)}", exc_info=True)
    
    def handle_add_variable_result(self, result, success, var_name):
        """处理添加变量结果"""
        if success:
            self.variables[var_name] = result
            self.update_var_display()
            
            self.var_name_edit.clear()
            self.var_value_edit.clear()
            self.status_bar.showMessage(f"变量 {var_name} 添加成功", 3000)
        else:
            QMessageBox.warning(self, "错误", str(result))
    
    def delete_variable(self):
        """删除变量"""
        var_name = self.var_name_edit.text().strip()
        
        if not var_name:
            QMessageBox.warning(self, "错误", "请输入要删除的变量名")
            return
        
        if var_name in self.variables:
            del self.variables[var_name]
            self.update_var_display()
            self.var_name_edit.clear()
            self.status_bar.showMessage(f"变量 {var_name} 已删除", 3000)
        else:
            QMessageBox.warning(self, "错误", f"变量 {var_name} 不存在")
    
    def clear_all_variables(self):
        """清除所有变量"""
        reply = QMessageBox.question(
            self, '确认', 
            '确定要清除所有变量吗？此操作不可撤销！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.variables.clear()
            self.update_var_display()
            self.status_bar.showMessage("所有变量已清除", 3000)
    
    def filter_variables(self):
        """过滤显示变量"""
        search_text = self.var_search_edit.text().lower()
        
        if not self.variables:
            self.var_display.setPlainText("没有定义变量")
            return
        
        var_text = "当前定义的变量:\n"
        max_len = max(len(k) for k in self.variables.keys()) if self.variables else 0
        
        for name, value in sorted(self.variables.items()):
            if search_text in name.lower() or search_text in str(value).lower():
                var_text += f"{name.ljust(max_len)} = {value}\n"
        
        self.var_display.setPlainText(var_text if var_text.count('\n') > 1 else "没有匹配的变量")
    
    def filter_history(self):
        """过滤显示历史记录"""
        search_text = self.hist_search_edit.text().lower()
        
        if not self.history:
            self.history_list.setPlainText("没有历史记录")
            return
        
        filtered_history = [line for line in self.history if search_text in line.lower()]
        self.history_list.setPlainText("\n".join(filtered_history) if filtered_history else "没有匹配的历史记录")
    
    def update_var_display(self):
        """更新变量显示"""
        if not self.variables:
            self.var_display.setPlainText("没有定义变量")
            return
        
        var_text = "当前定义的变量:\n"
        max_len = max(len(k) for k in self.variables.keys()) if self.variables else 0
        
        for name, value in sorted(self.variables.items()):
            var_text += f"{name.ljust(max_len)} = {self.format_number(value)}\n"
        
        self.var_display.setPlainText(var_text)
    
    def copy_results(self):
        """复制结果到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_area.toPlainText())
        self.status_bar.showMessage("结果已复制到剪贴板", 3000)
    
    def clear_results(self):
        """清除结果区显示，并清空保存的结果和历史记录"""
        reply = QMessageBox.question(
            self, '确认清除', 
            '确定要清除所有结果吗？\n\n注意：清除后无法恢复！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            # 清空结果区显示
            self.result_area.clear()
            
            # 清空保存的结果列表
            self.saved_results = []
            
            # 清空历史记录列表
            self.history = []
            
            # 清空结果文件
            try:
                self.settings_manager.save_results([])
            except Exception as e:
                logger.error(f"清空结果文件失败: {str(e)}")
            
            # 清空历史记录文件（注册表）
            try:
                self.settings_manager.save_history([])
            except Exception as e:
                logger.error(f"清空历史记录失败: {str(e)}")
            
            # 更新历史记录显示
            self.history_list.clear()
            
            self.status_bar.showMessage("所有结果已清除", 3000)
            logger.info("所有结果已清除")



    
    def clear_input(self):
        """清除输入区"""
        self.input_area.clear()
        self.input_area.setFocus()
        self.status_bar.showMessage("输入已清除", 3000)
    
    def clear_history(self):
        """清除历史记录"""
        reply = QMessageBox.question(
            self, '确认', 
            '确定要清除所有历史记录吗？此操作不可撤销！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.history = []
            self.history_list.clear()
            self.save_history()
            self.status_bar.showMessage("历史记录已清除", 3000)
    
    def prev_history(self):
        """导航到上一条输入历史"""
        if not self.input_history:
            return
            
        if self.history_index < len(self.input_history) - 1:
            self.history_index += 1
            self.input_area.setText(self.input_history[-(self.history_index + 1)])
            self.input_area.setFocus()
    
    def next_history(self):
        """导航到下一条输入历史"""
        if not self.input_history or self.history_index < 0:
            return
            
        self.history_index -= 1
        if self.history_index >= 0:
            self.input_area.setText(self.input_history[-(self.history_index + 1)])
        else:
            self.input_area.clear()
        self.input_area.setFocus()
    
    def save_results_to_file(self):
        """保存结果到文件"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "", 
            "文本文件 (*.txt);;HTML 文件 (*.html);;所有文件 (*)")
        
        if not file_name:
            return
            
        try:
            if file_name.endswith('.html'):
                # 保存为HTML格式，保留格式
                html = self.result_area.document().toHtml()
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(html)
            else:
                # 默认保存为纯文本
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.result_area.toPlainText())
            
            self.status_bar.showMessage(f"结果已保存到 {file_name}", 5000)
            logger.info(f"结果已保存到 {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
            logger.error(f"保存结果失败: {str(e)}", exc_info=True)
    
    def export_history(self):
        """导出历史记录"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", "", 
            "文本文件 (*.txt);;JSON 文件 (*.json);;CSV 文件 (*.csv);;所有文件 (*)")
        
        if not file_name:
            return
            
        try:
            if file_name.endswith('.json'):
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, ensure_ascii=False, indent=2)
            elif file_name.endswith('.csv'):
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write("Timestamp,Expression\n")
                    for expr in self.history:
                        f.write(f"{datetime.now().isoformat()},{expr}\n")
            else:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write("\n".join(self.history))
            
            self.status_bar.showMessage(f"历史记录已导出到 {file_name}", 5000)
            logger.info(f"历史记录已导出到 {file_name}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
            logger.error(f"导出历史失败: {str(e)}", exc_info=True)
    
    def import_history(self):
        """导入历史记录"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "导入历史记录", "", 
            "文本文件 (*.txt);;JSON 文件 (*.json);;CSV 文件 (*.csv);;所有文件 (*)")
        
        if not file_name:
            return
            
        try:
            if file_name.endswith('.json'):
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            elif file_name.endswith('.csv'):
                with open(file_name, 'r', encoding='utf-8') as f:
                    # 跳过标题行
                    lines = f.readlines()[1:]
                    self.history = [line.split(',', 1)[1].strip() for line in lines]
            else:
                with open(file_name, 'r', encoding='utf-8') as f:
                    self.history = [line.strip() for line in f.readlines() if line.strip()]
            
            self.history_list.setPlainText("\n".join(self.history))
            self.save_history()
            self.status_bar.showMessage(f"历史记录已从 {file_name} 导入", 5000)
            logger.info(f"历史记录已从 {file_name} 导入")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
            logger.error(f"导入历史失败: {str(e)}", exc_info=True)
    
    def change_font_size(self, size: int):
        """改变结果区字体大小，不影响其他区域"""
        try:
            self.result_font.setPointSize(size)
            self.result_area.setFont(self.result_font)
            self.save_settings()
        except Exception as e:
            logger.error(f"更改结果字体大小错误: {str(e)}", exc_info=True)

    
    def change_input_font_size(self, size: int):
        """改变输入区字体大小"""
        try:
            font = QFont(self.input_area.font())
            font.setPointSize(size)
            self.input_area.setFont(font)
            self.save_settings()
        except Exception as e:
            logger.error(f"更改输入字体大小错误: {str(e)}", exc_info=True)
    
    def change_panel_font_size(self, size: int):
        """改变控制面板字体大小"""
        try:
            font = QFont()
            font.setPointSize(size)
            
            # 更新控制面板内所有控件的字体
            for widget in self.dock.findChildren(QWidget):
                widget.setFont(font)
            
            self.save_settings()
        except Exception as e:
            logger.error(f"更改控制面板字体大小错误: {str(e)}", exc_info=True)
    
    def apply_theme(self):
        """应用当前主题设置 - 使用更舒适的默认配色"""
        theme = self.theme_combo.currentText()
        
        try:
            if theme == "默认":
                # 使用系统默认主题，但稍微美化
                palette = QApplication.style().standardPalette()
                # 设置更舒适的背景色
                palette.setColor(QPalette.ColorRole.Window, QColor(248, 248, 248))
                palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
                palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
                palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                self.setPalette(palette)
            elif theme == "深色":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 35))
                palette.setColor(QPalette.ColorRole.WindowText, QColor(230, 230, 230))
                palette.setColor(QPalette.ColorRole.Base, QColor(20, 20, 25))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 40))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(40, 40, 45))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor(230, 230, 230))
                palette.setColor(QPalette.ColorRole.Text, QColor(230, 230, 230))
                palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 50))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor(230, 230, 230))
                palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 100, 100))
                palette.setColor(QPalette.ColorRole.Link, QColor(0, 160, 230))
                palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
                palette.setColor(QPalette.ColorRole.HighlightedText, QColor(230, 230, 230))
                self.setPalette(palette)
            elif theme == "浅色":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
                palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Base, QColor(250, 250, 250))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 245, 245))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Button, QColor(248, 248, 248))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.BrightText, QColor(200, 50, 50))
                palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 215))
                palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                self.setPalette(palette)
            elif theme == "蓝色":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, QColor(235, 242, 250))
                palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Base, QColor(248, 250, 252))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(240, 245, 250))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Button, QColor(230, 240, 250))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.BrightText, QColor(200, 50, 50))
                palette.setColor(QPalette.ColorRole.Link, QColor(0, 100, 200))
                palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 100, 200))
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                self.setPalette(palette)
            elif theme == "绿色":
                palette = QPalette()
                palette.setColor(QPalette.ColorRole.Window, QColor(240, 250, 240))
                palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Base, QColor(250, 255, 250))
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(245, 250, 245))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
                palette.setColor(QPalette.ColorRole.ToolTipText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Button, QColor(235, 245, 235))
                palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.BrightText, QColor(200, 50, 50))
                palette.setColor(QPalette.ColorRole.Link, QColor(0, 120, 0))
                palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 0))
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                self.setPalette(palette)
            
            self.save_settings()
        except Exception as e:
            logger.error(f"应用主题错误: {str(e)}", exc_info=True)
    
    def apply_font(self):
        """应用字体设置"""
        font_name = self.font_combo.currentText()
        try:
            font = QFont(font_name)
            font.setPointSize(self.font_size_spin.value())
            self.setFont(font)
            
            # 更新所有子控件的字体，除了结果区域
            for widget in self.findChildren(QWidget):
                if widget != self.result_area:  # 排除结果区域
                    widget.setFont(font)
            
            # 特殊处理输入区字体大小
            input_font = QFont(font)
            input_font.setPointSize(self.input_font_size_spin.value())
            self.input_area.setFont(input_font)
            
            self.save_settings()
        except Exception as e:
            logger.error(f"应用字体错误: {str(e)}", exc_info=True)
    
    def toggle_always_on_top(self, state):
        """切换窗口置顶状态"""
        try:
            # PySide6中设置窗口标志的方式略有不同
            if state:
                self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
            else:
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowStaysOnTopHint)
            self.show()
            self.save_settings()
        except Exception as e:
            logger.error(f"切换窗口置顶错误: {str(e)}", exc_info=True)
    
    def show_help(self):
        """显示帮助信息"""
        QMessageBox.information(self, "帮助", ProjectInfo.get_help_text())
    
    def check_for_updates(self):
        """检查更新"""
        # 这里可以添加实际的更新检查逻辑
        QMessageBox.information(self, "检查更新", f"{ProjectInfo.get_full_name()} 当前已是最新版本")
    
    def load_history(self):
        """加载历史记录 - 现在由 load_saved_results() 统一处理"""
        # 这个方法现在只负责加载变量，历史记录由 load_saved_results() 处理
        try:
            # 加载变量
            self.variables = self.settings_manager.load_variables()
            self.update_var_display()
        except Exception as e:
            logger.error(f"加载变量错误: {str(e)}", exc_info=True)
            self.variables = {}

    
    def save_history(self):
        """保存历史记录"""
        if not self.autosave_check.isChecked():
            return
            
        try:
            self.settings_manager.save_history(self.history)
            self.settings_manager.save_variables(self.variables)
        except Exception as e:
            logger.error(f"保存历史记录错误: {str(e)}", exc_info=True)
    

    def save_settings(self):
        """保存设置"""
        try:
            settings = {
                "font_size": str(self.font_size_spin.value()),
                "input_font_size": str(self.input_font_size_spin.value()),
                "panel_font_size": str(self.panel_font_size_spin.value()),
                "theme": self.theme_combo.currentText(),
                "font": self.font_combo.currentText(),
                "autosave": self.autosave_check.isChecked(),
                "always_on_top": self.always_on_top_check.isChecked(),
                "panel_visible": self.dock.isVisible(),
                "decimals": self.decimal_spin.currentText(),
                "force_decimal": self.force_decimal_check.isChecked(),
                "scientific": self.sci_check.isChecked(),
                "expr_limit": self.expr_limit_spin.value(),
            }
            
            # 保存到配置文件
            with open(self.settings_manager.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
                
            # 同时保存到QSettings保持兼容
            self.settings_manager.save_app_settings(settings)
            
            # 保存UI状态
            ui_state = {
                "geometry": [
                    int(self.geometry().x()), 
                    int(self.geometry().y()),
                    int(self.geometry().width()),
                    int(self.geometry().height())
                ],
                "window_state": self.saveState().toBase64().data().decode('utf-8')
            }
            self.settings_manager.save_ui_state(ui_state)
            
            logger.debug("设置已保存")
        except Exception as e:
            logger.error(f"保存设置错误: {str(e)}", exc_info=True)
    
    def load_settings(self):
        """加载设置"""
        try:
            # 优先使用配置文件中的设置
            settings = self.config
            
            # 如果配置文件没有设置，则使用QSettings
            if not settings:
                settings = self.settings_manager.load_app_settings()
            
            # 控制面板状态
            panel_visible = settings.get("panel_visible", True)
            self.dock.setVisible(panel_visible)
            
            # 结果区域字体设置（独立设置）
            result_font_size = int(settings.get("font_size", str(ProjectInfo.DEFAULT_RESULT_FONT_SIZE)))
            self.font_size_spin.setValue(result_font_size)
            self.result_font = QFont(ProjectInfo.DEFAULT_FONT, result_font_size)
            self.result_area.setFont(self.result_font)
            
            # 输入区字体设置
            input_font_size = int(settings.get("input_font_size", str(ProjectInfo.DEFAULT_INPUT_FONT_SIZE)))
            self.input_font_size_spin.setValue(input_font_size)
            input_font = QFont(self.input_area.font())
            input_font.setPointSize(input_font_size)
            self.input_area.setFont(input_font)
            
            # 面板字体设置
            panel_font_size = int(settings.get("panel_font_size", str(ProjectInfo.DEFAULT_PANEL_FONT_SIZE)))
            self.panel_font_size_spin.setValue(panel_font_size)
            panel_font = QFont()
            panel_font.setPointSize(panel_font_size)
            
            # 更新控制面板内所有控件的字体
            for widget in self.dock.findChildren(QWidget):
                widget.setFont(panel_font)
            
            # 主题设置
            theme = str(settings.get("theme", "默认"))
            self.theme_combo.setCurrentText(theme)
            self.apply_theme()
            
            # 全局字体设置（不影响结果区域）
            font = str(settings.get("font", ProjectInfo.DEFAULT_FONT))
            self.font_combo.setCurrentText(font)
            global_font = QFont(font)
            global_font.setPointSize(panel_font_size)
            
            # 设置全局字体，排除结果区域和输入区域（因为它们已有独立设置）
            for widget in self.findChildren(QWidget):
                if widget not in [self.result_area, self.input_area]:
                    widget.setFont(global_font)
            
            # 其他设置
            self.autosave_check.setChecked(bool(settings.get("autosave", True)))
            self.always_on_top_check.setChecked(bool(settings.get("always_on_top", False)))
            self.toggle_always_on_top(self.always_on_top_check.isChecked())
            self.decimal_spin.setCurrentText(str(settings.get("decimals", ProjectInfo.DEFAULT_DECIMALS)))
            self.force_decimal_check.setChecked(bool(settings.get("force_decimal", False)))
            self.sci_check.setChecked(bool(settings.get("scientific", False)))
            self.expr_limit_spin.setValue(int(settings.get("expr_limit", ProjectInfo.DEFAULT_EXPR_LIMIT)))
            self.evaluator.max_expr_length = self.expr_limit_spin.value()
            
            # 加载UI状态
            ui_state = self.settings_manager.load_ui_state()
            if ui_state:
                geometry = ui_state.get("geometry")
                if geometry:
                    try:
                        x, y, w, h = map(int, geometry)
                        self.setGeometry(QRect(x, y, w, h))
                    except (ValueError, TypeError) as e:
                        logger.warning(f"无效的geometry参数: {geometry}, 使用默认窗口大小")
                        self.resize(self.default_width, self.default_height)
                        screen_geometry = QApplication.primaryScreen().geometry()
                        x = (screen_geometry.width() - self.default_width) // 2
                        y = (screen_geometry.height() - self.default_height) // 2
                        self.move(x, y)
                
                window_state = ui_state.get("window_state")
                if window_state:
                    self.restoreState(window_state)
        except Exception as e:
            logger.error(f"加载设置错误: {str(e)}", exc_info=True)





    def reset_settings(self):
        """恢复默认设置"""
        reply = QMessageBox.question(
            self, '确认', 
            '确定要恢复所有默认设置吗？此操作不可撤销！',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # 删除所有设置文件
                for file_path in self.settings_manager.settings_files.values():
                    if os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
                
                # 重置内存中的设置（使用ProjectInfo中的默认值）
                self.font_size_spin.setValue(ProjectInfo.DEFAULT_RESULT_FONT_SIZE)
                self.input_font_size_spin.setValue(ProjectInfo.DEFAULT_INPUT_FONT_SIZE)
                self.panel_font_size_spin.setValue(ProjectInfo.DEFAULT_PANEL_FONT_SIZE)
                self.theme_combo.setCurrentText("默认")
                self.font_combo.setCurrentText(ProjectInfo.DEFAULT_FONT)
                self.autosave_check.setChecked(True)
                self.always_on_top_check.setChecked(False)
                self.decimal_spin.setCurrentText(ProjectInfo.DEFAULT_DECIMALS)
                self.force_decimal_check.setChecked(False)
                self.sci_check.setChecked(False)
                self.expr_limit_spin.setValue(ProjectInfo.DEFAULT_EXPR_LIMIT)
                self.evaluator.max_expr_length = ProjectInfo.DEFAULT_EXPR_LIMIT
                
                # 应用重置的设置
                self.change_font_size(ProjectInfo.DEFAULT_RESULT_FONT_SIZE)
                self.change_input_font_size(ProjectInfo.DEFAULT_INPUT_FONT_SIZE)
                self.change_panel_font_size(ProjectInfo.DEFAULT_PANEL_FONT_SIZE)
                self.apply_theme()
                self.apply_font()
                self.toggle_always_on_top(False)
                
                self.status_bar.showMessage("已恢复默认设置", 3000)
                logger.info("已恢复默认设置")
            except Exception as e:
                logger.error(f"恢复默认设置错误: {str(e)}", exc_info=True)
                self.status_bar.showMessage("恢复默认设置失败", 3000)
    
    def autosave(self):
        """自动保存"""
        if self.autosave_check.isChecked():
            self.save_history()
            self.save_settings()
            self.save_current_results()  # 新增：自动保存结果
            logger.debug("自动保存完成（包括结果）")

    
    def closeEvent(self, event):
        """关闭事件处理"""
        try:
            # 停止当前计算线程
            if self.current_worker and self.current_worker.isRunning():
                self.current_worker.stop()
            
            self.save_history()
            self.save_settings()
            self.save_current_results()  # 新增：关闭时保存结果
            logger.info("应用程序关闭，结果已保存")
            event.accept()
        except Exception as e:
            logger.error(f"关闭应用程序错误: {str(e)}", exc_info=True)
            event.accept()

    def load_saved_results(self):
        """加载保存的结果"""
        try:
            self.saved_results = self.settings_manager.load_results()
            
            # 同时加载历史记录（保持两者同步）
            self.history = self.settings_manager.load_history()
            
            # 优先显示保存的结果，如果为空则显示历史记录
            if self.saved_results:
                display_text = "\n".join(self.saved_results)
            elif self.history:
                display_text = "\n".join(self.history)
            else:
                display_text = ""
            
            # 将结果显示在结果区域
            self.result_area.setPlainText(display_text)
            self.result_area.moveCursor(QTextCursor.MoveOperation.End)
            
            # 更新历史记录显示
            self.history_list.setPlainText("\n".join(self.history))
            
            logger.info(f"加载了 {len(self.saved_results)} 条保存的结果和 {len(self.history)} 条历史记录")
        except Exception as e:
            logger.error(f"加载保存的结果错误: {str(e)}", exc_info=True)
            self.saved_results = []
            self.history = []



    def save_current_results(self):
        """保存当前结果到文件，并同步更新历史记录"""
        try:
            current_text = self.result_area.toPlainText()
            # 按行分割，过滤空行
            results = [line.strip() for line in current_text.split('\n') if line.strip()]
            
            # 更新保存的结果列表
            self.saved_results = results
            
            # 同时更新历史记录（保持两者一致）
            self.history = results.copy()
            
            # 保存到文件
            self.settings_manager.save_results(results)
            
            # 保存历史记录到注册表
            self.settings_manager.save_history(results)
            
            logger.debug(f"结果已实时保存，共 {len(results)} 条")
        except Exception as e:
            logger.error(f"保存当前结果错误: {str(e)}", exc_info=True)



    def on_result_changed(self):
        """处理结果区域内容变化，实现实时保存"""
        if self.autosave_check.isChecked():
            # 使用单次定时器，避免频繁保存
            QTimer.singleShot(1000, self.save_current_results)


if __name__ == "__main__":
    try:
        # 设置应用程序信息
        app = QApplication(sys.argv)
        app.setApplicationName(ProjectInfo.NAME)
        app.setApplicationVersion(ProjectInfo.VERSION)
        app.setOrganizationName("DumaSoft")
        app.setOrganizationDomain("dumasoft.com")
        
        # 创建并显示主窗口
        calculator = FormulaCalculator()
        calculator.show()
        
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"应用程序启动失败: {str(e)}", exc_info=True)
        QMessageBox.critical(None, "致命错误", f"应用程序启动失败: {str(e)}")
        sys.exit(1)
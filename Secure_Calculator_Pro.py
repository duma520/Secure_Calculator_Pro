import sys
import json
import math
import re
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QTabWidget, QLabel, QMessageBox, QFileDialog,
                             QComboBox, QCheckBox, QGroupBox, QScrollArea, 
                             QSpinBox, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QFont, QTextCursor, QClipboard, QTextOption, QColor, QPalette

class SafeEvaluator:
    """安全表达式评估器"""
    def __init__(self):
        # 定义允许的数学函数和常量
        self.safe_dict = {
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
    
    def evaluate(self, expr, variables=None):
        """安全评估数学表达式"""
        try:
            # 预处理表达式
            expr = self.sanitize_input(expr)
            
            # 检查表达式安全性
            if not self.is_safe_expression(expr):
                raise ValueError("表达式包含不安全字符")
                
            # 合并变量字典
            eval_dict = self.safe_dict.copy()
            if variables:
                eval_dict.update(variables)
            
            # 评估表达式
            return eval(expr, {'__builtins__': None}, eval_dict)
        except Exception as e:
            raise ValueError(f"计算错误: {str(e)}")
    
    def sanitize_input(self, expr):
        """清理输入表达式"""
        # 移除所有空白字符
        expr = ''.join(expr.split())
        # 替换中文括号和符号为英文
        expr = (expr.replace('（', '(').replace('）', ')'))
        return expr
    
    def is_safe_expression(self, expr):
        """检查表达式是否只包含安全字符"""
        # 允许的字符: 数字、基本运算符、括号、字母(用于函数名)、点、逗号
        safe_pattern = r'^[\d+\-*/%().,a-zA-Z!^&=<>|~]+$'
        return re.match(safe_pattern, expr) is not None

class FormulaCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"安全公式计算器 Pro Max v1.6.1 - 作者: 杜玛 (版权无限期所有)")
        self.resize(600, 700)
        self.evaluator = SafeEvaluator()
        self.variables = {}  # 用户定义的变量
        
        # 使用QSettings替代文件存储配置
        self.settings = QSettings("DumaSoft", "FormulaCalculatorProMax")
        
        # 初始化UI
        self.init_ui()
        
        # 加载历史记录和设置
        self.load_history()
        self.load_settings()
        
        # 自动保存计时器
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.autosave)
        self.autosave_timer.start(30000)  # 每30秒自动保存
        
        # 启动后自动聚焦输入框
        QTimer.singleShot(0, self.input_area.setFocus)
    
    def init_ui(self):
        """初始化用户界面"""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout()
        self.main_widget.setLayout(self.main_layout)
        
        # 结果区
        self.init_result_area()
        
        # 可折叠控制面板
        self.init_collapsible_panel()
        
        # 输入区
        self.init_input_area()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 应用主题
        self.apply_theme()
    
    def init_result_area(self):
        """初始化结果区域"""
        result_group = QGroupBox("计算结果")
        result_layout = QVBoxLayout()
        
        # 结果显示区
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setFont(QFont("Consolas", 10))
        self.result_area.setMinimumHeight(250)
        
        # 设置文本右对齐
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignRight)
        self.result_area.document().setDefaultTextOption(text_option)
        
        # 结果区工具栏
        result_toolbar = QHBoxLayout()
        
        # 复制按钮
        self.copy_btn = QPushButton("复制结果")
        self.copy_btn.clicked.connect(self.copy_results)
        
        # 清除按钮
        self.clear_btn = QPushButton("清除结果")
        self.clear_btn.clicked.connect(self.clear_results)
        
        # 保存按钮
        self.save_btn = QPushButton("保存到文件")
        self.save_btn.clicked.connect(self.save_results_to_file)
        
        # 字体大小调整
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems(["8", "10", "12", "14", "16", "18", "20"])
        self.font_size_combo.setCurrentText("10")
        self.font_size_combo.currentTextChanged.connect(self.change_font_size)
        
        result_toolbar.addWidget(self.copy_btn)
        result_toolbar.addWidget(self.clear_btn)
        result_toolbar.addWidget(self.save_btn)
        result_toolbar.addStretch()
        result_toolbar.addWidget(QLabel("字体大小:"))
        result_toolbar.addWidget(self.font_size_combo)
        
        result_layout.addLayout(result_toolbar)
        result_layout.addWidget(self.result_area)
        result_group.setLayout(result_layout)
        
        self.main_layout.addWidget(result_group)
    
    def init_collapsible_panel(self):
        """初始化可折叠控制面板"""
        # 折叠/展开按钮
        self.toggle_panel_btn = QPushButton("▲ 折叠控制面板")
        self.toggle_panel_btn.setCheckable(True)
        self.toggle_panel_btn.setChecked(True)
        self.toggle_panel_btn.clicked.connect(self.toggle_panel)
        self.main_layout.addWidget(self.toggle_panel_btn)
        
        # 控制面板框架
        self.panel_frame = QFrame()
        self.panel_frame.setFrameShape(QFrame.StyledPanel)
        self.panel_layout = QVBoxLayout()
        self.panel_frame.setLayout(self.panel_layout)
        self.main_layout.addWidget(self.panel_frame)
        
        # 标签控制面板
        self.tab_panel = QTabWidget()
        self.panel_layout.addWidget(self.tab_panel)
        
        # 计算标签页
        self.init_calculation_tab()
        
        # 变量标签页
        self.init_variables_tab()
        
        # 历史记录标签页
        self.init_history_tab()
        
        # 设置标签页
        self.init_settings_tab()
    
    def toggle_panel(self, checked):
        """切换控制面板的折叠状态"""
        if checked:
            self.panel_frame.show()
            self.toggle_panel_btn.setText("▲ 折叠控制面板")
        else:
            self.panel_frame.hide()
            self.toggle_panel_btn.setText("▼ 展开控制面板")
        
        # 保存面板状态
        self.settings.setValue("panel_expanded", checked)
    
    def init_calculation_tab(self):
        """初始化计算标签页"""
        calc_tab = QWidget()
        self.tab_panel.addTab(calc_tab, "计算")
        
        layout = QVBoxLayout()
        
        # 常用函数按钮组
        func_group = QGroupBox("常用函数")
        func_layout = QHBoxLayout()
        
        # 数学函数按钮
        math_funcs = ["sqrt()", "sin()", "cos()", "tan()", "log()", "exp()"]
        for func in math_funcs:
            btn = QPushButton(func)
            btn.clicked.connect(lambda _, f=func: self.insert_function(f))
            func_layout.addWidget(btn)
        
        func_group.setLayout(func_layout)
        layout.addWidget(func_group)
        
        # 常数按钮组
        const_group = QGroupBox("常数")
        const_layout = QHBoxLayout()
        
        constants = ["π", "e", "τ"]
        for const in constants:
            btn = QPushButton(const)
            btn.clicked.connect(lambda _, c=const: self.insert_constant(c))
            const_layout.addWidget(btn)
        
        const_group.setLayout(const_layout)
        layout.addWidget(const_group)
        
        # 运算符按钮组
        op_group = QGroupBox("运算符")
        op_layout = QHBoxLayout()
        
        operators = ["+", "-", "*", "/", "^", "(", ")", "="]
        for op in operators:
            btn = QPushButton(op)
            btn.clicked.connect(lambda _, o=op: self.insert_operator(o))
            op_layout.addWidget(btn)
        
        op_group.setLayout(op_layout)
        layout.addWidget(op_group)
        
        calc_tab.setLayout(layout)
    
    def init_variables_tab(self):
        """初始化变量标签页"""
        var_tab = QWidget()
        self.tab_panel.addTab(var_tab, "变量")
        
        layout = QVBoxLayout()
        
        # 变量管理区
        var_group = QGroupBox("变量管理")
        var_layout = QVBoxLayout()
        
        # 变量表格区域
        self.var_display = QTextEdit()
        self.var_display.setReadOnly(True)
        self.var_display.setFont(QFont("Consolas", 10))
        self.update_var_display()
        
        # 变量操作按钮
        var_btn_layout = QHBoxLayout()
        
        self.var_name_edit = QLineEdit()
        self.var_name_edit.setPlaceholderText("变量名")
        
        self.var_value_edit = QLineEdit()
        self.var_value_edit.setPlaceholderText("值")
        
        add_var_btn = QPushButton("添加变量")
        add_var_btn.clicked.connect(self.add_variable)
        
        del_var_btn = QPushButton("删除变量")
        del_var_btn.clicked.connect(self.delete_variable)
        
        var_btn_layout.addWidget(self.var_name_edit)
        var_btn_layout.addWidget(self.var_value_edit)
        var_btn_layout.addWidget(add_var_btn)
        var_btn_layout.addWidget(del_var_btn)
        
        var_layout.addWidget(self.var_display)
        var_layout.addLayout(var_btn_layout)
        var_group.setLayout(var_layout)
        
        layout.addWidget(var_group)
        var_tab.setLayout(layout)
    
    def init_history_tab(self):
        """初始化历史记录标签页"""
        hist_tab = QWidget()
        self.tab_panel.addTab(hist_tab, "历史")
        
        layout = QVBoxLayout()
        
        # 历史记录管理
        hist_group = QGroupBox("历史记录")
        hist_layout = QVBoxLayout()
        
        self.history_list = QTextEdit()
        self.history_list.setReadOnly(True)
        self.history_list.setFont(QFont("Consolas", 10))
        
        # 设置文本右对齐
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignRight)
        self.history_list.document().setDefaultTextOption(text_option)
        
        # 历史操作按钮
        hist_btn_layout = QHBoxLayout()
        
        load_hist_btn = QPushButton("加载历史")
        load_hist_btn.clicked.connect(self.load_history)
        
        clear_hist_btn = QPushButton("清除历史")
        clear_hist_btn.clicked.connect(self.clear_history)
        
        export_hist_btn = QPushButton("导出历史")
        export_hist_btn.clicked.connect(self.export_history)
        
        hist_btn_layout.addWidget(load_hist_btn)
        hist_btn_layout.addWidget(clear_hist_btn)
        hist_btn_layout.addWidget(export_hist_btn)
        
        hist_layout.addWidget(self.history_list)
        hist_layout.addLayout(hist_btn_layout)
        hist_group.setLayout(hist_layout)
        
        layout.addWidget(hist_group)
        hist_tab.setLayout(layout)
    
    def init_settings_tab(self):
        """初始化设置标签页"""
        settings_tab = QWidget()
        self.tab_panel.addTab(settings_tab, "设置")
        
        layout = QVBoxLayout()
        
        # 外观设置
        appear_group = QGroupBox("外观设置")
        appear_layout = QVBoxLayout()
        
        # 主题选择
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("主题:"))
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "深色", "浅色"])
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        
        # 字体选择
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("字体:"))
        
        self.font_combo = QComboBox()
        self.font_combo.addItems(["Consolas", "Courier New", "Arial", "Times New Roman"])
        self.font_combo.setCurrentText("Consolas")
        font_layout.addWidget(self.font_combo)
        font_layout.addStretch()
        
        # 自动保存
        self.autosave_check = QCheckBox("启用自动保存")
        self.autosave_check.setChecked(True)
        
        appear_layout.addLayout(theme_layout)
        appear_layout.addLayout(font_layout)
        appear_layout.addWidget(self.autosave_check)
        appear_group.setLayout(appear_layout)
        
        # 其他设置
        other_group = QGroupBox("其他设置")
        other_layout = QVBoxLayout()
        
        # 小数位数
        decimal_layout = QHBoxLayout()
        decimal_layout.addWidget(QLabel("小数位数:"))
        
        self.decimal_spin = QComboBox()
        self.decimal_spin.addItems(["0", "1", "2", "3", "4", "5", "6", "8", "10"])
        self.decimal_spin.setCurrentText("6")
        decimal_layout.addWidget(self.decimal_spin)
        decimal_layout.addStretch()
        
        # 科学计数法
        self.sci_check = QCheckBox("使用科学计数法显示大数")
        self.sci_check.setChecked(False)
        
        other_layout.addLayout(decimal_layout)
        other_layout.addWidget(self.sci_check)
        other_group.setLayout(other_layout)
        
        # 保存设置按钮
        save_settings_btn = QPushButton("保存设置")
        save_settings_btn.clicked.connect(self.save_settings)
        
        layout.addWidget(appear_group)
        layout.addWidget(other_group)
        layout.addWidget(save_settings_btn)
        layout.addStretch()
        
        settings_tab.setLayout(layout)
    
    def init_input_area(self):
        """初始化输入区域"""
        input_group = QGroupBox("输入")
        input_layout = QVBoxLayout()
        
        # 表达式输入框
        self.input_area = QLineEdit()
        self.input_area.setPlaceholderText("输入数学表达式，按Enter计算 (例如: 2+3*5, sin(pi/2), a=5)")
        self.input_area.returnPressed.connect(self.calculate)
        
        # 输入辅助按钮
        input_btn_layout = QHBoxLayout()
        
        calc_btn = QPushButton("计算")
        calc_btn.clicked.connect(self.calculate)
        
        clear_input_btn = QPushButton("清空输入")
        clear_input_btn.clicked.connect(self.clear_input)
        
        help_btn = QPushButton("帮助")
        help_btn.clicked.connect(self.show_help)
        
        input_btn_layout.addWidget(calc_btn)
        input_btn_layout.addWidget(clear_input_btn)
        input_btn_layout.addWidget(help_btn)
        
        input_layout.addWidget(self.input_area)
        input_layout.addLayout(input_btn_layout)
        input_group.setLayout(input_layout)
        
        self.main_layout.addWidget(input_group)
    
    def calculate(self):
        """计算输入的公式"""
        expr = self.input_area.text().strip()
        if not expr:
            self.statusBar().showMessage("输入不能为空", 3000)
            return
        
        try:
            # 检查是否是变量赋值
            if '=' in expr:
                var_parts = expr.split('=', 1)
                var_name = var_parts[0].strip()
                var_expr = var_parts[1].strip()
                
                if not var_name.isidentifier():
                    raise ValueError("无效的变量名")
                
                # 计算变量值
                var_value = self.evaluator.evaluate(var_expr, self.variables)
                self.variables[var_name] = var_value
                self.update_var_display()
                
                result_text = f"{var_name} = {var_value}"
                self.result_area.append(result_text)
                self.history.append(result_text)
            else:
                # 普通表达式计算
                result = self.evaluator.evaluate(expr, self.variables)
                result_text = f"{expr} = {result}"
                self.result_area.append(result_text)
                self.history.append(result_text)
            
            # 滚动到最后
            self.result_area.moveCursor(QTextCursor.End)
            self.input_area.clear()
            self.statusBar().showMessage("计算成功", 3000)
            
        except ValueError as e:
            QMessageBox.warning(self, "计算错误", str(e))
            self.statusBar().showMessage("计算失败", 3000)
    
    def insert_function(self, func):
        """插入函数到输入框"""
        self.input_area.insert(func)
        self.input_area.setFocus()
    
    def insert_constant(self, const):
        """插入常数到输入框"""
        const_map = {
            "π": "pi",
            "e": "e",
            "τ": "tau"
        }
        self.input_area.insert(const_map.get(const, const))
        self.input_area.setFocus()
    
    def insert_operator(self, op):
        """插入运算符到输入框"""
        op_map = {
            "^": "**",
            "=": "=="
        }
        self.input_area.insert(op_map.get(op, op))
        self.input_area.setFocus()
    
    def add_variable(self):
        """添加变量"""
        var_name = self.var_name_edit.text().strip()
        var_value = self.var_value_edit.text().strip()
        
        if not var_name or not var_value:
            QMessageBox.warning(self, "错误", "变量名和值不能为空")
            return
        
        if not var_name.isidentifier():
            QMessageBox.warning(self, "错误", "无效的变量名")
            return
        
        try:
            value = self.evaluator.evaluate(var_value, self.variables)
            self.variables[var_name] = value
            self.update_var_display()
            
            self.var_name_edit.clear()
            self.var_value_edit.clear()
            self.statusBar().showMessage(f"变量 {var_name} 添加成功", 3000)
        except ValueError as e:
            QMessageBox.warning(self, "错误", str(e))
    
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
            self.statusBar().showMessage(f"变量 {var_name} 已删除", 3000)
        else:
            QMessageBox.warning(self, "错误", f"变量 {var_name} 不存在")
    
    def update_var_display(self):
        """更新变量显示"""
        if not self.variables:
            self.var_display.setPlainText("没有定义变量")
            return
        
        var_text = "当前定义的变量:\n"
        max_len = max(len(k) for k in self.variables.keys()) if self.variables else 0
        
        for name, value in sorted(self.variables.items()):
            var_text += f"{name.ljust(max_len)} = {value}\n"
        
        self.var_display.setPlainText(var_text)
    
    def copy_results(self):
        """复制结果到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_area.toPlainText())
        self.statusBar().showMessage("结果已复制到剪贴板", 3000)
    
    def clear_results(self):
        """清除结果区"""
        self.result_area.clear()
        self.statusBar().showMessage("结果已清除", 3000)
    
    def clear_input(self):
        """清除输入区"""
        self.input_area.clear()
        self.input_area.setFocus()
        self.statusBar().showMessage("输入已清除", 3000)
    
    def clear_history(self):
        """清除历史记录"""
        self.history = []
        self.history_list.clear()
        self.save_history()
        self.statusBar().showMessage("历史记录已清除", 3000)
    
    def save_results_to_file(self):
        """保存结果到文件"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存结果", "", "文本文件 (*.txt);;所有文件 (*)")
        
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(self.result_area.toPlainText())
                self.statusBar().showMessage(f"结果已保存到 {file_name}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败: {str(e)}")
    
    def export_history(self):
        """导出历史记录"""
        file_name, _ = QFileDialog.getSaveFileName(
            self, "导出历史记录", "", "文本文件 (*.txt);;JSON 文件 (*.json);;所有文件 (*)")
        
        if file_name:
            try:
                if file_name.endswith('.json'):
                    with open(file_name, 'w', encoding='utf-8') as f:
                        json.dump(self.history, f, ensure_ascii=False, indent=2)
                else:
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write("\n".join(self.history))
                
                self.statusBar().showMessage(f"历史记录已导出到 {file_name}", 5000)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def change_font_size(self, size):
        """改变字体大小"""
        font = self.result_area.font()
        font.setPointSize(int(size))
        self.result_area.setFont(font)
        self.history_list.setFont(font)
        self.var_display.setFont(font)
        self.settings.setValue("font_size", size)
    
    def apply_theme(self):
        """应用当前主题设置"""
        theme = self.theme_combo.currentText()
        
        palette = self.palette()
        if theme == "深色":
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
        elif theme == "浅色":
            palette.setColor(QPalette.Window, Qt.white)
            palette.setColor(QPalette.WindowText, Qt.black)
            palette.setColor(QPalette.Base, QColor(240, 240, 240))
            palette.setColor(QPalette.AlternateBase, Qt.white)
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.black)
            palette.setColor(QPalette.Text, Qt.black)
            palette.setColor(QPalette.Button, QColor(240, 240, 240))
            palette.setColor(QPalette.ButtonText, Qt.black)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(0, 0, 255))
            palette.setColor(QPalette.Highlight, QColor(0, 0, 255))
            palette.setColor(QPalette.HighlightedText, Qt.white)
        else:  # 默认
            palette = QApplication.style().standardPalette()
        
        self.setPalette(palette)
        self.settings.setValue("theme", theme)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """安全公式计算器 Pro Max v1.5.0 帮助:

基本运算: + - * / // % ** 
比较运算: == != > >= < <=
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
- 可折叠控制面板
- 多种主题选择

作者: 杜玛
版权: 无限期所有
"""
        QMessageBox.information(self, "帮助", help_text)
    
    def load_history(self):
        """加载历史记录"""
        history = self.settings.value("history", [])
        if history:
            self.history = history
            self.result_area.setPlainText("\n".join(self.history))
            self.history_list.setPlainText("\n".join(self.history))
        else:
            self.history = []
    
    def save_history(self):
        """保存历史记录"""
        if not self.autosave_check.isChecked():
            return
            
        self.settings.setValue("history", self.history)
    
    def load_settings(self):
        """加载设置"""
        # 控制面板状态
        panel_expanded = self.settings.value("panel_expanded", True, type=bool)
        self.toggle_panel_btn.setChecked(panel_expanded)
        self.toggle_panel(panel_expanded)
        
        # 字体设置
        font_size = self.settings.value("font_size", "10")
        self.font_size_combo.setCurrentText(font_size)
        self.change_font_size(font_size)
        
        # 主题设置
        theme = self.settings.value("theme", "默认")
        self.theme_combo.setCurrentText(theme)
        self.apply_theme()
        
        # 其他设置
        self.autosave_check.setChecked(self.settings.value("autosave", True, type=bool))
        self.decimal_spin.setCurrentText(self.settings.value("decimals", "6"))
        self.sci_check.setChecked(self.settings.value("scientific", False, type=bool))
        self.font_combo.setCurrentText(self.settings.value("font", "Consolas"))
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("font_size", self.font_size_combo.currentText())
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("autosave", self.autosave_check.isChecked())
        self.settings.setValue("decimals", self.decimal_spin.currentText())
        self.settings.setValue("scientific", self.sci_check.isChecked())
        self.settings.setValue("font", self.font_combo.currentText())
        
        self.apply_theme()
        self.statusBar().showMessage("设置已保存", 3000)
    
    def autosave(self):
        """自动保存"""
        if self.autosave_check.isChecked():
            self.save_history()
    
    def closeEvent(self, event):
        """关闭事件处理"""
        self.save_history()
        self.save_settings()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("安全公式计算器 Pro Max")
    app.setApplicationVersion("1.6.1")
    app.setOrganizationName("DumaSoft")
    app.setOrganizationDomain("dumasoft.com")
    
    calculator = FormulaCalculator()
    calculator.show()
    sys.exit(app.exec_())

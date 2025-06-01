import sys
import os
import json
import subprocess
import tempfile
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog,
                             QListWidget, QListWidgetItem, QGroupBox, QTextEdit,
                             QMessageBox, QComboBox, QSplitter, QProgressBar, QAction)
from PyQt5.QtCore import Qt, QProcess, QTimer, QSettings, QStandardPaths
from PyQt5.QtGui import QIcon, QFont, QColor, QCloseEvent


class PyInstallerPackager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyInstaller 打包工具")
        self.setGeometry(100, 100, 900, 700)

        # 设置图标
        try:
            self.setWindowIcon(QIcon("icon.ico"))
        except:
            pass

        # 初始化配置路径
        self.config_path = self.get_config_path()
        self.auto_save_enabled = True

        # 创建主部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # 使用分割器
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter)

        # 创建顶部设置区域
        settings_group = QGroupBox("打包设置")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)

        # 创建日志区域
        log_group = QGroupBox("打包日志")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_output)

        splitter.addWidget(settings_group)
        splitter.addWidget(log_group)
        splitter.setSizes([400, 300])

        # 创建设置区域表单
        form_layout = QVBoxLayout()
        settings_layout.addLayout(form_layout)

        # 0. Python解释器路径
        python_layout = QHBoxLayout()
        form_layout.addLayout(python_layout)

        python_layout.addWidget(QLabel("Python解释器路径:"))
        self.python_path = QLineEdit()
        self.python_path.setPlaceholderText("默认使用系统PATH中的Python解释器")
        python_layout.addWidget(self.python_path, 3)

        self.python_browse_btn = QPushButton("浏览...")
        self.python_browse_btn.clicked.connect(self.select_python)
        python_layout.addWidget(self.python_browse_btn)


        # 1. 选择Python脚本
        script_layout = QHBoxLayout()
        form_layout.addLayout(script_layout)

        script_layout.addWidget(QLabel("Python脚本路径:"))
        self.script_path = QLineEdit()
        self.script_path.setPlaceholderText("请选择要打包的Python脚本")
        script_layout.addWidget(self.script_path, 3)

        self.script_browse_btn = QPushButton("浏览...")
        self.script_browse_btn.clicked.connect(self.select_script)
        script_layout.addWidget(self.script_browse_btn)

        # 2. 选择输出目录
        output_layout = QHBoxLayout()
        form_layout.addLayout(output_layout)

        output_layout.addWidget(QLabel("输出目录:"))
        self.output_path = QLineEdit()
        self.output_path.setPlaceholderText("请选择打包结果输出目录")
        output_layout.addWidget(self.output_path, 3)

        self.output_browse_btn = QPushButton("浏览...")
        self.output_browse_btn.clicked.connect(self.select_output)
        output_layout.addWidget(self.output_browse_btn)

        # 3. 单文件选项
        self.onefile_check = QCheckBox("打包为单文件 (--onefile)")
        self.onefile_check.setChecked(True)
        form_layout.addWidget(self.onefile_check)

        # 4. 窗口选项
        window_layout = QHBoxLayout()
        form_layout.addLayout(window_layout)

        window_layout.addWidget(QLabel("窗口模式:"))
        self.window_combo = QComboBox()
        self.window_combo.addItem("无控制台窗口 (--windowed)", "--windowed")
        self.window_combo.addItem("显示控制台窗口 (--console)", "--console")
        self.window_combo.addItem("默认模式 (不添加参数)", "")
        window_layout.addWidget(self.window_combo)

        # 5. 添加图标
        icon_layout = QHBoxLayout()
        form_layout.addLayout(icon_layout)

        icon_layout.addWidget(QLabel("应用程序图标:"))
        self.icon_path = QLineEdit()
        self.icon_path.setPlaceholderText("可选: 选择.ico图标文件")
        icon_layout.addWidget(self.icon_path, 3)

        self.icon_browse_btn = QPushButton("浏览...")
        self.icon_browse_btn.clicked.connect(self.select_icon)
        icon_layout.addWidget(self.icon_browse_btn)

        # 6. 添加数据文件
        data_layout = QHBoxLayout()
        form_layout.addLayout(data_layout)

        data_layout.addWidget(QLabel("添加数据文件/目录:"))
        self.data_path = QLineEdit()
        self.data_path.setPlaceholderText("格式: 源路径;目标路径 (如: images;images)")
        data_layout.addWidget(self.data_path, 2)

        self.data_add_btn = QPushButton("添加")
        self.data_add_btn.clicked.connect(self.add_data)
        data_layout.addWidget(self.data_add_btn)

        # 7. 添加依赖项
        hidden_layout = QHBoxLayout()
        form_layout.addLayout(hidden_layout)

        hidden_layout.addWidget(QLabel("添加隐藏依赖:"))
        self.hidden_import = QLineEdit()
        self.hidden_import.setPlaceholderText("输入模块名 (如: numpy,PyQt5.QtWebEngine)")
        hidden_layout.addWidget(self.hidden_import, 2)

        self.hidden_add_btn = QPushButton("添加")
        self.hidden_add_btn.clicked.connect(self.add_hidden)
        hidden_layout.addWidget(self.hidden_add_btn)

        # 8. 高级选项
        advanced_group = QGroupBox("高级选项")
        advanced_layout = QVBoxLayout()
        advanced_group.setLayout(advanced_layout)
        form_layout.addWidget(advanced_group)

        # 清理选项
        clean_layout = QHBoxLayout()
        advanced_layout.addLayout(clean_layout)

        self.clean_check = QCheckBox("清理打包临时文件 (--clean)")
        self.clean_check.setChecked(True)
        clean_layout.addWidget(self.clean_check)

        self.no_confirm_check = QCheckBox("不显示控制台确认 (--noconfirm)")
        self.no_confirm_check.setChecked(True)
        clean_layout.addWidget(self.no_confirm_check)

        # 自动保存配置
        self.auto_save_check = QCheckBox("自动保存配置")
        self.auto_save_check.setChecked(True)
        clean_layout.addWidget(self.auto_save_check)

        # 其他参数
        other_layout = QHBoxLayout()
        advanced_layout.addLayout(other_layout)

        other_layout.addWidget(QLabel("其他参数:"))
        self.extra_args = QLineEdit()
        self.extra_args.setPlaceholderText("输入额外的PyInstaller参数")
        other_layout.addWidget(self.extra_args)

        # 数据文件列表
        self.data_list = QListWidget()
        self.data_list.setMinimumHeight(100)
        form_layout.addWidget(QLabel("已添加数据文件:"))
        form_layout.addWidget(self.data_list)

        # 依赖项列表
        self.hidden_list = QListWidget()
        self.hidden_list.setMinimumHeight(100)
        form_layout.addWidget(QLabel("已添加隐藏依赖:"))
        form_layout.addWidget(self.hidden_list)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(5)
        form_layout.addWidget(self.progress_bar)

        # 按钮区域
        button_layout = QHBoxLayout()
        form_layout.addLayout(button_layout)

        self.package_btn = QPushButton("开始打包")
        self.package_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.package_btn.clicked.connect(self.start_packaging)
        self.package_btn.setMinimumHeight(40)
        button_layout.addWidget(self.package_btn)

        # 强制停止按钮
        self.force_stop_btn = QPushButton("强制停止")
        self.force_stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.force_stop_btn.clicked.connect(self.force_stop)
        self.force_stop_btn.setMinimumHeight(40)
        self.force_stop_btn.setEnabled(False)  # 初始不可用
        button_layout.addWidget(self.force_stop_btn)

        self.clear_btn = QPushButton("清空设置")
        self.clear_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.clear_btn.clicked.connect(self.clear_settings)
        self.clear_btn.setMinimumHeight(40)
        button_layout.addWidget(self.clear_btn)

        # 添加配置操作按钮
        config_layout = QHBoxLayout()
        form_layout.addLayout(config_layout)

        self.save_config_btn = QPushButton("保存配置")
        self.save_config_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.save_config_btn.clicked.connect(self.save_config)
        config_layout.addWidget(self.save_config_btn)

        self.load_config_btn = QPushButton("加载配置")
        self.load_config_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.load_config_btn.clicked.connect(self.load_config)
        config_layout.addWidget(self.load_config_btn)

        # 初始化进程
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.packaging_finished)
        self.process.stateChanged.connect(self.process_state_changed)

        # 进度更新计时器
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_value = 0

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 创建菜单栏
        self.create_menu()

        # 加载上次配置
        self.load_last_config()

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu('文件')

        save_config_action = QAction('保存配置', self)
        save_config_action.triggered.connect(self.save_config)
        file_menu.addAction(save_config_action)

        load_config_action = QAction('加载配置', self)
        load_config_action.triggered.connect(self.load_config)
        file_menu.addAction(load_config_action)

        export_config_action = QAction('导出配置', self)
        export_config_action.triggered.connect(self.export_config)
        file_menu.addAction(export_config_action)

        import_config_action = QAction('导入配置', self)
        import_config_action.triggered.connect(self.import_config)
        file_menu.addAction(import_config_action)

        file_menu.addSeparator()

        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 帮助菜单
        help_menu = menubar.addMenu('帮助')

        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def get_config_path(self):
        """获取配置文件路径"""
        # 获取应用数据目录
        app_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)

        # 如果目录不存在则创建
        if not os.path.exists(app_data_dir):
            os.makedirs(app_data_dir)

        # 返回配置文件路径
        return os.path.join(app_data_dir, "pyinstaller_packager_config.json")

    def closeEvent(self, event: QCloseEvent):
        """重写关闭事件，保存配置"""
        if self.auto_save_check.isChecked():
            self.save_config_to_file(self.config_path)
        event.accept()

    def load_last_config(self):
        """加载上次配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.apply_config(config)
                self.log_output.append(f"已加载上次配置: {self.config_path}")
                self.statusBar().showMessage("已加载上次配置")
            except Exception as e:
                self.log_output.append(f"加载配置失败: {str(e)}")

    def save_config(self):
        """保存当前配置"""
        try:
            self.save_config_to_file(self.config_path)
            self.log_output.append(f"配置已保存: {self.config_path}")
            self.statusBar().showMessage("配置已保存")
            QMessageBox.information(self, "保存成功", "当前配置已成功保存！")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存配置时出错: {str(e)}")

    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.apply_config(config)
                self.log_output.append(f"配置已加载: {self.config_path}")
                self.statusBar().showMessage("配置已加载")
                QMessageBox.information(self, "加载成功", "配置已成功加载！")
            else:
                QMessageBox.warning(self, "配置不存在", "找不到配置文件，请先保存配置")
        except Exception as e:
            QMessageBox.critical(self, "加载失败", f"加载配置时出错: {str(e)}")

    def export_config(self):
        """导出配置到指定文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path:
            try:
                if not file_path.endswith('.json'):
                    file_path += '.json'
                self.save_config_to_file(file_path)
                self.log_output.append(f"配置已导出: {file_path}")
                self.statusBar().showMessage("配置已导出")
                QMessageBox.information(self, "导出成功", f"配置已成功导出到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出配置时出错: {str(e)}")

    def import_config(self):
        """从文件导入配置"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json);;所有文件 (*.*)"
        )
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.apply_config(config)
                self.log_output.append(f"配置已导入: {file_path}")
                self.statusBar().showMessage("配置已导入")
                QMessageBox.information(self, "导入成功", "配置已成功导入！")
            except Exception as e:
                QMessageBox.critical(self, "导入失败", f"导入配置时出错: {str(e)}")

    def save_config_to_file(self, file_path):
        """保存配置到指定文件"""
        config = self.get_current_config()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def get_current_config(self):
        """获取当前配置"""
        config = {
            "python_path": self.python_path.text(),
            "script_path": self.script_path.text(),
            "output_path": self.output_path.text(),
            "icon_path": self.icon_path.text(),
            "onefile": self.onefile_check.isChecked(),
            "window_mode": self.window_combo.currentIndex(),
            "clean": self.clean_check.isChecked(),
            "no_confirm": self.no_confirm_check.isChecked(),
            "auto_save": self.auto_save_check.isChecked(),
            "extra_args": self.extra_args.text(),
            "data_files": [],
            "hidden_imports": []
        }

        # 保存数据文件列表
        for i in range(self.data_list.count()):
            config["data_files"].append(self.data_list.item(i).text())

        # 保存隐藏依赖列表
        for i in range(self.hidden_list.count()):
            config["hidden_imports"].append(self.hidden_list.item(i).text())

        return config

    def apply_config(self, config):
        """应用配置到UI"""
        # 恢复基本设置
        self.python_path.setText(config.get("python_path", ""))
        self.script_path.setText(config.get("script_path", ""))
        self.output_path.setText(config.get("output_path", ""))
        self.icon_path.setText(config.get("icon_path", ""))
        self.onefile_check.setChecked(config.get("onefile", True))

        # 恢复窗口模式
        window_index = config.get("window_mode", 0)
        if window_index < self.window_combo.count():
            self.window_combo.setCurrentIndex(window_index)

        # 恢复高级选项
        self.clean_check.setChecked(config.get("clean", True))
        self.no_confirm_check.setChecked(config.get("no_confirm", True))
        self.auto_save_check.setChecked(config.get("auto_save", True))
        self.extra_args.setText(config.get("extra_args", ""))

        # 恢复数据文件列表
        self.data_list.clear()
        for data in config.get("data_files", []):
            self.data_list.addItem(data)

        # 恢复隐藏依赖列表
        self.hidden_list.clear()
        for module in config.get("hidden_imports", []):
            self.hidden_list.addItem(module)

    def select_script(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Python脚本", "", "Python文件 (*.py);;所有文件 (*.*)"
        )
        if file_path:
            self.script_path.setText(file_path)
            # 自动设置输出目录
            if not self.output_path.text():
                output_dir = os.path.dirname(file_path)
                self.output_path.setText(os.path.join(output_dir, "dist"))

    def select_output(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择输出目录"
        )
        if dir_path:
            self.output_path.setText(dir_path)

    def select_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件", "", "图标文件 (*.ico);;所有文件 (*.*)"
        )
        if file_path:
            self.icon_path.setText(file_path)

    def add_data(self):
        data = self.data_path.text().strip()
        if not data:
            QMessageBox.warning(self, "输入错误", "请输入数据文件路径")
            return

        if ";" not in data:
            # 自动添加目标路径
            if os.path.isdir(data):
                target = os.path.basename(data)
            else:
                target = os.path.dirname(data)
            data = f"{data};{target}"

        self.data_list.addItem(data)
        self.data_path.clear()

    def add_hidden(self):
        modules = self.hidden_import.text().strip()
        if not modules:
            QMessageBox.warning(self, "输入错误", "请输入依赖模块名称")
            return

        # 支持逗号分隔的多个模块
        for module in modules.split(","):
            module = module.strip()
            if module:
                self.hidden_list.addItem(module)

        self.hidden_import.clear()

    def clear_settings(self):
        # 清除所有设置
        self.script_path.clear()
        self.output_path.clear()
        self.icon_path.clear()
        self.data_list.clear()
        self.hidden_list.clear()
        self.onefile_check.setChecked(True)
        self.window_combo.setCurrentIndex(0)
        self.clean_check.setChecked(True)
        self.no_confirm_check.setChecked(True)
        self.auto_save_check.setChecked(True)
        self.extra_args.clear()
        self.log_output.clear()
        self.progress_bar.reset()
        self.statusBar().showMessage("设置已清空")

    def build_command(self):
        """构建PyInstaller命令"""
        script_path = self.script_path.text().strip()
        if not script_path:
            QMessageBox.critical(self, "错误", "请选择要打包的Python脚本")
            return None

        if not os.path.exists(script_path):
            QMessageBox.critical(self, "错误", "Python脚本不存在")
            return None

        output_dir = self.output_path.text().strip()
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(script_path), "dist")
            self.output_path.setText(output_dir)

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 基本命令
        cmd = ["pyinstaller"]

        # 单文件选项
        if self.onefile_check.isChecked():
            cmd.append("--onefile")

        # 窗口选项
        window_mode = self.window_combo.currentData()
        if window_mode:
            cmd.append(window_mode)

        # 添加图标
        icon_path = self.icon_path.text().strip()
        if icon_path and os.path.exists(icon_path):
            # 处理包含空格的路径
            if " " in icon_path:
                icon_path = f'"{icon_path}"'
            cmd.extend(["--icon", icon_path])

        # 添加数据文件
        for i in range(self.data_list.count()):
            data_item = self.data_list.item(i).text()
            cmd.extend(["--add-data", data_item])

        # 添加隐藏依赖
        for i in range(self.hidden_list.count()):
            module = self.hidden_list.item(i).text()
            cmd.extend(["--hidden-import", module])

        # 清理选项
        if self.clean_check.isChecked():
            cmd.append("--clean")

        if self.no_confirm_check.isChecked():
            cmd.append("--noconfirm")

        # 其他参数
        extra_args = self.extra_args.text().strip()
        if extra_args:
            cmd.extend(extra_args.split())

        # 添加输出目录和工作目录
        cmd.extend(["--distpath", output_dir])
        cmd.append(script_path)

        return cmd

    def start_packaging(self):
        cmd = self.build_command()
        if not cmd:
            return

        # 使用完整路径执行 PyInstaller
        # 获取Python解释器路径，如果用户没有设置，则使用字符串"python"（希望系统PATH中有）
        # 尝试查找系统 PyInstaller
        python_interpreter = self.python_path.text().strip()
        if python_interpreter and not self.validate_python_path(python_interpreter):
            QMessageBox.critical(self, "错误", "指定的Python解释器路径无效")
            return None

        # if not python_interpreter.endswith("python") and not python_interpreter.endswith("python3"):
        #
        #     pyinstaller_paths = [
        #         os.path.join(os.path.dirname(sys.executable), "Scripts", "python.exe"),
        #         os.path.join(os.path.dirname(sys.executable), "python.exe"),
        #         r"C:\Python38\Scripts\pyinstaller.exe",  # 常见路径
        #         r"C:\Program Files\Python38\Scripts\pyinstaller.exe"
        #     ]
        #
        #     found = False
        #     for path in pyinstaller_paths:
        #         if os.path.exists(path):
        #             python_interpreter = path
        #             found = True
        #             break
        #
        #     if not found:
        #         self.log_output.append("错误: 未找到 pyinstaller.exe")
        #         self.log_output.append("请确保 PyInstaller 已安装")
        #         return

        cmd = [python_interpreter, "-m", "PyInstaller"] + cmd[1:]

        self.log_output.clear()
        self.log_output.append(f"python_interpreter: {python_interpreter}")
        self.log_output.append("开始打包...")
        self.log_output.append(f"执行命令: {' '.join(cmd)}")
        self.statusBar().showMessage("打包中...")
        self.package_btn.setEnabled(False)
        self.force_stop_btn.setEnabled(True)

        # 重置进度条
        self.progress_value = 0
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("正在启动打包进程...")
        self.progress_timer.start(100)  # 每100毫秒更新一次进度

        # 设置工作目录为脚本所在目录
        work_dir = os.path.dirname(self.script_path.text())

        # 启动进程
        try:
            self.process.setWorkingDirectory(work_dir)
            self.process.start(cmd[0], cmd[1:])

            if not self.process.waitForStarted(5000):  # 5秒超时
                self.log_output.append("进程启动超时！")
                self.log_output.append(f"请检查 PyInstaller 是否安装: pip install pyinstaller")
                self.packaging_finished(-1, QProcess.CrashExit)
        except Exception as e:
            self.log_output.append(f"启动进程失败: {str(e)}")
            self.packaging_finished(-1, QProcess.CrashExit)

    def force_stop(self):
        """强制停止打包进程"""
        if self.process.state() == QProcess.Running:
            self.log_output.append("<font color='red'>用户请求强制停止打包进程...</font>")
            self.log_output.append("<font color='red'>正在终止打包进程...</font>")
            self.statusBar().showMessage("正在强制停止...")

            # 尝试优雅终止
            self.process.terminate()

            # 设置超时，如果5秒内未终止则强制杀死
            if not self.process.waitForFinished(5000):
                self.log_output.append("<font color='red'>进程未响应，强制杀死...</font>")
                self.process.kill()

            self.log_output.append("<font color='red'>打包进程已强制终止</font>")
            self.statusBar().showMessage("打包已取消")

            # 清理临时文件
            self.cleanup_after_stop()

            # 重置UI状态
            self.package_btn.setEnabled(True)
            self.force_stop_btn.setEnabled(False)
            self.progress_timer.stop()
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("已取消")

    def cleanup_after_stop(self):
        """强制停止后清理临时文件"""
        script_path = self.script_path.text().strip()
        if not script_path:
            return

        script_name = os.path.splitext(os.path.basename(script_path))[0]
        build_dir = os.path.join(os.path.dirname(script_path), "build", script_name)

        # 尝试删除build目录
        try:
            if os.path.exists(build_dir):
                self.log_output.append(f"正在清理临时目录: {build_dir}")
                subprocess.run(f'rmdir /s /q "{build_dir}"', shell=True, check=True)
        except Exception as e:
            self.log_output.append(f"清理临时目录失败: {str(e)}")

    def update_progress(self):
        """更新进度条显示"""
        if self.process.state() == QProcess.Running:
            # 简单的进度模拟
            if self.progress_value < 95:
                self.progress_value += 1
                self.progress_bar.setValue(self.progress_value)

                # 更新进度文本
                if self.progress_value < 30:
                    self.progress_bar.setFormat("正在收集依赖...")
                elif self.progress_value < 60:
                    self.progress_bar.setFormat("正在编译二进制...")
                else:
                    self.progress_bar.setFormat("正在生成可执行文件...")

    def process_state_changed(self, state):
        """处理进程状态变化"""
        if state == QProcess.NotRunning:
            self.progress_timer.stop()

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        self.log_output.append(stdout)

        # 根据输出更新进度
        if "INFO: Analyzing" in stdout:
            self.progress_bar.setFormat("分析依赖中...")
        elif "INFO: Building" in stdout:
            self.progress_bar.setFormat("构建二进制中...")
        elif "INFO: Appending" in stdout:
            self.progress_bar.setFormat("添加依赖中...")

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="ignore")
        self.log_output.append(f"<font color='red'>{stderr}</font>")

    def packaging_finished(self, exit_code, exit_status):
        self.package_btn.setEnabled(True)
        self.force_stop_btn.setEnabled(False)
        self.progress_timer.stop()

        if exit_code == 0:
            self.log_output.append("\n打包成功完成!")
            self.statusBar().showMessage("打包成功")
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("完成")

            # 打开输出目录
            output_dir = self.output_path.text()
            if os.path.exists(output_dir):
                self.log_output.append(f"\n输出目录: {output_dir}")

                # 添加打开文件夹按钮
                self.log_output.append('<a href="open_folder">点击此处打开输出目录</a>')
        else:
            self.log_output.append("\n打包失败!")
            self.statusBar().showMessage("打包失败")
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat("失败")
            QMessageBox.critical(self, "打包失败", "打包过程中发生错误，请查看日志获取详细信息")

    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>PyInstaller 打包工具</h2>
        <p>版本: 2.0</p>
        <p>作者: Joe Lin</p>
        <p>描述: 这是一个强大的PyInstaller图形化打包工具，支持配置保存和恢复功能。</p>
        <p>特点:</p>
        <ul>
            <li>可视化配置PyInstaller参数</li>
            <li>支持单文件和目录模式</li>
            <li>可添加数据文件和隐藏依赖</li>
            <li>自动保存和恢复上次配置</li>
            <li>支持配置导入导出</li>
            <li>打包进度可视化</li>
            <li>强制停止功能</li>
        </ul>
        """
        QMessageBox.about(self, "关于", about_text)

    # 新增Python解释器选择方法
    def select_python(self):
        """选择Python解释器"""
        filter = "可执行文件 (*.exe *.bin)" if sys.platform == "win32" else "所有文件 (*)"
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Python解释器",
            "",
            filter
        )
        if file_path:
            self.python_path.setText(file_path)
            # 自动验证路径有效性
            if not self.validate_python_path(file_path):
                QMessageBox.warning(self, "路径无效", "选择的路径不是有效的Python解释器")
                self.python_path.clear()

    def validate_python_path(self, path):
        """验证Python解释器路径是否有效"""
        if not os.path.isfile(path):
            return False

        # 检查是否包含Python可执行文件
        exe_name = os.path.basename(path).lower()
        valid_names = {
            "python", "python.exe",
            "python3", "python3.exe",
            "pythonw", "pythonw.exe"
        }
        return exe_name in valid_names

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle("Fusion")
    app.setFont(QFont("Microsoft YaHei", 10))

    # 设置全局样式
    app.setStyleSheet("""
        QGroupBox {
            font-weight: bold;
            border: 1px solid gray;
            border-radius: 5px;
            margin-top: 1ex;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        QTextEdit {
            background-color: #f0f0f0;
            border: 1px solid #c0c0c0;
        }
        QListWidget {
            background-color: #f8f8f8;
            border: 1px solid #c0c0c0;
        }
        QProgressBar {
            border: 1px solid #c0c0c0;
            border-radius: 2px;
            text-align: center;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
        }
    """)

    window = PyInstallerPackager()
    window.show()
    sys.exit(app.exec_())
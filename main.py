import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QCheckBox, QFileDialog,
                             QListWidget, QListWidgetItem, QGroupBox, QTextEdit,
                             QMessageBox, QComboBox, QSplitter)
from PyQt5.QtCore import Qt, QProcess
from PyQt5.QtGui import QIcon, QFont


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

        # 按钮区域
        button_layout = QHBoxLayout()
        form_layout.addLayout(button_layout)

        self.package_btn = QPushButton("开始打包")
        self.package_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.package_btn.clicked.connect(self.start_packaging)
        self.package_btn.setMinimumHeight(40)
        button_layout.addWidget(self.package_btn)

        self.clear_btn = QPushButton("清空设置")
        self.clear_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.clear_btn.clicked.connect(self.clear_settings)
        self.clear_btn.setMinimumHeight(40)
        button_layout.addWidget(self.clear_btn)

        # 初始化进程
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.packaging_finished)

        # 状态栏
        self.statusBar().showMessage("就绪")

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
        self.extra_args.clear()
        self.log_output.clear()
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
            cmd.extend(["--icon", icon_path])

        # 添加数据文件
        for i in range(self.data_list.count()):
            data_item = self.data_list.item(i).text()
            cmd.extend(["--add-data", data_item])

        # 添加隐藏依赖
        for i in range(self.data_list.count()):
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

        self.log_output.clear()
        self.log_output.append("开始打包...")
        self.log_output.append(f"执行命令: {' '.join(cmd)}")
        self.statusBar().showMessage("打包中...")
        self.package_btn.setEnabled(False)

        # 设置工作目录为脚本所在目录
        work_dir = os.path.dirname(self.script_path.text())

        # 启动进程
        self.process.setWorkingDirectory(work_dir)
        self.process.start(cmd[0], cmd[1:])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        self.log_output.append(stdout)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="ignore")
        self.log_output.append(f"<font color='red'>{stderr}</font>")

    def packaging_finished(self, exit_code, exit_status):
        self.package_btn.setEnabled(True)

        if exit_code == 0:
            self.log_output.append("\n打包成功完成!")
            self.statusBar().showMessage("打包成功")

            # 打开输出目录
            output_dir = self.output_path.text()
            if os.path.exists(output_dir):
                self.log_output.append(f"\n输出目录: {output_dir}")
        else:
            self.log_output.append("\n打包失败!")
            self.statusBar().showMessage("打包失败")
            QMessageBox.critical(self, "打包失败", "打包过程中发生错误，请查看日志获取详细信息")


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
    """)

    window = PyInstallerPackager()
    window.show()
    sys.exit(app.exec_())
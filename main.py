from PySide6 import QtCore
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QApplication, QWidget, QFileDialog
from ui.Ui_main import Ui_Form
import subprocess
import sys


class CommandThread(QThread):
    output_signal = Signal(str)

    def __init__(self, command):
        super().__init__()
        self.command = command
        self.process = None

    def run(self):
        self.process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True)
        
        for line in self.process.stdout:
            self.output_signal.emit(line.strip())
        
        self.process.stdout.close()
        self.process.wait()

class MainWindow(QWidget, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.compressedZipPath = ''  # 用于存储被加密的压缩包路径
        self.plainFilePath = ''  # 用于存储明文路径
        self.bind()

    def bind(self):
        # 选择被加密的压缩包
        self.SelectCompressedFile.clicked.connect(lambda: self.UpdateCompressedFilePath(str(QFileDialog.getOpenFileName(self, "请选择被加密的压缩包", "", "Zip Files (*.zip)")[0])))
        # 查看被加密的压缩包信息
        self.CompressedZipInfo.clicked.connect(self.GetCompressedZipInfo)
        # 选择明文路径
        self.SelectPlainFile.clicked.connect(lambda: self.UpdatePlainFilePath(str(QFileDialog.getOpenFileName(self, "请选择明文路径", "")[0])))
        self.StartAttack.clicked.connect(self.Attack)
        self.ExportZip.clicked.connect(self.DoExportZip)
    
    def UpdatePlainFilePath(self, path):
        self.plainFilePath = path
        self.ViewPlainFile.setPlainText(path)
    
    def UpdateCompressedFilePath(self, path):
        self.compressedZipPath = path
        self.ViewCompressedZip.setPlainText(path)

    def GetCompressedZipInfo(self):
        # "bkcrack.exe -L " + self.ViewCompressedZip.toPlainText()
        command = ["bkcrack.exe", "-L", self.ViewCompressedZip.toPlainText()]
        print(command)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result)
        self.OutPutArea.setPlainText(result.stdout)

    def Attack(self):
        plainname = self.PlainName.toPlainText()
        if not plainname:
            self.OutPutArea.setPlainText("请先输入明文文件名称")
            return
        # "bkcrack.exe -C " + self.ViewCompressedZip.toPlainText() + " -c " + plainname + " -p " + self.ViewPlainFile.toPlainText()
        command = ["bkcrack.exe", "-C", self.ViewCompressedZip.toPlainText(), "-c", plainname, "-p", self.ViewPlainFile.toPlainText()]
        print(command)
        self.OutPutArea.clear()
        self.OutPutArea.setPlainText("正在进行明文攻击，请稍等...")
        # 启动子线程执行命令
        self.command_thread = CommandThread(command)
        self.command_thread.output_signal.connect(self.update_output)
        self.command_thread.start()
    
    def update_output(self, text):
        if "Keys:" in text:
            key = text.split(":", 1)[1].strip()
            self.InputKey.setPlainText(key)
            self.OutPutArea.append(f"攻击成功，密钥为: {key}\n已自动提取密钥并填入密钥输入框！")
            self.command_thread.terminate()
            return
        self.OutPutArea.append(text)  # 实时更新输出

    def DoExportZip(self):
        key = self.InputKey.toPlainText()
        if not key:
            self.OutPutArea.setPlainText("请先输入密钥")
            return
        plainname = self.PlainName.toPlainText()
        if not plainname:
            self.OutPutArea.setPlainText("请先输入明文文件名称")
            return
        # "bkcrack.exe -C " + self.ViewCompressedZip.toPlainText() + " -c " + plainname + " -k " + key + " -D " + self.ViewCompressedZip.toPlainText() + "_NO_PASS.zip"
        key_parts = key.strip().split() # 分割密钥为三个部分，不然 command 不会把它们当成三个参数
        command = ["bkcrack.exe", "-C", self.ViewCompressedZip.toPlainText(), "-c", plainname, "-k", key_parts[0], key_parts[1], key_parts[2], "-D", self.ViewCompressedZip.toPlainText() + "_NO_PASS.zip"]
        print(command)
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result)
        self.OutPutArea.setPlainText(result.stdout + '\n' + "导出成功！无密码压缩包路径：" + self.ViewCompressedZip.toPlainText() + "_NO_PASS.zip")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()

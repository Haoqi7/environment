import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import seaborn as sns  # 强制触发依赖分析
from matplotlib import pyplot as plt
import os
import sys
import scipy
import sklearn
import mplcursors
import pandas as pd
import numpy as np
from pandas._libs import tslibs 
def resource_path(relative_path):
    """ 获取打包后资源的绝对路径 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# 在调用cs.py和data.py的地方使用：
cs_path = resource_path('cs.py')
data_path = resource_path('data.py')

# 示例：动态导入
from importlib.util import spec_from_file_location, module_from_spec

def load_module(file_path):
    module_name = os.path.basename(file_path).split('.')[0]
    # 确保路径使用正确分隔符
    file_path = file_path.replace('/', os.sep).replace('\\', os.sep)
    spec = spec_from_file_location(module_name, file_path)
    module = module_from_spec(spec)
    # 修复Windows路径问题
    spec.loader.exec_module(module)
    return module

cs_module = load_module(cs_path)
data_module = load_module(data_path)
class AppLauncher:
    def __init__(self, master):  # 添加master参数
        self.master = master
        master.title("数据分析工具套件")
        master.geometry("300x180")


        
        # 设置界面样式
        self.style = ttk.Style()
        self.style.configure('TButton', font=('微软雅黑', 12), padding=6)
        
        # 创建主容器
        main_frame = ttk.Frame(master)
        main_frame.pack(expand=True, fill='both', padx=20, pady=15)
        
        # 环境分析工具按钮
        env_btn = ttk.Button(
            main_frame,
            text="环境数据分析工具",
            command=self.launch_env_tool,
            style='TButton'
        )
        env_btn.pack(fill='x', pady=3)
        
        # 数据处理工具按钮
        data_btn = ttk.Button(
            main_frame,
            text="数据整理工具",
            command=self.launch_data_tool,
            style='TButton'
        )
        data_btn.pack(fill='x', pady=3)
        
        # 帮助按钮
        help_btn = ttk.Button(
            main_frame,
            text="使用说明",
            command=self.show_help,
            style='TButton'
        )
        help_btn.pack(fill='x', pady=8)
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """【工具功能说明】

环境数据分析工具：
- 分析环境监测数据（温度、湿度、光照等）
- 支持多种统计方法（最大值/最小值/平均值）
- 生成专业可视化图表
- 输出Excel/CSV/图片等多种格式

数据整理工具：
- 转换数据格式（宽表转长表）
- 智能识别处理编号和指标
- 生成规范化的数据透视表
- 自动保存处理结果

适用场景：
环境数据分析 → 科研报告、环境监测
数据整理工具 → 数据预处理、格式标准化"""
        messagebox.showinfo("工具说明", help_text)
    
    def launch_env_tool(self):
        self.master.withdraw()  # 隐藏主窗口
        from cs import 环境数据分析工具
        child_window = tk.Toplevel(self.master)
        app = 环境数据分析工具(child_window, self.master)
        child_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(child_window))

    def launch_data_tool(self):
        self.master.withdraw()  # 隐藏主窗口
        from data import DataProcessorGUI
        child_window = tk.Toplevel(self.master)
        app = DataProcessorGUI(child_window, self.master)
        child_window.protocol("WM_DELETE_WINDOW", lambda: self.on_child_close(child_window))

    def on_child_close(self, child_window):
        child_window.destroy()
        self.master.deiconify()  # 恢复主窗口

    def run_script(self, filename):
        if os.path.exists(filename):
            try:
                subprocess.Popen(['python', filename])
            except Exception as e:
                messagebox.showerror("错误", f"启动失败：{str(e)}")
        else:
            messagebox.showerror("错误", f"缺失文件：{filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppLauncher(root)
    root.mainloop()

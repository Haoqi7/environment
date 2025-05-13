# -*- coding: utf-8 -*-
"""
环境数据分析工具 - 修复无法选择分析指标问题
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import re
import json
import warnings
import threading
import traceback
from typing import Dict, List, Tuple, Optional, Any, Callable
import logging
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass
import mplcursors

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('环境数据分析.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================== 配置类 ====================
@dataclass
class AppConfig:
    """应用配置类"""
    图表样式: Dict[str, Any]
    颜色配置: List[str]
    指标映射: Dict[str, List[str]]
    统计选项: List[Tuple[str, str]]
    输出格式: List[str]

默认配置 = AppConfig(
    图表样式={
        'figure.figsize': (12, 6),
        'figure.dpi': 300,
        'axes.grid': True,
        'font.size': 12
    },
    颜色配置=sns.color_palette("husl"),
    指标映射={
        '时间': ['时间', '日期', '记录时间'],
        '光照': ['光照', '亮度', '光照强度'],
        '温度': ['温度', '气温', '环境温度'],
        '湿度': ['湿度', '相对湿度']
    },
    统计选项=[
        ("每日最高值", "daily_max"),
        ("每日最低值", "daily_min"),
        ("每日平均值", "daily_avg"),
        ("日间均值(6-17时)", "daytime_avg"),
        ("夜间均值(18-5时)", "night_avg")
    ],
    输出格式=['Excel文件', 'CSV文件', '图表', '全部']
)

# ==================== 数据处理核心类 ====================
class 数据分析器:
    """数据处理核心类"""
    
    def __init__(self, 配置: AppConfig = 默认配置):
        self.配置 = 配置
        self.数据框: Optional[pd.DataFrame] = None
        self.时间列: Optional[str] = None
        self._初始化设置()

    def _初始化设置(self) -> None:
        """初始化图表样式"""
        plt.style.use('default')
        sns.set_theme(style="whitegrid", font='SimHei')
        
        合法参数 = {
            'figure.figsize': self.配置.图表样式['figure.figsize'],
            'figure.dpi': self.配置.图表样式['figure.dpi'],
            'axes.grid': self.配置.图表样式['axes.grid'],
            'font.size': self.配置.图表样式['font.size'],
            'font.sans-serif': ['SimHei', 'Microsoft YaHei'],
            'axes.unicode_minus': False
        }
        plt.rcParams.update(合法参数)

    def _读取数据(self, 文件路径: str) -> pd.DataFrame:
        """带缓存的数据读取"""
        try:
            return pd.read_excel(文件路径)
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            raise

    def _识别列类型(self, 列名: str) -> Optional[str]:
        """智能识别列类型"""
        列名清洗 = re.sub(r'[\s_（）]', '', str(列名))
        for 指标, 关键词列表 in self.配置.指标映射.items():
            if any(关键词 in 列名清洗 for 关键词 in 关键词列表):
                return 指标
        return None

    def 加载数据(self, 文件路径: str) -> Tuple[bool, str, List[str]]:
        """加载并预处理数据"""
        try:
            self.数据框 = self._读取数据(文件路径)
            
            # 识别各指标对应列
            已识别列 = {}
            for 列 in self.数据框.columns:
                if 指标 := self._识别列类型(列):
                    已识别列[指标] = 列

            if not 已识别列.get('时间'):
                return False, "⚠️ 未找到时间列（请检查是否包含'时间'或'日期'列）", []

            self.时间列 = 已识别列['时间']
            
            # 增强的时间格式预处理
            self.数据框[self.时间列] = self.数据框[self.时间列].astype(str)
            self.数据框[self.时间列] = self.数据框[self.时间列].str.replace(
                r'([年月日时分秒])',
                lambda m: {
                    '年': '/', '月': '/', '日': ' ',
                    '时': ':', '分': ':', '秒': ''
                }.get(m.group(1), m.group(1)),
                regex=True
            )
            
            # 解析日期时间
            self.数据框[self.时间列] = pd.to_datetime(
                self.数据框[self.时间列],
                format='mixed',
                errors='coerce'
            )
            
            # 处理无效日期
            if self.数据框[self.时间列].isna().any():
                无效行数 = self.数据框[self.时间列].isna().sum()
                self.数据框 = self.数据框.dropna(subset=[self.时间列])
                logger.warning(f"移除{无效行数}行无效时间数据")
                if len(self.数据框) == 0:
                    return False, "❌ 所有时间数据都无法识别", []

            # 处理缺失值
            缺失行 = self.处理缺失值(策略='插值')
            
            可用指标 = [指标 for 指标 in 已识别列 if 指标 != '时间']
            消息 = "✅ 数据加载成功" + (f" (已修复{len(缺失行)}行缺失数据)" if 缺失行 else "")
            return True, 消息, 可用指标

        except Exception as e:
            logger.error(f"数据加载错误: {traceback.format_exc()}")
            return False, f"❌ 数据加载失败: {str(e)}", []

    def 处理缺失值(self, 策略: str = '删除') -> List[int]:
        """处理缺失数据"""
        if self.数据框 is None:
            return []
            
        缺失行索引 = self.数据框.index[self.数据框.isnull().all(axis=1)].tolist()
        
        if 策略 == '删除':
            self.数据框 = self.数据框.dropna(how='all')
        elif 策略 == '插值':
            self.数据框 = self.数据框.interpolate()
        elif 策略 == '填充零':
            self.数据框 = self.数据框.fillna(0)
            
        return 缺失行索引

    def 分析数据(self, 选定指标: List[str], 统计方法: List[str]) -> Optional[pd.DataFrame]:
        """执行数据分析"""
        if self.数据框 is None or not 选定指标:
            return None

        try:
            结果 = pd.DataFrame()
            结果['日期'] = self.数据框[self.时间列].dt.date.unique()

            for 指标 in 选定指标:
                指标列 = next(
                    (列 for 列 in self.数据框.columns if self._识别列类型(列) == 指标),
                    None
                )
                if not 指标列:
                    continue

                日数据 = self.数据框.copy()
                日数据['日期'] = 日数据[self.时间列].dt.date
                日数据['小时'] = 日数据[self.时间列].dt.hour

                统计方法映射 = {
                    'daily_max': ('最高值', 'max'),
                    'daily_min': ('最低值', 'min'),
                    'daily_avg': ('平均值', 'mean'),
                    'daytime_avg': ('日间均值', lambda x: x[日数据['小时'].between(6, 17)].mean()),
                    'night_avg': ('夜间均值', lambda x: x[~日数据['小时'].between(6, 17)].mean())
                }

                for 方法 in 统计方法:
                    if 方法 in 统计方法映射:
                        标签, 函数 = 统计方法映射[方法]
                        结果[f'{指标}_{标签}'] = 日数据.groupby('日期')[指标列].agg(函数).values

            return 结果.dropna(how='all')

        except Exception as e:
            logger.error(f"数据分析错误: {traceback.format_exc()}")
            return None

    def 生成图表(self, 分析结果: pd.DataFrame, 指标: str, 输出路径: str) -> None:
        """创建可视化图表"""
        try:
            图, 坐标轴 = plt.subplots(figsize=self.配置.图表样式['figure.figsize'])
            指标列 = [列 for 列 in 分析结果.columns if 列.startswith(指标)]
            
            # 样式设置
            线型 = ['-', '--', '-.', ':']
            标记 = ['o', 's', '^', 'D', '*']
            颜色 = self.配置.颜色配置[:len(指标列)]
            
            for 序号, 列 in enumerate(指标列):
                坐标轴.plot(
                    分析结果['日期'],
                    分析结果[列],
                    label=列.split('_')[-1],
                    linestyle=线型[序号 % len(线型)],
                    marker=标记[序号 % len(标记)],
                    color=颜色[序号],
                    markersize=8,
                    linewidth=2
                )
            
            # 交互式数据提示
            mplcursors.cursor(坐标轴, hover=True).connect(
                "add", lambda sel: sel.annotation.set_text(
                    f"{sel.artist.get_label()}: {sel.target[1]:.2f}\n"
                    f"日期: {pd.to_datetime(sel.target[0]).strftime('%Y-%m-%d')}"
                )
            )
            
            # 智能调整X轴刻度
            self._调整刻度(坐标轴, 分析结果['日期'])
            
            坐标轴.set_title(f"{指标}数据分析", fontsize=14)
            坐标轴.legend(loc='upper left')
            坐标轴.grid(True, linestyle='--', alpha=0.6)
            图.tight_layout()
            
            图.savefig(输出路径, dpi=300, bbox_inches='tight')
            plt.close(图)
            
        except Exception as e:
            logger.error(f"图表生成错误: {traceback.format_exc()}")
            raise

    def _调整刻度(self, 坐标轴, 日期列表):
        """智能调整X轴显示"""
        数量 = len(日期列表)
        间隔 = max(1, 数量 // 10)  # 最多显示10个标签
        
        坐标轴.set_xticks(日期列表[::间隔])
        坐标轴.set_xticklabels(
            [pd.to_datetime(日期).strftime('%m-%d') for 日期 in 日期列表[::间隔]],
            rotation=45, 
            ha='right'
        )

# ==================== GUI界面类 ====================
class 分析线程(threading.Thread):
    """后台分析线程"""
    
    def __init__(self, 分析器: 数据分析器, 回调: Callable):
        super().__init__(daemon=True)
        self.分析器 = 分析器
        self.回调 = 回调
        self.选定指标 = []
        self.统计方法 = []
        self.输出路径 = ""
        self.输出格式 = "Excel文件"
        
    def 设置参数(self, 指标: List[str], 方法: List[str], 路径: str, 格式: str):
        self.选定指标 = 指标
        self.统计方法 = 方法
        self.输出路径 = 路径
        self.输出格式 = 格式
    
    def run(self):
        try:
            结果 = self.分析器.分析数据(self.选定指标, self.统计方法)
            if 结果 is None:
                raise ValueError("分析结果为空")
                
            文件前缀 = self.输出路径.rsplit('.', 1)[0]
            
            if self.输出格式 in ['Excel文件', '全部']:
                结果.to_excel(self.输出路径, index=False)
                
            if self.输出格式 in ['CSV文件', '全部']:
                结果.to_csv(f"{文件前缀}.csv", index=False, encoding='utf_8_sig')
                
            if self.输出格式 in ['图表', '全部']:
                for 指标 in self.选定指标:
                    self.分析器.生成图表(
                        结果, 
                        指标,
                        f"{文件前缀}_{指标}.png"
                    )
            
            self.回调(成功=True, 消息="✅ 分析完成")
            
        except Exception as e:
            self.回调(成功=False, 错误=f"❌ 分析错误: {str(e)}")

class 环境数据分析工具:
    """主界面类"""
    
    def __init__(self, master, parent_window=None):
        self.master = master
        self.parent_window = parent_window  # 新增父窗口引用
        self.配置 = 默认配置
        self.分析器 = 数据分析器(self.配置)
        self._初始化界面()
        
    def _初始化界面(self):
        """设置主窗口"""
        self.主窗口 = self.master  # 使用传入的Toplevel窗口
        self._设置样式()
        self._创建控件()
        self._创建菜单()
        self.主窗口.protocol("WM_DELETE_WINDOW", self.on_close)
    def on_close(self):

        if self.parent_window:

            self.parent_window.deiconify()  # 增加缩进
        self.主窗口.destroy()  # 保持统一缩进

    def _设置样式(self):
        """配置界面样式"""
        样式 = ttk.Style()
        样式.theme_use('clam')
        
        # 主框架
        样式.configure('主框架.TFrame', background='#f5f5f5')
        
        # 按钮
        样式.configure('主按钮.TButton', 
            padding=6, 
            font=('微软雅黑', 10, 'bold'),
            foreground='#333'
        )
        
        # 标签
        样式.configure('标题.TLabel', 
            font=('微软雅黑', 12, 'bold'), 
            background='#f5f5f5'
        )
        
        # 复选框
        样式.configure('勾选框.TCheckbutton', font=('微软雅黑', 10))
        
        # 进度条
        样式.configure('进度条.Horizontal.TProgressbar',
            thickness=25,
            troughcolor='#e0e0e0',
            background='#4CAF50'
        )

    def _创建菜单(self):
        """创建菜单系统"""
        菜单栏 = tk.Menu(self.主窗口)
        
        # 文件菜单
        文件菜单 = tk.Menu(菜单栏, tearoff=0)
        文件菜单.add_command(label="打开文件", command=self._加载文件)
        文件菜单.add_separator()
        文件菜单.add_command(label="退出", command=self.主窗口.quit)
        菜单栏.add_cascade(label="文件", menu=文件菜单)
        
        # 工具菜单
        工具菜单 = tk.Menu(菜单栏, tearoff=0)
        工具菜单.add_command(label="配置", command=self._显示配置)
        菜单栏.add_cascade(label="工具", menu=工具菜单)
        
        # 帮助菜单
        帮助菜单 = tk.Menu(菜单栏, tearoff=0)
        帮助菜单.add_command(label="使用说明", command=self._显示帮助)
        帮助菜单.add_command(label="关于", command=self._显示关于)
        菜单栏.add_cascade(label="帮助", menu=帮助菜单)
        
        self.主窗口.config(menu=菜单栏)
    
    def _创建控件(self):
        """构建界面控件"""
        主框架 = ttk.Frame(self.主窗口, style='主框架.TFrame')
        主框架.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 文件选择区域
        文件框架 = ttk.Frame(主框架)
        文件框架.pack(fill=tk.X, pady=5)
        ttk.Label(文件框架, text="数据文件:", style='标题.TLabel').pack(side=tk.LEFT)
        self.文件输入 = ttk.Entry(文件框架, width=60)
        self.文件输入.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(
            文件框架, 
            text="浏览...", 
            command=self._加载文件,
            style='主按钮.TButton'
        ).pack(side=tk.LEFT)
        
        # 指标选择区域
        指标框架 = ttk.LabelFrame(主框架, text="选择分析指标")
        指标框架.pack(fill=tk.BOTH, expand=True, pady=5)
        self.指标变量 = {}
        self.指标复选框 = {}  # 新增：保存复选框引用
        for 序号, 指标 in enumerate(self.配置.指标映射.keys()):
            if 指标 != '时间':
                变量 = tk.BooleanVar()
                勾选框 = ttk.Checkbutton(
                    指标框架, 
                    text=指标, 
                    variable=变量,
                    style='勾选框.TCheckbutton',
                    state='disabled'
                )
                勾选框.grid(
                    row=序号//2, 
                    column=序号%2, 
                    sticky=tk.W, 
                    padx=10, 
                    pady=3
                )
                self.指标变量[指标] = 变量
                self.指标复选框[指标] = 勾选框  # 保存引用
        
        # 统计方法区域
        统计框架 = ttk.LabelFrame(主框架, text="统计方法")
        统计框架.pack(fill=tk.BOTH, pady=5)
        self.统计变量 = {}
        for 序号, (文本, 值) in enumerate(self.配置.统计选项):
            变量 = tk.BooleanVar()
            勾选框 = ttk.Checkbutton(
                统计框架, 
                text=文本, 
                variable=变量,
                style='勾选框.TCheckbutton'
            )
            勾选框.grid(
                row=序号, 
                column=0, 
                sticky=tk.W, 
                padx=10, 
                pady=3
            )
            self.统计变量[值] = 变量
        
        # 输出选项区域
        输出框架 = ttk.LabelFrame(主框架, text="输出选项")
        输出框架.pack(fill=tk.X, pady=10)
        
        self.输出选项 = tk.StringVar(value="Excel文件")
        输出格式 = ['Excel文件', 'CSV文件', '图表', '全部']
        
        for i, 格式 in enumerate(输出格式):
            ttk.Radiobutton(
                输出框架,
                text=格式,
                value=格式,
                variable=self.输出选项,
                style='勾选框.TCheckbutton'
            ).pack(side=tk.LEFT, padx=15, ipady=3)
        
        # 进度条
        self.进度条 = ttk.Progressbar(
            主框架,
            orient=tk.HORIZONTAL,
            length=300,
            mode='determinate',
            style='进度条.Horizontal.TProgressbar'
        )
        self.进度条.pack(fill=tk.X, pady=10)
        
        # 操作按钮
        按钮框架 = ttk.Frame(主框架)
        按钮框架.pack(pady=10)
        
        ttk.Button(
            按钮框架,
            text="开始分析",
            command=self._执行分析,
            style='主按钮.TButton'
        ).pack(side=tk.LEFT, padx=20)
        
        ttk.Button(
            按钮框架,
            text="重置选项",
            command=self._重置界面,
            style='主按钮.TButton'
        ).pack(side=tk.LEFT, padx=20)
        
        # 状态信息
        self.状态栏 = ScrolledText(
            主框架,
            height=8,
            wrap=tk.WORD,
            font=('微软雅黑', 9),
            padx=10,
            pady=10
        )
        self.状态栏.pack(fill=tk.BOTH, expand=True)
        self._更新状态("就绪，请选择数据文件...")
    
    def _加载文件(self):
        """加载数据文件"""
        文件路径 = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("CSV文件", "*.csv")],
            initialdir=str(Path.home())
        )
        
        if 文件路径:
            self.文件输入.delete(0, tk.END)
            self.文件输入.insert(0, 文件路径)
            self._更新状态(f"正在加载文件: {文件路径}")
            
            # 在后台线程中加载文件
            def 加载线程():
                try:
                    成功, 消息, 可用指标 = self.分析器.加载数据(文件路径)
                    self._更新状态(消息)
                    if 成功:
                        self._启用指标(可用指标)
                except Exception as e:
                    self._更新状态(f"加载失败: {str(e)}")
            
            threading.Thread(target=加载线程, daemon=True).start()
    
    def _启用指标(self, 可用指标: List[str]):
        """根据数据可用性启用/禁用指标选项"""
        for 指标, 勾选框 in self.指标复选框.items():
            if 指标 in 可用指标:
                勾选框.configure(state='normal')
                self.指标变量[指标].set(True)  # 默认选中可用指标
            else:
                勾选框.configure(state='disabled')
                self.指标变量[指标].set(False)
    
    def _验证选择(self) -> Tuple[bool, List[str], List[str]]:
        """验证用户选择的有效性"""
        选定指标 = [指标 for 指标, 变量 in self.指标变量.items() if 变量.get()]
        if not 选定指标:
            messagebox.showwarning("警告", "请至少选择一个分析指标！")
            return False, [], []
        
        选定方法 = [方法 for 方法, 变量 in self.统计变量.items() if 变量.get()]
        if not 选定方法:
            messagebox.showwarning("警告", "请至少选择一种统计方法！")
            return False, [], []
        
        return True, 选定指标, 选定方法
    
    def _执行分析(self):
        """执行数据分析"""
        有效, 指标, 方法 = self._验证选择()
        if not 有效:
            return
        
        保存路径 = filedialog.asksaveasfilename(
            title="保存结果",
            defaultextension=".xlsx",
            filetypes=[
                ("Excel文件", "*.xlsx"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ],
            initialdir=os.path.abspath("分析结果"),
            initialfile="分析结果.xlsx"
        )
        
        if not 保存路径:
            return
        
        # 禁用控件防止重复操作
        self._设置控件状态('disabled')
        self.进度条['value'] = 0
        self._更新状态("正在分析数据，请稍候...")
        
        def 完成回调(成功: bool, 消息: str = None, 错误: str = None):
            self.进度条['value'] = 100 if 成功 else 0
            self._更新状态(消息 if 成功 else 错误)
            self._设置控件状态('normal')
            
            if 成功:
                messagebox.showinfo("完成", "数据分析完成！")
        
        # 创建并启动分析线程
        分析任务 = 分析线程(self.分析器, 完成回调)
        分析任务.设置参数(
            指标=指标,
            方法=方法,
            路径=保存路径,
            格式=self.输出选项.get()
        )
        分析任务.start()
        
        # 启动进度条动画
        self._动画进度()
    
    def _动画进度(self):
        """进度条动画效果"""
        if self.进度条['value'] < 90:
            self.进度条['value'] += 5
            self.主窗口.after(200, self._动画进度)
    
    def _重置界面(self):
        """重置所有选择"""
        for 变量 in self.指标变量.values():
            变量.set(False)
        
        for 变量 in self.统计变量.values():
            变量.set(False)
        
        self.输出选项.set("Excel文件")
        self._更新状态("已重置所有选项")
    
    def _设置控件状态(self, 状态: str):
        """统一设置控件状态"""
        for 控件 in self.主窗口.winfo_children():
            if isinstance(控件, (ttk.Button, ttk.Checkbutton, ttk.Radiobutton)):
                控件.configure(state=状态)
    
    def _更新状态(self, 消息: str):
        """更新状态栏信息"""
        时间戳 = datetime.now().strftime("%H:%M:%S")
        self.状态栏.insert(tk.END, f"[{时间戳}] {消息}\n")
        self.状态栏.see(tk.END)
        self.状态栏.update()
    
    def _显示配置(self):
        """显示配置窗口"""
        配置窗口 = tk.Toplevel(self.主窗口)
        配置窗口.title("分析配置")
        配置窗口.geometry("400x300")
        配置窗口.resizable(False, False)
        
        # 缺失值处理配置
        ttk.Label(配置窗口, text="缺失值处理方式:").pack(pady=(10, 0))
        缺失值处理 = ttk.Combobox(
            配置窗口,
            values=["自动填充", "删除行", "设为零值"],
            state="readonly"
        )
        缺失值处理.pack(pady=5)
        缺失值处理.current(0)
        
        # 图表样式配置
        ttk.Label(配置窗口, text="图表主题:").pack(pady=(10, 0))
        图表主题 = ttk.Combobox(
            配置窗口,
            values=["浅色", "深色", "专业", "学术"],
            state="readonly"
        )
        图表主题.pack(pady=5)
        图表主题.current(0)
        
        # 保存按钮
        ttk.Button(
            配置窗口,
            text="保存配置",
            command=lambda: self._保存配置(缺失值处理.get(), 图表主题.get()),
            style='主按钮.TButton'
        ).pack(pady=20)
    
    def _保存配置(self, 缺失值方式: str, 图表主题: str):
        """保存配置更改"""
        # TODO: 实现实际配置保存逻辑
        messagebox.showinfo("提示", f"配置已保存:\n缺失值处理: {缺失值方式}\n图表主题: {图表主题}")
    
    def _显示帮助(self):
        """显示帮助文档"""
        帮助文本 = """环境数据分析工具使用指南

1. 基本流程
   - 点击[浏览]选择数据文件(支持Excel/CSV)
   - 勾选需要分析的指标
   - 选择统计计算方法
   - 设置输出格式
   - 点击[开始分析]执行

2. 数据要求
   - 必须包含时间列(可识别'时间'/'日期'等列名)
   - 支持常见中文日期格式
   - 自动处理缺失值和格式错误

3. 输出选项
   - Excel文件: 标准Excel格式
   - CSV文件: 通用逗号分隔格式
   - 图表: 生成可视化分析图
   - 全部: 同时输出数据和图表
"""
        messagebox.showinfo("使用帮助", 帮助文本)
    
    def _显示关于(self):
        """显示关于信息"""
        import matplotlib
        关于文本 = f"""环境数据分析工具 版本2.1

功能特点:
- 多指标并行分析
- 智能日期识别
- 专业可视化图表
- 高效数据处理引擎

技术支持:
Python {pd.__version__} | Pandas {pd.__version__}
Matplotlib {matplotlib.__version__} | Seaborn {sns.__version__}

© 2023 环境数据科学团队 保留所有权利
"""
        messagebox.showinfo("关于", 关于文本)
    
    def 运行(self, block=True):
        if self.parent is None or block:
             self.主窗口.mainloop()

# ==================== 主程序入口 ====================

def main(parent=None):
    output_dir = Path("分析结果")
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    # 设置中文编码
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except:
        pass
    
    # 隐藏警告信息
    warnings.filterwarnings("ignore", category=UserWarning)
    
    # 创建输出目录
    输出目录 = Path("分析结果")
    if not 输出目录.exists():
        输出目录.mkdir()
    
    # 启动应用
    try:
        应用 = 环境数据分析工具(parent)
        应用.运行(block=(parent is None))
    except Exception as e:
       logger.critical(f"程序崩溃: {traceback.format_exc()}")
       messagebox.showerror("错误", f"程序启动失败:\n{str(e)}")

if __name__ == "__main__":
    # 独立运行时的处理
    root = tk.Tk()
    app = 环境数据分析工具(root)
    root.mainloop()
  
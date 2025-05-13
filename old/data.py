import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class DataProcessorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("数据整理工具")
        
        # ----------------------- 配置参数 -----------------------
        self.file_path = ""  # 输入文件路径
        self.id_col = ""      # 处理编号列（默认第一列）
        self.selected_metrics = []  # 选中的指标
        self.new_suffix = "_处理后"  # 输出文件后缀
        
        # ----------------------- 界面布局 -----------------------
        self.create_widgets()
    
    def create_widgets(self):
        # 1. 文件选择区域
        tk.Label(self.root, text="输入文件路径:").grid(row=0, column=0, padx=10, pady=10)
        self.file_entry = ttk.Entry(self.root, width=50)
        self.file_entry.grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(self.root, text="选择文件", command=self.select_file).grid(row=0, column=2, padx=5, pady=10)
        
        # 2. 指标选择区域
        tk.Label(self.root, text="可选指标:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.metric_list = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=30, height=10)
        self.metric_list.grid(row=2, column=0, rowspan=4, padx=10, pady=5, sticky=tk.NS)
        
        # 指标操作按钮
        ttk.Button(self.root, text="全选", command=self.select_all).grid(row=2, column=1, pady=2)
        ttk.Button(self.root, text="反选", command=self.invert_selection).grid(row=3, column=1, pady=2)
        ttk.Button(self.root, text="取消全选", command=self.deselect_all).grid(row=4, column=1, pady=2)
        
        # 3. 处理按钮与状态显示
        self.process_btn = ttk.Button(self.root, text="开始处理", command=self.process_data, state=tk.DISABLED)
        self.process_btn.grid(row=6, column=0, columnspan=3, pady=15)
        
        self.status_label = ttk.Label(self.root, text="", foreground="blue")
        self.status_label.grid(row=7, column=0, columnspan=3, pady=5)
    
    def select_file(self):
        """选择Excel文件并加载指标列表"""
        self.file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx;*.xls")])
        if self.file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(tk.END, self.file_path)
            # 读取数据并获取指标列（第一列为处理编号）
            try:
                df = pd.read_excel(self.file_path, nrows=5)  # 仅读取前5行获取列名
                self.id_col = df.columns[0]  # 假设第一列为处理编号
                metrics = df.columns[1:].tolist()  # 其余列为指标
                self.metric_list.delete(0, tk.END)
                for metric in metrics:
                    self.metric_list.insert(tk.END, metric)
                self.process_btn.config(state=tk.NORMAL)  # 启用处理按钮
            except Exception as e:
                messagebox.showerror("错误", f"文件读取失败：{str(e)}")
    
    def select_all(self):
        """全选指标"""
        self.metric_list.select_set(0, tk.END)
    
    def deselect_all(self):
        """取消全选"""
        self.metric_list.select_clear(0, tk.END)
    
    def invert_selection(self):
        """反选指标"""
        for i in range(self.metric_list.size()):
            if self.metric_list.selection_includes(i):
                self.metric_list.select_clear(i)
            else:
                self.metric_list.select_set(i)
    
    def get_selected_metrics(self):
        """获取选中的指标"""
        selected_indices = self.metric_list.curselection()
        return [self.metric_list.get(i) for i in selected_indices]
    
    def process_data(self):
        """核心数据处理逻辑"""
        self.status_label.config(text="处理中...", foreground="black")
        self.root.update()  # 刷新界面显示状态
        
        try:
            # 1. 验证输入
            if not self.file_path:
                raise ValueError("请先选择输入文件")
            self.selected_metrics = self.get_selected_metrics()
            if not self.selected_metrics:
                raise ValueError("请至少选择一个指标")
            
            # 2. 读取数据
            df = pd.read_excel(self.file_path)
            if self.id_col not in df.columns:
                raise ValueError(f"未找到处理编号列：{self.id_col}")
            
            # 3. 数据整理（复用之前的核心逻辑）
            df = df[[self.id_col] + self.selected_metrics]  # 仅保留处理编号和选中指标
            df["序号"] = df.groupby(self.id_col).cumcount() + 1  # 生成序号（1,2,3...）
            
            # 转换为长格式
            df_long = df.melt(
                id_vars=[self.id_col, "序号"],
                var_name="指标",
                value_name="值"
            )
            
            # 透视表重塑
            df_pivot = df_long.pivot_table(
                index=self.id_col,
                columns=["指标", "序号"],
                values="值"
            ).reset_index()
            
            # 简化列名
            df_pivot.columns = ["_".join(map(str, col)) if col[0] != self.id_col else col[0] for col in df_pivot.columns]
            
            # 4. 保存结果
            base_name, ext = os.path.splitext(self.file_path)
            new_file_path = f"{base_name}{self.new_suffix}{ext}"
            df_pivot.to_excel(new_file_path, index=False)
            
            self.status_label.config(text=f"处理完成！结果已保存至：\n{new_file_path}", foreground="green")
            # 打开文件所在目录（Windows系统）
            os.startfile(os.path.dirname(new_file_path))
        
        except Exception as e:
            messagebox.showerror("处理失败", f"错误：{str(e)}")
            self.status_label.config(text="", foreground="black")
        finally:
            self.process_btn.config(state=tk.NORMAL)
def main(parent=None):
    if parent is None:
        root = tk.Tk()
    else:
        root = tk.Toplevel(parent)
    app = DataProcessorGUI(root)
    if parent is None:
        root.mainloop()
if __name__ == "__main__":
    root = tk.Tk()
    app = DataProcessorGUI(root)
    root.mainloop()
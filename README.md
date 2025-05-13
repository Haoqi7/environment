


# 环境数据分析工具

![应用图标](app.ico)  
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一款专业的环境数据分析工具，支持多指标分析、数据可视化和多种格式导出。

## 主要功能

- **智能数据加载**
  - 自动识别时间序列数据
  - 处理缺失值（自动填充/删除/插值）
  - 支持Excel/CSV格式

- **多维分析**
  - 支持温度/湿度/光照等指标
  - 提供5种统计方法：
    - 每日最高/最低/平均值
    - 日间均值（6-17时）
    - 夜间均值（18-5时）

- **可视化输出**
  - 生成交互式折线图
  - 支持PNG高清导出（300dpi）
  - 智能调整刻度密度

- **灵活输出**  
  ✔️ Excel文件 ✔️ CSV文件 ✔️ 图表图像 ✔️ 批量导出

## 快速开始

### 环境要求
- Python 3.9+
- Windows/Linux/macOS

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序
```bash
# 启动主程序
python launcher.py

# 直接运行环境分析工具
python cs.py
```

## 界面操作指南

1. **文件操作**
   - 点击 `文件 > 打开` 选择数据文件
   - 支持多级目录浏览

2. **分析设置**
   - 勾选需要分析的指标
   - 选择统计方法（可多选）
   - 设置输出格式

3. **结果导出**
   - 默认保存到`分析结果`目录
   - 支持自定义保存路径
   - 实时显示处理进度

![界面截图](https://via.placeholder.com/800x500/EEE?text=GUI+Preview)



### 打包为EXE
```bash
pyinstaller --noconsole --onefile \
--add-data "cs.py;." \
--add-data "data.py;." \
--hidden-import sklearn.utils._cython_blas \
--hidden-import sklearn.neighbors.typedefs \
--hidden-import scipy._lib.messagestream \
--collect-all matplotlib \
--collect-all scipy \
--collect-all sklearn \
launcher.py
```

## 贡献指南

欢迎通过Issue或PR参与改进：
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/新功能`)
3. 提交更改 (`git commit -m '添加新功能'`)
4. 推送分支 (`git push origin feature/新功能`)
5. 发起Pull Request

## 许可证
MIT License © 2023 [Haoqi7]

## 技术支持
遇到问题请提交Issue
```

---




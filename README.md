# myGit

皇帝排行榜（MySQL + Flask）：支持列表查询、排序/筛选/搜索，以及 DIY 自定义排行榜（拖拽/双击增删、右侧自由换位）。

## 环境要求

- Python 3.8+
- MySQL 5.7+ / 8.0+

## 安装

```bash
pip install -r requirements.txt
```

## 数据库准备

1. 创建数据库（示例用 `mygit`）：

```sql
CREATE DATABASE mygit DEFAULT CHARSET utf8mb4;
```

2. 建表：

```bash
mysql -u root -p mygit < create_emperor_table.sql
```

> 说明：表名为 `emperor_rank`，主键为 `overall_rank`。

## 配置（推荐使用 `.env`）

在项目根目录创建 `.env`（该文件已被 `.gitignore` 忽略，不会提交）：

```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DATABASE=mygit
```

也可以改用环境变量（例如 Windows PowerShell）：

```powershell
$env:MYSQL_PASSWORD="你的密码"
$env:MYSQL_DATABASE="mygit"
python app.py
```

## 导入 Excel 数据

```bash
python import_emperor.py --excel "C:\path\to\皇帝排行榜3.0修订版.xlsx"
```

也支持用环境变量指定 Excel 路径：

```bash
set EXCEL_PATH=C:\path\to\皇帝排行榜3.0修订版.xlsx
python import_emperor.py
```

仅验证列映射（不连库）：

```bash
python import_emperor.py --dry-run --excel "C:\path\to\皇帝排行榜3.0修订版.xlsx"
```

## 导出为 Excel

将数据库中的 `emperor_rank` 整表导出为 Excel：

```bash
python export_emperor.py -o emperor_rank_export.xlsx
```

## 启动网页

```bash
python app.py
```

浏览器访问 `http://localhost:5000`

## 功能说明

- **排行榜页**（`/`）
  - 按时代筛选、关键字搜索
  - 表头排序（排名、时代、各维度分数、综合评分）
  - 点击行查看详情
- **DIY 排名页**（`/diy`）
  - 左侧帝王名单：**双击**加入右侧榜单末尾，或**拖拽**加入
  - 右侧我的排行榜：**自由拖拽换位**调整顺序
  - 右侧条目：**双击移回左侧**，或**拖回左侧区域**
  - 支持重置、保存/加载/删除本地排行榜（localStorage）

## 目录结构

```
├── app.py                      # Flask 后端
├── create_emperor_table.sql     # 建表 SQL
├── import_emperor.py            # Excel 导入脚本
├── export_emperor.py            # 从数据库导出为 Excel
├── requirements.txt
├── templates/
│   ├── index.html               # 排行榜页
│   └── diy.html                 # DIY 页
├── static/
│   ├── css/style.css
│   └── js/
│       ├── main.js              # 排行榜页脚本
│       └── diy.js               # DIY 页脚本
└── README.md
```

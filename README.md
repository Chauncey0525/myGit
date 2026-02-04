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
  - 表头排序（排名、时代、各维度分数、综合评分）；倒序时无评分（—）排在最后
  - 分页：首页、上一页、下一页、尾页、跳至第 N 页
  - 点击行查看详情（弹窗）；可设置多指标排序（1～5 级，如德→智→体）
  - 入口：猜猜乐、DIY 排名
- **DIY 排名页**（`/diy`）
  - 左侧帝王名单：**双击**加入右侧榜单末尾，或**拖拽**加入
  - 右侧我的排行榜：**自由拖拽换位**调整顺序
  - 右侧条目：**双击移回左侧**，或**拖回左侧区域**
  - 支持重置、保存/加载/删除本地排行榜（localStorage）
- **皇帝猜猜乐**（`/guess`）
  - 难度预设：简单 15 次（全部提示）、中等 10 次（8 个提示）、困难 5 次（4 个提示）、炼狱 3 次（1 个提示）
  - 输入皇帝**姓名**或**谥/庙号**（谥庙号需精确匹配）提交猜测
  - 每次猜测后展示各维度对比：猜的数值 + 符号（高了红↑、低了橘↓、正确绿√）
  - **放弃**按钮可立即显示答案；猜中或次数用尽后显示答案，可「再玩一局」

## API 接口（供前端调用）

- `GET /api/emperors`：列表（分页、时代筛选、搜索）；`sort`/`order` 支持多级，如 `sort=virtue,wisdom,fitness&order=desc,asc,desc`
- `GET /api/emperors/all`：全部帝王（供 DIY 左侧）
- `GET /api/emperors/<rank>`：单条详情
- `GET /api/eras`：时代列表
- `GET /api/guess/start?difficulty=easy|medium|hard|hell`：开始一局猜猜乐（分别对应 15/10/5/3 次机会，提示数量  全部/8/4/1）
- `POST /api/guess/guess`：提交猜测（body: `{ "guess": "姓名或谥庙号" }`）
- `POST /api/guess/giveup`：放弃本局并返回答案
- `GET /api/guess/names`：皇帝姓名列表（联想用）
- `GET /api/emperors/export`：按当前筛选导出 CSV（query 参数同列表）

## 运行测试

```bash
pip install pytest
python -m pytest tests/ -v
```

## 目录结构

```
├── app.py                      # Flask 后端
├── create_emperor_table.sql     # 建表 SQL
├── import_emperor.py            # Excel 导入脚本
├── export_emperor.py            # 从数据库导出为 Excel
├── requirements.txt
├── tests/
│   ├── __init__.py
│   └── test_api.py              # pytest 关键接口与 _compare_value 等
├── templates/
│   ├── index.html              # 排行榜页
│   ├── diy.html                # DIY 页
│   ├── guess.html              # 皇帝猜猜乐页
│   └── emperor_detail.html     # 皇帝详情独立页（可分享链接）
├── static/
│   ├── css/
│   │   ├── style.css           # 排行榜/DIY 共用
│   │   └── guess.css           # 猜猜乐页
│   └── js/
│       ├── main.js             # 排行榜页脚本
│       ├── diy.js              # DIY 页脚本
│       └── guess.js            # 猜猜乐页脚本
└── README.md
```

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

默认读取项目根目录下的 `emperor_rank_export.xlsx`（英文表头，与导出格式一致）：

```bash
python import_emperor.py
```

指定其他 Excel 文件（支持中文表头的旧版）：

```bash
python import_emperor.py --excel "path/to/你的文件.xlsx"
```

仅验证列映射（不连库）：

```bash
python import_emperor.py --dry-run
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
├── create_emperor_table.sql    # 建表 SQL
├── import_emperor.py           # Excel 导入脚本
├── export_emperor.py           # 从数据库导出为 Excel
├── requirements.txt
├── .env.example                # 配置示例（复制为 .env 使用）
├── tests/
│   ├── __init__.py
│   └── test_api.py
├── templates/
│   ├── index.html
│   ├── diy.html
│   ├── guess.html
│   └── emperor_detail.html
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── guess.css
│   └── js/
│       ├── main.js
│       ├── diy.js
│       └── guess.js
└── README.md
```

可选：`emperor_rank_export.xlsx` 可作为初始数据，部署时若不需要可删除；导入时用 `--excel` 指定其它文件即可。

---

## 打包与部署到云服务器

本项目无 Windows 专用路径，可在 Linux 云服务器上直接运行。

### 1. 打包

在本地排除无关文件后打包（不包含 `.env`、`__pycache__`、`.pytest_cache` 等，已由 `.gitignore` 忽略）：

```bash
# 方式 A：git 归档（推荐，不含 .git）
git archive -o mygit-deploy.zip HEAD

# 方式 B：若未用 git，手动 zip 时不要包含 .env、__pycache__、.pytest_cache
```

如需带初始数据一起部署，保留 `emperor_rank_export.xlsx`；否则可删除该文件，到服务器后再导入。

### 2. 上传到云服务器

```bash
scp mygit-deploy.zip user@你的服务器IP:/home/user/
ssh user@你的服务器IP
cd /home/user && unzip mygit-deploy.zip -d mygit && cd mygit
```

### 3. 服务器环境

- **Python 3.8+**
- **MySQL 5.7+ / 8.0+**（与应用同机或远程均可）

安装依赖：

```bash
python3 -m venv venv
source venv/bin/activate   # Linux
pip install -r requirements.txt
```

### 4. 数据库

在服务器上创建库并建表（若 MySQL 在本地）：

```bash
mysql -u root -p -e "CREATE DATABASE mygit DEFAULT CHARSET utf8mb4;"
mysql -u root -p mygit < create_emperor_table.sql
```

若 MySQL 在其它机器，请修改下面 `.env` 中的 `MYSQL_HOST`。

### 5. 配置

在项目根目录创建 `.env`（**不要**提交到 git）：

```bash
cp .env.example .env
nano .env
```

填写生产环境值，例如：

```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的MySQL密码
MYSQL_DATABASE=mygit
FLASK_SECRET_KEY=随机长字符串
```

### 6. 导入数据（可选）

若打包时带了 `emperor_rank_export.xlsx`：

```bash
python import_emperor.py
```

否则将 Excel 上传后执行：

```bash
python import_emperor.py --excel /path/to/emperor_rank_export.xlsx
```

### 7. 启动服务

**开发/调试**（仅本机访问）：

```bash
python app.py
# 默认 http://0.0.0.0:5000，云服务器需在安全组放行 5000 端口
```

**生产环境**（推荐用 Gunicorn）：

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

- `-w 4`：4 个 worker，可按 CPU 核数调整  
- `-b 0.0.0.0:5000`：监听所有网卡的 5000 端口  

后台运行示例：

```bash
nohup gunicorn -w 4 -b 0.0.0.0:5000 app:app > gunicorn.log 2>&1 &
```

### 8. 可选：Nginx 反代

如需用 80 端口或配置域名，可在 Nginx 中增加：

```nginx
server {
    listen 80;
    server_name 你的域名或IP;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

重载 Nginx：`sudo nginx -s reload`

### 部署检查清单

- [ ] Python 3.8+、MySQL 已安装
- [ ] 已创建数据库并执行 `create_emperor_table.sql`
- [ ] 已配置 `.env`（且未提交到 git）
- [ ] 已执行 `import_emperor.py` 导入数据（若需要）
- [ ] 安全组/防火墙已放行 5000（或 Nginx 的 80）
- [ ] 生产环境使用 `gunicorn` 或等效 WSGI 服务器

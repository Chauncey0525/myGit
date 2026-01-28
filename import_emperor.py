# -*- coding: utf-8 -*-
"""从「皇帝排行榜3.0修订版.xlsx」导入到 emperor_rank（英文字段）"""
import os
import sys

try:
    import pandas as pd
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "openpyxl", "-q"])
    import pandas as pd

# 连接在 main() 内按需选用 mysql.connector 或 pymysql；
# mysql.connector 通常不需 cryptography，可避免旧 pip 下安装 cryptography 失败。

# Excel 路径（可用环境变量 EXCEL_PATH 覆盖，或运行时传 --excel）
EXCEL_PATH = os.environ.get("EXCEL_PATH", r"c:\Users\wb.zhangchixin02\Desktop\皇帝排行榜3.0修订版.xlsx")

# Excel 列名 -> 目标表列名（英文字段）。
# - “顺序号”不入表
# - “历史影响”不直接用 Excel 的该列，而是用 “历史影响赋分*10” 计算后写入 historical_impact
EXCEL_TO_DB = {
    "总排名": "overall_rank",
    "顺序号": "_sequence_no_ignore",  # 仅用于读 Excel，不入表
    "时代": "era",
    "庙/谥\n/称号": "temple_posthumous_title",
    "姓名": "name",
    "短\n评": "short_comment",
    "德\n(11%)": "virtue",
    "智\n(10%)": "wisdom",
    "体\n(2%)": "fitness",
    "美\n(2%)": "beauty",
    "劳\n(6%)": "diligence",
    "雄心\n(3%)": "ambition",
    "尊严\n(7%)": "dignity",
    "气量\n(4%)": "magnanimity",
    "欲望\n自控\n(4%)": "desire_self_control",
    "人事\n管理\n(12%)": "personnel_management",
    "国力\n(6%)": "national_power",
    "军事\n外交\n(9%)": "military_diplomacy",
    "民心\n(7%)": "public_support",
    "经济\n民生(7%)": "economy_livelihood",
    "历史\n影响\n(10%)": "_historical_impact_ignore",  # 不采此列，用 impact_score*10
    "综合评分": "overall_score",
    "历史影响赋分": "impact_score",  # 仅用于计算 historical_impact=impact_score*10，不入表
}

# 入表列：不含顺序号、impact_score；historical_impact 在导入时用 impact_score*10 填充
DB_COLS = [
    "overall_rank",
    "era",
    "temple_posthumous_title",
    "name",
    "short_comment",
    "virtue",
    "wisdom",
    "fitness",
    "beauty",
    "diligence",
    "ambition",
    "dignity",
    "magnanimity",
    "desire_self_control",
    "personnel_management",
    "national_power",
    "military_diplomacy",
    "public_support",
    "economy_livelihood",
    "historical_impact",
    "overall_score",
]


def _norm(x):
    """NaN/NaT -> None，其它转为可写入数据库的值"""
    if pd.isna(x):
        return None
    if hasattr(x, "item"):  # numpy scalar
        return x.item()
    return x


def _to_int_or_none(x):
    """转为 int 或 None，避免 顺序号/总排名 的 float/字符串导致 Data truncated"""
    if x is None or pd.isna(x):
        return None
    s = str(x).strip()
    if s in ("", "-", "—", "－"):
        return None
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _to_decimal_or_none(x):
    """转为适合 DECIMAL 的 float 或 None，过滤 [object Object] 等无效值"""
    if x is None or pd.isna(x):
        return None
    if hasattr(x, "item"):
        x = x.item()
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        return float(x)
    s = str(x).strip()
    if not s or s.lower().startswith("[object"):
        return None
    if s in ("-", "—", "－"):
        return None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _to_str_or_none(x):
    """按字符串导入，NaN/空 -> None"""
    if x is None or pd.isna(x):
        return None
    s = str(x).strip()
    return s if s else None


def main(excel_path=None):
    excel_path = excel_path or EXCEL_PATH
    if not os.path.isfile(excel_path):
        print(f"文件不存在: {excel_path}")
        sys.exit(1)

    print("正在读取 Excel …")
    df = pd.read_excel(excel_path, sheet_name=0, engine="openpyxl")

    # 按 Excel 列名匹配到表结构（Excel 表头可能含换行，用 strip 后的首词或整列名匹配）
    def norm_excel(s):
        return "".join(str(s).split())

    use_cols = []
    rename = {}
    for c in df.columns:
        sc = str(c).strip()
        # 先精确匹配，再按“去空白”后的关键词匹配
        if sc in EXCEL_TO_DB:
            use_cols.append(c)
            rename[c] = EXCEL_TO_DB[sc]
        else:
            nc = norm_excel(c)
            for k, v in EXCEL_TO_DB.items():
                if norm_excel(k) == nc:
                    use_cols.append(c)
                    rename[c] = v
                    break
    if len(use_cols) < len(EXCEL_TO_DB):
        print("部分列未匹配，请检查 Excel 表头与 EXCEL_TO_DB 是否一致。")
    data = df[use_cols].copy()
    data = data.rename(columns=rename)
    # historical_impact = impact_score*10 (impact_score 不入表)
    if "impact_score" in data.columns:
        data["historical_impact"] = data["impact_score"].map(
            lambda x: (_to_decimal_or_none(x) * 10) if _to_decimal_or_none(x) is not None else None
        )
    data = data[[c for c in DB_COLS if c in data.columns]]

    # MySQL 连接（可从环境变量覆盖）
    host = os.environ.get("MYSQL_HOST", "127.0.0.1")
    port = int(os.environ.get("MYSQL_PORT", "3306"))
    user = os.environ.get("MYSQL_USER", "root")
    password = os.environ.get("MYSQL_PASSWORD", "")
    database = os.environ.get("MYSQL_DATABASE", "mygit")
    if not password:
        try:
            import getpass
            password = getpass.getpass("MySQL 密码 (直接回车表示无密码): ")
        except Exception:
            password = input("MySQL 密码 (直接回车表示无密码): ")

    cols = list(data.columns)
    placeholders = ", ".join(["%s"] * len(cols))
    col_list = "`, `".join(cols)
    sql = f"INSERT INTO `emperor_rank` (`{col_list}`) VALUES ({placeholders})"

    print(f"准备导入 {len(data)} 行到数据库 {database}.emperor_rank …")

    def connect():
        """优先用 mysql-connector（不需 cryptography），再试 pymysql"""
        try:
            import mysql.connector
            return mysql.connector.connect(
                host=host, port=port, user=user, password=password,
                database=database, charset="utf8mb4",
            ), "mysql.connector"
        except ImportError:
            pass
        try:
            import pymysql
            return pymysql.connect(
                host=host, port=port, user=user, password=password,
                database=database, charset="utf8mb4",
            ), "pymysql"
        except ImportError:
            raise RuntimeError("请安装：pip install mysql-connector-python  或  pip install pymysql")

    try:
        conn, driver = connect()
        cur = conn.cursor()
        # 确保使用 UTF-8 编码
        cur.execute("SET NAMES utf8mb4")
        # 主键/唯一冲突时跳过的异常类型
        if driver == "pymysql":
            import pymysql as _db
            integ_error = _db.IntegrityError
        else:
            import mysql.connector.errors as _db_err
            integ_error = _db_err.IntegrityError
        INT_COLS = {"overall_rank"}  # 主键，空时用行号兜底
        DECIMAL_COLS = {
            "virtue",
            "wisdom",
            "fitness",
            "beauty",
            "diligence",
            "ambition",
            "dignity",
            "magnanimity",
            "desire_self_control",
            "personnel_management",
            "national_power",
            "military_diplomacy",
            "public_support",
            "economy_livelihood",
            "historical_impact",
            "overall_score",
        }
        imported = 0
        for idx, row in data.iterrows():
            vals = []
            for c in cols:
                v = row[c]
                if c in INT_COLS:
                    n = _to_int_or_none(v)
                    if c == "overall_rank" and n is None:
                        n = int(idx) + 1
                    vals.append(n)
                elif c in DECIMAL_COLS:
                    vals.append(_to_decimal_or_none(v))
                else:
                    vals.append(_norm(v))
            try:
                cur.execute(sql, vals)
                imported += 1
            except integ_error as e:
                print(f"  跳过重复行 overall_rank={row.get('overall_rank')}: {e}")
        conn.commit()
        cur.close()
        conn.close()
        print(f"导入完成，成功 {imported} 行。")
    except Exception as e:
        err = str(e).lower()
        if "cryptography" in err or "caching_sha2" in err or "sha256" in err:
            print("MySQL 8 认证需要 cryptography，但安装失败。可改用官方驱动：")
            print("  pip install mysql-connector-python")
            print("然后重新运行本脚本。")
        else:
            print(f"导入失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="从 Excel 导入皇帝排行榜数据到 MySQL 表 emperor_rank")
    parser.add_argument("--excel", help="Excel 文件路径（也可用环境变量 EXCEL_PATH）", default=None)
    parser.add_argument("--dry-run", "-n", action="store_true", help="仅校验 Excel 读取与列映射，不连接数据库")
    args = parser.parse_args()

    dry = "--dry-run" in sys.argv or "-n" in sys.argv
    if args.dry_run or dry:
        # 仅校验 Excel 读取与列映射，不连库
        excel_path = args.excel or EXCEL_PATH
        df = pd.read_excel(excel_path, sheet_name=0, engine="openpyxl")
        def norm_excel(s):
            return "".join(str(s).split())
        use_cols = []
        rename = {}
        for c in df.columns:
            sc = str(c).strip()
            if sc in EXCEL_TO_DB:
                use_cols.append(c)
                rename[c] = EXCEL_TO_DB[sc]
            else:
                nc = norm_excel(c)
                for k, v in EXCEL_TO_DB.items():
                    if norm_excel(k) == nc:
                        use_cols.append(c)
                        rename[c] = v
                        break
        data = df[use_cols].rename(columns=rename)
        if "impact_score" in data.columns:
            data["historical_impact"] = data["impact_score"].map(
                lambda x: (_to_decimal_or_none(x) * 10) if _to_decimal_or_none(x) is not None else None
            )
        data = data[[c for c in DB_COLS if c in data.columns]]
        print("--dry-run: 列数=%d, 行数=%d" % (len(data.columns), len(data)))
        print("列名:", list(data.columns))
        sys.exit(0)
    main(args.excel)

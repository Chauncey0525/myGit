# -*- coding: utf-8 -*-
"""从 MySQL 导出 emperor_rank 到 Excel 文件。"""

import os
import sys

import pandas as pd


def _load_env():
    """启动时加载 .env：先尝试脚本所在目录，再当前工作目录（与 app.py 一致）。"""
    try:
        from dotenv import load_dotenv
        base_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(base_dir, ".env"))
        load_dotenv(".env")
    except ImportError:
        pass
    if not os.environ.get("MYSQL_PASSWORD"):
        _read_env_file()


def _read_env_file():
    """从项目根目录的 .env 兜底加载 MYSQL_* 配置（不依赖 python-dotenv）。"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(base_dir, ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and (k not in os.environ or not os.environ.get(k)):
                    os.environ[k] = v
    except Exception:
        pass


def get_db_config():
    if not os.environ.get("MYSQL_PASSWORD"):
        _read_env_file()
    cfg = {
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", ""),
        "database": os.environ.get("MYSQL_DATABASE", "mygit"),
    }
    if not cfg.get("password") and cfg.get("user") == "root":
        print("提示: 未检测到 MYSQL_PASSWORD。请在项目根目录创建 .env 并设置 MYSQL_PASSWORD=你的密码", file=sys.stderr)
    return cfg


def get_connection():
    """优先使用 mysql-connector，其次 pymysql。"""
    cfg = get_db_config()
    try:
        import mysql.connector

        conn = mysql.connector.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            charset="utf8mb4",
        )
        return conn
    except ImportError:
        pass

    try:
        import pymysql

        conn = pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            charset="utf8mb4",
        )
        return conn
    except ImportError:
        raise RuntimeError("请安装：pip install mysql-connector-python 或 pip install pymysql")


def export_to_excel(output_path: str) -> None:
    """将 emperor_rank 全表导出到 Excel。"""
    conn = None
    try:
        conn = get_connection()
        # 使用 pandas 直接读取整张表
        df = pd.read_sql(
            """
            SELECT overall_rank, era, temple_posthumous_title, name, short_comment,
                   virtue, wisdom, fitness, beauty, diligence, ambition, dignity,
                   magnanimity, desire_self_control, personnel_management,
                   national_power, military_diplomacy, public_support,
                   economy_livelihood, historical_impact, overall_score
            FROM emperor_rank
            ORDER BY overall_rank
            """,
            conn,
        )
        # 导出为 Excel
        df.to_excel(output_path, index=False)
        print(f"已导出 {len(df)} 行到: {output_path}")
    except Exception as e:
        print(f"导出失败: {e}")
        sys.exit(1)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description="将 emperor_rank 表导出为 Excel 文件")
    parser.add_argument(
        "--output",
        "-o",
        help="输出 Excel 路径（默认: emperor_rank_export.xlsx）",
        default="emperor_rank_export.xlsx",
    )
    args = parser.parse_args()
    output_path = os.path.abspath(args.output)
    export_to_excel(output_path)


if __name__ == "__main__":
    _load_env()
    main()


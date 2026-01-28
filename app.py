# -*- coding: utf-8 -*-
"""皇帝排名网页应用 - Flask 后端"""
import os

# 启动时加载 .env：先尝试 app 所在目录，再尝试当前工作目录，确保能读到 MYSQL_PASSWORD
def _load_env():
    try:
        from dotenv import load_dotenv
        app_dir = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(app_dir, ".env"))
        load_dotenv(".env")  # 当前工作目录，不覆盖已有
    except ImportError:
        pass
_load_env()

from flask import Flask, request, jsonify, render_template

app = Flask(__name__, static_folder="static", template_folder="templates")


def _read_env_file():
    """若环境变量无密码或未设置，从 app 同目录的 .env 再读一次（兜底，不依赖 python-dotenv）。"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    # 未设置或为空时从 .env 填入（覆盖空密码）
                    if k and (k not in os.environ or not os.environ.get(k)):
                        os.environ[k] = v
    except Exception:
        pass


def get_db_config():
    # 密码为空时从 .env 兜底读取（不依赖 python-dotenv 是否安装）
    if not os.environ.get("MYSQL_PASSWORD"):
        _read_env_file()
    return {
        "host": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.environ.get("MYSQL_PORT", "3306")),
        "user": os.environ.get("MYSQL_USER", "root"),
        "password": os.environ.get("MYSQL_PASSWORD", ""),
        "database": os.environ.get("MYSQL_DATABASE", "mygit"),
    }


def get_connection():
    """优先 mysql-connector，否则 pymysql。返回连接与 cursor 工厂（dict 游标）。"""
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
        return conn, lambda c: c.cursor(dictionary=True)
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
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn, lambda c: c.cursor()
    except ImportError:
        raise RuntimeError("请安装：pip install mysql-connector-python 或 pip install pymysql")


def row_to_json(row):
    """把一行（含 Decimal）转为可 JSON 序列化的 dict。"""
    if row is None:
        return None
    out = {}
    for k, v in row.items():
        if hasattr(v, "__float__") and not isinstance(v, (bool, int)):
            try:
                out[k] = float(v)
            except (TypeError, ValueError):
                out[k] = v
        elif v is None:
            out[k] = None
        else:
            out[k] = v
    return out


# 允许排序的字段（白名单，防注入）；name、temple_posthumous_title 不在表头排序
SORT_FIELDS = {
    "overall_rank", "era",
    "virtue", "wisdom", "fitness", "beauty", "diligence",
    "ambition", "dignity", "magnanimity", "desire_self_control",
    "personnel_management", "national_power", "military_diplomacy",
    "public_support", "economy_livelihood", "historical_impact",
    "overall_score",
}

# 时代排序用：按朝代先后，与前端 ERA_ORDER 一致
ERA_ORDER = [
    "秦", "西汉", "新", "东汉", "成汉", "曹魏", "蜀汉", "孙吴", "西晋", "前赵", "前燕", "前凉",
    "东晋", "后赵", "前秦", "冉魏", "前蜀", "后燕", "南燕", "西秦", "后秦", "后凉", "南凉", "北凉",
    "西凉", "北燕", "胡夏", "北魏", "南朝宋", "南齐", "南梁", "陈", "西魏", "东魏", "北齐", "北周",
    "隋", "唐", "武周", "吴越", "闽国", "南吴", "南楚", "前蜀", "后梁", "辽", "后唐", "南汉", "南平",
    "后蜀", "后晋", "南唐", "后汉", "后周", "北汉", "北宋", "西夏", "西辽", "金", "南宋", "蒙古", "元", "明", "清",
]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/diy")
def diy():
    return render_template("diy.html")


@app.route("/api/emperors", methods=["GET"])
def api_emperors():
    """GET /api/emperors?page=1&per_page=50&sort=overall_score&order=desc&era=唐&search=李世民"""
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 50, type=int)))
    sort = request.args.get("sort", "overall_rank")
    order = request.args.get("order", "asc").lower()
    era = request.args.get("era", "").strip()
    search = request.args.get("search", "").strip()

    if sort not in SORT_FIELDS:
        sort = "overall_rank"
    if order not in ("asc", "desc"):
        order = "asc"
    # 时代按朝代顺序：升序=秦→清，降序=清→秦；未在列表中的时代排在最后
    order_params = []
    if sort == "era":
        placeholders = ", ".join("%s" for _ in ERA_ORDER)
        if order == "asc":
            order_clause = f"ORDER BY (FIELD(era, {placeholders}) = 0), FIELD(era, {placeholders}) ASC"
            order_params = list(ERA_ORDER) + list(ERA_ORDER)
        else:
            order_clause = f"ORDER BY FIELD(era, {placeholders}) DESC"
            order_params = list(ERA_ORDER)
    else:
        order_sql = "ASC" if order == "asc" else "DESC"
        order_clause = f"ORDER BY `{sort}` {order_sql}"

    where_clauses = []
    params = []
    if era:
        where_clauses.append("era = %s")
        params.append(era)
    if search:
        where_clauses.append("(name LIKE %s OR era LIKE %s OR temple_posthumous_title LIKE %s)")
        like_val = f"%{search}%"
        params.extend([like_val, like_val, like_val])
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            count_sql = "SELECT COUNT(*) AS total FROM emperor_rank " + where_sql
            cur.execute(count_sql, params)
            row = cur.fetchone()
            total = row["total"] if isinstance(row, dict) else (row[0] if row else 0)

            offset = (page - 1) * per_page
            list_sql = (
                "SELECT overall_rank, era, temple_posthumous_title, name, short_comment, "
                "virtue, wisdom, fitness, beauty, diligence, ambition, dignity, magnanimity, "
                "desire_self_control, personnel_management, national_power, military_diplomacy, "
                "public_support, economy_livelihood, historical_impact, overall_score "
                "FROM emperor_rank " + where_sql + " " + order_clause + " LIMIT %s OFFSET %s"
            )
            params_ext = params + order_params + [per_page, offset]
            cur.execute(list_sql, params_ext)
            rows = cur.fetchall()
            data = [row_to_json(r) for r in rows]
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "data": data,
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@app.route("/api/emperors/all", methods=["GET"])
def api_emperors_all():
    """GET /api/emperors/all - 全部帝王（按时代、排名），供 DIY 页左侧按朝代展示"""
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            cur.execute(
                "SELECT overall_rank, era, temple_posthumous_title, name "
                "FROM emperor_rank ORDER BY era, overall_rank"
            )
            rows = cur.fetchall()
            data = [row_to_json(r) for r in rows]
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"data": data})


@app.route("/api/emperors/<int:rank>", methods=["GET"])
def api_emperor_detail(rank):
    """GET /api/emperors/1 - 单个皇帝详情"""
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            cur.execute(
                "SELECT overall_rank, era, temple_posthumous_title, name, short_comment, "
                "virtue, wisdom, fitness, beauty, diligence, ambition, dignity, magnanimity, "
                "desire_self_control, personnel_management, national_power, military_diplomacy, "
                "public_support, economy_livelihood, historical_impact, overall_score "
                "FROM emperor_rank WHERE overall_rank = %s",
                (rank,),
            )
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(row_to_json(row))


@app.route("/api/emperors/reorder", methods=["POST"])
def api_emperors_reorder():
    """POST /api/emperors/reorder - DIY 排序由前端 localStorage 保存，此接口仅返回成功。"""
    body = request.get_json() or {}
    ranks = body.get("ranks", [])
    if not isinstance(ranks, list):
        return jsonify({"success": False, "error": "ranks must be array"}), 400
    return jsonify({"success": True})


@app.route("/api/eras", methods=["GET"])
def api_eras():
    """GET /api/eras - 时代列表，用于筛选下拉"""
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            cur.execute("SELECT DISTINCT era FROM emperor_rank WHERE era IS NOT NULL AND era != '' ORDER BY era")
            rows = cur.fetchall()
            eras = [r["era"] if isinstance(r, dict) else r[0] for r in rows]
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"data": eras})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

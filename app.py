# -*- coding: utf-8 -*-
"""皇帝排名网页应用 - Flask 后端"""
import os
import random

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

import csv
import io

from flask import Flask, request, jsonify, render_template, session, Response

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-in-prod")


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

# 多指标排序：解析 sort=field1,field2&order=asc,desc，返回 (order_clause, order_params)
def _parse_multi_sort(sort_str, order_str):
    sort_list = [s.strip() for s in (sort_str or "").split(",") if s.strip()]
    sort_list = [s for s in sort_list if s in SORT_FIELDS][:10]
    if not sort_list:
        sort_list = ["overall_rank"]
    order_list = [o.strip().lower() for o in (order_str or "asc").split(",") if o.strip()]
    if len(order_list) == 1 and order_list[0] in ("asc", "desc"):
        order_list = [order_list[0]] * len(sort_list)
    else:
        order_list = [(o if o in ("asc", "desc") else "asc") for o in order_list[: len(sort_list)]]
    while len(order_list) < len(sort_list):
        order_list.append("asc")
    order_parts = []
    order_params = []
    for i, sf in enumerate(sort_list):
        ord_dir = order_list[i]
        if sf == "era":
            placeholders = ", ".join("%s" for _ in ERA_ORDER)
            if ord_dir == "asc":
                order_parts.append(
                    f"(FIELD(era, {placeholders}) = 0), FIELD(era, {placeholders}) ASC"
                )
                order_params.extend(ERA_ORDER)
                order_params.extend(ERA_ORDER)
            else:
                order_parts.append(f"FIELD(era, {placeholders}) DESC")
                order_params.extend(ERA_ORDER)
        else:
            order_sql = "ASC" if ord_dir == "asc" else "DESC"
            order_parts.append(f"`{sf}` IS NULL, `{sf}` {order_sql}")
    order_clause = "ORDER BY " + ", ".join(order_parts)
    return order_clause, order_params


# 时代排序用：按朝代先后，与前端 ERA_ORDER 一致
ERA_ORDER = [
    "秦", "西汉", "新", "东汉", "成汉", "曹魏", "蜀汉", "孙吴", "西晋", "前赵", "前燕", "前凉",
    "东晋", "后赵", "前秦", "冉魏", "前蜀", "后燕", "南燕", "西秦", "后秦", "后凉", "南凉", "北凉",
    "西凉", "北燕", "胡夏", "北魏", "南朝宋", "南齐", "南梁", "陈", "西魏", "东魏", "北齐", "北周",
    "隋", "唐", "武周", "吴越", "闽国", "南吴", "南楚", "前蜀", "后梁", "辽", "后唐", "南汉", "南平",
    "后蜀", "后晋", "南唐", "后汉", "后周", "北汉", "北宋", "西夏", "西辽", "金", "南宋", "蒙古", "元", "明", "清",
]

# 猜猜乐：提示用一项评分字段（随机）；比较时用所有评分相关字段
GUESS_HINT_FIELDS = [
    "virtue", "wisdom", "fitness", "beauty", "diligence", "ambition", "dignity", "magnanimity",
    "desire_self_control", "personnel_management", "national_power", "military_diplomacy",
    "public_support", "economy_livelihood", "historical_impact", "overall_score",
]
GUESS_COMPARE_FIELDS = [
    "overall_rank", "era",
    "virtue", "wisdom", "fitness", "beauty", "diligence", "ambition", "dignity", "magnanimity",
    "desire_self_control", "personnel_management", "national_power", "military_diplomacy",
    "public_support", "economy_livelihood", "historical_impact", "overall_score",
]
GUESS_FIELD_LABELS = {
    "overall_rank": "排名", "era": "时代",
    "virtue": "德", "wisdom": "智", "fitness": "体", "beauty": "美", "diligence": "劳",
    "ambition": "雄心", "dignity": "尊严", "magnanimity": "气量", "desire_self_control": "欲望自控",
    "personnel_management": "人事管理", "national_power": "国力", "military_diplomacy": "军事外交",
    "public_support": "民心", "economy_livelihood": "经济民生", "historical_impact": "历史影响",
    "overall_score": "综合评分",
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/diy")
def diy():
    return render_template("diy.html")


@app.route("/guess")
def guess():
    return render_template("guess.html")


@app.route("/e/<int:rank>")
def emperor_detail_page(rank):
    """皇帝详情独立页，便于分享链接。"""
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
        return render_template("emperor_detail.html", emperor=None, error=str(e))
    if not row:
        return render_template("emperor_detail.html", emperor=None, error="Not found"), 404
    emperor = row_to_json(row)
    return render_template("emperor_detail.html", emperor=emperor, error=None)


def _is_valid_score(val):
    """评分为有效数字时才用作提示，排除 None、空、'-' 等。"""
    if val is None or val == "":
        return False
    try:
        float(val)
        return True
    except (TypeError, ValueError):
        return False


@app.route("/api/guess/start", methods=["GET"])
def api_guess_start():
    """开始一局猜猜乐：按难度设置可猜次数与初始提示数量。"""
    difficulty_raw = request.args.get("difficulty", "medium")
    DIFFICULTY_PRESETS = {
        "easy": {"guesses": 15, "hint_count": "all"},
        "medium": {"guesses": 10, "hint_count": 8},
        "hard": {"guesses": 5, "hint_count": 4},
        "hell": {"guesses": 3, "hint_count": 1},
    }
    # 兼容旧数字参数：15/10/5/3
    if isinstance(difficulty_raw, str) and difficulty_raw.isdigit():
        d_map = {"15": "easy", "10": "medium", "5": "hard", "3": "hell"}
        difficulty_key = d_map.get(difficulty_raw, "medium")
    else:
        difficulty_key = str(difficulty_raw).lower()
        if difficulty_key not in DIFFICULTY_PRESETS:
            difficulty_key = "medium"
    preset = DIFFICULTY_PRESETS[difficulty_key]
    total_guesses = preset["guesses"]
    hint_count = preset["hint_count"]
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            for _ in range(50):  # 最多重试 50 次，避免抽到所有评分都为空的皇帝
                cur.execute(
                    "SELECT overall_rank, era, temple_posthumous_title, name, short_comment, "
                    "virtue, wisdom, fitness, beauty, diligence, ambition, dignity, magnanimity, "
                    "desire_self_control, personnel_management, national_power, military_diplomacy, "
                    "public_support, economy_livelihood, historical_impact, overall_score "
                    "FROM emperor_rank ORDER BY RAND() LIMIT 1"
                )
                row = cur.fetchone()
                if not row:
                    break
                answer = row_to_json(row)
                valid_hint_fields = [f for f in GUESS_HINT_FIELDS if _is_valid_score(answer.get(f))]
                try:
                    overall = answer.get("overall_score")
                    overall_zero = overall is None or overall == "" or float(overall) == 0
                except (TypeError, ValueError):
                    overall_zero = True
                if valid_hint_fields and not overall_zero:
                    if hint_count == "all":
                        chosen_fields = valid_hint_fields
                    else:
                        take = min(len(valid_hint_fields), int(hint_count) if isinstance(hint_count, int) else 1)
                        chosen_fields = random.sample(valid_hint_fields, take)
                    hints = [{
                        "field": hf,
                        "label": GUESS_FIELD_LABELS.get(hf, hf),
                        "value": answer.get(hf),
                    } for hf in chosen_fields]
                    session["guess_answer"] = answer
                    session["guess_guesses_left"] = total_guesses
                    session["guess_hint_field"] = chosen_fields[0] if chosen_fields else None
                    return jsonify({
                        "hints": hints,
                        "total_guesses": total_guesses,
                    })
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"error": "暂无可用的皇帝数据（需至少有一项有效评分）"}), 500


def _compare_value(field, guess_val, answer_val):
    """返回 'high' | 'low' | 'correct'。排名：数字小=高；时代：ERA_ORDER 索引小=早。"""
    if field == "overall_rank":
        g, a = (guess_val is not None and guess_val != ""), (answer_val is not None and answer_val != "")
        if not g and not a:
            return "correct"
        if not g or not a:
            return "low" if not g else "high"
        gv, av = int(guess_val), int(answer_val)
        if gv == av:
            return "correct"
        return "low" if gv > av else "high"  # 排名数字小=更好=高了
    if field == "era":
        if (not guess_val and not answer_val) or guess_val == answer_val:
            return "correct"
        try:
            gi = ERA_ORDER.index(guess_val) if guess_val else -1
            ai = ERA_ORDER.index(answer_val) if answer_val else -1
        except (ValueError, TypeError):
            return "correct"
        if gi == ai:
            return "correct"
        return "early" if gi < ai else "late"  # 时代早/晚
    # 数值型
    g_ok = guess_val is not None and guess_val != ""
    a_ok = answer_val is not None and answer_val != ""
    if not g_ok and not a_ok:
        return "correct"
    if not g_ok or not a_ok:
        return "low" if not g_ok else "high"
    try:
        gv = float(guess_val)
        av = float(answer_val)
    except (TypeError, ValueError):
        return "correct"
    if gv == av:
        return "correct"
    return "high" if gv > av else "low"


@app.route("/api/guess/guess", methods=["POST"])
def api_guess_guess():
    """提交一次猜测，返回各字段对比（高了/低了/正确）及是否猜中、剩余次数。"""
    try:
        answer = session.get("guess_answer")
        if not answer:
            return jsonify({"error": "请先开始游戏"}), 400
        guesses_left = session.get("guess_guesses_left", 0)
        if guesses_left <= 0:
            return jsonify({"error": "本局次数已用完"}), 400
        body = request.get_json(silent=True) or {}
        guess_input = (body.get("guess") or "").strip()
        if not guess_input:
            return jsonify({"error": "请输入皇帝姓名或谥/庙号"}), 400
    except Exception as e:
        return jsonify({"error": "请求解析失败: " + str(e)}), 500
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            # 支持按姓名或谥/庙号查询：先姓名（精确、模糊），再谥/庙号（精确、模糊）
            cols = (
                "SELECT overall_rank, era, temple_posthumous_title, name, short_comment, "
                "virtue, wisdom, fitness, beauty, diligence, ambition, dignity, magnanimity, "
                "desire_self_control, personnel_management, national_power, military_diplomacy, "
                "public_support, economy_livelihood, historical_impact, overall_score "
                "FROM emperor_rank "
            )
            cur.execute(cols + "WHERE name = %s LIMIT 1", (guess_input,))
            row = cur.fetchone()
            if not row:
                cur.execute(cols + "WHERE name LIKE %s LIMIT 1", ("%" + guess_input + "%",))
                row = cur.fetchone()
            if not row:
                cur.execute(cols + "WHERE temple_posthumous_title = %s LIMIT 1", (guess_input,))
                row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    if not row:
        return jsonify({"error": "未找到该皇帝，请检查姓名或谥/庙号"}), 404
    try:
        guess_emp = row_to_json(row)
    except Exception as e:
        return jsonify({"error": "数据解析失败: " + str(e)}), 500
    def _fmt_display_val(val, field):
        if val is None or val == "":
            return None
        if field == "overall_rank":
            try:
                return int(val) if isinstance(val, (int, float)) else int(float(val))
            except (TypeError, ValueError):
                return str(val)
        if field in GUESS_HINT_FIELDS:
            try:
                return float(val) if isinstance(val, (int, float)) else float(val)
            except (TypeError, ValueError):
                return str(val)
        return str(val) if not isinstance(val, (int, float)) else (int(val) if val == int(val) else float(val))

    comparison = []
    for f in GUESS_COMPARE_FIELDS:
        try:
            res = _compare_value(f, guess_emp.get(f), answer.get(f))
        except Exception:
            res = "correct"
        v = _fmt_display_val(guess_emp.get(f), f)
        comparison.append({"field": f, "label": GUESS_FIELD_LABELS[f], "result": res, "value": v})
    guesses_left -= 1
    session["guess_guesses_left"] = guesses_left
    gr, ar = guess_emp.get("overall_rank"), answer.get("overall_rank")
    try:
        won = gr is not None and ar is not None and int(gr) == int(ar)
    except (TypeError, ValueError):
        won = gr == ar
    if won or guesses_left <= 0:
        session.pop("guess_answer", None)
        session.pop("guess_guesses_left", None)
        session.pop("guess_hint_field", None)
    return jsonify({
        "comparison": comparison,
        "guess_name": guess_emp.get("name"),
        "guess_rank": guess_emp.get("overall_rank"),
        "won": won,
        "guesses_left": guesses_left,
        "answer": (answer if (won or guesses_left <= 0) else None),
    })


@app.route("/api/guess/giveup", methods=["POST"])
def api_guess_giveup():
    """放弃本局，返回当前答案并清空 session。"""
    answer = session.get("guess_answer")
    if not answer:
        return jsonify({"error": "没有进行中的对局"}), 400
    session.pop("guess_answer", None)
    session.pop("guess_guesses_left", None)
    session.pop("guess_hint_field", None)
    return jsonify({"answer": answer})


@app.route("/api/guess/names", methods=["GET"])
def api_guess_names():
    """返回所有皇帝姓名列表，供前端联想输入。"""
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            cur.execute("SELECT name FROM emperor_rank ORDER BY overall_rank")
            rows = cur.fetchall()
            names = [r["name"] if isinstance(r, dict) else r[0] for r in rows]
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"data": names})


@app.route("/api/emperors", methods=["GET"])
def api_emperors():
    """GET /api/emperors?page=1&per_page=50&sort=overall_score&order=desc 或 sort=virtue,wisdom,fitness&order=desc,asc,desc"""
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(100, max(1, request.args.get("per_page", 50, type=int)))
    sort = request.args.get("sort", "overall_rank")
    order = request.args.get("order", "asc")
    era = request.args.get("era", "").strip()
    search = request.args.get("search", "").strip()

    order_clause, order_params = _parse_multi_sort(sort, order)

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


def _emperors_where_order():
    """与 api_emperors 一致的筛选与排序，返回 (where_sql, order_clause, params, order_params)。"""
    sort = request.args.get("sort", "overall_rank")
    order = request.args.get("order", "asc")
    era = request.args.get("era", "").strip()
    search = request.args.get("search", "").strip()
    order_clause, order_params = _parse_multi_sort(sort, order)
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
    return where_sql, order_clause, params, order_params


@app.route("/api/emperors/export", methods=["GET"])
def api_emperors_export():
    """按当前筛选/排序导出全部结果为 CSV（query 参数同 /api/emperors）。"""
    where_sql, order_clause, params, order_params = _emperors_where_order()
    try:
        conn, cursor_factory = get_connection()
        cur = cursor_factory(conn)
        try:
            list_sql = (
                "SELECT overall_rank, era, temple_posthumous_title, name, short_comment, "
                "virtue, wisdom, fitness, beauty, diligence, ambition, dignity, magnanimity, "
                "desire_self_control, personnel_management, national_power, military_diplomacy, "
                "public_support, economy_livelihood, historical_impact, overall_score "
                "FROM emperor_rank " + where_sql + " " + order_clause
            )
            cur.execute(list_sql, params + order_params)
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    buf = io.StringIO()
    writer = csv.writer(buf)
    headers = [
        "overall_rank", "era", "temple_posthumous_title", "name", "short_comment",
        "virtue", "wisdom", "fitness", "beauty", "diligence", "ambition", "dignity", "magnanimity",
        "desire_self_control", "personnel_management", "national_power", "military_diplomacy",
        "public_support", "economy_livelihood", "historical_impact", "overall_score"
    ]
    writer.writerow(headers)
    for r in rows:
        row = r if isinstance(r, dict) else dict(zip(headers, r))
        writer.writerow([row.get(h) if row.get(h) is not None else "" for h in headers])
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=emperor_rank_export.csv"}
    )


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

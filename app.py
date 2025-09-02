# app.py
import streamlit as st
import sqlite3
from datetime import date, datetime

DB_FILE = "tasks.db"

# -----------------------------
# DB初期化（既存データを壊さない）
# -----------------------------
def ensure_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT,
        priority TEXT,
        deadline TEXT,
        completed INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

# -----------------------------
# DB操作
# -----------------------------
def get_tasks(category_filter="全て"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    order_case = """
      CASE priority
        WHEN '高' THEN 3
        WHEN '中' THEN 2
        WHEN '低' THEN 1
        ELSE 0
      END DESC
    """
    if category_filter == "全て":
        c.execute(f"SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 ORDER BY {order_case}, deadline ASC, title ASC")
    else:
        c.execute(f"SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 AND category=? ORDER BY {order_case}, deadline ASC, title ASC", (category_filter,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_task(category, title, content, priority, deadline):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (category, title, content, priority, deadline, completed) VALUES (?, ?, ?, ?, ?, 0)",
              (category, title, content, priority, deadline))
    conn.commit()
    conn.close()

def update_task(task_id, category, title, content, priority, deadline, completed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET category=?, title=?, content=?, priority=?, deadline=?, completed=? WHERE id=?",
              (category, title, content, priority, deadline, completed, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# -----------------------------
# セッション初期化（選択状態など）
# -----------------------------
if "edit_task_id" not in st.session_state:
    st.session_state["edit_task_id"] = None
if "category_input" not in st.session_state:
    st.session_state["category_input"] = "仕事"
if "title_input" not in st.session_state:
    st.session_state["title_input"] = ""
if "content_input" not in st.session_state:
    st.session_state["content_input"] = ""
if "priority_input" not in st.session_state:
    st.session_state["priority_input"] = "中"
if "deadline_input" not in st.session_state:
    st.session_state["deadline_input"] = date.today()
if "completed_input" not in st.session_state:
    st.session_state["completed_input"] = False

# -----------------------------
# UI
# -----------------------------
ensure_db()
st.title("タスク管理（UI固め版）")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリを選択", categories)

# 中段：タスク一覧（5行表示、スクロール可能）
st.subheader("タスク一覧（未完了のみ）")
tasks = get_tasks(selected_category)
if not tasks:
    st.info("未完了のタスクはありません。")
else:
    # 最大5行表示、超える場合はスクロール
    display_limit = 5
    for idx, t in enumerate(tasks):
        if idx >= display_limit:
            break
        task_id, category, title, content, priority, deadline = t
        col_left, col_btn = st.columns([8, 2])
        with col_left:
            st.markdown(f"**{deadline}**  —  **{title}**  \u2003  _{category}_  /  _{priority}_")
            with st.expander("詳細を表示する"):
                st.write(content if content else "(内容なし)")
        with col_btn:
            if st.button("編集", key=f"edit_{task_id}"):
                st.session_state["edit_task_id"] = task_id
                st.session_state["category_input"] = category
                st.session_state["title_input"] = title
                st.session_state["content_input"] = content
                st.session_state["priority_input"] = priority if priority in ["高","中","低"] else "中"
                try:
                    st.session_state["deadline_input"] = datetime.strptime(deadline, "%Y-%m-%d").date()
                except Exception:
                    st.session_state["deadline_input"] = date.today()
                st.session_state["completed_input"] = False

# 下段：タスク追加／編集フォーム
st.subheader("タスク追加／編集")
col_cat = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事","個人開発","その他"].index(st.session_state["category_input"]))
title_w = st.text_input("タイトル", value=st.session_state["title_input"])
content_w = st.text_area("内容", value=st.session_state["content_input"])
priority_w = st.selectbox("重要度", ["高","中","低"], index=["高","中","低"].index(st.session_state["priority_input"]))
deadline_w = st.date_input("締切日", value=st.session_state["deadline_input"])
completed_w = st.checkbox("完了", value=st.session_state["completed_input"])

# ボタン
save_col, delete_col, clear_col = st.columns(3)
with save_col:
    if st.button("保存"):
        if st.session_state["edit_task_id"] is None:
            add_task(col_cat, title_w, content_w, priority_w, deadline_w.isoformat())
            st.session_state["title_input"] = ""
            st.session_state["content_input"] = ""
            st.session_state["priority_input"] = "中"
            st.session_state["deadline_input"] = date.today()
            st.session_state["completed_input"] = False
            st.success("タスクを追加しました。")
        else:
            update_task(st.session_state["edit_task_id"], col_cat, title_w, content_w, priority_w, deadline_w.isoformat(), int(completed_w))
            st.session_state["edit_task_id"] = None
            st.success("タスクを更新しました。")

with delete_col:
    if st.button("削除"):
        if st.session_state["edit_task_id"] is not None:
            delete_task(st.session_state["edit_task_id"])
            st.session_state["edit_task_id"] = None
            st.success("選択中のタスクを削除しました。")
        else:
            st.warning("削除するタスクを一覧から「編集」ボタンで選択してください。")

with clear_col:
    if st.button("フォームクリア"):
        st.session_state["edit_task_id"] = None
        st.session_state["category_input"] = "仕事"
        st.session_state["title_input"] = ""
        st.session_state["content_input"] = ""
        st.session_state["priority_input"] = "中"
        st.session_state["deadline_input"] = date.today()
        st.session_state["completed_input"] = False
        # ここでは st.experimental_rerun() は不要。レンダリングで自動反映

# セッション保持
st.session_state["category_input"] = col_cat
st.session_state["title_input"] = title_w
st.session_state["content_input"] = content_w
st.session_state["priority_input"] = priority_w
st.session_state["deadline_input"] = deadline_w
st.session_state["completed_input"] = completed_w

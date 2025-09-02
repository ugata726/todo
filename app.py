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
st.title("タスク管理（仕様完全版）")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリを選択", categories)

# 中段：タスク一覧（表形式、5行表示＋スクロール）
st.subheader("タスク一覧（未完了のみ）")
tasks = get_tasks(selected_category)

if not tasks:
    st.info("未完了のタスクはありません。")
else:
    # 5行表示＋スクロール
    container = st.container()
    max_rows = 5
    scroll_index = 0
    for idx, t in enumerate(tasks):
        task_id, category, title, content, priority, deadline = t
        if idx >= max_rows:
            break
        cols = container.columns([5, 3, 2, 2])
        cols[0].write(title)
        cols[1].write(category)
        cols[2].write(priority)
        cols[3].write(deadline)
        # 選択ボタンで下段フォームにロード
        if cols[0].button("選択", key=f"select_{task_id}"):
            st.session_state["edit_task_id"] = task_id
            st.session_state["category_input"] = category
            st.session_state["title_input"] = title
            st.session_state["content_input"] = content
            st.session_state["priority_input"] = priority
            try:
                st.session_state["deadline_input"] = datetime.strptime(deadline, "%Y-%m-%d").date()
            except Exception:
                st.session_state["deadline_input"] = date.today()
            st.session_state["completed_input"] = False

# 下段：タスク追加／編集フォーム
st.subheader("タスク追加／編集")
col_cat = st.selectbox("カテゴリ", ["仕事","個人開発","その他"], index=["仕事","個人開発","その他"].index(st.session_state["category_input"]))
title_w = st.text_input("タイトル", value=st.session_state["title_input"])
content_w = st.text_area("内容", value=st.session_state["content_input"])
priority_w = st.selectbox("重要度", ["高","中","低"], index=["高","中","低"].index(st.session_state["priority_input"]))
deadline_w = st.date_input("締切日", value=st.session_state["deadline_input"])
completed_w = st.checkbox("完了", value=st.session_state["completed_input"])

# 保存／削除／クリアボタン
save_col, delete_col, clear_col = st.columns(3)

with save_col:
    if st.button("保存"):
        if st.session_state["edit_task_id"] is None:
            add_task(col_cat, title_w, content_w, priority_w, deadline_w.isoformat())
            st.success("タスクを追加しました。")
        else:
            update_task(st.session_state["edit_task_id"], col_cat, title_w, content_w, priority_w, deadline_w.isoformat(), int(completed_w))
            st.success("タスクを更新しました。")
            st.session_state["edit_task_id"] = None
        # フォームクリア
        st.session_state["title_input"] = ""
        st.session_state["content_input"] = ""
        st.session_state["priority_input"] = "中"
        st.session_state["deadline_input"] = date.today()
        st.session_state["completed_input"] = False

with delete_col:
    if st.button("削除"):
        if st.session_state["edit_task_id"] is not None:
            delete_task(st.session_state["edit_task_id"])
            st.session_state["edit_task_id"] = None
            st.success("選択中のタスクを削除しました。")
        else:
            st.warning("削除するタスクを一覧から選択してください。")

with clear_col:
    if st.button("フォームクリア"):
        st.session_state["edit_task_id"] = None
        st.session_state["category_input"] = "仕事"
        st.session_state["title_input"] = ""
        st.session_state["content_input"] = ""
        st.session_state["priority_input"] = "中"
        st.session_state["deadline_input"] = date.today()
        st.session_state["completed_input"] = False

# セッションに反映
st.session_state["category_input"] = col_cat
st.session_state["title_input"] = title_w
st.session_state["content_input"] = content_w
st.session_state["priority_input"] = priority_w
st.session_state["deadline_input"] = deadline_w
st.session_state["completed_input"] = completed_w

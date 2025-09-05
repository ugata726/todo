# app.py
import streamlit as st
import sqlite3
from datetime import date, datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd
import os

DB_FILE = "tasks.db"

# -----------------------------
# DB操作
# -----------------------------
def ensure_db():
    """DBを初期化（存在しない場合のみ作成）"""
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE tasks (
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

def get_tasks(category_filter="全て"):
    if not os.path.exists(DB_FILE):
        return []
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
# セッション初期化
# -----------------------------
for key, value in {
    "edit_task_id": None,
    "category_input": "仕事",
    "title_input": "",
    "content_input": "",
    "priority_input": "中",
    "deadline_input": date.today(),
    "completed_input": False
}.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -----------------------------
# UI
# -----------------------------
st.title("タスク管理（完全版）")

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリを選択", categories)

# 中段：タスク一覧
st.subheader("タスク一覧（未完了のみ）")
tasks = get_tasks(selected_category)

if not tasks:
    st.info("未完了のタスクはありません。")
else:
    df = pd.DataFrame(tasks, columns=["ID","カテゴリ","タイトル","内容","重要度","締切日"])
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection("single")
    gb.configure_grid_options(domLayout='normal', rowHeight=25, floatingFilter=True)
    gb.configure_column("ID", width=50)
    gb.configure_column("タイトル", width=200)
    gb.configure_column("カテゴリ", width=100)
    gb.configure_column("重要度", width=80)
    gb.configure_column("締切日", width=100)
    gb.configure_column("内容", hide=True)
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=150,
        width='100%',
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True
    )

    # -----------------------------
    # 選択行の安全反映
    # -----------------------------
    selected_rows = grid_response.get('selected_rows')
    if selected_rows is not None and len(selected_rows) > 0:
        sel = selected_rows[0]
        st.session_state["edit_task_id"] = sel.get("ID")
        st.session_state["category_input"] = sel.get("カテゴリ", "仕事")
        st.session_state["title_input"] = sel.get("タイトル", "")
        st.session_state["content_input"] = sel.get("内容", "")
        st.session_state["priority_input"] = sel.get("重要度", "中")
        try:
            st.session_state["deadline_input"] = datetime.strptime(sel.get("締切日", date.today().isoformat()), "%Y-%m-%d").date()
        except:
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

# ボタン操作
save_col, delete_col, clear_col = st.columns(3)

with save_col:
    if st.button("保存"):
        # DBなければ作る
        if not os.path.exists(DB_FILE):
            ensure_db()
        if st.session_state["edit_task_id"] is None:
            add_task(col_cat, title_w, content_w, priority_w, deadline_w.isoformat())
            st.success("タスクを追加しました。")
        else:
            update_task(st.session_state["edit_task_id"], col_cat, title_w, content_w, priority_w, deadline_w.isoformat(), int(completed_w))
            st.session_state["edit_task_id"] = None
            st.success("タスクを更新しました。")
        # フォームクリア
        st.session_state.update({"edit_task_id": None,"category_input":"仕事","title_input":"","content_input":"","priority_input":"中","deadline_input":date.today(),"completed_input":False})

with delete_col:
    if st.button("削除"):
        if st.session_state["edit_task_id"] is not None:
            delete_task(st.session_state["edit_task_id"])
            st.session_state["edit_task_id"] = None
            st.success("選択中のタスクを削除しました。")
            # フォームクリア
            st.session_state.update({"edit_task_id": None,"category_input":"仕事","title_input":"","content_input":"","priority_input":"中","deadline_input":date.today(),"completed_input":False})
        else:
            st.warning("削除するタスクを一覧から選択してください。")

with clear_col:
    if st.button("フォームクリア"):
        st.session_state.update({"edit_task_id": None,"category_input":"仕事","title_input":"","content_input":"","priority_input":"中","deadline_input":date.today(),"completed_input":False})
        st.success("フォームをクリアしました。")

# セッション更新
st.session_state["category_input"] = col_cat
st.session_state["title_input"] = title_w
st.session_state["content_input"] = content_w
st.session_state["priority_input"] = priority_w
st.session_state["deadline_input"] = deadline_w
st.session_state["completed_input"] = completed_w

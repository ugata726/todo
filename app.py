# app.py
import streamlit as st
import sqlite3
from datetime import date

# --- SQLite ローカル DB 接続 ---
conn = sqlite3.connect("todo_local.db", check_same_thread=False)
c = conn.cursor()

# --- テーブル作成（存在しない場合のみ） ---
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT,
    importance TEXT,
    due_date TEXT,
    done INTEGER DEFAULT 0
)
""")
conn.commit()

# --- ページ設定 ---
st.set_page_config(page_title="TODOアプリ UI 固め版", layout="centered")
st.title("TODO アプリ UI 確認用")

# --- タスク一覧（上段） ---
st.subheader("タスク一覧")
c.execute("SELECT id, title, importance, due_date, done FROM tasks ORDER BY due_date ASC, importance DESC")
tasks = c.fetchall()

selected_task_id = None
if tasks:
    options = [f"{t[1]} {'✅' if t[4] else ''}" for t in tasks]
    selected_task_label = st.selectbox("一覧（タスクタイトル）", options)
    idx = options.index(selected_task_label)
    selected_task_id = tasks[idx][0]

    # 選択タスク詳細表示（下段）
    task = tasks[idx]
    st.markdown(f"**タイトル:** {task[1]}")
    st.markdown(f"**重要度:** {task[2]}")
    st.markdown(f"**締切日:** {task[3]}")
    done = st.checkbox("完了", value=bool(task[4]))
    col1, col2 = st.columns(2)
    with col1:
        if st.button("削除"):
            c.execute("DELETE FROM tasks WHERE id=?", (task[0],))
            conn.commit()
            st.experimental_rerun()
    with col2:
        if done != bool(task[4]):
            c.execute("UPDATE tasks SET done=? WHERE id=?", (int(done), task[0]))
            conn.commit()
            st.experimental_rerun()
else:
    st.info("タスクはありません。")

# --- タスク追加 / 編集（下段） ---
st.subheader("タスク追加 / 編集")
with st.form("task_form", clear_on_submit=True):
    title = st.text_input("タイトル")
    content = st.text_area("内容")
    importance = st.radio("重要度", ["最優先", "優先", "通常"])
    due_date = st.date_input("締切日", value=date.today())
    submitted = st.form_submit_button("追加")

    if submitted and title:
        c.execute("INSERT INTO tasks (title, content, importance, due_date) VALUES (?, ?, ?, ?)",
                  (title, content, importance, due_date.isoformat()))
        conn.commit()
        st.success(f"タスク「{title}」を追加しました！")
        st.experimental_rerun()

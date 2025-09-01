# app.py
import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="TODO App", layout="wide")

# --- DB準備 ---
conn = sqlite3.connect("todo.db", check_same_thread=False)
c = conn.cursor()
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

# --- UI構成 ---
st.title("TODO App (UI 固め用)")

# メニュー（固定）
menu_options = ["仕事", "個人開発", "その他"]
selected_menu = st.selectbox("メニュー", menu_options)

# --- 中段：タスク一覧 ---
st.subheader("タスク一覧")
c.execute("""
SELECT id, title, content, importance, due_date, done
FROM tasks
ORDER BY
  CASE importance
    WHEN '最優先' THEN 1
    WHEN '優先' THEN 2
    ELSE 3
  END,
  due_date ASC
""")
tasks = c.fetchall()

# スクロールバー付きの一覧表示
if tasks:
    for t in tasks[:5]:  # 5件まで表示
        id_, title, content, importance, due_date, done = t
        st.text(f"{title} ({importance}) 期限:{due_date} 完了:{bool(done)}")
else:
    st.write("タスクはありません")

# --- 下段：タスク追加／編集 ---
st.subheader("タスク追加／編集")
with st.form(key="task_form"):
    title_input = st.text_input("タイトル")
    content_input = st.text_area("内容")
    importance_input = st.radio("重要度", ["最優先", "優先", "通常"])
    due_date_input = st.date_input("期限日", datetime.today())
    submit_button = st.form_submit_button("追加")

if submit_button:
    c.execute("""
        INSERT INTO tasks (title, content, importance, due_date)
        VALUES (?, ?, ?, ?)
    """, (title_input, content_input, importance_input, due_date_input.strftime("%Y-%m-%d")))
    conn.commit()
    st.success("タスクを追加しました！")
    st.experimental_rerun()

# --- タスク削除／完了チェック ---
for t in tasks[:5]:
    id_, title, content, importance, due_date, done = t
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button(f"完了:{title}", key=f"done_{id_}"):
            c.execute("UPDATE tasks SET done=1 WHERE id=?", (id_,))
            conn.commit()
            st.experimental_rerun()
    with col2:
        if st.button(f"削除:{title}", key=f"del_{id_}"):
            c.execute("DELETE FROM tasks WHERE id=?", (id_,))
            conn.commit()
            st.experimental_rerun()

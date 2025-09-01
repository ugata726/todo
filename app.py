# app.py
import streamlit as st
import sqlite3
from datetime import date

# --- DB接続 ---
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    content TEXT,
    importance TEXT,
    due_date TEXT
)
""")
conn.commit()

# --- 固定カテゴリ ---
CATEGORIES = ["仕事", "個人開発", "その他"]
IMPORTANCE = ["最優先", "優先", "通常"]

# --- UI構成 ---
st.title("TODOアプリ（UI固め用）")

# 上段：タスク追加／編集フォーム
st.subheader("タスク追加／編集")
with st.form("task_form", clear_on_submit=False):
    selected_id = st.number_input("編集用ID（新規追加は空白）", min_value=0, step=1, value=0)
    category = st.selectbox("カテゴリ", CATEGORIES)
    title = st.text_input("タスクタイトル")
    content = st.text_area("タスク内容")
    importance = st.radio("重要度", IMPORTANCE)
    due_date = st.date_input("締切日", value=date.today())
    submitted = st.form_submit_button("保存")

    if submitted:
        if selected_id == 0:
            # 新規追加
            c.execute(
                "INSERT INTO tasks (category, title, content, importance, due_date) VALUES (?, ?, ?, ?, ?)",
                (category, title, content, importance, due_date)
            )
        else:
            # 編集
            c.execute(
                "UPDATE tasks SET category=?, title=?, content=?, importance=?, due_date=? WHERE id=?",
                (category, title, content, importance, due_date, selected_id)
            )
        conn.commit()
        st.success("タスクを保存しました！")

# 中段：タスク一覧
st.subheader("タスク一覧")
c.execute("SELECT id, category, title, importance, due_date FROM tasks ORDER BY due_date ASC, importance ASC")
tasks = c.fetchall()
if tasks:
    import pandas as pd
    df = pd.DataFrame(tasks, columns=["ID", "カテゴリ", "タイトル", "重要度", "締切日"])
    st.dataframe(df, height=200)
else:
    st.info("タスクはありません。")

# 下段：選択タスク詳細
st.subheader("選択タスク詳細")
task_id = st.number_input("表示したいタスクIDを入力", min_value=0, step=1, value=0)
if task_id > 0:
    c.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    t = c.fetchone()
    if t:
        st.write(f"**ID:** {t[0]}")
        st.write(f"**カテゴリ:** {t[1]}")
        st.write(f"**タイトル:** {t[2]}")
        st.write(f"**内容:** {t[3]}")
        st.write(f"**重要度:** {t[4]}")
        st.write(f"**締切日:** {t[5]}")
        if st.button("削除"):
            c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
            conn.commit()
            st.success("タスクを削除しました！")

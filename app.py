# app.py
import streamlit as st
import sqlite3
from datetime import datetime

# ----- DBセットアップ -----
conn = sqlite3.connect("todo_ui.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT,
    title TEXT,
    content TEXT,
    importance TEXT,
    due_date TEXT,
    done INTEGER DEFAULT 0
)
""")
conn.commit()

# ----- 固定カテゴリ -----
CATEGORIES = ["仕事", "個人開発", "その他"]
IMPORTANCE_LEVELS = ["最優先", "優先", "通常"]

st.title("UI 固め用 TODOアプリ")

# ----- 上段：カテゴリ選択 -----
selected_category = st.selectbox("カテゴリ選択", CATEGORIES)

# ----- 中段：タスク一覧 -----
st.subheader("タスク一覧")
# DBからタスク取得（カテゴリフィルタ）
c.execute("""
SELECT id, category, title, due_date, importance
FROM tasks
WHERE category=?
ORDER BY due_date ASC,
         CASE importance
            WHEN '最優先' THEN 1
            WHEN '優先' THEN 2
            ELSE 3
         END ASC,
         title ASC
""", (selected_category,))
tasks = c.fetchall()

# 一覧表示用のテーブル作成
if tasks:
    st.dataframe(
        [{"ID": t[0], "カテゴリ": t[1], "タイトル": t[2], "締切日": t[3], "重要度": t[4]} for t in tasks],
        height=200
    )
else:
    st.write("タスクがありません")

# ----- 下段：選択タスク編集・削除／新規追加 -----
st.subheader("タスク追加／編集")

# 選択タスク
task_ids = [t[0] for t in tasks]
task_selection = st.selectbox("編集対象タスクを選択（新規追加は未選択）", ["新規追加"] + task_ids)

if task_selection == "新規追加":
    title_input = st.text_input("タイトル")
    content_input = st.text_area("内容")
    importance_input = st.radio("重要度", IMPORTANCE_LEVELS)
    due_date_input = st.date_input("締切日", datetime.today())
    
    if st.button("追加"):
        c.execute("INSERT INTO tasks (category, title, content, importance, due_date) VALUES (?, ?, ?, ?, ?)",
                  (selected_category, title_input, content_input, importance_input, due_date_input))
        conn.commit()
        st.success("タスクを追加しました！")
        st.experimental_rerun()
else:
    # 選択タスクの情報読み込み
    c.execute("SELECT title, content, importance, due_date FROM tasks WHERE id=?", (task_selection,))
    task_data = c.fetchone()
    title_input = st.text_input("タイトル", task_data[0])
    content_input = st.text_area("内容", task_data[1])
    importance_input = st.radio("重要度", IMPORTANCE_LEVELS, index=IMPORTANCE_LEVELS.index(task_data[2]))
    due_date_input = st.date_input("締切日", datetime.strptime(task_data[3], "%Y-%m-%d"))
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("更新"):
            c.execute("UPDATE tasks SET title=?, content=?, importance=?, due_date=? WHERE id=?",
                      (title_input, content_input, importance_input, due_date_input, task_selection))
            conn.commit()
            st.success("タスクを更新しました！")
            st.experimental_rerun()
    with col2:
        if st.button("削除"):
            c.execute("DELETE FROM tasks WHERE id=?", (task_selection,))
            conn.commit()
            st.success("タスクを削除しました！")
            st.experimental_rerun()

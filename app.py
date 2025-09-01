# app.py
import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="TODOアプリ UI固め版", layout="centered")

# --- DB 初期化 ---
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

# --- カテゴリ ---
CATEGORIES = ["仕事", "個人開発", "その他"]

# --- 上段：カテゴリ選択 ---
st.title("TODOアプリ UI固め版")
selected_category = st.selectbox("カテゴリ選択", CATEGORIES)

# --- データ取得 ---
c.execute("""
SELECT id, category, title, content, importance, due_date, done
FROM tasks
WHERE category = ?
ORDER BY due_date ASC,
         CASE importance
           WHEN '最優先' THEN 1
           WHEN '優先' THEN 2
           WHEN '通常' THEN 3
           ELSE 4
         END ASC
""", (selected_category,))
tasks = c.fetchall()

# --- 中段：タスク一覧 ---
st.subheader("タスク一覧")
if tasks:
    # タスク一覧テーブル作成
    table_data = []
    for t in tasks:
        table_data.append({
            "ID": t[0],
            "カテゴリ": t[1],
            "タイトル": t[2],
            "重要度": t[4],
            "締切日": t[5],
            "完了": "✅" if t[6] else ""
        })
    st.dataframe(table_data, height=200)
else:
    st.write("タスクは存在しません。")

# --- 下段：タスク追加／編集／削除 ---
st.subheader("タスク追加／編集／削除")
task_ids = [t[0] for t in tasks]
selected_task_id = st.selectbox("編集するタスクを選択", ["新規追加"] + task_ids)

if selected_task_id == "新規追加":
    edit_task = {"title": "", "content": "", "importance": "通常", "due_date": ""}
else:
    for t in tasks:
        if t[0] == selected_task_id:
            edit_task = {"title": t[2], "content": t[3], "importance": t[4], "due_date": t[5]}

title = st.text_input("タイトル", value=edit_task["title"])
content = st.text_area("内容", value=edit_task["content"])
importance = st.radio("重要度", ["最優先", "優先", "通常"], index=["最優先", "優先", "通常"].index(edit_task["importance"]))
due_date = st.date_input("締切日", value=datetime.today() if edit_task["due_date"]=="" else datetime.strptime(edit_task["due_date"], "%Y-%m-%d"))

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("保存"):
        if selected_task_id == "新規追加":
            c.execute("INSERT INTO tasks (category, title, content, importance, due_date) VALUES (?, ?, ?, ?, ?)",
                      (selected_category, title, content, importance, due_date.strftime("%Y-%m-%d")))
            conn.commit()
            st.success("タスクを追加しました！")
        else:
            c.execute("UPDATE tasks SET title=?, content=?, importance=?, due_date=? WHERE id=?",
                      (title, content, importance, due_date.strftime("%Y-%m-%d"), selected_task_id))
            conn.commit()
            st.success("タスクを更新しました！")
        st.experimental_rerun()
with col2:
    if st.button("削除") and selected_task_id != "新規追加":
        c.execute("DELETE FROM tasks WHERE id=?", (selected_task_id,))
        conn.commit()
        st.success("タスクを削除しました！")
        st.experimental_rerun()
with col3:
    if st.button("完了/未完了切替") and selected_task_id != "新規追加":
        for t in tasks:
            if t[0] == selected_task_id:
                new_done = 0 if t[6] else 1
                c.execute("UPDATE tasks SET done=? WHERE id=?", (new_done, selected_task_id))
                conn.commit()
                st.experimental_rerun()

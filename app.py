# app.py
import streamlit as st
import sqlite3
from datetime import datetime

# DB接続
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()

# テーブル作成（存在しない場合のみ）
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

# --- 上段：カテゴリ選択 ---
st.title("TODO アプリ (UI固め版)")

CATEGORIES = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", CATEGORIES)

# --- 中段：タスク一覧 ---
st.subheader("タスク一覧")

def get_tasks(category):
    if category == "全て":
        c.execute("SELECT id, category, title, importance, due_date FROM tasks ORDER BY due_date ASC, importance DESC")
    else:
        c.execute("SELECT id, category, title, importance, due_date FROM tasks WHERE category=? ORDER BY due_date ASC, importance DESC", (category,))
    return c.fetchall()

tasks = get_tasks(selected_category)

if tasks:
    for task in tasks:
        st.write(f"{task[4]} | {task[2]} | {task[3]} | {task[1]}")
else:
    st.write("タスクはありません。")

# --- 下段：タスク追加／編集／削除 ---
st.subheader("タスク追加 / 編集 / 削除")

with st.form(key="task_form"):
    # 選択タスクID（編集用）
    task_to_edit = st.number_input("編集するタスクID (新規の場合は0)", min_value=0, step=1, value=0)
    category = st.selectbox("カテゴリ", CATEGORIES[1:])
    title = st.text_input("タイトル")
    content = st.text_area("内容")
    importance = st.radio("重要度", ["最優先", "優先", "通常"])
    due_date = st.date_input("締切日", datetime.today())
    submit_button = st.form_submit_button("保存")

if submit_button:
    if task_to_edit == 0:
        # 新規追加
        c.execute("INSERT INTO tasks (category, title, content, importance, due_date) VALUES (?, ?, ?, ?, ?)",
                  (category, title, content, importance, due_date.strftime("%Y-%m-%d")))
        st.success("タスクを追加しました！")
    else:
        # 編集
        c.execute("UPDATE tasks SET category=?, title=?, content=?, importance=?, due_date=? WHERE id=?",
                  (category, title, content, importance, due_date.strftime("%Y-%m-%d"), task_to_edit))
        st.success("タスクを更新しました！")
    conn.commit()
    st.experimental_rerun()

# 削除フォーム
with st.form(key="delete_form"):
    delete_id = st.number_input("削除するタスクID", min_value=0, step=1, value=0)
    delete_button = st.form_submit_button("削除")

if delete_button and delete_id != 0:
    c.execute("DELETE FROM tasks WHERE id=?", (delete_id,))
    conn.commit()
    st.success("タスクを削除しました！")
    st.experimental_rerun()

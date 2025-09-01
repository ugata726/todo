# app.py
import streamlit as st
import sqlite3
from datetime import date

# DB接続（ローカルSQLite）
conn = sqlite3.connect("tasks.db", check_same_thread=False)
c = conn.cursor()

# テーブル作成（存在しなければ）
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
st.title("TODOアプリ (UI固め版)")
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリ選択", categories)

# --- 中段：タスク一覧 ---
st.subheader("タスク一覧")
if selected_category == "全て":
    c.execute("SELECT id, category, title, due_date, importance FROM tasks ORDER BY due_date ASC, importance DESC")
else:
    c.execute("SELECT id, category, title, due_date, importance FROM tasks WHERE category=? ORDER BY due_date ASC, importance DESC", (selected_category,))
tasks = c.fetchall()

if tasks:
    for t in tasks:
        st.write(f"{t[1]} | {t[3]} | {t[2]} | {t[4]}")
else:
    st.write("タスクはありません")

# --- 下段：タスク操作フォーム ---
st.subheader("タスク追加／編集／削除")
with st.form("task_form"):
    task_id = st.number_input("編集するタスクID（新規追加は0）", min_value=0, step=1)
    category = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"])
    title = st.text_input("タイトル")
    content = st.text_area("内容")
    importance = st.radio("重要度", ["最優先", "優先", "通常"])
    due_date = st.date_input("締切日", value=date.today())

    submitted = st.form_submit_button("実行")
    if submitted:
        if task_id == 0:
            # 新規追加
            c.execute("INSERT INTO tasks (category, title, content, importance, due_date) VALUES (?, ?, ?, ?, ?)",
                      (category, title, content, importance, due_date))
            conn.commit()
            st.success("タスクを追加しました！")
        else:
            # 編集
            c.execute("UPDATE tasks SET category=?, title=?, content=?, importance=?, due_date=? WHERE id=?",
                      (category, title, content, importance, due_date, task_id))
            conn.commit()
            st.success("タスクを更新しました！")
        st.experimental_rerun()

# --- タスク削除フォーム ---
with st.form("delete_form"):
    del_id = st.number_input("削除するタスクID", min_value=0, step=1, key="del")
    del_submitted = st.form_submit_button("削除")
    if del_submitted and del_id > 0:
        c.execute("DELETE FROM tasks WHERE id=?", (del_id,))
        conn.commit()
        st.success("タスクを削除しました！")
        st.experimental_rerun()

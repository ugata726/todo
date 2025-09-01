import streamlit as st
import sqlite3

# データベース接続
conn = sqlite3.connect("todo.db")
c = conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, task TEXT, category TEXT, deadline TEXT, done INTEGER)')

# UI
st.title("TODOアプリ")

menu = ["追加", "一覧"]
choice = st.sidebar.selectbox("メニュー", menu)

if choice == "追加":
    task = st.text_input("タスク名")
    category = st.text_input("カテゴリ")
    deadline = st.date_input("期限")
    if st.button("追加"):
        c.execute("INSERT INTO tasks(task, category, deadline, done) VALUES (?, ?, ?, 0)",
                  (task, category, deadline))
        conn.commit()
        st.success("タスクを追加しました！")

elif choice == "一覧":
    c.execute("SELECT * FROM tasks")
    rows = c.fetchall()
    for r in rows:
        checked = st.checkbox(f"{r[1]} | {r[2]} | {r[3]}", value=bool(r[4]))
        if checked != bool(r[4]):
            c.execute("UPDATE tasks SET done=? WHERE id=?", (int(checked), r[0]))
            conn.commit()

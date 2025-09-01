import streamlit as st
import sqlite3
import pandas as pd

# データベース接続
conn = sqlite3.connect("todo.db", check_same_thread=False)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY,
    task TEXT,
    category TEXT,
    deadline TEXT,
    done INTEGER
)
''')

st.title("TODOアプリ")

menu = ["追加", "一覧", "進捗"]
choice = st.sidebar.selectbox("メニュー", menu)

# --- タスク追加 ---
if choice == "追加":
    task = st.text_input("タスク名")
    category = st.text_input("カテゴリ")
    deadline = st.date_input("期限")
    if st.button("追加"):
        c.execute(
            "INSERT INTO tasks(task, category, deadline, done) VALUES (?, ?, ?, 0)",
            (task, category, str(deadline))
        )
        conn.commit()
        st.success("タスクを追加しました！")

# --- タスク一覧・編集・削除 ---
elif choice == "一覧":
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    if df.empty:
        st.info("タスクがありません。")
    else:
        for i, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            with col1:
                new_task = st.text_input("タスク", row["task"], key=f"task_{row['id']}")
            with col2:
                new_cat = st.text_input("カテゴリ", row["category"], key=f"cat_{row['id']}")
            with col3:
                new_dead = st.date_input("期限", pd.to_datetime(row["deadline"]), key=f"dead_{row['id']}")
            with col4:
                checked = st.checkbox("完了", value=bool(row["done"]), key=f"done_{row['id']}")
            with col5:
                if st.button("削除", key=f"del_{row['id']}"):
                    c.execute("DELETE FROM tasks WHERE id=?", (row["id"],))
                    conn.commit()
                    st.success("タスクを削除しました！")

            # --- 更新処理 ---
            if (new_task != row["task"] or
                new_cat != row["category"] or
                str(new_dead) != row["deadline"] or
                int(checked) != row["done"]):
                c.execute(
                    "UPDATE tasks SET task=?, category=?, deadline=?, done=? WHERE id=?",
                    (new_task, new_cat, str(new_dead), int(checked), row["id"])
                )
                conn.commit()

# --- 進捗表示 ---
elif choice == "進捗":
    df = pd.read_sql_query("SELECT * FROM tasks", conn)
    if df.empty:
        st.info("タスクがありません。")
    else:
        total = len(df)
        done = df["done"].sum()
        st.metric("完了数", f"{done}/{total}")
        st.progress(done / total)

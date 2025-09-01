# app.py
import streamlit as st
import sqlite3
from datetime import date

# -----------------------
# DB 初期化（UI確認用）
# -----------------------
conn = sqlite3.connect("todo.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu TEXT,
    title TEXT,
    content TEXT,
    importance TEXT,
    due_date TEXT,
    done INTEGER DEFAULT 0
)
""")
conn.commit()

# -----------------------
# 固定メニュー
# -----------------------
MENUS = ["仕事", "個人開発", "その他"]

# -----------------------
# 画面構成
# -----------------------
st.set_page_config(page_title="TODOアプリ", layout="wide")

# 上段: メニュー（サイドバー）
st.sidebar.title("メニュー")
selected_menu = st.sidebar.radio("選択メニュー", MENUS)

# -----------------------
# 中段: タスクリスト（最大5件表示、スクロール対応）
# -----------------------
st.header("タスクリスト")
c.execute("""
SELECT id, menu, title, content, importance, due_date, done 
FROM tasks 
WHERE menu = ? 
ORDER BY 
    CASE importance 
        WHEN '最優先' THEN 1
        WHEN '優先' THEN 2
        ELSE 3
    END,
    due_date ASC
""", (selected_menu,))
rows = c.fetchall()

if rows:
    # スクロール可能領域
    container = st.container()
    for r in rows[:5]:  # 最大5行表示
        done_checkbox = st.checkbox(
            f"{r[2]}",  # タイトルのみ
            value=bool(r[6]),
            key=f"done_{r[0]}"
        )
        if done_checkbox != bool(r[6]):
            c.execute("UPDATE tasks SET done = ? WHERE id = ?", (int(done_checkbox), r[0]))
            conn.commit()
else:
    st.info("タスクはまだ登録されていません。")

# -----------------------
# 下段: タスク追加／編集フォーム
# -----------------------
st.header("タスク追加 / 編集")
with st.form("task_form", clear_on_submit=True):
    title = st.text_input("タイトル")
    content = st.text_area("内容")
    importance = st.radio("重要度", ["最優先", "優先", "通常"])
    due_date = st.date_input("締切日", value=date.today())
    submitted = st.form_submit_button("追加")
    if submitted:
        if title.strip() != "":
            c.execute(
                "INSERT INTO tasks (menu, title, content, importance, due_date) VALUES (?, ?, ?, ?, ?)",
                (selected_menu, title, content, importance, due_date.isoformat())
            )
            conn.commit()
            st.success(f"タスク「{title}」を追加しました！")
        else:
            st.warning("タイトルを入力してください")

# -----------------------
# 下段: 選択タスク詳細
# -----------------------
st.header("タスク詳細")
task_ids = [r[0] for r in rows[:5]]
if task_ids:
    selected_task_id = st.selectbox(
        "選択タスク", 
        task_ids, 
        format_func=lambda x: f"{next(r[2] for r in rows if r[0]==x)}"
    )
    task = next(r for r in rows if r[0]==selected_task_id)
    st.write(f"**タイトル:** {task[2]}")
    st.write(f"**内容:** {task[3]}")
    st.write(f"**メニュー:** {task[1]}")
    st.write(f"**重要度:** {task[4]}")
    st.write(f"**締切日:** {task[5]}")
    delete = st.button("削除")
    if delete:
        c.execute("DELETE FROM tasks WHERE id = ?", (selected_task_id,))
        conn.commit()
        st.success(f"タスク「{task[2]}」を削除しました！")
        st.experimental_rerun()

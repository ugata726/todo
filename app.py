# app.py
import streamlit as st  # Streamlit UIライブラリ
import sqlite3  # SQLite DB操作用
from datetime import date, datetime  # 日付操作用
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode  # 高機能グリッド表示

DB_FILE = "tasks.db"  # DBファイル名

# -----------------------------
# DB初期化（既存データを壊さない）
# -----------------------------
def ensure_db():
    conn = sqlite3.connect(DB_FILE)  # DB接続
    c = conn.cursor()  # カーソル取得
    c.execute("""  # tasksテーブルを作成（存在しない場合のみ）
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        title TEXT,
        content TEXT,
        priority TEXT,
        deadline TEXT,
        completed INTEGER DEFAULT 0
    )
    """)
    conn.commit()  # コミット
    conn.close()  # 接続閉じる

# -----------------------------
# DB操作
# -----------------------------
def get_tasks(category_filter="全て"):
    conn = sqlite3.connect(DB_FILE)  # DB接続
    c = conn.cursor()
    order_case = """
      CASE priority
        WHEN '高' THEN 3
        WHEN '中' THEN 2
        WHEN '低' THEN 1
        ELSE 0
      END DESC
    """
    if category_filter == "全て":  # カテゴリ指定なし
        c.execute(f"SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 ORDER BY {order_case}, deadline ASC, title ASC")
    else:  # 特定カテゴリのみ
        c.execute(f"SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 AND category=? ORDER BY {order_case}, deadline ASC, title ASC", (category_filter,))
    rows = c.fetchall()  # 全件取得
    conn.close()  # 接続閉じる
    return rows  # 取得結果返す

def add_task(category, title, content, priority, deadline):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (category, title, content, priority, deadline, completed) VALUES (?, ?, ?, ?, ?, 0)",
              (category, title, content, priority, deadline))
    conn.commit()
    conn.close()

def update_task(task_id, category, title, content, priority, deadline, completed):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tasks SET category=?, title=?, content=?, priority=?, deadline=?, completed=? WHERE id=?",
              (category, title, content, priority, deadline, completed, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

# -----------------------------
# セッション初期化
# -----------------------------
# 以下、セッションステート初期化。フォーム反映用
if "edit_task_id" not in st.session_state:
    st.session_state["edit_task_id"] = None
if "category_input" not in st.session_state:
    st.session_state["category_input"] = "仕事"
if "title_input" not in st.session_state:
    st.session_state["title_input"] = ""
if "content_input" not in st.session_state:
    st.session_state["content_input"] = ""
if "priority_input" not in st.session_state:
    st.session_state["priority_input"] = "中"
if "deadline_input" not in st.session_state:
    st.session_state["deadline_input"] = date.today()
if "completed_input" not in st.session_state:
    st.session_state["completed_input"] = False

# -----------------------------
# UI
# -----------------------------
ensure_db()  # DB初期化
st.title("タスク管理（完全版）")  # タイトル

# 上段：カテゴリ選択
categories = ["全て", "仕事", "個人開発", "その他"]
selected_category = st.selectbox("カテゴリを選択", categories)

# 中段：タスク一覧
st.subheader("タスク一覧（未完了のみ）")
tasks = get_tasks(selected_category)

if not tasks:  # タスクが0件ならメッセージ表示
    st.info("未完了のタスクはありません。")
else:
    import pandas as pd  # DataFrame化用
    df = pd.DataFrame(tasks, columns=["ID","カテゴリ","タイトル","内容","重要度","締切日"])
    
    # AgGrid 設定
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection("single")  # 単一選択
    gb.configure_grid_options(domLayout='normal')
    gb.configure_grid_options(rowHeight=25)
    gb.configure_grid_options(floatingFilter=True)
    gb.configure_column("ID", headerName="ID", width=50)
    gb.configure_column("タイトル", headerName="タイトル", width=200)
    gb.configure_column("カテゴリ", headerName="カテゴリ", width=100)
    gb.configure_column("重要度", headerName="重要度", width=80)
    gb.configure_column("締切日", headerName="締切日", width=100)
    gb.configure_column("内容", hide=True)  # 内容は下段フォーム表示
    gb.configure_grid_options(domLayout='normal')
    grid_options = gb.build()
    
    # AgGrid表示
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=150,
        width='100%',
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True
    )
    
    # -----------------------------
    # 修正箇所: ValueError防止
    # -----------------------------
    selected_rows = grid_response.get('selected_rows', [])  # Noneの場合に備えて get() を使用
    if selected_rows:  # 選択されていればフォームに反映
        sel = selected_rows[0]
        st.session_state["edit_task_id"] = sel["ID"]
        st.session_state["category_input"] = sel["カテゴリ"]
        st.session_state["title_input"] = sel["タイトル"]
        st.session_state["content_input"] = sel["内容"]
        st.session_state["priority_input"] = sel["重要度"] if sel["重要度"] in ["高","中","低"] else "中"
        try:
            st.session_state["deadline_input"] = datetime.strptime(sel["締切日"], "%Y-%m-%d").date()
        except:
            st.session_state["deadline_input"] = date.today()
        st.session_state["completed_input"] = False

# 下段：タスク追加／編集フォーム
st.subheader("タスク追加／編集")
col_cat = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事","個人開発","その他"].index(st.session_state["category_input"]))
title_w = st.text_input("タイトル", value=st.session_state["title_input"])
content_w = st.text_area("内容", value=st.session_state["content_input"])
priority_w = st.selectbox("重要度", ["高","中","低"], index=["高","中","低"].index(st.session_state["priority_input"]))
deadline_w = st.date_input("締切日", value=st.session_state["deadline_input"])
completed_w = st.checkbox("完了", value=st.session_state["completed_input"])

# ボタン操作
save_col, delete_col, clear_col = st.columns(3)

with save_col:
    if st.button("保存"):
        if st.session_state["edit_task_id"] is None:
            add_task(col_cat, title_w, content_w, priority_w, deadline_w.isoformat())
            # フォームクリア
            st.session_state.update({"title_input":"","content_input":"","priority_input":"中","deadline_input":date.today(),"completed_input":False})
            st.success("タスクを追加しました。")
        else:
            update_task(st.session_state["edit_task_id"], col_cat, title_w, content_w, priority_w, deadline_w.isoformat(), int(completed_w))
            st.session_state["edit_task_id"] = None
            st.success("タスクを更新しました。")

with delete_col:
    if st.button("削除"):
        if st.session_state["edit_task_id"] is not None:
            delete_task(st.session_state["edit_task_id"])
            st.session_state["edit_task_id"] = None
            st.success("選択中のタスクを削除しました。")
        else:
            st.warning("削除するタスクを一覧から選択してください。")

with clear_col:
    if st.button("フォームクリア"):
        # -----------------------------
        # 修正箇所: experimental_rerunを使わず、フォームクリアを安全に反映
        # -----------------------------
        st.session_state.update({"edit_task_id":None,"category_input":"仕事","title_input":"","content_input":"","priority_input":"中","deadline_input":date.today(),"completed_input":False})

# セッション更新
st.session_state["category_input"] = col_cat
st.session_state["title_input"] = title_w
st.session_state["content_input"] = content_w
st.session_state["priority_input"] = priority_w
st.session_state["deadline_input"] = deadline_w
st.session_state["completed_input"] = completed_w

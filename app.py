# app.py
import streamlit as st  # Streamlit UIライブラリ
import sqlite3  # SQLite DB操作用
from datetime import date, datetime  # 日付操作用
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode  # 高機能グリッド表示
import pandas as pd  # DataFrame化用

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
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # -----------------------------
    # 修正箇所: 並び順を仕様に合わせる（締切日 -> 重要度(高>中>低) -> タイトル）
    # -----------------------------
    order_case = """
      CASE priority
        WHEN '高' THEN 3
        WHEN '中' THEN 2
        WHEN '低' THEN 1
        ELSE 0
      END DESC
    """
    if category_filter == "全て":  # カテゴリ指定なし
        # deadline(昇順) を最優先、その次に priority (高->低)、最後に title
        c.execute(f"SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 ORDER BY deadline ASC, {order_case}, title ASC")
    else:
        c.execute(f"SELECT id, category, title, content, priority, deadline FROM tasks WHERE completed=0 AND category=? ORDER BY deadline ASC, {order_case}, title ASC", (category_filter,))
    rows = c.fetchall()
    conn.close()
    return rows

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
selected_category = st.selectbox("カテゴリを選択", categories, index=categories.index("全て") if "selected_category" not in st.session_state else categories.index(st.session_state.get("selected_category","全て")))
# セッションに選択カテゴリを保持（仕様：セッション管理）
st.session_state["selected_category"] = selected_category

# 中段：タスク一覧（表のタイトル含む）
st.subheader("タスク一覧（未完了のみ）")  # 表のタイトル（仕様に一致）

tasks = get_tasks(selected_category)

if not tasks:
    st.info("未完了のタスクはありません。")
else:
    # DataFrame 作成（列順は仕様通り: ID, タイトル, カテゴリ, 重要度, 締切日）
    df = pd.DataFrame(tasks, columns=["ID","カテゴリ","タイトル","内容","重要度","締切日"])
    # 列並びを変更（仕様: ID、タイトル、カテゴリ、重要度、締切日）
    df = df[["ID","タイトル","カテゴリ","重要度","締切日","内容"]]  # 内容は最後にして非表示にする

    # -----------------------------
    # 修正箇所: AgGrid 行数固定（最大5行を表示、超過時にスクロール）
    # - row_height を明示し、height を計算して与える
    # -----------------------------
    row_height = 30  # 行の高さ（px） - 明示することで環境差を抑える
    rows_to_show = min(5, len(df))
    grid_height = rows_to_show * row_height + 35  # ヘッダー等の余白を加算（実験的な安全余裕）

    # AgGrid 設定
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection("single")  # 単一選択（仕様）
    gb.configure_grid_options(domLayout='normal')
    gb.configure_grid_options(rowHeight=row_height)
    gb.configure_grid_options(floatingFilter=True)
    gb.configure_column("ID", headerName="ID", width=60)
    gb.configure_column("タイトル", headerName="タイトル", width=250)
    gb.configure_column("カテゴリ", headerName="カテゴリ", width=120)
    gb.configure_column("重要度", headerName="重要度", width=90)
    gb.configure_column("締切日", headerName="締切日", width=110)
    gb.configure_column("内容", hide=True)  # 内容は下段フォームで確認・編集（一覧非表示）
    grid_options = gb.build()

    # AgGrid表示
    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        height=grid_height,
        width='100%',
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True
    )

    # -----------------------------
    # 修正箇所: 選択時の安全処理（ValueError / pandas __nonzero__ 対策）
    # - grid_response.get('selected_rows', []) を使い、型変換や例外処理を行う
    # -----------------------------
    selected_rows = grid_response.get('selected_rows', []) or []
    if selected_rows:
        sel = selected_rows[0]
        # ID が float / numpy 型の可能性があるため安全に int に変換
        try:
            st.session_state["edit_task_id"] = int(sel.get("ID"))
        except Exception:
            st.session_state["edit_task_id"] = None
        # その他のフィールドを session_state に反映（存在確認して代替値を用いる）
        st.session_state["category_input"] = sel.get("カテゴリ", "仕事") if sel.get("カテゴリ") in ["仕事","個人開発","その他"] else "仕事"
        st.session_state["title_input"] = sel.get("タイトル", "") or ""
        st.session_state["content_input"] = sel.get("内容", "") or ""
        st.session_state["priority_input"] = sel.get("重要度", "中") if sel.get("重要度") in ["高","中","低"] else "中"
        # 締切日は文字列の可能性があるため、安全にパース
        try:
            raw_deadline = sel.get("締切日")
            if raw_deadline:
                st.session_state["deadline_input"] = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
            else:
                st.session_state["deadline_input"] = date.today()
        except Exception:
            st.session_state["deadline_input"] = date.today()
        # 完了フラグは一覧では表示していない（未完了のみ表示）ので False をセット
        st.session_state["completed_input"] = False

# 下段：タスク追加／編集フォーム
st.subheader("タスク追加／編集")
# フォームの入力順は仕様どおり（カテゴリ、タイトル、内容、重要度、締切日、完了チェック）
col_cat = st.selectbox("カテゴリ", ["仕事", "個人開発", "その他"], index=["仕事","個人開発","その他"].index(st.session_state.get("category_input","仕事")))
title_w = st.text_input("タイトル", value=st.session_state.get("title_input",""))
content_w = st.text_area("内容", value=st.session_state.get("content_input",""))
priority_w = st.selectbox("重要度", ["高","中","低"], index=["高","中","低"].index(st.session_state.get("priority_input","中")))
deadline_w = st.date_input("締切日", value=st.session_state.get("deadline_input", date.today()))
completed_w = st.checkbox("完了", value=st.session_state.get("completed_input", False))

# ボタン操作（保存／削除／フォームクリア）
save_col, delete_col, clear_col = st.columns(3)

with save_col:
    if st.button("保存"):
        # バリデーション（最低限のチェック）
        if not title_w.strip():
            st.warning("タイトルを入力してください。")
        else:
            if st.session_state.get("edit_task_id") is None:
                # 新規追加
                add_task(col_cat, title_w, content_w, priority_w, deadline_w.isoformat())
                # 保存後フォームを初期化（仕様：フォームクリアは自動で反映）
                st.session_state.update({
                    "edit_task_id": None,
                    "category_input": "仕事",
                    "title_input": "",
                    "content_input": "",
                    "priority_input": "中",
                    "deadline_input": date.today(),
                    "completed_input": False
                })
                st.success("タスクを追加しました。")
            else:
                # 編集更新
                update_task(st.session_state["edit_task_id"], col_cat, title_w, content_w, priority_w, deadline_w.isoformat(), int(bool(completed_w)))
                st.session_state["edit_task_id"] = None
                # フォームを初期化（編集終了）
                st.session_state.update({
                    "category_input": "仕事",
                    "title_input": "",
                    "content_input": "",
                    "priority_input": "中",
                    "deadline_input": date.today(),
                    "completed_input": False
                })
                st.success("タスクを更新しました。")

with delete_col:
    if st.button("削除"):
        # 削除は選択中タスクのみ（仕様）
        if st.session_state.get("edit_task_id") is not None:
            delete_task(st.session_state["edit_task_id"])
            # 削除後、セッションをクリアして一覧に反映
            st.session_state.update({
                "edit_task_id": None,
                "category_input": "仕事",
                "title_input": "",
                "content_input": "",
                "priority_input": "中",
                "deadline_input": date.today(),
                "completed_input": False
            })
            st.success("選択中のタスクを削除しました。")
        else:
            st.warning("削除するタスクを一覧から選択してください。")

with clear_col:
    if st.button("フォームクリア"):
        # -----------------------------
        # 修正箇所: experimental_rerunを使わず、フォームクリアを安全に反映（仕様）
        # -----------------------------
        st.session_state.update({
            "edit_task_id": None,
            "category_input": "仕事",
            "title_input": "",
            "content_input": "",
            "priority_input": "中",
            "deadline_input": date.today(),
            "completed_input": False
        })

# セッション更新（フォームの現状態をセッションに反映しておく）
st.session_state["category_input"] = col_cat
st.session_state["title_input"] = title_w
st.session_state["content_input"] = content_w
st.session_state["priority_input"] = priority_w
st.session_state["deadline_input"] = deadline_w
st.session_state["completed_input"] = completed_w

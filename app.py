import streamlit as st
import sqlite3
from datetime import date, datetime
import pandas as pd
from contextlib import closing

st.set_page_config(page_title="TODOアプリ（UI固め）", layout="centered")

# ---------- DB 準備 ----------
DB_PATH = "tasks.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  category   TEXT NOT NULL,
  title      TEXT NOT NULL,
  content    TEXT NOT NULL,
  importance TEXT NOT NULL,   -- 最優先 / 優先 / 通常
  due_date   TEXT NOT NULL     -- YYYY-MM-DD
)
""")
conn.commit()

# 重要度の並び替え用（最優先>優先>通常 を降順にする）
IMP_ORDER = {"最優先": 3, "優先": 2, "通常": 1}

def fetch_tasks(category: str):
    if category == "全て":
        c.execute("""
            SELECT id, category, title, content, importance, due_date
            FROM tasks
            ORDER BY 
              CASE importance 
                WHEN '最優先' THEN 3 WHEN '優先' THEN 2 ELSE 1 END DESC,
              due_date DESC,
              title ASC
        """)
    else:
        c.execute("""
            SELECT id, category, title, content, importance, due_date
            FROM tasks
            WHERE category = ?
            ORDER BY 
              CASE importance 
                WHEN '最優先' THEN 3 WHEN '優先' THEN 2 ELSE 1 END DESC,
              due_date DESC,
              title ASC
        """, (category,))
    rows = c.fetchall()
    # DataFrame（一覧表示用）
    df = pd.DataFrame(rows, columns=["id","カテゴリ","タイトル","内容","重要度","締切日"])
    return df

def get_task(task_id: int):
    c.execute("""
        SELECT id, category, title, content, importance, due_date
        FROM tasks WHERE id=?
    """, (task_id,))
    row = c.fetchone()
    if not row: 
        return None
    return {
        "id": row[0], "category": row[1], "title": row[2], "content": row[3],
        "importance": row[4], "due_date": row[5]
    }

def insert_task(category, title, content, importance, due_date):
    c.execute("""
        INSERT INTO tasks (category, title, content, importance, due_date)
        VALUES (?, ?, ?, ?, ?)
    """, (category, title, content, importance, due_date))
    conn.commit()

def update_task(task_id, category, title, content, importance, due_date):
    c.execute("""
        UPDATE tasks
        SET category=?, title=?, content=?, importance=?, due_date=?
        WHERE id=?
    """, (category, title, content, importance, due_date, task_id))
    conn.commit()

def delete_task(task_id):
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()

# ---------- セッション状態 ----------
if "selected_task_id" not in st.session_state:
    st.session_state.selected_task_id = None  # 一覧で選ばれたID
if "list_df" not in st.session_state:
    st.session_state.list_df = pd.DataFrame(columns=["id","カテゴリ","タイトル","内容","重要度","締切日"])

# ---------- 上段：カテゴリ選択 ----------
st.title("TODOアプリ（UI固め）")
CATEGORIES = ["全て", "仕事", "個人開発", "その他"]
sel_category = st.selectbox("カテゴリを選択", CATEGORIES, index=0)

# ---------- 中段：タスク一覧（スクロール領域） ----------
st.subheader("タスク一覧（カテゴリ | 締切日 | タイトル | 重要度）")

# 一覧データ取得
st.session_state.list_df = fetch_tasks(sel_category)

# 表示用に必要カラムのみ、IDは表示しない
show_df = st.session_state.list_df[["カテゴリ","締切日","タイトル","重要度"]].copy()

# 5件超ならスクロール：data_editor で高さ固定
# 選択列（チェックボックス）を先頭に付与
if not show_df.empty:
    show_df.insert(0, "選択", False)
    edited = st.data_editor(
        show_df,
        hide_index=True,
        use_container_width=True,
        height=240,  # 約5行分＋ヘッダ、スクロール可能
        disabled=["カテゴリ","締切日","タイトル","重要度"],  # 編集不可
        key="list_editor",
    )
    # チェックされた行を特定
    selected_rows = edited.index[edited["選択"] == True].tolist()
    # 複数チェックされたら最後の1件を採用
    selected_row = selected_rows[-1] if selected_rows else None

    # 「読み込む」ボタン（一覧のすぐ下、フル幅で）
    col_load, col_clear = st.columns([3,1])
    with col_load:
        if st.button("選択したタスクをフォームに読み込む", use_container_width=True):
            if selected_row is not None:
                # 対応する元DFの行を取得（id は元DFにしかない）
                origin_row = st.session_state.list_df.iloc[selected_row]
                st.session_state.selected_task_id = int(origin_row["id"])
                st.success("タスクを下段フォームに読み込みました。")
            else:
                st.warning("読み込むタスクを一覧でチェックしてください。")
    with col_clear:
        if st.button("選択解除", use_container_width=True):
            st.session_state.selected_task_id = None
            st.success("選択を解除しました。新規追加モードです。")
else:
    st.info("タスクはありません。下段フォームから新規追加してください。")

st.divider()

# ---------- 下段：タスク追加／編集／削除フォーム ----------
mode = "編集" if st.session_state.selected_task_id else "新規追加"
st.subheader(f"タスク{mode}フォーム")

# 選択済みなら初期値を取得
init = None
if st.session_state.selected_task_id:
    init = get_task(st.session_state.selected_task_id)

with st.form("task_form", clear_on_submit=False):
    # 新規時はカテゴリは上段の選択に合わせるが、編集時は既存値を反映
    category = st.selectbox(
        "カテゴリ",
        CATEGORIES[1:],  # 「全て」は選択不可
        index=(CATEGORIES[1:].index(init["category"]) if init else 0)
    )
    title = st.text_input("タイトル", value=(init["title"] if init else ""))
    content = st.text_area("内容", value=(init["content"] if init else ""), height=120)
    importance = st.radio("重要度", ["最優先","優先","通常"],
                          index=(["最優先","優先","通常"].index(init["importance"]) if init else 2),
                          horizontal=True)
    # 締切日
    init_due = date.fromisoformat(init["due_date"]) if (init and init["due_date"]) else date.today()
    due = st.date_input("締切日", value=init_due)

    colA, colB, colC = st.columns([2,2,1])
    with colA:
        save = st.form_submit_button("保存（追加／更新）", use_container_width=True)
    with colB:
        del_ok = st.form_submit_button("削除（選択タスク）", use_container_width=True,
                                       disabled=(st.session_state.selected_task_id is None))
    with colC:
        clear = st.form_submit_button("新規モード", use_container_width=True)

# ----- バリデーション＆DB操作（メッセージはフル幅に出す） -----
def validate_inputs():
    errs = []
    if not title.strip():
        errs.append("タイトルは必須です。")
    if not content.strip():
        errs.append("内容は必須です。")
    # 締切日は常に受け入れ（重複可／過去日許容：UI検証段階）
    return errs

if 'last_action' not in st.session_state:
    st.session_state.last_action = None

if save:
    errors = validate_inputs()
    if errors:
        for e in errors:
            st.error(e)
    else:
        if st.session_state.selected_task_id:
            # 更新
            update_task(
                st.session_state.selected_task_id,
                category, title.strip(), content.strip(),
                importance, due.strftime("%Y-%m-%d")
            )
            st.session_state.last_action = "update"
            st.success("タスクを更新しました。")
        else:
            # 追加
            insert_task(
                category, title.strip(), content.strip(),
                importance, due.strftime("%Y-%m-%d")
            )
            st.session_state.last_action = "insert"
            st.success("タスクを追加しました。")
        # 再読込：フォーム値は維持しつつ一覧だけ最新化（rerunは使わない）
        st.session_state.list_df = fetch_tasks(sel_category)

if del_ok:
    if st.session_state.selected_task_id:
        delete_task(st.session_state.selected_task_id)
        st.session_state.last_action = "delete"
        st.success("タスクを削除しました。")
        # 選択解除して一覧を更新
        st.session_state.selected_task_id = None
        st.session_state.list_df = fetch_tasks(sel_category)
    else:
        st.warning("削除対象のタスクが選ばれていません。")

if clear:
    st.session_state.selected_task_id = None
    st.info("新規モードに切り替えました。")

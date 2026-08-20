from pathlib import Path

import pandas as pd
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent.parent
CATEGORY_PATH = ROOT_DIR / "customer_categories.csv"
SALES_PATH = ROOT_DIR / "sample_sales.csv"

st.set_page_config(page_title="顧客分類マスタ", page_icon="🛠️", layout="wide")
st.title("🛠️ 顧客分類マスタ メンテナンス")
st.caption("売上データの顧客分類で選択できる候補を追加・削除できます。")

categories = pd.read_csv(CATEGORY_PATH)
edited_categories = st.data_editor(
    categories,
    column_config={
        "顧客分類": st.column_config.TextColumn(
            "顧客分類",
            help="空白ではない一意な名称を入力してください",
            required=True,
        )
    },
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True,
    key="category_editor",
)

st.info(
    "売上データで使用中の分類は削除できません。先に売上データ側の分類を変更してください。"
)

if st.button("💾 マスタを保存", type="primary"):
    normalized = edited_categories["顧客分類"].dropna().astype(str).str.strip()
    normalized = normalized[normalized != ""]

    if normalized.empty:
        st.error("顧客分類を1件以上登録してください。")
    elif normalized.duplicated().any():
        duplicates = sorted(normalized[normalized.duplicated(keep=False)].unique())
        st.error("重複している顧客分類があります: " + "、".join(duplicates))
    else:
        sales_categories = set(
            pd.read_csv(SALES_PATH, usecols=["顧客分類"])["顧客分類"].dropna()
        )
        removed_in_use = sorted(sales_categories - set(normalized))
        if removed_in_use:
            st.error(
                "売上データで使用中のため削除できません: "
                + "、".join(removed_in_use)
            )
        else:
            pd.DataFrame({"顧客分類": normalized}).to_csv(
                CATEGORY_PATH, index=False, encoding="utf-8-sig"
            )
            st.success("顧客分類マスタを保存しました。")

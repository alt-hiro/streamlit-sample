from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


DATA_PATH = Path(__file__).with_name("sample_sales.csv")

st.set_page_config(page_title="売上データ管理", page_icon="📊", layout="wide")
st.title("📊 売上データ管理")
st.caption("売上データの絞り込み、顧客分類の編集、集計結果の確認ができます。")


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["対象日付"])
    data["売上金額"] = pd.to_numeric(data["売上金額"])
    return data


if "sales_data" not in st.session_state:
    st.session_state.sales_data = load_data(DATA_PATH).copy()

data = st.session_state.sales_data

st.header("1. フィルタ")
filter_col1, filter_col2 = st.columns(2)
years = sorted(data["対象日付"].dt.year.unique().tolist())
with filter_col1:
    st.markdown("**対象年**")
    selected_years = [
        year
        for year in years
        if st.checkbox(str(year), value=True, key=f"year_{year}")
    ]
with filter_col2:
    staff_options = sorted(data["担当者"].unique().tolist())
    selected_staff = st.multiselect(
        "担当者",
        options=staff_options,
        default=staff_options,
        placeholder="担当者を選択してください",
        help="入力欄に文字を入力すると候補を絞り込めます。",
    )

filtered = data[
    data["対象日付"].dt.year.isin(selected_years) & data["担当者"].isin(selected_staff)
].copy()

st.divider()
st.header("2. テーブル表示と編集")
st.caption("「顧客分類」だけを編集できます。変更内容はこの画面を開いている間保持されます。")

display_data = filtered.copy()
edited_data = st.data_editor(
    display_data,
    disabled=["対象日付", "担当者", "顧客名", "売上金額"],
    column_config={
        "対象日付": st.column_config.DateColumn("対象日付", format="YYYY-MM-DD"),
        "顧客分類": st.column_config.TextColumn("顧客分類", help="この列のみ編集できます"),
        "売上金額": st.column_config.NumberColumn("売上金額", format="¥%d"),
    },
    hide_index=True,
    use_container_width=True,
    key="sales_editor",
)

# フィルタ後も元データの行インデックスを維持しているため、編集値を正しい行へ戻せます。
if not edited_data.empty:
    st.session_state.sales_data.loc[edited_data.index, "顧客分類"] = edited_data[
        "顧客分類"
    ]

st.divider()
st.header("3. グラフ")
if filtered.empty:
    st.info("フィルタ条件に該当するデータがありません。")
else:
    # 編集直後の分類を円グラフにも反映します。
    chart_data = st.session_state.sales_data.loc[filtered.index].copy()
    chart_data["年月"] = chart_data["対象日付"].dt.strftime("%Y-%m")
    monthly_sales = chart_data.groupby("年月", as_index=False)["売上金額"].sum()
    category_sales = chart_data.groupby("顧客分類", as_index=False)["売上金額"].sum()

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("年月別の売上金額")
        bar_chart = (
            alt.Chart(monthly_sales)
            .mark_bar(color="#4C78A8")
            .encode(
                x=alt.X("年月:N", title="年月", sort=None),
                y=alt.Y("売上金額:Q", title="売上金額（円）"),
                tooltip=["年月:N", alt.Tooltip("売上金額:Q", format=",")],
            )
        )
        st.altair_chart(bar_chart, use_container_width=True)

    with chart_col2:
        st.subheader("顧客分類別の売上金額")
        pie_chart = (
            alt.Chart(category_sales)
            .mark_arc(innerRadius=35)
            .encode(
                theta=alt.Theta("売上金額:Q"),
                color=alt.Color("顧客分類:N", title="顧客分類"),
                tooltip=["顧客分類:N", alt.Tooltip("売上金額:Q", format=",")],
            )
        )
        st.altair_chart(pie_chart, use_container_width=True)

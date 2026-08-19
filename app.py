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
if "chart_data" not in st.session_state:
    st.session_state.chart_data = st.session_state.sales_data.copy()

data = st.session_state.sales_data

with st.sidebar:
    st.header("🔎 フィルター")
    years = sorted(data["対象日付"].dt.year.unique().tolist())
    st.markdown("**対象年**")
    selected_years = [
        year
        for year in years
        if st.checkbox(str(year), value=True, key=f"year_{year}")
    ]

    staff_options = sorted(data["担当者"].unique().tolist())
    selected_staff = st.multiselect(
        "担当者",
        options=staff_options,
        default=staff_options,
        placeholder="担当者を選択してください",
        help="入力欄に文字を入力すると候補を絞り込めます。",
    )

    st.divider()
    st.header("↕️ 並び順")
    sort_columns = st.multiselect(
        "ソートする列（優先順）",
        options=data.columns.tolist(),
        default=["対象日付"],
        help="選択した順番がソートの優先順位になります。",
    )
    sort_ascending = []
    for position, column in enumerate(sort_columns):
        direction = st.selectbox(
            f"{position + 1}. {column}",
            options=["昇順", "降順"],
            key=f"sort_direction_{column}",
        )
        sort_ascending.append(direction == "昇順")

filtered = data[
    data["対象日付"].dt.year.isin(selected_years) & data["担当者"].isin(selected_staff)
].copy()
if sort_columns:
    filtered = filtered.sort_values(
        by=sort_columns, ascending=sort_ascending, kind="mergesort"
    )

st.header("1. テーブル表示と編集")
st.caption("「顧客分類」だけを編集できます。編集後に保存またはグラフ更新を実行してください。")

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

save_col, refresh_col, message_col = st.columns([1, 1.4, 4])
with save_col:
    save_clicked = st.button("💾 保存", type="primary", use_container_width=True)
with refresh_col:
    refresh_clicked = st.button("🔄 グラフを更新", use_container_width=True)

if save_clicked:
    save_data = st.session_state.sales_data.copy()
    save_data.to_csv(DATA_PATH, index=False, date_format="%Y-%m-%d", encoding="utf-8-sig")
    with message_col:
        st.success("編集内容を CSV に保存しました。")

if refresh_clicked:
    st.session_state.chart_data = st.session_state.sales_data.copy()
    with message_col:
        st.success("グラフを最新の編集内容で更新しました。")

st.divider()
st.header("2. グラフ")
chart_source = st.session_state.chart_data
chart_filtered = chart_source[
    chart_source["対象日付"].dt.year.isin(selected_years)
    & chart_source["担当者"].isin(selected_staff)
].copy()
if chart_filtered.empty:
    st.info("フィルタ条件に該当するデータがありません。")
else:
    chart_data = chart_filtered
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

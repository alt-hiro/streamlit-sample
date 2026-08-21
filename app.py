from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, DataReturnMode, GridOptionsBuilder, GridUpdateMode


DATA_PATH = Path(__file__).with_name("sample_sales.csv")
CATEGORY_PATH = Path(__file__).with_name("customer_categories.csv")

st.set_page_config(page_title="売上データ管理", page_icon="📊", layout="wide")
st.title("📊 売上データ管理")
st.caption("売上データの絞り込み、顧客分類の編集、集計結果の確認ができます。")


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path, parse_dates=["対象日付"])
    for column in ["種別", "部署", "売上金額"]:
        data[column] = pd.to_numeric(data[column])
    return data


def load_categories(path: Path) -> list[str]:
    category_data = pd.read_csv(path)
    return category_data["顧客分類"].dropna().astype(str).str.strip().tolist()


if "sales_data" not in st.session_state:
    st.session_state.sales_data = load_data(DATA_PATH).copy()
if "chart_data" not in st.session_state:
    st.session_state.chart_data = st.session_state.sales_data.copy()

data = st.session_state.sales_data
categories = load_categories(CATEGORY_PATH)
if not categories:
    st.error("顧客分類マスタが空です。マスタメンテナンス画面で分類を登録してください。")
    st.stop()

invalid_categories = sorted(set(data["顧客分類"].dropna()) - set(categories))
if invalid_categories:
    st.error(
        "売上データにマスタ未登録の顧客分類があります: "
        + "、".join(invalid_categories)
    )
    st.stop()

with st.sidebar:
    st.header("🔎 フィルター")
    years = sorted(data["対象日付"].dt.year.unique().tolist())
    selected_years = st.multiselect(
        "対象年",
        options=years,
        default=[],
        placeholder="指定なし（すべての年）",
        help="未選択の場合はすべての年を表示します。",
    )

    staff_options = sorted(data["担当者"].unique().tolist())
    selected_staff = st.multiselect(
        "担当者",
        options=staff_options,
        default=[],
        placeholder="指定なし（すべての担当者）",
        help="未選択の場合はすべての担当者を表示します。入力すると候補を絞り込めます。",
    )

    customer_options = sorted(data["顧客名"].unique().tolist())
    selected_customers = st.multiselect(
        "顧客名",
        options=customer_options,
        default=[],
        placeholder="指定なし（すべての顧客）",
        help="未選択の場合はすべての顧客を表示します。入力すると候補を絞り込めます。",
    )

    st.divider()
    st.header("↕️ 並び順")
    sort_columns = st.multiselect(
        "ソートする列（優先順）",
        options=data.columns.tolist(),
        default=["対象日付", "顧客分類", "顧客名"],
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

filter_mask = pd.Series(True, index=data.index)
if selected_years:
    filter_mask &= data["対象日付"].dt.year.isin(selected_years)
if selected_staff:
    filter_mask &= data["担当者"].isin(selected_staff)
if selected_customers:
    filter_mask &= data["顧客名"].isin(selected_customers)
filtered = data[filter_mask].copy()
if sort_columns:
    filtered = filtered.sort_values(
        by=sort_columns, ascending=sort_ascending, kind="mergesort"
    )

st.header("1. テーブル表示と編集")
st.caption(
    "薄い黄色の「顧客分類」列だけを編集できます。編集後に保存またはグラフ更新を実行してください。"
)

display_data = filtered.copy()
display_data["対象日付"] = display_data["対象日付"].dt.strftime("%Y-%m-%d")
display_data["__row_id"] = display_data.index

grid_builder = GridOptionsBuilder.from_dataframe(display_data)
grid_builder.configure_default_column(editable=False, sortable=False, filter=False)
grid_builder.configure_column("対象日付", header_name="対象日付")
grid_builder.configure_column("種別", header_name="種別", type=["numericColumn"])
grid_builder.configure_column("種別名", header_name="種別名")
grid_builder.configure_column("部署", header_name="部署", type=["numericColumn"])
grid_builder.configure_column("部署名", header_name="部署名")
grid_builder.configure_column("担当者", header_name="担当者")
grid_builder.configure_column("顧客名", header_name="顧客名")
grid_builder.configure_column(
    "顧客分類",
    header_name="顧客分類（編集可）",
    editable=True,
    cellEditor="agSelectCellEditor",
    cellEditorParams={"values": categories},
    cellStyle={"backgroundColor": "#fff9c4"},
)
grid_builder.configure_column("売上金額", header_name="売上金額", type=["numericColumn"])
grid_builder.configure_column("__row_id", hide=True)

grid_response = AgGrid(
    display_data,
    gridOptions=grid_builder.build(),
    update_mode=GridUpdateMode.VALUE_CHANGED,
    data_return_mode=DataReturnMode.AS_INPUT,
    fit_columns_on_grid_load=True,
    height=420,
    key="sales_editor_grid",
)
edited_data = pd.DataFrame(grid_response["data"])

# フィルタ後も元データの行インデックスを維持しているため、編集値を正しい行へ戻せます。
if not edited_data.empty:
    row_ids = pd.to_numeric(edited_data["__row_id"]).astype(int)
    st.session_state.sales_data.loc[row_ids, "顧客分類"] = edited_data[
        "顧客分類"
    ].to_numpy()

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
chart_filter_mask = pd.Series(True, index=chart_source.index)
if selected_years:
    chart_filter_mask &= chart_source["対象日付"].dt.year.isin(selected_years)
if selected_staff:
    chart_filter_mask &= chart_source["担当者"].isin(selected_staff)
if selected_customers:
    chart_filter_mask &= chart_source["顧客名"].isin(selected_customers)
chart_filtered = chart_source[chart_filter_mask].copy()
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

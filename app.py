from pathlib import Path
import base64
import io
import math
import struct
import wave

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components


DATA_PATH = Path(__file__).with_name("data.csv")


def build_fallback_data() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "SKU": "FALL-001",
                "Product_Name": "Fallback Inventory Item",
                "Category": "General",
                "Supplier": "Default Supplier",
                "Quantity_On_Hand": 0,
                "Reorder_Level": 10,
                "Unit_Cost": 5.0,
                "Unit_Price": 9.0,
                "Lead_Time_Days": 7,
                "Last_Restock_Date": "2026-06-01",
            }
        ]
    )


@st.cache_data
def build_order_jingle() -> str:
    sample_rate = 44100
    tones = [
        (659.25, 0.13),
        (783.99, 0.13),
        (987.77, 0.18),
        (1318.51, 0.24),
    ]
    frames = bytearray()

    for frequency, duration in tones:
        frame_count = int(sample_rate * duration)
        fade_frames = max(1, int(sample_rate * 0.015))

        for index in range(frame_count):
            fade_in = min(1.0, index / fade_frames)
            fade_out = min(1.0, (frame_count - index) / fade_frames)
            envelope = min(fade_in, fade_out)
            sample = int(0.38 * envelope * 32767 * math.sin(2 * math.pi * frequency * index / sample_rate))
            frames.extend(struct.pack("<h", sample))

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(bytes(frames))

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def play_order_jingle() -> None:
    encoded_audio = build_order_jingle()
    components.html(
        f"""
        <audio autoplay>
            <source src="data:audio/wav;base64,{encoded_audio}" type="audio/wav">
        </audio>
        """,
        height=0,
    )


@st.cache_data
def load_data() -> pd.DataFrame:
    try:
        data = pd.read_csv(DATA_PATH, parse_dates=["Last_Restock_Date"])
    except FileNotFoundError:
        st.warning("data.csv was not found, so a small fallback dataset is being shown.")
        data = build_fallback_data()
        data["Last_Restock_Date"] = pd.to_datetime(data["Last_Restock_Date"])
    except Exception as exc:
        st.error(f"Could not load data.csv: {exc}")
        data = build_fallback_data()
        data["Last_Restock_Date"] = pd.to_datetime(data["Last_Restock_Date"])

    numeric_columns = [
        "Quantity_On_Hand",
        "Reorder_Level",
        "Unit_Cost",
        "Unit_Price",
        "Lead_Time_Days",
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)

    data["Last_Restock_Date"] = pd.to_datetime(data["Last_Restock_Date"], errors="coerce")
    data["Inventory_Value"] = data["Quantity_On_Hand"] * data["Unit_Cost"]
    data["Potential_Revenue"] = data["Quantity_On_Hand"] * data["Unit_Price"]
    data["Gross_Margin_Per_Unit"] = data["Unit_Price"] - data["Unit_Cost"]
    data["Units_Short"] = (data["Reorder_Level"] - data["Quantity_On_Hand"]).clip(lower=0)
    data["Suggested_Reorder_Qty"] = data["Units_Short"] + data["Reorder_Level"]
    data["Stock_Status"] = data.apply(classify_stock_status, axis=1)
    return data


def classify_stock_status(row: pd.Series) -> str:
    if row["Quantity_On_Hand"] <= 0:
        return "Out of Stock"
    if row["Quantity_On_Hand"] <= row["Reorder_Level"]:
        return "Low Stock"
    return "Healthy"


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def kpi_card(label: str, value: str, helper: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-helper">{helper}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_color(status: str) -> str:
    colors = {
        "Out of Stock": "background-color: #fee2e2; color: #991b1b;",
        "Low Stock": "background-color: #ffedd5; color: #9a3412;",
        "Healthy": "background-color: #dcfce7; color: #166534;",
    }
    return colors.get(status, "")


def style_inventory_table(data: pd.DataFrame):
    formatters = {
        "Unit_Cost": "${:,.2f}",
        "Unit_Price": "${:,.2f}",
        "Inventory_Value": "${:,.2f}",
        "Potential_Revenue": "${:,.2f}",
        "Last_Restock_Date": lambda value: ""
        if pd.isna(value)
        else value.strftime("%Y-%m-%d"),
    }
    active_formatters = {
        column: formatter
        for column, formatter in formatters.items()
        if column in data.columns
    }

    styled = data.style.format(active_formatters)
    if "Stock_Status" in data.columns:
        styled = styled.map(status_color, subset=["Stock_Status"])
    if "Units_Short" in data.columns:
        styled = styled.background_gradient(cmap="Oranges", subset=["Units_Short"])
    return styled


st.set_page_config(
    page_title="Inventory Management Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }
        .app-title {
            font-size: 2.2rem;
            font-weight: 750;
            color: #111827;
            margin-bottom: 0.15rem;
        }
        .app-subtitle {
            color: #4b5563;
            font-size: 1rem;
            margin-bottom: 1.25rem;
        }
        .kpi-card {
            border: 1px solid #e5e7eb;
            border-left: 5px solid #2563eb;
            border-radius: 8px;
            padding: 1rem;
            background: #ffffff;
            box-shadow: 0 1px 3px rgba(17, 24, 39, 0.08);
            min-height: 116px;
        }
        .kpi-label {
            color: #6b7280;
            font-size: 0.82rem;
            font-weight: 650;
            text-transform: uppercase;
            letter-spacing: 0;
        }
        .kpi-value {
            color: #111827;
            font-size: 1.85rem;
            font-weight: 750;
            margin-top: 0.25rem;
            line-height: 1.15;
        }
        .kpi-helper {
            color: #6b7280;
            font-size: 0.84rem;
            margin-top: 0.25rem;
        }
        .alert-panel {
            background: #fff7ed;
            border: 1px solid #fdba74;
            border-left: 6px solid #ea580c;
            border-radius: 8px;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1rem;
        }
        .alert-panel h3 {
            color: #9a3412;
            margin-top: 0;
            margin-bottom: 0.2rem;
        }
        .empty-state {
            background: #ecfdf5;
            border: 1px solid #86efac;
            border-left: 6px solid #16a34a;
            border-radius: 8px;
            color: #166534;
            padding: 1rem 1.1rem;
            margin: 0.5rem 0 1rem;
            font-weight: 650;
        }
        div[data-testid="stDataFrame"] {
            border: 1px solid #e5e7eb;
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

inventory = load_data()

with st.sidebar:
    st.header("Filters")
    categories = sorted(inventory["Category"].dropna().unique())
    suppliers = sorted(inventory["Supplier"].dropna().unique())

    selected_categories = st.multiselect("Category", categories, default=categories)
    selected_suppliers = st.multiselect("Supplier", suppliers, default=suppliers)
    selected_status = st.radio(
        "Stock status",
        ["All", "Low Stock", "Out of Stock", "Healthy"],
        index=0,
    )

    st.divider()
    st.caption("Download respects every active filter.")

filtered = inventory[
    inventory["Category"].isin(selected_categories)
    & inventory["Supplier"].isin(selected_suppliers)
].copy()

if selected_status != "All":
    filtered = filtered[filtered["Stock_Status"] == selected_status].copy()

st.markdown('<div class="app-title">Inventory Management Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Monitor stock health, reorder risks, supplier exposure, and inventory value from one operational view.</div>',
    unsafe_allow_html=True,
)

if filtered.empty:
    st.info("No inventory rows match the selected filters. Adjust the sidebar filters to continue.")
    st.download_button(
        "Download filtered CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        "filtered_inventory.csv",
        "text/csv",
        use_container_width=True,
    )
    st.stop()

low_stock = filtered[filtered["Quantity_On_Hand"] <= filtered["Reorder_Level"]].copy()
out_of_stock = filtered[filtered["Quantity_On_Hand"] <= 0].copy()

kpi_columns = st.columns(5)
with kpi_columns[0]:
    kpi_card("Total SKUs", f"{filtered['SKU'].nunique():,}", "unique products")
with kpi_columns[1]:
    kpi_card("Inventory Value", format_currency(filtered["Inventory_Value"].sum()), "at unit cost")
with kpi_columns[2]:
    kpi_card("Units in Stock", f"{filtered['Quantity_On_Hand'].sum():,.0f}", "on hand now")
with kpi_columns[3]:
    kpi_card("Low-Stock Items", f"{len(low_stock):,}", "at or below reorder point")
with kpi_columns[4]:
    kpi_card("Out of Stock", f"{len(out_of_stock):,}", "zero units available")

st.subheader("Low Stock Alerts")
if low_stock.empty:
    st.markdown(
        '<div class="empty-state">No items need reordering right now.</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="alert-panel">
            <h3>Reorder attention needed</h3>
            <div>{len(low_stock)} item(s) are at or below reorder level. Suggested reorder quantity covers the current shortfall plus one reorder-level buffer.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    alert_columns = [
        "SKU",
        "Product_Name",
        "Category",
        "Supplier",
        "Quantity_On_Hand",
        "Reorder_Level",
        "Units_Short",
        "Suggested_Reorder_Qty",
        "Lead_Time_Days",
    ]
    st.dataframe(
        style_inventory_table(low_stock[alert_columns].sort_values(["Units_Short", "Lead_Time_Days"], ascending=False)),
        use_container_width=True,
        hide_index=True,
    )
    reorder_units = int(low_stock["Suggested_Reorder_Qty"].sum())
    if st.button(
        f"Place reorder for {len(low_stock):,} item(s)",
        type="primary",
        use_container_width=True,
    ):
        st.success(f"Order placed for {reorder_units:,} suggested units.")
        play_order_jingle()

stock_tab, category_tab, supplier_tab, valuation_tab = st.tabs(
    ["Stock Levels", "Category Analysis", "Supplier Analysis", "Inventory Valuation"]
)

with stock_tab:
    left, right = st.columns([1.15, 1])
    with left:
        stock_chart_data = filtered.sort_values("Quantity_On_Hand", ascending=True).tail(25)
        fig_stock = px.bar(
            stock_chart_data,
            x="Quantity_On_Hand",
            y="Product_Name",
            color="Stock_Status",
            orientation="h",
            color_discrete_map={
                "Healthy": "#16a34a",
                "Low Stock": "#f97316",
                "Out of Stock": "#dc2626",
            },
            hover_data=["SKU", "Category", "Supplier", "Reorder_Level"],
            title="Current Stock Levels by Product",
        )
        fig_stock.update_layout(height=650, yaxis_title="", xaxis_title="Units on hand")
        st.plotly_chart(fig_stock, use_container_width=True)
    with right:
        st.write("Sortable inventory ledger")
        table_columns = [
            "SKU",
            "Product_Name",
            "Category",
            "Supplier",
            "Quantity_On_Hand",
            "Reorder_Level",
            "Stock_Status",
            "Unit_Cost",
            "Inventory_Value",
            "Last_Restock_Date",
        ]
        st.dataframe(
            style_inventory_table(filtered[table_columns].sort_values("Quantity_On_Hand")),
            use_container_width=True,
            hide_index=True,
            height=650,
        )

with category_tab:
    category_summary = (
        filtered.groupby("Category", as_index=False)
        .agg(
            Inventory_Value=("Inventory_Value", "sum"),
            Units=("Quantity_On_Hand", "sum"),
            SKU_Count=("SKU", "nunique"),
            Low_Stock_Items=("Units_Short", lambda values: int((values > 0).sum())),
        )
        .sort_values("Inventory_Value", ascending=False)
    )

    left, right = st.columns(2)
    with left:
        fig_category_value = px.bar(
            category_summary,
            x="Category",
            y="Inventory_Value",
            color="Category",
            title="Inventory Value by Category",
            text_auto=".2s",
        )
        fig_category_value.update_layout(showlegend=False, yaxis_title="Inventory value")
        st.plotly_chart(fig_category_value, use_container_width=True)
    with right:
        fig_category_units = px.treemap(
            category_summary,
            path=["Category"],
            values="Units",
            color="Inventory_Value",
            color_continuous_scale="Tealrose",
            title="Units on Hand by Category",
        )
        st.plotly_chart(fig_category_units, use_container_width=True)

    st.dataframe(
        category_summary.style.format({"Inventory_Value": "${:,.2f}", "Units": "{:,.0f}"}),
        use_container_width=True,
        hide_index=True,
    )

with supplier_tab:
    supplier_summary = (
        filtered.groupby("Supplier", as_index=False)
        .agg(
            Inventory_Value=("Inventory_Value", "sum"),
            SKU_Count=("SKU", "nunique"),
            Units=("Quantity_On_Hand", "sum"),
            Avg_Lead_Time_Days=("Lead_Time_Days", "mean"),
            Low_Stock_Items=("Units_Short", lambda values: int((values > 0).sum())),
        )
        .sort_values("Inventory_Value", ascending=False)
    )

    left, right = st.columns(2)
    with left:
        fig_supplier_value = px.bar(
            supplier_summary,
            x="Supplier",
            y="Inventory_Value",
            color="Supplier",
            title="Inventory Value by Supplier",
            text_auto=".2s",
        )
        fig_supplier_value.update_layout(showlegend=False, yaxis_title="Inventory value")
        st.plotly_chart(fig_supplier_value, use_container_width=True)
    with right:
        fig_supplier_lead = px.scatter(
            supplier_summary,
            x="Avg_Lead_Time_Days",
            y="Inventory_Value",
            size="SKU_Count",
            color="Supplier",
            hover_data=["Units", "Low_Stock_Items"],
            title="Supplier Dependence vs. Average Lead Time",
        )
        fig_supplier_lead.update_layout(xaxis_title="Average lead time in days", yaxis_title="Inventory value")
        st.plotly_chart(fig_supplier_lead, use_container_width=True)

    st.dataframe(
        supplier_summary.style.format(
            {
                "Inventory_Value": "${:,.2f}",
                "Units": "{:,.0f}",
                "Avg_Lead_Time_Days": "{:.1f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

with valuation_tab:
    category_value = filtered.groupby("Category", as_index=False)["Inventory_Value"].sum()
    supplier_value = filtered.groupby("Supplier", as_index=False)["Inventory_Value"].sum()

    metric_left, metric_right, metric_third = st.columns(3)
    metric_left.metric("Filtered inventory value", format_currency(filtered["Inventory_Value"].sum()))
    metric_right.metric("Potential shelf revenue", format_currency(filtered["Potential_Revenue"].sum()))
    metric_third.metric(
        "Estimated gross margin",
        format_currency((filtered["Potential_Revenue"] - filtered["Inventory_Value"]).sum()),
    )

    left, right = st.columns(2)
    with left:
        fig_category_pie = px.pie(
            category_value,
            names="Category",
            values="Inventory_Value",
            title="Inventory Value Share by Category",
            hole=0.42,
        )
        st.plotly_chart(fig_category_pie, use_container_width=True)
    with right:
        fig_supplier_pie = px.pie(
            supplier_value,
            names="Supplier",
            values="Inventory_Value",
            title="Inventory Value Share by Supplier",
            hole=0.42,
        )
        st.plotly_chart(fig_supplier_pie, use_container_width=True)

st.subheader("Export Filtered Inventory")
export_columns = [
    "SKU",
    "Product_Name",
    "Category",
    "Supplier",
    "Quantity_On_Hand",
    "Reorder_Level",
    "Unit_Cost",
    "Unit_Price",
    "Lead_Time_Days",
    "Last_Restock_Date",
    "Inventory_Value",
    "Stock_Status",
    "Units_Short",
    "Suggested_Reorder_Qty",
]
st.download_button(
    "Download filtered CSV",
    filtered[export_columns].to_csv(index=False).encode("utf-8"),
    "filtered_inventory.csv",
    "text/csv",
    use_container_width=True,
)

from pathlib import Path
import base64
from html import escape
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


def render_order_button(item_count: int, reorder_units: int) -> None:
    encoded_audio = build_order_jingle()
    components.html(
        f"""
        <style>
            .order-action {{
                align-items: center;
                background: #111827;
                border: 0;
                border-radius: 8px;
                color: #ffffff;
                cursor: pointer;
                display: flex;
                font: 700 15px/1.2 Arial, sans-serif;
                justify-content: center;
                min-height: 46px;
                width: 100%;
            }}
            .order-action:hover {{
                background: #1f2937;
            }}
            .order-message {{
                color: #166534;
                display: none;
                font: 700 14px/1.4 Arial, sans-serif;
                margin-top: 10px;
            }}
        </style>
        <button class="order-action" id="place-order">
            Place reorder for {item_count:,} item(s)
        </button>
        <div class="order-message" id="order-message">
            Order placed for {reorder_units:,} suggested units.
        </div>
        <script>
            const button = document.getElementById("place-order");
            const message = document.getElementById("order-message");
            button.addEventListener("click", async () => {{
                const audio = new Audio("data:audio/wav;base64,{encoded_audio}");
                audio.volume = 0.75;
                try {{
                    await audio.play();
                }} catch (error) {{
                    console.log("Audio playback was blocked by the browser.", error);
                }}
                message.style.display = "block";
                button.textContent = "Order placed";
                button.style.background = "#166534";
            }});
        </script>
        """,
        height=96,
    )


def render_low_stock_rows(data: pd.DataFrame) -> None:
    rows = []
    for _, row in data.iterrows():
        status_class = "out" if row["Quantity_On_Hand"] <= 0 else "low"
        rows.append(
            f"""
            <div class="product-row">
                <div class="product-main">
                    <span class="sku-pill">{escape(str(row["SKU"]))}</span>
                    <strong>{escape(str(row["Product_Name"]))}</strong>
                    <span>{escape(str(row["Category"]))} | {escape(str(row["Supplier"]))}</span>
                </div>
                <div class="product-metrics">
                    <span class="stock-chip {status_class}">{escape(str(row["Stock_Status"]))}</span>
                    <span><b>{int(row["Quantity_On_Hand"]):,}</b> on hand</span>
                    <span><b>{int(row["Units_Short"]):,}</b> short</span>
                    <span><b>{int(row["Suggested_Reorder_Qty"]):,}</b> reorder</span>
                    <span><b>{int(row["Lead_Time_Days"]):,}</b> day lead</span>
                </div>
            </div>
            """
        )

    st.markdown(
        f"""
        <div class="product-list">
            {''.join(rows)}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_rotating_banner(data: pd.DataFrame, low_stock_count: int, out_of_stock_count: int) -> None:
    top_category = (
        data.groupby("Category")["Inventory_Value"].sum().sort_values(ascending=False).index[0]
        if not data.empty
        else "Inventory"
    )
    st.markdown(
        f"""
        <div class="rotating-banner">
            <div class="banner-track">
                <div class="banner-slide">
                    <strong>{low_stock_count:,} low-stock item(s)</strong>
                    <span>Review reorder priorities before the next supplier cycle.</span>
                </div>
                <div class="banner-slide">
                    <strong>{out_of_stock_count:,} out-of-stock item(s)</strong>
                    <span>Focus urgent orders where sales can be blocked.</span>
                </div>
                <div class="banner-slide">
                    <strong>{escape(str(top_category))} leads value</strong>
                    <span>Keep an eye on category concentration and cash exposure.</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
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
        .rotating-banner {
            background: linear-gradient(90deg, #111827, #134e4a, #7c2d12);
            border-radius: 8px;
            color: #ffffff;
            margin: 0.2rem 0 1.1rem;
            min-height: 72px;
            overflow: hidden;
            position: relative;
        }
        .banner-track {
            animation: rotateBanner 15s infinite;
        }
        .banner-slide {
            align-items: center;
            display: flex;
            gap: 0.85rem;
            min-height: 72px;
            padding: 0.9rem 1.1rem;
        }
        .banner-slide strong {
            font-size: 1.05rem;
            white-space: nowrap;
        }
        .banner-slide span {
            color: #e5e7eb;
            font-size: 0.95rem;
        }
        @keyframes rotateBanner {
            0%, 28% { transform: translateY(0); }
            33%, 61% { transform: translateY(-72px); }
            66%, 94% { transform: translateY(-144px); }
            100% { transform: translateY(0); }
        }
        .kpi-card {
            animation: riseIn 0.45s ease both;
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
        .product-list {
            display: grid;
            gap: 0.65rem;
            margin-bottom: 0.8rem;
        }
        .product-row {
            animation: riseIn 0.35s ease both;
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-left: 5px solid #ea580c;
            border-radius: 8px;
            display: grid;
            gap: 0.8rem;
            grid-template-columns: minmax(220px, 1.4fr) minmax(320px, 2fr);
            padding: 0.85rem 1rem;
        }
        .product-main {
            display: grid;
            gap: 0.2rem;
            min-width: 0;
        }
        .product-main strong {
            color: #111827;
            overflow-wrap: anywhere;
        }
        .product-main span:last-child {
            color: #6b7280;
            font-size: 0.88rem;
            overflow-wrap: anywhere;
        }
        .sku-pill,
        .stock-chip {
            border-radius: 999px;
            display: inline-flex;
            font-size: 0.78rem;
            font-weight: 750;
            justify-content: center;
            padding: 0.18rem 0.5rem;
            width: fit-content;
        }
        .sku-pill {
            background: #e0f2fe;
            color: #075985;
        }
        .stock-chip.low {
            background: #ffedd5;
            color: #9a3412;
        }
        .stock-chip.out {
            background: #fee2e2;
            color: #991b1b;
        }
        .product-metrics {
            align-items: center;
            display: grid;
            gap: 0.45rem;
            grid-template-columns: repeat(5, minmax(86px, 1fr));
        }
        .product-metrics span {
            background: #f9fafb;
            border: 1px solid #eef2f7;
            border-radius: 8px;
            color: #374151;
            font-size: 0.86rem;
            padding: 0.45rem 0.55rem;
            text-align: center;
        }
        @keyframes riseIn {
            from {
                opacity: 0;
                transform: translateY(8px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        @media (max-width: 900px) {
            .banner-slide {
                align-items: flex-start;
                flex-direction: column;
                gap: 0.2rem;
                justify-content: center;
            }
            .banner-slide strong {
                white-space: normal;
            }
            .product-row {
                grid-template-columns: 1fr;
            }
            .product-metrics {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

inventory = load_data()

with st.sidebar:
    st.header("Navigation")
    selected_view = st.radio(
        "Dashboard section",
        ["Stock Levels", "Category Analysis", "Supplier Analysis", "Inventory Valuation"],
        index=0,
    )

    st.divider()
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

render_rotating_banner(filtered, len(low_stock), len(out_of_stock))

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
        "Stock_Status",
    ]
    sorted_alerts = low_stock[alert_columns].sort_values(["Units_Short", "Lead_Time_Days"], ascending=False)
    render_low_stock_rows(sorted_alerts)
    reorder_units = int(low_stock["Suggested_Reorder_Qty"].sum())
    render_order_button(len(low_stock), reorder_units)

if selected_view == "Stock Levels":
    st.subheader("Stock Levels")
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
        st.write("Inventory ledger")
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
        st.table(style_inventory_table(filtered[table_columns].sort_values("Quantity_On_Hand")))

if selected_view == "Category Analysis":
    st.subheader("Category Analysis")
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

if selected_view == "Supplier Analysis":
    st.subheader("Supplier Analysis")
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

if selected_view == "Inventory Valuation":
    st.subheader("Inventory Valuation")
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

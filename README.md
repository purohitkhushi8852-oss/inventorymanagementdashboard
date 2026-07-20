# Inventory Management Dashboard

## Live Link

https://inventorymanagementdashboard-6sdhkazti7hbjhpjx8wdt4.streamlit.app/

A Streamlit dashboard for monitoring warehouse inventory health, reorder risks, supplier exposure, and inventory valuation. The sample data is synthetic, but shaped like a realistic small-business inventory ledger with healthy, low-stock, and out-of-stock SKUs.

## Project Structure

```text
inventorymanagementdashboard/
|-- app.py
|-- data.csv
|-- requirements.txt
|-- README.md
|-- Create Storyline.md
```

## Local Setup

From inside the project root folder, run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app will open in your browser. If it does not open automatically, Streamlit will print a local URL such as `http://localhost:8501`.

## What The Dashboard Shows

- KPI cards for total SKUs, inventory value, units on hand, low-stock items, and out-of-stock items.
- Sidebar filters for category, supplier, and stock status.
- A visually highlighted reorder alert panel for items at or below reorder level.
- Plotly charts for stock levels, category performance, supplier dependence, lead time, and inventory valuation.
- A CSV download button that exports the currently filtered inventory table.

## Deployment

### Streamlit Community Cloud

1. Push the project root folder to a GitHub repository.
2. Go to `https://share.streamlit.io`.
3. Choose the repository, branch, and set the main file path to `app.py`.
4. Deploy. Streamlit Community Cloud will install packages from `requirements.txt`.

GitHub Pages cannot host this app because GitHub Pages only serves static sites, while Streamlit requires a running Python server.

### Alternatives

- Render: create a web service, install from `requirements.txt`, and run `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
- Hugging Face Spaces: create a Streamlit Space and upload `app.py`, `data.csv`, and `requirements.txt`.

## Presentation Notes

- Start with the KPI cards to explain the current business position in one glance.
- Move to the low-stock alert panel and explain that it answers the manager's most urgent question: what should be reordered now?
- Use the supplier and category tabs to discuss where inventory value is concentrated and which suppliers create lead-time exposure.

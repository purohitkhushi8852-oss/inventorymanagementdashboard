# Inventory Management Dashboard Presentation Storyline

## 1. Opening

Good morning everyone. Today I am presenting my Inventory Management Dashboard.

This dashboard is made to help a business understand its inventory position in one place. In many stores, warehouses, or small businesses, inventory data is available, but it is hard to quickly answer important questions like:

- Which products are available?
- Which products are running low?
- Which items are completely out of stock?
- Which supplier or category has the highest inventory value?
- Where should the business take action first?

The idea of this dashboard is to convert raw inventory data into clear visual insights so that a manager can make faster and better decisions.

## 2. What This Dashboard Is About

This dashboard is about inventory monitoring and decision making.

Inventory management is important because both overstocking and understocking can create problems. If a company keeps too much stock, money gets blocked in inventory. If it keeps too little stock, customers may not get the products they need.

So this dashboard focuses on four main areas:

1. Stock health
2. Reorder alerts
3. Supplier and category analysis
4. Inventory value and revenue potential

The dashboard uses a sample inventory dataset with 60 products. It includes product names, categories, suppliers, quantity on hand, reorder levels, unit cost, unit price, lead time, and last restock date.

## 3. Main Idea

The main idea is simple:

Instead of looking at a long spreadsheet, the user can open this dashboard and immediately understand what is happening in the inventory.

The dashboard answers three business questions:

1. What is the current inventory status?
2. Which products need urgent attention?
3. Where is the inventory value concentrated?

This makes the dashboard useful for warehouse managers, store owners, operations teams, and anyone responsible for stock planning.

## 4. First View: KPI Cards

At the top of the dashboard, we can see five KPI cards.

These cards give a quick summary of the full inventory:

- Total SKUs: 60 products
- Inventory Value: about $46,573
- Units in Stock: 3,628 units
- Low-Stock Items: 26 products
- Out of Stock Items: 6 products

This first section is useful because it gives the manager a quick health check. Without opening any chart, we already know that some products need attention because 26 items are low in stock and 6 items are completely out of stock.

## 5. Low Stock Alerts

After the KPI cards, the dashboard shows the Low Stock Alerts section.

This is one of the most important parts of the dashboard because it directly tells the user which products need to be reordered.

The dashboard compares Quantity On Hand with Reorder Level. If the quantity is less than or equal to the reorder level, the item is marked as low stock. If the quantity is zero, it is marked as out of stock.

The table also shows:

- Units short
- Suggested reorder quantity
- Supplier name
- Lead time in days

This helps the manager decide not only what to reorder, but also how urgent the reorder is. For example, if a product has low stock and a long supplier lead time, it should be handled quickly.

## 6. Stock Levels Chart

Next, the Stock Levels tab shows the current stock level of products.

This chart uses colors to separate products by stock status:

- Green means healthy stock
- Orange means low stock
- Red means out of stock

This chart is useful because it makes the stock situation visual. Instead of reading every row in a table, the user can quickly identify which products are healthy and which products are risky.

The table beside the chart works like a detailed inventory ledger. It shows the SKU, product name, category, supplier, quantity, reorder level, stock status, unit cost, inventory value, and last restock date.

## 7. Category Analysis

The Category Analysis tab shows how inventory is distributed across product categories.

The bar chart shows Inventory Value by Category. In this dataset, the highest inventory value is in Groceries, followed by Electronics, Office Supplies, and Apparel & Safety.

This helps answer the question: Which category has the most money invested in stock?

The treemap shows Units on Hand by Category. This helps compare categories visually based on stock quantity.

This section is useful for business planning because the company can see which categories are financially important and which categories may need better stock control.

## 8. Supplier Analysis

The Supplier Analysis tab focuses on supplier dependence.

The first chart shows Inventory Value by Supplier. In this dataset, FreshLine Distributors and Metro Office Mart have the highest inventory value.

The second chart compares Supplier Dependence with Average Lead Time.

This is important because a supplier with high inventory value and long lead time can create risk. If that supplier delays delivery, the business may face stock shortages.

For example, Vertex Traders has an average lead time of about 16.5 days, which is higher than the other suppliers. This tells the manager that products from this supplier may need earlier reorder planning.

## 9. Inventory Valuation

The Inventory Valuation tab shows the financial side of the inventory.

It includes:

- Filtered inventory value
- Potential shelf revenue
- Estimated gross margin

In the full dataset, the inventory value is about $46,573 and the potential shelf revenue is about $81,001.

This means the dashboard is not only checking stock quantity. It also helps understand the money connected to inventory.

The pie charts show inventory value share by category and by supplier. These charts help the business understand where most of its inventory investment is located.

## 10. Filters and Export

The sidebar filters allow the user to filter data by:

- Category
- Supplier
- Stock status

This makes the dashboard interactive. For example, a user can select only low-stock items, or only one supplier, and all the charts update automatically.

At the end, there is also a download option. The user can export the filtered inventory data as a CSV file. This is useful for sharing reports or sending reorder lists to another team.

## 11. Conclusion

To conclude, this Inventory Management Dashboard changes inventory data from a simple spreadsheet into a useful decision-making tool.

It helps the user:

- Understand the current stock position
- Identify low-stock and out-of-stock products
- Analyze suppliers and categories
- Understand inventory value and revenue potential
- Export filtered data for reporting

The main benefit of this dashboard is that it saves time and helps managers take action before stock problems affect customers or business operations.

Thank you.

## Short Presentation Flow

1. Introduce the problem: inventory is difficult to manage from spreadsheets.
2. Explain the idea: convert inventory data into visual insights.
3. Show KPI cards: current business position.
4. Show low-stock alerts: urgent action items.
5. Show stock chart: product-level stock health.
6. Show category analysis: where inventory value is concentrated.
7. Show supplier analysis: supplier risk and lead-time exposure.
8. Show valuation: financial view of stock.
9. Show filters and export: interactive reporting.
10. End with the conclusion: the dashboard supports faster and smarter inventory decisions.

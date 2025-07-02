from sklearn.linear_model import LinearRegression
import numpy as np

from collections import defaultdict
from datetime import datetime

def prepare_sales_data(order_data):
    product_sales = defaultdict(list)

    # Group sales by product
    for order in order_data:
        product = order['product']
        date = order['created_at'].date()
        quantity = order['quantity']
        product_sales[product].append((date, quantity))

    # Aggregate quantity per day
    final_data = {}
    for product, entries in product_sales.items():
        daily = defaultdict(int)
        for date, qty in entries:
            daily[date] += qty
        sorted_dates = sorted(daily.keys())
        base_date = sorted_dates[0]
        X = [(date - base_date).days for date in sorted_dates]
        y = [daily[date] for date in sorted_dates]
        final_data[product] = (X, y)

    return final_data

def predict_next_week_sales(order_data):
    sales_data = prepare_sales_data(order_data)
    predictions = {}

    for product, (X, y) in sales_data.items():
        if len(X) < 2:
            predictions[product] = "Not enough data"
            continue
        model = LinearRegression()
        model.fit(np.array(X).reshape(-1, 1), y)

        next_days = np.array([[max(X)+i] for i in range(1, 8)])
        predicted = model.predict(next_days)
        predicted_total = int(sum(predicted))
        predictions[product] = predicted_total

    return predictions

from collections import defaultdict

def detect(products, payout_lookup, min_profit: float = 1.0):
    grouped = defaultdict(list)
    for p in products:
        # Normalize names to improve matching precision
        name_key = p["name"].strip().lower()
        grouped[name_key].append(p)

    opportunities = []
    for name, items in grouped.items():
        if len(items) < 2:
            continue

        # Optimization: Sort by price to allow early exit or two-pointer approach if scaled
        for buy in items:
            for sell in items:
                # Skip same source or same unique product ID
                if buy["source"] == sell["source"]:
                    continue
                if buy.get("id") == sell.get("id") and buy.get("id") is not None:
                    continue

                buy_price = buy["price"]
                sell_price = sell["price"]

                product_id = str(sell.get("id", ""))
                commission = payout_lookup(sell["source"], product_id)
                if commission is None or not isinstance(commission, (int, float)):
                    continue

                revenue = sell_price * commission
                profit = revenue - buy_price

                # Thresholding for business viability
                if profit > min_profit:
                    opportunities.append(
                        {
                            "product": name,
                            "buy": buy["source"],
                            "sell": sell["source"],
                            "buy_price": buy_price,
                            "sell_price": sell_price,
                            "profit": profit,
                            "commission_rate": commission,
                        }
                    )

    return opportunities

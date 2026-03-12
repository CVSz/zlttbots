from collections import defaultdict
from engine.commission import commission_rate

def detect(products):

    grouped = defaultdict(list)

    for p in products:
        grouped[p["name"]].append(p)

    opportunities = []

    for name,items in grouped.items():

        if len(items) < 2:
            continue

        for buy in items:

            for sell in items:

                if buy["source"] == sell["source"]:
                    continue

                buy_price = buy["price"]
                sell_price = sell["price"]

                commission = commission_rate(sell["source"])

                revenue = sell_price * commission

                profit = revenue - buy_price

                if profit > 1:

                    opportunities.append({
                        "product": name,
                        "buy": buy["source"],
                        "sell": sell["source"],
                        "buy_price": buy_price,
                        "sell_price": sell_price,
                        "profit": profit
                    })

    return opportunities

from collections import defaultdict


def detect(products, payout_lookup):

    grouped = defaultdict(list)

    for p in products:
        grouped[p["name"]].append(p)

    opportunities = []

    for name, items in grouped.items():

        if len(items) < 2:
            continue

        for buy in items:

            for sell in items:

                if buy["source"] == sell["source"]:
                    continue

                buy_price = buy["price"]
                sell_price = sell["price"]

                product_id = str(sell.get("id", ""))
                commission = payout_lookup(sell["source"], product_id)
                if commission is None:
                    continue

                revenue = sell_price * commission

                profit = revenue - buy_price

                if profit > 1:

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

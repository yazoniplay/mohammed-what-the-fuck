from collections import Counter


def seller_report(items):
    sold = [i for i in items if i.get('status') == 'sold']
    brands = Counter()
    profits = []

    for item in sold:
        brand = item.get('brand') or item.get('title', 'Unknown').split(' ')[0]
        brands[brand] += 1
        profits.append(float(item.get('profit', 0)))

    best_brand = brands.most_common(1)[0][0] if brands else 'No data'
    avg_profit = round(sum(profits) / len(profits), 2) if profits else 0

    return {
        'sold_count': len(sold),
        'best_brand': best_brand,
        'average_profit': avg_profit,
        'recommendation': 'Sell more similar items to your profitable listings.' if sold else 'Sell more items to collect data.'
    }

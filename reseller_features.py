"""Reseller automation helpers."""


def calculate_profit(buy_price, sell_price):
    try:
        return float(sell_price) - float(buy_price)
    except (TypeError, ValueError):
        return 0


def listing_quality(item):
    score = 100
    missing = []

    for key, label in [
        ('title', 'title'),
        ('description', 'description'),
        ('brand', 'brand'),
        ('size', 'size'),
        ('condition', 'condition'),
        ('color', 'color')
    ]:
        if not item.get(key) or item.get(key) == 'Okänt':
            score -= 10
            missing.append(label)

    return {
        'score': max(score, 0),
        'missing': missing
    }


def generate_tags(item):
    tags = []
    for key in ['brand', 'product_type', 'category', 'color', 'material']:
        value = item.get(key)
        if value and value != 'Okänt':
            tags.append(str(value).lower().replace(' ', ''))
    return tags

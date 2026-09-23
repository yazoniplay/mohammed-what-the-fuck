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
    return {'score': max(score, 0), 'missing': missing}


def generate_tags(item):
    tags = []
    for key in ['brand', 'product_type', 'category', 'color', 'material']:
        value = item.get(key)
        if value and value != 'Okänt':
            tags.append(str(value).lower().replace(' ', ''))
    return tags


def photo_quality(images):
    issues = []
    count = len(images)
    if count < 3:
        issues.append('Add more photos (front, back, details)')
    if count == 0:
        return {'score': 0, 'issues': ['No photos uploaded']}
    score = 100
    if count < 2:
        score -= 25
    if count < 3:
        score -= 15
    return {'score': max(score, 0), 'issues': issues}


def recommend_price(item):
    """Estimate a Vinted price from available listing data."""
    base = 100
    condition = str(item.get('condition', '')).lower()
    brand = str(item.get('brand', '')).lower()
    if any(x in brand for x in ['nike', 'adidas', 'carhartt', 'ralph']):
        base += 50
    if any(x in condition for x in ['new', 'excellent', 'very good']):
        base += 30
    elif 'bad' in condition or 'poor' in condition:
        base -= 30
    return max(20, base)

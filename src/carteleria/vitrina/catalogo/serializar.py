from decimal import Decimal


def json_default(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "keys") and not isinstance(value, dict):
        try:
            return {k: value[k] for k in value.keys()}
        except Exception:
            pass
    return str(value)


def to_serializable(rows):
    res = []
    if not rows:
        return res
    for row in rows:
        if isinstance(row, dict):
            res.append(dict(row))
        elif hasattr(row, "_mapping"):
            res.append(dict(row._mapping))
        elif hasattr(row, "keys") and callable(row.keys):
            try:
                res.append({k: row[k] for k in row.keys()})
            except Exception:
                res.append(list(row))
        elif isinstance(row, (list, tuple)):
            res.append(list(row))
        else:
            try:
                res.append(dict(row))
            except Exception:
                res.append(str(row))
    return res

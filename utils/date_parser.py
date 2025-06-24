import datetime

FORMAT_MAP = {
    "dd/mm/yyyy": "%d/%m/%Y",
    "mm/dd/yyyy": "%m/%d/%Y",
    "yyyy/mm/dd": "%Y/%m/%d",
    "yyyy/dd/mm": "%Y/%d/%m"
}

def parse_date(date_str, user_format):
    fmt = FORMAT_MAP.get(user_format)
    if not fmt:
        raise ValueError("Invalid date format configured.")
    return datetime.datetime.strptime(date_str, fmt).date()

def format_date(date_obj, user_format):
    fmt = FORMAT_MAP.get(user_format)
    return date_obj.strftime(fmt)

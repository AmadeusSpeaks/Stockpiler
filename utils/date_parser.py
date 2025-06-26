import datetime

FORMAT_MAP = {
    "dd/mm/yyyy": "%d/%m/%Y",
    "mm/dd/yyyy": "%m/%d/%Y",
    "yyyy/mm/dd": "%Y/%m/%d",
    "yyyy/dd/mm": "%Y/%d/%m"
}

def parse_date(date_str, fmt):
    fmt_map = {
        "dd/mm/yyyy": "%d/%m/%Y",
        "mm/dd/yyyy": "%m/%d/%Y",
        "yyyy/mm/dd": "%Y/%m/%d",
        "yyyy/dd/mm": "%Y/%d/%m",
    }
    
    try:
        return datetime.datetime.strptime(date_str, fmt_map[fmt])
    except (ValueError, KeyError):
        try:
            # Try ISO format as fallback
            return datetime.datetime.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"Date '{date_str}' does not match expected format or ISO format.")

def format_date(date_obj, user_format):
    fmt = FORMAT_MAP.get(user_format)
    return date_obj.strftime(fmt)

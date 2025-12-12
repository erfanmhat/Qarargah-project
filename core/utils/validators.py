import re
import datetime
import jdatetime


def parse_jalali_date(val: str) -> datetime.date:
    s = str(val).strip()
    s = s.replace("-", "/")
    if re.fullmatch(r"\d{8}", s):  # 14040918
        y = int(s[0:4]);
        m = int(s[4:6]);
        d = int(s[6:8])
    else:
        parts = s.split("/")
        if len(parts) != 3:
            raise ValueError("فرمت تاریخ نامعتبر است (مثلاً 1404/09/18)")
        y, m, d = map(int, parts)

    jd = jdatetime.date(y, m, d)
    return jd.togregorian()

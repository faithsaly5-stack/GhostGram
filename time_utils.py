from datetime import datetime, timezone, timedelta

def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = gy if gm > 2 else gy - 1
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd

def get_current_persian_datetime() -> str:
    """
    Returns current Persian date, day of week, time, and period of day
    adjusted to Iran Standard Time (UTC+3:30).
    """
    tz_iran = timezone(timedelta(hours=3, minutes=30))
    now = datetime.now(tz_iran)
    
    weekdays = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یکشنبه"]
    weekday_name = weekdays[now.weekday()]
    
    months = [
        "", "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    
    jy, jm, jd = gregorian_to_jalali(now.year, now.month, now.day)
    month_name = months[jm]
    
    hour = now.hour
    if 5 <= hour < 12:
        period = "صبح"
    elif 12 <= hour < 16:
        period = "ظهر / بعدازظهر"
    elif 16 <= hour < 20:
        period = "عصر / غروب"
    elif 20 <= hour < 24:
        period = "شب"
    else:
        period = "بامداد / نصف‌شب"
        
    time_str = now.strftime("%H:%M")
    return f"{weekday_name}، {jd} {month_name} {jy} - ساعت {time_str} ({period})"

{% extends "dashboard/base.html" %}
{% load static %}
{% load jalali %}

{% block title %}داشبورد مدیریت{% endblock %}

{% block content %}
<style>
    /* 1. تعریف متغیرهای رنگی برای حالت روشن (پیش‌فرض) */
    :root, [data-theme="light"] {
        --calc-bg: #ffffff;
        --calc-text-main: #333333;
        --calc-text-label: #555555;
        --calc-border: #e0e0e0;
        --calc-input-bg: #ffffff;
        --calc-input-border: #ced4da;
        --calc-input-text: #333333;
        --calc-shadow: rgba(0, 0, 0, 0.05);
        --calc-btn-bg: #0d6efd;
        --calc-btn-hover: #0b5ed7;
        --calc-success-bg: #d1e7dd;
        --calc-success-text: #0f5132;
        --calc-error-bg: #f8d7da;
        --calc-error-text: #842029;
    }

    /* 2. تعریف متغیرهای رنگی برای حالت تاریک (Dark Mode) */
    [data-theme="dark"] {
        --calc-bg: #1e1e2d; /* رنگ پس‌زمینه کارت در حالت دارک */
        --calc-text-main: #e4e6ef;
        --calc-text-label: #b5b5c3;
        --calc-border: #323248;
        --calc-input-bg: #151521; /* رنگ پس‌زمینه فیلد ورودی */
        --calc-input-border: #323248;
        --calc-input-text: #e4e6ef;
        --calc-shadow: rgba(0, 0, 0, 0.25);
        --calc-btn-bg: #3699ff;
        --calc-btn-hover: #187de4;
        --calc-success-bg: rgba(25, 135, 84, 0.2);
        --calc-success-text: #75b798;
        --calc-error-bg: rgba(220, 53, 69, 0.2);
        --calc-error-text: #ea868f;
    }

    /* 3. استایل‌های اصلی (استفاده از متغیرها) */
    .calc-card {
        background-color: var(--calc-bg);
        border: 1px solid var(--calc-border);
        border-radius: 12px;
        padding: 30px;
        max-width: 450px;
        margin: 20px auto;
        box-shadow: 0 8px 16px var(--calc-shadow);
        font-family: 'IRANSans', Tahoma, sans-serif;
        direction: rtl;
        transition: background-color 0.3s, border-color 0.3s, color 0.3s;
    }

    .calc-card h3 {
        text-align: center;
        color: var(--calc-text-main);
        font-size: 1.4rem;
        margin-bottom: 25px;
        font-weight: bold;
    }

    .form-group {
        margin-bottom: 20px;
    }

    .form-group label {
        display: block;
        font-size: 1.1rem;
        color: var(--calc-text-label);
        margin-bottom: 8px;
        font-weight: 600;
    }

    .form-control {
        width: 100%;
        padding: 12px 15px;
        font-size: 1.2rem;
        background-color: var(--calc-input-bg);
        color: var(--calc-input-text);
        border: 1px solid var(--calc-input-border);
        border-radius: 8px;
        box-sizing: border-box;
        transition: border-color 0.3s, background-color 0.3s, color 0.3s;
        text-align: left;
        direction: ltr;
    }

    .form-control:focus {
        border-color: var(--calc-btn-bg);
        outline: none;
        box-shadow: 0 0 5px rgba(13, 110, 253, 0.25);
    }

    .btn-calc {
        width: 100%;
        background-color: var(--calc-btn-bg);
        color: white;
        border: none;
        padding: 15px;
        font-size: 1.2rem;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.3s, transform 0.1s;
        font-weight: bold;
        margin-top: 10px;
    }

    .btn-calc:hover {
        background-color: var(--calc-btn-hover);
    }

    .btn-calc:active {
        transform: scale(0.98);
    }

    .result-box {
        margin-top: 25px;
        padding: 15px;
        border-radius: 8px;
        font-size: 1.3rem;
        font-weight: bold;
        text-align: center;
        display: none;
    }

    /* یک استایل کمکی برای تیره کردن بک‌گراند تقویم در حالت دارک (اختیاری) */
    [data-theme="dark"] .datepicker-plot-area {
        background-color: var(--calc-bg) !important;
        border-color: var(--calc-border) !important;
        color: var(--calc-text-main) !important;
    }
</style>

<!-- بخش رابط کاربری (HTML) -->
<div class="calc-card">
    <h3>محاسبه‌گر مدت خدمت و مرخصی</h3>

    <div class="form-group">
        <label for="start_date">تاریخ شروع:</label>
        <!-- مقدار پیش‌فرض value حذف شد تا توسط JS از URL خوانده شود -->
        <input type="text" id="start_date" class="form-control p-datepicker" placeholder="1404/04/10" autocomplete="off">
    </div>

    <div class="form-group">
        <label for="end_date">تاریخ پایان:</label>
        <input type="text" id="end_date" class="form-control p-datepicker" placeholder="1404/10/20" autocomplete="off">
    </div>

    <button class="btn-calc" onclick="calculateDifference()">محاسبه اختلاف</button>

    <div id="result" class="result-box"></div>
</div>

<!-- بخش منطق (JavaScript) -->
<script>
    $(document).ready(function() {
        // 1. خواندن پارامترها از URL
        const urlParams = new URLSearchParams(window.location.search);
        const urlStartDate = urlParams.get('start_date');
        const urlEndDate = urlParams.get('end_date');

        // جایگذاری در فیلدها در صورت وجود
        if (urlStartDate) document.getElementById('start_date').value = urlStartDate;
        if (urlEndDate) document.getElementById('end_date').value = urlEndDate;

        // 2. فعال‌سازی Persian Datepicker
        $('.p-datepicker').persianDatepicker({
            format: 'YYYY/MM/DD',
            autoClose: true,
            initialValue: false // برای جلوگیری از اوررایت شدن مقادیر خوانده شده از URL با تاریخ امروز
        });

        // اگر مقادیر از URL لود شده بودند، به صورت خودکار محاسبه را انجام بده
        if (urlStartDate && urlEndDate) {
            calculateDifference();
        }
    });

    // تابع کمکی برای تعداد روزهای ماه‌های شمسی
    function getJalaliDaysInMonth(month) {
        if (month >= 1 && month <= 6) return 31;
        if (month >= 7 && month <= 11) return 30;
        return 29;
    }

    function calculateDifference() {
        const startDateStr = document.getElementById('start_date').value;
        const endDateStr = document.getElementById('end_date').value;
        const resultBox = document.getElementById('result');

        // دریافت متغیرهای رنگی تم فعلی برای اعمال روی پیام نتیجه
        const computedStyles = getComputedStyle(document.documentElement);
        const successBg = computedStyles.getPropertyValue('--calc-success-bg').trim();
        const successText = computedStyles.getPropertyValue('--calc-success-text').trim();
        const errorBg = computedStyles.getPropertyValue('--calc-error-bg').trim();
        const errorText = computedStyles.getPropertyValue('--calc-error-text').trim();

        // تابعی برای نمایش خطا
        const showError = (msg) => {
            resultBox.innerText = msg;
            resultBox.style.backgroundColor = errorBg;
            resultBox.style.color = errorText;
            resultBox.style.border = `1px solid ${errorText}`;
            resultBox.style.display = "block";
        };

        if (!startDateStr || !endDateStr) {
            return showError("لطفا هر دو تاریخ را وارد کنید.");
        }

        const startParts = startDateStr.split('/').map(Number);
        const endParts = endDateStr.split('/').map(Number);

        if (startParts.length !== 3 || endParts.length !== 3 || startParts.includes(NaN) || endParts.includes(NaN)) {
            return showError("فرمت تاریخ نامعتبر است.");
        }

        let y1 = startParts[0], m1 = startParts[1], d1 = startParts[2];
        let y2 = endParts[0], m2 = endParts[1], d2 = endParts[2];

        let yearsDiff = y2 - y1;
        let monthsDiff = m2 - m1;
        let daysDiff = d2 - d1;

        if (daysDiff < 0) {
            monthsDiff--;
            let prevMonth = m2 - 1;
            if (prevMonth === 0) prevMonth = 12;
            daysDiff += getJalaliDaysInMonth(prevMonth);
        }

        if (monthsDiff < 0) {
            yearsDiff--;
            monthsDiff += 12;
        }

        let totalMonths = (yearsDiff * 12) + monthsDiff;

        if (totalMonths < 0 || (totalMonths === 0 && daysDiff < 0)) {
            return showError("تاریخ پایان نمی‌تواند قبل از تاریخ شروع باشد.");
        }

        // نمایش موفقیت آمیز نتیجه
        resultBox.innerText = `اختلاف: ${totalMonths} ماه و ${daysDiff} روز`;
        resultBox.style.backgroundColor = successBg;
        resultBox.style.color = successText;
        resultBox.style.border = `1px solid ${successText}`;
        resultBox.style.display = "block";
    }

    // آپدیت کردن رنگ‌های Result Box وقتی کاربر همزمان با نمایش نتیجه، تم را عوض می‌کند
    window.addEventListener('themechange', function() {
        const resultBox = document.getElementById('result');
        if (resultBox.style.display === "block") {
            calculateDifference(); // فراخوانی مجدد برای اعمال رنگ‌های تم جدید روی باکس نتیجه
        }
    });
</script>
{% endblock %}

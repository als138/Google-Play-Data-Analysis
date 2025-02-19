import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# فرض کنید API شما در localhost:8000 اجرا می‌شود
API_URL = "http://localhost:8000"

st.title("داشبورد گوگل پلی استور")

# دریافت دسته‌بندی‌ها از API
@st.cache_data(ttl=600)
def fetch_categories():
    response = requests.get(f"{API_URL}/categories")
    if response.status_code == 200:
        # انتظار داریم API لیستی از دیکشنری‌ها مانند [{"id": 1, "name": "Social"}, ...] برگرداند
        return response.json()
    else:
        st.error("خطا در دریافت دسته‌بندی‌ها از API")
        return []

categories_data = fetch_categories()
# ساخت لیست نمایش: گزینه "All" به عنوان انتخاب همه، سپس نام دسته‌ها
if categories_data:
    category_names = ["All"] + [cat["name"] for cat in categories_data]
else:
    category_names = ["All"]

# بخش فیلتر کردن اپلیکیشن‌ها
st.header("فیلتر اپلیکیشن‌ها")
selected_category = st.selectbox("دسته‌بندی", category_names)
min_rating = st.slider("حداقل امتیاز", 0.0, 5.0, 3.0, 0.1)
free_only = st.checkbox("فقط اپلیکیشن‌های رایگان", value=True)

if st.button("اعمال فیلتر"):
    # در صورتی که دسته "All" انتخاب باشد، پارامتر category ارسال نمی‌شود.
    params = {"min_rating": min_rating, "free": free_only}
    if selected_category != "All":
        params["category"] = selected_category
    
    response = requests.get(f"{API_URL}/apps/filter", params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)
        st.dataframe(df)
        
        # نمایش نمودار توزیع امتیاز در صورت وجود ستون "rating"
        if not df.empty and "rating" in df.columns:
            fig = px.histogram(df, x="rating", title="توزیع امتیاز")
            st.plotly_chart(fig)
    else:
        st.error("خطا در دریافت اطلاعات از API")

# نمایش نمودار میانگین امتیاز هر دسته
if st.button("میانگین امتیاز هر دسته"):
    response = requests.get(f"{API_URL}/apps/average_rating")
    if response.status_code == 200:
        data = response.json()
        df_avg = pd.DataFrame(data)
        fig = px.bar(df_avg, x="category", y="average_rating", title="میانگین امتیاز هر دسته")
        st.plotly_chart(fig)
    else:
        st.error("خطا در دریافت اطلاعات از API")

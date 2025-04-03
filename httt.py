import streamlit as st
import pandas as pd
import requests
import re
from PIL import Image
from io import BytesIO

API_KEY = "AIzaSyANUWlnh43MDqZ3SS0DqCRiR8ns_5aP5DY"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/channels"

def get_channel_id(url):
    response = requests.get(url)
    if response.status_code != 200:
        return "Lỗi: Không thể truy cập trang"
    
    match = re.search(r'"externalId":"(UC[\w-]+)"', response.text)
    return match.group(1) if match else "Không tìm thấy channel_id"

def crawl(url_channel):
    channel_id = get_channel_id(url_channel)
    if not channel_id:
        return {"Error": "Không thể xác định Channel ID từ URL"}
    
    params = {"part": "snippet,statistics", "id": channel_id, "key": API_KEY}
    response = requests.get(YOUTUBE_API_URL, params=params)
    data = response.json()
    if "items" not in data or not data["items"]:
        return {"Error": "Không tìm thấy dữ liệu cho kênh này"}
    
    channel_info = data["items"][0]
    snippet = channel_info["snippet"]
    stats = channel_info["statistics"]
    
    return {
        "Created": snippet.get("publishedAt", "N/A")[:10],
        "Add_to_ViralStat": "N/A",
        "Country": snippet.get("country", "N/A"),
        "Subscribers": int(stats.get("subscriberCount", 0)),
        "Total_videos": int(stats.get("videoCount", 0)),
        "Avatar": snippet["thumbnails"]["high"]["url"] if "thumbnails" in snippet else None,
        "Description": snippet.get("description", "Không có mô tả"),
        "List_id": channel_id
    }

def save(file_csv):
    df = pd.DataFrame([file_csv])  # Chuyển dictionary thành DataFrame
    csv_bytes = BytesIO()
    df.to_csv(csv_bytes, index=False, encoding="utf-8-sig")  # Lưu file với UTF-8 (hỗ trợ tiếng Việt)
    csv_bytes.seek(0)
    return csv_bytes

def profile_overview(uploaded_file):
    df = pd.read_csv(uploaded_file)
    st.write("Column names:", df.columns.tolist())  # Print column names for debugging
    return {
        "Created": df['Created'].iloc[0] if 'Created' in df.columns else "N/A",
        "Add_to_ViralStat": df['Add_to_ViralStat'].iloc[0] if 'Add_to_ViralStat' in df.columns else "N/A",
        "Country": df['Country'].iloc[0] if 'Country' in df.columns else "N/A",
        "Subscribers": df['Subscribers'].iloc[0] if 'Subscribers' in df.columns else 0,
        "Total_videos": df['Total_videos'].iloc[0] if 'Total_videos' in df.columns else 0
    }

def profile_stats(uploaded_file):
    df = pd.read_csv(uploaded_file)
    st.write("Column names:", df.columns.tolist())  # Print column names for debugging
    return {
        "Subscribers": df['Subscribers'].sum() if 'Subscribers' in df.columns else 0,
        "Total_view": df['Total_view'].sum() if 'Total_view' in df.columns else 0,
        "Avg": df['Avg'].mean() if 'Avg' in df.columns else 0
    }

def analyze_comments(uploaded_file):
    df = pd.read_csv(uploaded_file)
    st.write("Column names:", df.columns.tolist())  # Print column names for debugging
    # Placeholder for comment analysis logic
    return {
        "Positive_comments": df['Positive_comments'].sum() if 'Positive_comments' in df.columns else 0,
        "Negative_comments": df['Negative_comments'].sum() if 'Negative_comments' in df.columns else 0,
        "Neutral_comments": df['Neutral_comments'].sum() if 'Neutral_comments' in df.columns else 0
    }

def recommend_videos(uploaded_file):
    df = pd.read_csv(uploaded_file)
    st.write("Column names:", df.columns.tolist())  # Print column names for debugging
    # Placeholder for recommendation logic
    return {
        "Recommended_videos": ["Video1", "Video2", "Video3"]  # Example recommendations
    }

def main():
    st.set_page_config(layout="wide")
    st.sidebar.title("Chức năng")
    page = st.sidebar.radio("Chọn trang", ["Tổng quan", "Crawl", "Statistical", "Phân tích comment", "Đề xuất"])
    
    if page == "Tổng quan":
        st.title("Tổng quan")
        uploaded_file = st.file_uploader("Tải lên file CSV", type=["csv"])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.dataframe(df)
    
    elif page == "Crawl":
        st.title("Crawl dữ liệu")
        url = st.text_input("Nhập URL kênh")
        
        if st.button("Tìm kiếm"):
            data = crawl(url)
            if "Error" in data:
                st.error(data["Error"])
            else:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if data["Avatar"]:
                        response = requests.get(data["Avatar"])
                        image = Image.open(BytesIO(response.content))
                        st.image(image, width=100)
                    else:
                        st.warning("Không tìm thấy ảnh đại diện.")
                with col2:
                    st.markdown("**Kênh YouTube**")
                    st.text(f"Created: {data['Created']}")
                    st.text(f"Added to ViralStat: {data['Add_to_ViralStat']}")
                    st.text(f"Country: {data['Country']}")
                    st.text(f"List ID: {data['List_id']}")
                    st.markdown("**Description:**")
                    st.write(data["Description"])
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.text("Subscribers")
                    st.markdown(f"### {data['Subscribers']}")
                with col2:
                    st.text("Total_videos")
                    st.markdown(f"### {data['Total_videos']}")
                
                st.session_state.crawled_data = data
        
        if "crawled_data" in st.session_state:
            if st.button("Lưu CSV"):
                data = st.session_state.crawled_data
                csv_bytes = save(data)
        
                st.success("Đã tạo file CSV! Nhấn nút dưới đây để tải về.")
                st.download_button(
                    label="📥 Tải xuống CSV",
                    data=csv_bytes,
                    file_name="youtube_channel_data.csv",
                    mime="text/csv"
                )
    
    elif page == "Statistical":
        st.title("Thống kê")
        uploaded_file = st.file_uploader("Tải lên file CSV", type=["csv"])
        if uploaded_file:
            overview_data = profile_overview(uploaded_file)
            stats_data = profile_stats(uploaded_file)
            
            st.markdown("**Profile Overview**")
            st.text(f"Created: {overview_data['Created']}")
            st.text(f"Added to ViralStat: {overview_data['Add_to_ViralStat']}")
            st.text(f"Country: {overview_data['Country']}")
            st.text(f"Subscribers: {overview_data['Subscribers']}")
            st.text(f"Total_videos: {overview_data['Total_videos']}")
            
            st.markdown("**Profile Stats**")
            st.text(f"Subscribers: {stats_data['Subscribers']}")
            st.text(f"Total_view: {stats_data['Total_view']}")
            st.text(f"Avg: {stats_data['Avg']}")
    
    elif page == "Phân tích comment":
        st.title("Phân tích comment")
        uploaded_file = st.file_uploader("Tải lên file CSV", type=["csv"])
        if uploaded_file:
            comment_data = analyze_comments(uploaded_file)
            
            st.markdown("**Comment Analysis**")
            st.text(f"Positive comments: {comment_data['Positive_comments']}")
            st.text(f"Negative comments: {comment_data['Negative_comments']}")
            st.text(f"Neutral comments: {comment_data['Neutral_comments']}")
    
    elif page == "Đề xuất":
        st.title("Đề xuất video")
        uploaded_file = st.file_uploader("Tải lên file CSV", type=["csv"])
        if uploaded_file:
            recommendation_data = recommend_videos(uploaded_file)
            
            st.markdown("**Video Recommendations**")
            for video in recommendation_data["Recommended_videos"]:
                st.text(video)

if __name__ == "__main__":
    main()

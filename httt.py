import streamlit as st
import pandas as pd
import requests
import re
from io import BytesIO
from PIL import Image

API_KEY = "AIzaSyANUWlnh43MDqZ3SS0DqCRiR8ns_5aP5DY"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_VIDEO_API_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_COMMENTS_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"


def get_channel_id(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    match = re.search(r'"externalId":"(UC[\w-]+)"', response.text)
    return match.group(1) if match else None


def get_recent_videos(channel_id):
    """Lấy 10 video gần nhất của kênh."""
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 10,
        "order": "date",
        "type": "video",
        "key": API_KEY
    }
    response = requests.get(YOUTUBE_VIDEO_API_URL, params=params)
    data = response.json()

    if "items" not in data:
        return []

    videos = []
    video_ids = []

    for item in data["items"]:
        video_id = item["id"]["videoId"]
        video_ids.append(video_id)
        videos.append({
            "channel_name": item["snippet"]["channelTitle"],
            "title": item["snippet"]["title"],
            "published_date": item["snippet"]["publishedAt"],
            "id": video_id,
            "link": f"https://www.youtube.com/watch?v={video_id}"
        })

    # Gọi API để lấy số lượt xem và số bình luận
    stats_url = "https://www.googleapis.com/youtube/v3/videos"
    stats_params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    stats_response = requests.get(stats_url, params=stats_params)
    stats_data = stats_response.json()

    stats_dict = {item["id"]: item["statistics"] for item in stats_data.get("items", [])}

    for v in videos:
        vid = v["id"]
        v["views"] = stats_dict.get(vid, {}).get("viewCount", "N/A")
        v["comments"] = stats_dict.get(vid, {}).get("commentCount", "N/A")

    return videos


def get_all_comments(video_id, channel_id, video_title):
    """Lấy toàn bộ bình luận từ video."""
    comments_list = []
    next_page_token = None

    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,
            "textFormat": "plainText",
            "key": API_KEY
        }
        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(YOUTUBE_COMMENTS_API_URL, params=params)
        comments_data = response.json()

        if "items" in comments_data:
            for item in comments_data["items"]:
                comment_snippet = item["snippet"]["topLevelComment"]["snippet"]
                comments_list.append({
                    "channel_id": channel_id,  # Thêm channelID
                    "video_id": video_id,      # Thêm videoID
                    "video_title": video_title,  # Thêm Title video
                    "author": comment_snippet["authorDisplayName"],
                    "comment": comment_snippet["textDisplay"],
                    "publishedAt": comment_snippet["publishedAt"]
                })

        next_page_token = comments_data.get("nextPageToken")
        if not next_page_token:
            break

    return comments_list

# Cập nhật phần crawl để hiển thị thông tin bình luận
def crawl(url_channel):
    """Crawl thông tin kênh và danh sách video."""
    channel_id = get_channel_id(url_channel)
    if not channel_id:
        return None

    params = {"part": "snippet,statistics", "id": channel_id, "key": API_KEY}
    response = requests.get(YOUTUBE_API_URL, params=params)
    data = response.json()

    if "items" not in data or not data["items"]:
        return None

    channel_info = data["items"][0]
    snippet = channel_info["snippet"]
    stats = channel_info["statistics"]

    recent_videos = get_recent_videos(channel_id)

    return {
        "Created": snippet.get("publishedAt", "N/A")[:10],
        "Country": snippet.get("country", "N/A"),
        "Subscribers": int(stats.get("subscriberCount", 0)),
        "Total_videos": int(stats.get("videoCount", 0)),
        "Avatar": snippet["thumbnails"]["high"]["url"] if "thumbnails" in snippet else None,
        "Description": snippet.get("description", "Không có mô tả"),
        "List_id": channel_id,
        "Recent_videos": recent_videos
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
            st.session_state["channel_data"] = crawl(url)
            if st.session_state["channel_data"] is None:
                st.error("Không tìm thấy dữ liệu!")
                st.stop()

        # Nếu đã có dữ liệu kênh
        if "channel_data" in st.session_state:
            data = st.session_state["channel_data"]

            col1, col2 = st.columns([1, 3])
            with col1:
                if data["Avatar"]:
                    response = requests.get(data["Avatar"])
                    image = Image.open(BytesIO(response.content))
                    st.image(image, width=100)
            with col2:
                st.write(f"**Created:** {data['Created']}")
                st.write(f"**Country:** {data['Country']}")
                st.write(f"**Subscribers:** {data['Subscribers']}")
                st.write(f"**Total Videos:** {data['Total_videos']}")
                st.write(f"**Description:** {data['Description']}")
            st.write("**Danh sách 10 video gần nhất**")
            # 🟢 Lưu danh sách video vào session_state để tránh reload mất dữ liệu
            if "Recent_videos" not in st.session_state:
                st.session_state["Recent_videos"] = data["Recent_videos"]
                
            df_videos = pd.DataFrame(st.session_state["Recent_videos"])
            # 🟢 Thêm phần tải về CSV
            if not df_videos.empty:
                csv_data = df_videos.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="Tải danh sách video gần nhất về máy",
                    data=csv_data,
                    file_name="recent_videos.csv",
                    mime="text/csv"
                )

            # 🟢 Dropdown chọn video
            video_ids = [video["id"] for video in st.session_state["Recent_videos"]]
            selected_video_id = st.selectbox("Chọn video:", video_ids, format_func=lambda vid: next(v["title"] for v in st.session_state["Recent_videos"] if v["id"] == vid))

            # 🟢 Hiển thị thông tin video đã chọn
            selected_video = next(v for v in st.session_state["Recent_videos"] if v["id"] == selected_video_id)
            st.write(f"**Tiêu đề video:** {selected_video['title']}")
            st.write(f"**Lượt xem:** {selected_video['views']}")
            st.write(f"**Số bình luận:** {selected_video['comments']}")
            

            # 🟢 Lấy bình luận chỉ khi chưa có
            if "video_comments" not in st.session_state or st.session_state["video_comments"]["video_id"] != selected_video_id:
                st.session_state["video_comments"] = {"video_id": selected_video_id, "comments": get_all_comments(selected_video_id, data['List_id'], selected_video['title'])}

            # 🟢 Hiển thị bình luận
            df_comments = pd.DataFrame(st.session_state["video_comments"]["comments"])
            st.dataframe(df_comments)

            # 🟢 Thêm phần tải về CSV
            if not df_comments.empty:
                csv_data = df_comments.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    label="Tải bảng bình luận về máy",
                    data=csv_data,
                    file_name="comments.csv",
                    mime="text/csv"
                )
            # 🟢 Nút lấy toàn bộ comment của tất cả video
            if st.button("Lấy toàn bộ bình luận của 10 video"):
                all_comments = []
                for video in st.session_state["Recent_videos"]:
                    st.info(f"Đang lấy bình luận từ video: {video['title']}")
                    comments = get_all_comments(video["id"], data["List_id"], video["title"])
                    all_comments.extend(comments)

                # Lưu toàn bộ comment vào session
                st.session_state["all_video_comments"] = all_comments
                st.success("Đã lấy xong toàn bộ bình luận!")

            # 🟢 Hiển thị bảng toàn bộ bình luận nếu có
            if "all_video_comments" in st.session_state:
                df_all_comments = pd.DataFrame(st.session_state["all_video_comments"])
                
                if not df_all_comments.empty:
                    st.write("### Toàn bộ bình luận của tất cả các video")
                    st.dataframe(df_all_comments)

                    # Tải về CSV
                    csv_data = df_all_comments.to_csv(index=False, encoding="utf-8-sig")
                    st.download_button(
                        label="Tải toàn bộ bình luận về máy",
                        data=csv_data,
                        file_name="all_video_comments.csv",
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

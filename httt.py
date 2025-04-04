import streamlit as st
import pandas as pd
import requests
import re
from PIL import Image
from io import BytesIO

API_KEY = "AIzaSyANUWlnh43MDqZ3SS0DqCRiR8ns_5aP5DY"
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/channels"
YOUTUBE_VIDEO_API_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_COMMENTS_API_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

def get_channel_id(url):
    response = requests.get(url)
    if response.status_code != 200:
        return "Lỗi: Không thể truy cập trang"
    
    match = re.search(r'"externalId":"(UC[\w-]+)"', response.text)
    return match.group(1) if match else "Không tìm thấy channel_id"

def get_recent_videos(channel_id):
    # Bước 1: Lấy 10 video gần nhất
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

    # Bước 2: Gọi API videos để lấy views và comments
    stats_url = "https://www.googleapis.com/youtube/v3/videos"
    stats_params = {
        "part": "statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    stats_response = requests.get(stats_url, params=stats_params)
    stats_data = stats_response.json()

    stats_dict = {}
    for item in stats_data.get("items", []):
        stats_dict[item["id"]] = {
            "views": item["statistics"].get("viewCount", "N/A"),
            "comments": item["statistics"].get("commentCount", "N/A")
        }

    # Bước 3: Gộp lại với danh sách video
    for v in videos:
        vid = v["id"]
        v["views"] = stats_dict.get(vid, {}).get("views", "N/A")
        v["comments"] = stats_dict.get(vid, {}).get("comments", "N/A")

    return videos

def get_all_comments(video_id, channel_name, video_title):
    """Lấy toàn bộ bình luận từ video bằng cách xử lý nextPageToken."""
    comments_list = []
    next_page_token = None

    while True:
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,  # Số lượng tối đa mỗi lần request
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
                    "channelID": channel_name,
                    "videoID": video_id,
                    "Title": video_title,
                    "comment": comment_snippet["textDisplay"],
                    "authorDisplayName": comment_snippet["authorDisplayName"],
                    "publishedAt": comment_snippet["publishedAt"]
                })

        # Kiểm tra nếu còn trang tiếp theo
        next_page_token = comments_data.get("nextPageToken")
        if not next_page_token:
            break  # Dừng khi không còn bình luận nào nữa

    return comments_list


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
                    st.text(f"Added to ViralStat: {data.get('Add_to_ViralStat', 'N/A')}")
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

                # 🟢 Hiển thị danh sách 10 video gần nhất
                if "Recent_videos" in data and data["Recent_videos"]:
                    st.markdown("### 📺 Danh sách 10 video gần nhất")
                    df_videos = pd.DataFrame(data["Recent_videos"])
                    
                    # Cho phép chọn một video
                    selected_video_index = st.selectbox("Chọn một video để xem chi tiết:", df_videos.index, format_func=lambda x: df_videos.iloc[x]["title"])
                    
                    # Lấy dữ liệu của video đã chọn
                    selected_video = df_videos.iloc[selected_video_index]
                    
                    # Hiển thị thông tin chi tiết về video đã chọn
                    st.markdown("### 🎥 Chi tiết Video đã chọn")
                    st.write(f"**Tiêu đề:** {selected_video['title']}")
                    st.write(f"**Video ID:** {selected_video['id']}")
                    st.write(f"**Lượt xem:** {selected_video['views']}")
                    st.write(f"**Số bình luận:** {selected_video['comments']}")
                    
                    st.info("🔄 Đang lấy toàn bộ bình luận, vui lòng chờ...")
            comments_list = get_all_comments(selected_video["id"], selected_video["channel_name"], selected_video["title"])

            if comments_list:
                df_comments = pd.DataFrame(comments_list)
                
                st.markdown("### 💬 Danh sách bình luận")
                st.dataframe(df_comments)

                # Nút tải về file CSV
                csv_file = BytesIO()
                df_comments.to_csv(csv_file, index=False, encoding="utf-8-sig")
                csv_file.seek(0)

                st.download_button(
                    label="📥 Tải về CSV",
                    data=csv_file,
                    file_name=f"{selected_video['id']}_comments.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Không tìm thấy bình luận nào cho video này!")

    
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

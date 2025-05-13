import streamlit as st
import requests
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import math
import altair as alt
from datetime import datetime, timedelta
import random

# Set page config
st.set_page_config(
    page_title="YouTube Trends Analyzer",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    /* Main styles */
    .main {
        background-color: #f9f9f9;
    }
    
    /* Header styles */
    .header-container {
        background-color: #FF0000;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    /* Card styles */
    .video-card {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        padding: 1rem;
        transition: transform 0.3s;
    }
    .video-card:hover {
        transform: translateY(-5px);
    }
    
    /* Metric styles */
    .metric-container {
        background-color: #f0f0f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Button styles */
    .stButton>button {
        background-color: #FF0000;
        color: white;
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        border: none;
        font-weight: bold;
    }
    
    /* Tab styles */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        # background-color: #f0f0f0;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding: 15px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF0000;
        color: white;
    }
    
    /* Section headers */
    h1, h2, h3 {
        color: #212121;
    }
    
    /* Video statistics styles */
    .stats-container {
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
    }
    .stat-item {
        text-align: center;
        padding: 0.5rem;
        flex: 1;
        min-width: 100px;
    }
    
    /* Recommendation box */
    .recommendation-box {
        background-color: #f8f9fa;
        border-left: 4px solid #FF0000;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    /* Loading spinner */
    .stSpinner > div > div {
        border-top-color: #FF0000 !important;
    }
    
    /* Make metric values stand out */
    .big-metric {
        font-size: 24px;
        font-weight: bold;
        color: #FF0000;
    }
    
    /* Custom tag style */
    .tag {
        background-color: #e0e0e0;
        padding: 5px 10px;
        border-radius: 15px;
        margin-right: 5px;
        margin-bottom: 5px;
        display: inline-block;
        font-size: 0.8rem;
    }
    
    /* Success metrics box */
    .success-metric-box {
        background-color: #f0f8ff;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border-left: 4px solid #4285f4;
    }
    
    /* Custom expander styling */
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #212121;
    }
    
    /* Thumbnail hover effect */
    .thumbnail-container {
        position: relative;
        overflow: hidden;
        border-radius: 8px;
    }
    .thumbnail-container img {
        transition: transform 0.3s;
    }
    .thumbnail-container:hover img {
        transform: scale(1.05);
    }
    
    /* Video grid layout */
    .video-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
    }
    
    .recommendation-box, .success-metric-box {
        height: 200px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_video_thumbnail(video_id):
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

def format_number(num):
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    else:
        return str(num)

def get_engagement_color(rate):
    if rate > 0.1:  # 10% or higher
        return "#4CAF50"  # Green
    elif rate > 0.05:  # 5-10%
        return "#2196F3"  # Blue
    elif rate > 0.02:  # 2-5%
        return "#FF9800"  # Orange
    else:
        return "#F44336"  # Red

def create_wordcloud(keywords):
    # Create word frequency dictionary
    word_freq = {}
    for item in keywords:
        word_freq[item[0]] = item[1]
    
    # Generate WordCloud
    wordcloud = WordCloud(
        width=800, 
        height=400, 
        background_color='white',
        colormap='viridis',
        max_words=100,
        contour_width=1,
        contour_color='steelblue'
    ).generate_from_frequencies(word_freq)
    
    return wordcloud

def create_radar_chart(video_data):
    # Normalize metrics for radar chart
    
    # st.write(video_data['statistics'])
    metrics = {
        'View/Sub Ratio': min(1.0, video_data['statistics']['views'] / (video_data['statistics']['subscribers'] or 100000)),
        'Engagement Rate': video_data['statistics']['engagement_rate']/10,
        'Like/View Ratio': video_data['statistics']['likes'] / video_data['statistics']['views']*10 if video_data['statistics']['views'] > 0 else 0,
        'Comment/View Ratio': video_data['statistics']['comments'] / video_data['statistics']['views']*100 if video_data['statistics']['views'] > 0 else 0,
        'Views/Day': min(1.0, video_data['statistics'].get('views_per_day', 0) / 500000)
    }
    
    # st.write(metrics)
    
    categories = list(metrics.keys())
    values = list(metrics.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Performance',
        line_color='#FF0000',
        fillcolor='rgba(255, 0, 0, 0.2)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=False,
        margin=dict(l=70, r=70, t=20, b=20),
        height=300
    )
    
    return fig

def display_video_card(video, is_detailed=False):
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class="thumbnail-container">
            <a href="{video.get('video_url')}">
                <img src="{get_video_thumbnail(video['video_id'])}" width="100%" alt="Video thumbnail">
            </a>
        </div>
        """, unsafe_allow_html=True)
        
        if is_detailed and 'statistics' in video:
            radar_chart = create_radar_chart(video)
            st.plotly_chart(radar_chart, use_container_width=True)
    
    with col2:
        st.markdown(f"### [{video['title']}]({video.get('video_url')}) ")
        
        if 'description' in video and len(video['description']) > 0:
            with st.expander("Description"):
                st.write(video['description'][:300] + ("..." if len(video['description']) > 300 else ""))
        
        if 'statistics' in video:
            stats_cols = st.columns(4)
            with stats_cols[0]:
                st.metric("Views", format_number(video['statistics'].get('views', 0)))
            with stats_cols[1]:
                st.metric("Likes", format_number(video['statistics'].get('likes', 0)))
            with stats_cols[2]:
                st.metric("Comments", format_number(video['statistics'].get('comments', 0)))
            # with stats_cols[3]:
            #     engagement = video['statistics'].get('engagement_rate', 0)
            #     st.markdown(f"""
            #     <div style="text-align: center;">
            #         <p>Engagement</p>
            #         <p style="color: {get_engagement_color(engagement)}; font-size: 1.5rem; font-weight: bold;">
            #             {engagement:.1%}
            #         </p>
            #     </div>
            #     """, unsafe_allow_html=True)
        
        if is_detailed and 'analysis' in video:
            with st.expander("Content Analysis"):
                st.write(video['analysis'])
        
        if is_detailed and 'current_trends' in video:
            with st.expander("Trends"):
                st.markdown("#### Current Trends")
                st.write(video['current_trends'])
                if 'future_trends' in video:
                    st.markdown("#### Future Predictions")
                    st.write(video['future_trends'])

# Main app
def main():
    # Header
    st.markdown("""
    <div class="header-container">
        <h1>🎬 YouTube Trends Analyzer</h1>
        <p>Analyze YouTube content trends and get actionable marketing insights</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e1/Logo_of_YouTube_%282015-2017%29.svg", width=200)
    st.sidebar.title("Search Parameters")
    
    # Input form
    with st.sidebar.form("search_form"):
        prompt = st.text_area("What type of content are you looking to create?", 
                            "AI Agents")
        
        content_type = st.selectbox(
            "Content Type",
            ["shorts", "videos", "both"],
            index=2,
            help="Select the type of content you want to analyze"
        )
        
        region_code = st.selectbox(
            "Region",
            ["US", "IN", "GB", "CA", "AU", "DE", "FR", "JP", "KR", "BR", "RU"],
            index=1,
            help="Select the target region for your content"
        )
        
        submit_button = st.form_submit_button("Analyze Content")
    
    # Display sample data or processed results
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    
    if submit_button:
        with st.spinner("Analyzing YouTube trends... This may take a few minutes..."):
            try:
                # Make API call to the Flask backend
                response = requests.post(
                    "https://youtube-trend-api.onrender.com/analyze-shorts",
                    json={
                        "prompt": prompt,
                        "content_type": content_type,
                        "region_code": region_code
                    },
                    timeout=300  # Increased timeout for longer API calls
                )
                
                if response.status_code == 200:
                    st.session_state.analysis_data = response.json()['data']['marketing_strategy']
                    st.success("Analysis complete! Scroll down to see results.")
                else:
                    st.error(f"Error: {response.json().get('message', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error connecting to API: {str(e)}")
    
    # Display results if available
    if st.session_state.analysis_data:
        data = st.session_state.analysis_data
        
        # Main tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🎥 Analyzed Videos", "📈 Content Strategy", "🔍 All Videos"])
        
        with tab1:
            # Overview section
            st.markdown("## 📊 Content Strategy Overview")
            
            # Target audience and goal
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div class="recommendation-box">
                    <h3>🎯 Target Audience</h3>
                    <p>{}</p>
                </div>
                """.format(data.get('target_audience', 'Not specified')), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="recommendation-box">
                    <h3>🚀 Intent</h3>
                    <p>{}</p>
                </div>
                """.format(data.get('overall_goal', 'Not specified')), unsafe_allow_html=True)
            
            # Keywords analysis
            st.markdown("### 🔑 Top Keywords Analysis")
            if 'recommended_tags_and_keywords' in data.get('marketing_tactics', {}):
                keywords = data['marketing_tactics']['recommended_tags_and_keywords']
                
                # Create two columns for wordcloud and bar chart
                keyword_cols = st.columns([3, 2])
                
                with keyword_cols[0]:
                    # Generate word cloud
                    wordcloud = create_wordcloud(keywords)
                    plt.figure(figsize=(10, 5))
                    plt.imshow(wordcloud, interpolation='bilinear')
                    plt.axis("off")
                    st.pyplot(plt)
                
                with keyword_cols[1]:
                    # Create a bar chart for top keywords
                    sorted_keywords = sorted(keywords, key=lambda x: x[1], reverse=True)[:10]
                    keyword_df = pd.DataFrame(sorted_keywords, columns=['Keyword', 'Count'])
                    
                    chart = alt.Chart(keyword_df).mark_bar().encode(
                        y=alt.Y('Keyword:N', sort='-x', title=None),
                        x=alt.X('Count:Q', title='Frequency'),
                        color=alt.Color('Count:Q', scale=alt.Scale(scheme='reds'), legend=None),
                        tooltip=['Keyword', 'Count']
                    ).properties(
                        height=300
                    )
                    
                    st.altair_chart(chart, use_container_width=True)
            
            # Current trends and future predictions
            st.markdown("### 🔮 Trend Analysis")
            trend_cols = st.columns(2)
            
            with trend_cols[0]:
                st.markdown("""
                <div class="recommendation-box" style="border-left: 4px solid #FF9800;">
                    <h3>📊 Current Trends</h3>
                    <p>{}</p>
                </div>
                """.format(data.get('trend_analysis', {}).get('current_trends', 'Not specified')), unsafe_allow_html=True)
            
            with trend_cols[1]:
                st.markdown("""
                <div class="recommendation-box" style="border-left: 4px solid #2196F3;">
                    <h3>🚀 Future Predictions</h3>
                    <p>{}</p>
                </div>
                """.format(data.get('trend_analysis', {}).get('future_predictions', 'Not specified')), unsafe_allow_html=True)
        
        with tab2:
            # Analyzed Videos section
            st.markdown("## 🎥 Analyzed Videos")
            
            if 'analyzed_videos' in data.get('videos', {}):
                for i, video in enumerate(data['videos']['analyzed_videos']):
                    st.markdown(f"""<div class="video-card">""", unsafe_allow_html=True)
                    st.subheader(f"Video {i+1}: {'Trending' if i==0 else 'Search'} Analysis")
                    display_video_card(video, is_detailed=True)
                    st.markdown("""</div>""", unsafe_allow_html=True)
                    
                    # Specific video metrics
                    if 'statistics' in video:
                        st.markdown("#### 📊 Video Performance Metrics")
                        metrics_cols = st.columns(3)
                        
                        with metrics_cols[0]:
                            # Views over time chart - Fix potential missing or zero views_per_day
                            # Calculate views_per_day if not present
                            if 'views_per_day' not in video['statistics'] or video['statistics']['views_per_day'] == 0:
                                # Estimate views per day based on total views divided by estimated age of video (default 30 days if not available)
                                video_age_days = video['statistics']['video_age_days']
                                if video_age_days == 0:  # Avoid division by zero
                                    video_age_days = 1
                                views_per_day = video['statistics']['views'] / video_age_days
                            else:
                                views_per_day = video['statistics']['views_per_day']
                            
                            # Ensure we have a reasonable value for visualization
                            views_per_day = max(1, views_per_day)  # Minimum 1 view per day
                            days = 30
                            cumulative_views = []
                            daily_views = []
                            
                            # Generate a more realistic view growth pattern
                            view_multipliers = [random.uniform(0.1, 10) for _ in range(5)] + \
                                            [random.uniform(0.1, 1.2) for _ in range(15)] + \
                                            [random.uniform(0.1, 1.0) for _ in range(10)]
                            
                            random.shuffle(view_multipliers)
                            
                            for d in range(days):
                                # Add randomness to daily views with more variance at the beginning
                                daily_view = max(1, views_per_day * view_multipliers[d])
                                daily_views.append(daily_view)
                                cumulative_views.append(sum(daily_views))
                            
                            views_df = pd.DataFrame({
                                'Day': list(range(1, days+1)),
                                'Views': cumulative_views
                            })
                            
                            views_chart = alt.Chart(views_df).mark_area(
                                color='#FF0000',
                                opacity=0.3,
                                line={
                                    'color': '#FF0000', 
                                    'size': 2
                                }
                            ).encode(
                                x=alt.X('Day:Q', title='Days Since Publishing'),
                                y=alt.Y('Views:Q', title='Cumulative Views'),
                                tooltip=['Day', alt.Tooltip('Views:Q', format=',')]
                            ).properties(
                                title='Projected View Growth',
                                height=250
                            )
                            
                            st.altair_chart(views_chart, use_container_width=True)
                        
                        with metrics_cols[1]:
                            # Engagement metrics comparison - Fix for potential zero values
                            views = max(1, video['statistics']['views'])  # Avoid division by zero
                            likes = video['statistics']['likes']
                            comments = video['statistics']['comments']
                            
                            # st.write(views,likes,comments)
                            
                            # Calculate engagement metrics
                            like_view_ratio = likes / views
                            comment_view_ratio = comments / views
                            
                            # Get overall engagement or calculate if missing
                            engagement_rate = video['statistics']['engagement_rate']
                            if engagement_rate == 0:
                                # Simplified engagement rate calculation if not provided
                                engagement_rate = (like_view_ratio + comment_view_ratio) / 2
                            
                            # Industry benchmarks
                            like_benchmark = 0.05  # 5% likes per view
                            comment_benchmark = 0.01  # 1% comments per view
                            engagement_benchmark = 0.06  # 6% overall engagement
                            
                            # st.write(like_view_ratio,comment_view_ratio,engagement_rate)
                            
                            # Create dataframe for visualization
                            engagement_data = pd.DataFrame({
                                'Metric': ['Like/View', 'Comment/View', 'Overall Engagement'],
                                'Value': [like_view_ratio, comment_view_ratio, engagement_rate/100],
                                'Benchmark': [like_benchmark, comment_benchmark, engagement_benchmark]
                            })
                            
                            engagement_df = pd.melt(
                                engagement_data,
                                id_vars=['Metric'],
                                value_vars=['Value', 'Benchmark'],
                                var_name='Type',
                                value_name='Rate'
                            )
                            
                            engagement_chart = alt.Chart(engagement_df).mark_bar().encode(
                                x=alt.X('Metric:N', title=None),
                                y=alt.Y('Rate:Q', title='Rate', axis=alt.Axis(format='.1%')),
                                color=alt.Color('Type:N', scale=alt.Scale(
                                    domain=['Value', 'Benchmark'],
                                    range=['#FF0000', '#757575']
                                )),
                                tooltip=['Metric', 'Type', alt.Tooltip('Rate:Q', format='.2%')]
                            ).properties(
                                title='Engagement vs Benchmark',
                                height=250
                            )
                            
                            st.altair_chart(engagement_chart, use_container_width=True)
                        
                        with metrics_cols[2]:
                            # Create a bubble chart showing relationship between engagement metrics
                            # Extract data from existing metrics
                            views = max(1, video['statistics']['views'])
                            likes = video['statistics']['likes']
                            comments = video['statistics']['comments']
                            engagement_rate = video['statistics'].get('engagement_rate', 0)
                            if engagement_rate == 0:
                                engagement_rate = ((likes / views) + (comments / views)) / 2 * 100
                            
                            # Create data for bubble chart
                            # Show relationship between: Views, Likes, Comments, and Engagement Rate
                            bubble_data = [
                                {"metric": "Likes-Comments Ratio", "x": likes / max(1, comments), "y": likes / max(1, views) * 100, 
                                "size": (likes / max(1, views) * 100)**2, "color": "Likes"},
                                {"metric": "Comments-Views Ratio", "x": comments / max(1, views) * 1000, "y": comments / max(1, likes) * 100, 
                                "size": (comments / max(1, views) * 100)*100, "color": "Comments"},
                                {"metric": "Overall Engagement", "x": engagement_rate / 10, "y": (likes + comments) / max(1, views) * 100, 
                                "size": engagement_rate**2, "color": "Engagement"}
                            ]
                            
                            # st.write(bubble_data)
                            
                            bubble_df = pd.DataFrame(bubble_data)
                            
                            # Create bubble chart
                            bubble_chart = alt.Chart(bubble_df).mark_circle().encode(
                                x=alt.X('x:Q', title='Interaction Rate (scaled)'),
                                y=alt.Y('y:Q', title='Percentage of Views', axis=alt.Axis(format='.1f')),
                                size=alt.Size('size:Q', legend=None),
                                color=alt.Color('color:N', scale=alt.Scale(
                                    domain=['Likes', 'Comments', 'Engagement'],
                                    range=['#FF0000', '#4285F4', '#FBBC05']
                                )),
                                tooltip=['metric', 
                                        alt.Tooltip('x:Q', title='Interaction Rate', format='.2f'),
                                        alt.Tooltip('y:Q', title='% of Views', format='.2f')]
                            ).properties(
                                title='Engagement Bubble Analysis',
                                height=250
                            )
                            
                            # Add text labels to each bubble
                            text = alt.Chart(bubble_df).mark_text(
                                align='center',
                                baseline='middle',
                                fontSize=11,
                                fontWeight='bold',
                                color='white'
                            ).encode(
                                x='x:Q',
                                y='y:Q',
                                text='metric:N'
                            )
                            
                            # Combine chart and labels
                            final_chart = (bubble_chart + text)
                            
                            st.altair_chart(final_chart, use_container_width=True)
                        
            else:
                st.info("No analyzed videos available")
                
        with tab3:
            # Content Strategy section
            st.markdown("## 📈 Content Strategy Recommendations")
            
            # Content recommendations
            if 'content_recommendations' in data:
                content_recs = data['content_recommendations']
                
                # Content types
                st.markdown("### 🎬 Recommended Content Types")
                if 'content_types' in content_recs and len(content_recs['content_types']) > 0:
                    content_types = content_recs['content_types']
                    
                    # Create cards for content types
                    cols = st.columns(min(3, len(content_types)))
                    for i, content_type in enumerate(content_types):
                        with cols[i % 3]:
                            st.markdown(f"""
                            <div style="background-color: white; padding: 1rem; border-radius: 10px; 
                                       border-top: 5px solid #FF0000; margin-bottom: 1rem; height: 100px;
                                       display: flex; align-items: center; justify-content: center; text-align: center;">
                                <h6>{content_type}</h6>
                            </div>
                            """, unsafe_allow_html=True)
                
                # Style recommendations
                style_cols = st.columns(2)
                
                with style_cols[0]:
                    st.markdown("### 🎨 Visual Style")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #9C27B0;">
                        <p>{content_recs.get('visual_style', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### 🎵 Audio/Music")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #2196F3;">
                        <p>{content_recs.get('audio_music', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with style_cols[1]:
                    st.markdown("### 📖 Storytelling Approach")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #4CAF50;">
                        <p>{content_recs.get('storytelling_approach', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("### ✂️ Editing Style & Pacing")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #FF9800;">
                        <p>{content_recs.get('editing_style_and_pacing', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Marketing tactics
            if 'marketing_tactics' in data:
                st.markdown("### 📣 Marketing Tactics")
                tactics = data['marketing_tactics']
                
                tactics_cols = st.columns(2)
                
                with tactics_cols[0]:
                    st.markdown("#### 📝 Title & Description Optimization")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #E91E63;">
                        <p>{tactics.get('title_and_description_optimization', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 🖼️ Thumbnail Design")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #673AB7;">
                        <p>{tactics.get('thumbnail_design_recommendations', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with tactics_cols[1]:
                    st.markdown("#### ⏰ Best Posting Times & Frequency")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #00BCD4;">
                        <p>{tactics.get('best_posting_times_and_frequency', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("#### 👥 Audience Engagement Strategies")
                    st.markdown(f"""
                    <div class="recommendation-box" style="border-left: 4px solid #8BC34A;">
                        <p>{tactics.get('audience_engagement_strategies', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Success metrics
            if 'success_metrics' in data:
                st.markdown("### 📊 Success Metrics")
                success_metrics = data['success_metrics']
                
                metrics_cols = st.columns(3)
                
                with metrics_cols[0]:
                    st.markdown(f"""
                    <div class="success-metric-box">
                        <h4>📏 How to Measure Effectiveness</h4>
                        <p>{success_metrics.get('how_to_measure_effectiveness', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metrics_cols[1]:
                    st.markdown(f"""
                    <div class="success-metric-box">
                        <h4>👁️ Expected Engagement Patterns</h4>
                        <p>{success_metrics.get('expected_engagement_patterns', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with metrics_cols[2]:
                    st.markdown(f"""
                    <div class="success-metric-box">
                        <h4>📈 Growth Opportunities</h4>
                        <p>{success_metrics.get('growth_opportunities', 'Not specified')}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        with tab4:
            # All Videos section
            st.markdown("## 🔍 All Videos")
            
            # Video selection tabs
            video_tabs = st.tabs(["Top Matches"])
            
            with video_tabs[0]:
                st.markdown("### 🏆 Top Matching Videos")
                
                # Top trending matches
                if 'top_matches' in data.get('videos', {}) and 'trending' in data['videos']['top_matches']:
                    st.markdown("#### Trending Matches")
                    trending_matches = data['videos']['top_matches']['trending']
                    
                    for video in trending_matches:
                        st.markdown(f"""<div class="video-card">""", unsafe_allow_html=True)
                        display_video_card(video)
                        st.markdown("""</div>""", unsafe_allow_html=True)
                
                # Top search matches
                if 'top_matches' in data.get('videos', {}) and 'search' in data['videos']['top_matches']:
                    st.markdown("#### Search Matches")
                    search_matches = data['videos']['top_matches']['search']
                    
                    for video in search_matches:
                        st.markdown(f"""<div class="video-card">""", unsafe_allow_html=True)
                        display_video_card(video)
                        st.markdown("""</div>""", unsafe_allow_html=True)
            
            # with video_tabs[1]:
            #     st.markdown("### 👯 Similar Content")
                
            #     if 'similar_content' in data.get('videos', {}):
            #         similar_videos = data['videos']['similar_content']
                    
            #         st.markdown("""<div class="video-grid">""", unsafe_allow_html=True)
            #         for video in similar_videos:
            #             st.markdown(f"""<div class="video-card">""", unsafe_allow_html=True)
            #             display_video_card(video)
            #             st.markdown("""</div>""", unsafe_allow_html=True)
            #         st.markdown("""</div>""", unsafe_allow_html=True)
            #     else:
            #         st.info("No similar content available")
            
            # with video_tabs[2]:
            #     st.markdown("### 🔥 Trending Content")
                
            #     if 'trending_content' in data.get('videos', {}):
            #         trending_videos = data['videos']['trending_content']
                    
            #         st.markdown("""<div class="video-grid">""", unsafe_allow_html=True)
            #         for video in trending_videos:
            #             st.markdown(f"""<div class="video-card">""", unsafe_allow_html=True)
            #             display_video_card(video)
            #             st.markdown("""</div>""", unsafe_allow_html=True)
            #         st.markdown("""</div>""", unsafe_allow_html=True)
            #     else:
            #         st.info("No trending content available")
    
    else:
        # Display example data when first loading the app
        st.markdown("## 👋 Welcome to YouTube Trends Analyzer")
        st.markdown("""
        This tool helps you analyze YouTube trends and generate content strategy recommendations 
        based on your specific niche and goals.
        
        ### How it works:
        1. Enter your content description in the sidebar
        2. Select content type and target region
        3. Click "Analyze Content" to get personalized recommendations
        
        ### You'll receive:
        - Content strategy overview
        - Keyword analysis
        - Trend insights
        - Video performance metrics
        - Marketing recommendations
        """)

# Run main function
if __name__ == "__main__":
    main()
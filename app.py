import streamlit as st
import time
import os
import pickle
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd

# ---------------- CONFIG ---------------- #
st.set_page_config(
    page_title="NEUROSYNC – Beast Mode Control Panel", 
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🧠"
)

SCOPES = [
    'https://www.googleapis.com/auth/fitness.activity.read',
    'https://www.googleapis.com/auth/fitness.body.read',
    'https://www.googleapis.com/auth/fitness.body.write',
    'https://www.googleapis.com/auth/fitness.activity.write',
    'https://www.googleapis.com/auth/fitness.location.read',
    'https://www.googleapis.com/auth/fitness.heart_rate.read'
]

# ---------------- ENHANCED STYLING ---------------- #
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');
        
        .stApp {
            background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
        }
        
        .main-header {
            font-family: 'Orbitron', monospace;
            font-size: 3.5rem;
            font-weight: 900;
            text-align: center;
            color: #00f5d4; /* Use a solid neon color for sharpness */
            /* Removed gradient background-clip and text-fill-color for clarity */
            margin-bottom: 0.5rem;
            text-shadow: 0 0 10px rgba(0, 245, 212, 0.2); /* Softer, less blurry shadow */
        }
        
        .sub-header {
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.4rem;
            text-align: center;
            color: #b0b0b0;
            margin-bottom: 2rem;
        }
        
        .metric-card {
            background: rgba(30, 40, 60, 0.6);
            border: 2px solid rgba(0, 245, 212, 0.3);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            border-color: rgba(0, 245, 212, 0.6);
            box-shadow: 0 12px 40px rgba(0, 245, 212, 0.2);
        }
        
        .emotion-display {
            font-family: 'Orbitron', monospace;
            font-size: 2.8rem;
            font-weight: 700;
            text-align: center;
            padding: 2.5rem;
            border-radius: 20px;
            margin: 2rem 0;
            text-shadow: 0 0 25px currentColor;
            width: 100%;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        }
        
        .emotion-balanced { 
            background: linear-gradient(45deg, rgba(0, 245, 212, 0.1), rgba(0, 212, 245, 0.1));
            color: #00f5d4; 
            border: 2px solid rgba(0, 245, 212, 0.3);
        }
        .emotion-energized { 
            background: linear-gradient(45deg, rgba(255, 193, 7, 0.1), rgba(255, 152, 0, 0.1));
            color: #ffc107; 
            border: 2px solid rgba(255, 193, 7, 0.3);
        }
        .emotion-overactive { 
            background: linear-gradient(45deg, rgba(255, 87, 51, 0.1), rgba(255, 23, 68, 0.1));
            color: #ff5733; 
            border: 2px solid rgba(255, 87, 51, 0.3);
        }
        .emotion-fatigued { 
            background: linear-gradient(45deg, rgba(156, 39, 176, 0.1), rgba(103, 58, 183, 0.1));
            color: #9c27b0; 
            border: 2px solid rgba(156, 39, 176, 0.3);
        }
        
        .tip-box {
            background: rgba(0, 60, 80, 0.4);
            border-left: 4px solid #00f5d4;
            border-radius: 15px;
            padding: 2rem;
            margin: 2rem 0;
            font-family: 'Rajdhani', sans-serif;
            font-size: 1.3rem;
            font-weight: 500;
            box-shadow: 0 6px 25px rgba(0, 245, 212, 0.15);
        }
        
        .progress-container {
            background: rgba(40, 50, 70, 0.6);
            border-radius: 25px;
            padding: 8px;
            margin: 2rem 0;
            overflow: hidden;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.4);
        }
        
        .progress-bar {
            height: 40px;
            border-radius: 20px;
            transition: all 1.2s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0, 245, 212, 0.3);
        }
        
        .progress-bar::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 50px;
            font-weight: 600;
            font-size: 0.9rem;
            margin: 0.25rem;
        }
        
        .badge-excellent { background: linear-gradient(45deg, #4CAF50, #45a049); }
        .badge-good { background: linear-gradient(45deg, #2196F3, #1976D2); }
        .badge-warning { background: linear-gradient(45deg, #FF9800, #F57C00); }
        .badge-danger { background: linear-gradient(45deg, #F44336, #D32F2F); }
        
        .stat-number {
            font-family: 'Orbitron', monospace;
            font-size: 3.5rem;
            font-weight: 700;
            color: #00f5d4;
            text-shadow: 0 0 20px rgba(0, 245, 212, 0.5);
            margin-bottom: 0.5rem;
        }
        
        .sidebar .element-container {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 1rem;
            margin: 0.5rem 0;
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- SESSION STATE INITIALIZATION ---------------- #
if "goals" not in st.session_state:
    st.session_state.goals = {
        "hourly_steps": 1000,
        "daily_steps": 10000,
        "weekly_steps": 70000
    }

if "history" not in st.session_state:
    st.session_state.history = []

if "settings" not in st.session_state:
    st.session_state.settings = {
        "sync_interval": 5,
        "notifications": True,
        "advanced_metrics": True
    }

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "weight": 70.0,  # kg
        "height": 170.0,  # cm
        "age": 30,
        "gender": "Male"
    }

# ---------------- ENHANCED AUTH HANDLER ---------------- #
@st.cache_resource
def get_credentials():
    """Enhanced credential management with better error handling"""
    creds = None
    
    if os.path.exists('token.pkl'):
        try:
            with open('token.pkl', 'rb') as token:
                creds = pickle.load(token)
        except Exception as e:
            st.error(f"Error loading credentials: {str(e)}")
            return None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                st.error(f"Error refreshing credentials: {str(e)}")
                return None
        else:
            if not os.path.exists('credentials.json'):
                st.error("❌ credentials.json file not found. Please upload your Google API credentials.")
                return None
            
            try:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                st.error(f"Error during OAuth flow: {str(e)}")
                return None
        
        try:
            with open('token.pkl', 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            st.warning(f"Could not save credentials: {str(e)}")
    
    return creds

# ---------------- ENHANCED FITNESS DATA FETCH ---------------- #
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_comprehensive_fit_data(hours_back=1):
    """Fetch comprehensive fitness data with multiple metrics"""
    creds = get_credentials()
    if not creds:
        return None
    
    try:
        service = build('fitness', 'v1', credentials=creds)
        
        now = int(time.time() * 1e9)
        time_ago = now - int(hours_back * 3600 * 1e9)
        dataset = f"{time_ago}-{now}"
        
        data = {
            'steps': 0,
            'calories': 0,
            'distance': 0.0,
            'active_minutes': 0,
            'heart_rate': None,
            'weight': st.session_state.user_profile['weight'],
            'height': st.session_state.user_profile['height'],
            'timestamp': datetime.now()
        }
        
        # Fetch steps
        try:
            step_data = service.users().dataSources().datasets().get(
                userId='me',
                dataSourceId='derived:com.google.step_count.delta:com.google.android.gms:merge_step_deltas',
                datasetId=dataset
            ).execute()
            
            for point in step_data.get("point", []):
                data['steps'] += point['value'][0]['intVal']
        except Exception as e:
            st.warning(f"Could not fetch step data: {str(e)}")
        
        # Fetch calories
        try:
            calorie_data = service.users().dataSources().datasets().get(
                userId='me',
                dataSourceId='derived:com.google.calories.expended:com.google.android.gms:merge_calories_expended',
                datasetId=dataset
            ).execute()
            
            for point in calorie_data.get("point", []):
                data['calories'] += point['value'][0]['fpVal']
        except Exception as e:
            st.warning(f"Could not fetch calorie data: {str(e)}")
        
        # Fetch distance
        try:
            distance_data = service.users().dataSources().datasets().get(
                userId='me',
                dataSourceId='derived:com.google.distance.delta:com.google.android.gms:merge_distance_delta',
                datasetId=dataset
            ).execute()
            
            for point in distance_data.get("point", []):
                data['distance'] += point['value'][0]['fpVal']
        except Exception as e:
            st.warning(f"Could not fetch distance data: {str(e)}")
        
        # Try to fetch weight from Google Fit (if available)
        try:
            weight_data = service.users().dataSources().datasets().get(
                userId='me',
                dataSourceId='derived:com.google.weight:com.google.android.gms:merge_weight',
                datasetId=dataset
            ).execute()
            
            for point in weight_data.get("point", []):
                data['weight'] = point['value'][0]['fpVal']
                st.session_state.user_profile['weight'] = data['weight']
        except:
            pass  # Use stored weight if Google Fit doesn't have recent data
        
        return data
        
    except Exception as e:
        st.error(f"Error fetching fitness data: {str(e)}")
        return None

# ---------------- ENHANCED EMOTION & RECOMMENDATION ENGINE ---------------- #
def analyze_fitness_state(data):
    """Advanced emotion and recommendation analysis"""
    if not data:
        return "Unknown 🤔", "Unable to fetch data. Please check your connection.", "neutral", "badge-warning"
    
    steps = data['steps']
    calories = data['calories']
    distance = data['distance']
    weight = data.get('weight', 70)
    height = data.get('height', 170)
    
    # Calculate BMI
    bmi = weight / ((height/100) ** 2)
    
    # Calculate intensity score
    intensity_score = 0
    if steps > 2000: intensity_score += 3
    elif steps > 1000: intensity_score += 2
    elif steps > 500: intensity_score += 1
    
    if calories > 300: intensity_score += 2
    elif calories > 150: intensity_score += 1
    
    # Determine state
    if intensity_score >= 5:
        emotion = "Beast Mode Activated 🔥"
        tip = f"You're crushing it! BMI: {bmi:.1f}. Consider recovery time and stay hydrated. Your body is working hard."
        css_class = "emotion-overactive"
        badge_class = "badge-excellent"
    elif intensity_score >= 3:
        emotion = "Energized & Flowing 💪"
        tip = f"Perfect balance! BMI: {bmi:.1f}. You're in the zone. Keep this momentum while listening to your body."
        css_class = "emotion-energized"
        badge_class = "badge-good"
    elif intensity_score >= 1:
        emotion = "Balanced & Steady 😊"
        tip = f"Good baseline activity. BMI: {bmi:.1f}. Consider adding light movement to boost energy and mood."
        css_class = "emotion-balanced"
        badge_class = "badge-good"
    else:
        emotion = "Rest & Recharge Mode 💤"
        tip = f"Time to activate! BMI: {bmi:.1f}. Try a 5-minute walk or light stretching to kickstart your energy."
        css_class = "emotion-fatigued"
        badge_class = "badge-warning"
    
    return emotion, tip, css_class, badge_class

# ---------------- MAIN APP UI ---------------- #
st.markdown('<h1 class="main-header">🧠 NEUROSYNC</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Beast Mode Control Panel – Real-time Emotion & Motion Sync</p>', unsafe_allow_html=True)

# ---------------- SIDEBAR CONTROLS ---------------- #
with st.sidebar:
    st.markdown("### ⚙️ Control Center")
    
    # Sync controls
    auto_sync = st.checkbox("🔄 Auto-sync every 5 minutes", value=False)
    time_range = st.selectbox("📊 Data Time Range", [1, 2, 4, 8, 12, 24], index=0, format_func=lambda x: f"Last {x} hour{'s' if x > 1 else ''}")
    
    st.markdown("### 🎯 Goal Settings")
    hourly_goal = st.number_input("Hourly Steps Goal", min_value=100, max_value=5000, value=st.session_state.goals["hourly_steps"], step=100)
    daily_goal = st.number_input("Daily Steps Goal", min_value=1000, max_value=50000, value=st.session_state.goals["daily_steps"], step=1000)
    
    st.session_state.goals["hourly_steps"] = hourly_goal
    st.session_state.goals["daily_steps"] = daily_goal
    
    st.markdown("### 🔧 Advanced Settings")
    show_charts = st.checkbox("📈 Show Analytics Charts", value=True)
    show_detailed_metrics = st.checkbox("📊 Detailed Metrics", value=True)

# ---------------- MAIN DASHBOARD ---------------- #
# Center the sync button
sync_col1, sync_col2, sync_col3 = st.columns([2, 1, 2])
with sync_col2:
    sync_button = st.button("🚀 SYNC NOW", type="primary", help="Fetch latest fitness data")

if sync_button:
        with st.spinner("Syncing with Google Fit..."):
            fitness_data = get_comprehensive_fit_data(time_range)
            
            if fitness_data:
                # Store in history
                st.session_state.history.append(fitness_data)
                if len(st.session_state.history) > 100:  # Keep last 100 entries
                    st.session_state.history = st.session_state.history[-100:]
                
                st.success("✅ Sync Complete!")
                
                # Analyze state
                emotion, tip, css_class, badge_class = analyze_fitness_state(fitness_data)
                
                # Display main metrics - Full width container
                st.markdown(f'<div class="emotion-display {css_class}">{emotion}</div>', unsafe_allow_html=True)
                
                # Key metrics row - Full width
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.markdown(f'<div class="stat-number">{fitness_data["steps"]}</div>', unsafe_allow_html=True)
                    st.markdown("**Steps**")
                
                with metric_col2:
                    st.markdown(f'<div class="stat-number">{int(fitness_data["calories"])}</div>', unsafe_allow_html=True)
                    st.markdown("**Calories**")
                
                with metric_col3:
                    st.markdown(f'<div class="stat-number">{fitness_data["distance"]:.1f}</div>', unsafe_allow_html=True)
                    st.markdown("**Distance (m)**")
                
                with metric_col4:
                    progress = min(int((fitness_data["steps"] / hourly_goal) * 100), 100)
                    st.markdown(f'<div class="stat-number">{progress}%</div>', unsafe_allow_html=True)
                    st.markdown("**Goal Progress**")
                
                # Progress bar - Full width
                st.markdown("### 🎯 Goal Progress")
                progress_color = "#00f5d4" if progress < 100 else "#ffc107"
                st.markdown(f"""
                    <div class="progress-container">
                        <div class="progress-bar" style="width: {progress}%; background: linear-gradient(45deg, {progress_color}, {progress_color}aa);">
                        </div>
                    </div>
                    <div style="text-align: center; margin-top: 10px;">
                        <span class="status-badge {badge_class}">{fitness_data["steps"]} / {hourly_goal} steps</span>
                    </div>
                """, unsafe_allow_html=True)
                
                # AI Tip - Full width
                st.markdown(f'<div class="tip-box">💡 <strong>AI Insight:</strong> {tip}</div>', unsafe_allow_html=True)
                
                # Detailed metrics
                if show_detailed_metrics:
                    st.markdown("### 📊 Detailed Analytics")
                    
                    detail_col1, detail_col2 = st.columns(2)
                    
                    with detail_col1:
                        st.metric("Steps per Minute", f"{fitness_data['steps'] / (time_range * 60):.1f}")
                        st.metric("Calories per Hour", f"{fitness_data['calories'] / time_range:.0f}")
                    
                    with detail_col2:
                        st.metric("Average Speed", f"{(fitness_data['distance'] / 1000) / time_range:.1f} km/h" if fitness_data['distance'] > 0 else "0 km/h")
                        st.metric("Activity Level", "High" if fitness_data['steps'] > hourly_goal else "Moderate" if fitness_data['steps'] > hourly_goal/2 else "Low")
                
                # Charts
                if show_charts and len(st.session_state.history) > 1:
                    st.markdown("### 📈 Trend Analysis")
                    
                    # Create dataframe from history
                    df = pd.DataFrame(st.session_state.history[-20:])  # Last 20 entries
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    chart_col1, chart_col2 = st.columns(2)
                    
                    with chart_col1:
                        fig_steps = px.line(df, x='timestamp', y='steps', 
                                          title='Steps Over Time',
                                          color_discrete_sequence=['#00f5d4'])
                        fig_steps.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white'
                        )
                        st.plotly_chart(fig_steps, use_container_width=True)
                    
                    with chart_col2:
                        fig_calories = px.bar(df.tail(10), x='timestamp', y='calories',
                                            title='Calories Burned',
                                            color_discrete_sequence=['#ffc107'])
                        fig_calories.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font_color='white'
                        )
                        st.plotly_chart(fig_calories, use_container_width=True)
            
            else:
                st.error("❌ Could not fetch fitness data. Please check your Google Fit permissions and internet connection.")

# ---------------- FOOTER ---------------- #
st.markdown("---")
st.markdown("""
    <div style="text-align: center; padding: 2rem; background: rgba(0, 245, 212, 0.05); border-radius: 15px; margin-top: 2rem;">
        <h3 style="color: #00f5d4; font-family: 'Orbitron', monospace;">👑 Your Mind Rules Your Body</h3>
        <p style="color: #b0b0b0; font-family: 'Rajdhani', sans-serif;">
            Sync your motion, elevate your emotion, dominate your goals.
        </p>
    </div>
""", unsafe_allow_html=True)

# ---------------- AUTO-SYNC FUNCTIONALITY ---------------- #
if auto_sync:
    if 'last_sync' not in st.session_state:
        st.session_state.last_sync = time.time()
    
    if time.time() - st.session_state.last_sync > 300:  # 5 minutes
        st.rerun()
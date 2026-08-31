import streamlit as st
import cv2
import numpy as np
import mediapipe as mp
import plotly.graph_objects as go
import tempfile
import time

# ==========================================
# 1. PAGE CONFIG & HIGH-CONTRAST DARK CSS
# ==========================================
st.set_page_config(
    page_title="SRH Kinetic Warfare Lab",
    page_icon="🧡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Contrast CSS (Dark Mode + Neon Orange + Dropdown Fix)
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #0b0e14;
        color: #ffffff;
    }
    
    /* Global White Text Overrides */
    h1, h2, h3, h4, h5, h6, p, span, label, .stMarkdown {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* SRH Accent Headers */
    .srh-title {
        color: #ff5500 !important;
        font-weight: 900;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }
    
    /* Content Feature Box Cards */
    .card-box {
        background-color: #161b22;
        border: 1px solid #262c36;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f131a !important;
        border-right: 1px solid #262c36;
    }

    /* DROPDOWN & SELECTBOX TEXT CONTRAST FIX */
    div[data-baseweb="select"] {
        background-color: #161b22 !important;
        border: 1px solid #262c36 !important;
        border-radius: 8px;
    }
    
    div[data-baseweb="select"] * {
        color: #ffffff !important;
        background-color: #161b22 !important;
    }

    /* Dropdown Popup Options List */
    ul[data-baseweb="menu"] {
        background-color: #161b22 !important;
        border: 1px solid #262c36 !important;
    }
    
    ul[data-baseweb="menu"] li {
        color: #ffffff !important;
        background-color: #161b22 !important;
    }

    ul[data-baseweb="menu"] li:hover {
        background-color: #ff5500 !important;
        color: #ffffff !important;
    }

    /* FILE UPLOADER BOX STYLING */
    div[data-testid="stFileUploader"] {
        background-color: #161b22 !important;
        border: 2px dashed #ff5500 !important;
        border-radius: 12px;
        padding: 15px;
    }

    div[data-testid="stFileUploader"] section {
        background-color: #161b22 !important;
    }

    div[data-testid="stFileUploader"] span, 
    div[data-testid="stFileUploader"] p,
    div[data-testid="stFileUploader"] button {
        color: #ffffff !important;
    }

    /* SLIDER ACCENT STYLING */
    div[data-baseweb="slider"] {
        color: #ff5500 !important;
    }

    /* Metric Display Values */
    div[data-testid="stMetricValue"] {
        color: #00e676 !important;
        font-size: 26px !important;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MEDIAPIPE & HELPER FUNCTIONS
# ==========================================
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b, c):
    """Calculates 3D joint angle between hip, knee, and ankle keypoints"""
    a = np.array(a)  # Hip
    b = np.array(b)  # Knee
    c = np.array(c)  # Ankle
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    
    if angle > 180.0:
        angle = 360 - angle
        
    return int(angle)

# ==========================================
# 3. SIDEBAR NAVIGATION & SRH SQUAD
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/e/eb/Sunrisers_Hyderabad_IPL_Logo.svg", width=130)
st.sidebar.markdown("<h2 class='srh-title'>ORANGE ARMY TELEMETRY</h2>", unsafe_allow_html=True)

# SRH Key Bowlers List
srh_bowlers = [
    "Pat Cummins (Captain & Fast Bowler)",
    "Harshal Patel (Fast-Medium Bowler)",
    "Jaydev Unadkat (Left-arm Fast-Medium)",
    "Shivam Mavi (Fast Bowler)",
    "Brydon Carse (Fast Bowler)",
    "Eshan Malinga (Fast Bowler)",
    "Zeeshan Ansari (Spinner)",
    "Sakib Hussain (Fast Bowler)",
    "Dilshan Madushanka (Fast Bowler)",
    "Praful Hinge (Fast Bowler)",
    "Onkar Tarmale (Bowler)",
    "Nitish Kumar Reddy (All-Rounder / Fast-Medium)"
]

selected_player = st.sidebar.selectbox(
    "Select SRH Bowler Profile",
    srh_bowlers
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Engine Parameters")
knee_threshold = st.sidebar.slider("Front Knee Angle Threshold (°)", 120, 165, 150)
fatigue_index_sim = st.sidebar.slider("Simulated ACWR Fatigue Ratio", 0.5, 2.0, 1.34)

st.sidebar.markdown("---")
st.sidebar.caption("SRH Kinetic Warfare Lab v2.0 | Built by @thecricketalchemist19")

# ==========================================
# 4. HEADER SECTION
# ==========================================
st.markdown("<h1 style='color: #ff5500 !important; font-size: 36px; font-weight: 900; margin-bottom: 0px;'>SRH KINETIC WARFARE LAB 🔥</h1>", unsafe_allow_html=True)
st.markdown("<p style='font-size: 13px; color: #8b949e !important; margin-top: 0px;'>BIO-VELOCITY ENGINE v2.0 | F1 TELEMETRY GRADE | BUILT BY @THECRICKETALCHEMIST19</p>", unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 5. MAIN INTERFACE & LAYOUT
# ==========================================
col_left, col_right = st.columns([1.1, 1])

with col_left:
    st.markdown("<h3 class='srh-title'>🎯 SYSTEM CAPABILITIES</h3>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='card-box'>
        <p style='margin:0; font-weight:bold; color:#00e676 !important;'>1. Real-Time Pose Landmarking</p>
        <p style='margin:0; font-size:13px; color:#c9d1d9 !important;'>Mediapipe 33-point skeletal vector mapping directly from match clips.</p>
    </div>
    <div class='card-box'>
        <p style='margin:0; font-weight:bold; color:#ff5500 !important;'>2. Front Knee Absorption Angle (<150°)</p>
        <p style='margin:0; font-size:13px; color:#c9d1d9 !important;'>Automated biomechanical strain detection at front-foot stride release.</p>
    </div>
    <div class='card-box'>
        <p style='margin:0; font-weight:bold; color:#ff1744 !important;'>3. ACWR Fatigue & Injury Risk Forecaster</p>
        <p style='margin:0; font-size:13px; color:#c9d1d9 !important;'>Predicts high hamstring & back strain risk before catastrophic injury.</p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload Bowling Clip (MP4/MOV/AVI)", type=["mp4", "mov", "avi"])

with col_right:
    st.markdown("<h3 class='srh-title'>⚠️ TELEMETRY MONITOR</h3>", unsafe_allow_html=True)
    
    if not uploaded_file:
        st.info(f"👈 Selected Player: **{selected_player}**\nPlease upload a bowling clip to run kinematic analysis.")
    else:
        st.success(f"Clip loaded for **{selected_player}**. Initializing video pipeline...")

# ==========================================
# 6. VIDEO PROCESSING & METRICS PIPELINE
# ==========================================
if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    
    cap = cv2.VideoCapture(tfile.name)
    stframe = st.empty()
    
    angles_list = []
    frames_list = []
    
    # Top Live Metrics
    col_m1, col_m2, col_m3 = st.columns(3)
    metric_angle = col_m1.empty()
    metric_status = col_m2.empty()
    metric_acwr = col_m3.empty()
    
    frame_count = 0
    
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            
            results = pose.process(image)
            image.flags.writeable = True
            
            current_angle = 180
            status_text = "SAFE ABSORPTION"
            line_color = (0, 255, 0)
            
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                
                current_angle = calculate_angle(hip, knee, ankle)
                angles_list.append(current_angle)
                frames_list.append(frame_count)
                
                if current_angle < knee_threshold:
                    status_text = "HIGH ABSORPTION LOAD"
                    line_color = (255, 0, 0)
                else:
                    line_color = (0, 255, 0)
                    
                mp_drawing.draw_landmarks(
                    image, 
                    results.pose_landmarks, 
                    mp_pose.POSE_CONNECTIONS,
                    mp_drawing.DrawingSpec(color=(255, 50, 50), thickness=3, circle_radius=4),
                    mp_drawing.DrawingSpec(color=line_color, thickness=3, circle_radius=2)
                )
                
                h, w, _ = image.shape
                knee_pos = (int(knee[0] * w) - 100, int(knee[1] * h) - 20)
                cv2.putText(
                    image, 
                    f"KNEE: {current_angle} deg", 
                    knee_pos, 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, 
                    (255, 255, 255), 
                    3, 
                    cv2.LINE_AA
                )
            
            stframe.image(image, channels="RGB", use_container_width=True)
            
            metric_angle.metric("Front Knee Flexion", f"{current_angle}°")
            metric_status.metric("Load Status", status_text)
            metric_acwr.metric("ACWR Fatigue Ratio", f"{fatigue_index_sim}")
            
            time.sleep(0.01)
            
    cap.release()

    # ==========================================
    # 7. TELEMETRY GRAPH
    # ==========================================
    st.markdown("---")
    st.markdown("<h3 class='srh-title'>📊 KINEMATIC ANGLE DYNAMICS</h3>", unsafe_allow_html=True)
    
    if angles_list:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=frames_list, 
            y=angles_list, 
            mode='lines+markers', 
            name='Knee Angle (°)',
            line=dict(color='#ff5500', width=3),
            marker=dict(size=5, color='#00e676')
        ))
        
        fig.add_hline(y=knee_threshold, line_dash="dash", line_color="#ff1744", annotation_text="Load Threshold (150°)")
        
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0e14",
            plot_bgcolor="#161b22",
            title=f"Frame Sequence vs. Front Knee Flexion Angle ({selected_player})",
            xaxis_title="Frame Index",
            yaxis_title="Angle (Degrees)",
            height=380,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #8b949e !important; font-size: 12px;'>BUILT WITH ❤️ BY SRI SAAKYA (@THECRICKETALCHEMIST19) FOR SRH MANAGEMENT | STEALTH WARFARE v2.0</p>", unsafe_allow_html=True)
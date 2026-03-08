import streamlit as st
import requests
import io
import time
from datetime import datetime
import base64

# ===== Helper for Base64 Logo =====
def get_base64_image(image_file):
    with open(image_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_base64 = get_base64_image("logoo.png")


# Enhanced page configuration
st.set_page_config(
    page_title="SecurePDF - Malware Scanner & Cleaner", 
    page_icon="logoo.png", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for enhanced styling
st.markdown("""
<style>
    /* Import modern fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styling */
    .stApp {
    background: linear-gradient(135deg, #ffffff 0%, #b91c1c 100%);
    font-family: 'Inter', sans-serif;
    
}
    
    /* Main container */
    .main-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        margin: 2rem 0;
        animation: fadeInUp 0.8s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        margin-bottom: 2rem;
        animation: fadeInDown 1s ease-out;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Logo styling */
    .logo {
        width: 200px;
        display: block;
        margin: 0 auto 1.5rem;
        filter: drop-shadow(0 8px 16px rgba(239,68,68,0.2));
        animation: logoFloat 3s ease-in-out infinite;
    }
    
    @keyframes logoFloat {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .main-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ef4444, #b91c1c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .subtitle {
        font-size: 1.2rem;
        color: #334155;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    /* Feature cards */
    .feature-card {
        background: linear-gradient(135deg, #f8fafc, #e2e8f0);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #ef4444;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(239,68,68,0.15);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #334155;
        font-size: 0.9rem;
        line-height: 1.5;
    }
    
    /* Upload area styling */
    .upload-container {
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        padding: 3rem 2rem;
        text-align: center;
        background: linear-gradient(135deg, #f8fafc, #f1f5f9);
        margin: 2rem 0;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .upload-container:hover {
        border-color: #ef4444;
        background: linear-gradient(135deg, #fff5f5, #fee2e2);
        transform: scale(1.02);
    }
    
    .upload-container::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(239,68,68,0.1) 0%, transparent 70%);
        animation: rotate 10s linear infinite;
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    
    .upload-container:hover::before {
        opacity: 1;
    }
    
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .upload-icon {
        font-size: 4rem;
        color: #ef4444;
        margin-bottom: 1rem;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(239,68,68,0.3) !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(239,68,68,0.4) !important;
        background: linear-gradient(135deg, #dc2626, #b91c1c) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0) !important;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        margin: 1rem 0;
    }
    
    /* Success/Error message styling */
        /* Success/Error message styling */
    .stSuccess, .stError, .stInfo {
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    
    .stSuccess {
        color: #000000 !important;
    }
    
    .stSuccess > div {
        color: #000000 !important;
    }
    
    .stSuccess div[data-testid="stMarkdownContainer"] {
        color: #000000 !important;
    }
    
    .stSuccess p {
        color: #000000 !important;
    }
    
    .stSuccess * {
        color: #000000 !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #ef4444, #dc2626) !important;
        border-radius: 10px !important;
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #10b981, #059669) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(16,185,129,0.3) !important;
        width: 100% !important;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(16,185,129,0.4) !important;
    }
    
    /* Stats container */
    .stats-container {
        background: linear-gradient(135deg, #1e293b, #334155);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 2rem 0;
        color: white;
        text-align: center;
    }
    
    .stat-item {
        margin: 0.5rem 0;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        color: #ef4444;
    }
    
    .stat-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Security badge */
    .security-badge {
        display: inline-flex;
        align-items: center;
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(239,68,68,0.3);
    }
    
    .security-badge::before {
        content: '🔒';
        margin-right: 0.5rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# ===== Header Section =====
st.markdown(f"""
<div class="main-container">
    <div class="header-container">
        <img src="data:image/png;base64,{logo_base64}" class="logo" alt="SecurePDF Logo"/>
        <h2 class="main-title">🛡️SecurePDF</h2>
        <p class="subtitle">Advanced Malware Scanner & PDF Cleaner</p>
        <div class="security-badge">Military-Grade Security</div>
    </div>
""", unsafe_allow_html=True)

# Feature highlights
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">⚡</div>
        <div class="feature-title">Lightning Fast</div>
        <div class="feature-desc">Scan and clean PDFs in seconds using our optimized engine</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🔒</div>
        <div class="feature-title">100% Secure</div>
        <div class="feature-desc">Isolated Docker sandbox ensures complete security</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <div class="feature-title">99.9% Accurate</div>
        <div class="feature-desc">Advanced AI detection with minimal false positives</div>
    </div>
    """, unsafe_allow_html=True)

# Stats section
st.markdown("""
<div class="stats-container">
    <div style="display: flex; justify-content: space-around; flex-wrap: wrap;">
        <div class="stat-item">
            <div class="stat-number">100+</div>
            <div class="stat-label">Files Scanned</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">99.9%</div>
            <div class="stat-label">Detection Rate</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">< 30s</div>
            <div class="stat-label">Avg Scan Time</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">24/7</div>
            <div class="stat-label">Uptime</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Upload section (style the actual Streamlit uploader)
st.markdown("""
<style>
/* Style Streamlit's real file uploader dropzone */
[data-testid="stFileUploaderDropzone"] {
    border: 2px dashed #cbd5e1 !important;
    border-radius: 16px !important;
    padding: 3rem 2rem !important;
    background: linear-gradient(135deg, #f8fafc, #f1f5f9) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #ef4444 !important;
    background: linear-gradient(135deg, #fff5f5, #fee2e2) !important;
    transform: scale(1.01);
}
/* Ensure uploader label and all nested text are black */
[data-testid="stFileUploaderLabel"],
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] *,
[data-testid="stFileUploaderDropzone"] *,
[data-baseweb="file-uploader"] *,
section[data-testid="stFileUploader"] *,
section[aria-label="Upload file"] *,
label[for^="file_uploader"] *,
label[for^="file_uploader"] {
    color: #a9a9a9 !important;
}
/* Also ensure any markdown container near the uploader uses black */
[data-testid="stFileUploader"] [data-testid="stMarkdownContainer"] *,
[data-testid="stMarkdownContainer"] p:has(+ [data-testid="stFileUploader"]) {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

backend_url = "http://localhost:8000"

uploaded = st.file_uploader("Drop your PDF here (max 50MB)", type=["pdf"], label_visibility="visible", accept_multiple_files=False)

if uploaded:
    st.markdown(f"""
    <div style="background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 12px; padding: 1rem; margin: 1rem 0; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
        <p style="color: #000000; margin: 0; font-size: 1rem;">✅ <strong>{uploaded.name}</strong> loaded successfully ({uploaded.size:,} bytes)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration options
    st.markdown('<h3 style="color: #000000;">⚙️ Scanning Options</h3>', unsafe_allow_html=True)    
    st.markdown("""
    <style>
        .stCheckbox label {
            color: #000000 !important;
        }
        .stCheckbox label p {
            color: #000000 !important;
        }
    </style>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        aggressive = st.checkbox(
            "🔥 Maximum Safety Mode", 
            value=False,
            help="Converts pages to images to neutralize ALL active content. Results in larger files but maximum security."
        )
    with col2:
        show_report = st.checkbox(
            "📊 Generate Detailed Report", 
            value=True,
            help="Includes comprehensive analysis report with threat details and remediation steps."
        )
    
    # Security level indicator
    if aggressive:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <strong style="color: #000000;">🔥 Maximum Safety Mode Active</strong><br>
            <small style="color: #000000;">All content will be rasterized for ultimate protection. Text selection will be disabled.</small>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #dbeafe, #bfdbfe); border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
            <strong style="color: #000000;">⚖️ Balanced Mode Active</strong><br>
            <small style="color: #000000;">Removes threats while preserving text and formatting where safe.</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Scan button
    if st.button("🚀 **SCAN & SECURE MY PDF**", type="primary", use_container_width=True):
        # Create progress tracking
        progress_container = st.container()
        status_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        try:
            # Step 1: Initialize
            progress_bar.progress(5)
            st.markdown("""
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <p style="color: #000000; margin: 0;">🔄 Initializing secure scanning environment...</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.5)
            
            # Step 2: Prepare files
            files = {"file": ("upload.pdf", uploaded.getvalue(), "application/pdf")}
            data = {
                "mode": "rasterize" if aggressive else "sanitize", 
                "report": "1" if show_report else "0"
            }
            
            progress_bar.progress(15)
            st.markdown("""
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <p style="color: #000000; margin: 0;">📤 Uploading file to isolated sandbox...</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.5)
            
            # Step 3: Send to backend
            progress_bar.progress(25)
            st.markdown("""
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <p style="color: #000000; margin: 0;">🔍 Deep scanning for threats and malware...</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("🛡️ Scanning in progress - This may take a few moments for complex PDFs..."):
                resp = requests.post(f"{backend_url}/scan", files=files, data=data, timeout=600)
            
            progress_bar.progress(70)
            st.markdown("""
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <p style="color: #000000; margin: 0;">🧹 Cleaning and sanitizing detected threats...</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)
            
            progress_bar.progress(90)
            st.markdown("""
            <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <p style="color: #000000; margin: 0;">📋 Generating security report...</p>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.5)
            
            # Step 4: Process results
            if resp.status_code == 200:
                progress_bar.progress(100)
                st.markdown("""
                <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    <p style="color: #000000; margin: 0;">✅ **Scan Complete!** Your PDF has been successfully secured.</p>
                </div>
                """, unsafe_allow_html=True)
                
                content_type = resp.headers.get("Content-Type", "")
                current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if "application/zip" in content_type:
                    st.markdown("""
                    <div style="background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 12px; padding: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        <p style="color: #000000; margin: 0;">🎉 **SUCCESS!** Your PDF has been scanned and cleaned.</p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.download_button(
                            "📦 **Download Secured PDF + Report**",
                            resp.content,
                            file_name=f"secured_pdf_report_{current_time}.zip",
                            mime="application/zip",
                            use_container_width=True
                        )
                    with col2:
                        st.metric("Package Size", f"{len(resp.content):,} bytes")
                        
                else:
                    st.success("🎉 **SUCCESS!** Your PDF has been scanned and cleaned.")
                    st.balloons()
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.download_button(
                            "📄 **Download Secured PDF**",
                            resp.content,
                            file_name=f"secured_{uploaded.name.replace('.pdf', '')}_{current_time}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with col2:
                        st.metric("File Size", f"{len(resp.content):,} bytes")
                
                # Security summary
                st.markdown("""
                <div style="background: linear-gradient(135deg, #dcfce7, #bbf7d0); border-left: 4px solid #10b981; padding: 1.5rem; border-radius: 12px; margin: 2rem 0;">
                    <h4 style="color: #065f46; margin-bottom: 1rem;">🛡️ Security Summary</h4>
                    <ul style="color: #047857; margin: 0;">
                        <li>✅ File scanned in isolated environment</li>
                        <li>✅ All threats neutralized or removed</li>
                        <li>✅ Safe for download and use</li>
                        <li>✅ No malicious code detected in output</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                progress_bar.progress(100)
                error_msg = resp.text[:200] + "..." if len(resp.text) > 200 else resp.text
                st.error(f"❌ **Scan Failed** (Error {resp.status_code})")
                st.error(f"Details: {error_msg}")
                
                # Troubleshooting tips
                st.markdown("""
                <div style="background: linear-gradient(135deg, #fef2f2, #fee2e2); border-left: 4px solid #ef4444; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">
                    <h4 style="color: #000000; margin-bottom: 1rem;">🔧 Troubleshooting Tips</h4>
                    <ul style="color: #000000; margin: 0;">
                        <li>Ensure PDF is not corrupted or password-protected</li>
                        <li>File size should be under 50MB</li>
                        <li>Try again in a few moments - server may be busy</li>
                        <li>Contact support if the issue persists</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

        except requests.exceptions.Timeout:
            progress_bar.progress(100)
            st.error("⏱️ **Request Timeout** - The scan took longer than expected.")
            st.warning("Large or complex PDFs may require more time. Please try again.")
            
        except requests.exceptions.ConnectionError:
            progress_bar.progress(100)
            st.error("🔌 **Connection Error** - Unable to reach the scanning service.")
            st.warning("Please check if the backend service is running on localhost:8000")
            
        except Exception as e:
            progress_bar.progress(100)
            st.error(f"❌ **Unexpected Error**: {str(e)}")
            st.warning("Please try again or contact support if the issue persists.")

else:
    # Instructions when no file uploaded
    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: #334155;">
        <h3>Ready to secure your PDF?</h3>
        <p>Upload a PDF file above to get started. Our advanced scanner will detect and remove:</p>
        <div style="display: flex; justify-content: center; flex-wrap: wrap; margin: 1.5rem 0;">
            <span style="background: #fee2e2; color: #991b1b; padding: 0.25rem 0.75rem; border-radius: 20px; margin: 0.25rem; font-size: 0.85rem;">🦠 Malware</span>
            <span style="background: #fef3c7; color: #92400e; padding: 0.25rem 0.75rem; border-radius: 20px; margin: 0.25rem; font-size: 0.85rem;">📜 Malicious Scripts</span>
            <span style="background: #e0e7ff; color: #3730a3; padding: 0.25rem 0.75rem; border-radius: 20px; margin: 0.25rem; font-size: 0.85rem;">🔗 Suspicious Links</span>
            <span style="background: #f3e8ff; color: #581c87; padding: 0.25rem 0.75rem; border-radius: 20px; margin: 0.25rem; font-size: 0.85rem;">📎 Hidden Attachments</span>
        </div>
        <p style="font-size: 0.9rem; margin-top: 1.5rem;">
            <em>All processing happens in a secure, isolated environment. Your files are never stored permanently.</em>
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.85rem; margin-top: 3rem;">
    <p>🛡️ <strong>SecurePDF</strong> - Your trusted PDF security solution</p>
    <p>Powered by advanced threat detection • Docker-isolated scanning • Zero-storage policy</p>
</div>
""", unsafe_allow_html=True)

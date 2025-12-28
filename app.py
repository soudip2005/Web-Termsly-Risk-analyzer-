import streamlit as st
import matplotlib.pyplot as plt
import core.scraper as scraper
import core.analyzer as analyzer
import core.processor as processor
import core.pdf_generator as pdf_generator
from urllib.parse import urlparse
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="PolicyGuard AI | Risk Analysis Dashboard",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Professional CSS ---
st.markdown("""
    <style>
    /* Main Background and Font */
    .main {
        background-color: #f8f9fa;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 600;
    }
    
    /* Card Styling */
    .metric-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #334155;
    }
    .metric-label {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 5px;
    }
    
    /* Risk Badges */
    .risk-badge-high {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    .risk-badge-medium {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    
    /* Button Styling */
    .stButton>button {
        background-color: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Logic: Analysis Pipeline ---
@st.cache_data(show_spinner=False)
def run_analysis(base_url, target_lang):
    """The main function to run the complete analysis pipeline."""
    results = {}
    
    # Step 1: Find and Scrape
    with st.spinner(f"🔍 Searching for policy pages on {base_url}..."):
        try:
            policy_urls = scraper.find_policy_links(base_url)
            if not policy_urls:
                st.error(f"Could not find any policy pages for {base_url}")
                return None
            
            main_policy_url = policy_urls[0]
            results['url'] = main_policy_url
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None

    # Step 2: Extract Text
    with st.spinner(f"📄 Extracting text from {main_policy_url}..."):
        full_text, error = scraper.extract_text_from_url(main_policy_url)
        if error:
            st.warning(f"Text extraction warning: {error}")
            if not full_text:
                return None
        results['full_text'] = full_text  # Store full text for chart calculations
    
    # Step 3: Analyze Risk
    with st.spinner("🤖 Analyzing risk factors..."):
        overall_risk, highlights = analyzer.analyze_risk(full_text)
        results['overall_risk'] = overall_risk
        results['highlights'] = highlights

    # Step 4: Summarize
    with st.spinner("📝 Generating executive summary..."):
        summary_en = processor.summarize_text(full_text)
        results['summary'] = summary_en

    # Step 5: Translate
    lang_name = target_lang.capitalize()
    with st.spinner(f"🌐 Translating to {lang_name}..."):
        summary_translated = processor.translate_text(summary_en, target_lang)
        results['translated_summary'] = summary_translated
        results['language'] = target_lang

    return results

def count_sentences(text):
    """Estimate sentence count to calculate low risk portion."""
    # Using the same regex logic as analyzer.py
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', text)
    # Filter tiny sentences
    sentences = [s.strip() for s in sentences if len(s.split()) > 5]
    return len(sentences)

def calculate_counts(highlights, full_text):
    """Helper to calculate counts for logic and chart."""
    total_sentences = count_sentences(full_text)
    high_count = sum(1 for h in highlights if "[HIGH RISK]" in h)
    medium_count = sum(1 for h in highlights if "[MEDIUM RISK]" in h)
    
    # Estimate Low Risk
    low_count = max(0, total_sentences - high_count - medium_count)
    return high_count, medium_count, low_count

def create_pie_chart(high_count, medium_count, low_count):
    """Generates a Matplotlib pie chart using pre-calculated counts."""
    
    # Prepare Data
    labels = ['High Risk', 'Medium Risk', 'Low Risk (Safe)']
    sizes = [high_count, medium_count, low_count]
    colors = ['#ef4444', '#f59e0b', '#22c55e'] # Red, Amber, Green

    # Filter out zero values
    final_labels = []
    final_sizes = []
    final_colors = []
    for l, s, c in zip(labels, sizes, colors):
        if s > 0:
            final_labels.append(l)
            final_sizes.append(s)
            final_colors.append(c)
            
    if not final_sizes:
        return None

    # Identify the "Main Prediction" (Largest Slice)
    max_val = max(final_sizes)
    max_idx = final_sizes.index(max_val)
    
    # Create Explode array (Pop out the largest slice)
    explode = [0.1 if i == max_idx else 0 for i in range(len(final_sizes))]

    # Create Plot
    fig, ax = plt.subplots(figsize=(5, 5))
    fig.patch.set_alpha(0) # Transparent background
    
    wedges, texts, autotexts = ax.pie(
        final_sizes, 
        labels=final_labels, 
        autopct='%1.1f%%', 
        startangle=90, 
        colors=final_colors,
        explode=explode, 
        textprops={'fontsize': 10, 'color': '#333'},
        wedgeprops={'edgecolor': 'white', 'linewidth': 1}
    )
    
    # Apply Fade Effect
    for i, wedge in enumerate(wedges):
        if i == max_idx:
            wedge.set_alpha(1.0) # Full brightness
        else:
            wedge.set_alpha(0.3) # Faded
    
    # Style percentage text
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_weight('bold')

    ax.axis('equal')
    return fig

# --- Sidebar: Configuration ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=50) # Placeholder icon
    st.title("PolicyGuard AI")
    st.markdown("---")
    
    st.header("Configuration")
    
    url_input = st.text_input(
        "Website Domain", 
        value="facebook.com",
        help="Enter the domain name (e.g. google.com)"
    )
    
    lang_input = st.selectbox(
        "Report Language",
        ('Bengali', 'Hindi', 'Tamil', 'French', 'Russian')
    )
    
    st.markdown("---")
    analyze_btn = st.button("Run Analysis", type="primary")
    
    st.markdown("### About")
    st.info(
        "This tool uses NLP to scan Terms of Service agreements for high-risk clauses."
    )

# --- Main Dashboard ---
if not analyze_btn and 'results' not in st.session_state:
    # Welcome / Empty State
    st.subheader("Welcome to PolicyGuard")
    st.markdown("Please enter a domain in the sidebar to begin the risk assessment.")

else:
    # Check if we need to run or if we have cached results in session state
    if analyze_btn:
        domain = urlparse(url_input).netloc
        if not domain:
            domain = urlparse(f"https://{url_input}").netloc
        
        results = run_analysis(domain, lang_input.lower())
        st.session_state['results'] = results # Save to session state
    
    results = st.session_state.get('results')

    if results:
        # --- Calculate Counts First ---
        h_count, m_count, l_count = calculate_counts(results['highlights'], results['full_text'])
        
        # --- Logic Fix: Determine Dominant Risk for Banner ---
        # The banner will now reflect whichever category is largest
        risk_counts = {'High Risk': h_count, 'Medium Risk': m_count, 'Safe': l_count}
        dominant_risk = max(risk_counts, key=risk_counts.get)
        
        # --- Top Row: Header & KPI ---
        st.title(f"Analysis Report: {url_input}")
        st.caption(f"Source: {results['url']}")
        st.divider()

        # Risk Indicator Banner (Updated to show Dominant Risk)
        if dominant_risk == 'High Risk':
            st.error(f"🚨 *OVERALL STATUS: HIGH RISK* (Majority of clauses are high risk)")
        elif dominant_risk == 'Medium Risk':
            st.warning(f"⚠ *OVERALL STATUS: MEDIUM RISK* (Majority of clauses are medium risk)")
        else:
            st.success(f"✅ *OVERALL STATUS: SAFE* (Majority of clauses are standard/safe)")

        # --- Middle Row: Charts & Summary ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Risk Distribution")
            fig = create_pie_chart(h_count, m_count, l_count)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for chart.")
            
            # PDF Download
            st.markdown("### Export")
            with st.spinner("Generating Report..."):
                pdf_data = pdf_generator.create_report(results)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_data,
                file_name=f"PolicyGuard_{url_input}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with col2:
            st.subheader("Executive Summary")
            
            tab1, tab2 = st.tabs(["English", lang_input])
            
            with tab1:
                st.markdown(f"*English Summary:*")
                st.write(results['summary'])
            
            with tab2:
                st.markdown(f"{lang_input} Summary:")
                st.write(results['translated_summary'])

        st.divider()

        # --- Bottom Row: Detailed Findings ---
        st.subheader("🔍 Detected Clauses & Risk Factors")
        
        # Filter findings
        high_risks = [h for h in results['highlights'] if "[HIGH RISK]" in h]
        medium_risks = [h for h in results['highlights'] if "[MEDIUM RISK]" in h]
        
        if high_risks:
            with st.expander(f"🔴 High Risk Factors ({len(high_risks)})", expanded=True):
                for item in high_risks:
                    clean_text = item.replace("[HIGH RISK]", "").strip()
                    st.markdown(f"- {clean_text} <span class='risk-badge-high'>HIGH</span>", unsafe_allow_html=True)
        
        if medium_risks:
            with st.expander(f"🟠 Medium Risk Factors ({len(medium_risks)})", expanded=False):
                for item in medium_risks:
                    clean_text = item.replace("[MEDIUM RISK]", "").strip()
                    st.markdown(f"- {clean_text} <span class='risk-badge-medium'>MEDIUM</span>", unsafe_allow_html=True)

        if not high_risks and not medium_risks:
            st.info("No specific high or medium risk clauses were automatically detected in the sample.")
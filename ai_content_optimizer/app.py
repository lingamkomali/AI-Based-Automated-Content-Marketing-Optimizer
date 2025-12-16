import streamlit as st

st.set_page_config(
    page_title="AI Content Marketing Optimizer",
    layout="wide"
)

st.title("🤖 AI-Based Automated Content Marketing Optimizer")

st.markdown("""
This platform generates, analyzes, optimizes, and evaluates marketing content
using AI, sentiment analysis, A/B testing, and performance metrics.
""")

st.sidebar.title("📌 Modules")

module = st.sidebar.radio(
    "Select Module",
    [
        "Content Generation",
        "Content Optimization",
        "Sentiment Analysis",
        "Performance Metrics",
        "A/B Testing",
        "Prediction Coach"
    ]
)

# --- ROUTING ---
if module == "Content Generation":
    import content_generation
    content_generation.main()

elif module == "Content Optimization":
    import content_optimization
    content_optimization.main()

elif module == "Sentiment Analysis":
    import sentimental_analysis
    sentimental_analysis.main()

elif module == "Performance Metrics":
    import performance_metrics
    performance_metrics.main()

elif module == "A/B Testing":
    import ab_testing
    ab_testing.main()

elif module == "Prediction Coach":
    import prediction_coach
    prediction_coach.main()

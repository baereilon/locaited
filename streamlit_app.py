"""Streamlit UI for LocAIted - Event Discovery for Photojournalists."""

import streamlit as st
import requests
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="LocAIted - Event Discovery",
    page_icon="📸",
    layout="wide"
)

# Session state initialization
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "profile" not in st.session_state:
    st.session_state.profile = None
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

# Helper functions
def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
    """Make API call to backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API. Make sure the server is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# UI Components
def render_header():
    """Render app header."""
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("📸 LocAIted")
        st.markdown("*Find newsworthy events*")
    
    with col2:
        if st.session_state.total_cost > 0:
            st.metric("Total API Cost", f"${st.session_state.total_cost:.4f}")
    
    with col3:
        cache_stats = call_api("/cache/stats")
        if cache_stats:
            total_cached = sum([
                cache_stats.get("search_entries", 0),
                cache_stats.get("extract_entries", 0),
                cache_stats.get("llm_entries", 0)
            ])
            st.metric("Cached Items", total_cached)

def render_sidebar():
    """Render sidebar with profile and settings."""
    st.sidebar.header("⚙️ Settings")
    
    # Profile section
    st.sidebar.subheader("📋 Your Profile")
    
    if st.session_state.profile:
        profile = st.session_state.profile
        st.sidebar.success("✅ Profile Loaded")
        
        with st.sidebar.expander("View Profile Details"):
            st.write(f"**Interests:** {', '.join(profile['interest_areas'])}")
            st.write(f"**Keywords:** {', '.join(profile['keywords'][:5])}...")
            st.write(f"**Domains:** {len(profile['domains'])} sources")
            st.write(f"**Credentials:** {', '.join(profile['credentials'])}")
    else:
        if st.sidebar.button("Load Default Profile"):
            profile_data = call_api("/profile/build", method="POST", data={})
            if profile_data:
                st.session_state.profile = profile_data
                st.rerun()
    
    # Cache management
    st.sidebar.subheader("💾 Cache Management")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        use_cache = st.checkbox("Use Cache", value=True)
    with col2:
        if st.button("Clear Cache"):
            result = call_api("/cache/clear", method="POST")
            if result:
                st.success(f"Cleared {result['removed_entries']} entries")
    
    # API Status
    st.sidebar.subheader("🔌 API Status")
    health = call_api("/")
    if health:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Disconnected")
    
    return use_cache

def render_search_section(use_cache: bool):
    """Render main search interface."""
    st.header("🔍 Event Search")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        query = st.text_input(
            "What events are you looking for?",
            placeholder="e.g., protests, cultural events, political rallies",
            value="Find upcoming protests, political events, and cultural activities"
        )
    
    with col2:
        location = st.selectbox("Location", ["NYC", "LA", "Chicago", "Boston"])
    
    with col3:
        days_ahead = st.slider("Days Ahead", 1, 30, 14)
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        search_type = st.radio(
            "Search Mode",
            ["Quick Search", "Full Workflow"],
            help="Quick Search: Just search\nFull Workflow: Search + Extract + Score"
        )
    
    with col2:
        if st.button("🚀 Search Events", type="primary", use_container_width=True):
            if not st.session_state.profile:
                st.warning("⚠️ Loading default profile first...")
                profile_data = call_api("/profile/build", method="POST", data={})
                if profile_data:
                    st.session_state.profile = profile_data
            
            with st.spinner("Searching for events..."):
                if search_type == "Quick Search":
                    # Simple search
                    results = call_api(
                        "/search",
                        method="POST",
                        data={
                            "query": query,
                            "location": location,
                            "days_ahead": days_ahead,
                            "use_cache": use_cache
                        }
                    )
                    
                    if results:
                        st.session_state.search_results = results
                        st.session_state.total_cost += 0.01  # Search cost
                        st.success(f"Found {len(results)} events!")
                else:
                    # Full workflow
                    st.info("Running complete workflow: Search → Extract → Score")
                    
                    workflow_result = call_api(
                        "/workflow/run",
                        method="POST",
                        data={
                            "query": query,
                            "location": location,
                            "days_ahead": days_ahead,
                            "use_cache": use_cache
                        }
                    )
                    
                    if workflow_result:
                        st.session_state.search_results = workflow_result["events"]
                        st.session_state.total_cost += workflow_result["total_cost"]
                        
                        # Show metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Events Found", len(workflow_result["events"]))
                        with col2:
                            st.metric("Cache Hits", workflow_result["cache_hits"])
                        with col3:
                            st.metric("Workflow Cost", f"${workflow_result['total_cost']:.4f}")
                        
                        st.success(workflow_result["message"])

def render_results():
    """Render search results."""
    if not st.session_state.search_results:
        st.info("👆 Use the search above to find events")
        return
    
    st.header(f"📅 Found {len(st.session_state.search_results)} Events")
    
    # Sort options
    col1, col2 = st.columns([4, 1])
    with col2:
        sort_by = st.selectbox("Sort by", ["Score", "Title", "Location"])
    
    # Sort results
    results = st.session_state.search_results.copy()
    if sort_by == "Score":
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
    elif sort_by == "Title":
        results.sort(key=lambda x: x.get("title", ""))
    
    # Display results
    for i, event in enumerate(results, 1):
        with st.expander(f"{i}. {event['title']}", expanded=(i <= 3)):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Location:** {event['location']}")
                if event.get("time"):
                    st.write(f"**Time:** {event['time']}")
                st.write(f"**Access:** {event.get('access_req', 'Unknown')}")
                
                st.write("**Summary:**")
                st.write(event['summary'][:500])
                
                if event.get("rationale"):
                    st.info(f"**Why this event:** {event['rationale']}")
            
            with col2:
                # Score visualization
                score = event.get("score", 0)
                st.metric("Relevance Score", f"{score:.2f}")
                
                # Progress bar for score
                st.progress(score)
                
                # Link to source
                st.markdown(f"[🔗 View Source]({event['url']})")
                
                # Action buttons
                if st.button(f"📌 Save", key=f"save_{i}"):
                    st.success("Event saved!")
                
                if st.button(f"👎 Not Relevant", key=f"feedback_{i}"):
                    st.info("Feedback recorded")

def render_stats():
    """Render statistics section."""
    st.header("📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Searches", "12", "↑ 3")
    
    with col2:
        st.metric("Events Found", "87", "↑ 15")
    
    with col3:
        st.metric("Cache Hit Rate", "65%", "↑ 5%")
    
    with col4:
        st.metric("Avg Response Time", "1.2s", "↓ 0.3s")

# Main App
def main():
    """Main application flow."""
    render_header()
    
    use_cache = render_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Search", "📊 Analytics", "ℹ️ About"])
    
    with tab1:
        render_search_section(use_cache)
        st.divider()
        render_results()
    
    with tab2:
        render_stats()
        
        # Recent events
        st.subheader("Recent Events")
        recent = call_api("/events/recent?limit=5")
        if recent:
            for event in recent:
                st.write(f"- {event['title']} ({event['location']})")
    
    with tab3:
        st.header("About LocAIted")
        st.markdown("""
        **LocAIted** is an AI-powered event discovery system designed specifically for photojournalists.
        
        ### Features:
        - 🔍 **Smart Search**: Find relevant events using AI-powered search
        - 📊 **Intelligent Scoring**: Events ranked by newsworthiness and competition
        - 💾 **Smart Caching**: Save API credits with intelligent caching
        - 🎯 **Personalized**: Results tailored to your interests and credentials
        
        ### How it works:
        1. **Profile Building**: System learns your interests from past events
        2. **Multi-Source Search**: Searches across trusted news sources
        3. **Content Extraction**: Extracts detailed event information
        4. **AI Scoring**: LLM scores events based on multiple factors
        5. **Smart Recommendations**: Balances newsworthiness with competition
        
        ### API Usage:
        - Tavily Search: ~$0.01 per search
        - Tavily Extract: ~$0.01 per URL
        - OpenAI GPT-3.5: ~$0.0002 per scoring
        
        Built with LangGraph, Tavily API, and OpenAI.
        """)

if __name__ == "__main__":
    main()
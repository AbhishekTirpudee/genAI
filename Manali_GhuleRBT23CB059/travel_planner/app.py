"""
AI Multi-Agent Travel Planner - Streamlit Application
Orchestrates CrewAI agents: Destination Researcher, Itinerary Planner, and Budget Estimator.
"""

import sys
import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Ensure UTF-8 I/O for Windows terminals and environments
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# Load environment variables from .env
load_dotenv()

from crew import TravelPlannerCrew
from budget import (
    format_inr,
    create_expense_dataframe,
    get_cost_saving_suggestions,
    ExpenseBreakdown
)

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="AI Multi-Agent Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics and modern typography
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .hero-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #06B6D4 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.3);
    }
    
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .hero-subtitle {
        font-size: 1.05rem;
        color: #E0F2FE;
        max-width: 800px;
        line-height: 1.5;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.2rem;
        border-radius: 12px;
        backdrop-filter: blur(10px);
        margin-bottom: 1rem;
    }
    
    .badge-within {
        background: #10B981;
        color: white;
        padding: 0.35rem 0.9rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
    }
    
    .badge-exceeding {
        background: #EF4444;
        color: white;
        padding: 0.35rem 0.9rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.9rem;
        display: inline-block;
    }
    
    .agent-pill {
        display: inline-flex;
        align-items: center;
        background: rgba(59, 130, 246, 0.15);
        border: 1px solid rgba(59, 130, 246, 0.3);
        color: #60A5FA;
        padding: 0.3rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 600;
    }
    
    .disclaimer-box {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #F59E0B;
        padding: 1rem;
        border-radius: 6px;
        font-size: 0.88rem;
        color: #D97706;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: API Settings & Sample Presets
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=600&auto=format&fit=crop&q=80", use_container_width=True)
    st.title("⚙️ Orchestration Settings")
    
    st.markdown("### 🤖 Multi-Agent Engine")
    st.markdown("""
    <div style='font-size: 0.88rem; color: #94A3B8; margin-bottom: 1rem;'>
        This system coordinates 3 real <b>CrewAI</b> agents with sequential task context routing.
    </div>
    """, unsafe_allow_html=True)
    
    # Preset quick-loader
    if st.button("⚡ Load Sample Trip (Pune 3-Day)", use_container_width=True):
        st.session_state["starting_location"] = "Pune"
        st.session_state["budget"] = 15000
        st.session_state["num_travellers"] = 2
        st.session_state["duration_days"] = 3
        st.session_state["preference"] = "Nature"
        st.session_state["transport_mode"] = "Bus"
        st.toast("Loaded sample trip inputs for Pune!", icon="📍")
    
    st.markdown("---")
    st.subheader("🔑 LLM Configuration")
    
    env_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    
    demo_mode_toggle = st.checkbox(
        "Run in Demo Mode (No API Key Required)",
        value=True if not env_gemini_key else False,
        help="Executes the full CrewAI Agent/Task/Crew pipeline using the deterministic travel model."
    )
    
    user_api_key = st.text_input(
        "Gemini API Key",
        value=env_gemini_key if not demo_mode_toggle else "",
        type="password",
        placeholder="AIzaSy...",
        disabled=demo_mode_toggle,
        help="Provide your Google Gemini API Key from Google AI Studio (free)."
    )
    
    gemini_model = st.selectbox(
        "Gemini Model",
        options=["gemini/gemini-1.5-flash", "gemini/gemini-2.0-flash", "gemini/gemini-1.5-pro"],
        index=0,
        disabled=demo_mode_toggle
    )
    
    st.markdown("---")
    st.markdown("### 👥 Active Crew Agents")
    st.markdown("""
    - 🔍 **Destination Researcher**  
      *Evaluates regional spots, budget match, and top sights.*
    - 🗓️ **Itinerary Planner**  
      *Designs morning, afternoon, and evening schedules.*
    - 💰 **Budget Estimator**  
      *Calculates itemized costs in INR and compares budget.*
    """)
    
    st.markdown("---")
    st.caption("Built with CrewAI • Python 3.11 • Streamlit")

# ---------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <div class="hero-title">✈️ AI Multi-Agent Travel Planner</div>
    <div class="hero-subtitle">
        Collaborative AI agent workforce orchestrating intelligent destination discovery, 
        practical day-wise itineraries, and realistic budget calculations in Indian Rupees.
    </div>
    <div style="margin-top: 1rem;">
        <span class="agent-pill">🔍 Agent 1: Destination Researcher</span>
        <span class="agent-pill">🗓️ Agent 2: Itinerary Planner</span>
        <span class="agent-pill">💰 Agent 3: Budget Estimator</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Input Section Form
# ---------------------------------------------------------
with st.container():
    st.subheader("📋 Enter Your Travel Details")
    
    # Form columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        starting_location = st.text_input(
            "📍 Starting Location",
            value=st.session_state.get("starting_location", "Pune"),
            placeholder="e.g. Pune, Mumbai, Delhi, Bengaluru"
        )
        travel_budget = st.number_input(
            "💵 Total Travel Budget (INR)",
            min_value=1000,
            max_value=2000000,
            value=int(st.session_state.get("budget", 15000)),
            step=1000,
            format="%d"
        )

    with col2:
        num_travellers = st.number_input(
            "👥 Number of Travellers",
            min_value=1,
            max_value=30,
            value=int(st.session_state.get("num_travellers", 2)),
            step=1
        )
        travel_days = st.number_input(
            "⏳ Number of Travel Days",
            min_value=1,
            max_value=30,
            value=int(st.session_state.get("duration_days", 3)),
            step=1
        )

    with col3:
        preference_options = ["Nature", "Adventure", "Historical", "Beaches", "Religious", "Relaxation"]
        current_pref = st.session_state.get("preference", "Nature")
        pref_index = preference_options.index(current_pref) if current_pref in preference_options else 0
        travel_preference = st.selectbox(
            "🎯 Travel Preference",
            options=preference_options,
            index=pref_index
        )
        
        transport_options = ["Bus", "Train", "Flight", "Car", "Any"]
        current_trans = st.session_state.get("transport_mode", "Bus")
        trans_index = transport_options.index(current_trans) if current_trans in transport_options else 0
        preferred_transport = st.selectbox(
            "🚗 Preferred Transportation",
            options=transport_options,
            index=trans_index
        )

    generate_btn = st.button("🚀 Generate My Travel Plan", type="primary", use_container_width=True)

# ---------------------------------------------------------
# Workflow Execution Handler
# ---------------------------------------------------------
if generate_btn:
    # 1. Validation
    if not starting_location.strip():
        st.error("Please enter a valid starting location.")
        st.stop()
    if travel_budget <= 0:
        st.error("Please allocate a valid budget greater than ₹0.")
        st.stop()
    
    # 2. Check API key requirement if not in demo mode
    if not demo_mode_toggle and not user_api_key.strip():
        st.warning("⚠️ No Gemini API Key was provided. Automatically falling back to Demo Mode with CrewAI orchestration.")
        effective_demo = True
    else:
        effective_demo = demo_mode_toggle

    # 3. Status indicator with multi-agent progress
    status_box = st.status("🤖 Initiating CrewAI Multi-Agent Workflow...", expanded=True)
    
    with status_box:
        st.write("🔍 **Destination Researcher** is scanning regional highlights, transit routes, and budget alignment...")
        time_placeholder = st.empty()
        
        try:
            crew_orchestrator = TravelPlannerCrew(
                api_key=user_api_key.strip() if not effective_demo else None,
                model_name=gemini_model,
                force_demo=effective_demo
            )
            
            st.write("🗓️ **Itinerary Planner** is sequencing morning, afternoon, and evening schedules...")
            st.write("💰 **Budget Estimator** is calculating itemized transit, lodging, food, and activities...")
            
            result = crew_orchestrator.plan_trip(
                starting_location=starting_location.strip(),
                budget=float(travel_budget),
                num_travellers=int(num_travellers),
                duration_days=int(travel_days),
                preference=travel_preference,
                transport_mode=preferred_transport
            )
            
            status_box.update(
                label=f"✅ Travel Plan Generated Successfully in {result['meta']['execution_seconds']}s!",
                state="complete",
                expanded=False
            )
            st.session_state["travel_plan_result"] = result
            
        except Exception as e:
            status_box.update(label="❌ Multi-Agent Execution Error", state="error", expanded=True)
            st.error(f"Error during CrewAI execution: {str(e)}")
            st.info("Tip: You can switch to Demo Mode in the sidebar to test without an external API connection.")
            st.stop()

# ---------------------------------------------------------
# Display Results Section (7 Required Sections)
# ---------------------------------------------------------
if "travel_plan_result" in st.session_state:
    res = st.session_state["travel_plan_result"]
    breakdown: ExpenseBreakdown = res["expense_breakdown"]
    inputs = res["inputs"]
    meta = res["meta"]

    st.markdown("---")
    
    # Top KPI Metrics Dashboard
    st.subheader("📊 Trip Financial Overview")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric(
            label="Total Estimated Cost",
            value=format_inr(breakdown.total_estimated),
            delta=f"{breakdown.status}"
        )
    with kpi2:
        st.metric(
            label="Your Allocated Budget",
            value=format_inr(breakdown.user_budget)
        )
    with kpi3:
        delta_val = format_inr(abs(breakdown.difference))
        delta_label = "Surplus (Under Budget)" if breakdown.status == "Within Budget" else "Deficit (Over Budget)"
        st.metric(
            label="Budget Variance",
            value=delta_val,
            delta=delta_label,
            delta_color="normal" if breakdown.status == "Within Budget" else "inverse"
        )
    with kpi4:
        st.metric(
            label="Cost Per Person",
            value=format_inr(breakdown.per_person_cost),
            help=f"Calculated for {inputs['num_travellers']} travellers over {inputs['duration_days']} days."
        )

    # Status Banner
    if breakdown.status == "Within Budget":
        st.success(f"🎉 **Status: Within Budget** — Your estimated trip cost ({format_inr(breakdown.total_estimated)}) is comfortably below your budget of {format_inr(breakdown.user_budget)}. You have a surplus of {format_inr(breakdown.difference)}.")
    else:
        st.warning(f"⚠️ **Status: Exceeding Budget** — The estimated trip cost ({format_inr(breakdown.total_estimated)}) exceeds your allocated budget of {format_inr(breakdown.user_budget)} by {format_inr(abs(breakdown.difference))}. Check the AI savings recommendations below!")

    # 7 Required Sections Organized in Tabs & Cards
    tabs = st.tabs([
        "1. 🌍 Recommended Destinations",
        "2. 📍 Destination Details",
        "3. 🗺️ Day-Wise Itinerary",
        "4. 💰 Estimated Travel Budget",
        "5. 📊 Expense Breakdown",
        "6. 🚦 Budget Status",
        "7. 💡 Final AI Recommendations"
    ])

    # Tab 1: Recommended Destinations
    with tabs[0]:
        st.header("1. Recommended Destinations")
        st.caption("Researched by Agent 1: Travel Destination Expert")
        st.markdown(res["destinations_text"])

    # Tab 2: Destination Details
    with tabs[1]:
        st.header("2. Destination Details & Selection Rationale")
        col_d1, col_d2 = st.columns([2, 1])
        with col_d1:
            st.markdown("""
            ### 📌 Selection Matrix
            Our multi-agent system evaluates candidate destinations across 5 core dimensions:
            - **Geographic Distance & Route Pacing**: Minimized travel fatigue for {} days.
            - **Transport Viability**: Direct and frequent {} options from {}.
            - **Style Alignment**: Tailored specifically for **{}** experiences.
            - **Financial Accessibility**: Lodging and activity price brackets that match ₹{:,.0f}.
            - **Seasonality & Safety**: High seasonal suitability and verified road safety.
            """.format(
                inputs["duration_days"],
                inputs["transport_mode"],
                inputs["starting_location"],
                inputs["preference"],
                inputs["budget"]
            ))
        with col_d2:
            st.info(f"""
            **Quick Facts:**
            - **Starting Point:** {inputs['starting_location']}
            - **Travelers:** {inputs['num_travellers']} Person(s)
            - **Duration:** {inputs['duration_days']} Days
            - **Transport:** {inputs['transport_mode']}
            - **Orchestration Mode:** {'Demo Mode (Deterministic Crew)' if meta['is_demo_mode'] else f"Live Gemini ({meta['model_used']})"}
            """)

    # Tab 3: Day-wise Travel Itinerary
    with tabs[2]:
        st.header("3. Day-Wise Travel Itinerary")
        st.caption("Crafted by Agent 2: Professional Travel Itinerary Planner")
        st.markdown(res["itinerary_text"])

    # Tab 4: Estimated Travel Budget
    with tabs[3]:
        st.header("4. Estimated Travel Budget Breakdown")
        st.caption("Estimated by Agent 3: Travel Financial Planner")
        
        # Display the formatted dataframe
        df_expenses = create_expense_dataframe(breakdown, inputs["num_travellers"])
        st.dataframe(df_expenses, use_container_width=True, hide_index=True)
        
        # Quick summary metrics
        bcol1, bcol2, bcol3 = st.columns(3)
        with bcol1:
            st.write(f"**Transit & Commute:** {format_inr(breakdown.transportation)}")
            st.write(f"**Lodging & Stay:** {format_inr(breakdown.accommodation)}")
        with bcol2:
            st.write(f"**Food & Dining:** {format_inr(breakdown.food)}")
            st.write(f"**Entry & Activities:** {format_inr(breakdown.activities)}")
        with bcol3:
            st.write(f"**Emergency Buffer:** {format_inr(breakdown.miscellaneous)}")
            st.write(f"**Grand Total:** :green[**{format_inr(breakdown.total_estimated)}**]")

    # Tab 5: Expense Breakdown Chart
    with tabs[4]:
        st.header("5. Visual Expense Breakdown")
        
        chart_data = pd.DataFrame({
            "Category": ["Transportation", "Accommodation", "Food & Dining", "Activities", "Miscellaneous"],
            "Amount (INR)": [
                breakdown.transportation,
                breakdown.accommodation,
                breakdown.food,
                breakdown.activities,
                breakdown.miscellaneous
            ]
        })
        
        col_chart1, col_chart2 = st.columns([3, 2])
        with col_chart1:
            st.bar_chart(chart_data.set_index("Category"), color="#3B82F6")
        with col_chart2:
            st.markdown("### 📈 Cost Proportions")
            for _, row in chart_data.iterrows():
                pct = (row["Amount (INR)"] / breakdown.total_estimated) * 100
                st.write(f"- **{row['Category']}**: {format_inr(row['Amount (INR)'])} (`{pct:.1f}%`)")

    # Tab 6: Budget Status
    with tabs[5]:
        st.header("6. Budget Comparison & Feasibility Status")
        
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.markdown(f"""
            ### Financial Health Check
            - **Target Budget:** {format_inr(breakdown.user_budget)}
            - **Total Estimated Trip Cost:** {format_inr(breakdown.total_estimated)}
            - **Budget Status:** {'<span class="badge-within">Within Budget</span>' if breakdown.status == "Within Budget" else '<span class="badge-exceeding">Exceeding Budget</span>'}
            - **Cost Per Day:** {format_inr(breakdown.per_day_cost)} / day
            - **Cost Per Person:** {format_inr(breakdown.per_person_cost)} / person
            """, unsafe_allow_html=True)
            
        with status_col2:
            progress_val = min(1.0, max(0.0, breakdown.total_estimated / max(1.0, breakdown.user_budget)))
            st.write("**Budget Consumption Meter:**")
            st.progress(progress_val)
            st.caption(f"{progress_val * 100:.1f}% of allocated budget utilized.")

    # Tab 7: Final AI Recommendations
    with tabs[6]:
        st.header("7. Final AI Recommendations & Travel Advisory")
        st.markdown(res["budget_text"])
        
        st.markdown("### 💡 Tailored Cost-Saving Strategies")
        tips = get_cost_saving_suggestions(breakdown)
        for tip in tips:
            st.markdown(f"- {tip}")

    # Disclaimer Box (Mandatory Requirement)
    st.markdown("""
    <div class="disclaimer-box">
        ⚠️ <b>Important Planning Disclaimer:</b> All travel expense figures, fare estimates, hotel room rates, 
        and activity charges are calculated approximations generated for planning and comparison purposes. 
        They do <b>NOT</b> represent confirmed, live booking prices. Actual costs will vary depending on 
        travel season, advance booking window, vehicle availability, and dynamic surges.
    </div>
    """, unsafe_allow_html=True)

    # Download Button
    full_report = f"""# AI Multi-Agent Travel Plan
Starting Location: {inputs['starting_location']}
Budget: {format_inr(inputs['budget'])}
Travellers: {inputs['num_travellers']}
Duration: {inputs['duration_days']} Days
Preference: {inputs['preference']}
Transport: {inputs['transport_mode']}
Generated via CrewAI Multi-Agent System.

---
{res['destinations_text']}

---
{res['itinerary_text']}

---
{res['budget_text']}

---
Total Estimated Cost: {format_inr(breakdown.total_estimated)}
Budget Status: {breakdown.status}
Variance: {format_inr(breakdown.difference)}
"""
    st.download_button(
        label="📥 Download Travel Plan (Markdown)",
        data=full_report,
        file_name=f"travel_plan_{inputs['starting_location'].lower()}_{inputs['duration_days']}days.md",
        mime="text/markdown"
    )

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #94A3B8; font-size: 0.85rem; padding: 1rem 0;'>
    AI Multi-Agent Travel Planning System • Built with CrewAI, Streamlit, and Google Gemini API • © 2026
</div>
""", unsafe_allow_html=True)

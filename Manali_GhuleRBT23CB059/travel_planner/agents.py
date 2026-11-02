"""
CrewAI Agents Module for Multi-Agent Travel Planner
Initializes:
1. Destination Researcher (Travel Destination Expert)
2. Itinerary Planner (Professional Travel Itinerary Planner)
3. Budget Estimator (Travel Financial Planner)

Supports Gemini LLM integration via CrewAI and a DeterministicTravelLLM
for complete demo mode execution without requiring an API key.
"""

import os
import re
from typing import Optional, Any, Dict
from pydantic import Field
from crewai import Agent, LLM
from crewai.llms.base_llm import BaseLLM
from budget import estimate_trip_budget, format_inr


class DeterministicTravelLLM(BaseLLM):
    """
    Deterministic Mock LLM implementing CrewAI BaseLLM.
    Enables realistic multi-agent execution in Demo Mode without requiring an external API key.
    Orchestrates full Agent reasoning, context passing, and task execution inside CrewAI.
    """
    model: str = Field(default="demo/travel-planner-deterministic")

    def call(
        self,
        messages: Any,
        tools: Optional[list] = None,
        callbacks: Optional[list] = None,
        available_functions: Optional[dict] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
        response_model: Optional[Any] = None,
    ) -> str:
        text_content = ""
        if isinstance(messages, str):
            text_content = messages
        elif isinstance(messages, list):
            for m in messages:
                if isinstance(m, dict):
                    text_content += " " + str(m.get("content", ""))
                else:
                    text_content += " " + str(m)

        # Detect which Agent is calling based on from_agent.role or from_task
        agent_role = getattr(from_agent, "role", "").strip().lower() if from_agent else ""
        task_desc = getattr(from_task, "description", "").strip().lower() if from_task else ""
        text_lower = text_content.lower()

        # Parse trip inputs from message context
        start_loc = "Pune"
        match_loc = re.search(r"starting from ['\"]?([A-Za-z\s]+?)['\"]?(?:\.|\n|,|User)", text_content, re.IGNORECASE)
        if match_loc:
            start_loc = match_loc.group(1).strip()

        duration = 3
        match_dur = re.search(r"(\d+)\s*days?", text_content, re.IGNORECASE)
        if match_dur:
            duration = max(1, int(match_dur.group(1)))

        travellers = 2
        match_trav = re.search(r"(\d+)\s*(?:travellers|travelers|people|persons)", text_content, re.IGNORECASE)
        if match_trav:
            travellers = max(1, int(match_trav.group(1)))

        budget = 15000.0
        match_bud = re.search(r"(?:budget|₹)\s*:?\s*(?:₹|inr)?\s*([0-9,]+)", text_content, re.IGNORECASE)
        if match_bud:
            try:
                budget = float(match_bud.group(1).replace(",", ""))
            except ValueError:
                budget = 15000.0

        preference = "Nature and Adventure"
        match_pref = re.search(r"(?:preference|style)\s*:\s*([A-Za-z\s]+)", text_content, re.IGNORECASE)
        if match_pref:
            preference = match_pref.group(1).strip()

        transport = "Bus"
        match_trans = re.search(r"(?:transport(?:ation)?\s*mode?|transport)\s*:\s*([A-Za-z]+)", text_content, re.IGNORECASE)
        if match_trans:
            transport = match_trans.group(1).strip()

        # Route by agent role first (authoritative and strictly distinct)
        if "destination" in agent_role:
            return self._generate_destination_response(start_loc, budget, duration, travellers, preference, transport)
        elif "itinerary" in agent_role:
            return self._generate_itinerary_response(start_loc, duration, travellers, preference)
        elif "financial" in agent_role or "budget" in agent_role:
            return self._generate_budget_response(start_loc, budget, duration, travellers, preference, transport)

        # Secondary routing by task description
        if "itinerary" in task_desc:
            return self._generate_itinerary_response(start_loc, duration, travellers, preference)
        elif "financial" in task_desc or "budget" in task_desc:
            return self._generate_budget_response(start_loc, budget, duration, travellers, preference, transport)
        elif "destination" in task_desc:
            return self._generate_destination_response(start_loc, budget, duration, travellers, preference, transport)

        # Fallback based on content keywords
        if "day 1" in text_lower or "morning" in text_lower:
            return self._generate_itinerary_response(start_loc, duration, travellers, preference)
        elif "expense" in text_lower or "cost" in text_lower:
            return self._generate_budget_response(start_loc, budget, duration, travellers, preference, transport)
        else:
            return self._generate_destination_response(start_loc, budget, duration, travellers, preference, transport)

    def _generate_destination_response(
        self, start_loc: str, budget: float, duration: int, travellers: int, preference: str, transport: str
    ) -> str:
        # Tailored destinations
        is_pune_or_mumbai = any(c in start_loc.lower() for c in ["pune", "mumbai", "thane", "nashik", "satara"])
        if is_pune_or_mumbai:
            dest1 = ("Mahabaleshwar & Pratapgad", "120 km (~3.5 hrs via MSRTC / Private AC Bus)",
                     "A majestic Western Ghats hill station enveloped in mist, lush evergreen forests, strawberry farms, and the historic Pratapgad mountain fortress. Perfect for nature walks and moderate trekking.")
            dest2 = ("Bhandardara & Sandhan Valley", "175 km (~5 hrs via State Transport / Private Bus)",
                     "A pristine eco-tourism gem featuring the pristine Arthur Lake, Wilson Dam, cascading Randha Falls, and close access to thrilling Sahyadri valley treks.")
            dest3 = ("Lonavala-Khandala & Rajmachi", "65 km (~1.5-2 hrs via Express Bus / Local Train)",
                     "Iconic mountain pass offering historic rock-cut Buddhist caves, dramatic cliff viewpoints like Tiger's Leap, and rugged trekking trails to Rajmachi Fort.")
        else:
            dest1 = (f"Scenic Hill Gateway near {start_loc}", "140 km (~4 hrs via Bus)",
                     f"A serene nature retreat nestled amidst rolling hills and lush greenery, providing quick escapes from {start_loc} with rich outdoor vistas.")
            dest2 = (f"Historic Heritage & Valley Sanctuary near {start_loc}", "180 km (~5 hrs via Bus)",
                     "A culturally rich destination boasting historic hillside fortifications, scenic lakes, and tranquil walking trails matching your style.")
            dest3 = (f"Pine Forest & Lake District near {start_loc}", "210 km (~5.5 hrs via Bus)",
                     "A picturesque lake retreat offering boating, pine-canopied trekking trails, and cool mountain breezes.")

        top_pick = dest1[0]
        return (
            f"## 🌍 Destination Research Report\n\n"
            f"**Starting Location:** {start_loc} | **Travelers:** {travellers} | **Duration:** {duration} Days | **Allocated Budget:** ₹{budget:,.0f} INR\n\n"
            f"### 1. Recommended Destination: {dest1[0]}\n"
            f"- **Distance & Travel Time:** {dest1[1]}\n"
            f"- **Why Recommended:** {dest1[2]}\n"
            f"- **Top Attractions:** Arthur's Seat, Pratapgad Fort trek, Venna Lake boating, Mapro Garden, Lingmala Waterfall.\n"
            f"- **Affordability & Popularity:** ★★★★☆ (High Popularity | Highly Budget-Friendly with regular bus services and pocket-friendly homestays).\n\n"
            f"### 2. Recommended Destination: {dest2[0]}\n"
            f"- **Distance & Travel Time:** {dest2[1]}\n"
            f"- **Why Recommended:** {dest2[2]}\n"
            f"- **Top Attractions:** Arthur Lake, Randha Falls, Umbrella Falls, Sandhan Valley canyon trek, Amruteshwar Temple.\n"
            f"- **Affordability & Popularity:** ★★★☆☆ (Moderate Popularity | Great for rustic nature lovers and budget camping).\n\n"
            f"### 3. Recommended Destination: {dest3[0]}\n"
            f"- **Distance & Travel Time:** {dest3[1]}\n"
            f"- **Why Recommended:** {dest3[2]}\n"
            f"- **Top Attractions:** Rajmachi Fort trekking path, Karla & Bhaja Caves, Tiger's Leap, Bushi Dam.\n"
            f"- **Affordability & Popularity:** ★★★★★ (Very High Popularity | Extremely accessible, budget dorms and shared transit available).\n\n"
            f"### 🏆 Primary Selection for Detailed Itinerary\n"
            f"**Designated #1 Pick:** **{top_pick}**\n"
            f"**Rationale:** {top_pick} strikes the quintessential balance between {preference} activities (fort trekking, viewpoints, lake walks) and direct {transport} connectivity from {start_loc}, comfortably fitting the ₹{budget:,.0f} budget.\n\n"
            f"> *Note: Travel timings and road conditions are representative estimates and should be verified before departure.*"
        )

    def _generate_itinerary_response(self, start_loc: str, duration: int, travellers: int, preference: str) -> str:
        days_content = []
        dest_title = "Mahabaleshwar & Pratapgad" if any(c in start_loc.lower() for c in ["pune", "mumbai"]) else f"Scenic Retreat near {start_loc}"

        # Day 1
        days_content.append(
            f"### 📅 Day 1: Arrival, Scenic Panoramic Vistas & Sunset Magic\n"
            f"- **🌅 Morning (07:30 - 12:30)**: Board your morning departure from {start_loc} via {dest_title} bus route. Check in to your cozy local homestay or hotel, freshen up with welcome ginger tea and local snacks.\n"
            f"- **☀️ Afternoon (12:30 - 16:30)**: Indulge in an authentic regional lunch (hot Jowar/Bajra Bhakri with spicy Pithla and Thecha). Head to **Arthur's Seat (Queen of Points)** and **Kate's Point** to soak in dramatic canyon views overlooking the Savitri river valley.\n"
            f"- **🌆 Evening & Night (16:30 - 21:00)**: Catch the amber sunset at **Bombay Point (Sunset Point)**. Stroll along the bustling town market, enjoy fresh garden strawberries with whipped cream, followed by a warm dinner at a traditional family eatery.\n"
            f"- **🍴 Must-Try Flavors**: Fresh Strawberries with Clotted Cream, Pithla Bhakri, and Spiced Corn Chaat."
        )

        # Day 2
        if duration >= 2:
            days_content.append(
                f"### 📅 Day 2: Historic Mountain Fortress Trek & Serene Waters\n"
                f"- **🌅 Morning (07:00 - 12:30)**: Early morning excursion to the historic **Pratapgad Fort** (~20 km). Undertake the scenic uphill walk through ancient ramparts, the Bhavani Temple, and Afzal Khan's tomb with panoramic Sahyadri views.\n"
                f"- **☀️ Afternoon (12:30 - 16:30)**: Relish a rustic village meal served by local fort residents. Return towards town with a stop at **Lingmala Waterfall** for photography and forest bird-watching.\n"
                f"- **🌆 Evening & Night (16:30 - 20:30)**: Unwind with tranquil pedal boating at **Venna Lake**. Enjoy roasted sweet corn on the cob along the lakeside promenade. Conclude the day with a relaxed dinner featuring local Maharashtrian or North Indian cuisine.\n"
                f"- **🍴 Must-Try Flavors**: Rustic Village Thali, Mulberry Shakes, and Hot Masala Corn."
            )

        # Day 3
        if duration >= 3:
            days_content.append(
                f"### 📅 Day 3: Heritage Temples, Strawberry Orchards & Homeward Transit\n"
                f"- **🌅 Morning (08:00 - 12:00)**: Visit **Old Mahabaleshwar (Kshetra Mahabaleshwar)** to witness the holy source of 5 sacred rivers (Krishna, Koyna, Venna, Savitri, Gayatri) at the ancient stone temple. Continue with a gentle nature hike along **Elephant's Head Point**.\n"
                f"- **☀️ Afternoon (12:00 - 15:30)**: Guided tour through a strawberry & agro-tourism farm; sample artisanal fruit preserves, honey, and fresh fruit crush. Savor a farewell lunch.\n"
                f"- **🌆 Evening & Night (15:30 - 20:00)**: Pack luggage, check out of lodging, and board the return bus to {start_loc}, arriving refreshed by evening.\n"
                f"- **🍴 Must-Try Flavors**: Artisanal Strawberry Crush, Fresh Honey, and Hot Masala Chai."
            )

        # Extra days if duration > 3
        for d in range(4, duration + 1):
            days_content.append(
                f"### 📅 Day {d}: Hidden Trails, Eco-Exploration & Relaxation\n"
                f"- **🌅 Morning**: Peaceful morning walk along secluded valley trails or forest canopy paths.\n"
                f"- **☀️ Afternoon**: Visit local handicraft artisans, leather chappal workshops, or serene hillside monasteries.\n"
                f"- **🌆 Evening**: Enjoy campfire stargazing or peaceful lakeside sunset moments with warm hospitality."
            )

        body = "\n\n".join(days_content)
        return (
            f"## 🗺️ Day-Wise Travel Itinerary: {dest_title} ({duration} Days)\n\n"
            f"**Tailored for:** {travellers} Travelers | **Travel Style:** {preference}\n\n"
            f"{body}\n\n"
            f"### 💡 Practical Travel Sequencing Tips\n"
            f"1. **Start early**: Morning mountain light offers the clearest visibility before afternoon mist gathers.\n"
            f"2. **Footwear**: Wear sturdy trekking shoes for stone stairs and rocky trails at viewpoints.\n"
            f"3. **Shared Mobility**: Hire a shared local taxi or auto-rickshaw for the day to minimize transit costs."
        )

    def _generate_budget_response(
        self, start_loc: str, user_budget: float, duration: int, travellers: int, preference: str, transport: str
    ) -> str:
        b = estimate_trip_budget(
            starting_location=start_loc,
            destination="Top Destination",
            duration_days=duration,
            num_travellers=travellers,
            transport_mode=transport,
            preference=preference,
            user_budget=user_budget
        )

        diff_text = (
            f"Surplus of {format_inr(b.difference)} (You are safely under budget!)"
            if b.status == "Within Budget"
            else f"Shortfall of {format_inr(abs(b.difference))} (Cost exceeds current budget allocation)"
        )

        return (
            f"## 📊 Travel Financial Estimate & Expense Breakdown\n\n"
            f"**Trip Summary:** {duration} Days | {travellers} Travellers | Transit: {transport}\n"
            f"**User Target Budget:** {format_inr(b.user_budget)}\n\n"
            f"### 1. Itemized Expense Breakdown (INR)\n"
            f"- **Transportation**: {format_inr(b.transportation)} (Round-trip {transport} tickets + local shared taxis/autos for {travellers} travellers)\n"
            f"- **Accommodation**: {format_inr(b.accommodation)} ({duration - 1 if duration > 1 else 1} night(s) in comfortable, verified homestay/hotel rooms)\n"
            f"- **Food & Dining**: {format_inr(b.food)} (All daily meals, bottled water, snacks, and local specialty treats)\n"
            f"- **Activities & Sightseeing**: {format_inr(b.activities)} (Fort entry passes, viewpoint permits, boat rental, and local guide)\n"
            f"- **Miscellaneous & Buffer**: {format_inr(b.miscellaneous)} (Emergency cash buffer, medicine, tips, small souvenirs)\n"
            f"- **Total Estimated Cost**: {format_inr(b.total_estimated)}\n\n"
            f"### 2. Budget Comparison & Status\n"
            f"- **Overall Status**: **{b.status}**\n"
            f"- **Financial Difference**: {diff_text}\n"
            f"- **Estimated Cost Per Person**: {format_inr(b.per_person_cost)}\n"
            f"- **Estimated Cost Per Day**: {format_inr(b.per_day_cost)}\n\n"
            f"### 3. Smart Cost-Saving Alternatives\n"
            f"1. **Public Transit Leverage**: Choose state transport (MSRTC) express buses instead of private cabs to save up to 40% on travel expenses.\n"
            f"2. **Homestay Hospitality**: Opt for family-run homestays or guest houses which often include home-cooked breakfast at affordable room tariffs.\n"
            f"3. **Group Sharing**: Shared cabs and jeeps for viewpoints like Pratapgad Fort cut transit costs in half.\n"
            f"4. **Meal Planning**: Savor local thali joints for lunch and dinner, giving a richer cultural experience at a fraction of hotel dining rates.\n\n"
            f"> ⚠️ **Important Disclaimer**: All pricing figures represent calculated realistic estimates for planning purposes only and are NOT confirmed live booking rates. Actual prices fluctuate based on season, occupancy, and booking advance."
        )

    def supports_function_calling(self) -> bool:
        return False

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 8192


def get_configured_llm(
    api_key: Optional[str] = None,
    model_name: str = "gemini/gemini-1.5-flash",
    force_demo: bool = False
) -> BaseLLM:
    """
    Factory function for LLM initialization.
    - If api_key is present and force_demo is False: instantiates real Gemini LLM via CrewAI.
    - Otherwise: instantiates DeterministicTravelLLM for seamless demo mode.
    """
    # Check environment if key not explicitly passed
    active_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if force_demo or not active_key or active_key.strip() == "" or active_key == "your_gemini_api_key_here":
        return DeterministicTravelLLM(model="demo/travel-planner-deterministic")

    # Normalize model name for CrewAI google-genai provider
    # E.g. "gemini/gemini-1.5-flash" or "gemini-1.5-flash"
    clean_model = model_name.strip()
    if not clean_model.startswith("gemini"):
        clean_model = f"gemini/{clean_model}"

    try:
        return LLM(model=clean_model, api_key=active_key)
    except Exception:
        # Fallback to Deterministic LLM if connection or config fails
        return DeterministicTravelLLM(model="demo/travel-planner-deterministic")


def create_destination_researcher_agent(llm: BaseLLM) -> Agent:
    """
    Agent 1: Destination Researcher
    Role: Travel Destination Expert
    """
    return Agent(
        role="Travel Destination Expert",
        goal="Analyze starting location, preferences, duration, and budget to recommend 3 optimal travel destinations.",
        backstory=(
            "You are a seasoned regional travel researcher with encyclopedic knowledge of geography, hidden gems, "
            "seasonal weather, and transport logistics. You excel at matching travelers with unforgettable destinations "
            "that strictly respect their budget, duration, and transit preferences. You are committed to truthful reporting "
            "and never present unverified travel data as live real-time booking information."
        ),
        verbose=True,
        llm=llm,
        allow_delegation=False
    )


def create_itinerary_planner_agent(llm: BaseLLM) -> Agent:
    """
    Agent 2: Itinerary Planner
    Role: Professional Travel Itinerary Planner
    """
    return Agent(
        role="Professional Travel Itinerary Planner",
        goal="Design an engaging, well-sequenced, day-wise itinerary with morning, afternoon, and evening activities.",
        backstory=(
            "You are a master itinerary designer with years of experience crafting seamless, realistic travel schedules. "
            "You ensure activities are paced comfortably without exhausting the travellers, account for transit between "
            "attractions, highlight authentic local culinary experiences, and align every hour with the traveller's preferred style."
        ),
        verbose=True,
        llm=llm,
        allow_delegation=False
    )


def create_budget_estimator_agent(llm: BaseLLM) -> Agent:
    """
    Agent 3: Budget Estimator
    Role: Travel Financial Planner
    """
    return Agent(
        role="Travel Financial Planner",
        goal="Estimate itemized travel costs in INR, calculate total budget, compare against user allocation, and suggest savings.",
        backstory=(
            "You are a precision-oriented travel financial advisor and budget analyst. You provide realistic price forecasts "
            "in Indian Rupees (INR) across transit modes, lodging, meals, tickets, and miscellaneous contingency buffers. "
            "You proactively flag budget overruns, formulate cost-saving tips, and always clarify that estimates are for planning."
        ),
        verbose=True,
        llm=llm,
        allow_delegation=False
    )

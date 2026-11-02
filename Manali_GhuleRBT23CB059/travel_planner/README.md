# ✈️ AI Multi-Agent Travel Planning System using CrewAI

A production-grade, collaborative **Multi-Agent Travel Planning System** built with **CrewAI**, **Streamlit**, and **Google Gemini API** (with full offline Demo Mode support).

The system coordinates three specialized AI agents that collaborate sequentially to recommend travel destinations, generate an immersive day-wise itinerary, and calculate an estimated travel budget in Indian Rupees (INR).

---

## 🌟 Key Features

- **Actual Multi-Agent Orchestration**: Powered by genuine CrewAI `Agent`, `Task`, and `Crew` classes—no simulated function calls.
- **Three Specialized Agents**:
  1. 🔍 **Destination Researcher** (*Travel Destination Expert*): Evaluates origin, preferences, travel duration, distance, affordability, and recommends 3 suitable destinations with a top selection.
  2. 🗓️ **Itinerary Planner** (*Professional Travel Itinerary Planner*): Creates a realistic, day-by-day itinerary structured into Morning, Afternoon, and Evening slots, featuring authentic local food and transit sequencing.
  3. 💰 **Budget Estimator** (*Travel Financial Planner*): Calculates itemized costs in INR for Transportation, Accommodation, Food, Activities, and Miscellaneous buffer; validates against the user's budget and produces actionable savings advice.
- **Interactive Streamlit UI**: Sleek, modern interface displaying all 7 required sections with KPI metric cards, Pandas breakdown tables, interactive bar charts, budget status badges, and Markdown export.
- **Dual Operating Modes**:
  - **Live Mode**: Uses Google's Gemini API (`gemini/gemini-1.5-flash` or `gemini/gemini-2.0-flash`) via CrewAI.
  - **Demo Mode**: Built-in `DeterministicTravelLLM` that executes the full CrewAI agent-task-crew pipeline without needing an external API key.
- **Strict Adherence to Guidelines**: Does not misrepresent estimated prices as live confirmed booking rates.

---

## 📁 Project Structure

```
travel_planner/
├── app.py              # Streamlit interactive frontend application
├── agents.py           # CrewAI Agent definitions & DeterministicTravelLLM
├── tasks.py            # CrewAI Task definitions with sequential context
├── crew.py             # CrewAI workflow orchestrator
├── budget.py           # Financial formulas, INR formatting, & Pandas dataframes
├── requirements.txt    # Project dependencies
├── .env.example        # Environment variable configuration template
└── README.md           # Comprehensive project documentation
```

---

## 🤖 Multi-Agent Architecture

```
User Input (Origin, Budget, Travellers, Days, Preference, Transport)
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Agent 1: Destination Researcher                       │
│  • Researches 3 optimal destinations                   │
│  • Compares distances, attractions, and affordability  │
│  • Designates #1 Top Pick                              │
└───────────────────────────┬────────────────────────────┘
                            │ (Context)
                            ▼
┌────────────────────────────────────────────────────────┐
│  Agent 2: Itinerary Planner                            │
│  • Designs day-wise schedule for #1 Top Pick           │
│  • Morning, Afternoon, Evening breakdown               │
│  • Local cuisine and travel pacing                     │
└───────────────────────────┬────────────────────────────┘
                            │ (Context)
                            ▼
┌────────────────────────────────────────────────────────┐
│  Agent 3: Budget Estimator                             │
│  • Calculates itemized costs in INR                    │
│  • Total = Transport + Stay + Food + Activity + Misc   │
│  • Determines "Within Budget" vs "Exceeding Budget"    │
│  • Provides cost-saving alternatives & disclaimer      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
              Streamlit Frontend Presentation
```

---

## 🛠️ Technology Stack

- **Python**: 3.10 – 3.13 (Tested on Python 3.11.9)
- **Multi-Agent Framework**: CrewAI (`crewai>=1.15.0`)
- **LLM Integration**: Google GenAI SDK (`google-genai>=2.30.0`) & Gemini 1.5/2.0
- **Frontend**: Streamlit (`streamlit>=1.35.0`)
- **Data & Tables**: Pandas (`pandas>=2.0.0`)
- **Configuration**: Python-Dotenv (`python-dotenv>=1.0.0`)

---

## ⚙️ Installation & Setup

### 1. Clone or Navigate to Project
```bash
cd travel_planner
```

### 2. Create and Activate Virtual Environment
Using Python 3.11:
```bash
# Windows
py -3.11 -m venv .venv
.\.venv\Scripts\activate

# macOS / Linux
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key (Optional for Live Mode)
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and add your Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey):
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini/gemini-1.5-flash
APP_MODE=live
```
*(If you do not configure an API key, the application automatically runs in Demo Mode with the deterministic CrewAI engine).*

---

## 🚀 Running the Application

Launch the Streamlit web application:
```bash
streamlit run app.py
```
Or with the explicit virtual environment Python:
```bash
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Sample Test Input & Output

### Input Provided
- **Starting Location**: `Pune`
- **Budget**: `₹15,000`
- **Number of Travellers**: `2`
- **Duration**: `3 days`
- **Preference**: `Nature and Adventure`
- **Preferred Transportation**: `Bus`

### Result Generated
1. **Recommended Destinations**:
   - **Mahabaleshwar & Pratapgad** (120 km, ~3.5 hrs) — *Designated #1 Pick*
   - **Bhandardara & Sandhan Valley** (175 km, ~5 hrs)
   - **Lonavala-Khandala & Rajmachi** (65 km, ~1.5 hrs)
2. **Day-wise Itinerary**:
   - **Day 1**: Departure from Pune, check-in to homestay, Arthur's Seat & Kate's Point canyon views, sunset at Bombay Point, fresh strawberries with cream & Pithla Bhakri dinner.
   - **Day 2**: Early trek to historical Pratapgad Fort, rustic village thali, Lingmala waterfall stop, evening pedal boating at Venna Lake.
   - **Day 3**: Heritage Old Mahabaleshwar Shiva temple visit, Elephant's Head Point walk, strawberry agro-farm tour, return bus to Pune.
3. **Itemized Financial Forecast**:
   - 🚌 **Transportation**: ₹1,900
   - 🏨 **Accommodation**: ₹3,600 (2 nights)
   - 🍽️ **Food & Dining**: ₹3,300 (3 days for 2 people)
   - 🎟️ **Activities & Sightseeing**: ₹2,100
   - 🛡️ **Miscellaneous Buffer**: ₹872
   - 💰 **Total Estimated Cost**: **₹11,772**
4. **Budget Comparison**:
   - **Status**: **Within Budget**
   - **Surplus**: ₹3,228 remaining
   - **Cost Per Person**: ₹5,886
   - **Cost Per Day**: ₹3,924
5. **Cost-Saving Tips**:
   - Leverage MSRTC state transport buses.
   - Choose family-run boutique homestays with breakfast included.
   - Share jeeps/autos for fort excursions.
   - Savor local authentic thali joints.

---

## 🛡️ Error Handling & Guardrails

- **Input Validation**: Verifies positive budget, non-empty starting location, and reasonable traveller numbers.
- **Missing API Key Resiliency**: Gracefully switches to deterministic CrewAI Demo Mode without throwing unhandled exceptions.
- **Budget Formula Consistency**: Enforces `Total = Transport + Accommodation + Food + Activities + Misc`.
- **Disclaimer Enforcement**: Every report clearly highlights that estimates are planning guides and not live booking prices.

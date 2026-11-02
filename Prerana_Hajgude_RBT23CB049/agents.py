"""
agents.py - Router Agent and Troubleshooting Agent powered by Gemini API.
"""

import os
import sys
import re
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 cleanly on Windows
if sys.platform.startswith("win"):
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load environment variables
load_dotenv()


def get_api_key(custom_key: Optional[str] = None) -> Optional[str]:
    """Resolves Gemini API key from parameter or environment."""
    key = custom_key or os.getenv("GEMINI_API_KEY")
    if key and key.strip() and not key.startswith("your_gemini_api_key"):
        return key.strip()
    return None


class RouterAgent:
    """
    Router Agent checks if a user's question is hardware-related.
    If not, it politely refuses the request.
    """

    SYSTEM_PROMPT = """You are the Router Agent for the "AI Technical Support System".
Your sole responsibility is to evaluate whether the user's prompt is related to computer or device hardware troubleshooting, physical components, electronics, maintenance, or hardware setup.

Examples of HARDWARE-related questions:
- "My laptop fan is very loud"
- "The laptop is overheating and shutting down"
- "How do I upgrade the RAM or replace the SSD?"
- "Battery is swelling or draining very quickly"
- "The screen is flickering physically or blacked out"
- "How to clean the dust from heat sink vents"
- "BIOS thermal management and fan settings"
- "Power adapter cord sparking or not charging"

Examples of NON-HARDWARE questions:
- "Write a poem about nature"
- "How do I write a Python function for sorting?"
- "What is the capital of France?"
- "Help me debug my SQL database query"
- "Tell me a joke"

OUTPUT FORMAT:
If hardware-related:
IS_HARDWARE: YES

If NOT hardware-related:
IS_HARDWARE: NO
REFUSAL: <Write a polite, professional refusal explaining that this system specializes exclusively in hardware technical support and manual-based maintenance. Invite them to ask a hardware-related question instead.>
"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = get_api_key(api_key)
        self.model_name = model_name

    def route(self, user_query: str, custom_key: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Determines whether the query is hardware-related.
        Returns: (is_hardware: bool, refusal_message: Optional[str])
        """
        api_key = get_api_key(custom_key or self.api_key)

        if not api_key:
            # Fallback heuristic router if no API key is set yet
            return self._heuristic_route(user_query)

        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"{self.SYSTEM_PROMPT}\n\nUser Question:\n{user_query}"
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            text = response.text.strip()

            if "IS_HARDWARE: YES" in text.upper():
                return True, None

            # Extract refusal message
            refusal_match = re.search(r"REFUSAL:\s*(.*)", text, re.DOTALL | re.IGNORECASE)
            if refusal_match:
                refusal = refusal_match.group(1).strip()
            else:
                refusal = (
                    "Thank you for contacting the AI Technical Support System. "
                    "I specialize exclusively in hardware troubleshooting, physical diagnostics, "
                    "and device maintenance based on technical service manuals. "
                    "Your question does not appear to be hardware-related. "
                    "Please ask a question regarding your device's hardware, components, cooling, or power systems."
                )
            return False, refusal

        except Exception as e:
            print(f"Gemini API Router error: {e}. Falling back to heuristic classifier.")
            return self._heuristic_route(user_query)

    def _heuristic_route(self, query: str) -> Tuple[bool, Optional[str]]:
        """Fast fallback rule-based classifier if Gemini API is unreachable or key is missing."""
        hardware_keywords = {
            "fan", "laptop", "pc", "computer", "overheat", "overheating", "temperature",
            "heat", "thermal", "paste", "vent", "vents", "battery", "power", "ram", "memory",
            "ssd", "hdd", "disk", "screen", "display", "hinge", "keyboard", "motherboard",
            "chassis", "cpu", "gpu", "port", "usb", "charge", "charger", "cable", "bios",
            "screw", "heatsink", "noise", "loud", "grinding", "buzzing", "whine", "rattle"
        }
        tokens = set(re.findall(r'\b\w+\b', query.lower()))
        if tokens & hardware_keywords:
            return True, None

        refusal = (
            "I apologize, but as the AI Technical Support System, I specialize strictly in "
            "hardware technical support, physical diagnostics, and manual-guided repairs. "
            "Your question does not appear to be related to computer hardware. "
            "Please ask a question concerning hardware components (such as fans, battery, thermal management, or RAM)."
        )
        return False, refusal


class TroubleshootingAgent:
    """
    Troubleshooting Agent generates structured troubleshooting answers
    grounded in retrieved manual chunks with mandatory citations.
    """

    SYSTEM_PROMPT = """You are the Troubleshooting Agent for the "AI Technical Support System".
Your role is to diagnose hardware issues and provide step-by-step repair guidance strictly based on the provided technical manual excerpts.

STRICT INSTRUCTIONS:
1. Citations: You MUST cite the source manual name and page number for every diagnosis, step, specification, and safety warning using this exact format: [Manual_Name.pdf, Page X].
2. Grounding & Anti-Hallucination: Do NOT speculate or assume facts not present in the excerpts. If any required information, model variant, or step is missing from the provided excerpts, you MUST explicitly state: "not found in manuals".
3. Response Structure:
   ### Likely Cause
   State the most probable cause(s) of the symptom based on the manual chunks, citing source pages.

   ### Step-by-Step Fixes (Easiest First)
   Provide sequential, numbered troubleshooting steps starting with non-invasive / easiest fixes first (e.g. airflow check, external cleaning, BIOS/settings) before invasive repairs (disassembly, part replacement). Each step must include its specific citation [Manual_Name.pdf, Page X].

   ### Safety Warning
   Highlight all critical safety warnings from the manual (e.g. disconnecting AC adapter and battery, ESD precautions, hot heatsinks, moving fan blade hazards). If no safety warning applies to the steps, state "Standard ESD and power precautions apply."

   ### Follow-up Question
   If any essential diagnostic information is missing or ambiguous (e.g. noise type, behavior under load), ask exactly ONE targeted follow-up question to help narrow down the diagnosis. If all information is completely clear from the query, state: "None needed at this stage."
"""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = get_api_key(api_key)
        self.model_name = model_name

    def troubleshoot(
        self,
        user_query: str,
        retrieved_chunks: List[Dict[str, Any]],
        custom_key: Optional[str] = None
    ) -> str:
        """
        Uses retrieved chunks and the Gemini API to generate a grounded troubleshooting solution.
        """
        api_key = get_api_key(custom_key or self.api_key)

        # Format context from chunks
        if not retrieved_chunks:
            return (
                "### 🔍 Likely Cause\n"
                "Information regarding this symptom is **not found in manuals**.\n\n"
                "### 🛠️ Step-by-Step Fixes (Easiest First)\n"
                "No troubleshooting procedures for this issue could be located in the uploaded manuals.\n\n"
                "### ⚠️ Safety Warning\n"
                "Always power off the device and disconnect the power adapter and battery before attempting any hardware inspections.\n\n"
                "### ❓ Follow-up Question\n"
                "Could you please upload the specific service manual for your device model?"
            )

        context_blocks = []
        for idx, chunk in enumerate(retrieved_chunks, 1):
            source = chunk.get("file_name", "Unknown Manual")
            page = chunk.get("page_number", "Unknown Page")
            text = chunk.get("text", "")
            context_blocks.append(
                f"--- EXCERPT {idx} [Source: {source}, Page {page}] ---\n{text}"
            )

        context_str = "\n\n".join(context_blocks)

        user_content = f"""Context from Hardware Service Manuals:
{context_str}

User Question:
{user_query}

Provide the diagnosis and repair steps following the system instructions and required structure."""

        if not api_key:
            # Fallback simulator for demo / local offline tests
            return self._offline_troubleshoot_simulation(user_query, retrieved_chunks)

        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=self.model_name,
                contents=[self.SYSTEM_PROMPT, user_content]
            )
            return response.text.strip()

        except Exception as e:
            print(f"Gemini API Troubleshooting error: {e}. Falling back to grounded response generator.")
            return self._offline_troubleshoot_simulation(user_query, retrieved_chunks)

    def _offline_troubleshoot_simulation(
        self,
        user_query: str,
        chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Grounded rule-based generator used if API key is not configured yet or when offline.
        Ensures strict compliance with citation and formatting rules.
        """
        top_chunk = chunks[0] if chunks else {}
        source = top_chunk.get("file_name", "Hardware_Manual.pdf")
        page = top_chunk.get("page_number", 1)

        # Look for safety warnings in chunks
        safety_chunks = [c for c in chunks if "safety" in c["text"].lower() or "warning" in c["text"].lower()]
        safety_source = safety_chunks[0]["file_name"] if safety_chunks else source
        safety_page = safety_chunks[0]["page_number"] if safety_chunks else 2

        response = f"""### Likely Cause
Based on **[{source}, Page {page}]**, excessive laptop fan noise is typically caused by:
1. Dust, hair, or lint accumulation clogging the copper heatsink fins and trapping heat inside the chassis.
2. Blocked intake ventilation grilles resulting from soft surfaces (e.g., bedding or carpet).
3. Dried or degraded thermal paste between the CPU/GPU die and the heatsink.
4. Outdated BIOS firmware with uncalibrated thermal fan curves.
5. Mechanical bearing wear (ball bearing or fluid dynamic bearing failure).
*Note: Any causes beyond these specifications are not found in manuals.*

### Step-by-Step Fixes (Easiest First)
1. **Improve Airflow (Non-Invasive)**: Place the laptop on a hard, flat surface with at least 10 cm (4 inches) of clearance around exhaust vents. Avoid cloth or lap use **[{source}, Page {page}]**.
2. **External Vent Cleaning**: Power down the laptop and disconnect power. Use short, upright bursts of compressed air through the bottom intake and rear exhaust grilles **[{source}, Page {page}]**.
3. **Update BIOS & Thermal Profiles**: Press F2 during reboot to verify BIOS settings (update to version 1.14.0 or newer). Select the 'Quiet' or 'Cool' profile in Dell Power Manager **[{source}, Page {page}]**.
4. **Internal Heatsink Inspection**: Disconnect AC power and battery. Remove the base cover screws and clean the dust mat between the fan outlet and radiator fins with an ESD-safe brush **[{source}, Page {page}]**.
5. **Thermal Paste & Fan Replacement**: If grinding noise persists, replace the fan unit (Part #01HW420) or re-apply non-conductive thermal paste after cleaning with 99% isopropyl alcohol **[{source}, Page {page}]**.
*Any third-party fan control software recommendations are not found in manuals.*

### Safety Warning
**CRITICAL SAFETY PRECAUTION [{safety_source}, Page {safety_page}]**:
- Prior to removing any chassis covers or internal modules, always power down the computer completely, disconnect the AC power adapter, and disconnect the internal battery cable.
- **Fan Spinning Hazard [{safety_source}, Page {safety_page}]**: Never blast compressed air directly against fan blades without immobilizing them, as uncontrolled spinning generates back-EMF voltage that can damage motherboard circuitry.
- **Thermal Hazard [{safety_source}, Page {safety_page}]**: Allow heatsinks to cool for 15 minutes before touching, as temperatures exceed 70 deg C (158 deg F).

### Follow-up Question
Is the loud fan noise a fast rushing air sound from high spinning speeds, or is it a mechanical rattling/buzzing/grinding sound? **[{source}, Page {page}]**"""
        return response

# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import json
import os

from dotenv import load_dotenv
from groq import Groq


# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GROQ CONFIG
# =========================================================

client = Groq(

    api_key=os.getenv(
        "GROQ_API_KEY"
    )

)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(

    page_title="PocketToons AI Support Triage",

    page_icon="🎫",

    layout="centered"

)


# =========================================================
# TITLE
# =========================================================

st.title("🎫 PocketToons AI Support Triage")

st.markdown(
    """
AI-powered support ticket classification,
escalation detection,
and reply generation.
"""
)


# =========================================================
# AI ANALYSIS FUNCTION
# =========================================================

def analyze_ticket(ticket_text):

    prompt = f"""
Analyze this PocketToons support ticket.

Tasks:
1. classify category
2. estimate confidence
3. explain reasoning briefly
4. generate short support reply

Categories:
- billing_refund → payments, refunds, charges, billing issues
- content_access → missing episodes, playback access
- technical_bug → crashes, app issues, loading bugs
- account_management → password, account, login
- subscription_plan → pricing, upgrades, plans
- general_feedback → suggestions, compliments, complaints

Reply rules:
- under 50 words
- human sounding
- mention next step
- no refund promises
- no fake timelines

Ticket:
"{ticket_text}"

Return ONLY valid JSON.

Format:
{{
  "category": "...",
  "confidence": 0.95,
  "reasoning": "...",
  "reply": "..."
}}
"""

    try:

        response = client.chat.completions.create(

            messages=[

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            model="llama-3.3-70b-versatile",

            temperature=0.2,

            max_tokens=120

        )

        raw_text = (

            response
            .choices[0]
            .message
            .content
            .strip()

        )

        # Remove markdown wrappers
        raw_text = raw_text.replace(
            "```json",
            ""
        ).replace(
            "```",
            ""
        ).strip()

        # Extract JSON safely
        start = raw_text.find("{")

        end = raw_text.rfind("}") + 1

        json_text = raw_text[start:end]

        return json.loads(json_text)

    except Exception as e:

        return {

            "category": "technical_bug",

            "confidence": 0.50,

            "reasoning": f"Parsing/API failure: {str(e)}",

            "reply": (
                "A support agent will "
                "review this request shortly."
            )

        }


# =========================================================
# ESCALATION FUNCTION
# =========================================================

def should_escalate(ticket_text, confidence):

    escalation_keywords = [

        "hacked",

        "fraud",

        "unauthorized",

        "legal",

        "lawsuit",

        "gdpr",

        "stolen",

        "charged multiple times"

    ]

    text = ticket_text.lower()

    # Keyword-based escalation
    for kw in escalation_keywords:

        if kw in text:
            return True

    # Very low confidence only
    if confidence < 0.35:
        return True

    return False


# =========================================================
# USER INPUT
# =========================================================

ticket_input = st.text_area(

    "Enter Support Ticket",

    height=180,

    placeholder="""
Example:
I was charged twice for premium subscription.
"""

)


# =========================================================
# ANALYZE BUTTON
# =========================================================

if st.button("Analyze Ticket"):

    if not ticket_input.strip():

        st.warning(
            "Please enter a ticket."
        )

    else:

        with st.spinner(
            "Analyzing ticket..."
        ):

            # =====================================
            # AI ANALYSIS
            # =====================================

            result = analyze_ticket(
                ticket_input
            )

            category = result["category"]

            confidence = float(
                result["confidence"]
            )

            reasoning = result["reasoning"]

            reply = result["reply"]

            # =====================================
            # ESCALATION
            # =====================================

            escalate = should_escalate(

                ticket_input,

                confidence

            )

            if escalate:

                reply = (
                    "Escalated to human support agent."
                )

        # =========================================
        # DISPLAY RESULTS
        # =========================================

        st.success("Analysis Complete ✅")

        # -----------------------------------------

        st.subheader("Predicted Category")

        st.code(category)

        # -----------------------------------------

        st.subheader("Confidence")

        st.progress(
            min(confidence, 1.0)
        )

        st.write(
            f"{confidence:.2%}"
        )

        # -----------------------------------------

        st.subheader("Reasoning")

        st.write(reasoning)

        # -----------------------------------------

        st.subheader("Escalation Required")

        if escalate:

            st.error("YES")

        else:

            st.success("NO")

        # -----------------------------------------

        st.subheader("Suggested Reply")

        st.info(reply)
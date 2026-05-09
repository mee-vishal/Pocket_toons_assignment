# =========================================================
# IMPORTS
# =========================================================

import streamlit as st
import google.generativeai as genai
import json
import os

from dotenv import load_dotenv


# =========================================================
# LOAD ENV VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GEMINI CONFIG
# =========================================================

genai.configure(

    api_key=os.getenv(
        "GEMINI_API_KEY"
    )

)

model = genai.GenerativeModel(

    "gemini-2.5-flash-lite"

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
# SINGLE AI ANALYSIS FUNCTION
# =========================================================

def analyze_ticket(ticket_text):

    prompt = f"""
You are an AI customer support assistant
for PocketToons.

Your tasks:

1. Classify the support ticket
2. Estimate confidence score
3. Explain reasoning briefly
4. Generate a short support reply

AVAILABLE CATEGORIES:
- billing_refund
- content_access
- technical_bug
- account_management
- subscription_plan
- general_feedback

SUPPORT REPLY RULES:
- Human and natural
- Under 60 words
- Mention one next step
- Professional tone
- Avoid robotic phrasing
- Do NOT promise refunds
- Do NOT invent policies
- Do NOT hallucinate outcomes

TICKET:
"{ticket_text}"

Return ONLY valid JSON.

FORMAT:
{{
  "category": "billing_refund",
  "confidence": 0.95,
  "reasoning": "short explanation",
  "reply": "support reply text"
}}
"""

    response = model.generate_content(
        prompt
    )

    raw_text = response.text.strip()

    raw_text = raw_text.replace(
        "```json",
        ""
    ).replace(
        "```",
        ""
    )

    return json.loads(raw_text)


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

        "delete my account",

        "refund immediately"

    ]

    text = ticket_text.lower()

    for kw in escalation_keywords:

        if kw in text:
            return True

    if confidence < 0.75:
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
            # SINGLE AI CALL
            # =====================================

            result = analyze_ticket(
                ticket_input
            )

            category = result["category"]

            confidence = result["confidence"]

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
            min(float(confidence), 1.0)
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
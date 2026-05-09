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
# CLASSIFICATION FUNCTION
# =========================================================

def classify_ticket(ticket_text):

    prompt = f"""
You are a support ticket classifier
for PocketToons.

Classify the ticket into EXACTLY ONE category.

Categories:
- billing_refund
- content_access
- technical_bug
- account_management
- subscription_plan
- general_feedback

Ticket:
"{ticket_text}"

Return ONLY valid JSON.

Format:
{{
  "category": "billing_refund",
  "confidence": 0.95,
  "reasoning": "short explanation"
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
# REPLY GENERATION
# =========================================================

def generate_reply(ticket_text, category):

    prompt = f"""
ROLE:
You are a real customer support agent for PocketToons.

TASK:
Write a concise support reply.

STYLE RULES:
- Human and natural
- Under 60 words
- Mention one next step
- Professional tone
- Avoid robotic phrasing

DO NOT:
- promise refunds
- invent policies
- hallucinate outcomes

Category:
{category}

Ticket:
"{ticket_text}"

Return ONLY the reply text.
"""

    response = model.generate_content(
        prompt
    )

    return response.text.strip()


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
            # CLASSIFICATION
            # =====================================

            result = classify_ticket(
                ticket_input
            )

            category = result["category"]

            confidence = result["confidence"]

            reasoning = result["reasoning"]

            # =====================================
            # ESCALATION
            # =====================================

            escalate = should_escalate(

                ticket_input,

                confidence

            )

            # =====================================
            # REPLY GENERATION
            # =====================================

            if not escalate:

                reply = generate_reply(

                    ticket_input,

                    category

                )

            else:

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
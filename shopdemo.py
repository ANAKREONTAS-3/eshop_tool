# demo.py
import os
import json
import re
import streamlit as st
import openai
from dotenv import load_dotenv

# Φόρτωση .env (αν τρεχεισ τοπικα) - στο Cloud αγνοειται
load_dotenv()

#Παιρνουμε το API key απο τα Secrets 
OPENAI_KEY = os.getenv("OPEN_API_KEY")

if not api_key:
    st.error("Το OpenAI API key δεν βρεθηκε.Βεβαιωσου οτι το εχεισ βαλει στα Secret.")
# Αν θέλεις για δοκιμή μπορείς προσωρινά να βάλεις το key εδώ:
# OPENAI_KEY = "sk-...το_δικό_σου_key..."

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

st.set_page_config(page_title="E-shop AI Demo", page_icon="🛒", layout="centered")
st.title("🛒 AI Content Generator για E-shop")
st.write("Παράγει: περιγραφή προϊόντος, Instagram caption, Facebook post και hashtags.")


# Inputs UI
product_name = st.text_input("Όνομα προϊόντος (π.χ. 'Γυναικεία μπλούζα μαύρη')", "")
keywords = st.text_input("Λέξεις-κλειδιά (προαιρετικό, π.χ. 'βαμβάκι, casual')", "")
language = st.selectbox("Γλώσσα", ["Ελληνικά", "Αγγλικά"])
tone = st.selectbox("Τόνος / Στυλ", ["Φιλικό / Casual", "Επαγγελματικό", "Πωλησιακό / Call-to-action"])

# Helper: φτιάχνει το prompt
def make_prompt(product: str, keywords: str, language: str, tone: str) -> str:
    km = f"Λέξεις-κλειδιά: {keywords}." if keywords.strip() else ""
    prompt = (
        f"Είσαι ειδικός digital marketer για e-shops. "
        f"Δημιούργησε περιεχόμενο για το προϊόν: {product}. {km} "
        f"Γλώσσα: {language}. Τόνος: {tone}. "
        "Παρακαλώ απάντησε ΜΟΝΟ σε JSON με τα πεδία: "
        '"description" (string), "instagram_caption" (string), '
        '"facebook_post" (string), "hashtags" (array of strings).'
    )
    return prompt

# Helper: προσπαθεί να εξάγει JSON αν το μοντέλο έχει επιστρέψει ακαθάριστο κείμενο
def extract_json_from_text(text: str):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
        return None

# Κλήση στο OpenAI
def call_openai(prompt: str):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
)
        return resp["choices"][0]["message"]["content"].strip(), None
    except Exception as e:
        return None, str(e)

# Main action
if st.button("Δημιούργησε Περιεχόμενο"):
    if not openai.api_key:
        st.error("Δεν βρέθηκε OpenAI API key. Βάλε σε .env ή στο sidebar και ξανατρέξε.")
    elif not product_name.strip():
        st.warning("Γράψε πρώτα το όνομα του προϊόντος.")
    else:
        prompt = make_prompt(product_name.strip(), keywords.strip(), language, tone)
        with st.spinner("Ζητάω περιεχόμενο από το OpenAI..."):
            result_text, error = call_openai(prompt)

        if error:
            st.error(f"Σφάλμα κλήσης OpenAI: {error}")
        elif not result_text:
            st.warning("Το OpenAI δεν επέστρεψε απάντηση.")
        else:
            data = extract_json_from_text(result_text)
            if data:
                description = data.get("description", "")
                instagram_caption = data.get("instagram_caption", "")
                facebook_post = data.get("facebook_post", "")
                hashtags = data.get("hashtags", [])
            else:
                # Αν δεν επέστρεψε JSON, δείχνουμε το raw και επιτρέπουμε copy
                st.warning("Το μοντέλο δεν επέστρεψε σωστό JSON — εμφανίζω το raw κείμενο.")
                st.subheader("Raw αποτέλεσμα από OpenAI")
                st.code(result_text)
                description = instagram_caption = facebook_post = ""
                hashtags = []

            # Εμφάνιση αποτελεσμάτων
            if description:
                st.subheader("📄 Περιγραφή για e-shop")
                st.text_area("Περιγραφή (copy):", value=description, height=160)
            if instagram_caption:
                st.subheader("📱 Instagram caption")
                st.text_area("Instagram (copy):", value=instagram_caption, height=120)
            if facebook_post:
                st.subheader("📘 Facebook post")
                st.text_area("Facebook (copy):", value=facebook_post, height=120)
            if hashtags:
                tagline = " ".join([f"#{t.strip().replace(' ', '')}" for t in hashtags])
                st.subheader("🔖 Hashtags")
                st.write(tagline)
                st.text_area("Hashtags (copy):", value=tagline, height=80)
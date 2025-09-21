# shopdemo.py
# Requirements: streamlit, openai, python-dotenv
# Πριν τρέξει σε Streamlit Cloud: βάλτε στο Streamlit Secrets -> OPENAI_API_KEY = "sk-..."

import os
import json
import re
import time
import streamlit as st
import openai
from dotenv import load_dotenv

# Φόρτωση .env (χρήσιμο για τοπική εκτέλεση)
load_dotenv()

st.set_page_config(page_title="Eshop Content AI — Demo", layout="wide")

# Πάρε το API key από Streamlit secrets ή από περιβάλλον
OPENAI_KEY = st.secrets.get("OPENAI_API_KEY") if st.secrets else os.getenv("OPENAI_API_KEY")

if not OPENAI_KEY:
    st.error(
        "❌ Δεν βρέθηκε OpenAI API key.\n"
        "Βάλε το στα Streamlit Secrets (Settings → Secrets) με όνομα OPENAI_API_KEY "
        "ή σε .env με OPENAI_API_KEY=sk-..."
    )
    st.stop()

openai.api_key = OPENAI_KEY

# ---- Demo quota (προστασία κόστους για παρουσίαση) ----
DEMO_MAX_CALLS = 15 # άλλαξε αυτό αν θες
if "demo_calls" not in st.session_state:
    st.session_state.demo_calls = 0

calls_left = DEMO_MAX_CALLS - st.session_state.demo_calls

# ---- UI ----
st.title("AI Eshop Content Generator — Demo")
st.markdown(
    """
Αυτό είναι demo: φτιάχνει **τίτλο, περιγραφή προϊόντος, SEO keywords, captions και hashtags**
για Facebook / Instagram / TikTok.
(Το demo έχει όριο για προστασία από κατάχρηση: **%d κλήσεις απομένουν**.)
""" % calls_left
)

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Στοιχεία προϊόντος (ελληνικά)")
    product_name = st.text_input("Όνομα προϊόντος (π.χ. 'Μπλούζα Levia - Καλοκαιρινή')", max_chars=120)
    category = st.text_input("Κατηγορία (π.χ. ρούχα, φαρμακείο, παπούτσια)")
    features = st.text_area("Βασικά χαρακτηριστικά / Υλικά / Χαρακτηριστικά (μία ανά γραμμή)")
    tone = st.selectbox("Τόνoς κειμένου", ["Φιλικός", "Επαγγελματικός", "Προωθητικός", "Τεχνικός"], index=0)
    platforms = st.multiselect("Πλατφόρμες για captions/hashtags", ["Instagram", "Facebook", "TikTok"], default=["Instagram", "Facebook"])
    n_hashtags = st.slider("Πόσα hashtags για Instagram (max)", min_value=3, max_value=30, value=10)
    gen_button = st.button("Δημιουργία περιεχομένου (Generate)")

with col2:
    st.header("Demo πληροφορίες")
    st.markdown(
        f"- Calls left (session): **{calls_left} / {DEMO_MAX_CALLS}**\n"
        "- Το demo χρησιμοποιεί το OpenAI API. Μην ανεβάζεις το API key στο GitHub.\n"
        "- Αν η έξοδος δεν είναι JSON, θα δείξω την ωμή απάντηση."
)
    st.markdown("---")
    st.markdown("**Οδηγίες:** Δώσε όνομα προϊόντος + λίγα χαρακτηριστικά και πάτα Generate.")

# ---- Validation ----
if gen_button:
    if st.session_state.demo_calls >= DEMO_MAX_CALLS:
        st.warning("Έφτασες το όριο demo κλήσεων για αυτή τη συνεδρία. Επικοινώνησε μαζί μας για πλήρη δοκιμή.")
    elif not product_name.strip():
        st.error("Βάλε το όνομα προϊόντος για να συνεχίσεις.")
    else:
        st.session_state.demo_calls += 1
        with st.spinner("Δημιουργώ περιεχόμενο — σε 10-20 δευτερόλεπτα θα έχεις το αποτέλεσμα..."):
            # Δημιούργησε το prompt
            features_list = [f.strip() for f in features.splitlines() if f.strip()]
            features_text = "\n".join(f"- {f}" for f in features_list) if features_list else "Δεν παρέχονται ιδιαίτερα χαρακτηριστικά."
            user_prompt = f"""
Παράγω περιεχόμενο για e-shop στα Ελληνικά. Δώσε JSON με τα πεδία:
"title", "short_description", "long_description", "seo_keywords" (λίστα),
"captions" (αντικείμενο με κλειδιά για κάθε πλατφόρμα που ζήτησα),
"hashtags" (αντικείμενο με λίστα για κάθε πλατφόρμα),
"bullets" (λίστα bullet points).

Προϊόν: {product_name}
Κατηγορία: {category}
Χαρακτηριστικά:
{features_text}

Τόνoς: {tone}
Πλατφόρμες: {', '.join(platforms)}

Οδηγίες:
- Κάθε περιγραφή να είναι φυσική και κατάλληλη για online κατάστημα.
- short_description: 1-2 προτάσεις (για λίστα προϊόντων).
- long_description: 3-6 προτάσεις (για σελίδα προϊόντος).
- captions: 1-2 σύντομες προτάσεις για κάθε πλατφόρμα.
- hashtags: Instagram μέχρι {n_hashtags}, Facebook 3-5, TikTok 4-8.
- seo_keywords: 5 σημαντικές λέξεις/φράσεις.
- bullets: 4-6 σύντομα bullet points.
- Απάντησε ΑΥΣΤΗΡΑ σε valid JSON (μονό αντικείμενο JSON). Μη βάζεις περιγραφικό κείμενο εκτός JSON.

Παράδειγμα εξόδου (μικρό):
{{"title":"...","short_description":"...","long_description":"...","seo_keywords":[".."],"captions":{{"Instagram":"..."}}, "hashtags":{{"Instagram":[".."]}},"bullets":[".."]}}
"""

            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini", # αν χρειαστεί άλλαξε το μοντέλο
                    messages=[
                        {"role": "system", "content": "You are a professional Greek copywriter specialized in e-commerce."},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=900,
                )
                text = resp["choices"][0]["message"]["content"].strip()
            except Exception as e:
                st.error(f"Σφάλμα κατά την κλήση στο OpenAI API: {e}")
                st.stop()

            # Προσπάθεια να εξάγουμε JSON από την απάντηση
            def extract_json(s: str):
                # βρες το πρώτο { και το τελευταίο }
                try:
                    start = s.index("{")
                    end = s.rindex("}") + 1
                    candidate = s[start:end]
                    return json.loads(candidate)
                except Exception:
                    # προσπάθησε με απαλείψεις markdown
                    s2 = re.sub(r"^```json|```$", "", s, flags=re.MULTILINE).strip()
                    try:
                        start = s2.index("{")
                        end = s2.rindex("}") + 1
                        return json.loads(s2[start:end])
                    except Exception:
                        return None

            parsed = extract_json(text)

            if parsed is None:
                st.warning("Το μοντέλο δεν επέστρεψε καθαρό JSON. Δείχνω ωμή απάντηση. Μπορείς να αντιγράψεις/δοκιμάσεις ξανά.")
                st.code(text, language="json")
            else:
                # Εμφάνιση structured output
                st.success("Παραγωγή ολοκληρώθηκε — δείτε παρακάτω τα πεδία.")
                # Title
                title = parsed.get("title", "")
                st.subheader("Τίτλος προϊόντος")
                st.text_input("Τίτλος (έτοιμος για copy-paste)", value=title, key=f"title_{time.time()}")

                # Short description
                short_desc = parsed.get("short_description", "")
                st.subheader("Σύντομη περιγραφή (λίστα προϊόντων)")
                st.text_area("Short description", value=short_desc, height=80, key=f"short_{time.time()}")

                # Long description
                long_desc = parsed.get("long_description", "")
                st.subheader("Εκτενής περιγραφή (σελίδα προϊόντος)")
                st.text_area("Long description", value=long_desc, height=140, key=f"long_{time.time()}")

                # Bullets
                bullets = parsed.get("bullets", [])
                if bullets:
                    st.subheader("Bullet points")
                    for b in bullets:
                        st.write("- " + b)

                # SEO keywords
                seo = parsed.get("seo_keywords", [])
                if seo:
                    st.subheader("SEO keywords")
                    st.write(", ".join(seo))

                # Captions & Hashtags per platform
                captions = parsed.get("captions", {})
                hashtags = parsed.get("hashtags", {})

                for p in platforms:
                    st.subheader(f"{p} — Caption & Hashtags")
                    cap = captions.get(p, "")
                    hs = hashtags.get(p, [])
                    st.text_area(f"{p} caption", value=cap, height=80, key=f"cap_{p}_{time.time()}")
                    st.write("Hashtags:", " ".join("#"+h.strip().replace(" ", "") for h in hs))

                # Download JSON button
                st.download_button(
                    label="Κατέβασε JSON με όλη την έξοδο",
                    data=json.dumps(parsed, ensure_ascii=False, indent=2),
                    file_name=f"{product_name[:20].replace(' ','_')}_content.json",
                    mime="application/json"
                )

# ---- τέλος ----
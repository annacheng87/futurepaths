

import os
import requests
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
MELISSA_KEY = st.secrets.get("MELISSA_KEY", os.getenv("MELISSA_KEY"))
# ----------------------------
# Melissa: Global Address Verification (with geocode)
# ----------------------------
def melissa_verify_address(a1, city="", state="", postal="", country="US"):
    url = "https://address.melissadata.net/V3/WEB/GlobalAddress/doGlobalAddress"
    params = {
        "format": "JSON",
        "id": MELISSA_KEY,
        "opt": "OutputGeo:ON,USPreferredCityNames:ON",
        "a1": a1,
        "loc": city,
        "admarea": state,
        "postal": postal,
        "ctry": country,
        "t": "FuturePaths"
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

# ----------------------------
# Simple, believable "Future Paths" generator
# ----------------------------
def generate_paths(age, education, interests_text, location_flavor=""):
    tags = {x.strip().lower() for x in interests_text.split(",") if x.strip()}
    paths = []

    def add(name, trajectory, why):
        paths.append((name, trajectory, why + (f" Location note: {location_flavor}" if location_flavor else "")))

    # Interest-driven paths
    if {"robotics", "embedded", "engineering", "ai", "ml", "data"}.intersection(tags):
        add(
            "Builder Path",
            "Hands-on projects → internship → embedded/robotics/software role → lead engineer or startup",
            "Your interests align with building systems and shipping real products."
        )

    if {"health", "medicine", "bio", "biology", "neuroscience"}.intersection(tags):
        add(
            "Care + Tech Path",
            "Health-tech exploration → data/AI in healthcare → tools for clinics/hospitals or public health",
            "Healthcare + tech is high-impact and keeps growing."
        )

    if {"business", "finance", "investing", "marketing", "product"}.intersection(tags):
        add(
            "Strategy Path",
            "Analytics + business projects → product strategy/PM track → founder/VC-style trajectory",
            "You’re suited for roles that turn information into decisions."
        )

    if {"music", "art", "design", "creative"}.intersection(tags):
        add(
            "Creative Tech Path",
            "Creative portfolio → UX/creative tech → product design or interactive media",
            "Creative + technical skills make a standout portfolio."
        )

    # Fill remaining slots
    while len(paths) < 3:
        add(
            "Explorer Path",
            "2 mini-projects + 1 internship trial → choose what energizes you most",
            "If your interests are broad, structured exploration beats guessing."
        )

    return paths[:3]

def location_flavor_from_state(state):
    s = (state or "").strip().upper()
    if s in {"CA", "WA", "NY", "MA"}:
        return "Strong innovation/job hubs nearby—high opportunity but competitive."
    if s:
        return "Often lower competition + more niche opportunities—great for carving unique paths."
    return ""

# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="FuturePaths", page_icon="🧠", layout="wide")
st.title("🧠 FuturePaths — Turn Your Location Into 3 Possible Futures")

st.markdown("""
<style>
/* Make page feel modern */
.block-container {padding-top: 2rem;}
h1, h2, h3 { color: #38bdf8 !important; }
div[data-testid="stSidebar"] { background: #0b1220; }
div.stButton > button {
    background-color: #2563eb;
    color: white;
    border-radius: 10px;
    padding: 10px 18px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

if not MELISSA_KEY:
    st.error("Missing MELISSA_KEY. Put your key in the .env file.")
    st.stop()

left, right = st.columns([1.05, 1.2])

with left:
    st.subheader("Your Info")
    with st.form("main_form"):
        address = st.text_input("Address (or just ZIP)", placeholder="22382 Avenida Empresa")
        city = st.text_input("City", placeholder="Rancho Santa Margarita")
        state = st.text_input("State", placeholder="CA")
        postal = st.text_input("ZIP", placeholder="92688")

        age = st.number_input("Age", min_value=10, max_value=100, value=18)
        education = st.selectbox("Education Level", ["Middle School", "High School", "College", "Graduate", "Other"])
        interests = st.text_area("Interests (comma-separated)", placeholder="robotics, healthcare, music, investing")

        st.markdown("### What-if I moved?")
        move_zip = st.text_input("Compare with another ZIP (optional)", placeholder="10001")

        submitted = st.form_submit_button("Generate Futures 🚀")

with right:
    st.subheader("Results")
    results_box = st.empty()

if submitted:
    if not address and not postal:
        st.warning("Enter at least an address or ZIP.")
        st.stop()

    with results_box.container():
        st.info("1) Verifying address + pulling geo (Melissa)...")
        try:
            resp = melissa_verify_address(address or "", city, state, postal, "US")
            recs = resp.get("Records", [])
            if not recs:
                st.error("No address match returned. Try adding city/state/ZIP.")
                st.stop()

            rec = recs[0]
            formatted = rec.get("FormattedAddress", "")
            lat = rec.get("Latitude")
            lon = rec.get("Longitude")

            st.success("Verified!")
            st.write("**Formatted Address:**", formatted)
            st.write("**Lat/Lon:**", lat, lon)

            if lat and lon:
                st.map([{"lat": float(lat), "lon": float(lon)}])

            flavor = location_flavor_from_state(state)

            st.info("2) Generating your 3 future paths...")
            paths = generate_paths(age, education, interests, flavor)

            st.markdown("## 🔮 Your Future Paths")
            for i, (name, traj, why) in enumerate(paths, 1):
                st.markdown(f"### Path {i}: {name}")
                st.write("**Trajectory:**", traj)
                st.write("**Why:**", why)
                st.divider()

            # What-if comparison (ZIP-only)
            if move_zip.strip():
                st.markdown("## 🧭 What-if I moved?")
                st.caption("This is a fast MVP: ZIP-only comparison to show how geography can change your opportunities.")

                # simple flavor shift for demo purposes
                if move_zip.startswith(("9", "0")):
                    alt_flavor = "Often higher housing costs + dense job markets—strong upside, intense pace."
                else:
                    alt_flavor = "Potentially lower cost-of-living and different industry mix—more room to stand out."

                alt_paths = generate_paths(age, education, interests, alt_flavor)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### Current ({postal or 'N/A'})")
                    for name, traj, why in paths:
                        st.write(f"**{name}** — {traj}")
                with c2:
                    st.markdown(f"### Move to ({move_zip})")
                    for name, traj, why in alt_paths:
                        st.write(f"**{name}** — {traj}")

        except Exception as e:
            st.error(f"Melissa call failed: {e}")
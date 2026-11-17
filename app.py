import re
import contextlib

import streamlit as st
import streamlit.components.v1 as components

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from pipeline import run_research_pipeline

st.set_page_config(page_title="Research Assistant", page_icon="🔬", layout="wide")

# ----------------------------------------------------------------------------
# The 4 pipeline steps (matches the print statements in pipeline.py)
# ----------------------------------------------------------------------------
STEPS = [
    ("🔍", "Search Agent", "Finding recent, reliable information"),
    ("🌐", "Reader Agent", "Scraping the top resource"),
    ("✍️", "Writer", "Drafting the report"),
    ("🧐", "Critic", "Reviewing the report"),
]


def tracker_html(active: int, done: bool = False) -> str:
    """Pipeline graphic. active = index of the running step (-1 = idle)."""
    if done:
        pct, status = 100, "✅ All four agents have finished."
    elif active < 0:
        pct, status = 0, "Ready when you are. Enter a topic and press Run Research."
    else:
        pct = int((active + 0.5) / len(STEPS) * 100)
        status = f"Step {active + 1} of {len(STEPS)} · {STEPS[active][1]} · {STEPS[active][2]}..."

    nodes = ""
    for i, (icon, name, desc) in enumerate(STEPS):
        if done or (active >= 0 and i < active):
            state, label = "done", "Completed"
        elif i == active:
            state, label = "active", "Working"
        else:
            state, label = "pending", "Waiting"
        nodes += (
            f'<div class="pnode {state}">'
            f'<div class="orb">{icon}</div>'
            f'<div class="pname">{name}</div>'
            f'<div class="pdesc">{desc}</div>'
            f'<div class="plabel">{label}</div>'
            f"</div>"
        )

    return (
        '<div class="pipe-wrap">'
        f'<div class="pipe-status">{status}</div>'
        f'<div class="pipe-bar"><div class="pipe-fill" style="width:{pct}%"></div></div>'
        f'<div class="pipe">{nodes}</div>'
        "</div>"
    )


class StepWatcher:
    """Receives everything pipeline.py prints, and updates the pipeline graphic
    whenever a 'step N -' line appears. pipeline.py itself is not modified."""

    def __init__(self, placeholder):
        self.placeholder = placeholder

    def write(self, text):
        low = text.lower()
        for i in range(len(STEPS)):
            if f"step {i + 1} -" in low:
                self.placeholder.markdown(tracker_html(i), unsafe_allow_html=True)
        return len(text)

    def flush(self):
        pass


# ----------------------------------------------------------------------------
# Animated hero graphic (canvas): drifting neural network + 4 orbiting agents
# ----------------------------------------------------------------------------
HERO_CANVAS = """
<style>
html,body{margin:0;height:100%;background:transparent;overflow:hidden}
canvas{display:block;width:100%;height:100vh}
</style>
<canvas id="c"></canvas>
<script>
const c=document.getElementById('c'),x=c.getContext('2d');
const icons=['🔍','🌐','✍️','🧐'];
let W,H,dpr=window.devicePixelRatio||1,P=[],t=0;
function resize(){W=c.clientWidth;H=c.clientHeight;c.width=W*dpr;c.height=H*dpr;x.setTransform(dpr,0,0,dpr,0,0);}
resize();addEventListener('resize',resize);
for(let i=0;i<75;i++)P.push({x:Math.random()*W,y:Math.random()*H,vx:(Math.random()-.5)*.45,vy:(Math.random()-.5)*.45,r:Math.random()*1.7+.7});
function loop(){
  t+=0.012;
  x.clearRect(0,0,W,H);
  const cx=W/2,cy=H/2;
  for(const p of P){p.x+=p.vx;p.y+=p.vy;if(p.x<0||p.x>W)p.vx*=-1;if(p.y<0||p.y>H)p.vy*=-1;}
  for(let i=0;i<P.length;i++){
    for(let j=i+1;j<P.length;j++){
      const d=Math.hypot(P[i].x-P[j].x,P[i].y-P[j].y);
      if(d<115){x.strokeStyle='rgba(139,92,246,'+(0.24*(1-d/115))+')';x.lineWidth=1;x.beginPath();x.moveTo(P[i].x,P[i].y);x.lineTo(P[j].x,P[j].y);x.stroke();}
    }
    x.fillStyle='rgba(165,180,252,.75)';x.beginPath();x.arc(P[i].x,P[i].y,P[i].r,0,7);x.fill();
  }
  const pulse=1+Math.sin(t*2)*0.08;
  const g=x.createRadialGradient(cx,cy,0,cx,cy,78*pulse);
  g.addColorStop(0,'rgba(196,181,253,.95)');g.addColorStop(.4,'rgba(99,102,241,.45)');g.addColorStop(1,'rgba(99,102,241,0)');
  x.fillStyle=g;x.beginPath();x.arc(cx,cy,78*pulse,0,7);x.fill();
  x.fillStyle='#fff';x.beginPath();x.arc(cx,cy,9,0,7);x.fill();
  const R=Math.min(88,H/2-30),RX=R*2.1;
  x.strokeStyle='rgba(255,255,255,.14)';x.setLineDash([4,7]);x.beginPath();x.ellipse(cx,cy,RX,R,0,0,7);x.stroke();x.setLineDash([]);
  for(let k=0;k<4;k++){
    const a=t+k*Math.PI/2,sx=cx+Math.cos(a)*RX,sy=cy+Math.sin(a)*R;
    const lg=x.createLinearGradient(cx,cy,sx,sy);
    lg.addColorStop(0,'rgba(167,139,250,.55)');lg.addColorStop(1,'rgba(56,189,248,.15)');
    x.strokeStyle=lg;x.lineWidth=1.4;x.beginPath();x.moveTo(cx,cy);x.lineTo(sx,sy);x.stroke();
    const sg=x.createRadialGradient(sx,sy,2,sx,sy,30);
    sg.addColorStop(0,'rgba(56,189,248,.5)');sg.addColorStop(1,'rgba(56,189,248,0)');
    x.fillStyle=sg;x.beginPath();x.arc(sx,sy,30,0,7);x.fill();
    x.fillStyle='rgba(12,14,24,.92)';x.strokeStyle='rgba(165,180,252,.7)';x.lineWidth=1.5;
    x.beginPath();x.arc(sx,sy,21,0,7);x.fill();x.stroke();
    x.font='20px serif';x.textAlign='center';x.textBaseline='middle';x.fillStyle='#fff';
    x.fillText(icons[k],sx,sy+1);
  }
  requestAnimationFrame(loop);
}
loop();
</script>
"""

# ----------------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }

.stApp { background: #07080d; color: #e8e9f0; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { position: relative; z-index: 1; padding-top: 1.6rem; padding-bottom: 5rem; max-width: 1080px; }

/* Aurora + dotted grid background */
.aurora { position: fixed; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.aurora span { position: absolute; border-radius: 50%; filter: blur(115px); opacity: .42; animation: drift 18s ease-in-out infinite alternate; }
.aurora .a1 { width: 540px; height: 540px; background: #7c3aed; top: -150px; left: -130px; }
.aurora .a2 { width: 500px; height: 500px; background: #0ea5e9; top: 8%; right: -150px; animation-delay: -6s; }
.aurora .a3 { width: 480px; height: 480px; background: #ec4899; bottom: -170px; left: 32%; opacity: .26; animation-delay: -12s; }
@keyframes drift { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(70px,45px) scale(1.18); } }
.stApp::before {
    content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image: radial-gradient(rgba(255,255,255,.08) 1px, transparent 1px);
    background-size: 28px 28px;
    -webkit-mask-image: radial-gradient(ellipse at 50% 28%, #000 15%, transparent 72%);
    mask-image: radial-gradient(ellipse at 50% 28%, #000 15%, transparent 72%);
}

/* Hero */
.hero { text-align: center; margin: 0.4rem 0 0; }
.hero .badge {
    display: inline-flex; align-items: center; gap: 8px; padding: 7px 16px; border-radius: 999px;
    font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; font-weight: 600;
    color: #ddd6fe; background: rgba(139,92,246,0.14); border: 1px solid rgba(139,92,246,0.5);
    box-shadow: 0 0 30px -6px rgba(139,92,246,.8);
}
.hero .badge i { width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 10px #4ade80; display: inline-block; }
.hero h1 {
    font-size: clamp(2.6rem, 6vw, 4.4rem); line-height: 1.04; font-weight: 900; letter-spacing: -0.03em;
    margin: 1.1rem 0 0.8rem;
    background: linear-gradient(100deg, #ffffff 0%, #c4b5fd 25%, #67e8f9 50%, #f0abfc 75%, #ffffff 100%);
    background-size: 220% auto; -webkit-background-clip: text; background-clip: text; color: transparent;
    animation: shimmer 7s linear infinite;
}
@keyframes shimmer { to { background-position: 220% center; } }
.hero p { color: #a1a2b8; font-size: 1.12rem; margin: 0 auto; max-width: 620px; line-height: 1.6; }

/* Glass input panel */
.stTextInput label { font-weight: 600; color: #cfd0e0 !important; letter-spacing: .02em; }
.stTextInput input {
    background: rgba(18, 19, 30, 0.75) !important; color: #fff !important;
    border: 1px solid rgba(255,255,255,0.14) !important; border-radius: 16px !important;
    padding: 0.95rem 1.15rem !important; font-size: 1.05rem;
    backdrop-filter: blur(14px); transition: all .25s ease;
}
.stTextInput input::placeholder { color: #6f7087 !important; }
.stTextInput input:focus {
    border-color: #a78bfa !important; box-shadow: 0 0 0 4px rgba(139,92,246,0.25), 0 0 40px -8px rgba(139,92,246,.7) !important;
}

.stButton > button {
    width: 100%; border-radius: 16px; padding: 0.95rem 1rem; font-weight: 700; font-size: 1.02rem;
    color: #fff; border: none; position: relative; overflow: hidden;
    background: linear-gradient(120deg, #7c3aed, #6366f1 45%, #0ea5e9);
    background-size: 160% 100%; box-shadow: 0 12px 34px rgba(99,102,241,0.42);
    transition: all .3s ease;
}
.stButton > button:hover { transform: translateY(-2px); background-position: 100% 0; box-shadow: 0 18px 44px rgba(99,102,241,0.62); color: #fff; }
.stButton > button:active { transform: translateY(0); }

/* Pipeline graphic */
.pipe-wrap {
    margin: 1.8rem 0 1.2rem; padding: 1.6rem 1.6rem 1.8rem; border-radius: 26px;
    background: linear-gradient(160deg, rgba(255,255,255,0.065), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.1); backdrop-filter: blur(18px);
    box-shadow: 0 24px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,.06);
}
.pipe-status { text-align: center; font-weight: 600; color: #e4e4f2; font-size: 0.98rem; margin-bottom: 0.9rem; }
.pipe-bar { height: 6px; border-radius: 6px; background: rgba(255,255,255,0.08); overflow: hidden; margin: 0 auto 1.8rem; max-width: 640px; }
.pipe-fill {
    height: 100%; border-radius: 6px; transition: width .8s ease;
    background: linear-gradient(90deg, #7c3aed, #38bdf8, #4ade80);
    box-shadow: 0 0 18px rgba(56,189,248,.8);
}
.pipe { display: flex; align-items: flex-start; }
.pnode { flex: 1; text-align: center; position: relative; padding: 0 6px; }
.pnode .orb {
    width: 76px; height: 76px; border-radius: 50%; margin: 0 auto; display: grid; place-items: center;
    font-size: 1.9rem; position: relative; z-index: 2; transition: all .4s ease;
    background: rgba(255,255,255,0.05); border: 2px solid rgba(255,255,255,0.14);
}
.pnode:not(:last-child)::after {
    content: ""; position: absolute; top: 37px; left: calc(50% + 46px); width: calc(100% - 92px);
    height: 3px; border-radius: 3px; background: rgba(255,255,255,0.1); z-index: 1;
}
.pnode .pname { font-weight: 700; color: #fff; margin-top: 0.8rem; font-size: 0.98rem; }
.pnode .pdesc { color: #8d8ea6; font-size: 0.8rem; margin-top: 0.25rem; min-height: 2.4em; line-height: 1.3; }
.pnode .plabel {
    display: inline-block; margin-top: 0.55rem; padding: 3px 13px; border-radius: 999px;
    font-size: 0.7rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase;
    background: rgba(255,255,255,0.07); color: #8d8ea6;
}
.pnode.active .orb {
    border-color: #a78bfa; background: rgba(139,92,246,0.22);
    box-shadow: 0 0 34px -4px #8b5cf6; animation: ripple 1.7s ease-out infinite;
}
.pnode.active:not(:last-child)::after {
    background: linear-gradient(90deg, #8b5cf6, #38bdf8, #8b5cf6); background-size: 200% 100%;
    animation: flow 1.1s linear infinite;
}
.pnode.active .plabel { background: rgba(139,92,246,0.3); color: #ddd6fe; }
.pnode.done .orb { border-color: #4ade80; background: rgba(74,222,128,0.14); box-shadow: 0 0 30px -6px #4ade80; }
.pnode.done .orb::after {
    content: "✓"; position: absolute; top: -4px; right: -4px; width: 24px; height: 24px; border-radius: 50%;
    display: grid; place-items: center; font-size: .8rem; font-weight: 800; color: #04210f; background: #4ade80;
}
.pnode.done:not(:last-child)::after { background: linear-gradient(90deg, #4ade80, #4ade80); box-shadow: 0 0 12px rgba(74,222,128,.7); }
.pnode.done .plabel { background: rgba(74,222,128,0.18); color: #86efac; }
@keyframes ripple {
    0% { box-shadow: 0 0 0 0 rgba(139,92,246,.6), 0 0 34px -4px #8b5cf6; }
    70% { box-shadow: 0 0 0 20px rgba(139,92,246,0), 0 0 34px -4px #8b5cf6; }
    100% { box-shadow: 0 0 0 0 rgba(139,92,246,0), 0 0 34px -4px #8b5cf6; }
}
@keyframes flow { to { background-position: -200% 0; } }

/* Result banner + stats */
.result-head {
    position: relative; overflow: hidden; padding: 1.6rem 1.8rem; border-radius: 24px; margin: 1.4rem 0 1rem;
    background: linear-gradient(135deg, rgba(124,58,237,0.28), rgba(14,165,233,0.14) 60%, rgba(255,255,255,0.03));
    border: 1px solid rgba(167,139,250,0.4); box-shadow: 0 20px 50px rgba(0,0,0,.4);
}
.result-head::after {
    content: ""; position: absolute; right: -60px; top: -60px; width: 220px; height: 220px; border-radius: 50%;
    background: radial-gradient(circle, rgba(167,139,250,.45), transparent 70%);
}
.result-head .l { font-size: 0.72rem; letter-spacing: 0.2em; text-transform: uppercase; color: #c4b5fd; font-weight: 700; }
.result-head .t { font-size: 1.9rem; font-weight: 800; color: #fff; margin-top: 0.35rem; letter-spacing: -0.01em; position: relative; z-index: 1; }
.stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.9rem; margin-bottom: 1.4rem; }
.stat {
    padding: 1.1rem 1.2rem; border-radius: 20px; text-align: center;
    background: rgba(255,255,255,0.045); border: 1px solid rgba(255,255,255,0.09); backdrop-filter: blur(14px);
    transition: transform .25s ease, border-color .25s ease;
}
.stat:hover { transform: translateY(-4px); border-color: rgba(167,139,250,.6); }
.stat .n {
    font-size: 2rem; font-weight: 800; letter-spacing: -0.02em;
    background: linear-gradient(120deg, #fff, #a5b4fc); -webkit-background-clip: text; background-clip: text; color: transparent;
}
.stat .k { font-size: 0.75rem; color: #8d8ea6; letter-spacing: .12em; text-transform: uppercase; margin-top: 0.2rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 0.5rem; background: transparent; border-bottom: none; }
.stTabs [data-baseweb="tab"] {
    border-radius: 14px; padding: 0.7rem 1.3rem; color: #9a9bb0; font-weight: 600;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07); height: auto;
}
.stTabs [aria-selected="true"] {
    color: #fff !important; background: linear-gradient(120deg, rgba(124,58,237,.5), rgba(14,165,233,.35));
    border-color: rgba(167,139,250,.6); box-shadow: 0 8px 24px -8px rgba(124,58,237,.8);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }
.stTabs [data-baseweb="tab-panel"] {
    margin-top: 1rem; padding: 2rem 2.2rem; border-radius: 24px;
    background: linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.09); backdrop-filter: blur(16px);
    box-shadow: 0 24px 60px rgba(0,0,0,0.4);
}
.stTabs [data-baseweb="tab-panel"] h1, .stTabs [data-baseweb="tab-panel"] h2, .stTabs [data-baseweb="tab-panel"] h3 {
    letter-spacing: -0.01em; color: #fff;
}
.stTabs [data-baseweb="tab-panel"] h2 {
    margin-top: 1.6rem; padding-bottom: .4rem; border-bottom: 1px solid rgba(255,255,255,0.1);
}
.stTabs [data-baseweb="tab-panel"] p, .stTabs [data-baseweb="tab-panel"] li { line-height: 1.8; font-size: 1rem; color: #d6d7e6; }
.stTabs [data-baseweb="tab-panel"] a { color: #7dd3fc; }
.stTabs [data-baseweb="tab-panel"] strong { color: #fff; }

.footer-note { text-align: center; color: #5f6078; font-size: 0.78rem; margin-top: 2.4rem; letter-spacing: .08em; }

@media (max-width: 800px) {
    .stats { grid-template-columns: repeat(2, 1fr); }
    .pipe { flex-wrap: wrap; row-gap: 1.6rem; }
    .pnode { flex: 0 0 50%; }
    .pnode::after { display: none !important; }
}
</style>
<div class="aurora"><span class="a1"></span><span class="a2"></span><span class="a3"></span></div>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Hero
# ----------------------------------------------------------------------------
st.markdown(
    """
<div class="hero">
<span class="badge"><i></i>Multi-Agent Research System</span>
<h1>Think deeper.<br>Research faster.</h1>
<p>Four specialised AI agents search, read, write and review, so you get a polished, fact-checked report on any topic.</p>
</div>
""",
    unsafe_allow_html=True,
)

try:
    components.html(HERO_CANVAS, height=250)
except Exception:
    pass

# ----------------------------------------------------------------------------
# Input
# ----------------------------------------------------------------------------
if "result" not in st.session_state:
    st.session_state.result = None
    st.session_state.topic = None

col_input, col_btn = st.columns([4, 1], vertical_alignment="bottom")
with col_input:
    topic = st.text_input(
        "Enter a research topic",
        placeholder="e.g. Latest advances in quantum computing",
    )
with col_btn:
    run_clicked = st.button("🚀 Run Research")

tracker_slot = st.empty()

# ----------------------------------------------------------------------------
# Run the pipeline (pipeline.py is used exactly as it is)
# ----------------------------------------------------------------------------
if run_clicked:
    if not topic.strip():
        st.warning("Please enter a research topic first.")
        tracker_slot.markdown(tracker_html(-1), unsafe_allow_html=True)
    else:
        st.session_state.result = None
        tracker_slot.markdown(tracker_html(0), unsafe_allow_html=True)

        try:
            with contextlib.redirect_stdout(StepWatcher(tracker_slot)):
                state = run_research_pipeline(topic.strip())
            st.session_state.result = state
            st.session_state.topic = topic.strip()
        except Exception as e:
            tracker_slot.markdown(tracker_html(-1), unsafe_allow_html=True)
            st.error(f"The research pipeline failed: {e}")
elif st.session_state.result is None:
    tracker_slot.markdown(tracker_html(-1), unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------------
state = st.session_state.result
if state:
    tracker_slot.markdown(tracker_html(len(STEPS), done=True), unsafe_allow_html=True)

    report_text = str(state["report"])
    words = len(report_text.split())
    read_min = max(1, round(words / 200))
    sources = len(set(re.findall(r"https?://[^\s)\]>\"']+", str(state["search_results"]))))

    st.markdown(
        f"""
<div class="result-head">
<div class="l">Research complete</div>
<div class="t">{st.session_state.topic}</div>
</div>
<div class="stats">
<div class="stat"><div class="n">{words:,}</div><div class="k">Words</div></div>
<div class="stat"><div class="n">{read_min} min</div><div class="k">Read time</div></div>
<div class="stat"><div class="n">{sources}</div><div class="k">Sources found</div></div>
<div class="stat"><div class="n">4</div><div class="k">Agents used</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    tab_report, tab_feedback, tab_search, tab_scraped = st.tabs(
        ["📄 Final Report", "🧐 Critic Feedback", "🔍 Search Results", "🌐 Scraped Content"]
    )

    with tab_report:
        st.markdown(state["report"])

    with tab_feedback:
        st.markdown(state["feedback"])

    with tab_search:
        st.markdown(state["search_results"])

    with tab_scraped:
        st.markdown(state["scraped_content"])

st.markdown(
    '<div class="footer-note">SEARCH · READ · WRITE · REVIEW</div>',
    unsafe_allow_html=True,
)
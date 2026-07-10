import streamlit as st
import pandas as pd
import xgboost as xgb
import time

# ==============================================================================
# KONFIGURASI SISTEM UTAMA
# ==============================================================================
st.set_page_config(
    page_title="Sistem Prediksi Harga Ikan Kota Sorong | v2.0-Final",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# UNDERWATER BACKGROUND & ANIMASI
# ==============================================================================
UNDERWATER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');

.stApp {
    background: linear-gradient(to bottom, rgba(0, 26, 46, 0.6), rgba(0, 92, 138, 0.8)),
                url('https://images.unsplash.com/photo-1582967788606-a171c1080cb0?q=80&w=2000&auto=format&fit=crop');
    background-size: cover;
    background-position: center bottom;
    background-attachment: fixed;
    overflow: hidden;
}
.bubble {
    position: fixed;
    bottom: -20px;
    background-color: rgba(255, 255, 255, 0.3);
    border-radius: 50%;
    animation: floatUp infinite ease-in;
    z-index: 0;
}
@keyframes floatUp {
    0%   { transform: translateY(0) scale(0.5); opacity: 0.8; }
    100% { transform: translateY(-110vh) scale(1.2); opacity: 0; }
}
.fish-sprite {
    position: fixed;
    left: -100px;
    animation: swim linear infinite;
    z-index: 0;
    opacity: 0.85;
    pointer-events: none;
}
@keyframes swim {
    0%   { transform: translateX(-10vw) translateY(0) scaleX(-1); }
    50%  { transform: translateX(55vw) translateY(-40px) scaleX(-1); }
    100% { transform: translateX(110vw) translateY(30px) scaleX(-1); }
}
</style>

<div class="bubble" style="left: 5%;  width: 20px; height: 20px; animation-duration: 5s;"></div>
<div class="bubble" style="left: 25%; width: 15px; height: 15px; animation-duration: 7s; animation-delay: 1s;"></div>
<div class="bubble" style="left: 45%; width: 10px; height: 10px; animation-duration: 4s; animation-delay: 2s;"></div>
<div class="bubble" style="left: 65%; width: 25px; height: 25px; animation-duration: 6s; animation-delay: 3s;"></div>
<div class="bubble" style="left: 85%; width: 12px; height: 12px; animation-duration: 8s; animation-delay: 1s;"></div>

<div class="fish-sprite" style="top: 15%; font-size: 25px; animation-duration: 20s;">🐟</div>
<div class="fish-sprite" style="top: 25%; font-size: 35px; animation-duration: 25s; animation-delay: 4s;">🐠</div>
<div class="fish-sprite" style="top: 40%; font-size: 20px; animation-duration: 18s; animation-delay: 2s;">🐡</div>
<div class="fish-sprite" style="top: 70%; font-size: 28px; animation-duration: 22s; animation-delay: 1s;">🐟</div>
<div class="fish-sprite" style="top: 85%; font-size: 22px; animation-duration: 26s; animation-delay: 5s;">🐠</div>
"""
st.markdown(UNDERWATER_CSS, unsafe_allow_html=True)

# ==============================================================================
# JUDUL SISTEM
# ==============================================================================
st.markdown("""
    <div style='text-align: center; padding-top: 2rem; padding-bottom: 2rem;'>
        <h1 style='color: white; margin-bottom: 0px;'>⚓ SISTEM PREDIKSI KOMODITAS PERIKANAN</h1>
        <h4 style='color: #aed6f1; font-weight: normal;'>Analisis Prediktif Berbasis XGBoost untuk Wilayah Kota Sorong</h4>
        <p style='color: #85c1e9; font-size: 14px;'>Status Server: Online | Dataset Update: 500 Data Observasi</p>
    </div>
""", unsafe_allow_html=True)

# ==============================================================================
# CANVAS ANIMASI BAWAH LAUT
# ==============================================================================
OCEAN_CANVAS = """
<canvas id="ocean-canvas"></canvas>
<script>
(function() {
const canvas = document.getElementById('ocean-canvas');
const ctx    = canvas.getContext('2d');
function resize() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
resize();
window.addEventListener('resize', resize);

const bubbles = Array.from({length: 35}, () => ({
    x: Math.random() * window.innerWidth, y: window.innerHeight + Math.random() * 300,
    r: 2 + Math.random() * 10, sp: 0.4 + Math.random() * 1.2,
    drift: (Math.random() - 0.5) * 0.5, op: 0.2 + Math.random() * 0.5
}));
const plankton = Array.from({length: 60}, () => ({
    x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight,
    r: 0.5 + Math.random() * 2, vx: (Math.random()-0.5)*0.3, vy: (Math.random()-0.5)*0.3,
    op: 0.1 + Math.random() * 0.4, pulse: Math.random() * Math.PI * 2
}));
function makeFish(fromRight) {
    const h = window.innerHeight, size = 15 + Math.random() * 40;
    const sp = (0.8 + Math.random() * 2.5) * (fromRight ? -1 : 1);
    const colors = [['#FF6B35','#FF8C42'],['#FFD166','#EF9F27'],['#06D6A0','#1CB5A0'],
        ['#118AB2','#0FA3B1'],['#E63946','#C1121F'],['#F72585','#C77DFF'],
        ['#7209B7','#A8DADC'],['#FFF3B0','#E9C46A']];
    const col = colors[Math.floor(Math.random()*colors.length)];
    return { x: fromRight ? window.innerWidth + size : -size, y: 80 + Math.random() * (h * 0.65),
        size, sp, vy: (Math.random()-0.5)*0.3, col1: col[0], col2: col[1],
        wobble: Math.random()*Math.PI*2, flip: fromRight ? -1 : 1, stripe: Math.random() > 0.5 };
}
const fish = Array.from({length: 9}, () => makeFish(Math.random()>0.5));
const seahorses = Array.from({length: 2}, (_, i) => ({
    x: 60 + i*(window.innerWidth-100), y: window.innerHeight*0.3+Math.random()*200,
    t: Math.random()*Math.PI*2, dir: i===0?1:-1 }));
const jellies = Array.from({length: 4}, () => ({
    x: Math.random()*window.innerWidth, y: Math.random()*window.innerHeight*0.6,
    r: 20+Math.random()*30, t: Math.random()*Math.PI*2,
    sp: 0.008+Math.random()*0.012, hue: Math.floor(Math.random()*60+270) }));

function drawBubble(b) {
    ctx.save(); ctx.globalAlpha = b.op;
    const g = ctx.createRadialGradient(b.x-b.r*0.3,b.y-b.r*0.3,b.r*0.05,b.x,b.y,b.r);
    g.addColorStop(0,'rgba(255,255,255,0.8)'); g.addColorStop(0.4,'rgba(180,230,255,0.3)');
    g.addColorStop(1,'rgba(100,180,255,0.05)');
    ctx.beginPath(); ctx.arc(b.x,b.y,b.r,0,Math.PI*2);
    ctx.fillStyle=g; ctx.fill();
    ctx.strokeStyle='rgba(200,240,255,0.4)'; ctx.lineWidth=0.5; ctx.stroke(); ctx.restore();
}
function drawFish(f,t) {
    ctx.save(); ctx.translate(f.x,f.y); ctx.scale(f.flip,1);
    ctx.rotate(Math.sin(t*0.05+f.wobble)*0.12);
    const s=f.size;
    const bg=ctx.createLinearGradient(-s,0,s*0.8,0);
    bg.addColorStop(0,f.col2); bg.addColorStop(1,f.col1);
    ctx.beginPath(); ctx.ellipse(0,0,s,s*0.45,0,0,Math.PI*2);
    ctx.fillStyle=bg; ctx.fill();
    if(f.stripe){ctx.save();ctx.clip();ctx.strokeStyle='rgba(255,255,255,0.25)';ctx.lineWidth=s*0.12;
        for(let i=-1;i<=2;i++){ctx.beginPath();ctx.moveTo(i*s*0.45,-s*0.5);ctx.lineTo(i*s*0.45,s*0.5);ctx.stroke();}ctx.restore();}
    ctx.save(); ctx.translate(-s*0.85,0); ctx.rotate(Math.sin(t*0.08+f.wobble)*0.4);
    ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(-s*0.55,s*0.42); ctx.lineTo(-s*0.55,-s*0.42);
    ctx.closePath(); ctx.fillStyle=f.col1; ctx.fill(); ctx.restore();
    ctx.beginPath(); ctx.moveTo(-s*0.1,-s*0.38); ctx.quadraticCurveTo(s*0.15,-s*0.75,s*0.35,-s*0.42);
    ctx.quadraticCurveTo(s*0.1,-s*0.5,-s*0.1,-s*0.38); ctx.fillStyle=f.col2+'CC'; ctx.fill();
    ctx.beginPath(); ctx.arc(s*0.55,-s*0.1,s*0.1,0,Math.PI*2); ctx.fillStyle='#111'; ctx.fill();
    ctx.beginPath(); ctx.arc(s*0.57,-s*0.12,s*0.04,0,Math.PI*2); ctx.fillStyle='white'; ctx.fill();
    ctx.restore();
}
function drawSeahorse(sh,t) {
    ctx.save(); ctx.translate(sh.x,sh.y+Math.sin(t*0.02+sh.t)*6); ctx.scale(sh.dir*0.7,0.7);
    ctx.beginPath(); ctx.moveTo(0,-40); ctx.bezierCurveTo(25,-20,25,10,10,30);
    ctx.bezierCurveTo(0,50,-5,65,8,80); ctx.lineWidth=8; ctx.strokeStyle='#F4A261'; ctx.lineCap='round'; ctx.stroke();
    ctx.beginPath(); ctx.ellipse(0,-45,9,14,0.2,0,Math.PI*2); ctx.fillStyle='#E76F51'; ctx.fill();
    ctx.beginPath(); ctx.moveTo(9,-48); ctx.lineTo(28,-50); ctx.lineWidth=3.5; ctx.strokeStyle='#F4A261'; ctx.stroke();
    ctx.beginPath(); ctx.arc(6,-50,4,0,Math.PI*2); ctx.fillStyle='#222'; ctx.fill();
    ctx.beginPath(); ctx.arc(7,-51,1.5,0,Math.PI*2); ctx.fillStyle='white'; ctx.fill();
    ctx.save(); ctx.translate(14,-25); ctx.rotate(Math.sin(t*0.1+sh.t)*0.3);
    ctx.beginPath(); ctx.ellipse(0,0,12,6,0.5,0,Math.PI*2); ctx.fillStyle='rgba(244,162,97,0.6)'; ctx.fill(); ctx.restore();
    ctx.strokeStyle='#E9C46A'; ctx.lineWidth=2;
    for(let i=0;i<5;i++){const py=-30+i*14;ctx.beginPath();ctx.moveTo(2,py);ctx.lineTo(14,py-4);ctx.stroke();}
    ctx.restore();
}
function drawJellyfish(j,t) {
    ctx.save(); ctx.translate(j.x,j.y+Math.sin(t*0.015+j.t)*25);
    ctx.scale(1+Math.sin(t*j.sp*60)*0.12,1+Math.sin(t*j.sp*60)*0.12);
    const gj=ctx.createRadialGradient(0,-j.r*0.3,0,0,0,j.r);
    gj.addColorStop(0,`hsla(${j.hue},80%,80%,0.7)`); gj.addColorStop(0.7,`hsla(${j.hue},70%,55%,0.4)`);
    gj.addColorStop(1,`hsla(${j.hue},60%,40%,0.1)`);
    ctx.beginPath(); ctx.arc(0,0,j.r,Math.PI,0); ctx.closePath(); ctx.fillStyle=gj; ctx.fill();
    ctx.lineWidth=1;
    for(let i=-3;i<=3;i++){const wave=Math.sin(t*0.03+i*0.8)*12;
        ctx.beginPath(); ctx.moveTo(i*j.r*0.28,j.r*0.1);
        ctx.bezierCurveTo(i*j.r*0.28+wave,j.r*0.6,i*j.r*0.28-wave,j.r*1.2,i*j.r*0.28+wave*0.5,j.r*1.7);
        ctx.strokeStyle=`hsla(${j.hue},70%,70%,0.4)`; ctx.stroke();}
    ctx.restore();
}
let coralCanvas=null;
function buildCorals() {
    coralCanvas=document.createElement('canvas');
    coralCanvas.width=canvas.width; coralCanvas.height=canvas.height;
    const cc=coralCanvas.getContext('2d'), W=canvas.width, H=canvas.height;
    const sand=cc.createLinearGradient(0,H*0.82,0,H);
    sand.addColorStop(0,'rgba(180,140,90,0.0)'); sand.addColorStop(0.3,'rgba(160,120,70,0.35)');
    sand.addColorStop(1,'rgba(100,70,30,0.55)'); cc.fillStyle=sand; cc.fillRect(0,H*0.82,W,H*0.18);
    const grassColors=['#2d6a4f','#40916c','#52b788','#1b4332','#74c69d'];
    [[0.05,14],[0.18,10],[0.32,13],[0.55,11],[0.68,14],[0.82,12],[0.92,9]].forEach(([rx,cnt])=>{
        const gx=rx*W, col=grassColors[Math.floor(Math.random()*grassColors.length)];
        for(let i=0;i<cnt;i++){const x=gx+i*9+(Math.random()-0.5)*4,gh=(60+Math.random()*50)*(0.5+Math.random()*0.5),ctrl=(Math.random()-0.5)*30;
            cc.beginPath();cc.moveTo(x,H*0.92);cc.quadraticCurveTo(x+ctrl,H*0.92-gh*0.5,x+ctrl*0.3,H*0.92-gh);
            cc.lineWidth=2+Math.random()*2;cc.strokeStyle=col;cc.lineCap='round';cc.stroke();}
    });
    function branchCoral(x,y,len,angle,depth,col){
        if(depth===0||len<4)return;
        const ex=x+Math.cos(angle)*len,ey=y+Math.sin(angle)*len;
        cc.beginPath();cc.moveTo(x,y);cc.lineTo(ex,ey);cc.lineWidth=depth*1.8;cc.strokeStyle=col;cc.lineCap='round';cc.stroke();
        branchCoral(ex,ey,len*0.72,angle-0.45,depth-1,col);branchCoral(ex,ey,len*0.72,angle+0.45,depth-1,col);
        if(depth>2)branchCoral(ex,ey,len*0.6,angle,depth-1,col);
    }
    function roundCoral(x,y,size,col){
        for(let i=0;i<12;i++){const a=(i/12)*Math.PI*2,r=size*(0.7+Math.random()*0.3);
            cc.beginPath();cc.arc(x+Math.cos(a)*r*0.8,y+Math.sin(a)*r*0.5,size*0.15+Math.random()*size*0.1,0,Math.PI*2);
            cc.fillStyle=col;cc.fill();}
        cc.beginPath();cc.arc(x,y,size*0.5,0,Math.PI*2);cc.fillStyle=col+'99';cc.fill();
    }
    function fanCoral(x,y,size,col){
        for(let i=0;i<18;i++){const a=(i/18)*Math.PI-Math.PI/2,r=size*(0.6+Math.random()*0.4);
            cc.beginPath();cc.moveTo(x,y);cc.lineTo(x+Math.cos(a)*r,y+Math.sin(a)*r);
            cc.lineWidth=0.8+Math.random();cc.strokeStyle=col+'AA';cc.stroke();}
        for(let ring=1;ring<=4;ring++){cc.beginPath();cc.arc(x,y,size*ring*0.22,Math.PI*1.1,Math.PI*1.9);
            cc.lineWidth=0.5;cc.strokeStyle=col+'66';cc.stroke();}
    }
    [[0.04,0.88,55,'#E63946','branch'],[0.12,0.90,40,'#FF6B6B','round'],[0.20,0.87,65,'#F4A261','branch'],
     [0.28,0.92,30,'#06D6A0','fan'],[0.38,0.89,50,'#FF9F1C','round'],[0.45,0.86,70,'#C77DFF','branch'],
     [0.54,0.91,35,'#E63946','fan'],[0.62,0.88,55,'#FFD166','branch'],[0.70,0.90,42,'#06D6A0','round'],
     [0.78,0.87,60,'#F72585','branch'],[0.86,0.91,38,'#4CC9F0','fan'],[0.94,0.89,52,'#FF6B6B','round']
    ].forEach(([rx,ry,size,col,type])=>{
        const cx=rx*W,cy=ry*H;
        if(type==='branch')branchCoral(cx,cy,size,-Math.PI/2,5,col);
        else if(type==='round')roundCoral(cx,cy,size,col);
        else fanCoral(cx,cy,size,col);
    });
    [[0.1,0.95],[0.3,0.96],[0.5,0.95],[0.72,0.96],[0.9,0.95]].forEach(([rx,ry])=>{
        cc.beginPath();cc.ellipse(rx*W,ry*H,18+Math.random()*20,8+Math.random()*8,Math.random()*0.5,0,Math.PI*2);
        cc.fillStyle='rgba(80,60,40,0.55)';cc.fill();});
}
let t=0;
function loop(){
    const W=canvas.width,H=canvas.height;
    ctx.clearRect(0,0,W,H);
    const bg=ctx.createLinearGradient(0,0,0,H);
    bg.addColorStop(0,'#001a2e');bg.addColorStop(0.3,'#002d4a');
    bg.addColorStop(0.7,'#003d5c');bg.addColorStop(1,'#001a2e');
    ctx.fillStyle=bg;ctx.fillRect(0,0,W,H);
    if(!coralCanvas||coralCanvas.width!==W)buildCorals();
    ctx.drawImage(coralCanvas,0,0);
    for(let i=0;i<8;i++){
        const lx=(0.1+i*0.12)*W+Math.sin(t*0.008+i)*30;
        const alpha=0.03+Math.sin(t*0.012+i*0.7)*0.02;
        const lg=ctx.createLinearGradient(lx-18,0,lx+18,H*0.75);
        lg.addColorStop(0,`rgba(100,220,255,${alpha})`);lg.addColorStop(1,'transparent');
        ctx.fillStyle=lg;ctx.beginPath();ctx.moveTo(lx-18,0);ctx.lineTo(lx+18,0);
        ctx.lineTo(lx+50,H*0.75);ctx.lineTo(lx-50,H*0.75);ctx.closePath();ctx.fill();}
    plankton.forEach(p=>{
        p.x+=p.vx;p.y+=p.vy;p.pulse+=0.04;
        if(p.x<0)p.x=W;if(p.x>W)p.x=0;if(p.y<0)p.y=H;if(p.y>H)p.y=0;
        ctx.save();ctx.globalAlpha=p.op*(0.6+Math.sin(p.pulse)*0.4);
        ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
        ctx.fillStyle='#a0f0ff';ctx.shadowBlur=6;ctx.shadowColor='#00d2ff';ctx.fill();ctx.restore();});
    jellies.forEach(j=>drawJellyfish(j,t));
    seahorses.forEach(sh=>drawSeahorse(sh,t));
    fish.forEach((f,i)=>{
        drawFish(f,t);f.x+=f.sp;f.y+=f.vy;f.vy+=(Math.random()-0.5)*0.04;
        f.vy=Math.max(-0.8,Math.min(0.8,f.vy));
        if(f.y<60)f.vy+=0.1;if(f.y>H*0.78)f.vy-=0.1;
        const gone=(f.sp>0&&f.x>W+80)||(f.sp<0&&f.x<-80);
        if(gone)fish[i]=makeFish(f.sp>0);});
    bubbles.forEach(b=>{
        drawBubble(b);b.y-=b.sp;b.x+=b.drift;b.drift+=(Math.random()-0.5)*0.05;
        if(b.y<-30){b.y=canvas.height+20;b.x=Math.random()*canvas.width;}});
    t++;requestAnimationFrame(loop);
}
setTimeout(()=>{buildCorals();loop();},300);
})();
</script>
"""
st.markdown(OCEAN_CANVAS, unsafe_allow_html=True)

# ==============================================================================
# ▼▼▼ MAPPING DATASET BARU — Dataset_Ikan_Kelompok_11.csv ▼▼▼
# Kolom: Bulan, Jenis Ikan, Ukuran, Kondisi Stok, Kondisi Pembeli, Cuaca, Kondisi Laut
# Lokasi DIHAPUS sesuai permintaan
# Bulan hanya Januari–Juli
# Cuaca sesuai dataset: Cerah Berawan, Hujan Ringan, Hujan lebat dan angin kencang, Sedikit Extrem
# Jenis Ikan: 9 spesies sesuai dataset (sudah dinormalisasi)
# ==============================================================================
def get_mappings():
    return {
        # ── Bulan: Januari s.d. Juli ─────────────────────────────────────
        'bulan': {
            'Januari' : 1,
            'Februari': 2,
            'Maret'   : 3,
            'April'   : 4,
            'Mei'     : 5,
            'Juni'    : 6,
            'Juli'    : 7,
        },

        # ── Jenis Ikan: 9 spesies dari Dataset_Ikan_Kelompok_11.csv ─────
        # (sudah dinormalisasi: 'Ikan kakap Merah' & 'Kakap Merah' → 'Ikan Kakap Merah')
        'ikan': {
            'Ikan Bubara'         : 0,
            'Ikan Ekor Kuning'    : 1,
            'Ikan Kakap Merah'    : 2,
            'Ikan Kerapu'         : 3,
            'Ikan Lema'           : 4,
            'Ikan Momar'          : 5,
            'Ikan Oci'            : 6,
            'Ikan Tenggiri'       : 7,
            'Ikan Tongkol'        : 8,
            'Ikan Tuna Sirip Kuning': 9,
        },

        # ── Ukuran ──────────────────────────────────────────────────────
        'ukuran': {
            'Kecil' : 0,
            'Sedang': 1,
            'Besar' : 2,
        },

        # ── Kondisi Stok ─────────────────────────────────────────────────
        'stok': {
            'Sangat Sedikit': 0,
            'Sedikit'       : 1,
            'Sedang'        : 2,
            'Banyak'        : 3,
        },

        # ── Kondisi Pembeli ──────────────────────────────────────────────
        'pembeli': {
            'Sangat Sepi': 0,
            'Sepi'       : 1,
            'Sedang'     : 2,
            'Ramai'      : 3,
        },

        # ── Cuaca: sesuai nilai di Dataset_Ikan_Kelompok_11.csv ─────────
        'cuaca': {
            'Cerah Berawan'                : 0,
            'Hujan Ringan'                 : 1,
            'Sedikit Extrem'               : 2,
            'Hujan lebat dan angin kencang': 3,
        },

        # ── Kondisi Laut ─────────────────────────────────────────────────
        'laut': {
            'Laut Tenang'     : 0,
            'Gelombang Rendah': 1,
            'Gelombang Sedang': 2,
            'Gelombang Tinggi': 3,
        },
    }

# ==============================================================================
# LOAD MODEL
# ==============================================================================
@st.cache_resource
def initialize_ai_model():
    try:
        engine = xgb.XGBRegressor()
        engine.load_model('model_xgboost_sorong.json')
        return engine
    except Exception as e:
        st.error(f"FATAL ERROR: Gagal memuat kernel AI. Detail: {e}")
        return None

# ==============================================================================
# LOAD DATASET (untuk tab Analisis)
# ==============================================================================
@st.cache_data
def load_dataset():
    try:
        df = pd.read_csv('Dataset_Ikan_Kelompok_11.csv', sep=';')
        df.columns = df.columns.str.strip()
        # Normalisasi nama ikan
        df['Jenis Ikan'] = df['Jenis Ikan'].replace({
            'Ikan kakap Merah': 'Ikan Kakap Merah',
            'Kakap Merah'     : 'Ikan Kakap Merah',
        })
        return df
    except Exception as e:
        st.warning(f"Dataset tidak ditemukan: {e}")
        return None

# ==============================================================================
# MAIN LOGIC
# ==============================================================================
model_ai = initialize_ai_model()
maps     = get_mappings()

if model_ai:
    tab_prediksi, tab_analisis, tab_tentang = st.tabs(
        ["🚀 Engine Prediksi", "📊 Analisis Data", "📖 Dokumentasi"])

    # ── TAB 1: ENGINE PREDIKSI ────────────────────────────────────────────────
    with tab_prediksi:
        col_input, col_output = st.columns([1, 1.3], gap="large")

        with col_input:
            st.markdown("### 📥 Input Parameter Sistem")

            # ── Expander 1: Waktu (TANPA lokasi) ──
            with st.expander("🗓️ Informasi Waktu", expanded=True):
                var_bulan = st.selectbox(
                    "Pilih Bulan",
                    list(maps['bulan'].keys()),
                    help="Periode penelitian: Januari – Juli"
                )

            # ── Expander 2: Spesifikasi Ikan ──
            with st.expander("🐟 Spesifikasi Komoditas Ikan", expanded=True):
                var_ikan = st.selectbox(
                    "Jenis Ikan",
                    list(maps['ikan'].keys()),
                    help="9 jenis ikan yang diprediksi"
                )
                var_ukuran = st.select_slider(
                    "Ukuran Ikan",
                    options=list(maps['ukuran'].keys()),
                    value='Sedang'
                )

            # ── Expander 3: Kondisi Pasar ──
            with st.expander("🏪 Kondisi Pasar", expanded=True):
                var_stok = st.select_slider(
                    "Kondisi Stok",
                    options=list(maps['stok'].keys()),
                    value='Sedang'
                )
                var_pembeli = st.select_slider(
                    "Kondisi Pembeli",
                    options=list(maps['pembeli'].keys()),
                    value='Sedang'
                )

            # ── Expander 4: Lingkungan ──
            with st.expander("🌤️ Variabel Eksternal (Lingkungan)", expanded=True):
                var_cuaca = st.radio(
                    "Kondisi Cuaca",
                    list(maps['cuaca'].keys()),
                    horizontal=False,
                    help="Sesuai kondisi cuaca pada hari pengambilan data"
                )
                var_laut = st.selectbox(
                    "Kondisi Laut",
                    list(maps['laut'].keys())
                )

            st.write("")
            trigger_btn = st.button("🐟 PROSES DATA SEKARANG", use_container_width=True)

        # ── Kolom output ──
        with col_output:
            st.markdown("### 💻 Output Komputasi AI")
            if trigger_btn:
                with st.status("Mengirim data ke model XGBoost...", expanded=True) as status:
                    st.write("Melakukan ekstraksi fitur..."); time.sleep(0.5)
                    st.write("Menjalankan perhitungan regresi XGBoost..."); time.sleep(0.7)
                    st.write("Memformat hasil prediksi...")
                    status.update(label="Komputasi Selesai!", state="complete", expanded=False)

                # Susun input sesuai nama kolom SAAT MODEL DILATIH:
                # bulan, lokasi, jenis_ikan, ukuran, kondisi_cuaca, kondisi_laut, supply
                # lokasi diisi 0 (default) karena sudah dihapus dari form
                raw = [[
                    maps['bulan'][var_bulan],
                    0,                              # lokasi → default 0
                    maps['ikan'][var_ikan],
                    maps['ukuran'][var_ukuran],
                    maps['cuaca'][var_cuaca],
                    maps['laut'][var_laut],
                    maps['stok'][var_stok],         # supply = kondisi stok
                ]]
                cols_model = [
                    'bulan', 'lokasi', 'jenis_ikan',
                    'ukuran', 'kondisi_cuaca', 'kondisi_laut', 'supply'
                ]
                input_df = pd.DataFrame(raw, columns=cols_model)
                prediksi = model_ai.predict(input_df)[0]

                # Animasi gelembung bawah laut
                st.markdown("""
                <style>
                .gelembung-wrap {
                    position: fixed;
                    bottom: 0; left: 0;
                    width: 100%; height: 100%;
                    pointer-events: none;
                    z-index: 9999;
                    overflow: hidden;
                }
                .gelembung {
                    position: absolute;
                    bottom: -60px;
                    border-radius: 50%;
                    background: radial-gradient(circle at 35% 35%,
                        rgba(255,255,255,0.85),
                        rgba(150,230,255,0.4) 50%,
                        rgba(0,180,255,0.1) 100%);
                    border: 1px solid rgba(200,240,255,0.5);
                    animation: naik linear forwards;
                }
                @keyframes naik {
                    0%   { transform: translateY(0) translateX(0) scale(0.6); opacity: 0.9; }
                    50%  { opacity: 0.8; }
                    100% { transform: translateY(-110vh) translateX(var(--dx)) scale(1.1); opacity: 0; }
                }
                </style>
                <div class="gelembung-wrap" id="bubble-burst"></div>
                <script>
                (function(){
                    const wrap = document.getElementById('bubble-burst');
                    if (!wrap) return;
                    for (let i = 0; i < 55; i++) {
                        const b    = document.createElement('div');
                        b.className = 'gelembung';
                        const size  = 8  + Math.random() * 30;
                        const left  = Math.random() * 100;
                        const delay = Math.random() * 2.5;
                        const dur   = 3  + Math.random() * 4;
                        const dx    = (Math.random() - 0.5) * 120;
                        b.style.cssText =
                            'width:'+size+'px;height:'+size+'px;left:'+left+'%;' +
                            '--dx:'+dx+'px;animation-duration:'+dur+'s;animation-delay:'+delay+'s;';
                        wrap.appendChild(b);
                    }
                    setTimeout(function(){ wrap.remove(); }, 7000);
                })();
                </script>
                """, unsafe_allow_html=True)
                st.success(f"✅ Berhasil memproses estimasi untuk **{var_ikan}**")
                st.metric(
                    label=f"Estimasi Harga Per Kilogram — {var_bulan}",
                    value=f"Rp {int(prediksi):,}",
                    delta="Akurasi Model: 96,38%"
                )

                # Ringkasan input
                st.markdown("**📋 Ringkasan Parameter Input:**")
                ringkasan = {
                    "Bulan"          : var_bulan,
                    "Jenis Ikan"     : var_ikan,
                    "Ukuran"         : var_ukuran,
                    "Kondisi Stok"   : var_stok,
                    "Kondisi Pembeli": var_pembeli,
                    "Cuaca"          : var_cuaca,
                    "Kondisi Laut"   : var_laut,
                }
                st.table(pd.DataFrame(ringkasan.items(), columns=["Parameter", "Nilai"]))

                with st.chat_message("assistant"):
                    st.write(
                        f"Berdasarkan data input, harga **{var_ikan}** ukuran **{var_ukuran}** "
                        f"pada bulan **{var_bulan}** dengan kondisi stok **{var_stok}** "
                        f"dan cuaca **{var_cuaca}** diprediksi sebesar "
                        f"**Rp {int(prediksi):,} / kg**."
                    )
            else:
                st.info("Sistem standby. Silakan masukkan parameter di sebelah kiri dan klik tombol proses.")

    # ── TAB 2: ANALISIS DATA ──────────────────────────────────────────────────
    with tab_analisis:
        st.subheader("📊 Analisis Data — Dataset_Ikan_Kelompok_11.csv")
        st.markdown("Berikut adalah **9 jenis ikan** yang menjadi komoditas prediksi pada sistem ini:")

        # Tampilkan hanya nama jenis ikan (tanpa harga, tanpa ID label)
        daftar_ikan = [
            "Ikan Bubara",
            "Ikan Ekor Kuning",
            "Ikan Kakap Merah",
            "Ikan Kerapu",
            "Ikan Lema",
            "Ikan Momar",
            "Ikan Oci",
            "Ikan Tenggiri",
            "Ikan Tongkol",
            "Ikan Tuna Sirip Kuning",
        ]
        df_ikan = pd.DataFrame({
            "No" : range(1, len(daftar_ikan) + 1),
            "Nama Jenis Ikan": daftar_ikan,
        })
        st.table(df_ikan.set_index("No"))

        st.info(
            "💡 Dataset bersumber dari observasi langsung di Pasar Remu, Pasar Perumnas, "
            "dan Pasar Klademak Kota Sorong. Total data: 500 baris, periode Januari–Juli."
        )

    # ── TAB 3: DOKUMENTASI ───────────────────────────────────────────────────
    with tab_tentang:
        st.markdown("""
        ### 👨‍💻 Identitas Pengembang
        - **Kelompok 11B:** Mieshell dan Beiverly
        - **Studi:** Teknik Informatika (SMT 2)
        - **Instansi:** Universitas Muhammadiyah Sorong
        - **Model:** Extreme Gradient Boosting (XGBoost Regresi)

        ---

        ### 📁 Informasi Dataset
        - **Nama File:** Dataset_Ikan_Kelompok_11.csv
        - **Total Data:** 500 baris observasi
        - **Periode:** Januari – Juli
        - **Sumber:** Observasi primer Pasar Remu, Perumnas, Klademak — Kota Sorong
        - **Fitur:** Bulan, Jenis Ikan, Ukuran, Kondisi Stok, Kondisi Pembeli, Cuaca, Kondisi Laut

        ---

        ### 📊 Performa Model
        - **R² Testing:** 96,13% (0,9613)
        - **MAE Testing:** Rp 1.884,93 / kg
        - **MAPE Testing:** 3,62% → Akurasi ≈ 96,38%
        - **Cross Validation R²:** 0,9820 ± 0,0087

        ---
        **Versi Aplikasi:** 2.0.1 (Build-2026)
        **Tujuan:** Memenuhi Tugas Besar mata kuliah Algoritma & Pemrograman II
        """)

st.markdown("---")
st.caption("© 2026 Kelompok 11B — Informatika Project. Built with Streamlit & ❤️ in Kota Sorong.")
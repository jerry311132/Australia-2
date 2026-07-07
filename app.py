import streamlit as st
import datetime
import json
import os
import requests

try:
    from streamlit_js_eval import get_geolocation
except Exception:
    get_geolocation = None

DATA_FILE = os.path.join(os.path.dirname(__file__), "trip_data.json")

# ==========================================
# 0. 本地資料儲存（家人共用，存在伺服器端 JSON）
# ==========================================
def default_store():
    return {
        "packing": {
            "members": ["爸爸", "媽媽"],
            "current": "爸爸",
            "items": [
                "護照 / 簽證", "手機充電器", "轉接頭（澳洲插座）", "防曬乳",
                "常備藥品", "台灣駕照正本 + 國際駕照", "保暖外套（8月為冬季）",
                "澳洲上網 SIM / eSIM"
            ],
            "checks": {}
        },
        "flight_pax": {}
    }

def load_store():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    d = default_store()
    save_store(d)
    return d

def save_store(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

if "store" not in st.session_state:
    st.session_state.store = load_store()

store = st.session_state.store

def persist():
    save_store(store)

def maps_link(query):
    from urllib.parse import quote
    return f"https://www.google.com/maps/dir/?api=1&destination={quote(query)}"

def md(html):
    """st.markdown for HTML blocks - strips per-line indentation so Streamlit
    doesn't mistake indented lines for a Markdown code block."""
    cleaned = "\n".join(line.strip() for line in html.strip("\n").split("\n"))
    st.markdown(cleaned, unsafe_allow_html=True)

# ==========================================
# 1. 網頁基本設定
# ==========================================
st.set_page_config(page_title="2026 澳洲自駕隨身手冊 🦘", page_icon="🦘", layout="centered")

custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&family=Outfit:wght@300;400;500;600;700&display=swap');
html, body, .stApp {
    font-family: 'Outfit', 'Noto Sans TC', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background-color: #f7f9fa !important;
    color: #232d37 !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stConnectionStatus"] {display: none;}
.hero-banner {
    background: linear-gradient(135deg, #005f73 0%, #0a9396 45%, #ee9b00 85%, #ca6702 100%);
    color: white; padding: 30px 25px; border-radius: 20px; margin-bottom: 25px;
    box-shadow: 0 10px 25px rgba(10, 147, 150, 0.15); text-align: center;
}
.hero-banner h1 { font-size: 2.1rem !important; font-weight: 700 !important; margin: 0 !important; color: white !important; }
.hero-banner p { font-size: 0.95rem !important; margin: 8px 0 0 0 !important; opacity: 0.95; font-weight: 500; }
.travel-card {
    background: rgba(255, 255, 255, 0.95) !important; border-radius: 16px !important; padding: 22px !important;
    margin-bottom: 18px !important; border: 1px solid rgba(10, 147, 150, 0.15) !important;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.04) !important;
}
.timeline-container { padding-left: 5px; margin-top: 10px; }
.timeline-item { position: relative; padding-left: 28px; padding-bottom: 22px; border-left: 2.5px solid rgba(10, 147, 150, 0.3); }
.timeline-item:last-child { border-left: 2.5px solid transparent; padding-bottom: 5px; }
.timeline-item::before {
    content: ''; position: absolute; left: -8px; top: 5px; width: 14px; height: 14px;
    background-color: #0a9396; border: 3px solid white; border-radius: 50%;
    box-shadow: 0 0 0 3px rgba(10, 147, 150, 0.25);
}
.timeline-time {
    display: inline-block; background: linear-gradient(135deg, rgba(10, 147, 150, 0.15) 0%, rgba(0, 95, 115, 0.15) 100%);
    color: #005f73; font-weight: 700; font-size: 0.82rem; padding: 3px 10px; border-radius: 20px; margin-bottom: 6px;
}
.timeline-title { font-weight: 700; color: #1a202c; font-size: 1.05rem; }
.timeline-desc { color: #4a5568; font-size: 0.92rem; margin-top: 5px; line-height: 1.45; }
.timeline-tag-hotel { display: inline-block; background-color: rgba(10, 147, 150, 0.08); color: #005f73; font-size: 0.78rem; padding: 2px 8px; border-radius: 6px; margin-right: 6px; font-weight: bold; }
.timeline-tag-car-yes { display: inline-block; background-color: rgba(56, 161, 105, 0.08); color: #38a169; font-size: 0.78rem; padding: 2px 8px; border-radius: 6px; font-weight: bold; }
.timeline-tag-car-no { display: inline-block; background-color: rgba(229, 62, 62, 0.08); color: #e53e3e; font-size: 0.78rem; padding: 2px 8px; border-radius: 6px; font-weight: bold; }
.copyable-field { background-color: #f7fafc; border: 1px dashed #0a9396; border-radius: 10px; padding: 10px 14px; font-family: monospace; font-size: 0.95rem; color: #2d3748; margin: 8px 0; display: flex; justify-content: space-between; align-items: center; }
.map-btn { display: inline-flex; align-items: center; background-color: #ffffff; color: #ca6702; border: 1px solid #ca6702; border-radius: 20px; padding: 3px 12px; font-size: 0.8rem; font-weight: bold; text-decoration: none; margin-top: 8px; }
.alert-card-info { background: linear-gradient(135deg, rgba(10, 147, 150, 0.08) 0%, rgba(0, 95, 115, 0.08) 100%); border-left: 5px solid #0a9396; color: #005f73; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
.alert-card-success { background: linear-gradient(135deg, rgba(56, 161, 105, 0.08) 0%, rgba(47, 133, 90, 0.08) 100%); border-left: 5px solid #38a169; color: #22543d; padding: 15px; border-radius: 12px; margin-bottom: 15px; }
.weather-now { background: linear-gradient(135deg, #2b6cb0, #1c4a75); color: #fff; border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 14px; }
.weather-now .temp { font-size: 42px; font-weight: 700; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.markdown(
    """<div class="hero-banner"><h1>🇦🇺 2026 澳洲自駕隨身手冊</h1>
    <p>📱 全家共用行動版</p></div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🦘 澳洲旅程助手")
    departure_date = datetime.date(2026, 7, 30)
    today = datetime.date.today()
    days_left = (departure_date - today).days
    if days_left > 0:
        st.metric(label="✈️ 距離出發還有", value=f"{days_left} 天")
    elif days_left == 0:
        st.success("🎉 今天就是出發日！")
    else:
        st.info("✈️ 澳洲旅程進行中 / 已回國")
    st.write("---")
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    aest_time = now_utc + datetime.timedelta(hours=10)
    st.markdown(f"🕒 **澳洲東部時間 (AEST)**：`{aest_time.strftime('%H:%M:%S')}`")
    st.caption("※ 墨爾本/雪梨/布里斯本比台灣快 2 小時")

# ==========================================
# 主分頁
# ==========================================
tabs = st.tabs(["📅 行程", "✈️ 航班", "🚗 租車", "🏨 飯店", "☀️ 天氣", "🧳 行李"])

# ------------------------------------------
# 📅 行程
# ------------------------------------------
with tabs[0]:
    st.subheader("🗺️ 14 天完整行程安排")
    area_sel = st.segmented_control(
        "快速跳轉：",
        options=["全部天數", "新加坡+墨爾本段", "雪梨段", "昆士蘭段"],
        default="全部天數",
    )

    def day_card(title, expanded, hotel, car_tag, body_html):
        show = area_sel == "全部天數" or expanded[1]
        if not show:
            return
        with st.expander(title, expanded=False):
            md(f"""<div class="timeline-container">
                <span class="timeline-tag-hotel">🏠 {hotel}</span>
                <span class="{car_tag[0]}">{car_tag[1]}</span>
                {body_html}
                </div>""")

    day_card(
        "📅 7/30 (四) Day 1：凌晨出發，新加坡轉機一日遊 ✈️",
        (None, area_sel in ["全部天數", "新加坡+墨爾本段"]),
        "新加坡樟宜機場周邊 / 晚間飛墨爾本",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">凌晨</div>
        <div class="timeline-title">🛫 桃園機場出發，飛往新加坡轉機</div>
        <div class="timeline-desc">提早抵達桃園機場辦理登機，確認澳洲電子簽證(ETA)與國際駕照已備妥。</div></div>
        <div class="timeline-item"><div class="timeline-time">白天</div>
        <div class="timeline-title">🌺 新加坡一日遊</div>
        <div class="timeline-desc">濱海灣花園(Gardens by the Bay)、金沙酒店空中花園、烏節路，行李可先寄放機場。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Gardens+by+the+Bay+Singapore" target="_blank" class="map-btn">📍 濱海灣花園導航</a></div>
        <div class="timeline-item"><div class="timeline-time">傍晚</div>
        <div class="timeline-title">✈️ 搭乘晚班機飛往墨爾本</div>
        <div class="timeline-desc">於樟宜機場辦理登機，飛往墨爾本（隔日抵達）。</div></div>
        """,
    )

    day_card(
        "📅 7/31 (五) Day 2：抵達墨爾本 ✈️",
        (None, area_sel in ["全部天數", "新加坡+墨爾本段"]),
        "墨爾本小柯林斯智選假日酒店",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">晚上</div>
        <div class="timeline-title">✈️ 抵達墨爾本機場 (MEL)</div>
        <div class="timeline-desc">出關後，搭乘機場 SkyBus 巴士或 Uber/計程車前往市區飯店。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Melbourne+Airport" target="_blank" class="map-btn">📍 墨爾本機場導航</a></div>
        <div class="timeline-item"><div class="timeline-time">21:00</div>
        <div class="timeline-title">🏨 入住飯店休息</div>
        <div class="timeline-desc">入住「墨爾本小柯林斯智選假日酒店」，調整時差。</div></div>
        """,
    )

    day_card(
        "📅 8/1 (六) Day 3：墨爾本優雅英倫風市區觀光 📷",
        (None, area_sel in ["全部天數", "新加坡+墨爾本段"]),
        "墨爾本小柯林斯智選假日酒店",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">09:30</div>
        <div class="timeline-title">☕ 塗鴉牆與弗林德斯街車站</div>
        <div class="timeline-desc">漫步霍西爾巷(Hosier Lane)欣賞塗鴉，朝聖「Flinders Street Station」。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Flinders+Street+Station+Melbourne" target="_blank" class="map-btn">📍 弗林德斯街車站導航</a></div>
        <div class="timeline-item"><div class="timeline-time">13:00</div>
        <div class="timeline-title">☕ 墨爾本咖啡文化體驗</div>
        <div class="timeline-desc">前往著名拱廊與小巷，點一杯道地 Flat White。</div></div>
        <div class="timeline-item"><div class="timeline-time">16:00</div>
        <div class="timeline-title">⛪ 聖保羅大教堂 & 尤利卡觀景台</div>
        <div class="timeline-desc">傍晚登上尤利卡觀景台俯瞰市區夜景。</div></div>
        """,
    )

    day_card(
        "📅 8/2 (日) Day 4：彩虹小屋、蒸汽火車與企鵝歸巢 🚗",
        (None, area_sel in ["全部天數", "新加坡+墨爾本段"]),
        "墨爾本小柯林斯智選假日酒店",
        ("timeline-tag-car-yes", "🟢 租車 (2台)"),
        """
        <div class="timeline-item"><div class="timeline-time">08:30</div>
        <div class="timeline-title">🚗 市區取車與出發</div>
        <div class="timeline-desc">兩位指定駕駛辦理取車手續，熟悉右駕操作後前往 Brighton Beach。</div></div>
        <div class="timeline-item"><div class="timeline-time">09:30</div>
        <div class="timeline-title">🌈 布萊頓彩虹小屋 (Brighton Bathing Boxes)</div>
        <div class="timeline-desc">五彩繽紛的沙灘更衣小屋，墨爾本必拍地標。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Brighton+Bathing+Boxes+Melbourne" target="_blank" class="map-btn">📍 彩虹小屋導航</a></div>
        <div class="timeline-item"><div class="timeline-time">12:00</div>
        <div class="timeline-title">🚂 普芬比利蒸汽火車 (Puffing Billy)</div>
        <div class="timeline-desc">體驗復古森林蒸汽火車，欣賞丹頓農山脈美景。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Puffing+Billy+Railway" target="_blank" class="map-btn">📍 蒸汽火車站導航</a></div>
        <div class="timeline-item"><div class="timeline-time">17:00</div>
        <div class="timeline-title">🐧 菲利普島企鵝歸巢 (Penguin Parade)</div>
        <div class="timeline-desc">看藍色小企鵝成群走回沙丘，晚間氣溫低，請加強防寒。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Penguin+Parade+Phillip+Island" target="_blank" class="map-btn">📍 企鵝歸巢中心導航</a></div>
        """,
    )

    day_card(
        "📅 8/3 (一) Day 5：世界最美海岸公路大洋路之旅 🚗",
        (None, area_sel in ["全部天數", "新加坡+墨爾本段"]),
        "大洋路旅客公園飯店",
        ("timeline-tag-car-yes", "🟢 租車 (2台)"),
        """
        <div class="timeline-item"><div class="timeline-time">08:00</div>
        <div class="timeline-title">🔑 退房，開往大洋路</div>
        <div class="timeline-desc">辦理退房，正式開往世界級奇景公路 Great Ocean Road。</div></div>
        <div class="timeline-item"><div class="timeline-time">11:00</div>
        <div class="timeline-title">🌊 大洋路紀念牌樓 & 奧特威角</div>
        <div class="timeline-desc">Memorial Arch 拍照留念，駕駛請注意休息。</div></div>
        <div class="timeline-item"><div class="timeline-time">15:00</div>
        <div class="timeline-title">🪨 十二門徒石 (Twelve Apostles)</div>
        <div class="timeline-desc">順便參觀洛克阿德峽谷(Loch Ard Gorge)。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Twelve+Apostles+Great+Ocean+Road" target="_blank" class="map-btn">📍 十二門徒石導航</a></div>
        <div class="timeline-item"><div class="timeline-time">18:00</div>
        <div class="timeline-title">🏕️ 入住大洋路營地公園</div>
        <div class="timeline-desc">入住「大洋路旅客公園飯店」，享受大自然環繞的夜晚。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Irving+St+Peterborough+VIC+3270" target="_blank" class="map-btn">📍 營地公園飯店導航</a></div>
        """,
    )

    day_card(
        "📅 8/4 (二) Day 6：大洋路回程、還車與飛往雪梨 ✈️",
        (None, area_sel in ["全部天數", "新加坡+墨爾本段", "雪梨段"]),
        "雪梨宜必思 (ibis Styles Sydney Central)",
        ("timeline-tag-car-yes", "🟢 還車 & 機場移動"),
        """
        <div class="timeline-item"><div class="timeline-time">09:00</div>
        <div class="timeline-title">🌊 退房，經內陸線返回墨爾本</div>
        <div class="timeline-desc">內陸線路程較平坦好開。</div></div>
        <div class="timeline-item"><div class="timeline-time">14:00</div>
        <div class="timeline-title">⛽ 滿油還車 (墨爾本機場)</div>
        <div class="timeline-desc">還車前在機場附近加油站加滿油。</div></div>
        <div class="timeline-item"><div class="timeline-time">16:40</div>
        <div class="timeline-title">✈️ 國內線航班：墨爾本飛雪梨</div>
        <div class="timeline-desc">16:40 - 18:10，前往澳洲第一大城雪梨。</div></div>
        <div class="timeline-item"><div class="timeline-time">19:30</div>
        <div class="timeline-title">🏨 入住雪梨飯店</div>
        <div class="timeline-desc">搭乘機場快線抵達市區，辦理「雪梨宜必思」入住。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=272-282+Pitt+St+Sydney+NSW+2000" target="_blank" class="map-btn">📍 雪梨宜必思導航</a></div>
        """,
    )

    day_card(
        "📅 8/5 (三) Day 7：雪梨歌劇院與復古月神樂園 🎡",
        (None, area_sel in ["全部天數", "雪梨段"]),
        "雪梨宜必思 (ibis Styles Sydney Central)",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">09:30</div>
        <div class="timeline-title">🏛️ 雪梨歌劇院導覽</div>
        <div class="timeline-desc">深入了解這座世界文化遺產的建築與音樂廳。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Sydney+Opera+House" target="_blank" class="map-btn">📍 雪梨歌劇院導航</a></div>
        <div class="timeline-item"><div class="timeline-time">13:00</div>
        <div class="timeline-title">🌉 雪梨港灣大橋與岩石區</div>
        <div class="timeline-desc">The Rocks 用午餐，欣賞歷史老街與大橋全景。</div></div>
        <div class="timeline-item"><div class="timeline-time">15:30</div>
        <div class="timeline-title">🎡 雪梨月神樂園 (Luna Park)</div>
        <div class="timeline-desc">搭渡輪前往對岸經典懷舊樂園。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Luna+Park+Sydney" target="_blank" class="map-btn">📍 月神樂園導航</a></div>
        """,
    )

    day_card(
        "📅 8/6 (四) Day 8：藍山國家公園一日遊 🏔️",
        (None, area_sel in ["全部天數", "雪梨段"]),
        "雪梨宜必思 (ibis Styles Sydney Central)",
        ("timeline-tag-car-no", "❌ 本日不租車 (一日遊包車)"),
        """
        <div class="timeline-item"><div class="timeline-time">08:00</div>
        <div class="timeline-title">🚐 一日遊集合出發</div>
        <div class="timeline-desc">搭乘觀光巴士直達世界遺產藍山國家公園。</div></div>
        <div class="timeline-item"><div class="timeline-time">10:00</div>
        <div class="timeline-title">🏔️ 三姊妹岩與景觀世界</div>
        <div class="timeline-desc">森林纜車、陡峭紅木森林鐵道與高空玻璃纜車。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Scenic+World+Blue+Mountains" target="_blank" class="map-btn">📍 藍山景觀世界導航</a></div>
        <div class="timeline-item"><div class="timeline-time">15:00</div>
        <div class="timeline-title">🦘 蘿拉小鎮文青散策</div>
        <div class="timeline-desc">Leura 小鎮，逛手工藝品店、享受下午茶，傍晚返回雪梨。</div></div>
        """,
    )

    day_card(
        "📅 8/7 (五) Day 9：雪梨賞鯨與市區悠閒漫步 🐋",
        (None, area_sel in ["全部天數", "雪梨段"]),
        "雪梨宜必思 (ibis Styles Sydney Central)",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">09:00</div>
        <div class="timeline-title">🐋 環形碼頭登船賞鯨</div>
        <div class="timeline-desc">冬季座頭鯨遷徙期，搭遊艇駛出雪梨港賞鯨。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Circular+Quay+Sydney" target="_blank" class="map-btn">📍 環形碼頭導航</a></div>
        <div class="timeline-item"><div class="timeline-time">13:30</div>
        <div class="timeline-title">🛍️ 雪梨塔與維多利亞女王大廈 (QVB)</div>
        <div class="timeline-desc">欣賞古老機械鐘，皮特街購買伴手禮。</div></div>
        """,
    )

    day_card(
        "📅 8/8 (六) Day 10：飛往昆士蘭陽光黃金海岸 ✈️",
        (None, area_sel in ["全部天數", "雪梨段", "昆士蘭段"]),
        "陽光海岸 Airbnb",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">09:30</div>
        <div class="timeline-title">🔑 退房前往雪梨機場</div>
        <div class="timeline-desc">搭火車前往雪梨國內機場。</div></div>
        <div class="timeline-item"><div class="timeline-time">12:20</div>
        <div class="timeline-title">✈️ 航班：雪梨飛黃金海岸</div>
        <div class="timeline-desc">12:20 - 13:40，飛抵昆士蘭度假天堂。</div></div>
        <div class="timeline-item"><div class="timeline-time">15:00</div>
        <div class="timeline-title">🌊 陽光海灘與 Airbnb 入住</div>
        <div class="timeline-desc">入住後步行至沙灘，漫步衝浪者天堂。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Surfers+Paradise+Beach" target="_blank" class="map-btn">📍 衝浪者天堂沙灘導航</a></div>
        """,
    )

    day_card(
        "📅 8/9 (日) Day 11：火車前進布里斯本與美食街狂歡 🦘",
        (None, area_sel in ["全部天數", "昆士蘭段"]),
        "布里斯本喬治飯店",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">10:00</div>
        <div class="timeline-title">🚂 搭火車前往布里斯本</div>
        <div class="timeline-desc">沿途欣賞陽光州鄉野景致。</div></div>
        <div class="timeline-item"><div class="timeline-time">13:00</div>
        <div class="timeline-title">🏢 布里斯本市區 & 喬治飯店入住</div>
        <div class="timeline-desc">放置行李，皇后街商業區漫步。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=345+George+St+Brisbane+City+QLD+4000" target="_blank" class="map-btn">📍 喬治飯店導航</a></div>
        <div class="timeline-item"><div class="timeline-time">17:30</div>
        <div class="timeline-title">🍱 北岸集裝箱美食街 (Eat Street Northshore)</div>
        <div class="timeline-desc">人氣美食貨櫃市集，現場樂團演奏。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Eat+Street+Northshore+Brisbane" target="_blank" class="map-btn">📍 Eat Street 導航</a></div>
        """,
    )

    day_card(
        "📅 8/10 (一) Day 12：近距離親近無尾熊與夕陽展望 🚗",
        (None, area_sel in ["全部天數", "昆士蘭段"]),
        "布里斯本喬治飯店",
        ("timeline-tag-car-yes", "🟢 租車 (2台)"),
        """
        <div class="timeline-item"><div class="timeline-time">08:30</div>
        <div class="timeline-title">🚗 布里斯本租車手續</div>
        <div class="timeline-desc">兩位指定駕駛辦理租車，這是澳洲最後一次自駕。</div></div>
        <div class="timeline-item"><div class="timeline-time">09:30</div>
        <div class="timeline-title">🐨 龍柏無尾熊動物園</div>
        <div class="timeline-desc">親手餵食袋鼠，近距離接觸無尾熊。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Lone+Pine+Koala+Sanctuary" target="_blank" class="map-btn">📍 龍柏無尾熊動物園導航</a></div>
        <div class="timeline-item"><div class="timeline-time">15:30</div>
        <div class="timeline-title">🏔️ 庫薩山觀景台 (Mount Coot-tha)</div>
        <div class="timeline-desc">眺望布里斯本全市絕美全景。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Mount+Coot-tha+Lookout" target="_blank" class="map-btn">📍 庫薩山觀景台導航</a></div>
        """,
    )

    day_card(
        "📅 8/11-8/12 Day 13：布里斯本市區最後巡禮、平安回台 ✈️",
        (None, area_sel in ["全部天數", "昆士蘭段"]),
        "夜宿機上",
        ("timeline-tag-car-no", "❌ 本日不租車"),
        """
        <div class="timeline-item"><div class="timeline-time">10:00</div>
        <div class="timeline-title">🏢 南岸公園 (South Bank Parklands)</div>
        <div class="timeline-desc">退房寄存行李，欣賞市區人造沙灘與摩天輪。</div></div>
        <div class="timeline-item"><div class="timeline-time">17:00</div>
        <div class="timeline-title">🍴 告別晚餐與領取行李</div>
        <div class="timeline-desc">回飯店提領行李，搭 Uber 或機場快線前往機場。</div></div>
        <div class="timeline-item"><div class="timeline-time">19:00</div>
        <div class="timeline-title">🛫 抵達布里斯本機場 (BNE)</div>
        <div class="timeline-desc">辦理行李託運、退稅手續。</div>
        <a href="https://www.google.com/maps/dir/?api=1&destination=Brisbane+Airport" target="_blank" class="map-btn">📍 布里斯本機場導航</a></div>
        <div class="timeline-item"><div class="timeline-time">22:15</div>
        <div class="timeline-title">✈️ 航班返航回台 (22:15 - 次日 05:10)</div>
        <div class="timeline-desc">夜宿機上，8/12 清晨 05:10 抵達桃園機場，結束旅程！</div></div>
        """,
    )

# ------------------------------------------
# ✈️ 航班
# ------------------------------------------
with tabs[1]:
    st.subheader("✈️ 航班資訊")
    st.caption("點開每個航班可以幫每位家人填座位與餐食，資料會自動存檔")

    FLIGHTS = [
        {"id": "f1", "label": "台北 → 新加坡", "date": "2026-07-30", "dep": "台北桃園 TPE", "arr": "新加坡樟宜 SIN"},
        {"id": "f2", "label": "新加坡 → 墨爾本", "date": "2026-07-30", "dep": "新加坡樟宜 SIN", "arr": "墨爾本 MEL（隔日抵達）"},
        {"id": "f3", "label": "墨爾本 → 雪梨（國內線）", "date": "2026-08-04", "dep": "墨爾本 MEL 16:40", "arr": "雪梨 SYD 18:10"},
        {"id": "f4", "label": "雪梨 → 黃金海岸（國內線）", "date": "2026-08-08", "dep": "雪梨 SYD 12:20", "arr": "黃金海岸 OOL 13:40"},
        {"id": "f5", "label": "布里斯本 → 台北", "date": "2026-08-11", "dep": "布里斯本 BNE 22:15", "arr": "台北桃園 TPE 次日05:10"},
    ]
    MEAL_OPTIONS = ["（未選）", "一般餐", "兒童餐", "素食餐", "海鮮餐", "其他"]

    for fl in FLIGHTS:
        with st.expander(f"{fl['label']}　{fl['date']}", expanded=False):
            st.markdown(f"**出發**：{fl['dep']}　→　**抵達**：{fl['arr']}")
            fl_pax = store["flight_pax"].setdefault(fl["id"], {})
            cols = st.columns(len(store["packing"]["members"]) or 1)
            for i, person in enumerate(store["packing"]["members"]):
                with cols[i]:
                    st.markdown(f"**{person}**")
                    existing = fl_pax.get(person, {"seat": "", "meal": "（未選）"})
                    seat = st.text_input("座位", value=existing.get("seat", ""), key=f"{fl['id']}_seat_{person}")
                    meal = st.selectbox("餐食", MEAL_OPTIONS,
                                         index=MEAL_OPTIONS.index(existing.get("meal", "（未選）")) if existing.get("meal", "（未選）") in MEAL_OPTIONS else 0,
                                         key=f"{fl['id']}_meal_{person}")
                    fl_pax[person] = {"seat": seat, "meal": meal}
            persist()

# ------------------------------------------
# 🚗 租車
# ------------------------------------------
with tabs[2]:
    st.subheader("🚗 租車自駕日程與車輛分配")
    md("""
        <div class="travel-card">
            <div class="alert-card-success"><strong>🚗 澳洲用車清單（全程共需 2 台中大型休旅車）</strong></div>
            <p><strong>第一段：墨爾本（彩虹小屋、蒸汽火車、菲利普島、大洋路）</strong></p>
            <ul>
                <li><strong>用車時間</strong>：8/2 (日) 08:30 ～ 8/4 (二) 14:00 還車（共3天）</li>
                <li><strong>取還車點</strong>：墨爾本市區取車 / 墨爾本機場 (MEL) 還車</li>
                <li><strong>車輛配置</strong>：2 台 5-7人座 SUV</li>
            </ul>
            <p><strong>第二段：布里斯本（龍柏無尾熊動物園、庫薩山觀景）</strong></p>
            <ul>
                <li><strong>用車時間</strong>：8/10 (一) 08:30 ～ 8/10 (一) 18:30 當日還車</li>
                <li><strong>取還車點</strong>：布里斯本市區營業所同點取還</li>
                <li><strong>車輛配置</strong>：2 台中型 SUV</li>
            </ul>
            <p><strong>⚠️ 自駕必備文件</strong>：台灣駕照正本、英文版國際駕照正本、主駕駛人信用卡、護照正本</p>
        </div>
        """)
    md("""
        <div class="travel-card">
            <div class="alert-card-info"><strong>🚨 靠左行駛！澳洲自駕安全守則</strong></div>
            <ol>
                <li>轉彎口訣：靠左行駛，右轉大彎，左轉小彎。</li>
                <li>圓環：進入前完全停下，禮讓右側已在圓環內的車輛。</li>
                <li>加油請加 Unleaded 91，勿加錯柴油。</li>
                <li>超速零容忍，測速照相嚴格。緊急電話 000 (Triple Zero)。</li>
                <li>黃昏與夜間郊區道路盡量避免駕駛，留意野生動物衝出。</li>
            </ol>
        </div>
        """)

# ------------------------------------------
# 🏨 飯店
# ------------------------------------------
with tabs[3]:
    st.subheader("🏨 住宿詳情")
    HOTELS = [
        ("墨爾本小柯林斯智選假日酒店", "7/31 入住 ～ 8/3 退房（3晚）", "589 Little Collins St, Melbourne VIC 3000", "+61-3-9111-8888"),
        ("大洋路旅客公園飯店", "8/3 入住 ～ 8/4 退房（1晚）", "Irving St, Peterborough VIC 3270", "+61-3-5598-8123"),
        ("雪梨宜必思 (ibis Styles Sydney Central)", "8/4 入住 ～ 8/8 退房（4晚）", "272-282 Pitt St, Sydney NSW 2000", "+61-2-9289-0000"),
        ("陽光海岸 Airbnb", "8/8 入住 ～ 8/9 退房（1晚）", "Surfers Paradise Blvd, Surfers Paradise QLD 4217", ""),
        ("布里斯本喬治飯店 (George Hotel Brisbane)", "8/9 入住 ～ 8/11 退房（2晚）", "345 George St, Brisbane City QLD 4000", "+61-7-3221-1111"),
    ]
    for name, dates, addr, phone in HOTELS:
        md(f"""
            <div class="travel-card">
                <div class="alert-card-info"><strong>🏨 {name}</strong></div>
                <p><strong>住退日期</strong>：{dates}{'　<strong>電話</strong>：' + phone if phone else ''}</p>
                <p>📍 {addr}</p>
                <a href="{maps_link(addr)}" target="_blank" class="map-btn">📍 Google地圖導航</a>
            </div>
            """)

# ------------------------------------------
# ☀️ 天氣
# ------------------------------------------
with tabs[4]:
    st.subheader("☀️ 目前所在地天氣")
    if get_geolocation is None:
        st.warning("需要安裝 streamlit-js-eval 套件才能自動定位（requirements.txt 已包含）。")
    else:
        loc = get_geolocation()
        if loc and "coords" in loc:
            lat = loc["coords"]["latitude"]
            lon = loc["coords"]["longitude"]
            try:
                geo = requests.get(
                    f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=zh",
                    timeout=8,
                ).json()
                city = geo.get("city") or geo.get("locality") or "目前位置"
                country = geo.get("countryName", "")
            except Exception:
                city, country = "目前位置", ""

            try:
                wx = requests.get(
                    f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto",
                    timeout=8,
                ).json()
                cw = wx["current_weather"]
                md(f"""<div class="weather-now">
                    <div>{city} {('· ' + country) if country else ''}</div>
                    <div class="temp">{round(cw['temperature'])}°C</div>
                    <div>風速 {cw['windspeed']} km/h</div>
                    </div>""")
                days = wx["daily"]["time"]
                cols = st.columns(min(5, len(days)))
                for i, c in enumerate(cols):
                    with c:
                        st.markdown(f"**{days[i][5:]}**")
                        st.write(f"{round(wx['daily']['temperature_2m_max'][i])}° / {round(wx['daily']['temperature_2m_min'][i])}°")
            except Exception:
                st.error("天氣資料取得失敗，請檢查網路連線")
        else:
            st.info("正在等待瀏覽器定位授權，請允許位置權限（若手機沒反應，重新整理頁面再試一次）。")

    st.write("---")
    st.markdown("##### ❄️ 澳洲 8 月冬季氣候參考")
    st.markdown(
        "- **墨爾本**：8°C - 14°C 🌧️（濕冷多雨，務必帶防風厚外套與雨傘）\n"
        "- **雪梨**：10°C - 17°C ⛅（氣候舒適，早晚偏冷）\n"
        "- **布里斯本/黃金海岸**：11°C - 22°C ☀️（溫暖晴朗，防曬必備）"
    )

# ------------------------------------------
# 🧳 行李
# ------------------------------------------
with tabs[5]:
    st.subheader("🧳 行李打包清單")
    packing = store["packing"]

    colA, colB = st.columns([2, 1])
    with colA:
        current = st.radio("選擇你自己的名字：", packing["members"], horizontal=True,
                            index=packing["members"].index(packing["current"]) if packing["current"] in packing["members"] else 0)
        packing["current"] = current
    with colB:
        new_name = st.text_input("新增家人姓名", key="new_member")
        if st.button("➕ 新增家人") and new_name.strip():
            if new_name.strip() not in packing["members"]:
                packing["members"].append(new_name.strip())
            packing["current"] = new_name.strip()
            persist()
            st.rerun()

    with st.expander("⚙️ 管理家人名單（改名 / 刪除）"):
        for m in list(packing["members"]):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.write(m)
            with c2:
                renamed = st.text_input("改名為", value="", key=f"rename_{m}", label_visibility="collapsed", placeholder="輸入新名字")
            with c3:
                disabled = len(packing["members"]) <= 1
                if st.button("🗑️ 刪除", key=f"del_{m}", disabled=disabled):
                    packing["members"].remove(m)
                    for it in packing["checks"].values():
                        it.pop(m, None)
                    for fp in store["flight_pax"].values():
                        fp.pop(m, None)
                    if packing["current"] == m:
                        packing["current"] = packing["members"][0]
                    persist()
                    st.rerun()
            if renamed.strip() and renamed.strip() != m:
                if renamed.strip() not in packing["members"]:
                    idx = packing["members"].index(m)
                    packing["members"][idx] = renamed.strip()
                    for it in packing["checks"].values():
                        if m in it:
                            it[renamed.strip()] = it.pop(m)
                    for fp in store["flight_pax"].values():
                        if m in fp:
                            fp[renamed.strip()] = fp.pop(m)
                    if packing["current"] == m:
                        packing["current"] = renamed.strip()
                    persist()
                    st.rerun()
        if len(packing["members"]) <= 1:
            st.caption("至少要保留一位家人，無法刪除最後一位。")

    st.write("---")
    checks = packing["checks"]
    for item in packing["items"]:
        checked = checks.get(item, {}).get(current, False)
        new_val = st.checkbox(item, value=checked, key=f"pack_{item}_{current}")
        if new_val != checked:
            checks.setdefault(item, {})[current] = new_val
            persist()

    new_item = st.text_input("新增打包項目", key="new_item")
    if st.button("➕ 新增項目") and new_item.strip():
        if new_item.strip() not in packing["items"]:
            packing["items"].append(new_item.strip())
        persist()
        st.rerun()

    total = len(packing["items"])
    done = sum(1 for it in packing["items"] if checks.get(it, {}).get(current, False))
    st.write("---")
    st.markdown(f"**🎒 {current} 的打包進度：{done} / {total}**")
    if total:
        st.progress(done / total)
    if total and done == total:
        st.balloons()
        st.success("🎉 太棒了！裝備已備齊，隨時準備出發！")

    st.write("---")
    st.markdown("##### 👥 全家打包總覽")
    if packing["items"] and packing["members"]:
        table_md = "| 項目 | " + " | ".join(packing["members"]) + " |\n"
        table_md += "|---|" + "---|" * len(packing["members"]) + "\n"
        for it in packing["items"]:
            row = [it]
            for m in packing["members"]:
                row.append("✅" if checks.get(it, {}).get(m, False) else "")
            table_md += "| " + " | ".join(row) + " |\n"
        st.markdown(table_md)

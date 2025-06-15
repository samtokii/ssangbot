import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from dotenv import load_dotenv
from flask import Flask
import threading

# Flask Ping 서버 (Uptime Ping용)
app = Flask(__name__)

@app.route('/')
def ping():
    return "Bot is alive!", 200

def run_flask():
    app.run(host="0.0.0.0", port=10000)

threading.Thread(target=run_flask).start()

# .env 파일에서 DISCORD_TOKEN 불러오기
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
파일_경로 = os.path.join(BASE_DIR, "잔소리봇_data.json")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

지출_목록 = {}
카테고리 = {}
잔소리 = {}

기본_잔소리 = {
    "기타": [
        "그걸 왜 샀는지는 묻지 않을게… 그냥 울자",
        "야 이 정도면 그냥 소비 천재다 진짜",
        "이 돈이면 한 달에 물 두 박스를 살 수 있어요 고객님",
        "어? 또 썼어? 대체 월급은 왜 받아?",
        "예상했어. 넌 또 지를 줄 알았어. 이제 놀랍지도 않아.",
        "이건 아마 다음달에도 후회할 예정~",
        "자기 합리화도 이쯤이면 예술이야",
        "지갑아 미안해… 이 말 매일 하네?",
        "지금 기분 좋지? 그거 잠깐이야",
        "그거 안 사도 잘 살 수 있었을 텐데 말이야~"
    ]
}

def 저장():
    with open(파일_경로, "w", encoding="utf-8") as f:
        json.dump({
            "지출_목록": 지출_목록,
            "카테고리": 카테고리,
            "잔소리": 잔소리
        }, f, ensure_ascii=False, indent=2)

def 불러오기():
    global 지출_목록, 카테고리, 잔소리
    if os.path.exists(파일_경로):
        with open(파일_경로, "r", encoding="utf-8") as f:
            데이터 = json.load(f)
            지출_목록 = 데이터.get("지출_목록", {})
            카테고리 = 데이터.get("카테고리", {})
            잔소리 = 데이터.get("잔소리", {})

@bot.event
async def on_ready():
    global 잔소리
    if not 잔소리:
        잔소리 = 기본_잔소리.copy()
    await tree.sync()
    print(f"✅ 봇 실행됨: {bot.user}")

@tree.command(name="지출", description="지출을 기록하고 잔소리를 들어보세요!")
@app_commands.describe(금액="지출 금액", 내용="지출 내용")
async def 지출(interaction: discord.Interaction, 금액: int, 내용: str):
    user_id = str(interaction.user.id)
    if user_id not in 지출_목록:
        지출_목록[user_id] = []
    지출_목록[user_id].append((금액, 내용))
    저장()

    카테고리명 = next((cat for cat, kws in 카테고리.items() if any(kw in 내용 for kw in kws)), None)
    잔소리문 = ""
    if 카테고리명 and 카테고리명 in 잔소리:
        잔소리문 = random.choice(잔소리[카테고리명])
    elif "기타" in 잔소리 and 잔소리["기타"]:
        잔소리문 = random.choice(잔소리["기타"])

    await interaction.response.send_message(f"💸 {금액}원 지출 등록됨! ({내용})\n{잔소리문}")

@tree.command(name="지출삭제", description="가장 최근 지출 내역을 삭제합니다")
async def 지출삭제(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    if user_id not in 지출_목록 or not 지출_목록[user_id]:
        await interaction.response.send_message("❌ 삭제할 지출 내역이 없습니다")
        return
    삭제된 = 지출_목록[user_id].pop()
    저장()
    await interaction.response.send_message(f"🗑️ 최근 지출 삭제됨: {삭제된[0]}원 ({삭제된[1]})")

@tree.command(name="지출선택삭제", description="선택한 순번의 지출을 삭제합니다")
@app_commands.describe(순번="지출 내역에서 삭제할 번호 (1부터 시작)")
async def 지출선택삭제(interaction: discord.Interaction, 순번: int):
    user_id = str(interaction.user.id)
    if user_id not in 지출_목록 or 순번 < 1 or 순번 > len(지출_목록[user_id]):
        await interaction.response.send_message("❌ 해당 번호의 지출이 없습니다")
        return
    삭제된 = 지출_목록[user_id].pop(순번 - 1)
    저장()
    await interaction.response.send_message(f"🗑️ {순번}번 지출 삭제됨: {삭제된[0]}원 ({삭제된[1]})")

@tree.command(name="지출전체삭제", description="모든 지출 내역을 삭제합니다")
async def 지출전체삭제(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    지출_목록[user_id] = []
    저장()
    await interaction.response.send_message("🧹 모든 지출 내역이 삭제되었습니다")

@tree.command(name="잔소리삭제", description="특정 카테고리의 잔소리를 삭제합니다")
@app_commands.describe(카테고리이름="카테고리 이름", 순번="삭제할 잔소리 번호 (1부터 시작)")
async def 잔소리삭제(interaction: discord.Interaction, 카테고리이름: str, 순번: int):
    if 카테고리이름 not in 잔소리 or 순번 < 1 or 순번 > len(잔소리[카테고리이름]):
        await interaction.response.send_message("❌ 해당 잔소리가 없습니다")
        return
    삭제된 = 잔소리[카테고리이름].pop(순번 - 1)
    저장()
    await interaction.response.send_message(f"🗯️ '{카테고리이름}' 카테고리의 잔소리 삭제됨: {삭제된}")

@tree.command(name="잔소리전체삭제", description="카테고리의 잔소리를 전부 삭제합니다")
@app_commands.describe(카테고리이름="카테고리 이름")
async def 잔소리전체삭제(interaction: discord.Interaction, 카테고리이름: str):
    if 카테고리이름 not in 잔소리:
        await interaction.response.send_message("❌ 해당 카테고리가 없습니다")
        return
    잔소리[카테고리이름] = []
    저장()
    await interaction.response.send_message(f"🧹 '{카테고리이름}' 카테고리의 잔소리를 모두 삭제했습니다")

# 기존 명령어들 유지 (도움말 등)
@tree.command(name="도움말", description="명령어 사용법을 알려줍니다")
async def 도움말(interaction: discord.Interaction):
    설명 = (
        "📌 사용 가능한 명령어:\n"
        "/지출 [금액] [내용] - 지출을 등록하고 잔소리를 들어요\n"
        "/지출삭제 - 가장 최근 지출 삭제\n"
        "/지출선택삭제 [번호] - 특정 지출 삭제\n"
        "/지출전체삭제 - 모든 지출 삭제\n"
        "/지출총합 - 총 지출 금액 확인\n"
        "/지출내역 - 지출 내역 모두 보기\n"
        "/카테고리추가 [이름] [키워드] - 자동 분류 키워드 추가\n"
        "/카테고리목록 - 키워드 목록 보기\n"
        "/잔소리추가 [카테고리] [문장] - 잔소리 추가\n"
        "/잔소리목록 - 잔소리 목록 보기\n"
        "/잔소리삭제 [카테고리] [번호] - 특정 잔소리 삭제\n"
        "/잔소리전체삭제 [카테고리] - 해당 잔소리 모두 삭제"
    )
    await interaction.response.send_message(설명)

불러오기()

if not TOKEN:
    raise ValueError("DISCORD_TOKEN이 .env에 설정되어 있지 않습니다.")
bot.run(TOKEN)

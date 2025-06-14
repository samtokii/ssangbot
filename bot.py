import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import random
from dotenv import load_dotenv

# .env 파일에서 DISCORD_TOKEN 불러오기
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# 파일 경로는 bot.py 위치 기준으로 절대 경로 사용
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
파일_경로 = os.path.join(BASE_DIR, "잔소리봇_data.json")

# 디스코드 설정
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# 데이터 저장 구조
지출_목록 = {}
카테고리 = {}
잔소리 = {}

기본_잔소리 = {
    "기타": [
        "와... 이건 진짜 안 쓰면 손해인 소비였겠다^^",
        "그 돈이면 햄버거를 몇 개를 먹었을까~? 생각은 해봤어?",
        "또 썼어? 진짜 안 질린다 넌",
        "이 정도면 돈한테 사과해야지. 이건 학대야",
        "넌 진짜 지름의 미학을 아는 사람이야... 통장만 불쌍하지ㅋ"
    ],
    "카페": [
        "또 커피야? 하루에 몇 잔 마시는 거야~",
        "아메리카노는 물이랑 뭐가 다르다고...",
        "카페인이 아니라 소비에 중독된 거 아냐?"
    ],
    "쇼핑": [
        "이건 꼭 필요한 거였을까...? 아니지?",
        "지금 사는 그 순간은 행복하지~ 그리고 나중에 후회하지~",
        "충동구매 전문가 인증 완료👏"
    ]
}

# 데이터 저장 및 불러오기

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

# 봇 실행 시 동기화 및 데이터 불러오기
@bot.event
async def on_ready():
    global 잔소리
    if not 잔소리:
        잔소리 = 기본_잔소리.copy()
    await tree.sync()
    print(f"✅ 봇 실행됨: {bot.user}")

# 명령어 정의
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

@tree.command(name="지출총합", description="지금까지 지출한 총 금액을 알려줍니다")
async def 지출총합(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    총합 = sum(금액 for 금액, _ in 지출_목록.get(user_id, []))
    await interaction.response.send_message(f"📊 {interaction.user.display_name}님의 총 지출 금액: {총합}원")

@tree.command(name="지출내역", description="지출한 내역을 모두 보여줍니다")
async def 지출내역(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    내역 = 지출_목록.get(user_id, [])
    if not 내역:
        await interaction.response.send_message("📭 지출 내역이 없습니다")
        return
    메시지 = f"🧾 {interaction.user.display_name}님의 지출 내역:\n"
    for i, (금액, 내용) in enumerate(내역, 1):
        메시지 += f"{i}. {금액}원 - {내용}\n"
    await interaction.response.send_message(메시지)

@tree.command(name="카테고리추가", description="새 카테고리와 키워드를 추가합니다")
@app_commands.describe(카테고리이름="예: 카페", 키워드="예: 커피")
async def 카테고리추가(interaction: discord.Interaction, 카테고리이름: str, 키워드: str):
    if 카테고리이름 not in 카테고리:
        카테고리[카테고리이름] = []
    카테고리[카테고리이름].append(키워드)
    저장()
    await interaction.response.send_message(f"📂 '{카테고리이름}' 카테고리에 '{키워드}' 키워드 추가됨")

@tree.command(name="잔소리추가", description="카테고리에 잔소리를 추가합니다")
@app_commands.describe(카테고리이름="카테고리 이름", 문장="추가할 잔소리 문장")
async def 잔소리추가(interaction: discord.Interaction, 카테고리이름: str, 문장: str):
    if 카테고리이름 not in 잔소리:
        잔소리[카테고리이름] = []
    잔소리[카테고리이름].append(문장)
    저장()
    await interaction.response.send_message(f"🗯️ '{카테고리이름}' 카테고리에 잔소리 추가됨: {문장}")

@tree.command(name="카테고리목록", description="등록된 카테고리와 키워드를 보여줍니다")
async def 카테고리목록(interaction: discord.Interaction):
    if not 카테고리:
        await interaction.response.send_message("등록된 카테고리가 없습니다")
        return
    메시지 = "📂 등록된 카테고리 목록:\n"
    for 카, 키들 in 카테고리.items():
        메시지 += f"- {카}: {', '.join(키들)}\n"
    await interaction.response.send_message(메시지)

@tree.command(name="잔소리목록", description="등록된 잔소리들을 보여줍니다")
async def 잔소리목록(interaction: discord.Interaction):
    if not 잔소리:
        await interaction.response.send_message("등록된 잔소리가 없습니다")
        return
    메시지 = "🗯️ 잔소리 목록:\n"
    for 카, 문장들 in 잔소리.items():
        메시지 += f"- {카}: {len(문장들)}개 등록됨\n"
    await interaction.response.send_message(메시지)

@tree.command(name="도움말", description="명령어 사용법을 알려줍니다")
async def 도움말(interaction: discord.Interaction):
    설명 = (
        "📌 사용 가능한 명령어:\n"
        "/지출 [금액] [내용] - 지출을 등록하고 잔소리를 들어요\n"
        "/지출삭제 - 가장 최근 지출 내역을 삭제해요\n"
        "/지출총합 - 지금까지의 총 지출을 확인해요\n"
        "/지출내역 - 내가 쓴 모든 지출 내역을 한눈에 확인해요\n"
        "/카테고리추가 [카테고리] [키워드] - 키워드로 자동 분류되게 해요\n"
        "/잔소리추가 [카테고리] [문장] - 특정 카테고리의 잔소리를 늘려요\n"
        "/카테고리목록 - 등록된 카테고리와 키워드를 보여줘요\n"
        "/잔소리목록 - 각 카테고리에 몇 개의 잔소리가 있는지 알려줘요"
    )
    await interaction.response.send_message(설명)

불러오기()

if not TOKEN:
    raise ValueError("DISCORD_TOKEN이 .env에 설정되어 있지 않습니다.")

bot.run(TOKEN)

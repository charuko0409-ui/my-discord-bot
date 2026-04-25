import discord
from discord.ext import commands
import math
from fractions import Fraction
import re
import os
import asyncio
import json
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

# 儲存使用者的提醒任務（用於重啟後恢復，可選）
reminder_tasks = {}

def parse_time(time_str: str) -> int:
    """解析時間字串，回傳總秒數"""
    total_seconds = 0
    # 匹配 數字 + 單位 (min/hour 等)
    patterns = [
        (r'(\d+)\s*(?:min|分鐘|分)', 60),      # 分鐘
        (r'(\d+)\s*(?:hour|小時|時|h)', 3600), # 小時
        (r'(\d+)\s*(?:day|天|日)', 86400),     # 天
    ]
    for pattern, multiplier in patterns:
        matches = re.findall(pattern, time_str, re.IGNORECASE)
        for match in matches:
            total_seconds += int(match) * multiplier
    if total_seconds == 0:
        # 如果沒有匹配到，嘗試當作分鐘（預設）
        try:
            total_seconds = int(time_str) * 60
        except:
            raise ValueError("時間格式錯誤，請用例如: 10 min, 2 hour")
    return total_seconds

# 成績檔案路徑
if os.getenv('RAILWAY_VOLUME_MOUNT_PATH'):
    SCORE_FILE = os.path.join(os.getenv('RAILWAY_VOLUME_MOUNT_PATH'), 'scores.json')
else:
    SCORE_FILE = 'scores.json'

def load_scores():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_scores(scores):
    with open(SCORE_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)

bot = commands.Bot(command_prefix='!', intents=intents)

HEARTBEAT_CHANNEL_ID = 1491740163246915666

async def send_heartbeat():
    try:
        print(f"機器人在 {len(bot.guilds)} 個伺服器中")
        for guild in bot.guilds:
            print(f"  - 伺服器: {guild.name} (ID: {guild.id})")
            channel = guild.get_channel(HEARTBEAT_CHANNEL_ID)
            if channel:
                print(f"    ✅ 找到目標頻道！頻道名稱: {channel.name}")
                await channel.send("💓 working！")
                print("✅ message sent")
                return
        print(f"❌ 在所有伺服器中都找不到頻道 ID: {HEARTBEAT_CHANNEL_ID}")
    except Exception as e:
        print(f"❌ 心跳發送失敗: {e}")

@bot.event
async def on_ready():
    print(f'✅ ボットがオンラインになりました！ ログイン名: {bot.user}')
    await bot.change_presence(activity=discord.Game(name="Shadowverse: Worlds Beyond"))
    print(f"\n機器人已加入以下 {len(bot.guilds)} 個伺服器：")
    for guild in bot.guilds:
        print(f"  - {guild.name} (ID: {guild.id})")
    
    while True:
        await send_heartbeat()
        await asyncio.sleep(420)

# ================== 核心計算函數 ==================
def binomial_prob(n: int, k: int, p: float = 1/3) -> float:
    """計算二項式機率 P(X=k)"""
    if k < 0 or k > n:
        return 0.0
    return math.comb(n, k) * (p ** k) * ((1-p) ** (n-k))

def cumulative_prob(n: int, k: int, condition: str, p: float = 1/3) -> float:
    """計算累積機率 P(Z >= k) 或 P(Z <= k)"""
    total = 0.0
    if condition == '>=':
        for i in range(k, n + 1):
            total += binomial_prob(n, i, p)
    elif condition == '<=':
        for i in range(0, k + 1):
            total += binomial_prob(n, i, p)
    return total

# ================== 指令 ==================
@bot.command(name='remindme')
async def remind_me(ctx, *, arg: str):
    """設定提醒 用法: !remindme 10 min 吃飯"""
    time_part = ""
    message_part = arg
    time_keywords = ['min', 'hour', 'day', '分', '小時', '時', '天', '日']
    words = arg.split()
    for i, word in enumerate(words):
        if any(kw in word for kw in time_keywords):
            time_part = ' '.join(words[:i+1])
            message_part = ' '.join(words[i+1:])
            break
    if not time_part:
        await ctx.send("❌ 格式錯誤！請使用: `!remindme 10 min 提醒內容`")
        return
    if not message_part:
        message_part = "（沒有指定內容）"
    
    try:
        seconds = parse_time(time_part)
    except ValueError as e:
        await ctx.send(f"❌ {e}")
        return
    
    if seconds <= 0:
        await ctx.send("❌ 時間必須大於 0")
        return
    if seconds > 30 * 86400:
        await ctx.send("❌ 時間太長了，最長30天")
        return
    
    from datetime import timezone, timedelta as td
    tz_gmt8 = timezone(td(hours=8))
    remind_time_local = datetime.now(tz_gmt8) + timedelta(seconds=seconds)
    
    await ctx.send(f"✅ 設定提醒！會在 {remind_time_local.strftime('%Y-%m-%d %H:%M:%S')} (GMT+8) 私訊你：\n「{message_part}」")
    
    async def reminder_task():
        await asyncio.sleep(seconds)
        try:
            user = ctx.author
            await user.send(f"🔔 **提醒！**\n你設定的時間到了：\n「{message_part}」\n（設定於 {remind_time_local.strftime('%Y-%m-%d %H:%M:%S')} GMT+8）")
        except discord.Forbidden:
            await ctx.send(f"⚠️ {ctx.author.mention} 無法私訊你，請檢查隱私設定，允許伺服器成員私訊。")
        except Exception as e:
            print(f"提醒發送失敗: {e}")
            await ctx.send(f"⚠️ 提醒發送失敗：{e}")
    
    asyncio.create_task(reminder_task())

@bot.command(name='prob')
async def probability(ctx, *, arg: str):
    """
    計算逐次隨機選擇下 Z 的機率
    格式：
    !prob N = Z
    !prob N >= Z
    !prob N <= Z
    !prob N table
    """
    arg_lower = arg.lower().strip()
    numbers = re.findall(r'\d+', arg)
    
    if len(numbers) < 1:
        await ctx.send("❌ 使い方：\n`!prob 14 = 3`\n`!prob 14 >= 7`\n`!prob 14 table`")
        return
    
    try:
        N = int(numbers[0])
        
        # table mode
        if 'table' in arg_lower:
            await show_table(ctx, N)
            return
        
        if len(numbers) < 2:
            await ctx.send("❌ 使い方：\n`!prob 14 = 3`\n`!prob 14 >= 7`\n`!prob 14 table`")
            return
        
        K = int(numbers[-1])
        
        if '>=' in arg or '=>' in arg:
            condition = '>='
        elif '<=' in arg or '=<' in arg:
            condition = '<='
        else:
            condition = '='
            
    except ValueError:
        await ctx.send("❌ 正しい数字を入力してください！")
        return

    if N < 0:
        await ctx.send("❌ N は 0 以上である必要があります！")
        return
    
    if condition == '=' and (K < 0 or K > N):
        await ctx.send(f"❌ Z は 0～{N} の間である必要があります！")
        return
    
    if condition == '=':
        prob = binomial_prob(N, K)
        cond_str = f"Z = {K}"
        prob_float = prob
    elif condition == '>=':
        prob = cumulative_prob(N, K, '>=')
        cond_str = f"Z ≥ {K}"
        prob_float = prob
    else:  # '<='
        prob = cumulative_prob(N, K, '<=')
        cond_str = f"Z ≤ {K}"
        prob_float = prob
    
    percent = prob_float * 100
    
    # 分數表示
    prob_frac = Fraction(prob_float).limit_denominator(10000)
    
    if prob_float < 0.001:
        prob_display = f"{prob_float:.8f}"
        percent_display = f"{percent:.4f}%"
    else:
        prob_display = f"{prob_float:.4f}"
        percent_display = f"{percent:.2f}%"

    response = (
        f"**X+Y+Z = {N} かつ {cond_str} の確率**\n"
        f"(毎回 X,Y,Z からランダムに選択、{N}回繰り返し)\n"
        f"確率：`{prob_frac}` = `{prob_display}`（{percent_display}）\n"
    )

    await ctx.send(response)

async def show_table(ctx, n: int):
    """顯示所有 Z 值的機率表（二項式分布）"""
    if n < 0:
        await ctx.send("❌ N は 0 以上である必要があります！")
        return
    if n > 50:
        await ctx.send("⚠️ N が大きすぎます（最大50まで推奨）")
        return
    
    result = f"**X+Y+Z = {n} の確率分布表（逐次ランダム選択）**\n```\n"
    result += " Z │    確率    │  百分率\n"
    result += "───┼────────────┼─────────\n"
    
    for z in range(n + 1):
        prob = binomial_prob(n, z)
        percent = prob * 100
        result += f"{z:2} │ {prob:.6f} │ {percent:6.2f}%\n"
        
        if len(result) > 1500 and z < n:
            result += "```\n（続きは次のメッセージへ...）"
            await ctx.send(result)
            result = f"**続き（Z = {z+1} から）**\n```\n"
            result += " Z │    確率    │  百分率\n"
            result += "───┼────────────┼─────────\n"
    
    result += "```"
    await ctx.send(result)

@bot.command(name='expect')
async def expected(ctx, N: int):
    """計算 Z 的期望值"""
    exp = N / 3
    await ctx.send(f"**X+Y+Z = {N} のとき、Z の期待値: {exp:.2f}**")

@bot.command(name='simulate')
async def simulate(ctx, N: int, condition: str, Z: int, trials: int = 10000):
    """模擬逐次隨機選擇"""
    import random
    import time
    
    if trials > 100000:
        trials = 100000
    elif trials < 100:
        trials = 100
    
    if condition not in ['=', '>=', '<=']:
        await ctx.send("❌ 条件は =, >=, <= を使用してください")
        return
    
    if N < 0:
        await ctx.send("❌ N は 0 以上である必要があります")
        return
    
    # 理論確率
    if condition == '=':
        prob_theory = binomial_prob(N, Z)
        cond_str = f"Z = {Z}"
    elif condition == '>=':
        prob_theory = cumulative_prob(N, Z, '>=')
        cond_str = f"Z ≥ {Z}"
    else:
        prob_theory = cumulative_prob(N, Z, '<=')
        cond_str = f"Z ≤ {Z}"
    
    await ctx.send(f"🎲 シミュレーション中...（{trials:,}回）")
    start_time = time.time()
    
    count = 0
    for _ in range(trials):
        z = 0
        for _ in range(N):
            if random.random() < 1/3:  # Z 被選中的機率
                z += 1
        
        if condition == '=':
            if z == Z:
                count += 1
        elif condition == '>=':
            if z >= Z:
                count += 1
        else:
            if z <= Z:
                count += 1
    
    prob_sim = count / trials
    elapsed = time.time() - start_time
    
    response = (
        f"**📊 シミュレーション結果：X+Y+Z = {N} かつ {cond_str}**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎲 シミュレーション回数：**{trials:,}**回\n"
        f"✅ 条件一致回数：**{count:,}**回\n"
        f"⏱️ 処理時間：**{elapsed*1000:.0f}ms**\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 **シミュレーション確率**：`{prob_sim:.4f}`（{prob_sim*100:.2f}%）\n"
        f"📐 **理論確率**：`{prob_theory:.4f}`（{prob_theory*100:.2f}%）\n"
    )
    
    await ctx.send(response)



@bot.command(name='helpc')
async def help_command(ctx):
    embed = discord.Embed(
        title="📊 クリスタル計算機 - ヘルプ",
        description="毎回 X,Y,Z からランダムに選択（各1/3）、N回繰り返すときのZの確率",
        color=0x00ff00
    )
    embed.add_field(
        name="🎲 確率計算",
        value="`!prob N = Z`\n`!prob N >= Z`\n`!prob N <= Z`\n`!prob N table`",
        inline=False
    )
    embed.add_field(
        name="🧠 期待値",
        value="`!expect N`",
        inline=False
    )
    embed.add_field(
        name="🎲 シミュレーション",
        value="`!simulate N 条件 Z 回数`\n例: `!simulate 14 = 3 10000`",
        inline=False
    )

    embed.set_footer(text="Shadowverse ダメージ計算用 | モデル: 逐次ランダム選択")
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))

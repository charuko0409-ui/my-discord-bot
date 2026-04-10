import discord
from discord.ext import commands
import math
from fractions import Fraction
import re
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  # 確保可以讀取伺服器資訊

bot = commands.Bot(command_prefix='!', intents=intents)

HEARTBEAT_CHANNEL_ID = 1491740163246915666  # 你的頻道ID

async def send_heartbeat():
    """發送心跳訊息並顯示除錯資訊"""
    try:
        # 檢查機器人看到了哪些伺服器
        print(f"機器人在 {len(bot.guilds)} 個伺服器中")
        for guild in bot.guilds:
            print(f"  - 伺服器: {guild.name} (ID: {guild.id})")
            # 檢查這個伺服器裡有沒有目標頻道
            channel = guild.get_channel(HEARTBEAT_CHANNEL_ID)
            if channel:
                print(f"    ✅ 找到目標頻道！頻道名稱: {channel.name}")
                await channel.send("💓 ボットは稼働中です！")
                print("✅ 心跳發送成功")
                return
        
        # 如果找不到頻道
        print(f"❌ 在所有伺服器中都找不到頻道 ID: {HEARTBEAT_CHANNEL_ID}")
        print("請確認：")
        print("1. 機器人在正確的伺服器裡")
        print("2. 頻道 ID 是正確的（從頻道右鍵複製）")
        print("3. 機器人有權限讀取該頻道")
        
    except Exception as e:
        print(f"❌ 心跳發送失敗: {e}")

@bot.event
async def on_ready():
    print(f'✅ ボットがオンラインになりました！ ログイン名: {bot.user}')
    
    # 顯示機器人所在的所有伺服器
    print(f"\n機器人已加入以下 {len(bot.guilds)} 個伺服器：")
    for guild in bot.guilds:
        print(f"  - {guild.name} (ID: {guild.id})")
    
    # 啟動心跳循環（每5分鐘）
    while True:
        await send_heartbeat()
        await asyncio.sleep(300)  # 5分鐘

# ================== 你的 !prob 指令 ==================
@bot.command(name='prob')
async def probability(ctx, *, arg: str):
    numbers = re.findall(r'\d+', arg)
    if len(numbers) < 2:
        await ctx.send("❌ 使い方：\n`!prob 14 >= 7`\n`!prob 14 <= 5`\n`!prob 14 = 3`\n`!prob 14 3`")
        return
    
    try:
        N = int(numbers[0])
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
        await ctx.send("❌ 合計は0以上である必要があります！")
        return
    
    if condition == '=' and (K < 0 or K > N):
        await ctx.send(f"❌ Zの値は 0～{N} の間である必要があります！")
        return

    total = math.comb(N + 2, 2)
    
    if condition == '=':
        favorable = N - K + 1
        cond_str = f"Z = {K}"
    elif condition == '>=':
        if K > N:
            favorable = 0
        else:
            favorable = sum(N - z + 1 for z in range(K, N + 1))
        cond_str = f"Z ≥ {K}"
    else:
        if K < 0:
            favorable = 0
        else:
            favorable = sum(N - z + 1 for z in range(0, min(K, N) + 1))
        cond_str = f"Z ≤ {K}"
    
    prob_frac = Fraction(favorable, total)
    prob_float = float(prob_frac)
    percent = prob_float * 100

    response = (
        f"**X + Y + Z = {N} かつ {cond_str} の確率**\n"
        f"組み合わせ数：{favorable} / {total}\n"
        f"確率：`{prob_frac}` = `{prob_float:.4f}`（{percent:.2f}%）\n\n"
    
    )
    
    await ctx.send(response)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))

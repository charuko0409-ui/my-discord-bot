import discord
from discord.ext import commands
import math
from fractions import Fraction
import re
import os

# ================== 設定 ==================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ ボットがオンラインになりました！ ログイン名: {bot.user}')

@bot.command(name='prob')
async def probability(ctx, *, arg: str):
    # 対応形式：
    # !prob 14 >= 7
    # !prob 14 <= 5
    # !prob 14 = 3
    # !prob 14 3 (省略形、等しい)
    
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

# ================== 啟動 ==================
bot.run(os.getenv('DISCORD_BOT_TOKEN'))

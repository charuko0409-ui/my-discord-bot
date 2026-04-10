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
    print(f'✅ Bot 已上線！登入為 {bot.user}')

@bot.command(name='prob')
async def probability(ctx, *, arg: str):
    # 支援多種格式：
    # !prob 14 >= 7
    # !prob 14 <= 5
    # !prob 14 = 3
    # !prob 14 3 (簡寫，等於)
    # !prob x+y+z=14 z=3
    
    # 提取所有數字
    numbers = re.findall(r'\d+', arg)
    if len(numbers) < 2:
        await ctx.send("❌ 使用方式：\n`!prob 14 >= 7`\n`!prob 14 <= 5`\n`!prob 14 = 3`\n`!prob 14 3`")
        return
    
    try:
        N = int(numbers[0])   # 總和
        K = int(numbers[-1])  # Z 的值
        
        # 判斷條件類型
        if '>=' in arg or '=>' in arg:
            condition = '>='
        elif '<=' in arg or '=<' in arg:
            condition = '<='
        elif '=' in arg or len(numbers) == 2:
            condition = '='
        else:
            condition = '='
            
    except ValueError:
        await ctx.send("❌ 請輸入正確的數字！")
        return

    # 錯誤檢查
    if N < 0:
        await ctx.send("❌ 總和不能為負數！")
        return
    
    if condition == '=' and (K < 0 or K > N):
        await ctx.send(f"❌ 條件錯誤！Z 值必須介於 0～{N} 之間。")
        return

    # 計算
    total = math.comb(N + 2, 2)          # 總組合數
    
    if condition == '=':
        favorable = N - K + 1
        cond_str = f"Z = {K}"
        
    elif condition == '>=':
        if K > N:
            favorable = 0
        else:
            favorable = sum(N - z + 1 for z in range(K, N + 1))
        cond_str = f"Z ≥ {K}"
        
    else:  # condition == '<='
        if K < 0:
            favorable = 0
        else:
            favorable = sum(N - z + 1 for z in range(0, min(K, N) + 1))
        cond_str = f"Z ≤ {K}"
    
    prob_frac = Fraction(favorable, total)
    prob_float = float(prob_frac)
    percent = prob_float * 100

    # 輸出
    response = (
        f"**X + Y + Z = {N} 且 {cond_str} 的機率**\n"
        f"組合數：{favorable} / {total}\n"
        f"機率：`{prob_frac}` = `{prob_float:.4f}`（{percent:.2f}%）\n\n"
    )
    
    await ctx.send(response)

# ================== 啟動 ==================
bot.run(os.getenv('DISCORD_BOT_TOKEN'))
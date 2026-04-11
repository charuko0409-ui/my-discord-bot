import discord
from discord.ext import commands
import math
from fractions import Fraction
import re
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True  # server read

bot = commands.Bot(command_prefix='!', intents=intents)

HEARTBEAT_CHANNEL_ID = 1491740163246915666  # channal ID

async def send_heartbeat():
    """Display message check"""
    try:
        # checking server
        print(f"機器人在 {len(bot.guilds)} 個伺服器中")
        for guild in bot.guilds:
            print(f"  - 伺服器: {guild.name} (ID: {guild.id})")
            # check whether bot is in destinated channel
            channel = guild.get_channel(HEARTBEAT_CHANNEL_ID)
            if channel:
                print(f"    ✅ 找到目標頻道！頻道名稱: {channel.name}")
                await channel.send("💓 working！")
                print("✅ message sent")
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
        # set bot activity
    await bot.change_presence(activity=discord.Game(name="Shadowverse: Worlds Beyond"))
    # display bot server
    print(f"\n機器人已加入以下 {len(bot.guilds)} 個伺服器：")
    for guild in bot.guilds:
        print(f"  - {guild.name} (ID: {guild.id})")
    
    # ping
    while True:
        await send_heartbeat()
        await asyncio.sleep(420)  # 7 min

# ================== 你的 !prob 指令 ==================
@bot.command(name='helpc')
async def help_command(ctx):
    """Display all command"""
    embed = discord.Embed(
        title="📊 クリスタル計算機 - ヘルプ",
        description="X+Y+Z = N のとき、Zの確率を計算します",
        color=0x00ff00
    )
    
    embed.add_field(
        name="🎲 單一Z值確率",
        value="`!prob N = Z`\n例: `!prob 14 = 3`\n\n"
              "`!prob N >= Z`\n例: `!prob 14 >= 7`\n\n"
              "`!prob N <= Z`\n例: `!prob 14 <= 5`",
        inline=False
    )
    
    embed.add_field(
        name="📋 全Z值一覧（表格）",
        value="`!prob N table`\n例: `!prob 14 table`",
        inline=False
    )

    embed.add_field(
        name="🎲 シミュレーション",
        value="`!simulate N 条件 Z 回数`\n例: `!simulate 14 = 3 10000`\n"
              "例: `!simulate 14 >= 7 50000`",
        inline=False
    )
    
    embed.set_footer(text="Shadowverse ダメージ計算用 | 作成者：X@mikasuke_0308 ")
    
    await ctx.send(embed=embed)
@bot.command(name='simulate')
async def simulate(ctx, N: int, condition: str, Z: int, trials: int = 10000):
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
    
    # 理論確率の計算
    total = math.comb(N + 2, 2)
    
    if condition == '=':
        favorable_theory = N - Z + 1
        cond_str = f"Z = {Z}"
    elif condition == '>=':
        if Z > N:
            favorable_theory = 0
        else:
            favorable_theory = sum(N - z + 1 for z in range(Z, N + 1))
        cond_str = f"Z ≥ {Z}"
    else:
        if Z < 0:
            favorable_theory = 0
        else:
            favorable_theory = sum(N - z + 1 for z in range(0, min(Z, N) + 1))
        cond_str = f"Z ≤ {Z}"
    
    prob_theory = favorable_theory / total
    
    await ctx.send(f"🎲 シミュレーション中...（{trials:,}回）")
    start_time = time.time()
    
    count = 0
    
    # 修正：直接均勻選取所有 (X,Y,Z) 組合
    # 方法：將所有組合視為從 0 到 total-1 的整數，再映射回 (X,Y,Z)
    for _ in range(trials):
        # 隨機選取一個組合編號（0 到 total-1）
        combo_num = random.randint(0, total - 1)
        
        # 將組合編號轉換成 (X,Y,Z)
        # 先找 Z：Z 對應的起始編號 = C(N+2,2) - C(N-Z+2,2)
        z = 0
        remaining = total
        for z_candidate in range(N + 1):
            count_for_z = N - z_candidate + 1
            if combo_num < count_for_z:
                z = z_candidate
                break
            else:
                combo_num -= count_for_z
        
        # 再找 X（Y = 剩餘）
        x = combo_num
        y = N - z - x
        
        # 條件チェック
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

@bot.command(name='prob')
async def probability(ctx, *, arg: str):
    # 支援格式：
    # !prob 14 >= 7
    # !prob 14 <= 5
    # !prob 14 = 3
    # !prob 14 3
    # !prob 14 table  ← new z table
    
    arg_lower = arg.lower().strip()
    numbers = re.findall(r'\d+', arg)
    
    if len(numbers) < 1:
        await ctx.send("❌ 使い方：\n`!prob 14 >= 7`\n`!prob 14 table`")
        return
    
    try:
        N = int(numbers[0])
        
        # table mode
        if 'table' in arg_lower:
            await show_table(ctx, N)
            return
        
        # chance calculate
        if len(numbers) < 2:
            await ctx.send("❌ 使い方：\n`!prob 14 >= 7`\n`!prob 14 = 3`\n`!prob 14 table`")
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


async def show_table(ctx, n: int):
    """display z table"""
    
    if n < 0:
        await ctx.send("❌ 合計は0以上である必要があります！")
        return
    if n > 50:
        await ctx.send("⚠️ N が大きすぎます（最大50まで推奨）")
        return
    
    total = math.comb(n + 2, 2)
    
    result = f"**X + Y + Z = {n} の確率分布表**\n```\n"
    result += " Z │   確率   │  百分率\n"
    result += "───┼──────────┼─────────\n"
    
    for z in range(n + 1):
        favorable = n - z + 1
        prob = favorable / total
        percent = prob * 100
        result += f"{z:2} │ {prob:.4f} │ {percent:6.2f}%\n"
        
        # 避免訊息太長
        if len(result) > 1500 and z < n:
            result += "```\n（続きは次のメッセージへ...）"
            await ctx.send(result)
            result = f"**続き（Z = {z+1} から）**\n```\n"
            result += " Z │   確率   │  百分率\n"
            result += "───┼──────────┼─────────\n"
    
    result += "```"
    await ctx.send(result)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))

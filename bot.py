import discord
from discord.ext import commands
import math
from fractions import Fraction
import re
import os
import asyncio
import json

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

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
    
    response = (
        f"**X+Y+Z = {N} かつ {cond_str} の確率**\n"
        f"(毎回 X,Y,Z からランダムに選択、{N}回繰り返し)\n"
        f"確率：`{prob_frac}` = `{prob_float:.4f}`（{percent:.2f}%）\n"
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

# ================== 成績管理指令 ==================
@bot.command(name='addscore')
@commands.has_permissions(administrator=True)
async def add_score(ctx, player: str, score: str):
    scores = load_scores()
    scores[player] = score
    save_scores(scores)
    await ctx.send(f"✅ `{player}` の成績を `{score}` に登録しました！")

@bot.command(name='score', aliases=['search'])
async def get_score(ctx, player: str):
    scores = load_scores()
    if player in scores:
        await ctx.send(f"📊 `{player}` の成績: **{scores[player]}**")
    else:
        await ctx.send(f"❌ `{player}` の成績は見つかりませんでした。")

@bot.command(name='allscore')
async def all_scores(ctx):
    scores = load_scores()
    if not scores:
        await ctx.send("📭 まだ成績は登録されていません。")
        return
    
    def sort_key(item):
        player, score = item
        if '-' in score:
            parts = score.split('-')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                wins = int(parts[0])
                losses = int(parts[1])
                return (-wins, losses)
        return (float('inf'), score)
    
    sorted_items = sorted(scores.items(), key=sort_key)
    message = "**📊 選手成績一覧（勝率順）**\n"
    for player, score in sorted_items:
        message += f"• {player}: {score}\n"
        if len(message) > 1900:
            await ctx.send("⚠️ 選手が多すぎるため、一部のみ表示します。")
            break
    await ctx.send(message)

@bot.command(name='delscore')
@commands.has_permissions(administrator=True)
async def delete_score(ctx, player: str):
    scores = load_scores()
    if player in scores:
        del scores[player]
        save_scores(scores)
        await ctx.send(f"🗑️ `{player}` の成績を削除しました。")
    else:
        await ctx.send(f"❌ `{player}` は見つかりません。")

@bot.command(name='clearallscore')
@commands.has_permissions(administrator=True)
async def clear_all_scores(ctx):
    scores = load_scores()
    if scores:
        save_scores({})
        await ctx.send("✅ **すべての選手成績を削除しました。**")
    else:
        await ctx.send("📭 すでに成績データは空です。")

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
    embed.add_field(
        name="📊 成績管理",
        value="`!score 選手名` `!addscore 選手名 成績` `!allscore` `!delscore` `!clearallscore`",
        inline=False
    )
    embed.set_footer(text="Shadowverse ダメージ計算用 | モデル: 逐次ランダム選択")
    await ctx.send(embed=embed)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))

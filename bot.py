import os
import json
import random
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# M8 TOURNAMENT BOT
# ============================================================

intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

DATA_FILE = Path("tournament_data.json")

TANK_CLASSES = [
    "🛡️ Heavy Tank",
    "⚔️ Medium Tank",
    "⚡ Light Tank",
    "🎯 Tank Destroyer"
]

MAPS = [
    "Mines",
    "Himmelsdorf",
    "Normandy",
    "Canal",
    "Rockfield",
    "Desert Sands",
    "Middleburg",
    "Fort Despair"
]


# ============================================================
# DATA
# ============================================================

def load_data():
    if not DATA_FILE.exists():
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


data = load_data()


def get_guild_data(guild_id):
    guild_id = str(guild_id)

    if guild_id not in data:
        data[guild_id] = {
            "players": [],
            "started": False,
            "rounds": [],
            "champion": None
        }

    return data[guild_id]


def player_name(guild, user_id):
    if not user_id:
        return "TBD"

    member = guild.get_member(int(user_id))

    if member:
        return member.display_name

    return f"Player {user_id}"


# ============================================================
# BOT READY
# ============================================================

@bot.event
async def on_ready():
    bot.add_view(TournamentRegistrationView())
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} Slash Commands synchronized.")
    except Exception as e:
        print(f"❌ Slash Command Sync Error: {e}")

    print("------------------------------------------")
    print("🏆 M8 TOURNAMENT BOT ONLINE")
    print(f"🤖 Logged in as: {bot.user}")
    print("------------------------------------------")


# ============================================================
# REGISTER
# ============================================================

@bot.tree.command(
    name="register",
    description="Register yourself for the M8 Tournament"
)
async def register(interaction: discord.Interaction):

    guild_data = get_guild_data(interaction.guild.id)

    if guild_data["started"]:
        await interaction.response.send_message(
            "❌ Registration is closed. The tournament has already started.",
            ephemeral=True
        )
        return

    user_id = str(interaction.user.id)

    if user_id in guild_data["players"]:
        await interaction.response.send_message(
            "⚠️ You are already registered.",
            ephemeral=True
        )
        return

    guild_data["players"].append(user_id)
    save_data()

    embed = discord.Embed(
        title="✅ M8 TOURNAMENT REGISTRATION",
        description=f"{interaction.user.mention} has joined the tournament!"
    )

    embed.add_field(
        name="👥 Registered Players",
        value=str(len(guild_data["players"]))
    )

    embed.set_footer(text="M8 Community Tournament")

    await interaction.response.send_message(embed=embed)


# ============================================================
# UNREGISTER
# ============================================================

@bot.tree.command(
    name="unregister",
    description="Leave the M8 Tournament registration"
)
async def unregister(interaction: discord.Interaction):

    guild_data = get_guild_data(interaction.guild.id)

    if guild_data["started"]:
        await interaction.response.send_message(
            "❌ The tournament has already started.",
            ephemeral=True
        )
        return

    user_id = str(interaction.user.id)

    if user_id not in guild_data["players"]:
        await interaction.response.send_message(
            "⚠️ You are not registered.",
            ephemeral=True
        )
        return

    guild_data["players"].remove(user_id)
    save_data()

    await interaction.response.send_message(
        f"❌ {interaction.user.mention} left the tournament."
    )


# ============================================================
# PLAYERS
# ============================================================

@bot.tree.command(
    name="players",
    description="Show all registered tournament players"
)
async def players(interaction: discord.Interaction):

    guild_data = get_guild_data(interaction.guild.id)

    players_list = guild_data["players"]

    if not players_list:
        await interaction.response.send_message(
            "❌ Nobody is registered yet."
        )
        return

    text = ""

    for index, user_id in enumerate(players_list, 1):
        text += f"**{index}.** <@{user_id}>\n"

    embed = discord.Embed(
        title="👥 M8 TOURNAMENT PLAYERS",
        description=text
    )

    embed.set_footer(
        text=f"{len(players_list)} players registered"
    )

    await interaction.response.send_message(embed=embed)


# ============================================================
# START TOURNAMENT
# ============================================================

@bot.tree.command(
    name="start_tournament",
    description="Start and randomly draw the M8 Tournament"
)
async def start_tournament(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Only tournament staff can use this command.",
            ephemeral=True
        )
        return

    guild_data = get_guild_data(interaction.guild.id)

    players = guild_data["players"].copy()

    allowed_sizes = [4, 8, 16, 32]

    if len(players) not in allowed_sizes:
        await interaction.response.send_message(
            "❌ Tournament requires exactly **4, 8, 16 or 32 players**.\n"
            f"Currently registered: **{len(players)}**",
            ephemeral=True
        )
        return

    random.shuffle(players)

    rounds = []

    # ROUND 1
    round_one = []

    for i in range(0, len(players), 2):

        round_one.append({
            "p1": players[i],
            "p2": players[i + 1],
            "winner": None,
            "score": None
        })

    rounds.append(round_one)

    # FUTURE ROUNDS
    matches = len(round_one) // 2

    while matches >= 1:

        new_round = []

        for _ in range(matches):

            new_round.append({
                "p1": None,
                "p2": None,
                "winner": None,
                "score": None
            })

        rounds.append(new_round)

        matches //= 2

    guild_data["rounds"] = rounds
    guild_data["started"] = True
    guild_data["champion"] = None

    save_data()

    embed = discord.Embed(
        title="🏆 M8 COMMUNITY TOURNAMENT",
        description="The tournament bracket has been drawn!"
    )

    first_round = ""

    for index, match in enumerate(round_one, 1):

        first_round += (
            f"**Match #{index}**\n"
            f"<@{match['p1']}> ⚔️ <@{match['p2']}>\n\n"
        )

    embed.add_field(
        name="⚔️ FIRST ROUND",
        value=first_round,
        inline=False
    )

    embed.add_field(
        name="👥 Players",
        value=str(len(players))
    )

    embed.add_field(
        name="🎲 Draw",
        value="Random"
    )

    embed.set_footer(
        text="Use /bracket to view the full tournament tree."
    )

    await interaction.response.send_message(embed=embed)


# ============================================================
# BRACKET IMAGE
# ============================================================

def create_bracket_image(guild, guild_data):

    rounds = guild_data["rounds"]

    if not rounds:
        return None

    first_matches = len(rounds[0])

    height = max(700, first_matches * 130)
    width = 420 * len(rounds) + 150

    image = Image.new("RGB", (width, height), (24, 25, 28))
    draw = ImageDraw.Draw(image)

    try:
        title_font = ImageFont.truetype("arialbd.ttf", 38)
        round_font = ImageFont.truetype("arialbd.ttf", 24)
        player_font = ImageFont.truetype("arial.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        round_font = ImageFont.load_default()
        player_font = ImageFont.load_default()

    draw.text(
        (50, 30),
        "M8 COMMUNITY TOURNAMENT",
        fill="white",
        font=title_font
    )

    round_names = {
        2: "FINAL",
        4: "SEMIFINALS",
        8: "QUARTERFINALS",
        16: "ROUND OF 16",
        32: "ROUND OF 32"
    }

    first_player_count = len(rounds[0]) * 2

    for round_index, round_matches in enumerate(rounds):

        x = 60 + round_index * 410

        players_in_round = len(round_matches) * 2

        if players_in_round == 2:
            title = "FINAL"
        else:
            title = round_names.get(
                players_in_round,
                f"ROUND {round_index + 1}"
            )

        draw.text(
            (x, 100),
            title,
            fill=(220, 220, 220),
            font=round_font
        )

        spacing = height / (len(round_matches) + 1)

        for match_index, match in enumerate(round_matches):

            y = int(spacing * (match_index + 1))

            box_width = 310
            box_height = 82

            p1 = player_name(guild, match["p1"])
            p2 = player_name(guild, match["p2"])

            draw.rounded_rectangle(
                (x, y, x + box_width, y + box_height),
                radius=10,
                outline=(130, 130, 130),
                width=2
            )

            draw.text(
                (x + 15, y + 10),
                p1[:24],
                fill="white",
                font=player_font
            )

            draw.line(
                (x, y + 41, x + box_width, y + 41),
                fill=(80, 80, 80),
                width=1
            )

            draw.text(
                (x + 15, y + 50),
                p2[:24],
                fill="white",
                font=player_font
            )

            if match["winner"]:

                winner = player_name(
                    guild,
                    match["winner"]
                )

                draw.text(
                    (x + 200, y + 29),
                    f"✓ {winner[:10]}",
                    fill=(100, 255, 130),
                    font=player_font
                )

    path = "m8_bracket.png"

    image.save(path)

    return path


# ============================================================
# BRACKET COMMAND
# ============================================================

@bot.tree.command(
    name="bracket",
    description="Show the current M8 Tournament bracket"
)
async def bracket(interaction: discord.Interaction):

    guild_data = get_guild_data(interaction.guild.id)

    if not guild_data["started"]:
        await interaction.response.send_message(
            "❌ The tournament has not started yet.",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    path = create_bracket_image(
        interaction.guild,
        guild_data
    )

    if not path:
        await interaction.followup.send(
            "❌ Could not create bracket."
        )
        return

    file = discord.File(
        path,
        filename="M8_Tournament_Bracket.png"
    )

    embed = discord.Embed(
        title="🏆 M8 TOURNAMENT BRACKET"
    )

    embed.set_image(
        url="attachment://M8_Tournament_Bracket.png"
    )

    if guild_data["champion"]:

        embed.description = (
            f"👑 **CHAMPION:** "
            f"<@{guild_data['champion']}>"
        )

    await interaction.followup.send(
        embed=embed,
        file=file
    )


# ============================================================
# RESULT
# ============================================================

@bot.tree.command(
    name="result",
    description="Enter a tournament match result"
)
@app_commands.describe(
    round_number="Tournament round number",
    match_number="Match number in that round",
    winner="Winner of the match",
    score="Example: 3-1"
)
async def result(
    interaction: discord.Interaction,
    round_number: int,
    match_number: int,
    winner: discord.Member,
    score: str
):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Only tournament staff can enter results.",
            ephemeral=True
        )
        return

    guild_data = get_guild_data(interaction.guild.id)

    if not guild_data["started"]:
        await interaction.response.send_message(
            "❌ Tournament has not started.",
            ephemeral=True
        )
        return

    round_index = round_number - 1
    match_index = match_number - 1

    try:
        match = guild_data["rounds"][round_index][match_index]
    except:
        await interaction.response.send_message(
            "❌ Invalid round or match number.",
            ephemeral=True
        )
        return

    winner_id = str(winner.id)

    if winner_id not in [match["p1"], match["p2"]]:
        await interaction.response.send_message(
            "❌ That player is not part of this match.",
            ephemeral=True
        )
        return

    match["winner"] = winner_id
    match["score"] = score

    # FINAL
    if round_index == len(guild_data["rounds"]) - 1:

        guild_data["champion"] = winner_id
        save_data()

        embed = discord.Embed(
            title="👑 M8 TOURNAMENT CHAMPION",
            description=(
                f"🏆 {winner.mention} has won the "
                f"**M8 Community Tournament!**"
            )
        )

        embed.add_field(
            name="Final Score",
            value=score
        )

        embed.set_footer(
            text="M8 Community Tournament"
        )

        await interaction.response.send_message(embed=embed)

        return

    # MOVE WINNER TO NEXT ROUND
    next_round = guild_data["rounds"][round_index + 1]

    next_match_index = match_index // 2

    if match_index % 2 == 0:
        next_round[next_match_index]["p1"] = winner_id
    else:
        next_round[next_match_index]["p2"] = winner_id

    save_data()

    embed = discord.Embed(
        title="✅ MATCH RESULT",
        description=(
            f"🏆 **Winner:** {winner.mention}\n"
            f"📊 **Score:** {score}"
        )
    )

    embed.add_field(
        name="➡️ Next Round",
        value=f"{winner.mention} advances!"
    )

    await interaction.response.send_message(embed=embed)


# ============================================================
# RANDOM MATCH DRAW
# ============================================================

@bot.tree.command(
    name="draw",
    description="Create random BO5 tank classes and maps"
)
@app_commands.describe(
    player1="First player",
    player2="Second player"
)
async def draw(
    interaction: discord.Interaction,
    player1: discord.Member,
    player2: discord.Member
):

    classes = []

    for i in range(5):

        available = TANK_CLASSES.copy()

        if classes:
            available.remove(classes[-1])

        classes.append(
            random.choice(available)
        )

    maps = random.sample(MAPS, 5)

    embed = discord.Embed(
        title="🏆 M8 COMMUNITY TOURNAMENT",
        description=(
            f"{player1.mention} ⚔️ {player2.mention}"
        )
    )

    for i in range(5):

        embed.add_field(
            name=f"Battle {i + 1}",
            value=(
                f"🎲 **{classes[i]}**\n"
                f"🗺️ **{maps[i]}**"
            ),
            inline=False
        )

    embed.add_field(
        name="⚙️ MATCH SETTINGS",
        value=(
            "**Tier:** X\n"
            "**Format:** Best of 5\n"
            "**Mode:** 1v1\n"
            "**Server:** EU\n"
            "**Tanks:** Tech Tree only"
        ),
        inline=False
    )

    embed.set_footer(
        text="M8 Tournament • May the best player win!"
    )

    await interaction.response.send_message(embed=embed)


# ============================================================
# RESET TOURNAMENT
# ============================================================

@bot.tree.command(
    name="reset_tournament",
    description="Completely reset the current tournament"
)
async def reset_tournament(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Only tournament staff can reset the tournament.",
            ephemeral=True
        )
        return

    guild_id = str(interaction.guild.id)

    data[guild_id] = {
        "players": [],
        "started": False,
        "rounds": [],
        "champion": None
    }

    save_data()

    await interaction.response.send_message(
        "♻️ **M8 Tournament has been completely reset.**"
    )

# ============================================================
# REGISTRATION BUTTONS
# ============================================================

class TournamentRegistrationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Register",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="m8_register_button"
    )
    async def register_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild_data = get_guild_data(interaction.guild.id)

        if guild_data["started"]:
            await interaction.response.send_message(
                "❌ Registration is closed. The tournament has already started.",
                ephemeral=True
            )
            return

        user_id = str(interaction.user.id)

        if user_id in guild_data["players"]:
            await interaction.response.send_message(
                "⚠️ You are already registered for the tournament.",
                ephemeral=True
            )
            return

        guild_data["players"].append(user_id)
        save_data()

        await interaction.response.send_message(
            f"✅ You are registered! There are now **{len(guild_data['players'])} players**.",
            ephemeral=True
        )    
        embed = interaction.message.embeds[0]

        for i, field in enumerate(embed.fields):
            if field.name == "👥 Currently Registered":
                embed.set_field_at(
                    i,
                    name="👥 Currently Registered",
                    value=f"**{len(guild_data['players'])} players**",
                    inline=False
                )

        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Leave Tournament",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="m8_leave_button"
    )
    async def leave_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild_data = get_guild_data(interaction.guild.id)
        user_id = str(interaction.user.id)

        if guild_data["started"]:
            await interaction.response.send_message(
                "❌ You cannot leave after the tournament has started.",
                ephemeral=True
            )
            return

        if user_id not in guild_data["players"]:
            await interaction.response.send_message(
                "⚠️ You are not registered.",
                ephemeral=True
            )
            return

        guild_data["players"].remove(user_id)
        save_data()

        await interaction.response.send_message(
            "❌ You have left the M8 Tournament.",
            ephemeral=True
        )       
        embed = interaction.message.embeds[0]

        for i, field in enumerate(embed.fields):
            if field.name == "👥 Currently Registered":
                embed.set_field_at(
                    i,
                    name="👥 Currently Registered",
                    value=f"**{len(guild_data['players'])} players**",
                    inline=False
                )

        await interaction.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="View Players",
        emoji="👥",
        style=discord.ButtonStyle.secondary,
        custom_id="m8_players_button"
    )
    async def players_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild_data = get_guild_data(interaction.guild.id)

        if not guild_data["players"]:
            await interaction.response.send_message(
                "👥 Nobody is registered yet.",
                ephemeral=True
            )
            return

        player_list = "\n".join(
            f"**{i}.** <@{user_id}>"
            for i, user_id in enumerate(guild_data["players"], 1)
        )

        embed = discord.Embed(
            title="👥 M8 TOURNAMENT PLAYERS",
            description=player_list
        )

        embed.set_footer(
            text=f"{len(guild_data['players'])} players registered"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


@bot.tree.command(
    name="setup_registration",
    description="Post the official M8 Tournament registration"
)
async def setup_registration(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message(
            "❌ Only tournament staff can use this command.",
            ephemeral=True
        )
        return

    guild_data = get_guild_data(interaction.guild.id)

    embed = discord.Embed(
        title="🏆 M8 COMMUNITY 1V1 TOURNAMENT",
        description=(
            "### Registration is now open!\n\n"
            "Think you have what it takes to become the next "
            "**M8 Community Champion?**\n\n"
            "⚔️ **Mode:** 1v1\n"
            "🏅 **Tier:** X\n"
            "🎲 **Tank Classes:** Random\n"
            "🌳 **Tanks:** Tech Tree Only\n"
            "🏆 **Format:** Single Elimination\n"
            "🌍 **Server:** EU\n\n"
            "Press **Register** below to enter the tournament."
        )
    )

    embed.add_field(
        name="👥 Currently Registered",
        value=f"**{len(guild_data['players'])} players**",
        inline=False
    )

    embed.set_footer(
        text="M8 Community Tournament • Good luck!"
    )

    await interaction.response.send_message(
        embed=embed,
        view=TournamentRegistrationView()
    )
# ============================================================
# START BOT
# ============================================================

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("❌ DISCORD_TOKEN was not found.")
else:
    bot.run(TOKEN)
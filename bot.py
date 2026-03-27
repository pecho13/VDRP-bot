import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  KONFIGURÁCIA
# ─────────────────────────────────────────────
TOKEN = "TVOJ_BOT_TOKEN_TU"          # <-- vlož sem token z Discord Developer Portal
PREFIX = "!"
TICKET_CATEGORY_NAME = "🎫 Tickety"
LOG_CHANNEL_NAME = "mod-logy"
WELCOME_CHANNEL_NAME = "uvitanie"    # názov kanála pre uvítanie

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ─────────────────────────────────────────────
#  DÁTOVÝ SÚBOR PRE POSTAVY / WARNS
# ─────────────────────────────────────────────
DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"characters": {}, "warns": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user} je online!")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synchronizovaných {len(synced)} slash príkazov.")
    except Exception as e:
        print(f"❌ Chyba pri synchronizácii: {e}")
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="KE:RP | Košice RP 🏙️"
        )
    )


# ─────────────────────────────────────────────
#  1️⃣  UVÍTACÍ BOT
# ─────────────────────────────────────────────
@bot.event
async def on_member_join(member: discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    if not channel:
        return

    embed = discord.Embed(
        title="👋 Vitaj na KE:RP | Košice RP!",
        description=(
            f"Ahoj {member.mention}, sme radi, že si tu! 🎉\n\n"
            "🏙️ **KE:RP** je slovenský roleplay server zasadený do Košíc.\n"
            "Prečítaj si pravidlá a užívaj si hru!\n\n"
            "Ak potrebuješ pomoc, otvor si **ticket** príkazom `/ticket`."
        ),
        color=0x2F3136,
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Člen č. {member.guild.member_count}")
    await channel.send(embed=embed)


@bot.event
async def on_member_remove(member: discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name=WELCOME_CHANNEL_NAME)
    if not channel:
        return
    embed = discord.Embed(
        title="👋 Člen odišiel",
        description=f"**{member.name}** opustil server. Škoda! 😢",
        color=0xFF4444,
        timestamp=datetime.utcnow()
    )
    await channel.send(embed=embed)


# ─────────────────────────────────────────────
#  2️⃣  RP PRÍKAZY – POSTAVA / ŽIVOTOPIS
# ─────────────────────────────────────────────
@bot.tree.command(name="postava_vytvor", description="Vytvor svoju RP postavu")
@app_commands.describe(
    meno="Celé meno postavy",
    vek="Vek postavy",
    povolanie="Povolanie / práca",
    popis="Krátky popis / životopis postavy"
)
async def postava_vytvor(interaction: discord.Interaction, meno: str, vek: int, povolanie: str, popis: str):
    data = load_data()
    uid = str(interaction.user.id)
    data["characters"][uid] = {
        "meno": meno,
        "vek": vek,
        "povolanie": povolanie,
        "popis": popis,
        "hrac": interaction.user.name,
        "vytvorena": datetime.utcnow().strftime("%d.%m.%Y")
    }
    save_data(data)

    embed = discord.Embed(
        title="✅ Postava vytvorená!",
        color=0x57F287,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👤 Meno", value=meno, inline=True)
    embed.add_field(name="🎂 Vek", value=f"{vek} rokov", inline=True)
    embed.add_field(name="💼 Povolanie", value=povolanie, inline=True)
    embed.add_field(name="📖 Popis", value=popis, inline=False)
    embed.set_footer(text=f"Hráč: {interaction.user.name}")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="postava", description="Zobraz svoju alebo cudziu RP postavu")
@app_commands.describe(hrac="Hráč, ktorého postavu chceš vidieť (voliteľné)")
async def postava(interaction: discord.Interaction, hrac: discord.Member = None):
    data = load_data()
    target = hrac or interaction.user
    uid = str(target.id)

    if uid not in data["characters"]:
        await interaction.response.send_message(
            f"❌ **{target.display_name}** nemá vytvorenú postavu. Použi `/postava_vytvor`.",
            ephemeral=True
        )
        return

    ch = data["characters"][uid]
    embed = discord.Embed(
        title=f"🎭 Postava: {ch['meno']}",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    embed.set_thumbnail(url=target.display_avatar.url)
    embed.add_field(name="👤 Meno", value=ch["meno"], inline=True)
    embed.add_field(name="🎂 Vek", value=f"{ch['vek']} rokov", inline=True)
    embed.add_field(name="💼 Povolanie", value=ch["povolanie"], inline=True)
    embed.add_field(name="📖 Životopis", value=ch["popis"], inline=False)
    embed.set_footer(text=f"Hráč: {ch['hrac']} • Vytvorená: {ch['vytvorena']}")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="postava_zmaz", description="Zmaž svoju RP postavu")
async def postava_zmaz(interaction: discord.Interaction):
    data = load_data()
    uid = str(interaction.user.id)
    if uid in data["characters"]:
        del data["characters"][uid]
        save_data(data)
        await interaction.response.send_message("✅ Tvoja postava bola vymazaná.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Nemáš vytvorenú postavu.", ephemeral=True)


# ─────────────────────────────────────────────
#  3️⃣  TICKETING SYSTÉM
# ─────────────────────────────────────────────
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Otvoriť ticket", style=discord.ButtonStyle.primary, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = discord.utils.get(guild.categories, name=TICKET_CATEGORY_NAME)
        if not category:
            category = await guild.create_category(TICKET_CATEGORY_NAME)

        existing = discord.utils.get(
            guild.text_channels,
            name=f"ticket-{interaction.user.name.lower().replace(' ', '-')}"
        )
        if existing:
            await interaction.response.send_message(
                f"❌ Máš už otvorený ticket: {existing.mention}", ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        for role in guild.roles:
            if role.permissions.manage_messages:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title="🎫 Nový Ticket",
            description=(
                f"Ahoj {interaction.user.mention}! Popíš nám tvoj problém a moderátor ti čoskoro pomôže.\n\n"
                "Na zatvorenie ticketu stlač tlačidlo nižšie."
            ),
            color=0xFEE75C,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="KE:RP Podpora")
        await channel.send(embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket otvorený: {channel.mention}", ephemeral=True)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Zatvoriť ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Ticket bude zatvorený za 5 sekúnd...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()


@bot.tree.command(name="ticket_panel", description="[ADMIN] Vytvor panel pre tickety")
@app_commands.checks.has_permissions(administrator=True)
async def ticket_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎫 Podpora | KE:RP",
        description=(
            "Potrebuješ pomoc? Máš otázku alebo problém?\n\n"
            "Klikni na tlačidlo nižšie a otvor si **support ticket**. "
            "Moderátor ti odpovie čo najskôr! 🙏"
        ),
        color=0x5865F2
    )
    embed.set_footer(text="KE:RP | Košice RP • Podpora")
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket panel vytvorený!", ephemeral=True)


# ─────────────────────────────────────────────
#  4️⃣  MODERAČNÉ PRÍKAZY
# ─────────────────────────────────────────────
async def send_log(guild: discord.Guild, embed: discord.Embed):
    log_channel = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
    if log_channel:
        await log_channel.send(embed=embed)


@bot.tree.command(name="warn", description="[MOD] Udeľ varovanie hráčovi")
@app_commands.describe(hrac="Hráč", dovod="Dôvod varovania")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn(interaction: discord.Interaction, hrac: discord.Member, dovod: str):
    data = load_data()
    uid = str(hrac.id)
    if uid not in data["warns"]:
        data["warns"][uid] = []
    data["warns"][uid].append({
        "dovod": dovod,
        "moderator": interaction.user.name,
        "datum": datetime.utcnow().strftime("%d.%m.%Y %H:%M")
    })
    save_data(data)
    pocet = len(data["warns"][uid])

    embed = discord.Embed(
        title="⚠️ Varovanie udelené",
        color=0xFEE75C,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👤 Hráč", value=hrac.mention, inline=True)
    embed.add_field(name="📋 Dôvod", value=dovod, inline=True)
    embed.add_field(name="🔢 Celkovo warningov", value=str(pocet), inline=True)
    embed.set_footer(text=f"Moderátor: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, embed)

    try:
        dm_embed = discord.Embed(
            title="⚠️ Dostal si varovanie na KE:RP",
            description=f"**Dôvod:** {dovod}\n**Moderátor:** {interaction.user.name}",
            color=0xFEE75C
        )
        await hrac.send(embed=dm_embed)
    except:
        pass


@bot.tree.command(name="warny", description="Zobraz warningy hráča")
@app_commands.describe(hrac="Hráč")
@app_commands.checks.has_permissions(manage_messages=True)
async def warny(interaction: discord.Interaction, hrac: discord.Member):
    data = load_data()
    uid = str(hrac.id)
    warns_list = data["warns"].get(uid, [])

    embed = discord.Embed(
        title=f"📋 Warningy – {hrac.display_name}",
        color=0xED4245 if warns_list else 0x57F287,
        timestamp=datetime.utcnow()
    )
    if not warns_list:
        embed.description = "✅ Žiadne warningy!"
    else:
        for i, w in enumerate(warns_list, 1):
            embed.add_field(
                name=f"#{i} – {w['datum']}",
                value=f"**Dôvod:** {w['dovod']}\n**Mod:** {w['moderator']}",
                inline=False
            )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="warn_zmaz", description="[MOD] Zmaž všetky warningy hráča")
@app_commands.describe(hrac="Hráč")
@app_commands.checks.has_permissions(manage_messages=True)
async def warn_zmaz(interaction: discord.Interaction, hrac: discord.Member):
    data = load_data()
    uid = str(hrac.id)
    data["warns"][uid] = []
    save_data(data)
    await interaction.response.send_message(f"✅ Warningy hráča {hrac.mention} boli vymazané.", ephemeral=True)


@bot.tree.command(name="kick", description="[MOD] Vykopni hráča zo servera")
@app_commands.describe(hrac="Hráč", dovod="Dôvod")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, hrac: discord.Member, dovod: str = "Bez dôvodu"):
    await hrac.kick(reason=dovod)
    embed = discord.Embed(
        title="👢 Hráč bol vykopnutý",
        color=0xED4245,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👤 Hráč", value=str(hrac), inline=True)
    embed.add_field(name="📋 Dôvod", value=dovod, inline=True)
    embed.set_footer(text=f"Moderátor: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, embed)


@bot.tree.command(name="ban", description="[MOD] Zabanuj hráča")
@app_commands.describe(hrac="Hráč", dovod="Dôvod", dni="Počet dní správ na zmazanie (0-7)")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, hrac: discord.Member, dovod: str = "Bez dôvodu", dni: int = 0):
    await hrac.ban(reason=dovod, delete_message_days=min(dni, 7))
    embed = discord.Embed(
        title="🔨 Hráč bol zabanovaný",
        color=0xED4245,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👤 Hráč", value=str(hrac), inline=True)
    embed.add_field(name="📋 Dôvod", value=dovod, inline=True)
    embed.set_footer(text=f"Moderátor: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, embed)


@bot.tree.command(name="unban", description="[MOD] Odbanuj hráča podľa ID")
@app_commands.describe(user_id="Discord ID hráča")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ Hráč **{user}** bol odbanovaný.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Chyba: {e}", ephemeral=True)


@bot.tree.command(name="mute", description="[MOD] Umlčaj hráča (timeout)")
@app_commands.describe(hrac="Hráč", minuty="Počet minút", dovod="Dôvod")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, hrac: discord.Member, minuty: int, dovod: str = "Bez dôvodu"):
    from datetime import timedelta
    duration = timedelta(minutes=minuty)
    await hrac.timeout(duration, reason=dovod)
    embed = discord.Embed(
        title="🔇 Hráč bol umlčaný",
        color=0xFEE75C,
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="👤 Hráč", value=hrac.mention, inline=True)
    embed.add_field(name="⏱️ Čas", value=f"{minuty} minút", inline=True)
    embed.add_field(name="📋 Dôvod", value=dovod, inline=True)
    embed.set_footer(text=f"Moderátor: {interaction.user.name}")
    await interaction.response.send_message(embed=embed)
    await send_log(interaction.guild, embed)


@bot.tree.command(name="clear", description="[MOD] Vymaž správy v kanáli")
@app_commands.describe(pocet="Počet správ (max 100)")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, pocet: int):
    pocet = min(pocet, 100)
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=pocet)
    await interaction.followup.send(f"✅ Vymazaných {len(deleted)} správ.", ephemeral=True)


# ─────────────────────────────────────────────
#  CHYBOVÉ HLÁSENIA
# ─────────────────────────────────────────────
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Nemáš oprávnenie na tento príkaz!", ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Chyba: {error}", ephemeral=True)


# ─────────────────────────────────────────────
#  SPUSTENIE
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bot.run(TOKEN)

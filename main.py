import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import json
import time

TOKEN = "PUT_YOUR_TOKEN_HERE"

LOG_CHANNEL_ID = 1483891442920456263

# الرتب
ROLES = {
    "warn1": 1475095531389714604,
    "warn2": 1475097777104097545,
    "warn3": 1475098153421377567,
    "disc1": 1473015121906368715,
    "disc2": 1473015122753749012,
    "timeout": 1473015129019908232
}

# مدة العقوبات (بالثواني)
DURATIONS = {
    "warn1": 5 * 24 * 3600,
    "warn2": 7 * 24 * 3600,
    "warn3": 14 * 24 * 3600,
    "disc1": 7 * 24 * 3600,
    "disc2": 14 * 24 * 3600,
    "timeout": 7 * 24 * 3600
}

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

punishments = {}

# تحميل البيانات
try:
    with open("punishments.json", "r") as f:
        punishments = json.load(f)
except:
    punishments = {}

def save_data():
    with open("punishments.json", "w") as f:
        json.dump(punishments, f)

# ================= UI =================

class PunishmentMenu(discord.ui.Select):
    def __init__(self, member, moderator):
        self.member = member
        self.moderator = moderator

        options = [
            discord.SelectOption(label="القذف", description="إنذار دسكورد أول + ثاني + تايم أوت أسبوع"),
            discord.SelectOption(label="السب", description="تحذير أول + تحذير ثاني"),
            discord.SelectOption(label="تسحيب", description="باند نهائي"),
            discord.SelectOption(label="تسحيب متكرر", description="إنذار دسكورد أول + ثاني"),
            discord.SelectOption(label="إساءة استخدام الإدارة", description="كسر رتبة"),
        ]

        super().__init__(placeholder="اختر نوع العقوبة...", options=options)

    async def callback(self, interaction: discord.Interaction):

        guild = interaction.guild
        member = self.member

        def add_role(role_key):
            role = guild.get_role(ROLES[role_key])
            if role:
                asyncio.create_task(member.add_roles(role))

                end_time = int(time.time()) + DURATIONS[role_key]

                if str(member.id) not in punishments:
                    punishments[str(member.id)] = []

                punishments[str(member.id)].append({
                    "role": role_key,
                    "end": end_time
                })

                save_data()

        # === العقوبات ===

        if self.values[0] == "القذف":
            add_role("disc1")
            add_role("disc2")
            add_role("timeout")

            await member.timeout(discord.utils.utcnow() + discord.timedelta(days=7))

        elif self.values[0] == "السب":
            add_role("warn1")
            add_role("warn2")

        elif self.values[0] == "تسحيب":
            await member.ban(reason="تسحيب")

        elif self.values[0] == "تسحيب متكرر":
            add_role("disc1")
            add_role("disc2")

        elif self.values[0] == "إساءة استخدام الإدارة":
            await member.edit(roles=[])

        # === لوق ===
        log = bot.get_channel(LOG_CHANNEL_ID)
        if log:
            await log.send(f"📢 تم معاقبة {member.mention} بواسطة {self.moderator.mention}\nالسبب: {self.values[0]}")

        await interaction.response.send_message("✅ تم تنفيذ العقوبة", ephemeral=True)


class PunishmentView(discord.ui.View):
    def __init__(self, member, moderator):
        super().__init__(timeout=None)
        self.add_item(PunishmentMenu(member, moderator))


# ================= COMMAND =================

@bot.tree.command(name="عقوبة", description="إعطاء عقوبة لعضو")
@app_commands.describe(member="اختر العضو")
async def punish(interaction: discord.Interaction, member: discord.Member):

    embed = discord.Embed(
        title="📋 نظام العقوبات",
        description="اختر نوع المخالفة من القائمة بالأسفل",
        color=discord.Color.red()
    )

    embed.set_image(url="PUT_IMAGE_LINK_HERE")  # حط الصورة هون

    await interaction.response.send_message(
        embed=embed,
        view=PunishmentView(member, interaction.user)
    )


# ================= إزالة الرتب تلقائي =================

@tasks.loop(seconds=60)
async def check_punishments():
    now = int(time.time())

    for user_id in list(punishments.keys()):
        member_data = punishments[user_id]
        guild = bot.guilds[0]
        member = guild.get_member(int(user_id))

        if not member:
            continue

        new_list = []

        for p in member_data:
            if now >= p["end"]:
                role = guild.get_role(ROLES[p["role"]])
                if role:
                    await member.remove_roles(role)
            else:
                new_list.append(p)

        punishments[user_id] = new_list

    save_data()


# ================= منع abuse الإدارة =================

action_counter = {}

@bot.event
async def on_member_update(before, after):

    if before.mute != after.mute or before.deaf != after.deaf:

        mod = after.guild.get_member(after.id)

        if not mod.guild_permissions.moderate_members:
            return

        if mod.id not in action_counter:
            action_counter[mod.id] = []

        action_counter[mod.id].append(time.time())

        # خلال 10 ثواني أكثر من 5 مرات
        action_counter[mod.id] = [t for t in action_counter[mod.id] if time.time() - t < 10]

        if len(action_counter[mod.id]) >= 5:
            await mod.timeout(discord.utils.utcnow() + discord.timedelta(minutes=5))
            action_counter[mod.id] = []


# ================= READY =================

@bot.event
async def on_ready():
    await bot.tree.sync()
    check_punishments.start()
    print(f"Bot Ready: {bot.user}")


bot.run(TOKEN)

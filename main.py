# ==============================================================================
# المشروع: بوت RMOT الصوتي - الإصدار الرابع (Modal & Admin System)
# الوصف: لوحة تحكم إدارية بنظام النوافذ المنبثقة لإرسال التحذيرات والإعلانات في الخاص
# المميزات: صوت 24/7، منشن إدارة، نوافذ إدخال بيانات، إرسال تلقائي للخاص
# ==============================================================================

import discord
from discord.ext import commands, tasks
from discord.ui import Button, View, Modal, TextInput
import asyncio
import os
import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

# ------------------------------------------------------------------------------
# [1] إعدادات الربط والتشغيل (Configuration)
# ------------------------------------------------------------------------------
VOICE_ID = 1466581684290850984
STAFF_CHANNEL_ID = 1467779526351392880
STAFF_ROLE_ID = 1466572944166883461
AUDIO_FILE = "support.mp3"
PANEL_IMAGE = "POT.png"

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# ------------------------------------------------------------------------------
# [2] نوافذ إدخال البيانات (Modals System)
# ------------------------------------------------------------------------------

class WarningModal(Modal, title="إصدار تحذير رسمي"):
    user_id = TextInput(label="آيدي العضو المعني", placeholder="أدخل ID العضو هنا...", min_length=15)
    reason = TextInput(label="سبب التحذير", style=discord.TextStyle.paragraph, placeholder="اكتب السبب بوضوح...")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user = await bot.fetch_user(int(self.user_id.value))
            embed = discord.Embed(title="⚠️ تحذير رسمي من الإدارة", description=f"تم إصدار تحذير بحقك بسبب:\n**{self.reason.value}**", color=0xff0000)
            await user.send(embed=embed)
            await interaction.response.send_message(f"✅ تم إرسال التحذير للعضو {user.name} في الخاص.", ephemeral=True)
        except:
            await interaction.response.send_message("❌ فشل الإرسال! تأكد من الآيدي أو أن العضو مغلق الخاص.", ephemeral=True)

class AnnouncementModal(Modal, title="نشر إعلان رتبة"):
    role_id = TextInput(label="آيدي الرتبة المستهدفة", placeholder="أدخل ID الرتبة هنا...", min_length=15)
    message = TextInput(label="نص الإعلان", style=discord.TextStyle.paragraph, placeholder="اكتب الإعلان الذي سيصلهم في الخاص...")

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("⏳ جاري البدء في عملية النشر التلقائي للرتبة...", ephemeral=True)
        role = interaction.guild.get_role(int(self.role_id.value))
        if not role:
            return await interaction.followup.send("❌ آيدي الرتبة غير صحيح!", ephemeral=True)

        count = 0
        for member in role.members:
            try:
                embed = discord.Embed(title="📢 إعلان هام", description=self.message.value, color=0x00ff00)
                await member.send(embed=embed)
                count += 1
            except:
                continue
        await interaction.followup.send(f"✅ تم الانتهاء! وصل الإعلان لـ {count} عضو في الخاص.", ephemeral=True)

# ------------------------------------------------------------------------------
# [3] لوحة التحكم RMOT (الأزرار والتحكم)
# ------------------------------------------------------------------------------

class ControlPanel(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="إعلان 📢", style=discord.ButtonStyle.green, custom_id="m_ann")
    async def announcement(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AnnouncementModal())

    @discord.ui.button(label="تحذير ⚠️", style=discord.ButtonStyle.red, custom_id="m_warn")
    async def warning(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(WarningModal())

    @discord.ui.button(label="طرد 👢", style=discord.ButtonStyle.red, custom_id="m_kick")
    async def kick(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("👢 نظام الطرد اليدوي: يرجى استخدام الأمر الإداري المباشر.", ephemeral=True)

    @discord.ui.button(label="تنبيه 🔔", style=discord.ButtonStyle.blurple, custom_id="m_alert")
    async def alert(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔔 تم تفعيل نظام التنبيهات السريع.", ephemeral=True)

    @discord.ui.button(label="رتبة 🏅", style=discord.ButtonStyle.grey, custom_id="m_role")
    async def role(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🏅 يرجى الانتظار في الروم الصوتي ليتم تسليمك الرتبة.", ephemeral=True)

    @discord.ui.button(label="معلومات ℹ️", style=discord.ButtonStyle.blurple, custom_id="m_info")
    async def info(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("ℹ️ RMOT V4: نظام التحكم الصوتي والإداري المتكامل.", ephemeral=True)

    @discord.ui.button(label="إعادة اتصال صوتي 🔄", style=discord.ButtonStyle.blurple, custom_id="m_recon")
    async def reconnect(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 جاري تحديث اتصال البوت الصوتي...", ephemeral=True)

# ------------------------------------------------------------------------------
# [4] نظام الصوت والبقاء 24/7
# ------------------------------------------------------------------------------

@bot.event
async def on_ready():
    print("✅ نظام RMOT V4 متصل وجاهز للعمل!")
    stay_in_voice.start()

@tasks.loop(seconds=15)
async def stay_in_voice():
    channel = bot.get_channel(VOICE_ID)
    if not channel:
        return
    vc = discord.utils.get(bot.voice_clients, guild=channel.guild)
    if not vc or not vc.is_connected():
        try:
            await channel.connect(reconnect=True)
        except:
            pass

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return
    if after.channel and after.channel.id == VOICE_ID:
        if before.channel is None or before.channel.id != VOICE_ID:
            staff_ch = bot.get_channel(STAFF_CHANNEL_ID)
            if staff_ch:
                await staff_ch.send(f"🚨 <@&{STAFF_ROLE_ID}>، العضو **{member.name}** دخل الانتظار!")
            vc = discord.utils.get(bot.voice_clients, guild=member.guild)
            if vc and vc.is_connected():
                if vc.is_playing():
                    vc.stop()
                vc.play(discord.FFmpegPCMAudio(AUDIO_FILE))

# ------------------------------------------------------------------------------
# [5] أنظمة الأوامر (Help & Panel)
# ------------------------------------------------------------------------------

@bot.command(name='مساعدة')
async def show_panel(ctx):
    if any(role.id == STAFF_ROLE_ID for role in ctx.author.roles):
        embed = discord.Embed(
            title="🛡️ لوحة التحكم الإدارية الكبرى",
            description="**الصوتي RMOT نظام 4**\n\nاضغط على الأزرار لفتح نوافذ التحكم والإرسال التلقائي للخاص.",
            color=0x2b2d31
        )
        if os.path.exists(PANEL_IMAGE):
            file = discord.File(PANEL_IMAGE, filename="p.png")
            embed.set_image(url="attachment://p.png")
            await ctx.send(file=file, embed=embed, view=ControlPanel())
        else:
            await ctx.send(embed=embed, view=ControlPanel())
    else:
        await ctx.send("❌ للإدارة فقط!")

@bot.command(name='هيلب')
async def manual(ctx):
    guide = discord.Embed(title="📚 دليل تشغيل بوت RMOT V4", color=0x00ff00)
    guide.add_field(name="❓ زر التحذير", value="يفتح لك نافذة تطلب منك آيدي العضو والسبب، ثم يرسل له البوت في الخاص مباشرة.", inline=False)
    guide.add_field(name="❓ زر الإعلان", value="يطلب منك آيدي الرتبة، ويرسل الإعلان لكل أعضاء هذه الرتبة في الخاص تلقائياً.", inline=False)
    guide.add_field(name="❓ النظام الصوتي", value="البوت يدخل الروم 24/7 ويشغل صوت ترحيبي ويمنشن الإدارة فور دخول عضو.", inline=False)
    await ctx.send(embed=guide)

if not TOKEN:
    raise ValueError("TOKEN not found in environment variables")

bot.run(TOKEN)
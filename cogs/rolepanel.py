import re
import discord
from discord.ext import commands

from database import (
    create_panel,
    update_panel,
    update_panel_message_id,
    delete_panel,
    get_panel,
    get_panels_for_guild,
    add_role_to_panel,
    remove_role_from_panel,
    get_roles_for_panel,
)
from views import build_panel_embed, RolePanelView, rebuild_panel_message

COLOR_MAP = {
    "青": 0x3498DB,
    "赤": 0xE74C3C,
    "緑": 0x2ECC71,
    "黄色": 0xF1C40F,
    "紫": 0x9B59B6,
    "オレンジ": 0xE67E22,
    "ピンク": 0xFD79A8,
    "水色": 0x00CEC9,
    "白": 0xFFFFFF,
    "グレー": 0x95A5A6,
}


def parse_role(ctx: commands.Context, text: str) -> discord.Role | None:
    mention = re.match(r"<@&(\d+)>", text)
    if mention:
        return ctx.guild.get_role(int(mention.group(1)))
    if text.isdigit():
        return ctx.guild.get_role(int(text))
    text_lower = text.lower()
    for role in ctx.guild.roles:
        if role.name.lower() == text_lower:
            return role
    return None


class RolePanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="rp", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    @commands.guild_only()
    async def rp(self, ctx: commands.Context):
        embed = discord.Embed(title="RolePanel ヘルプ", color=0x3498DB)
        embed.description = (
            "**!rp create <タイトル>** — パネル作成\n"
            "**!rp add <パネルID> <ロール> [絵文字] [ラベル]** — ロール追加\n"
            "**!rp remove <パネルID> <ロール>** — ロール削除\n"
            "**!rp edit <パネルID> title <タイトル>** — タイトル変更\n"
            "**!rp edit <パネルID> desc <説明>** — 説明変更\n"
            "**!rp edit <パネルID> color <色名>** — 色変更\n"
            "**!rp delete <パネルID>** — パネル削除\n"
            "**!rp list** — パネル一覧\n"
            "**!rp refresh <パネルID>** — パネル再送信\n"
        )
        color_names = " / ".join(COLOR_MAP.keys())
        embed.add_field(name="使用可能な色", value=color_names, inline=False)
        await ctx.send(embed=embed)

    @rp.command(name="create")
    @commands.has_permissions(administrator=True)
    async def panel_create(self, ctx: commands.Context, *, title: str):
        panel_id = await create_panel(
            guild_id=ctx.guild.id,
            channel_id=ctx.channel.id,
            title=title,
        )

        panel = await get_panel(panel_id)
        roles = await get_roles_for_panel(panel_id)
        embed = await build_panel_embed(panel, roles, ctx.guild)

        msg = await ctx.channel.send(embed=embed, view=discord.ui.View())
        await update_panel_message_id(panel_id, msg.id)

        await ctx.send(
            f"✅ ロールパネル **{title}** (ID: `{panel_id}`) を作成しました。\n"
            f"`!rp add {panel_id} @ロール` でロールを追加してください。"
        )

    @rp.command(name="add")
    @commands.has_permissions(administrator=True)
    async def panel_add_role(self, ctx: commands.Context, panel_id: int, role_text: str, emoji: str = None, *, label: str = None):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != ctx.guild.id:
            await ctx.send("❌ パネルが見つかりません。")
            return

        role = parse_role(ctx, role_text)
        if role is None:
            await ctx.send("❌ ロールが見つかりません。メンション・ID・名前で指定してください。")
            return

        existing_roles = await get_roles_for_panel(panel_id)
        if len(existing_roles) >= 25:
            await ctx.send("❌ 1つのパネルに追加できるロールは最大25個です。")
            return

        if any(r["role_id"] == role.id for r in existing_roles):
            await ctx.send(f"❌ **{role.name}** は既にこのパネルに追加されています。")
            return

        bot_member = ctx.guild.me
        if role >= bot_member.top_role:
            await ctx.send(f"❌ **{role.name}** はBotのロールより上位のため、付与/剥奪できません。")
            return

        if role.managed:
            await ctx.send(f"❌ **{role.name}** は外部連携ロールのため追加できません。")
            return

        display_label = label or role.name
        try:
            await add_role_to_panel(panel_id, role.id, display_label, emoji)
        except Exception:
            await ctx.send("❌ ロールの追加に失敗しました。")
            return

        await ctx.send(f"✅ **{role.name}** をパネル `{panel_id}` に追加しました。")
        await rebuild_panel_message(self.bot, await get_panel(panel_id))

    @rp.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def panel_remove_role(self, ctx: commands.Context, panel_id: int, *, role_text: str):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != ctx.guild.id:
            await ctx.send("❌ パネルが見つかりません。")
            return

        role = parse_role(ctx, role_text)
        if role is None:
            await ctx.send("❌ ロールが見つかりません。")
            return

        removed = await remove_role_from_panel(panel_id, role.id)
        if not removed:
            await ctx.send(f"❌ **{role.name}** はこのパネルに登録されていません。")
            return

        await ctx.send(f"✅ **{role.name}** をパネル `{panel_id}` から削除しました。")
        await rebuild_panel_message(self.bot, await get_panel(panel_id))

    @rp.command(name="edit")
    @commands.has_permissions(administrator=True)
    async def panel_edit(self, ctx: commands.Context, panel_id: int, field: str, *, value: str):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != ctx.guild.id:
            await ctx.send("❌ パネルが見つかりません。")
            return

        field = field.lower()
        if field == "title":
            await update_panel(panel_id, title=value)
        elif field in ("desc", "description"):
            await update_panel(panel_id, description=value)
        elif field == "color":
            color_value = COLOR_MAP.get(value)
            if color_value is None:
                names = " / ".join(COLOR_MAP.keys())
                await ctx.send(f"❌ 不明な色です。使用可能: {names}")
                return
            await update_panel(panel_id, color=color_value)
        else:
            await ctx.send("❌ フィールドは `title` / `desc` / `color` のいずれかを指定してください。")
            return

        await ctx.send(f"✅ パネル `{panel_id}` を更新しました。")
        await rebuild_panel_message(self.bot, await get_panel(panel_id))

    @rp.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def panel_delete(self, ctx: commands.Context, panel_id: int):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != ctx.guild.id:
            await ctx.send("❌ パネルが見つかりません。")
            return

        if panel.get("message_id"):
            try:
                channel = self.bot.get_channel(panel["channel_id"])
                if channel:
                    msg = await channel.fetch_message(panel["message_id"])
                    await msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        await delete_panel(panel_id)
        await ctx.send(f"✅ パネル `{panel_id}` を削除しました。")

    @rp.command(name="list")
    @commands.has_permissions(administrator=True)
    async def panel_list(self, ctx: commands.Context):
        panels = await get_panels_for_guild(ctx.guild.id)
        if not panels:
            await ctx.send("ロールパネルはまだ作成されていません。")
            return

        embed = discord.Embed(title="ロールパネル一覧", color=0x3498DB)
        for p in panels:
            channel = self.bot.get_channel(p["channel_id"])
            ch_text = channel.mention if channel else "(不明なチャンネル)"
            roles = await get_roles_for_panel(p["id"])
            embed.add_field(
                name=f"ID: {p['id']} — {p['title']}",
                value=f"チャンネル: {ch_text}\nロール数: {len(roles)}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @rp.command(name="refresh")
    @commands.has_permissions(administrator=True)
    async def panel_refresh(self, ctx: commands.Context, panel_id: int):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != ctx.guild.id:
            await ctx.send("❌ パネルが見つかりません。")
            return

        if panel.get("message_id"):
            try:
                channel = self.bot.get_channel(panel["channel_id"])
                if channel:
                    msg = await channel.fetch_message(panel["message_id"])
                    await msg.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

        roles = await get_roles_for_panel(panel_id)
        channel = self.bot.get_channel(panel["channel_id"])
        if channel is None:
            await ctx.send("❌ パネルのチャンネルが見つかりません。")
            return

        embed = await build_panel_embed(panel, roles, ctx.guild)
        view = RolePanelView(roles) if roles else discord.ui.View()

        msg = await channel.send(embed=embed, view=view)
        await update_panel_message_id(panel_id, msg.id)

        await ctx.send(f"✅ パネル `{panel_id}` を再送信しました。")

    @rp.error
    async def rp_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ このコマンドは管理者のみ使用できます。")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ 引数が不足しています: `{error.param.name}`\n`!rp` でヘルプを確認してください。")


async def setup(bot: commands.Bot):
    await bot.add_cog(RolePanelCog(bot))

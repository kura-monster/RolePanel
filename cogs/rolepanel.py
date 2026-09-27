import discord
from discord import app_commands
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

COLOR_CHOICES = [
    app_commands.Choice(name="青", value=0x3498DB),
    app_commands.Choice(name="赤", value=0xE74C3C),
    app_commands.Choice(name="緑", value=0x2ECC71),
    app_commands.Choice(name="黄色", value=0xF1C40F),
    app_commands.Choice(name="紫", value=0x9B59B6),
    app_commands.Choice(name="オレンジ", value=0xE67E22),
    app_commands.Choice(name="ピンク", value=0xFD79A8),
    app_commands.Choice(name="水色", value=0x00CEC9),
    app_commands.Choice(name="白", value=0xFFFFFF),
    app_commands.Choice(name="グレー", value=0x95A5A6),
]


class RolePanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    group = app_commands.Group(
        name="rolepanel",
        description="ロールパネルの管理コマンド",
        default_permissions=discord.Permissions(administrator=True),
    )

    @group.command(name="create", description="新しいロールパネルを作成します")
    @app_commands.describe(
        title="パネルのタイトル",
        description="パネルの説明文（任意）",
        color="パネルの色（任意）",
        channel="パネルを送信するチャンネル（任意、省略で現在のチャンネル）",
    )
    @app_commands.choices(color=COLOR_CHOICES)
    async def panel_create(
        self,
        interaction: discord.Interaction,
        title: str,
        description: str = "",
        color: app_commands.Choice[int] = None,
        channel: discord.TextChannel = None,
    ):
        target_channel = channel or interaction.channel
        color_value = color.value if color else 0x3498DB

        panel_id = await create_panel(
            guild_id=interaction.guild_id,
            channel_id=target_channel.id,
            title=title,
            description=description,
            color=color_value,
        )

        panel = await get_panel(panel_id)
        roles = await get_roles_for_panel(panel_id)
        embed = await build_panel_embed(panel, roles, interaction.guild)

        try:
            msg = await target_channel.send(embed=embed, view=discord.ui.View())
            await update_panel_message_id(panel_id, msg.id)
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ {target_channel.mention} にメッセージを送信する権限がありません。",
                ephemeral=True,
            )
            await delete_panel(panel_id)
            return

        await interaction.response.send_message(
            f"✅ ロールパネル **{title}** (ID: `{panel_id}`) を {target_channel.mention} に作成しました。\n"
            f"`/rolepanel add` でロールを追加してください。",
            ephemeral=True,
        )

    @group.command(name="add", description="パネルにロールを追加します")
    @app_commands.describe(
        panel_id="パネルID",
        role="追加するロール",
        label="ボタンに表示するラベル（任意、省略でロール名）",
        emoji="ボタンに表示する絵文字（任意）",
        description="ロールの説明（任意）",
    )
    async def panel_add_role(
        self,
        interaction: discord.Interaction,
        panel_id: int,
        role: discord.Role,
        label: str = None,
        emoji: str = None,
        description: str = "",
    ):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("❌ パネルが見つかりません。", ephemeral=True)
            return

        existing_roles = await get_roles_for_panel(panel_id)
        if len(existing_roles) >= 25:
            await interaction.response.send_message(
                "❌ 1つのパネルに追加できるロールは最大25個です。", ephemeral=True
            )
            return

        if any(r["role_id"] == role.id for r in existing_roles):
            await interaction.response.send_message(
                f"❌ **{role.name}** は既にこのパネルに追加されています。", ephemeral=True
            )
            return

        bot_member = interaction.guild.me
        if role >= bot_member.top_role:
            await interaction.response.send_message(
                f"❌ **{role.name}** はBotのロールより上位のため、付与/剥奪できません。",
                ephemeral=True,
            )
            return

        if role.managed:
            await interaction.response.send_message(
                f"❌ **{role.name}** は外部連携ロールのため追加できません。", ephemeral=True
            )
            return

        display_label = label or role.name
        try:
            await add_role_to_panel(panel_id, role.id, display_label, emoji, description)
        except Exception:
            await interaction.response.send_message(
                "❌ ロールの追加に失敗しました。", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ **{role.name}** をパネル `{panel_id}` に追加しました。", ephemeral=True
        )
        await rebuild_panel_message(self.bot, await get_panel(panel_id))

    @group.command(name="remove", description="パネルからロールを削除します")
    @app_commands.describe(panel_id="パネルID", role="削除するロール")
    async def panel_remove_role(
        self,
        interaction: discord.Interaction,
        panel_id: int,
        role: discord.Role,
    ):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("❌ パネルが見つかりません。", ephemeral=True)
            return

        removed = await remove_role_from_panel(panel_id, role.id)
        if not removed:
            await interaction.response.send_message(
                f"❌ **{role.name}** はこのパネルに登録されていません。", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ **{role.name}** をパネル `{panel_id}` から削除しました。", ephemeral=True
        )
        await rebuild_panel_message(self.bot, await get_panel(panel_id))

    @group.command(name="edit", description="パネルのタイトルや説明を編集します")
    @app_commands.describe(
        panel_id="パネルID",
        title="新しいタイトル（任意）",
        description="新しい説明文（任意）",
        color="新しい色（任意）",
    )
    @app_commands.choices(color=COLOR_CHOICES)
    async def panel_edit(
        self,
        interaction: discord.Interaction,
        panel_id: int,
        title: str = None,
        description: str = None,
        color: app_commands.Choice[int] = None,
    ):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("❌ パネルが見つかりません。", ephemeral=True)
            return

        if title is None and description is None and color is None:
            await interaction.response.send_message(
                "❌ 変更する内容を1つ以上指定してください。", ephemeral=True
            )
            return

        await update_panel(
            panel_id,
            title=title,
            description=description,
            color=color.value if color else None,
        )

        await interaction.response.send_message(
            f"✅ パネル `{panel_id}` を更新しました。", ephemeral=True
        )
        await rebuild_panel_message(self.bot, await get_panel(panel_id))

    @group.command(name="delete", description="ロールパネルを削除します")
    @app_commands.describe(panel_id="削除するパネルID")
    async def panel_delete(
        self,
        interaction: discord.Interaction,
        panel_id: int,
    ):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("❌ パネルが見つかりません。", ephemeral=True)
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
        await interaction.response.send_message(
            f"✅ パネル `{panel_id}` を削除しました。", ephemeral=True
        )

    @group.command(name="list", description="このサーバーのロールパネル一覧を表示します")
    async def panel_list(self, interaction: discord.Interaction):
        panels = await get_panels_for_guild(interaction.guild_id)
        if not panels:
            await interaction.response.send_message(
                "ロールパネルはまだ作成されていません。", ephemeral=True
            )
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

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @group.command(name="refresh", description="パネルのメッセージを再送信します")
    @app_commands.describe(panel_id="パネルID")
    async def panel_refresh(
        self,
        interaction: discord.Interaction,
        panel_id: int,
    ):
        panel = await get_panel(panel_id)
        if panel is None or panel["guild_id"] != interaction.guild_id:
            await interaction.response.send_message("❌ パネルが見つかりません。", ephemeral=True)
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
            await interaction.response.send_message(
                "❌ パネルのチャンネルが見つかりません。", ephemeral=True
            )
            return

        embed = await build_panel_embed(panel, roles, interaction.guild)
        view = RolePanelView(roles) if roles else discord.ui.View()

        try:
            msg = await channel.send(embed=embed, view=view)
            await update_panel_message_id(panel_id, msg.id)
        except discord.Forbidden:
            await interaction.response.send_message(
                f"❌ チャンネルにメッセージを送信する権限がありません。", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"✅ パネル `{panel_id}` を再送信しました。", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RolePanelCog(bot))

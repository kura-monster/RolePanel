import discord
from database import get_roles_for_panel, get_panel_by_message


class RoleButton(discord.ui.Button):
    def __init__(self, role_id: int, label: str, emoji: str | None, description: str):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            emoji=emoji,
            custom_id=f"rolepanel:toggle:{role_id}",
        )
        self.role_id = role_id
        self.role_description = description

    async def callback(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(self.role_id)
        if role is None:
            await interaction.response.send_message(
                "このロールは既に削除されています。", ephemeral=True
            )
            return

        member = interaction.user
        if role in member.roles:
            try:
                await member.remove_roles(role)
                await interaction.response.send_message(
                    f"🔴 **{role.name}** ロールを外しました。", ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "Botの権限が不足しているため、ロールを外せませんでした。", ephemeral=True
                )
        else:
            try:
                await member.add_roles(role)
                await interaction.response.send_message(
                    f"🟢 **{role.name}** ロールを付与しました。", ephemeral=True
                )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "Botの権限が不足しているため、ロールを付与できませんでした。", ephemeral=True
                )


class RolePanelView(discord.ui.View):
    def __init__(self, roles: list[dict]):
        super().__init__(timeout=None)
        for role_data in roles:
            self.add_item(
                RoleButton(
                    role_id=role_data["role_id"],
                    label=role_data["label"],
                    emoji=role_data.get("emoji"),
                    description=role_data.get("description", ""),
                )
            )


async def build_panel_embed(panel: dict, roles: list[dict], guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title=panel["title"],
        description=panel.get("description", "") or "",
        color=panel.get("color", 3447003),
    )

    if roles:
        role_lines = []
        for r in roles:
            guild_role = guild.get_role(r["role_id"])
            role_name = guild_role.mention if guild_role else f"(削除済み: {r['label']})"
            emoji_str = f"{r['emoji']} " if r.get("emoji") else ""
            desc_str = f" — {r['description']}" if r.get("description") else ""
            role_lines.append(f"{emoji_str}{role_name}{desc_str}")
        embed.add_field(name="選択可能なロール", value="\n".join(role_lines), inline=False)
    else:
        embed.add_field(name="ロール", value="ロールが追加されていません。", inline=False)

    embed.set_footer(text="ボタンをクリックしてロールを切り替え")
    return embed


async def rebuild_panel_message(bot: discord.Client, panel: dict):
    channel = bot.get_channel(panel["channel_id"])
    if channel is None:
        return

    roles = await get_roles_for_panel(panel["id"])
    guild = channel.guild
    embed = await build_panel_embed(panel, roles, guild)
    view = RolePanelView(roles) if roles else discord.ui.View()

    if panel.get("message_id"):
        try:
            msg = await channel.fetch_message(panel["message_id"])
            await msg.edit(embed=embed, view=view)
            return
        except discord.NotFound:
            pass

    msg = await channel.send(embed=embed, view=view)
    from database import update_panel_message_id
    await update_panel_message_id(panel["id"], msg.id)

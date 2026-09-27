import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import init_db, get_all_panels_with_messages, get_roles_for_panel
from views import RolePanelView

load_dotenv()


class RolePanelBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await init_db()
        await self.load_extension("cogs.rolepanel")
        await self.tree.sync()

    async def on_ready(self):
        print(f"ログイン完了: {self.user} (ID: {self.user.id})")
        print(f"サーバー数: {len(self.guilds)}")
        await self.restore_views()

    async def restore_views(self):
        for guild in self.guilds:
            panels = await get_all_panels_with_messages(guild.id)
            for panel in panels:
                roles = await get_roles_for_panel(panel["id"])
                if roles:
                    view = RolePanelView(roles)
                    self.add_view(view, message_id=panel["message_id"])

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("rolepanel:toggle:"):
            return

        try:
            role_id = int(custom_id.split(":")[2])
        except (IndexError, ValueError):
            return

        role = interaction.guild.get_role(role_id)
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


def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("エラー: DISCORD_TOKEN が設定されていません。")
        print(".env ファイルに DISCORD_TOKEN=your_token を設定してください。")
        return

    bot = RolePanelBot()
    bot.run(token)


if __name__ == "__main__":
    main()

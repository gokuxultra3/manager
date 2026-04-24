import discord
from discord.ui import Select, Button
from discord import ui
from squarecloud import Application, StatusData
from db import deletar_app, verificar_ativacao, ativar_bot
from pagamentos import gerar_pagamento, verificar_pagamento

class EmbedAplicacao(discord.Embed):
    def __init__(self, app:Application, status_app:StatusData):
        super().__init__()
        self.title = app.name
        descricao = [
            f"```{app.desc}```" if app.desc else "",
            "🟢`Online`" if status_app.running else "🔴`Offline`"
        ]
        descricao = "\n".join(descricao)
        self.description= descricao
        self.add_field(name="CPU", value=status_app.cpu)
        self.add_field(name="RAM", value=status_app.ram)
        self.add_field(name="Armazenamento", value=status_app.storage)
        self.add_field(name="Rede Total", value=status_app.network['total'])


class SelectAplicacoes(Select):
    def __init__(self, aplicacoes:list[Application]):
        self.aplicacoes = aplicacoes
        opcoes = []
        for app in aplicacoes:
            opcoes.append(discord.SelectOption(label=app.name, value=app.id))
        
        super().__init__(placeholder="Selecione uma aplicação", options=opcoes)
    
    async def callback(self, interact:discord.Interaction):
        app_escolhido = self.values[0]
        for app in self.aplicacoes:
            if app.id == app_escolhido:
                app_escolhido = app
        
        app_status = await app_escolhido.status()
        view = MenuAplicacao(app_escolhido, app_status)

        await interact.response.send_message(embed=EmbedAplicacao(app_escolhido, app_status), view=view)

class MenuAplicacao(discord.ui.View):
    def __init__(self, app:Application, status_app:StatusData):
        self.aplicacao = app
        self.client = app.client
        super().__init__()

        self.botao_iniciar = Button(label="Iniciar", style=discord.ButtonStyle.green, disabled=status_app.running)
        self.botao_parar = Button(label="Parar", style=discord.ButtonStyle.red, disabled=not status_app.running)
        self.botao_reiniciar = Button(label="Reiniciar", style=discord.ButtonStyle.blurple, disabled=not status_app.running)
        self.botao_deletar = Button(label='Deletar', style=discord.ButtonStyle.danger, emoji='🗑️', row=2)

        self.botao_iniciar.callback = self.iniciar
        self.botao_parar.callback = self.parar
        self.botao_reiniciar.callback = self.reiniciar
        self.botao_deletar.callback = self.deletar

        self.add_item(self.botao_iniciar)
        self.add_item(self.botao_parar)
        self.add_item(self.botao_reiniciar)
        self.add_item(self.botao_deletar)

    
    async def iniciar(self, interaction:discord.Interaction):
        await self.executar_acao(interaction, self.botao_iniciar, "Iniciando...", self.aplicacao.start)

    async def parar(self, interaction:discord.Interaction):
        await self.executar_acao(interaction, self.botao_parar, "Parando...", self.aplicacao.stop)

    async def reiniciar(self, interaction:discord.Interaction):
        await self.executar_acao(interaction, self.botao_reiniciar, "Reiniciando...", self.aplicacao.restart)

    async def deletar(self, interaction:discord.Interaction):
        await self.executar_acao(interaction, self.botao_deletar, "Deletando...", self.aplicacao.delete)

    async def executar_acao(self, interaction:discord.Interaction, botao:Button, label_temp:str, acao):
        for item in self.children:
            if isinstance(item, Button):
                item.disabled = True
        
        botao.label = label_temp
        await interaction.response.edit_message(view=self)

        await acao()

        if botao == self.botao_deletar:
            await interaction.message.delete()
            deletar_app(self.aplicacao.id)
            return

        app_status = await self.aplicacao.status()
        await interaction.message.edit(view=MenuAplicacao(self.aplicacao, app_status), embed=EmbedAplicacao(self.aplicacao, app_status))

class AtivacaoMenu(ui.LayoutView):
    def __init__(self, discord_user:discord.Member):
        super().__init__()
        self.discord_user = discord_user

        header = ui.Section(ui.TextDisplay(f"## {discord_user.name}"), accessory=ui.Thumbnail(discord_user.avatar.url))
        container = ui.Container(header)
        self.add_item(container)

        if verificar_ativacao(discord_user):
            container._colour = discord.Colour.green()
            container.add_item(ui.TextDisplay('> Sua conta está ativada e pronta para uso! ✅'))
        else:
            container._colour = discord.Colour.red()

            self.botao_ativar = ui.Button(style=discord.ButtonStyle.green, label="Ativar")
            self.botao_ativar.callback = self.ativar_callback
            secao_ativar = ui.Section(ui.TextDisplay("`Você ainda não ativou sua conta.`"), accessory=self.botao_ativar)
            container.add_item(secao_ativar)
    
    async def ativar_callback(self, interaction:discord.Interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()

        pagamento_url, referencia = gerar_pagamento(interaction.user)

        pagamento_embed = discord.Embed(color=discord.Colour.red())
        pagamento_embed.description = f"## Conclua o pagamento no link abaixo:\n{pagamento_url}\n> O bot será ativado assim que detectarmos o pagamento! 😊"
        pagamento_msg = await interaction.followup.send(embed=pagamento_embed, ephemeral=True)

        pagamento_status = await verificar_pagamento(referencia)
        if not pagamento_status:
            pagamento_embed.description = "Tempo limite de pagamento excedido ❌"
            await pagamento_msg.edit(embed=pagamento_embed)
            return
        
        ativar_bot(interaction.user)
        pagamento_embed.description = "### Pagamento efetuado com sucesso! ✅"
        pagamento_embed.color = discord.Colour.green()
        await pagamento_msg.edit(embed=pagamento_embed)

import mercadopago, time, asyncio
from os import getenv
from discord import Member
from random import randint

sdk = mercadopago.SDK(getenv("MP_TOKEN"))

def gerar_pagamento(discord_user:Member):
    referencia = f"{discord_user.id}_{randint(1, 999999)}"

    preferencia_config = {
        'items':[
            {
                'title':'Ativação de Bot Manager',
                'description':'Ativa o bot',
                'quantity':1,
                'currency_id':'BRL',
                'unit_price':50
            }
        ],
        'external_reference':referencia
    }

    resultado = sdk.preference().create(preferencia_config)
    response = resultado['response']
    checkout_url = response['init_point']

    return checkout_url, referencia

async def verificar_pagamento(referencia:str, tentativas = 20, cooldown= 15):
    cont = 1
    while cont <= tentativas:
        await asyncio.sleep(cooldown)
        pagamento_status = sdk.merchant_order().search({'external_reference':referencia})['response']
        if pagamento_status.get('elements', False):
            status = pagamento_status['elements'][0]['payments'][-1]['status']
            return status
        cont+=1
        continue

    return False

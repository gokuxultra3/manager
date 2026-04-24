from pymongo import MongoClient
from dotenv import load_dotenv
from os import getenv
from discord import Member
from squarecloud.data import UploadData

load_dotenv(override=True)
DATABASE_URL = getenv("DATABASE_URL")
mongo_client = MongoClient(DATABASE_URL, tlsCAFile="certificate.pem", tlsCertificateKeyFile="certificate.pem")

banco_bot_manager = mongo_client['bot_manager']
colecao_usuarios = banco_bot_manager['usuarios']

def obter_usuario(discord_user:Member):
    usuario = colecao_usuarios.find_one({'discord_id':discord_user.id})
    if not usuario:
        usuario_dados = {
            'discord_id':discord_user.id,
            'name':discord_user.name
        }
        colecao_usuarios.insert_one(usuario_dados)
        return usuario_dados
    return usuario

def enviar_app(upload_data:UploadData, discord_user:Member):
    usuario = obter_usuario(discord_user)
    if not usuario.get('apps'):
        usuario['apps'] = []
    
    apps = usuario['apps']
    app_data = {
        'id':upload_data.id,
        'name':upload_data.name
    }

    apps.append(app_data)
    colecao_usuarios.update_one({'discord_id':discord_user.id},
                                {'$set':{
                                    'apps':apps
                                }})

def obter_apps(discord_user:Member):
    usuario = obter_usuario(discord_user)
    if not usuario.get('apps'):
        return []
    
    return usuario['apps']

def deletar_app(id:str):
    colecao_usuarios.update_one({'apps.id':id},
                                {'$pull':{
                                    'apps':{'id':id}
                                }})

def verificar_ativacao(discord_user:Member):
    usuario = obter_usuario(discord_user)
    return usuario.get('ativo', False)

def ativar_bot(discord_user:Member):
    colecao_usuarios.update_one({'discord_id':discord_user.id}, {'$set':{'ativo':True}})

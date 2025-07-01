from bson import ObjectId
import json

def sync_favorites(db_redis, user_col, user):
    redis_key = f"user:{user['_id']}:favorites"
    
    favorite_strings = db_redis.smembers(redis_key)

    favorites = []
    for fav_str in favorite_strings:
        try:
            # Tenta usar json.loads primeiro (mais seguro)
            fav = json.loads(fav_str)
            # Converte _id de volta para ObjectId
            if isinstance(fav.get('_id'), str):
                fav['_id'] = ObjectId(fav['_id'])
            favorites.append(fav)
        except json.JSONDecodeError:
            # Fallback para eval apenas se necessário (dados antigos)
            try:
                fav = eval(fav_str, {"ObjectId": ObjectId})
                favorites.append(fav)
            except:
                print(f"Erro ao processar favorito: {fav_str}")
                continue

    user_col.update_one({'_id': ObjectId(user['_id'])}, {'$set': {'favoritos': favorites}})
    
    print("Sincronização com o MongoDB realizada com sucesso!")

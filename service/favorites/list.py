from bson import ObjectId
import json

def list_favorites(db_redis, user):
    redis_key = f"user:{user['_id']}:favorites"
    favorites = db_redis.smembers(redis_key)

    favorite_list = []
    for fav_str in favorites:
        try:
            # Tenta json.loads primeiro
            fav = json.loads(fav_str)
            favorite_list.append(fav)
        except json.JSONDecodeError:
            # Fallback para eval se necessário
            try:
                fav = eval(fav_str, {"ObjectId": ObjectId})
                favorite_list.append(fav)
            except:
                continue

    if favorite_list:
        print("-" * 40)
        print("Favoritos armazenados:")
        print("-" * 40)
        for fav in favorite_list:
            print(f"Produto ID: {fav['_id']}, \nNome: {fav['produto']}, Marca: {fav.get('marca', 'Não disponível')}, Preço: R$ {fav['preco']}")
            print(f"Vendedor: {fav['vendedor']['nome']}, Email: {fav['vendedor']['email']}")
            print("-" * 40)
    else:
        print("Nenhum favorito encontrado.")

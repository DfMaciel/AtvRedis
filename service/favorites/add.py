from utils.utils import list_products, find_product
import json

def add_favorite(product_col, db_redis, user):
    list_products(product_col)
    favorites = []

    while True:
        product_id = input('Digite o Id do produto que deseja favoritar: ').strip()
        product = find_product(product_id, product_col)

        if product:
            product_info = {
                "_id": str(product["_id"]),  # Converte ObjectId para string
                "produto": product["produto"],
                "descricao": product["descricao"],
                "preco": str(product["preco"]),  # Converte para string para consistência
                "estoque": str(product["estoque"]),  # Converte para string
                "marca": product["marca"],
                "vendedor": {
                    "nome": product["vendedor"]["nome"],
                    "email": product["vendedor"]["email"],
                    "telefone": product["vendedor"]["telefone"]
                }
            }
            favorites.append(product_info)
            print(f"Produto '{product['produto']}' adicionado à lista de favoritos.")
        else:
            print('Produto não encontrado!')

        proceed = input('Deseja favoritar mais algum? (S/N) ').lower()
        if proceed == 'n':
            break
    
    if favorites:
        redis_key = f"user:{user['_id']}:favorites"
        for fav in favorites:
            db_redis.sadd(redis_key, json.dumps(fav))
        
        print("-="*20)
        print(f"{len(favorites)} favorito(s) adicionado(s) com sucesso.")
    else:
        print("Nenhum favorito foi adicionado.")



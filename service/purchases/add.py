from utils.utils import list_products, find_product, list_addresses, generate_nota_fical, calculate_final_value, update_sale_and_stock
from datetime import datetime
import json

def add_purchase(product_col, purchase_col, db_redis, user):
    list_products(product_col)

    shopping_cart = []  
    value_purchase = 0 

    while True:
        product_id = input("Digite o ID do produto que deseja comprar: ")
        product = find_product(product_id, product_col)
        if not product:
            print("Produto não encontrado!")
            continue  
        
        quantity = int(input("Digite a quantidade que deseja comprar: "))
        shopping_cart.append({"product": product, "quantity": quantity})
        
        continue_process = input("Deseja selecionar mais algum produto? (S/N) ").lower()
        if continue_process == "n":
            break

    list_addresses(user)

    delivery_address_id = int(input("Digite o ID do endereço de entrega: "))
    if delivery_address_id < 0 or delivery_address_id >= len(user['endereco']):
        return print("Endereço de entrega inválido!")
    
    delivery_address_final = user['endereco'][delivery_address_id]
    date_purchase = datetime.now()
    nota_fiscal = generate_nota_fical()

    for item in shopping_cart:
        product = item["product"]
        quantity = item["quantity"]
        value_purchase += calculate_final_value(product, quantity)

    user_data = {
        "_id": str(user["_id"]),  # Converte ObjectId para string
        "nome": user["nome"],
        "email": user["email"]
    }

    product_list = []
    for item in shopping_cart:
        product = item["product"]
        quantity = item["quantity"]
        
        product_data = {
            "_id": str(product["_id"]),  # Converte ObjectId para string
            "produto": product["produto"],
            "descricao": product["descricao"],
            "preco": str(product["preco"]),  # Converte para string
            "quantidade": quantity,
            "marca": product["marca"],
            "vendedor": {
                "nome": product["vendedor"]["nome"],
                "email": product["vendedor"]["email"],
                "telefone": product["vendedor"]["telefone"]
            }
        }
        product_list.append(product_data)

    compra = {
        "valor": value_purchase,
        "data_compra": date_purchase,
        "nota_fiscal": nota_fiscal,
        "status": "Processando",
        "usuario": user_data,
        "produtos": product_list,  
        "endereco_entrega": delivery_address_final
    }

    result = purchase_col.insert_one(compra)
    purchase_id = result.inserted_id 

    redis_key = f"user:{user['_id']}:purchases:{purchase_id}"

    db_redis.hset(redis_key, mapping={
        "data_compra": date_purchase.strftime("%Y-%m-%d %H:%M:%S"),
        "nota_fiscal": nota_fiscal,
        "usuario": json.dumps(user_data),  # Usa json.dumps em vez de str()
        "produtos": json.dumps(product_list),  # Usa json.dumps em vez de str()
        "valor": str(value_purchase),
        "endereco_entrega": json.dumps(delivery_address_final),  # Usa json.dumps
        "status": "Processando"
    })

    user_purchase_key = f"user:{user['_id']}:purchases"
    db_redis.rpush(user_purchase_key, redis_key) 

    for item in shopping_cart:
        product = item["product"]
        quantity = item["quantity"]
        update_sale_and_stock(product, quantity, product_col)
    print("-="*20)
    print("Compra realizada com sucesso!")
    print("-="*20)

    

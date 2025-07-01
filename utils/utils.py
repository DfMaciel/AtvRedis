import uuid
from bson.objectid import ObjectId

def find_user(user_email, user_col):
    user = user_col.find_one({'email': user_email})
    if user:
        return user
    return None

def find_product(product_id, product_col):
    product = product_col.find_one({"_id": ObjectId(product_id)})
    if product:
        return product
    return None

def list_products(product_col):
    products = list(product_col.find().sort('produto'))
    products_list = [{'id':str(product['_id']), 'produto':product['produto'], 'marca':product['marca']} for product in products]
    print("-="*20)
    for product in products_list:
        print(f"ID: {product['id']}, Produto: {product['produto']}, Marca: {product['marca']}")
    print("-="*20)

def list_addresses(user):
    addresses = user.get("endereco", [])
    if not addresses:
        print("-="*20)
        print("Não existem endereços cadastrados!")
        print("-="*20)
        return None
    for index, address in enumerate(addresses):
        print(f"ID {index}. Rua: {address.get('rua')}, Número: {address.get('numero')}, Bairro: {address.get('bairro')}, Cidade: {address.get('cidade')}, Estado: {address.get('estado')}")
    print("-="*20)
    
def generate_nota_fical():
    return str(uuid.uuid4())

def calculate_final_value(product, quantity):
    value_product = float(product.get("preco"))
    final_value = value_product * quantity
    return round(final_value, 2)

def update_sale_and_stock(product, quantity, product_col):
    stock = int(product.get("estoque"))
    product["estoque"] = stock - quantity
    product_col.update_one({"_id":product["_id"]}, {"$set": {"estoque": product["estoque"]}})
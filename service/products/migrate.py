from utils.utils import list_products
import json

def migrate_products(product_col, db_redis):
    """
    Migra TODOS os produtos do MongoDB para Redis
    (Terceiro tipo de item conforme enunciado)
    """
    print("Iniciando migração de produtos MongoDB → Redis...")
    
    # Busca todos os produtos do MongoDB
    all_products = list(product_col.find())
    
    if not all_products:
        print("Nenhum produto encontrado no MongoDB.")
        return
    
    migrated_count = 0
    for product in all_products:
        try:
            product_id = str(product["_id"])
            
            # Chave para produto migrado
            redis_key = f"migrated:product:{product_id}"
            
            # Prepara dados do produto para Redis
            product_data = {
                "product_id": product_id,
                "produto": product["produto"],
                "descricao": product.get("descricao", ""),
                "preco": str(product["preco"]),
                "estoque": str(product["estoque"]),
                "marca": product["marca"],
                "vendedor": json.dumps({
                    "_id": str(product["vendedor"]["_id"]),
                    "nome": product["vendedor"]["nome"],
                    "email": product["vendedor"]["email"],
                    "telefone": product["vendedor"].get("telefone", "")
                })
            }
            
            # Salva no Redis com TTL de 1 hora
            db_redis.hset(redis_key, mapping=product_data)
            db_redis.expire(redis_key, 3600)  # 1 hora
            
            # Adiciona à lista geral de produtos migrados
            db_redis.rpush("migrated:products:all", redis_key)
            
            migrated_count += 1
            
        except Exception as e:
            print(f"Erro ao migrar produto {product['_id']}: {e}")
    
    print(f"✅ {migrated_count} produtos migrados para Redis!")
    input("\nPressione Enter para continuar...")

def list_migrated_products(db_redis):
    """
    Lista todos os produtos migrados no Redis
    """
    product_keys = db_redis.lrange("migrated:products:all", 0, -1)
    
    if not product_keys:
        print("Nenhum produto migrado encontrado no Redis.")
        return
    
    print("\n📋 Produtos Migrados (Redis):")
    print("-" * 80)
    
    for product_key in product_keys:
        product_data = db_redis.hgetall(product_key)
        if product_data:
            try:
                vendedor = json.loads(product_data.get('vendedor', '{}'))
                print(f"ID: {product_data.get('product_id', 'N/A')} | "
                      f"Produto: {product_data.get('produto', 'N/A')} | "
                      f"Marca: {product_data.get('marca', 'N/A')} | "
                      f"Preço: R$ {product_data.get('preco', '0')} | "
                      f"Estoque: {product_data.get('estoque', '0')} | "
                      f"Vendedor: {vendedor.get('nome', 'N/A')}")
            except:
                print(f"ID: {product_data.get('product_id', 'N/A')} | "
                      f"Produto: {product_data.get('produto', 'N/A')} | "
                      f"Marca: {product_data.get('marca', 'N/A')}")
    
    print("-" * 80)

def manipulate_products(db_redis):
    """
    Manipula produtos no Redis (aplicar desconto, atualizar estoque, etc.)
    """
    while True:
        print("\n🔧 Manipulação de Produtos no Redis:")
        print("1 - Aplicar desconto em todos os produtos")
        print("2 - Atualizar estoque de produto específico")
        print("3 - Buscar produtos por marca")
        print("4 - Ver detalhes de produto específico")
        print("5 - Voltar")
        
        try:
            opcao = int(input("Escolha uma opção: "))
        except ValueError:
            print("Opção inválida!")
            continue
        
        if opcao == 1:
            apply_discount(db_redis)
        elif opcao == 2:
            update_stock(db_redis)
        elif opcao == 3:
            search_by_brand(db_redis)
        elif opcao == 4:
            show_product_details(db_redis)
        elif opcao == 5:
            break
        else:
            print("Opção inválida!")

def apply_discount(db_redis):
    """
    Aplica desconto em todos os produtos migrados
    """
    try:
        desconto = float(input("Digite o percentual de desconto (ex: 10 para 10%): "))
        
        product_keys = db_redis.lrange("migrated:products:all", 0, -1)
        if not product_keys:
            print("Nenhum produto migrado encontrado.")
            return
        
        updated_count = 0
        for product_key in product_keys:
            product_data = db_redis.hgetall(product_key)
            if product_data:
                try:
                    preco_atual = float(product_data.get('preco', 0))
                    
                    # Salva preço original se não existir
                    if not db_redis.hexists(product_key, 'preco_original'):
                        db_redis.hset(product_key, 'preco_original', str(preco_atual))
                    
                    novo_preco = preco_atual * (1 - desconto/100)
                    
                    db_redis.hset(product_key, mapping={
                        'preco': f"{novo_preco:.2f}",
                        'desconto_aplicado': f"{desconto}%"
                    })
                    
                    # Renova TTL
                    db_redis.expire(product_key, 3600)
                    updated_count += 1
                except:
                    continue
        
        print(f"✅ Desconto de {desconto}% aplicado em {updated_count} produtos!")
        
    except ValueError:
        print("Valor inválido!")

def update_stock(db_redis):
    """
    Atualiza estoque de um produto específico
    """
    list_migrated_products(db_redis)
    
    product_id = input("\nDigite o ID do produto: ")
    redis_key = f"migrated:product:{product_id}"
    
    if not db_redis.exists(redis_key):
        print("Produto não encontrado no Redis.")
        return
    
    product_data = db_redis.hgetall(redis_key)
    current_stock = product_data.get('estoque', '0')
    
    print(f"Estoque atual: {current_stock}")
    
    try:
        new_stock = int(input("Digite o novo estoque: "))
        db_redis.hset(redis_key, 'estoque', str(new_stock))
        db_redis.expire(redis_key, 3600)  # Renova TTL
        print("✅ Estoque atualizado no Redis!")
    except ValueError:
        print("Valor inválido!")

def search_by_brand(db_redis):
    """
    Busca produtos por marca no Redis
    """
    marca = input("Digite a marca para buscar: ")
    product_keys = db_redis.lrange("migrated:products:all", 0, -1)
    
    encontrados = []
    for product_key in product_keys:
        product_data = db_redis.hgetall(product_key)
        if product_data and marca.lower() in product_data.get('marca', '').lower():
            encontrados.append(product_data)
    
    if encontrados:
        print(f"\n📋 {len(encontrados)} produtos da marca '{marca}':")
        print("-" * 60)
        for prod in encontrados:
            print(f"• {prod.get('produto', 'N/A')} - R$ {prod.get('preco', '0')} - Estoque: {prod.get('estoque', '0')}")
        print("-" * 60)
    else:
        print(f"Nenhum produto da marca '{marca}' encontrado.")

def show_product_details(db_redis):
    """
    Mostra detalhes completos de um produto específico
    """
    product_id = input("Digite o ID do produto: ")
    redis_key = f"migrated:product:{product_id}"
    
    if not db_redis.exists(redis_key):
        print("Produto não encontrado no Redis.")
        return
    
    product_data = db_redis.hgetall(redis_key)
    
    print("\n" + "="*50)
    print("DETALHES DO PRODUTO (Redis)")
    print("="*50)
    print(f"ID: {product_data.get('product_id')}")
    print(f"Produto: {product_data.get('produto')}")
    print(f"Descrição: {product_data.get('descricao')}")
    print(f"Marca: {product_data.get('marca')}")
    print(f"Preço: R$ {product_data.get('preco')}")
    print(f"Estoque: {product_data.get('estoque')}")
    
    if "preco_original" in product_data:
        print(f"Preço Original: R$ {product_data.get('preco_original')}")
    if "desconto_aplicado" in product_data:
        print(f"Desconto Aplicado: {product_data.get('desconto_aplicado')}")
    
    # Mostra vendedor
    try:
        vendedor = json.loads(product_data.get('vendedor', '{}'))
        print(f"\nVendedor: {vendedor.get('nome', 'N/A')}")
        print(f"Email: {vendedor.get('email', 'N/A')}")
        print(f"Telefone: {vendedor.get('telefone', 'N/A')}")
    except:
        print(f"Vendedor: {product_data.get('vendedor', 'N/A')}")
    
    print("="*50)

def sync_products_back_to_mongo(db_redis, product_col):
    """
    Sincroniza produtos modificados do Redis de volta para MongoDB
    """
    print("Sincronizando produtos Redis → MongoDB...")
    
    product_keys = db_redis.lrange("migrated:products:all", 0, -1)
    
    if not product_keys:
        print("Nenhum produto migrado encontrado no Redis.")
        return
    
    updated_count = 0
    from bson import ObjectId
    
    for product_key in product_keys:
        product_data = db_redis.hgetall(product_key)
        
        if product_data:
            try:
                product_id = ObjectId(product_data["product_id"])
                
                # Prepara dados para atualização no MongoDB
                update_data = {
                    "preco": product_data["preco"],
                    "estoque": product_data["estoque"]
                }
                
                # Adiciona campos de manipulação se existirem
                if "preco_original" in product_data:
                    update_data["preco_original"] = product_data["preco_original"]
                if "desconto_aplicado" in product_data:
                    update_data["desconto_aplicado"] = product_data["desconto_aplicado"]
                
                # Atualiza no MongoDB
                result = product_col.update_one(
                    {"_id": product_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    updated_count += 1
                    
            except Exception as e:
                print(f"Erro ao sincronizar produto {product_data.get('product_id')}: {e}")
    
    print(f"✅ {updated_count} produtos sincronizados com MongoDB!")
    input("\nPressione Enter para continuar...")

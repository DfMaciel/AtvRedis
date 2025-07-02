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
            # Verificações de segurança para campos obrigatórios
            product_id = str(product.get("_id", ""))
            if not product_id:
                print(f"Produto sem ID encontrado, pulando...")
                continue
                
            produto_nome = product.get("produto", "Produto sem nome")
            descricao = product.get("descricao", "Sem descrição")
            preco = product.get("preco", 0)
            estoque = product.get("estoque", 0)
            marca = product.get("marca", "Marca não informada")
            
            # Chave para produto migrado
            redis_key = f"migrated:product:{product_id}"
            
            # Prepara dados do vendedor com verificações (schema AtvMongo)
            vendedor_data = {}
            if "vendedor" in product and product["vendedor"]:
                vendedor = product["vendedor"]
                vendedor_data = {
                    "_id": str(vendedor.get("_id", "")),
                    "nome": vendedor.get("nome", "Nome não informado"),
                    "email": vendedor.get("email", "Email não informado"),
                    "endereco": vendedor.get("endereco", "Endereço não informado"),
                    "telefone": vendedor.get("telefone", "Telefone não informado")
                }
            else:
                vendedor_data = {
                    "_id": "",
                    "nome": "Vendedor não informado",
                    "email": "Email não informado",
                    "endereco": "Endereço não informado",
                    "telefone": "Telefone não informado"
                }
            
            # Prepara dados do produto para Redis (schema AtvMongo)
            product_data = {
                "_id": product_id,
                "produto": produto_nome,
                "descricao": descricao,
                "preco": str(preco),
                "estoque": str(estoque),
                "marca": marca,
                "vendedor": json.dumps(vendedor_data)
            }
            
            # Salva no Redis com TTL de 1 hora
            db_redis.hset(redis_key, mapping=product_data)
            db_redis.expire(redis_key, 3600)  # 1 hora
            
            # Adiciona à lista geral de produtos migrados
            db_redis.rpush("migrated:products:all", redis_key)
            
            migrated_count += 1
            print(f"✅ Produto '{produto_nome}' migrado com sucesso!")
            
        except Exception as e:
            product_id_safe = product.get("_id", "ID desconhecido")
            print(f"❌ Erro ao migrar produto {product_id_safe}: {str(e)}")
            continue
    
    print(f"✅ {migrated_count} produtos migrados para Redis!")
    input("\nPressione Enter para continuar...")

def list_migrated_products(db_redis):
    """
    Lista todos os produtos migrados no Redis
    """
    try:
        product_keys = db_redis.lrange("migrated:products:all", 0, -1)
        
        if not product_keys:
            print("❌ Nenhum produto migrado encontrado no Redis.")
            return []
        
        print(f"\n📋 {len(product_keys)} Produto(s) Migrado(s) no Redis:")
        print("-" * 80)
        
        products_list = []
        for i, product_key in enumerate(product_keys, 1):
            try:
                product_data = db_redis.hgetall(product_key)
                if product_data:
                    # Trata dados binários do Redis
                    product_info = {}
                    for key, value in product_data.items():
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                        product_info[key] = value
                    
                    products_list.append(product_info)
                    
                    # Trata vendedor
                    vendedor_nome = "N/A"
                    try:
                        vendedor_data = json.loads(product_info.get('vendedor', '{}'))
                        vendedor_nome = vendedor_data.get('nome', 'N/A')
                    except:
                        pass
                    
                    print(f"{i}. ID: {product_info.get('_id', 'N/A')}")
                    print(f"   Produto: {product_info.get('produto', 'N/A')}")
                    print(f"   Marca: {product_info.get('marca', 'N/A')}")
                    print(f"   Preço: R$ {product_info.get('preco', '0.00')}")
                    print(f"   Estoque: {product_info.get('estoque', '0')}")
                    print(f"   Vendedor: {vendedor_nome}")
                    
                    # Mostra TTL
                    ttl_seconds = db_redis.ttl(product_key)
                    if ttl_seconds > 0:
                        ttl_minutes = ttl_seconds // 60
                        ttl_remaining = ttl_seconds % 60
                        print(f"   ⏰ TTL: {ttl_minutes}m {ttl_remaining}s")
                    elif ttl_seconds == -1:
                        print(f"   ⏰ TTL: Sem expiração")
                    else:
                        print(f"   ⏰ TTL: Expirado")
                    
                    print("-" * 40)
                    
            except Exception as e:
                print(f"❌ Erro ao processar produto {i}: {e}")
                continue
        
        print("-" * 80)
        return products_list
        
    except Exception as e:
        print(f"❌ Erro ao listar produtos: {e}")
        return []

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
        print("5 - Mostrar estatísticas do cache")
        print("6 - Voltar")
        
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
            show_cache_statistics(db_redis)
        elif opcao == 6:
            break
        else:
            print("Opção inválida!")

def apply_discount(db_redis):
    """
    Aplica desconto em todos os produtos migrados
    """
    try:
        desconto = float(input("Digite o percentual de desconto (ex: 10 para 10%): "))
        
        if desconto < 0 or desconto > 100:
            print("❌ Desconto deve ser entre 0 e 100%!")
            return
        
        product_keys = db_redis.lrange("migrated:products:all", 0, -1)
        if not product_keys:
            print("Nenhum produto migrado encontrado.")
            return
        
        updated_count = 0
        for product_key in product_keys:
            product_data = db_redis.hgetall(product_key)
            if product_data:
                try:
                    # Converte dados binários para string
                    product_info = {}
                    for key, value in product_data.items():
                        if isinstance(key, bytes):
                            key = key.decode('utf-8')
                        if isinstance(value, bytes):
                            value = value.decode('utf-8')
                        product_info[key] = value
                    
                    preco_atual = float(product_info.get('preco', '0'))
                    
                    if preco_atual <= 0:
                        print(f"⚠️ Produto {product_info.get('produto', 'N/A')} tem preço inválido: {preco_atual}")
                        continue
                    
                    # Salva preço original se não existir
                    if not db_redis.hexists(product_key, 'preco_original'):
                        db_redis.hset(product_key, 'preco_original', str(preco_atual))
                    
                    novo_preco = preco_atual * (1 - desconto/100)
                    
                    db_redis.hset(product_key, mapping={
                        'preco': f"{novo_preco:.2f}",
                        'desconto_aplicado': f"{desconto}%"
                    })
                    
                    # Renova TTL para 1 hora
                    db_redis.expire(product_key, 3600)
                    updated_count += 1
                    
                    print(f"✅ {product_info.get('produto', 'N/A')}: R$ {preco_atual:.2f} → R$ {novo_preco:.2f}")
                    
                except ValueError as ve:
                    print(f"❌ Erro de conversão para produto {product_key}: {ve}")
                    continue
                except Exception as e:
                    print(f"❌ Erro ao processar produto {product_key}: {e}")
                    continue
        
        print(f"\n🎉 Desconto de {desconto}% aplicado em {updated_count} produtos!")
        print(f"⏰ TTL renovado para 1 hora (3600 segundos)")
        
    except ValueError:
        print("❌ Valor de desconto inválido!")

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
    
    # Converte dados binários para string
    product_info = {}
    for key, value in product_data.items():
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        product_info[key] = value
    
    current_stock = product_info.get('estoque', '0')
    
    print(f"Estoque atual: {current_stock}")
    
    # Verifica TTL
    ttl_seconds = db_redis.ttl(redis_key)
    if ttl_seconds > 0:
        ttl_minutes = ttl_seconds // 60
        print(f"⏰ Tempo restante em cache: {ttl_minutes}m {ttl_seconds % 60}s")
    
    try:
        new_stock = int(input("Digite o novo estoque: "))
        if new_stock < 0:
            print("❌ Estoque não pode ser negativo!")
            return
            
        db_redis.hset(redis_key, 'estoque', str(new_stock))
        db_redis.expire(redis_key, 3600)  # Renova TTL para 1 hora
        print("✅ Estoque atualizado no Redis!")
        print("⏰ TTL renovado para 1 hora")
    except ValueError:
        print("❌ Valor inválido!")

def search_by_brand(db_redis):
    """
    Busca produtos por marca no Redis
    """
    marca = input("Digite a marca para buscar: ")
    product_keys = db_redis.lrange("migrated:products:all", 0, -1)
    
    if not product_keys:
        print("❌ Nenhum produto migrado encontrado.")
        return
    
    encontrados = []
    for product_key in product_keys:
        product_data = db_redis.hgetall(product_key)
        if product_data:
            # Converte dados binários para string
            product_info = {}
            for key, value in product_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                product_info[key] = value
            
            if marca.lower() in product_info.get('marca', '').lower():
                encontrados.append(product_info)
    
    if encontrados:
        print(f"\n📋 {len(encontrados)} produtos da marca '{marca}':")
        print("-" * 60)
        for prod in encontrados:
            # Verifica TTL
            redis_key = f"migrated:product:{prod.get('_id', '')}"
            ttl_seconds = db_redis.ttl(redis_key)
            if ttl_seconds > 0:
                ttl_info = f"({ttl_seconds//60}m restantes)"
            else:
                ttl_info = "(sem TTL)"
                
            print(f"• {prod.get('produto', 'N/A')} - R$ {prod.get('preco', '0')} - Estoque: {prod.get('estoque', '0')} {ttl_info}")
        print("-" * 60)
    else:
        print(f"❌ Nenhum produto da marca '{marca}' encontrado.")

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
    
    # Converte dados binários do Redis para string
    product_info = {}
    for key, value in product_data.items():
        if isinstance(key, bytes):
            key = key.decode('utf-8')
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        product_info[key] = value
    
    # Verifica TTL (tempo restante em cache)
    ttl_seconds = db_redis.ttl(redis_key)
    if ttl_seconds > 0:
        ttl_minutes = ttl_seconds // 60
        ttl_remaining = ttl_seconds % 60
        time_info = f"{ttl_minutes}m {ttl_remaining}s"
    elif ttl_seconds == -1:
        time_info = "Sem expiração"
    else:
        time_info = "Expirado"
    
    print("\n" + "="*50)
    print("DETALHES DO PRODUTO (Redis)")
    print("="*50)
    print(f"ID: {product_info.get('_id', 'N/A')}")
    print(f"Produto: {product_info.get('produto', 'N/A')}")
    print(f"Descrição: {product_info.get('descricao', 'N/A')}")
    print(f"Marca: {product_info.get('marca', 'N/A')}")
    print(f"Preço: R$ {product_info.get('preco', '0.00')}")
    print(f"Estoque: {product_info.get('estoque', '0')}")
    print(f"⏰ Tempo em cache: {time_info}")
    
    if "preco_original" in product_info:
        print(f"Preço Original: R$ {product_info.get('preco_original')}")
    if "desconto_aplicado" in product_info:
        print(f"Desconto Aplicado: {product_info.get('desconto_aplicado')}")
    
    # Mostra vendedor (schema AtvMongo)
    try:
        vendedor = json.loads(product_info.get('vendedor', '{}'))
        print(f"\nVendedor: {vendedor.get('nome', 'N/A')}")
        print(f"Email: {vendedor.get('email', 'N/A')}")
        print(f"Endereço: {vendedor.get('endereco', 'N/A')}")
        print(f"Telefone: {vendedor.get('telefone', 'N/A')}")
    except:
        print(f"Vendedor: {product_info.get('vendedor', 'N/A')}")
    
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
                # Converte dados binários do Redis para string
                product_info = {}
                for key, value in product_data.items():
                    if isinstance(key, bytes):
                        key = key.decode('utf-8')
                    if isinstance(value, bytes):
                        value = value.decode('utf-8')
                    product_info[key] = value
                
                # Obtém o ID do produto e valida
                product_id_str = product_info.get("_id", "")
                if not product_id_str or len(product_id_str) != 24:
                    print(f"❌ ID inválido para produto: '{product_id_str}'")
                    continue
                
                try:
                    product_id = ObjectId(product_id_str)
                except Exception as e:
                    print(f"❌ Erro ao converter ID '{product_id_str}' para ObjectId: {e}")
                    continue
                
                # Converte valores de volta para tipos corretos
                preco_value = product_info.get("preco", "0")
                estoque_value = product_info.get("estoque", "0")
                
                try:
                    preco_float = float(preco_value)
                    estoque_int = int(estoque_value)
                except (ValueError, TypeError) as e:
                    print(f"❌ Erro ao converter valores do produto {product_id_str}: {e}")
                    continue
                
                # Prepara dados para atualização no MongoDB
                update_data = {
                    "preco": preco_float,
                    "estoque": estoque_int
                }
                
                # Adiciona campos de manipulação se existirem
                if "preco_original" in product_info:
                    try:
                        update_data["preco_original"] = float(product_info["preco_original"])
                    except (ValueError, TypeError):
                        pass
                        
                if "desconto_aplicado" in product_info:
                    update_data["desconto_aplicado"] = product_info["desconto_aplicado"]
                
                # Atualiza no MongoDB
                result = product_col.update_one(
                    {"_id": product_id},
                    {"$set": update_data}
                )
                
                if result.modified_count > 0:
                    updated_count += 1
                    produto_nome = product_info.get('produto', 'N/A')
                    print(f"✅ Produto '{produto_nome}' (ID: {product_id_str}) sincronizado!")
                elif result.matched_count > 0:
                    print(f"⚠️ Produto {product_id_str} encontrado mas sem alterações")
                else:
                    print(f"❌ Produto {product_id_str} não encontrado no MongoDB")
                    
            except Exception as e:
                product_id_display = product_info.get('_id', 'ID desconhecido') if 'product_info' in locals() else 'ID desconhecido'
                print(f"❌ Erro geral ao sincronizar produto {product_id_display}: {e}")
                continue
    
    if updated_count > 0:
        print(f"\n🎉 {updated_count} produto(s) sincronizado(s) com sucesso Redis → MongoDB!")
        
        # Opcional: limpar Redis após sincronização
        clear_redis = input("Deseja limpar os produtos do Redis após sincronização? (S/N): ").lower()
        if clear_redis == 's':
            for key in product_keys:
                db_redis.delete(key)
            db_redis.delete("migrated:products:all")
            print("🗑️  Produtos removidos do Redis.")
    else:
        print("❌ Nenhum produto foi sincronizado.")
    
    input("\nPressione Enter para continuar...")

def show_cache_statistics(db_redis):
    """
    Mostra estatísticas do cache Redis dos produtos
    """
    product_keys = db_redis.lrange("migrated:products:all", 0, -1)
    
    if not product_keys:
        print("❌ Nenhum produto migrado encontrado no Redis.")
        return
    
    print("\n📊 ESTATÍSTICAS DO CACHE REDIS")
    print("="*50)
    print(f"Total de produtos em cache: {len(product_keys)}")
    
    # Contadores
    expired_count = 0
    permanent_count = 0
    active_count = 0
    total_discounts = 0
    min_ttl = float('inf')
    max_ttl = 0
    
    for product_key in product_keys:
        ttl = db_redis.ttl(product_key)
        
        if ttl == -2:  # Chave não existe
            expired_count += 1
        elif ttl == -1:  # Sem expiração
            permanent_count += 1
        else:  # TTL ativo
            active_count += 1
            if ttl < min_ttl:
                min_ttl = ttl
            if ttl > max_ttl:
                max_ttl = ttl
        
        # Verifica se tem desconto aplicado
        if db_redis.hexists(product_key, 'desconto_aplicado'):
            total_discounts += 1
    
    print(f"Produtos ativos: {active_count}")
    print(f"Produtos expirados: {expired_count}")
    print(f"Produtos permanentes: {permanent_count}")
    print(f"Produtos com desconto aplicado: {total_discounts}")
    
    if active_count > 0:
        print(f"\nTempo de vida (TTL):")
        print(f"  Menor TTL: {min_ttl//60}m {min_ttl%60}s")
        print(f"  Maior TTL: {max_ttl//60}m {max_ttl%60}s")
        print(f"  TTL médio: {((min_ttl + max_ttl) // 2)//60}m {((min_ttl + max_ttl) // 2)%60}s")
    
    # Uso de memória (aproximado)
    memory_usage = 0
    for product_key in product_keys:
        memory_usage += db_redis.memory_usage(product_key) or 0
    
    if memory_usage > 0:
        print(f"\nUso de memória aproximado: {memory_usage} bytes ({memory_usage/1024:.2f} KB)")
    
    print("="*50)

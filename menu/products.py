from service.products.migrate import migrate_products, list_migrated_products, manipulate_products, sync_products_back_to_mongo
from service.auth import user_logged

def manager_products(product_col, db_redis, user):
    while True:

        if not user_logged(db_redis, user['email']):
            print("Sessão expirada. Por favor, faça login novamente.")
            return
        
        print("-=" * 20)
        print("      Gerenciador de Produtos")
        print("-=" * 20)
        print("1. Migrar produtos MongoDB → Redis")
        print("2. Listar produtos migrados")
        print("3. Manipular produtos no Redis")
        print("4. Sincronizar produtos Redis → MongoDB")
        print("5. Sair")
        print("-=" * 20)

        try:
            choice = int(input("Digite a opção desejada: "))
        except ValueError:
            print("Opção inválida! Escolha novamente.")
            continue

        if choice == 1:
            migrate_products(product_col, db_redis)
        elif choice == 2:
            list_migrated_products(db_redis)
            input("\nPressione Enter para continuar...")
        elif choice == 3:
            manipulate_products(db_redis)
        elif choice == 4:
            sync_products_back_to_mongo(db_redis, product_col)
        elif choice == 5:
            print("Saindo do Gerenciador de Produtos.")
            break
        else:
            print("Opção inválida. Tente novamente.")

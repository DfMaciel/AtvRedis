from service.purchases.add import add_purchase
from service.purchases.sync import sync_purchases
from service.purchases.list import list_purchases
from service.auth import user_logged

def manager_purchases(product_col, purchase_col, db_redis, user, user_col):
    while True:

        if not user_logged(db_redis, user['email']):
            print("Sessão expirada. Por favor, faça login novamente.")
            return
        
        print("-=" * 20)
        print("      Gerenciador de Compras")
        print("-=" * 20)
        print("1. Adicionar Compra")
        print("2. Listar Compras")
        print("3. Sincronizar com MongoDB")
        print("4. Sair")
        print("-=" * 20)

        try:
            choice = int(input("Digite a opção desejada: "))
        except ValueError:
            print("Opção inválida! Escolha novamente.")
            continue

        if choice == 1:
            add_purchase(product_col, purchase_col, db_redis, user)
        elif choice == 2:
            list_purchases(db_redis, user)
        elif choice == 3:
            sync_purchases(db_redis, user_col, user)
        elif choice == 4:
            print("Saindo do Gerenciador de Compras.")
            break
        else:
            print("Opção inválida. Tente novamente.")

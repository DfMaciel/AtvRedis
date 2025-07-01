from service.favorites.add import add_favorite
from service.favorites.remove import remove_favorite
from service.favorites.sync import sync_favorites
from service.favorites.list import list_favorites
from service.auth import user_logged

def manager_favorites(product_col, db_redis, user, user_col):
    while True:

        if not user_logged(db_redis, user['email']):
            print("Sessão expirada. Por favor, faça login novamente.")
            return
        
        print("-="*20)
        print("      Gerenciador de Favoritos")
        print("-="*20)
        print("1. Adicionar Favorito")
        print("2. Remover Favorito")
        print("3. Sincronizar com MongoDB")
        print("4. Listar Favoritos")
        print("5. Sair")
        print("-="*20)

        try:
            choice = int(input("Digite a opção desejada: "))
        except ValueError:
            print("Opção inválida! Escolha novamente.")
            continue

        if choice == 1:
            add_favorite(product_col, db_redis, user)
        elif choice == 2:
            remove_favorite(product_col, db_redis, user)
        elif choice == 3:
            sync_favorites(db_redis, user_col, user)
        elif choice == 4:
            list_favorites(db_redis, user)
        elif choice == 5:
            print("Saindo do Gerenciador de Favoritos.")
            break
        else:
            print("Opção inválida. Tente novamente.")
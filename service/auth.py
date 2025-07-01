from utils.utils import find_user

def login(user_col, db_redis, user_email, user_password):
    user = find_user(user_email, user_col)
    if user is None:
        return print('Usuario não encontrado!')
    
    if user_password == user['senha']:
        db_redis.setex(f'user:{user_email}', 3600, user_email)
        print(f"Usuário {user_email} logado com sucesso por 1 hora!")
        return user
    else:
        print('Senha incorreta.')
        return None
    
def user_logged(db_redis, user_email):
    return db_redis.exists(f'user:{user_email}')


import redis

def connection_redis():
    try:
        r = redis.Redis(
        host='redis-14460.c114.us-east-1-4.ec2.redns.redis-cloud.com',
        port=14460,
        password='bcLdN3w4ZkWIQVVCLu5t3BRjFkuWUbby')
        r.ping()
        print('Redis conectado!')
        return r 
    except redis.ConnectionError:
        print('Erro ao conectar ao Redis')
        return None
    except Exception as e:
        print(f'Ocorreu um erro: {e}')  
        return None

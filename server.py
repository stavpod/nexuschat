import socket
import threading
import os
import time

# --- НАСТРОЙКИ СЕРВЕРА ---
# HOST: 0.0.0.0 означает, что сервер будет слушать все доступные сетевые интерфейсы.
# Это обязательно для работы на Render.com или любой другой облачной платформе.
HOST = '0.0.0.0'

# PORT: Берем порт из системной переменной окружения 'PORT' (предоставляется Render).
# Если переменная не найдена (т.е. запуск на локальном ПК), используем 8080.
PORT = int(os.environ.get('PORT', 8080))

# Словарь для хранения активных клиентов: {'username': socket_object}
clients = {}
threads = [] 
# --- КОНЕЦ НАСТРОЕК ---

def broadcast(message, sender_username=None):
    """
    Отправляет сообщение всем подключенным клиентам, кроме отправителя.
    """
    if not message:
        return

    formatted_message = f"[{time.strftime('%H:%M:%S')}] {message}"
    encoded_message = formatted_message.encode('utf-8')
    
    for username, client_socket in clients.items():
        try:
            client_socket.send(encoded_message)
        except Exception as e:
            # Клиент отключился
            pass


def handle_client(client_socket, client_address):
    """
    Обрабатывает соединение с одним клиентом (в отдельном потоке).
    """
    username = None
    
    try:
        # 1. Получаем имя пользователя (первое сообщение от клиента)
        # Устанавливаем таймаут на 10 секунд для первой передачи
        client_socket.settimeout(10.0) 
        username_raw = client_socket.recv(1024)
        
        if not username_raw:
            return 
            
        username = username_raw.decode('utf-8').strip()
        client_socket.settimeout(None) # Убираем таймаут
        
        if not username or username in clients:
            client_socket.send("STATUS: Username already taken or invalid.".encode('utf-8'))
            return
            
        clients[username] = client_socket
        print(f"[NEW USER] {username} connected from {client_address[0]}:{client_address[1]}")
        broadcast(f"--- {username} joined the chat. Total users: {len(clients)} ---")

        # 2. Основной цикл получения сообщений
        while True:
            message_raw = client_socket.recv(1024)
            if not message_raw:
                break # Клиент отключился
            
            message = message_raw.decode('utf-8')
            full_message = f"<{username}>: {message}"
            print(f"[MESSAGE] {full_message}")
            
            broadcast(full_message, sender_username=username)

    except socket.timeout:
        print(f"[TIMEOUT] Connection from {client_address} timed out during username reception.")
    except ConnectionResetError:
        pass
    except Exception as e:
        print(f"[ERROR] An unexpected error occurred with {client_address}: {e}")

    finally:
        # 3. Очистка после отключения
        if username in clients:
            del clients[username]
            print(f"[DISCONNECTED] {username} disconnected.")
            broadcast(f"--- {username} left the chat. Total users: {len(clients)} ---")
        try:
            client_socket.close()
        except:
            pass

def start_server():
    """
    Инициализирует и запускает сервер.
    """
    try:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Chat server started successfully on {HOST}:{PORT}")
    except Exception as e:
        # Это то место, где была ошибка 'Serveo'
        print(f"FATAL ERROR: Could not start server on {HOST}:{PORT}. Error: {e}")
        return

    # Основной цикл приема входящих подключений
    while True:
        try:
            client_socket, client_address = server.accept()
            client_thread = threading.Thread(
                target=handle_client, 
                args=(client_socket, client_address)
            )
            client_thread.start()
            threads.append(client_thread)
            
        except KeyboardInterrupt:
            print("\nServer shutting down...")
            break
        except Exception as e:
            continue

if __name__ == "__main__":
    start_server()

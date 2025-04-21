from flask import Flask, request, jsonify
import json
import requests # Para enviar comandos ao IoTA
import os

app = Flask(__name__)

# --- CONFIGURAÇÕES ---
# Valores baseados no seu docker-compose.yml (assumindo que este script roda como container na mesma rede)

# Host (endereço) onde o Orion Context Broker está escutando.
# No docker-compose, o nome do serviço é 'orion'. Containers na mesma rede se encontram por este nome.
ORION_HOST = 'orion'

# Porta em que o Orion Context Broker está escutando.
# No docker-compose, a porta interna é 1026 (mapeada como "1026:1026").
ORION_PORT = 1026

# Host (endereço) onde o FIWARE IoT Agent está escutando para comandos/administração.
# No docker-compose, o nome do serviço é 'iot-agent'.
IOTA_HOST = 'iot-agent'

# Porta de ADMINISTRAÇÃO/COMANDO do IoT Agent.
# No docker-compose, a porta interna é 4041 (mapeada como "4041:4041" e definida em IOTA_NORTH_PORT).
# Esta é a porta usada para enviar comandos *para* o IoTA.
IOTA_ADMIN_PORT = 4041

# Chave de API (API Key) usada para autenticar dispositivos no IoT Agent.
# !! IMPORTANTE !! Este valor NÃO está no docker-compose.
# Você DEVE usar a mesma chave que configurou no seu ESP32 e/ou ao provisionar o dispositivo.
# Substitua 'YOUR_API_KEY' pela sua chave real.
API_KEY = 'YOUR_API_KEY' # <-- SUBSTITUA PELA SUA API KEY REAL

# Cabeçalho Fiware-Service.
# !! IMPORTANTE !! Verifique qual Fiware-Service você está usando nas suas requisições (Postman, ESP32).
# Se não especificou nenhum, 'openiot' pode ser o padrão, mas confirme.
FIWARE_SERVICE = 'openiot' # <-- VERIFIQUE E AJUSTE SE NECESSÁRIO

# Cabeçalho Fiware-ServicePath.
# !! IMPORTANTE !! Verifique qual Fiware-ServicePath você está usando.
# '/' é o mais comum se você não criou sub-caminhos.
FIWARE_SERVICEPATH = '/' # <-- VERIFIQUE E AJUSTE SE NECESSÁRIO

# --- FIM DAS CONFIGURAÇÕES ---

# Caminho absoluto para o arquivo JSON de autorizados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_FILE_PATH = os.path.join(BASE_DIR, 'autorizados.json')

def carregar_autorizados():
    """Carrega os cartões autorizados do arquivo JSON."""
    try:
        with open(JSON_FILE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {JSON_FILE_PATH} não encontrado.")
        return {}
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar JSON em {JSON_FILE_PATH}.")
        return {}
    except Exception as e:
        print(f"Erro inesperado ao carregar {JSON_FILE_PATH}: {e}")
        return {}

def send_iota_command(device_id, command_name, command_value):
    """Envia um comando para um dispositivo via IoT Agent."""
    # Monta a URL para o endpoint de comando específico do dispositivo no IoT Agent
    url = f'http://{IOTA_HOST}:{IOTA_ADMIN_PORT}/iot/devices/{device_id}/commands/{command_name}'

    # Cabeçalhos necessários para a requisição ao IoT Agent
    headers = {
        'Content-Type': 'application/json',
        'fiware-service': FIWARE_SERVICE,
        'fiware-servicepath': FIWARE_SERVICEPATH
    }

    # Parâmetros de query string (API Key é essencial aqui)
    params = {'k': API_KEY, 'i': device_id} # 'i' (device ID) é redundante na URL mas pode ser esperado por algumas versões

    # Payload do comando. A estrutura exata pode depender do comando e do IoTA.
    # Para comandos simples que o ESP32 espera (como no exemplo anterior que só olha o valor),
    # enviar o valor diretamente pode funcionar se o IoTA repassar.
    # Uma estrutura mais padrão seria {"comando": "valor"}
    payload = { command_name : command_value } # Enviando { "controlDoor": "GRANTED" } ou { "controlDoor": "DENIED" }

    print(f"Enviando comando para IoTA:")
    print(f"  URL: {url}")
    print(f"  Headers: {headers}")
    print(f"  Params: {params}")
    print(f"  Payload: {json.dumps(payload)}")

    try:
        response = requests.post(url, headers=headers, json=payload, params=params, timeout=10)
        # Verifica se a requisição foi bem sucedida (status code 2xx)
        response.raise_for_status()
        print(f"  Comando enviado com sucesso! Status: {response.status_code}, Resposta: {response.text}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"  Erro ao enviar comando para o IoT Agent: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"  Resposta do IoTA (erro): {e.response.status_code} {e.response.text}")
        return False

@app.route('/notify', methods=['POST'])
def handle_orion_notification():
    """Recebe notificações do Orion sobre mudanças no 'lastCardRead'."""
    print("\n--- Notificação recebida do Orion ---")
    notification = request.get_json()
    print(json.dumps(notification, indent=2))

    autorizados = carregar_autorizados()

    # Extrai os dados relevantes da notificação
    try:
        if 'data' in notification and len(notification['data']) > 0:
            entity = notification['data'][0]
            if 'id' in entity and 'type' in entity and 'lastCardRead' in entity and 'value' in entity['lastCardRead']:
                entity_id = entity['id']
                entity_type = entity['type']
                card_id = entity['lastCardRead']['value']

                print(f"Entidade: {entity_id} ({entity_type}), Cartão Lido: {card_id}")

                # IMPORTANTE: Mapear entity_id para device_id
                # O comando é enviado ao IoTA usando o device_id (ex: 'esp32-access-001'),
                # mas a notificação do Orion vem com o entity_id (ex: 'urn:ngsi-ld:AccessPoint:001').
                # Você precisa de uma forma de saber qual device_id corresponde a qual entity_id.
                # Opções:
                # 1. Fazer o device_id ser igual ao entity_id (se possível/permitido).
                # 2. Armazenar esse mapeamento em algum lugar (ex: outro arquivo, BD, ou como atributo estático no IoTA).
                # 3. Assumir um mapeamento fixo se você só tem um dispositivo.
                # Vamos assumir um mapeamento fixo para este exemplo:
                if entity_id == "urn:ngsi-ld:AccessPoint:001": # Ajuste para seu entity_id real
                    device_id = "esp32-access-001" # Ajuste para seu device_id real
                else:
                    print(f"Erro: Não foi possível mapear entity_id {entity_id} para um device_id conhecido.")
                    return jsonify({"status": "erro", "mensagem": "Mapeamento entity/device não encontrado"}), 400

                # Verifica se o cartão lido está na lista de autorizados
                if card_id in autorizados:
                    usuario = autorizados[card_id]
                    print(f"Cartão {card_id} AUTORIZADO para {usuario}. Enviando comando GRANTED.")
                    send_iota_command(device_id, "controlDoor", "GRANTED") # Nome do comando definido no provisionamento
                else:
                    print(f"Cartão {card_id} NEGADO. Enviando comando DENIED.")
                    send_iota_command(device_id, "controlDoor", "DENIED") # Nome do comando definido no provisionamento
            else:
                print("Notificação não contém os atributos esperados (id, type, lastCardRead.value).")
        else:
             print("Formato de notificação inesperado (sem 'data' ou 'data' vazio).")

    except Exception as e:
        print(f"Erro ao processar notificação: {e}")
        return jsonify({"status": "erro interno"}), 500

    return jsonify({"status": "notificacao recebida"}), 200

if __name__ == '__main__':
    # Escuta em todas as interfaces na porta 5050 (ou outra)
    # Garanta que esta porta esteja acessível PELOS OUTROS CONTAINERS (Orion)
    print("Iniciando serviço de validação na porta 5050...")
    app.run(host='0.0.0.0', port=5050, debug=True) # Use debug=False em produção
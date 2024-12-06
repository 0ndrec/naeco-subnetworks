import json
import os
import sys
from eth_account import Account

def generate_wallet() -> dict:
    account = Account.create()
    return {
        "address": account.address,
        "private_key": '0x' + account._private_key.hex()
    }

def generate_wallets(count) -> list[dict]:
    return [generate_wallet() for _ in range(count)]

def read_wallets_from_txt(path) -> list[dict]:
    dict = {"address": "", "private_key": ""}
    with open(path, "r") as file:
        # формат wallets.txt: 0xPRIVATE_KEY[space]0xADDRESS
        return [dict | {"address": line.split()[1], "private_key": line.split()[0]} for line in file]

def save_wallets_to_json(wallets):
    with open("wallets.json", "w") as json_file:
        json.dump(wallets, json_file, indent=4)
    print("Generated wallets saved to wallets.json")


rpcs = {}

rpcs_json = json.dumps(rpcs)

def create_ocean_node_compose(wallet, i, ip_address, count_network):
    http_api_port = 2002 + i
    p2p_tcp_port = 3002 + i
    p2p_ws_port = 4002 + i
    typesense_api_key = 'inTheBestDkNodes'
    admin_password = 'DkNodes'

    # Определяем номер сети
    network_index = (i // count_network) + 1

    docker_compose_template = f"""
    services:
      ocean-node{i + 1}:
        image: oceanprotocol/ocean-node:latest
        pull_policy: always
        container_name: ocean-node-{i + 1}
        restart: on-failure
        deploy:
            resources:
                limits:
                    memory: '700m'
        oom_kill_disable: true
        ports:
          - "{http_api_port}:{http_api_port}"
          - "{p2p_tcp_port}:{p2p_tcp_port}"
          - "{p2p_ws_port}:{p2p_ws_port}"
          - "{5002 + i}:{5002 + i}"
          - "{6002 + i}:{6002 + i}"
        environment:
          PRIVATE_KEY: '{wallet['private_key']}'
          DB_URL: 'http://typesense:{8108 + i}/?apiKey=inTheBestDkNodes'
          IPFS_GATEWAY: 'https://ipfs.io/'
          ARWEAVE_GATEWAY: 'https://arweave.net/'
          INTERFACES: '["HTTP","P2P"]'
          ALLOWED_ADMINS: '["{wallet['address']}"]'
          HTTP_API_PORT: '{http_api_port}'
          P2P_ENABLE_IPV4: 'true'
          P2P_ipV4BindAddress: '0.0.0.0'
          P2P_ipV4BindTcpPort: '{p2p_tcp_port}'
          P2P_ipV4BindWsPort: '{p2p_ws_port}'
          P2P_ANNOUNCE_ADDRESSES: '["/ip4/{ip_address}/tcp/{p2p_tcp_port}", "/ip4/{ip_address}/ws/tcp/{p2p_ws_port}"]'
        networks:
          - ocean_network_{network_index}
    """

    # Добавляем контейнер `typesense`, если это первый узел для данной сети
    if (i % count_network) == 0:
        docker_compose_template += f"""
      typesense-{i + 1}:
        image: typesense/typesense:26.0
        container_name: typesense-{i + 1}
        ports:
          - "{8108 + i}:{8108 + i}"
        environment:
          TYPESENSE_API_KEY: '{typesense_api_key}'
          ADMIN_PASSWORD: '{admin_password}'
        networks:
          - ocean_network_{network_index}
        volumes:
          - typesense-data-{i + 1}:/data
        command: '--data-dir /data --api-key={typesense_api_key} --enable-authentication=true --admin-password={admin_password}'
    """

    # Определение секции volumes
    docker_compose_template += f"""
    volumes:
      typesense-data-{i + 1}:
        driver: local

    networks:
    """

    # Добавляем определение всех сетей с драйвером bridge
    for net_index in range(1, (i // count_network) + 2):
        docker_compose_template += f"""
      ocean_network_{net_index}:
        driver: bridge
        ipam:
          config:
            - subnet: '192.168.{net_index}.0/24'
              gateway: '192.168.{net_index}.1'
    """

    save_docker_compose_file(docker_compose_template, i)
    print(f"Generated docker-compose{i + 1}.yaml for ocean-node-{i + 1}")

def save_docker_compose_file(content, i):
    filename = f'docker-compose{i + 1}.yaml'
    with open(filename, 'w') as file:
        file.write(content)

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 script.py <IP_ADDRESS> <NUM_NODES> <NUM_NETWORKS>")
        print("For read from wallets.txt use python3 script.py <IP_ADDRESS> 0")
        sys.exit(1)

    ip_address = sys.argv[1]
    num_files = int(sys.argv[2])
    count_network = int(sys.argv[3])
    if num_files:
        wallets = generate_wallets(num_files)
    else :
        wallets = read_wallets_from_txt("wallets.txt")
    save_wallets_to_json(wallets)

    for i, wallet in enumerate(wallets, start=0):
        create_ocean_node_compose(wallet, i, ip_address, count_network)

if __name__ == "__main__":
    main()

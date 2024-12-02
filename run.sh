#!/bin/bash


get_ip_address() {
    ip_address=$(hostname -I | awk '{print $1}')
    if [[ -z "$ip_address" ]]; then
        echo -ne "Unable to determine IP address automatically. Please enter the IP address: "
        read ip_address
    fi
    echo "$ip_address"
}


get_count() {
    if [ -f "wallets.txt" ]; then
        count=$(wc -l < "wallets.txt")
        echo "$count"
    fi
}

prepare_env() {

    # Run in silent
    sudo apt update && sudo apt upgrade -y > /dev/null
    sudo apt install -y docker.io python3 python3-pip cron > /dev/null
    sudo systemctl start docker
    sudo systemctl enable docker

    # Install Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    # Install Python libraries
    pip3 install --upgrade pip
    pip3 install requests eth_account
}

show_menu() {
    clear
    current_dir=$(pwd)
    ip_address=$(get_ip_address)
    founded_wallets_count=$(get_count)

    echo -e "    Current Directory: ${current_dir}"
    echo -e "    IP Address: ${ip_address}"
    echo -e "    Founded Wallets: ${founded_wallets_count}"

    echo
    echo -e "    Please choose an option:"
    echo
    echo -e "    1. Install Nodes from listfile"
    echo -e "    2. View logs of Ocean nodes"
    echo -e "    3. Stop All Nodes"
    echo -e "    4. Start All Nodes"
    echo -e "    5. Delete all containers and images"
    echo -e "    0. Exit"
    echo

    echo -ne "    Enter your choice: "
    read choice
}



install_nodes() {


    prepare_env

    num_nodes = $(get_count)
    # Get IP address
    ip_address=$(get_ip_address)

    echo -ne "Enter the number of nodes in each network: "
    read networks

    python3 script.py "$ip_address" 0 "$networks"

    for ((i=1; i<=num_nodes; i++)); do
        if [ -f "docker-compose$i.yaml" ]; then
            docker-compose -f docker-compose$i.yaml build >> ocean.log 2>&1
            if [ $? -ne 0 ]; then
                echo -e "Node $i failed to build. Check ocean.log for details."
            else
                echo -e "Node $i built successfully."
            fi
        else
            echo -e "docker-compose$i.yaml not found. Skipping."
        fi
        sleep 5
    done

    # Add crontab entry
    current_dir=$(pwd)
    (crontab -l 2>/dev/null | grep -v "req.py"; echo "0 * * * * python3 $current_dir/req.py $ip_address $current_dir") | crontab -

    echo -e "Compose build complete."
    read -p "Press Enter to return to the main menu..."
}

start_nodes() {
    num_nodes=$(get_count)

    # Validate input
    if ! [[ "$num_nodes" =~ ^[0-9]+$ ]]; then
        echo -e "Invalid input. Please enter a valid number."
        return
    fi

    ip_address=$(get_ip_address)
    echo -e "  Starting Nodes..."

    for ((i=1; i<=num_nodes; i++)); do
        if [ -f "docker-compose$i.yaml" ]; then
            docker-compose -f docker-compose$i.yaml up -d >> ocean.log 2>&1
            if [ $? -ne 0 ]; then
                echo -e "Node $i failed to start. Check ocean.log for details."
            else
                echo -e "Node $i started successfully."
            fi
        else
            echo -e "docker-compose$i.yaml not found. Skipping."
        fi
        sleep 2
    done


    echo -e "Nodes started successfully."
    read -p "Press Enter to return to the main menu..."
}

check_log_compose() {
    #Rean num node
    echo -ne "Enter the number of node: "
    read num_node

    if [ -f "docker-compose$num_node.yaml" ]; then
        docker-compose -f docker-compose$num_node.yaml logs -f >> ocean.log 2>&1
    else
        echo -e "docker-compose$num_node.yaml not found. Skipping."
    fi
}

stop_all_nodes() {
    #get list of all running containers
    running_containers=$(docker ps -q)

    #stop all running containers
    if [ -n "$running_containers" ]; then
        docker stop $running_containers
    fi
}

clear_all_nodes() {
    #get list of all running containers
    running_containers=$(docker ps -q)
    images=$(docker images -q)
    networks=$(docker network ls -q)
    volumes=$(docker volume ls -q)

    #stop all running containers
    for container in $running_containers; do
        docker stop $container
    done

    #remove all images
    for image in $images; do
        docker rmi $image
    done

    #remove all networks
    for network in $networks; do
        docker network rm $network
    done

    #remove all volumes
    for volume in $volumes; do
        docker volume rm $volume
    done

    rm -rf docker-compose*
}




# Main loop
while true; do
    show_menu
    case $choice in
        1)
            install_nodes
            ;;
        2)
            check_log_compose
            ;;
        3)
            stop_all_nodes
            ;;
        4)
            start_nodes
            ;;
        5)
            clear_all_nodes
            ;;
        0)
            echo -e "Exiting..."
            exit 0
            ;;
        *)
            echo -e "Invalid choice. Please try again."
            ;;
    esac
done


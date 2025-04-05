# Fiware descomplicado

**Acesse o repositório original**

https://github.com/fabiocabrini/fiware.git

## Objetivo

Esse repositório tem como objetivo ser instalado na máquina virtual ``ubuntu linux`` para a criação de uma data base para manipular entidades via ``orion``.

## Instalando as dependências 

Siga o passo a passo para **configurar** a **maquina virtual** com **Linux Ubuntu** para executar o **Docker Compose** e iniciar os contêineres do **FIWARE**.

**1. Acesse a sua máquina virtual pelo terminal usando ``ssh``:**
```bash
ssh [usuário]@[ip da máquina virtual]
```

**2. Atualizar o Sistema e Instalar Dependências:**
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release -y
```
  - O primeiro comando atualiza a lista de pacotes disponíveis.
  - O segundo comando atualiza os pacotes instalados para as versões mais recentes.
  - O terceiro comando instala pacotes necessários para adicionar o repositório do Docker.

**3. Adicionar o Repositório do Docker:** 
```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```
  - Este comando adiciona o repositório oficial do Docker à sua lista de fontes de pacotes.

**4. Instalar o Docker Engine e Docker Compose:**
```bash
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
```
  - O primeiro comando atualiza a lista de pacotes novamente.
  - O segundo comando instala o Docker Engine, a CLI do Docker e o plugin Docker Compose.

**5. Clonar o Repositório que tem o FIWARE:**
```bash
git clone https://github.com/[repositório do git hub com o projeto]
cd [Acesse o repositório]
```

 **6. Iniciar os Contêineres Docker Compose:**
```bash
sudo docker compose up -d
```
  - Este comando inicia os contêineres definidos no arquivo ``docker-compose.yml``.
  - A flag ``-d`` executa os contêineres em segundo plano (detached mode).

**7.Verificar os Contêineres:**
```bash
docker ps
```
  - Este comando lista os contêineres em execução, permitindo que você verifique se todos os serviços foram iniciados corretamente.












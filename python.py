import oracledb
import json
import requests

def connect_db():
    try:
        dsn = "oracle.fiap.com.br:1521/orcl"

        conn = oracledb.connect(
            user='rm557334',
            password='010703',
            dsn=dsn
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def validar_cpf(cpf):
    return len(cpf) == 11 and cpf.isdigit()

def validar_placa(placa):
    return len(placa) >= 7 and len(placa) <= 8 and placa.isalnum()

def validar_nome(nome):
    return nome.replace(" ", "").isalpha()

def validar_entrada_numero(numero):
    try:
        return int(numero)
    except ValueError:
        print("Entrada inválida. Deve ser um número.")
        return None

def adicionar_cliente(conn):
    try:
        nome = input("Nome do Cliente: ").strip()
        if not validar_nome(nome):
            raise ValueError("Nome inválido. Deve conter apenas letras.")
        
        endereco = input("Endereço do Cliente: ").strip()
        telefone = input("Telefone do Cliente: ").strip()
        email = input("Email do Cliente: ").strip()
        senha = input("Senha do Cliente: ").strip()
        cpf = input("CPF do Cliente: ").strip()
        if not validar_cpf(cpf):
            raise ValueError("CPF inválido. Deve conter 11 dígitos numéricos.")
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO T_CHALLENGE_CLIENTES (Nome, Endereco, Telefone, Email, Senha, Cpf)
            VALUES (:nome, :endereco, :telefone, :email, :senha, :cpf)
        """, [nome, endereco, telefone, email, senha, cpf])
        conn.commit()
        print("Cliente adicionado com sucesso!")
    
    except oracledb.IntegrityError as e:
        error_obj, = e.args
        if error_obj.code == 1:
            print("Erro: Cliente com este CPF, Email ou Telefone já cadastrado.")
        else:
            print(f"Erro de integridade: {e}")
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def listar_clientes(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT ClienteID, Nome, Cpf FROM T_CHALLENGE_CLIENTES")
    clientes = cursor.fetchall()
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return []
    for idx, cliente in enumerate(clientes, 1):
        print(f"{idx} - ID: {cliente[0]}, Nome: {cliente[1]}, CPF: {cliente[2]}")
    return clientes

def alterar_cliente(conn):
    clientes = listar_clientes(conn)
    if not clientes:
        return
    idx = validar_entrada_numero(input("Escolha o cliente pelo número: "))
    if idx and 1 <= idx <= len(clientes):
        try:
            nome = input("Novo nome: ").strip()
            if not validar_nome(nome):
                raise ValueError("Nome inválido. Deve conter apenas letras.")
            cliente_id = clientes[idx - 1][0]
            cursor = conn.cursor()
            cursor.execute("UPDATE T_CHALLENGE_CLIENTES SET Nome = :nome WHERE ClienteID = :id", [nome, cliente_id])
            conn.commit()
            print("Cliente atualizado com sucesso.")
        except ValueError as ve:
            print(ve)
    else:
        print("Cliente inválido.")

def excluir_cliente(conn):
    clientes = listar_clientes(conn)
    if not clientes:
        return
    idx = validar_entrada_numero(input("Escolha o cliente pelo número para excluir: "))
    if idx and 1 <= idx <= len(clientes):
        try:
            cliente_id = clientes[idx - 1][0]
            cursor = conn.cursor()
            cursor.execute("DELETE FROM T_CHALLENGE_CLIENTES WHERE ClienteID = :id", [cliente_id])
            conn.commit()
            print("Cliente excluído com sucesso.")
        except oracledb.IntegrityError as e:
            print("Erro ao excluir: O cliente possui veículos cadastrados.")
        except Exception as e:
            print(f"Erro ao excluir: {e}")
    else:
        print("Cliente inválido.")

def adicionar_veiculo(conn):
    try:
        clientes = listar_clientes(conn)
        if not clientes:
            return
        cliente_idx = validar_entrada_numero(input("Escolha o cliente para o veículo: "))
        if cliente_idx and 1 <= cliente_idx <= len(clientes):
            cliente_id = clientes[cliente_idx - 1][0]
            marca = input("Marca do Veículo: ").strip()
            modelo = input("Modelo do Veículo: ").strip()
            ano = validar_entrada_numero(input("Ano do Veículo: "))
            if not ano or ano < 1886:
                raise ValueError("Ano inválido. Deve ser um número maior ou igual a 1886.")
            placa = input("Placa do Veículo: ").strip().upper()
            if not validar_placa(placa):
                raise ValueError("Placa inválida. Deve ter entre 7 e 8 caracteres alfanuméricos.")
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO T_CHALLENGE_VEICULOS (ClienteID, Marca, Modelo, Ano, Placa)
                VALUES (:cliente_id, :marca, :modelo, :ano, :placa)
            """, [cliente_id, marca, modelo, ano, placa])
            conn.commit()
            print("Veículo adicionado com sucesso.")
        else:
            print("Cliente inválido.")
    
    except oracledb.IntegrityError as e:
        error_obj, = e.args
        if error_obj.code == 1:
            print("Erro: Veículo com esta placa já cadastrado.")
        else:
            print(f"Erro de integridade: {e}")
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

def listar_veiculos(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.VeiculoID, v.Placa, v.Modelo, c.Nome
        FROM T_CHALLENGE_VEICULOS v
        JOIN T_CHALLENGE_CLIENTES c ON v.ClienteID = c.ClienteID
    """)
    veiculos = cursor.fetchall()
    if not veiculos:
        print("Nenhum veículo cadastrado.")
        return []
    for idx, veiculo in enumerate(veiculos, 1):
        print(f"{idx} - ID: {veiculo[0]}, Placa: {veiculo[1]}, Modelo: {veiculo[2]}, Cliente: {veiculo[3]}")
    return veiculos

def alterar_veiculo(conn):
    veiculos = listar_veiculos(conn)
    if not veiculos:
        return
    idx = validar_entrada_numero(input("Escolha o veículo pelo número: "))
    if idx and 1 <= idx <= len(veiculos):
        try:
            novo_modelo = input("Novo modelo: ").strip()
            veiculo_id = veiculos[idx - 1][0]
            cursor = conn.cursor()
            cursor.execute("UPDATE T_CHALLENGE_VEICULOS SET Modelo = :modelo WHERE VeiculoID = :id", [novo_modelo, veiculo_id])
            conn.commit()
            print("Veículo atualizado com sucesso.")
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
    else:
        print("Veículo inválido.")

def excluir_veiculo(conn):
    veiculos = listar_veiculos(conn)
    if not veiculos:
        return
    idx = validar_entrada_numero(input("Escolha o veículo pelo número para excluir: "))
    if idx and 1 <= idx <= len(veiculos):
        try:
            veiculo_id = veiculos[idx - 1][0]
            cursor = conn.cursor()
            cursor.execute("DELETE FROM T_CHALLENGE_VEICULOS WHERE VeiculoID = :id", [veiculo_id])
            conn.commit()
            print("Veículo excluído com sucesso.")
        except Exception as e:
            print(f"Erro ao excluir: {e}")
    else:
        print("Veículo inválido.")

def exportar_clientes_para_json(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM T_CHALLENGE_CLIENTES")
    colunas = [col[0] for col in cursor.description]
    clientes = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    if not clientes:
        print("Nenhum cliente cadastrado.")
        return
    with open('clientes.json', 'w', encoding='utf-8') as f:
        json.dump(clientes, f, ensure_ascii=False, indent=4)
    print("Dados exportados para clientes.json com sucesso.")

def exportar_veiculos_para_json(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.*, c.Nome as ClienteNome
        FROM T_CHALLENGE_VEICULOS v
        JOIN T_CHALLENGE_CLIENTES c ON v.ClienteID = c.ClienteID
    """)
    colunas = [col[0] for col in cursor.description]
    veiculos = [dict(zip(colunas, row)) for row in cursor.fetchall()]
    if not veiculos:
        print("Nenhum veículo cadastrado.")
        return
    with open('veiculos.json', 'w', encoding='utf-8') as f:
        json.dump(veiculos, f, ensure_ascii=False, indent=4)
    print("Dados exportados para veiculos.json com sucesso.")

def importar_cliente_api_externa(conn):
    try:
        response = requests.get('http://localhost:8080/techguard/cliente')
        if response.status_code == 200:
            data = response.json()

            # Verificar se `data` é uma lista e percorrer cada cliente
            if isinstance(data, list) and data:
                for user in data:
                    # Extração de dados do usuário com tratamento para campos ausentes
                    nome = user.get('nome', 'Nome Desconhecido')
                    endereco = 'Endereço não fornecido'  # Endereço não presente nos dados da API
                    telefone = user.get('telefone', 'Telefone não fornecido')
                    email = user.get('email', 'Email não fornecido')
                    senha = user.get('senha', 'Senha não fornecida')

                    # Tratamento de CPF, garantindo que apenas números sejam usados
                    cpf = ''.join(filter(str.isdigit, user.get('cpf', '')))[:11]
                    if not cpf or len(cpf) < 11:
                        cpf = cpf.ljust(11, '0')  # Completa com zeros se necessário
                    
                    # Inserção no banco de dados
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO T_CHALLENGE_CLIENTES (Nome, Endereco, Telefone, Email, Senha, Cpf)
                        VALUES (:nome, :endereco, :telefone, :email, :senha, :cpf)
                    """, [nome, endereco, telefone, email, senha, cpf])
                    conn.commit()
                    print(f"Cliente importado: Nome: {nome}, CPF: {cpf}")
            else:
                print("Erro: Dados inesperados, a API não retornou uma lista de clientes.")
        else:
            print("Falha ao obter dados da API externa.")
    except oracledb.IntegrityError as e:
        print("Erro ao inserir cliente importado: Possível duplicação de CPF, Email ou Telefone.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")


def menu_clientes(conn):
    while True:
        print("\n--- Menu Clientes ---")
        print("1 - Adicionar Cliente")
        print("2 - Listar Clientes")
        print("3 - Alterar Cliente")
        print("4 - Excluir Cliente")
        print("5 - Exportar Clientes para JSON")
        print("6 - Importar Cliente da API Externa")
        print("0 - Voltar")
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            adicionar_cliente(conn)
        elif opcao == '2':
            listar_clientes(conn)
        elif opcao == '3':
            alterar_cliente(conn)
        elif opcao == '4':
            excluir_cliente(conn)
        elif opcao == '5':
            exportar_clientes_para_json(conn)
        elif opcao == '6':
            importar_cliente_api_externa(conn)
        elif opcao == '0':
            break
        else:
            print("Opção inválida. Tente novamente.")

def menu_veiculos(conn):
    while True:
        print("\n--- Menu Veículos ---")
        print("1 - Adicionar Veículo")
        print("2 - Listar Veículos")
        print("3 - Alterar Veículo")
        print("4 - Excluir Veículo")
        print("5 - Exportar Veículos para JSON")
        print("0 - Voltar")
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            adicionar_veiculo(conn)
        elif opcao == '2':
            listar_veiculos(conn)
        elif opcao == '3':
            alterar_veiculo(conn)
        elif opcao == '4':
            excluir_veiculo(conn)
        elif opcao == '5':
            exportar_veiculos_para_json(conn)
        elif opcao == '0':
            break
        else:
            print("Opção inválida. Tente novamente.")

def main_menu(conn):
    while True:
        print("\n--- Menu Principal ---")
        print("1 - Gerenciar Clientes")
        print("2 - Gerenciar Veículos")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            menu_clientes(conn)
        elif opcao == '2':
            menu_veiculos(conn)
        elif opcao == '0':
            print("Saindo do sistema.")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    conn = connect_db()
    if conn:
        main_menu(conn)
        conn.close()

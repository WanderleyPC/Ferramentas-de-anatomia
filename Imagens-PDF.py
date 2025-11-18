#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Este programa converte **imagens salvas em uma pasta** para o formato PDF, permitindo ao usuário gerar:
1. Um **único PDF contendo todas as imagens**, com uma imagem por página.
2. **PDFs individuais**, um para cada imagem.

O programa possui uma interface no terminal que orienta o usuário passo a passo, desde a escolha da pasta com imagens até a geração dos arquivos PDF.

FUNCIONALIDADES:

1. **Verificação e Instalação de Dependências**:
   - Verifica se as bibliotecas `Pillow` e `reportlab` estão instaladas.
   - Caso não estejam, oferece a opção de instalá-las automaticamente.

2. **Validação de Caminho**:
   - O usuário informa o caminho da pasta com imagens.
   - O programa valida se o caminho é válido, se é uma pasta e se contém imagens suportadas.

3. **Suporte a Diversos Formatos de Imagem**:
   - São aceitos arquivos com extensões `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`, `.tiff` (maiúsculas e minúsculas).

4. **Verificação de Imagens Válidas**:
   - O programa tenta abrir todas as imagens encontradas para garantir que estão íntegras.
   - Exibe quais imagens são válidas para o processo.

5. **Modos de Conversão**:
   - **PDF Único**:
     - Todas as imagens são redimensionadas proporcionalmente e centralizadas em páginas A4.
     - Um único arquivo PDF é gerado com todas as imagens organizadas sequencialmente.
   - **PDFs Individuais**:
     - Cada imagem é convertida em um arquivo PDF separado.
     - Os arquivos são salvos em uma pasta indicada pelo usuário (ou sugerida pelo programa).

6. **Interface Limpa e Didática**:
   - Limpeza da tela.
   - Exibição clara do progresso.
   - Tratamento de erros.
   - Mensagens amigáveis e explicativas.

REQUISITOS:
- Python 3
- Bibliotecas: `Pillow`, `reportlab`
  - Podem ser instaladas automaticamente pelo programa, se necessário.

USO IDEAL:
- Estudantes ou professores que precisam compilar imagens escaneadas ou capturas de tela em PDFs.
- Impressão de material visual organizado.
- Transformar coleções de imagens (ex: slides, anotações, quadros) em arquivos prontos para compartilhamento ou arquivamento.

"""


import os
import sys
import glob
from typing import List, Tuple
import subprocess
import platform

# Função para verificar e instalar dependências
def verificar_instalar_dependencias() -> bool:
    """
    Verifica se as bibliotecas necessárias estão instaladas.
    Caso não estejam, orienta o usuário a instalá-las.
    
    Returns:
        bool: True se todas as dependências estão instaladas, False caso contrário
    """
    try:
        import PIL
        from PIL import Image
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter, A4
            return True
        except ImportError:
            print("\nA biblioteca 'reportlab' não está instalada.")
            print("Esta biblioteca é necessária para criar arquivos PDF.")
            instalar = input("Deseja instalar agora? (s/n): ").lower()
            if instalar == 's':
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
                    print("ReportLab instalado com sucesso!")
                    return True
                except Exception as e:
                    print(f"Erro ao instalar ReportLab: {e}")
                    return False
            else:
                print("Você precisa instalar a biblioteca 'reportlab' para usar este programa.")
                print("Execute: pip install reportlab")
                return False
    except ImportError:
        print("\nA biblioteca 'Pillow' não está instalada.")
        print("Esta biblioteca é necessária para processar imagens.")
        instalar = input("Deseja instalar agora? (s/n): ").lower()
        if instalar == 's':
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
                print("Pillow instalado com sucesso!")
                # Verifica a reportlab também
                return verificar_instalar_dependencias()
            except Exception as e:
                print(f"Erro ao instalar Pillow: {e}")
                return False
        else:
            print("Você precisa instalar a biblioteca 'Pillow' para usar este programa.")
            print("Execute: pip install Pillow")
            return False


def limpar_tela():
    """Limpa a tela do terminal/prompt de comando."""
    os.system('cls' if platform.system() == 'Windows' else 'clear')


def validar_caminho(caminho: str) -> bool:
    """
    Verifica se o caminho fornecido existe e é uma pasta válida.
    
    Args:
        caminho (str): O caminho da pasta a ser verificada
        
    Returns:
        bool: True se o caminho é válido, False caso contrário
    """
    if not caminho:
        print("Erro: Nenhum caminho foi fornecido.")
        return False
    
    # Remove aspas se o usuário tiver incluído ao copiar o caminho
    caminho = caminho.strip('"\'')
    
    if not os.path.exists(caminho):
        print(f"Erro: O caminho '{caminho}' não existe.")
        return False
        
    if not os.path.isdir(caminho):
        print(f"Erro: '{caminho}' não é uma pasta.")
        return False
        
    return True


def encontrar_imagens(caminho: str) -> List[str]:
    """
    Encontra todas as imagens na pasta especificada.
    
    Args:
        caminho (str): O caminho da pasta onde procurar as imagens
        
    Returns:
        List[str]: Lista com os caminhos completos de todas as imagens encontradas
    """
    # Extensões de imagem suportadas (usando conjuntos para evitar duplicações)
    imagens = set()
    
    # Lista de todas as extensões a serem verificadas (em minúsculas)
    extensoes = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff']
    
    for ext in extensoes:
        # Encontra arquivos com a extensão em minúsculas
        padrão_busca = os.path.join(caminho, ext)
        imagens.update(glob.glob(padrão_busca))
        
        # Encontra arquivos com a extensão em maiúsculas
        padrão_busca = os.path.join(caminho, ext.upper())
        imagens.update(glob.glob(padrão_busca))
    
    # Converte o conjunto para lista e ordena pelo nome
    return sorted(list(imagens))


def verificar_imagens_validas(caminhos_imagens: List[str]) -> Tuple[List[str], List[str]]:
    """
    Verifica quais imagens são válidas e podem ser processadas.
    
    Args:
        caminhos_imagens (List[str]): Lista de caminhos de imagens para verificar
        
    Returns:
        Tuple[List[str], List[str]]: Tupla contendo uma lista de imagens válidas e outra de inválidas
    """
    from PIL import Image
    
    validas = []
    invalidas = []
    
    print("\nVerificando imagens...")
    total = len(caminhos_imagens)
    
    for i, caminho in enumerate(caminhos_imagens):
        print(f"Verificando imagem {i+1}/{total}: {os.path.basename(caminho)}", end='\r')
        try:
            with Image.open(caminho) as img:
                # Apenas verifica se a imagem pode ser aberta
                img.verify()
                validas.append(caminho)
        except Exception:
            invalidas.append(caminho)
    
    print(" " * 80, end='\r')  # Limpa a linha
    
    return validas, invalidas


def criar_pdf_unico(imagens: List[str], nome_saida: str) -> bool:
    """
    Cria um único arquivo PDF contendo todas as imagens.
    
    Args:
        imagens (List[str]): Lista de caminhos das imagens a serem incluídas
        nome_saida (str): Nome do arquivo PDF de saída
        
    Returns:
        bool: True se o PDF foi criado com sucesso, False caso contrário
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from PIL import Image
    
    # Adiciona a extensão .pdf se não estiver presente
    if not nome_saida.lower().endswith('.pdf'):
        nome_saida += '.pdf'
    
    try:
        c = canvas.Canvas(nome_saida, pagesize=A4)
        largura_pagina, altura_pagina = A4
        
        print(f"\nCriando PDF único com {len(imagens)} imagens...")
        
        for i, img_path in enumerate(imagens):
            print(f"Processando imagem {i+1}/{len(imagens)}: {os.path.basename(img_path)}", end='\r')
            
            try:
                img = Image.open(img_path)
                
                # Calcula as dimensões para ajustar a imagem na página
                largura_img, altura_img = img.size
                ratio = min(largura_pagina / largura_img, altura_pagina / altura_img) * 0.9
                largura_final = largura_img * ratio
                altura_final = altura_img * ratio
                
                # Centraliza a imagem na página
                x_pos = (largura_pagina - largura_final) / 2
                y_pos = (altura_pagina - altura_final) / 2
                
                # Desenha a imagem
                c.drawImage(img_path, x_pos, y_pos, width=largura_final, height=altura_final)
                
                # Adiciona uma nova página para a próxima imagem (exceto para a última)
                if i < len(imagens) - 1:
                    c.showPage()
                
            except Exception as e:
                print(f"\nErro ao processar a imagem {os.path.basename(img_path)}: {e}")
        
        c.save()
        print(" " * 80, end='\r')  # Limpa a linha
        print(f"\nPDF criado com sucesso: {nome_saida}")
        return True
        
    except Exception as e:
        print(f"\nErro ao criar o PDF: {e}")
        return False


def criar_pdfs_individuais(imagens: List[str], pasta_saida: str) -> bool:
    """
    Cria PDFs individuais para cada imagem.
    
    Args:
        imagens (List[str]): Lista de caminhos das imagens
        pasta_saida (str): Pasta onde os PDFs serão salvos
        
    Returns:
        bool: True se todos os PDFs foram criados com sucesso, False caso contrário
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from PIL import Image
    
    # Cria a pasta de saída se não existir
    if not os.path.exists(pasta_saida):
        try:
            os.makedirs(pasta_saida)
        except Exception as e:
            print(f"Erro ao criar a pasta de saída: {e}")
            return False
    
    sucessos = 0
    falhas = 0
    
    print(f"\nCriando PDFs individuais para {len(imagens)} imagens...")
    
    for i, img_path in enumerate(imagens):
        nome_arquivo = os.path.splitext(os.path.basename(img_path))[0] + ".pdf"
        caminho_saida = os.path.join(pasta_saida, nome_arquivo)
        
        print(f"Processando imagem {i+1}/{len(imagens)}: {os.path.basename(img_path)}", end='\r')
        
        try:
            img = Image.open(img_path)
            
            c = canvas.Canvas(caminho_saida, pagesize=A4)
            largura_pagina, altura_pagina = A4
            
            # Calcula as dimensões para ajustar a imagem na página
            largura_img, altura_img = img.size
            ratio = min(largura_pagina / largura_img, altura_pagina / altura_img) * 0.9
            largura_final = largura_img * ratio
            altura_final = altura_img * ratio
            
            # Centraliza a imagem na página
            x_pos = (largura_pagina - largura_final) / 2
            y_pos = (altura_pagina - altura_final) / 2
            
            # Desenha a imagem
            c.drawImage(img_path, x_pos, y_pos, width=largura_final, height=altura_final)
            c.save()
            
            sucessos += 1
            
        except Exception as e:
            print(f"\nErro ao criar PDF para {os.path.basename(img_path)}: {e}")
            falhas += 1
    
    print(" " * 80, end='\r')  # Limpa a linha
    
    if falhas == 0:
        print(f"\nTodos os {sucessos} PDFs foram criados com sucesso na pasta: {pasta_saida}")
        return True
    else:
        print(f"\n{sucessos} PDFs foram criados com sucesso e {falhas} falharam.")
        print(f"Os PDFs estão na pasta: {pasta_saida}")
        return False


def menu_principal():
    """Função principal que gerencia o fluxo do programa."""
    limpar_tela()
    print("=" * 60)
    print("             CONVERSOR DE IMAGENS PARA PDF")
    print("=" * 60)
    
    # Verifica se as dependências estão instaladas
    if not verificar_instalar_dependencias():
        input("\nPressione ENTER para sair...")
        return
    
    # Solicita o caminho da pasta com as imagens
    while True:
        print("\nDigite o caminho completo da pasta contendo as imagens")
        print("(Exemplo: C:\\Fotos ou /home/usuario/fotos)")
        caminho = input("\nCaminho: ").strip()
        
        if validar_caminho(caminho):
            break
        else:
            continuar = input("\nDeseja tentar novamente? (s/n): ").lower()
            if continuar != 's':
                return
    
    # Encontra as imagens na pasta
    print(f"\nProcurando imagens em: {caminho}")
    imagens = encontrar_imagens(caminho)
    
    if not imagens:
        print("\nNenhuma imagem foi encontrada na pasta especificada.")
        input("\nPressione ENTER para sair...")
        return
    
    # Verifica quais imagens são válidas
    imagens_validas, imagens_invalidas = verificar_imagens_validas(imagens)
    
    if imagens_invalidas:
        print(f"\nAtenção: {len(imagens_invalidas)} imagens não puderam ser processadas:")
        for img in imagens_invalidas[:5]:  # Mostra apenas as 5 primeiras para não sobrecarregar
            print(f" - {os.path.basename(img)}")
        if len(imagens_invalidas) > 5:
            print(f" - ... e mais {len(imagens_invalidas) - 5} arquivo(s)")
    
    total_validas = len(imagens_validas)
    if total_validas == 0:
        print("\nNão há imagens válidas para processar.")
        input("\nPressione ENTER para sair...")
        return
    
    print(f"\nForam encontradas {total_validas} imagens válidas:")
    for i, img in enumerate(imagens_validas[:5]):  # Mostra apenas as 5 primeiras
        print(f" - {os.path.basename(img)}")
    if total_validas > 5:
        print(f" - ... e mais {total_validas - 5} arquivo(s)")
    
    # Menu de opções
    print("\nO que você deseja fazer?")
    print("1 - Criar um único PDF contendo todas as imagens")
    print("2 - Criar PDFs individuais para cada imagem")
    print("0 - Sair")
    
    while True:
        try:
            opcao = int(input("\nOpção escolhida: "))
            if opcao in [0, 1, 2]:
                break
            else:
                print("Opção inválida. Por favor, digite 0, 1 ou 2.")
        except ValueError:
            print("Por favor, digite um número válido.")
    
    if opcao == 0:
        print("\nPrograma encerrado pelo usuário.")
        return
    
    # Processar opção escolhida
    if opcao == 1:
        # Criar um único PDF
        print("\nVocê escolheu criar um único PDF com todas as imagens.")
        nome_arquivo = input("Digite o nome do arquivo PDF de saída (sem a extensão): ").strip()
        
        if not nome_arquivo:
            nome_arquivo = "imagens_unificadas"
        
        # Se o usuário não forneceu um caminho completo, salva na mesma pasta das imagens
        if not os.path.dirname(nome_arquivo):
            nome_arquivo = os.path.join(caminho, nome_arquivo)
            
        criar_pdf_unico(imagens_validas, nome_arquivo)
    
    elif opcao == 2:
        # Criar PDFs individuais
        print("\nVocê escolheu criar PDFs individuais para cada imagem.")
        
        # Sugere uma pasta de saída
        pasta_sugerida = os.path.join(caminho, "PDFs_Individuais")
        
        print(f"Pasta de saída sugerida: {pasta_sugerida}")
        usar_sugerida = input("Deseja usar esta pasta? (s/n): ").lower()
        
        if usar_sugerida == 's':
            pasta_saida = pasta_sugerida
        else:
            pasta_saida = input("Digite o caminho completo da pasta de saída: ").strip()
            if not pasta_saida:
                pasta_saida = pasta_sugerida
        
        criar_pdfs_individuais(imagens_validas, pasta_saida)
    
    input("\nPressione ENTER para sair...")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido pelo usuário.")
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
        input("\nPressione ENTER para sair...")
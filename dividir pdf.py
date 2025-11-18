import os
import sys
from PyPDF2 import PdfReader, PdfWriter

"""
Este programa interativo permite **extrair páginas específicas de um arquivo PDF** com base em intervalos definidos pelo usuário. Ele oferece a opção de salvar os trechos extraídos como arquivos separados ou combiná-los em um único PDF.

FUNCIONALIDADES:

1. **Entrada do Caminho do Arquivo PDF**:
   O usuário é solicitado a fornecer o caminho completo do arquivo PDF. O programa valida se o caminho é válido e se o arquivo é realmente um PDF.

2. **Definição de Intervalos de Páginas**:
   O usuário informa intervalos no formato `início-fim` (ex: `3-7`). É possível inserir vários intervalos consecutivamente, que serão processados um por um.

3. **Combinar ou Separar**:
   O usuário pode escolher entre:
   - **Criar um único PDF contendo todos os intervalos combinados**.
   - **Criar arquivos separados para cada intervalo especificado**.

4. **Validações**:
   - O programa verifica se os números de páginas fornecidos estão dentro do total de páginas do PDF.
   - Erros de digitação, arquivos inválidos ou caminhos incorretos são tratados com mensagens explicativas.

5. **Saída Automatizada**:
   - Os arquivos gerados são salvos no mesmo diretório do arquivo original.
   - A nomenclatura dos arquivos segue o padrão:
     - `"3-7-arquivooriginal.pdf"` para arquivos separados.
     - `"combinado-arquivooriginal.pdf"` para arquivos unidos.

6. **Tratamento de Erros**:
   Todo o processo está protegido contra exceções comuns (como `KeyboardInterrupt` ou falhas na leitura do PDF), garantindo uma experiência estável.

REQUISITOS:
- Python 3
- Biblioteca `PyPDF2` instalada (`pip install PyPDF2`)

USO IDEAL:
- Para estudantes e profissionais que precisam dividir livros ou apostilas em capítulos.
- Separar questões, textos ou seções específicas de provas ou materiais PDF.
- Unir partes selecionadas de um PDF em um novo documento personalizado.

"""


def obter_caminho_pdf():
    """Solicita e valida o caminho do arquivo PDF."""
    while True:
        caminho = input("Digite o caminho completo para o arquivo PDF: ").strip()
        
        # Verifica se o arquivo existe
        if not os.path.isfile(caminho):
            print("Erro: O arquivo não foi encontrado. Verifique o caminho e tente novamente.")
            continue
            
        # Verifica se é um arquivo PDF
        if not caminho.lower().endswith('.pdf'):
            print("Erro: O arquivo não parece ser um PDF. Por favor, forneça um arquivo PDF válido.")
            continue
            
        return caminho

def obter_intervalo_paginas(total_paginas):
    """Solicita e valida um intervalo de páginas."""
    while True:
        try:
            intervalo = input(f"Digite o intervalo de páginas (ex: 1-10) [total: {total_paginas} páginas]: ").strip()
            
            # Verifica o formato do intervalo
            if '-' not in intervalo:
                print("Erro: Formato inválido. Use o formato 'início-fim' (ex: 1-10).")
                continue
                
            inicio, fim = map(int, intervalo.split('-'))
            
            # Verifica se o intervalo está dentro dos limites
            if inicio < 1 or fim > total_paginas or inicio > fim:
                print(f"Erro: Intervalo inválido. O arquivo tem {total_paginas} páginas.")
                continue
                
            return inicio, fim
            
        except ValueError:
            print("Erro: Por favor, insira números válidos para o intervalo.")

def extrair_paginas_pdf(caminho_entrada, intervalos, combinar=False):
    """Extrai páginas do PDF conforme os intervalos especificados."""
    try:
        # Obtém o diretório e nome do arquivo original
        diretorio = os.path.dirname(caminho_entrada)
        nome_arquivo = os.path.basename(caminho_entrada)
        
        pdf_reader = PdfReader(caminho_entrada)
        total_paginas = len(pdf_reader.pages)
        
        if combinar:
            # Cria um único PDF com todos os intervalos
            pdf_writer = PdfWriter()
            
            for inicio, fim in intervalos:
                for i in range(inicio-1, fim):
                    pdf_writer.add_page(pdf_reader.pages[i])
            
            # Nome do arquivo combinado
            nome_saida = os.path.join(diretorio, f"combinado-{nome_arquivo}")
            
            # Salva o arquivo combinado
            with open(nome_saida, 'wb') as arquivo_saida:
                pdf_writer.write(arquivo_saida)
                
            print(f"Arquivo combinado criado com sucesso: {nome_saida}")
            
        else:
            # Cria um PDF separado para cada intervalo
            for inicio, fim in intervalos:
                pdf_writer = PdfWriter()
                
                for i in range(inicio-1, fim):
                    pdf_writer.add_page(pdf_reader.pages[i])
                
                # Nome do arquivo para este intervalo
                nome_saida = os.path.join(diretorio, f"{inicio}-{fim}-{nome_arquivo}")
                
                # Salva o arquivo deste intervalo
                with open(nome_saida, 'wb') as arquivo_saida:
                    pdf_writer.write(arquivo_saida)
                    
                print(f"Arquivo criado com sucesso: {nome_saida}")
                
        return True
        
    except Exception as e:
        print(f"Erro ao processar o PDF: {str(e)}")
        return False

def main():
    print("=== EXTRATOR DE INTERVALOS DE PDF ===")
    
    # Obtém o caminho do PDF
    caminho_pdf = obter_caminho_pdf()
    
    try:
        # Verifica se o arquivo pode ser aberto como PDF
        pdf = PdfReader(caminho_pdf)
        total_paginas = len(pdf.pages)
        print(f"PDF carregado com sucesso. Total de páginas: {total_paginas}")
        
        # Coleta os intervalos de páginas
        intervalos = []
        
        while True:
            inicio, fim = obter_intervalo_paginas(total_paginas)
            intervalos.append((inicio, fim))
            
            # Pergunta se deseja adicionar mais um intervalo
            continuar = input("Deseja adicionar mais um intervalo? (S/N): ").strip().upper()
            if continuar != 'S':
                break
        
        # Pergunta se deseja combinar os intervalos em um único PDF
        combinar = input("Deseja juntar todos os intervalos em um único PDF? (S/N): ").strip().upper() == 'S'
        
        # Extrai as páginas conforme solicitado
        if extrair_paginas_pdf(caminho_pdf, intervalos, combinar):
            print("Processamento concluído com sucesso!")
        else:
            print("Ocorreu um problema ao processar o PDF.")
            
    except Exception as e:
        print(f"Erro ao abrir o arquivo PDF: {str(e)}")
        print("Verifique se o arquivo é um PDF válido e tente novamente.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
    
    input("\nPressione Enter para sair...")
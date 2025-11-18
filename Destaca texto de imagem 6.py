import os
import sys
from pathlib import Path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image, ImageDraw, ImageFont
import argparse
from tqdm import tqdm
import logging
import re
from colorama import init, Fore
init()  # Inicializar colorama para cores no console

"""
Este programa permite detectar, destacar, apagar e numerar palavras ou frases específicas em imagens utilizando OCR com o Tesseract. 

É especialmente útil para criar **provas personalizadas**, **gabaritos comentados**, **atividades educativas**, ou para ocultar termos sensíveis em imagens de forma automática.

FUNCIONALIDADES:

1. **Entrada do Caminho da Pasta**:
   O usuário informa o caminho de uma pasta contendo imagens. O programa valida o caminho e verifica se há imagens compatíveis (JPG, PNG, BMP, TIFF).

2. **Palavras-Chave**:
   O usuário insere uma lista de palavras ou frases que deseja destacar nas imagens. A busca é feita ignorando maiúsculas/minúsculas.

3. **Modos de Processamento**:
   - **Normal**: Destaca as palavras com uma borda vermelha e pode (opcionalmente) apagar o conteúdo textual.
   - **Modo Duplo** ("Tudo"): Gera duas versões:
     - Uma com as palavras visíveis (gabarito).
     - Outra com as palavras apagadas (prova), podendo ter numeração sequencial para preenchimento.

4. **Numeração Sequencial**:
   Caso a opção esteja ativada, substitui as palavras ocultadas por números centralizados, úteis para gabaritos ou atividades com lacunas.

5. **Remoção de Imagens Irrelevantes**:
   Se desejado, o programa pode **excluir automaticamente imagens que não contenham nenhuma palavra-chave**, evitando arquivos inúteis.

6. **OCR com pytesseract**:
   O programa utiliza `pytesseract` para identificar texto nas imagens, bloco por bloco, com filtragem por nível de confiança para evitar erros.

7. **Saída Organizada**:
   As imagens processadas são salvas em novas pastas:
   - Ex: "Destacado-NomeDaPasta", "Gabarito-NomeDaPasta", "Prova-NomeDaPasta".

8. **Registro com Logging**:
   Todas as etapas do processo são registradas em tempo real no console e em um arquivo `processamento_imagens.log`, incluindo erros, progresso e relatório final.

REQUISITOS:
- Python 3.
- Bibliotecas: `pytesseract`, `Pillow`, `tqdm`, `colorama`.
- Tesseract OCR instalado (com caminho configurado corretamente no código).

USO IDEAL:
- Professores que desejam gerar provas com lacunas ou destacar termos.
- Estudantes que querem revisar conteúdos visuais.
- Aplicações que exigem anonimização ou ocultação de texto em imagens.

"""




# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("processamento_imagens.log")
    ]
)
logger = logging.getLogger(__name__)

def validar_caminho(caminho):
    """Valida se o caminho existe e contém imagens."""
    # Verificar se o caminho existe
    if not os.path.exists(caminho):
        return False, "O caminho não existe."
    
    # Verificar se é uma pasta
    if not os.path.isdir(caminho):
        return False, "O caminho especificado não é uma pasta."
    
    # Verificar se contém imagens
    extensoes = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    imagens = []
    
    for ext in extensoes:
        imagens.extend(list(Path(caminho).glob(f"*{ext}")))
        imagens.extend(list(Path(caminho).glob(f"*{ext.upper()}")))
    
    if not imagens:
        return False, "A pasta não contém imagens suportadas (JPG, PNG, BMP, TIFF)."
    
    return True, f"Pasta válida. Encontradas {len(imagens)} imagens."

def criar_pasta_destino(caminho_original, prefixo="Destacado"):
    """Cria a pasta de destino baseada no nome da pasta original."""
    pasta_original = Path(caminho_original)
    nome_pasta_destino = f"{prefixo}-{pasta_original.name}"
    caminho_destino = pasta_original.parent / nome_pasta_destino
    
    if not caminho_destino.exists():
        caminho_destino.mkdir()
        logger.info(f"Pasta de destino criada: {caminho_destino}")
    else:
        logger.info(f"Pasta de destino já existe: {caminho_destino}")
    
    return caminho_destino

def listar_imagens(pasta):
    """Lista todas as imagens suportadas na pasta especificada."""
    extensoes = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    arquivos_imagem = []
    
    for ext in extensoes:
        arquivos_imagem.extend(list(Path(pasta).glob(f"*{ext}")))
        arquivos_imagem.extend(list(Path(pasta).glob(f"*{ext.upper()}")))
    
    return arquivos_imagem

def detectar_e_destacar_palavras(imagem_path, caminho_destino, palavras_chave, ocultar_palavras, numerar_palavras=False):
    """Detecta palavras ou frases específicas na imagem e as destaca com retângulos coloridos.
    Opcionalmente oculta as palavras destacadas com uma tarja branca e adiciona numeração sequencial.
    Retorna True/False para sucesso, número de ocorrências e se alguma palavra foi encontrada"""
    try:
        # Abrir a imagem
        imagem = Image.open(imagem_path)
        
        # Se a imagem tem canal alfa (transparência) e não é RGB, converta para RGB
        if imagem.mode == 'RGBA':
            fundo = Image.new('RGB', imagem.size, (255, 255, 255))
            fundo.paste(imagem, mask=imagem.split()[3])
            imagem = fundo
        elif imagem.mode != 'RGB':
            imagem = imagem.convert('RGB')
        
        # Usar o pytesseract para extrair texto completo e blocos individuais
        texto_completo = pytesseract.image_to_string(imagem).lower()
        dados = pytesseract.image_to_data(imagem, output_type=pytesseract.Output.DICT)
        
        # Criar objeto para desenhar na imagem
        desenho = ImageDraw.Draw(imagem)
        
        # Tentar carregar uma fonte para numeração (se disponível)
        fonte = None
        try:
            # Tentar encontrar fontes do sistema (compatível com Windows)
            fonte = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            try:
                # Alternativa para outros sistemas
                fonte = ImageFont.load_default()
            except Exception:
                logger.warning("Não foi possível carregar uma fonte. A numeração pode não ser exibida corretamente.")
        
        # Converter palavras-chave para minúsculas para comparação sem diferenciar maiúsculas/minúsculas
        palavras_chave_lower = [palavra.lower() for palavra in palavras_chave]
        
        # Verificar se alguma palavra-chave está no texto completo
        palavras_encontradas = 0
        texto_encontrado = False
        for palavra in palavras_chave_lower:
            if palavra in texto_completo:
                texto_encontrado = True
                break
        
        # Se não encontrou nenhuma palavra-chave no texto completo, retorna sem processamento adicional
        if not texto_encontrado:
            logger.info(f"Nenhuma palavra-chave encontrada em: {imagem_path.name}")
            # Salvar a imagem original na pasta de destino
            nome_arquivo = imagem_path.name
            caminho_saida = caminho_destino / nome_arquivo
            imagem.save(caminho_saida, quality=95)
            return True, 0, False
        
        # Construir um texto contínuo a partir dos blocos detectados
        texto_reconstruido = ""
        coordenadas_palavras = []
        
        for i in range(len(dados['text'])):
            if dados['conf'][i] > 30 and dados['text'][i].strip():
                texto_reconstruido += dados['text'][i].strip() + " "
                coordenadas_palavras.append({
                    'texto': dados['text'][i].strip(),
                    'x': dados['left'][i],
                    'y': dados['top'][i],
                    'largura': dados['width'][i],
                    'altura': dados['height'][i]
                })
        
        # Lista para armazenar as coordenadas das palavras destacadas (para numeração)
        destaques = []
        
        # Destacar cada ocorrência das palavras ou frases-chave
        for palavra_chave in palavras_chave_lower:
            # Para frases com múltiplas palavras
            if ' ' in palavra_chave:
                # Tentar encontrar a sequência de palavras
                palavras_da_frase = palavra_chave.split()
                
                for i in range(len(coordenadas_palavras) - len(palavras_da_frase) + 1):
                    sequencia_encontrada = True
                    for j in range(len(palavras_da_frase)):
                        if i+j >= len(coordenadas_palavras):
                            sequencia_encontrada = False
                            break
                        
                        palavra_atual = coordenadas_palavras[i+j]['texto'].lower()
                        if palavras_da_frase[j] not in palavra_atual:
                            sequencia_encontrada = False
                            break
                    
                    if sequencia_encontrada:
                        # Calcular retângulo que abrange toda a frase
                        x_min = coordenadas_palavras[i]['x']
                        y_min = min(coordenadas_palavras[i+j]['y'] for j in range(len(palavras_da_frase)))
                        x_max = coordenadas_palavras[i+len(palavras_da_frase)-1]['x'] + coordenadas_palavras[i+len(palavras_da_frase)-1]['largura']
                        y_max = max(coordenadas_palavras[i+j]['y'] + coordenadas_palavras[i+j]['altura'] for j in range(len(palavras_da_frase)))
                        
                        # Se a opção de ocultar palavras estiver ativada, desenha um retângulo branco preenchido
                        if ocultar_palavras:
                            desenho.rectangle(
                                [x_min, y_min, x_max, y_max],
                                fill=(255, 255, 255)
                            )
                            
                            # Armazenar destaque para numeração posterior
                            if numerar_palavras:
                                destaques.append({
                                    'x': x_min + (x_max - x_min) // 2,  # Centralizar o número
                                    'y': y_min + (y_max - y_min) // 2,  # Centralizar o número
                                    'largura': x_max - x_min,
                                    'altura': y_max - y_min
                                })
                        
                        # Desenhar o retângulo de destaque
                        espessura = 2
                        desenho.rectangle(
                            [x_min-espessura, y_min-espessura, x_max+espessura, y_max+espessura],
                            outline=(255, 0, 0),
                            width=3
                        )
                        palavras_encontradas += 1
            else:
                # Para palavras individuais
                for coord in coordenadas_palavras:
                    if palavra_chave in coord['texto'].lower():
                        x = coord['x']
                        y = coord['y']
                        largura = coord['largura']
                        altura = coord['altura']
                        
                        # Se a opção de ocultar palavras estiver ativada, desenha um retângulo branco preenchido
                        if ocultar_palavras:
                            desenho.rectangle(
                                [x, y, x+largura, y+altura],
                                fill=(255, 255, 255)
                            )
                            
                            # Armazenar destaque para numeração posterior
                            if numerar_palavras:
                                destaques.append({
                                    'x': x + largura // 2,  # Centralizar o número
                                    'y': y + altura // 2,  # Centralizar o número
                                    'largura': largura,
                                    'altura': altura
                                })
                        
                        # Desenhar retângulo colorido
                        espessura = 2
                        desenho.rectangle(
                            [x-espessura, y-espessura, x+largura+espessura, y+altura+espessura],
                            outline=(255, 0, 0),
                            width=3
                        )
                        palavras_encontradas += 1
        
        # Adicionar numeração sequencial às palavras ocultadas, se solicitado
        if numerar_palavras and destaques:
            for i, destaque in enumerate(destaques, 1):
                numero_str = str(i)
                
                # Ajustar o tamanho da fonte conforme o tamanho do retângulo, se uma fonte foi carregada
                tamanho_fonte = min(destaque['largura'], destaque['altura']) // 2
                tamanho_fonte = max(tamanho_fonte, 12)  # Mínimo de 12 para legibilidade
                
                # Obter dimensões do texto para centralizá-lo
                if fonte:
                    # Estimar largura do texto (muitas vezes 'getsize' não está disponível nas versões mais recentes)
                    try:
                        # Para versões mais antigas do PIL/Pillow
                        largura_texto, altura_texto = fonte.getsize(numero_str)
                    except AttributeError:
                        try:
                            # Para versões mais recentes do PIL/Pillow
                            bbox = fonte.getbbox(numero_str)
                            largura_texto, altura_texto = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        except Exception:
                            # Estimativa se nenhum método funcionar
                            largura_texto = len(numero_str) * tamanho_fonte * 0.6
                            altura_texto = tamanho_fonte
                    
                    pos_x = destaque['x'] - largura_texto // 2
                    pos_y = destaque['y'] - altura_texto // 2
                    
                    # Garantir que o número fique dentro do retângulo
                    pos_x = max(pos_x, destaque['x'] - destaque['largura'] // 2 + 2)
                    pos_y = max(pos_y, destaque['y'] - destaque['altura'] // 2 + 2)
                    
                    # Desenhar o número
                    desenho.text((pos_x, pos_y), numero_str, fill=(0, 0, 255), font=fonte)
                else:
                    # Caso não tenha fonte disponível, desenhar diretamente
                    desenho.text((destaque['x'] - 5, destaque['y'] - 10), numero_str, fill=(0, 0, 255))
        
        # Salvar a imagem modificada na pasta de destino
        nome_arquivo = imagem_path.name
        caminho_saida = caminho_destino / nome_arquivo
        imagem.save(caminho_saida, quality=95)
        
        return True, palavras_encontradas, True
    
    except Exception as e:
        logger.error(f"Erro ao processar a imagem {imagem_path.name}: {str(e)}")
        return False, 0, False

def solicitar_palavras_chave():
    """Solicita ao usuário que insira as palavras-chave a serem destacadas."""
    print("\nInsira as palavras ou frases que deseja destacar nas imagens (uma por linha).")
    print("Você pode inserir termos simples como 'osso' ou compostos como 'sutura lacrimal'.")
    print("Digite uma linha vazia para finalizar a entrada:\n")
    
    palavras_chave = []
    while True:
        palavra = input().strip()
        if not palavra:
            break
        palavras_chave.append(palavra)
    
    return palavras_chave

def obter_opcoes_usuario():
    """Solicita ao usuário opções de processamento."""
    opcoes = {}
    
    # Opção para deletar imagens sem palavras destacadas
    print("\nDeseja deletar as imagens que não contêm nenhuma das palavras destacadas? (s/n)")
    resposta = input().strip().lower()
    opcoes['deletar_sem_destaque'] = resposta == 's'
    
    # Opção para ocultar as palavras destacadas (agora com a opção 't')
    print("\nDeseja apagar a palavra destacada da imagem, mantendo apenas a borda de destaque?")
    print("(s) Sim - apenas versão com palavras ocultadas")
    print("(n) Não - apenas versão com palavras visíveis")
    print("(t) Tudo - criar versões 'Gabarito' e 'Prova'")
    resposta = input().strip().lower()
    
    if resposta == 't':
        opcoes['modo_duplo'] = True
        opcoes['ocultar_palavras'] = False  # Valor temporário, será tratado especialmente
    else:
        opcoes['modo_duplo'] = False
        opcoes['ocultar_palavras'] = resposta == 's'
    
    # Se o usuário escolheu ocultar palavras (opção 's' ou 't'), perguntar sobre numeração
    if resposta == 's' or resposta == 't':
        print("\nDeseja substituir as palavras apagadas por uma numeração sequencial (1, 2, 3...)? (s/n)")
        resposta_numeracao = input().strip().lower()
        opcoes['numerar_palavras'] = resposta_numeracao == 's'
    else:
        opcoes['numerar_palavras'] = False
    
    return opcoes

def processar_imagens(caminho_pasta, palavras_chave, opcoes):
    """Processa todas as imagens na pasta, destacando as palavras-chave."""
    # Verificar se o caminho existe
    if not os.path.exists(caminho_pasta):
        logger.error(f"O caminho '{caminho_pasta}' não existe.")
        return
    
    # Verificar se foram fornecidas palavras-chave
    if not palavras_chave:
        logger.error("Nenhuma palavra-chave fornecida. O processamento não pode continuar.")
        return
    
    # Criar pasta de destino
    if opcoes['modo_duplo']:
        pasta_gabarito = criar_pasta_destino(caminho_pasta, "Gabarito")
        pasta_prova = criar_pasta_destino(caminho_pasta, "Prova")
        pasta_destino = None  # Não será usada no modo duplo
    else:
        pasta_destino = criar_pasta_destino(caminho_pasta)
        pasta_gabarito = None
        pasta_prova = None
    
    # Listar todas as imagens na pasta
    imagens = listar_imagens(caminho_pasta)
    
    if not imagens:
        logger.warning(f"Nenhuma imagem encontrada em {caminho_pasta}")
        return
    
    logger.info(f"Encontradas {len(imagens)} imagens para processamento.")
    logger.info(f"Termos a destacar: {', '.join(palavras_chave)}")
    
    # Registrar as opções escolhidas
    logger.info(f"Deletar imagens sem palavras destacadas: {'Sim' if opcoes['deletar_sem_destaque'] else 'Não'}")
    
    if opcoes['modo_duplo']:
        logger.info(f"Modo: Duplo (Gabarito e Prova)")
        if opcoes['numerar_palavras']:
            logger.info(f"Numeração sequencial: Sim (somente na versão Prova)")
    else:
        logger.info(f"Ocultar palavras destacadas: {'Sim' if opcoes['ocultar_palavras'] else 'Não'}")
        if opcoes['ocultar_palavras'] and opcoes['numerar_palavras']:
            logger.info(f"Numeração sequencial: Sim")
    
    # Processar cada imagem com uma barra de progresso
    imagens_processadas = 0
    imagens_com_erro = 0
    imagens_sem_palavras = 0
    imagens_deletadas = 0
    total_palavras_destacadas = 0
    
    for imagem_path in tqdm(imagens, desc="Processando imagens"):
        logger.info(f"Processando: {imagem_path.name}")
        
        if opcoes['modo_duplo']:
            # No modo duplo, processar para ambas as pastas
            # Primeiro para o gabarito (palavras visíveis)
            sucesso_gabarito, palavras_destacadas_gabarito, encontrou_palavras_gabarito = detectar_e_destacar_palavras(
                imagem_path, 
                pasta_gabarito, 
                palavras_chave,
                False,  # Não ocultar palavras para o gabarito
                False   # Não numerar palavras para o gabarito
            )
            
            # Depois para a prova (palavras ocultas)
            sucesso_prova, palavras_destacadas_prova, encontrou_palavras_prova = detectar_e_destacar_palavras(
                imagem_path, 
                pasta_prova, 
                palavras_chave,
                True,  # Ocultar palavras para a prova
                opcoes['numerar_palavras']  # Usar a opção de numeração para a prova
            )
            
            sucesso = sucesso_gabarito and sucesso_prova
            palavras_destacadas = palavras_destacadas_gabarito  # Ambos devem ser iguais
            encontrou_palavras = encontrou_palavras_gabarito    # Ambos devem ser iguais
            
            # Se a opção de deletar imagens sem destaque estiver ativada e nenhuma palavra foi encontrada
            if opcoes['deletar_sem_destaque'] and not encontrou_palavras:
                # Excluir os arquivos das pastas de destino
                caminho_gabarito = pasta_gabarito / imagem_path.name
                caminho_prova = pasta_prova / imagem_path.name
                
                if caminho_gabarito.exists():
                    caminho_gabarito.unlink()
                if caminho_prova.exists():
                    caminho_prova.unlink()
                    
                logger.info(f"✗ {imagem_path.name} - Excluída por não conter palavras-chave")
                imagens_deletadas += 1
            
        else:
            # Modo normal, processar para uma única pasta
            sucesso, palavras_destacadas, encontrou_palavras = detectar_e_destacar_palavras(
                imagem_path, 
                pasta_destino, 
                palavras_chave,
                opcoes['ocultar_palavras'],
                opcoes['ocultar_palavras'] and opcoes['numerar_palavras']  # Numerar apenas se estiver ocultando palavras
            )
            
            # Se a opção de deletar imagens sem destaque estiver ativada
            if not encontrou_palavras and opcoes['deletar_sem_destaque']:
                # Excluir o arquivo da pasta de destino
                caminho_saida = pasta_destino / imagem_path.name
                if caminho_saida.exists():
                    caminho_saida.unlink()
                    logger.info(f"✗ {imagem_path.name} - Excluída por não conter palavras-chave")
                    imagens_deletadas += 1
                    
        if sucesso:
            imagens_processadas += 1
            total_palavras_destacadas += palavras_destacadas
            
            if not encontrou_palavras:
                imagens_sem_palavras += 1
                if not opcoes['deletar_sem_destaque']:
                    logger.info(f"✓ {imagem_path.name} - Nenhuma ocorrência encontrada (mantida)")
            else:
                if opcoes['modo_duplo']:
                    texto_info = f"{palavras_destacadas} ocorrências destacadas (gabarito e prova)"
                    if opcoes['numerar_palavras']:
                        texto_info += " com numeração"
                    logger.info(f"✓ {imagem_path.name} - {texto_info}")
                else:
                    texto_info = f"{palavras_destacadas} ocorrências destacadas"
                    if opcoes['ocultar_palavras'] and opcoes['numerar_palavras']:
                        texto_info += " com numeração"
                    logger.info(f"✓ {imagem_path.name} - {texto_info}")
        else:
            imagens_com_erro += 1
            logger.error(f"✗ Falha ao processar {imagem_path.name}")
    
    # Relatório final
    logger.info("\n" + "="*50)
    logger.info(f"Processamento concluído!")
    logger.info(f"Total de imagens processadas: {imagens_processadas}")
    logger.info(f"Total de imagens com ocorrências encontradas: {imagens_processadas - imagens_sem_palavras}")
    logger.info(f"Total de imagens sem ocorrências: {imagens_sem_palavras}")
    if opcoes['deletar_sem_destaque']:
        logger.info(f"Total de imagens excluídas: {imagens_deletadas}")
    logger.info(f"Total de imagens com erro: {imagens_com_erro}")
    logger.info(f"Total de ocorrências destacadas: {total_palavras_destacadas}")
    
    if opcoes['modo_duplo']:
        logger.info(f"Imagens com palavras visíveis (gabarito) salvas em: {pasta_gabarito}")
        texto_prova = f"Imagens com palavras ocultas (prova) salvas em: {pasta_prova}"
        if opcoes['numerar_palavras']:
            texto_prova += " [com numeração sequencial]"
        logger.info(texto_prova)
    else:
        texto_saida = f"Imagens processadas salvas em: {pasta_destino}"
        if opcoes['ocultar_palavras'] and opcoes['numerar_palavras']:
            texto_saida += " [com numeração sequencial]"
        logger.info(texto_saida)
    
    logger.info("="*50)

def main():
    # Verificar se o pytesseract está configurado corretamente primeiro
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        print(f"{Fore.RED}Erro ao inicializar o Tesseract OCR: {str(e)}")
        print(f"Verifique se o Tesseract OCR está instalado corretamente.{Fore.RESET}")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="Programa para destacar palavras ou frases específicas em imagens usando OCR")
    parser.add_argument("caminho", nargs="?", help="Caminho da pasta contendo as imagens")
    args = parser.parse_args()
    
    # Se o caminho não foi fornecido como argumento, solicitar ao usuário
    caminho_pasta = args.caminho
    
    # Loop para validar o caminho até que seja válido
    while True:
        if not caminho_pasta:
            caminho_pasta = input("Digite o caminho da pasta contendo as imagens: ").strip()
        
        # Validar o caminho antes de continuar
        valido, mensagem = validar_caminho(caminho_pasta)
        
        if valido:
            print(f"{Fore.GREEN}{mensagem}{Fore.RESET}")
            break
        else:
            print(f"{Fore.RED}Erro: {mensagem}{Fore.RESET}")
            caminho_pasta = None  # Resetar para solicitar novamente
    
    # Solicitar as palavras-chave a serem destacadas
    palavras_chave = solicitar_palavras_chave()
    
    # Solicitar as opções de processamento
    opcoes = obter_opcoes_usuario()
    
    # Processar as imagens
    processar_imagens(caminho_pasta, palavras_chave, opcoes)

if __name__ == "__main__":
    main()
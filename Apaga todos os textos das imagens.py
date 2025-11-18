import os
import sys
from pathlib import Path
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from PIL import Image, ImageDraw
import argparse
from tqdm import tqdm
import logging

"""
Este programa foi desenvolvido para **remover automaticamente textos de imagens** utilizando reconhecimento óptico de caracteres (OCR) com a biblioteca `pytesseract`.

FUNCIONALIDADES:

1. **Entrada do Caminho da Pasta**:
   O usuário fornece o caminho de uma pasta contendo imagens. Caso o caminho não seja passado como argumento na linha de comando, o programa solicitará a entrada interativa no terminal.

2. **Criação de Pasta de Destino**:
   Uma nova pasta é criada no mesmo diretório da pasta original, com o prefixo "Tampado-". Todas as imagens modificadas serão salvas nesta nova pasta.

3. **Detecção de Texto**:
   Cada imagem é analisada com a biblioteca `pytesseract`, que detecta automaticamente os blocos de texto presentes na imagem por meio de OCR (Reconhecimento Óptico de Caracteres).

4. **Cobertura do Texto**:
   Cada área de texto detectada é coberta com um **retângulo branco**, apagando o conteúdo textual visível da imagem.

5. **Conversão de Modos de Cor**:
   Se a imagem estiver em um modo de cor diferente de RGB (como RGBA ou L), ela é convertida para o modo RGB antes da modificação, garantindo compatibilidade ao salvar.

6. **Feedback em Tempo Real**:
   - O programa exibe uma barra de progresso (com `tqdm`) mostrando o andamento do processamento.
   - Um log detalhado é salvo no arquivo `processamento_imagens.log` e também mostrado no terminal.

7. **Relatório Final**:
   Ao final do processamento, o programa exibe um resumo com:
   - Número total de imagens processadas.
   - Quantidade de imagens com erro.
   - Total de blocos de texto cobertos.
   - Caminho da pasta onde as imagens editadas foram salvas.

REQUISITOS:
- Python 3.
- Bibliotecas instaladas: `pytesseract`, `Pillow`, `tqdm`.
- Tesseract OCR instalado no sistema (com caminho corretamente configurado).

USO:
Ideal para situações em que é necessário ocultar informações textuais de imagens, como em provas, figuras didáticas, atividades de revisão ou arquivos que precisam ser anonimizados visualmente.

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

def criar_pasta_destino(caminho_original):
    """Cria a pasta de destino baseada no nome da pasta original."""
    pasta_original = Path(caminho_original)
    nome_pasta_destino = f"Tampado-{pasta_original.name}"
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

def detectar_e_cobrir_texto(imagem_path, caminho_destino):
    """Detecta texto na imagem e o cobre com retângulos brancos."""
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
        
        # Usar o pytesseract para detectar blocos de texto
        dados = pytesseract.image_to_data(imagem, output_type=pytesseract.Output.DICT)
        
        # Criar objeto para desenhar na imagem
        desenho = ImageDraw.Draw(imagem)
        
        # Cobrir cada bloco de texto detectado
        total_blocos_cobertos = 0
        for i in range(len(dados['text'])):
            # Verificar se o texto detectado não é vazio
            if dados['conf'][i] > 0 and dados['text'][i].strip():
                x = dados['left'][i]
                y = dados['top'][i]
                largura = dados['width'][i]
                altura = dados['height'][i]
                
                # Desenhar retângulo branco sobre o texto
                desenho.rectangle([x, y, x + largura, y + altura], fill=(255, 255, 255))
                total_blocos_cobertos += 1
        
        # Salvar a imagem modificada na pasta de destino
        nome_arquivo = imagem_path.name
        caminho_saida = caminho_destino / nome_arquivo
        imagem.save(caminho_saida, quality=95)
        
        return True, total_blocos_cobertos
    
    except Exception as e:
        logger.error(f"Erro ao processar a imagem {imagem_path.name}: {str(e)}")
        return False, 0

def processar_imagens(caminho_pasta):
    """Processa todas as imagens na pasta, detectando e cobrindo textos."""
    # Verificar se o caminho existe
    if not os.path.exists(caminho_pasta):
        logger.error(f"O caminho '{caminho_pasta}' não existe.")
        return
    
    # Criar pasta de destino
    pasta_destino = criar_pasta_destino(caminho_pasta)
    
    # Listar todas as imagens na pasta
    imagens = listar_imagens(caminho_pasta)
    
    if not imagens:
        logger.warning(f"Nenhuma imagem encontrada em {caminho_pasta}")
        return
    
    logger.info(f"Encontradas {len(imagens)} imagens para processamento.")
    
    # Processar cada imagem com uma barra de progresso
    imagens_processadas = 0
    imagens_com_erro = 0
    total_blocos_texto = 0
    
    for imagem_path in tqdm(imagens, desc="Processando imagens"):
        logger.info(f"Processando: {imagem_path.name}")
        sucesso, blocos_cobertos = detectar_e_cobrir_texto(imagem_path, pasta_destino)
        
        if sucesso:
            imagens_processadas += 1
            total_blocos_texto += blocos_cobertos
            logger.info(f"✓ {imagem_path.name} - {blocos_cobertos} blocos de texto cobertos")
        else:
            imagens_com_erro += 1
            logger.error(f"✗ Falha ao processar {imagem_path.name}")
    
    # Relatório final
    logger.info("\n" + "="*50)
    logger.info(f"Processamento concluído!")
    logger.info(f"Total de imagens processadas: {imagens_processadas}")
    logger.info(f"Total de imagens com erro: {imagens_com_erro}")
    logger.info(f"Total de blocos de texto cobertos: {total_blocos_texto}")
    logger.info(f"Imagens com textos cobertos salvas em: {pasta_destino}")
    logger.info("="*50)

def main():
    parser = argparse.ArgumentParser(description="Programa para cobrir textos em imagens usando OCR")
    parser.add_argument("caminho", nargs="?", help="Caminho da pasta contendo as imagens")
    args = parser.parse_args()
    
    # Se o caminho não foi fornecido como argumento, solicitar ao usuário
    caminho_pasta = args.caminho
    if not caminho_pasta:
        caminho_pasta = input("Digite o caminho da pasta contendo as imagens: ").strip()
    
    # Verificar se o pytesseract está configurado corretamente
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        logger.error(f"Erro ao inicializar o Tesseract OCR: {str(e)}")
        logger.error("Verifique se o Tesseract OCR está instalado corretamente.")
        sys.exit(1)
    
    # Processar as imagens
    processar_imagens(caminho_pasta)

if __name__ == "__main__":
    main()
import os
import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
"""
Este programa extrai **imagens completas de livros de anatomia em PDF**, preservando detalhes como setas, legendas e textos. A extração é feita por meio de processamento visual (print da página), garantindo que mesmo figuras não embutidas como imagens (ex: páginas escaneadas ou desenhadas) sejam capturadas corretamente.

FUNCIONALIDADES:

1. **Entrada Interativa do Caminho do PDF**:
   O usuário digita o caminho do arquivo PDF. O programa valida se é um arquivo existente e se tem a extensão `.pdf`.

2. **Renderização Visual das Páginas (300 DPI)**:
   Cada página é convertida para uma imagem com alta resolução (300 DPI), garantindo nitidez e fidelidade visual.

3. **Processamento com OpenCV**:
   - A imagem é convertida em escala de cinza.
   - Aplicado filtro de bordas (`Canny`) seguido de dilatação para detectar áreas que se destacam (normalmente quadros ou figuras).
   - Detecta contornos grandes (filtrando pequenos ruídos com base na área).

4. **Recorte Inteligente das Imagens**:
   - Cada contorno é transformado em um retângulo com **margem extra ajustável** (horizontal e vertical).
   - Isso permite capturar não apenas a imagem central, mas também suas **legendas, números e setas explicativas**.

5. **Exportação das Imagens**:
   - As imagens recortadas são convertidas para RGB e salvas no formato `.png`.
   - São salvas sequencialmente em uma pasta com nome `imagens de NOME_DO_PDF`, no mesmo diretório do arquivo original.

6. **Mensagens e Progresso no Terminal**:
   - O script informa o progresso da extração por página.
   - Notifica quantas imagens foram extraídas ao final.

7. **Tratamento de Erros**:
   Qualquer erro durante a leitura do PDF ou de uma página específica é exibido sem interromper o processo completo.

REQUISITOS:
- Python 3
- Bibliotecas necessárias:
  - `PyMuPDF` (instalar com `pip install pymupdf`)
  - `opencv-python` (instalar com `pip install opencv-python`)
  - `Pillow` (instalar com `pip install pillow`)
  - `numpy` (instalar com `pip install numpy`)

USO RECOMENDADO:
- Estudantes e professores de anatomia que desejam extrair figuras de livros digitais.
- Criar bancos de imagens com ilustrações médicas para estudo.
- Recortar quadros ou diagramas presentes em livros escaneados.

OBSERVAÇÃO:
Este código **não extrai imagens embutidas diretamente no PDF** (como JPEGs ou vetores), mas sim imagens "visíveis", capturadas por screenshot da página. Ele é ideal para PDFs escaneados ou com layout gráfico complexo, como os de anatomia.

"""

def obter_caminho_pdf_valido():
    """
    Solicita ao usuário o caminho do arquivo PDF e verifica se é válido.
    Repete até que um caminho válido seja fornecido.
    """
    while True:
        caminho_pdf = input("\nDigite o caminho completo do arquivo PDF de anatomia: ").strip()
        
        if (caminho_pdf.startswith('"') and caminho_pdf.endswith('"')) or \
           (caminho_pdf.startswith("'") and caminho_pdf.endswith("'")):
            caminho_pdf = caminho_pdf[1:-1]
        
        if not os.path.exists(caminho_pdf):
            print(f"Erro: O arquivo '{caminho_pdf}' não foi encontrado.")
            continue
        
        if not caminho_pdf.lower().endswith('.pdf'):
            print(f"Erro: O arquivo '{caminho_pdf}' não parece ser um PDF.")
            continue
        
        return caminho_pdf

def extrair_imagens_pdf_anatomia():
    """
    Função principal que solicita o caminho do PDF ao usuário e 
    extrai imagens completas (incluindo setas e legendas).
    """
    print("===== EXTRATOR DE IMAGENS DE LIVROS DE ANATOMIA =====")
    print("Este programa extrai imagens completas (incluindo legendas e setas) de PDFs.")
    
    caminho_pdf = obter_caminho_pdf_valido()
    
    nome_base = os.path.basename(caminho_pdf)
    nome_pdf_sem_extensao = os.path.splitext(nome_base)[0]
    
    diretorio_destino = f"imagens de {nome_pdf_sem_extensao}"
    diretorio_completo = os.path.join(os.path.dirname(caminho_pdf), diretorio_destino)
    
    if not os.path.exists(diretorio_completo):
        os.makedirs(diretorio_completo)
        print(f"Diretório criado: {diretorio_completo}")
    
    try:
        documento = fitz.open(caminho_pdf)
    except Exception as e:
        print(f"Erro ao abrir o PDF: {e}")
        return
    
    contador_imagens = 0
    
    print(f"\nProcessando PDF: {caminho_pdf}")
    print(f"Total de páginas: {len(documento)}")
    
    for num_pagina, pagina in enumerate(documento, 1):
        print(f"Processando página {num_pagina}/{len(documento)}...")
        
        try:
            pix = pagina.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
            img_bytes = pix.tobytes("png")
            
            nparr = np.frombuffer(img_bytes, np.uint8)
            img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            img_gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
            
            edges = cv2.Canny(img_gray, 50, 150)
            kernel = np.ones((5, 5), np.uint8)
            dilated = cv2.dilate(edges, kernel, iterations=2)
            
            contornos, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            area_minima = img_np.shape[0] * img_np.shape[1] * 0.01
            contornos_filtrados = [c for c in contornos if cv2.contourArea(c) > area_minima]
            
            for i, contorno in enumerate(contornos_filtrados):
                x, y, w, h = cv2.boundingRect(contorno)
                
                # Margens ajustadas separadamente
                margem_horizontal = 300  # Aumente esse valor se quiser mais espaço nas laterais 400/10-> ficou bom para cranio
                margem_vertical = 100    # Pode ajustar se quiser mais ou menos espaço acima/abaixo

                x_com_margem = max(0, x - margem_horizontal)
                y_com_margem = max(0, y - margem_vertical)
                w_com_margem = min(img_np.shape[1] - x_com_margem, w + 2 * margem_horizontal)
                h_com_margem = min(img_np.shape[0] - y_com_margem, h + 2 * margem_vertical)
                
                recorte = img_np[y_com_margem:y_com_margem+h_com_margem, 
                                 x_com_margem:x_com_margem+w_com_margem]
                
                if recorte.size > 0:
                    recorte_rgb = cv2.cvtColor(recorte, cv2.COLOR_BGR2RGB)
                    imagem_pil = Image.fromarray(recorte_rgb)
                    
                    contador_imagens += 1
                    caminho_imagem = os.path.join(diretorio_completo, f"{contador_imagens}.png")
                    imagem_pil.save(caminho_imagem)
                    print(f"Imagem {contador_imagens} salva: {caminho_imagem}")
        
        except Exception as e:
            print(f"Erro ao processar a página {num_pagina}: {e}")
            continue
    
    documento.close()
    
    if contador_imagens > 0:
        print(f"\nProcessamento concluído! {contador_imagens} imagens extraídas para: {diretorio_completo}")
    else:
        print("\nNenhuma imagem foi encontrada no documento.")
    
    input("\nPressione Enter para encerrar...")

if __name__ == "__main__":
    try:
        extrair_imagens_pdf_anatomia()
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
        input("\nPressione Enter para encerrar...")

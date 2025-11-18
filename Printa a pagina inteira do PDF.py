import fitz  # PyMuPDF
import io
import os
from PIL import Image
"""PRINTA A PAGINA INTEIRA DO PDF"""

def extract_images_from_pdf(pdf_path, output_dir="imagens_extraidas"):
    """
    Extrai todas as imagens de um arquivo PDF e as salva enumeradas.
    
    Args:
        pdf_path (str): Caminho para o arquivo PDF
        output_dir (str): Diretório onde as imagens serão salvas
    """
    # Cria o diretório de saída se não existir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Diretório '{output_dir}' criado.")
    
    # Abre o documento PDF
    pdf_document = fitz.open(pdf_path)
    
    # Contador para nomear as imagens
    img_count = 0
    
    # Itera por cada página do PDF
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        
        # Obtém a lista de imagens na página
        image_list = page.get_images(full=True)
        
        print(f"Encontradas {len(image_list)} imagens na página {page_num + 1}")
        
        # Itera por cada imagem na página
        for image_index, img in enumerate(image_list, start=1):
            # Obtém o número da imagem no dicionário
            xref = img[0]
            
            # Extrai a imagem como bytes
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Determina o formato da imagem
            image_format = base_image["ext"]
            
            # Incrementa o contador
            img_count += 1
            
            # Salva a imagem como um arquivo PNG
            output_filename = os.path.join(output_dir, f"{img_count}.png")
            
            # Converte e salva a imagem usando PIL
            image = Image.open(io.BytesIO(image_bytes))
            image.save(output_filename)
            
            print(f"Imagem {img_count} salva como {output_filename}")
    
    print(f"Processo concluído. {img_count} imagens extraídas e salvas.")
    
    # Fecha o documento PDF
    pdf_document.close()

if __name__ == "__main__":
    # Exemplo de uso
    pdf_file = input("Digite o caminho do arquivo PDF: ")
    extract_images_from_pdf(pdf_file)

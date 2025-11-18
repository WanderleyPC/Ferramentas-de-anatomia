import fitz  # PyMuPDF
import io
import os
from PIL import Image

"""
Este programa extrai automaticamente todas as imagens embutidas em um arquivo PDF e as salva como arquivos de imagem (PNG) numerados sequencialmente. 

É especialmente útil para recuperar figuras, ilustrações, gráficos ou fotos que fazem parte de documentos PDF, como livros, apostilas, provas ou materiais escaneados.

FUNCIONALIDADES:

1. **Entrada do Caminho do PDF**:
   O programa solicita ao usuário o caminho completo do arquivo PDF a ser processado.

2. **Criação de Pasta de Saída**:
   - As imagens extraídas são salvas na pasta `imagens_extraidas` (ou outra, se especificada).
   - Caso a pasta ainda não exista, ela será criada automaticamente.

3. **Processamento Página por Página**:
   - O programa percorre todas as páginas do PDF.
   - Em cada página, detecta todas as imagens incorporadas (mesmo que não estejam visíveis diretamente).

4. **Extração e Salvamento**:
   - Cada imagem é extraída utilizando o `xref` (identificador interno do PDF).
   - As imagens são convertidas para o modo RGB, se necessário (ex: se vierem em CMYK).
   - São salvas como arquivos `.png` com nomes sequenciais (`1.png`, `2.png`, etc).

5. **Mensagens no Terminal**:
   Durante o processo, o programa informa:
   - Quantas imagens foram encontradas por página.
   - O progresso da extração.
   - Um resumo final com o número total de imagens extraídas.

REQUISITOS:
- Python 3
- Bibliotecas instaladas:
  - `PyMuPDF` (instalar com `pip install pymupdf`)
  - `Pillow` (instalar com `pip install pillow`)

USO IDEAL:
- Estudantes que desejam extrair figuras de apostilas e livros em PDF.
- Professores e autores que precisam reutilizar imagens de materiais.
- Processos de digitalização e arquivamento de imagens contidas em PDFs escaneados.

"""


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
            xref = img[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_format = base_image["ext"]

            img_count += 1
            output_filename = os.path.join(output_dir, f"{img_count}.png")

            # Abre a imagem com PIL
            image = Image.open(io.BytesIO(image_bytes))

            # Converte para RGB se necessário (por exemplo, se estiver em CMYK)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Salva como PNG
            image.save(output_filename)
            print(f"Imagem {img_count} salva como {output_filename}")

    print(f"Processo concluído. {img_count} imagens extraídas e salvas.")

    # Fecha o documento PDF
    pdf_document.close()

if __name__ == "__main__":
    # Exemplo de uso
    pdf_file = input("Digite o caminho do arquivo PDF: ")
    extract_images_from_pdf(pdf_file)

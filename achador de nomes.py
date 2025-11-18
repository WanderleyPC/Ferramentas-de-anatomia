#14/05/2025
"""

Este programa foi desenvolvido para identificar automaticamente nomes de músculos presentes em imagens salvas em uma pasta do computador. 

FUNCIONAMENTO:

1. **Entrada do Caminho da Pasta**:
   O usuário é solicitado a digitar o caminho da pasta onde estão armazenadas as imagens. O programa verifica se o caminho é válido e só prossegue se for confirmado que a pasta existe.

2. **Filtragem de Imagens**:
   O programa escaneia todos os arquivos da pasta e seleciona apenas aqueles com extensões compatíveis com imagens (ex: .jpg, .png, .jpeg, etc).

3. **Envio e Análise com a API do Gemini**:
   Cada imagem é enviada para a API do modelo de linguagem multimodal Gemini 2.0 Flash, que foi configurada com uma chave de API (armazenada na variável `chave`).
   O modelo é instruído a analisar o conteúdo visual da imagem e **listar todos os nomes de músculos** visíveis. Se não encontrar nenhum músculo, o modelo responde com “[NÃO TEM]”.

4. **Exibição dos Resultados no Console**:
   Para cada imagem processada, o nome do arquivo é impresso no terminal, seguido da resposta do modelo (ou seja, os músculos encontrados).

5. **Gravação dos Resultados em Arquivo**:
   Todas as respostas obtidas são armazenadas em um arquivo de texto chamado `palavras_da_imagem.txt`, com uma linha para cada imagem.

USO:
Ideal para estudantes de anatomia, professores ou profissionais da saúde que precisam extrair rapidamente nomes de músculos de imagens ilustrativas.

REQUISITOS:
- Biblioteca `google-genai` instalada.
- Chave de API válida do Google.
- Conexão com a internet.

OBS: O caminho das imagens deve conter barras (`/`) em vez de contrabarras (`\`).


"""

chave='AIzaSyD8Pi0WP3XxWQi00Eovh-V3d7UAjeVUN_4'

from google import genai
import os
client = genai.Client(api_key=chave)

#Verifica se você colocou o nome da pasta de forma correta. Se não, perde que coloque denovo.
while True:
    caminho_pasta_da_imagem=input('Qual o caminho da pasta\n')
    #caminho_pasta_da_imagem='C:/Users/wj511/Downloads/teste'
    if os.path.isdir(caminho_pasta_da_imagem):
        print('O caminho da pasta foi colocado corretamente.\n')
        break
    else:
        print('Coloque o caminho correto da pasta.\n')

# Extensões de imagem que você quer considerar
extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']

# Lista todos os arquivos na pasta e filtra os que têm extensões de imagem
imagens = [arquivo for arquivo in os.listdir(caminho_pasta_da_imagem)
           if os.path.isfile(os.path.join(caminho_pasta_da_imagem, arquivo)) and
           os.path.splitext(arquivo)[1].lower() in extensoes_imagem]

imagens_achadas=[]

for i, imagem in enumerate(imagens):

    meu_arquivo = client.files.upload(file=f"{caminho_pasta_da_imagem}/{imagem}") #Coloque o caminho com / em vez de \

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[meu_arquivo, '''Cite todos os nomes de musculos que você achar nessa imagem. Se não tiver escreva '[NÃO TEM]' Não escreva mais nada além disso.'''],
    )
    print(f'{i} imagem: {imagem}')
    print(response.text)
    print('-'*20)
    imagens_achadas.append(response.text)

with open("palavras_da_imagem.txt", "w", encoding="utf-8") as arquivo:
    for palavra in imagens_achadas:
        arquivo.write(palavra + '\n')


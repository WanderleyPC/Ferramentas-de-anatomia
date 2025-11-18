import os
"Esse é u"
# Caminho da pasta onde estão as imagens
pasta = 'C:/Users/wj511/Downloads/teste'

# Extensões de imagem que você quer considerar
extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']

# Lista todos os arquivos na pasta e filtra os que têm extensões de imagem
imagens = [arquivo for arquivo in os.listdir(pasta)
           if os.path.isfile(os.path.join(pasta, arquivo)) and
           os.path.splitext(arquivo)[1].lower() in extensoes_imagem]

# Imprime o nome das imagens
for imagem in imagens:
    print(imagem)

"""
Este programa identifica nomes de músculos em imagens anatômicas usando o modelo Gemini da Google.
Além de identificar os nomes, ele detecta as coordenadas exatas de cada nome e gera novas imagens
com retângulos brancos de borda vermelha cobrindo os nomes dos músculos.
"""

import os
import cv2
import numpy as np
import json
import re
from google import genai
from PIL import Image
import io
import time
from datetime import datetime

def processar_imagem(client, caminho_completo, nome_arquivo):
    """
    Processa uma imagem para detectar nomes de músculos e suas coordenadas
    
    Args:
        client: Cliente da API Gemini
        caminho_completo: Caminho completo para o arquivo de imagem
        nome_arquivo: Nome do arquivo para exibição
        
    Returns:
        tuple: (nomes de músculos detectados, coordenadas normalizadas)
    """
    print(f"Processando imagem: {nome_arquivo}")
    
    # Carrega a imagem para obter dimensões
    imagem_original = cv2.imread(caminho_completo)
    altura_img, largura_img = imagem_original.shape[:2]
    
    # Upload do arquivo para a API
    meu_arquivo = client.files.upload(file=caminho_completo)
    
    # Prompt em inglês para detectar nomes de músculos e suas coordenadas
    prompt = """
Tell me the exact coordinates of all the muscle names you find in this image and normalized to 0-1000. 
Don't put the coordinates of the muscle, I want the coordinate of the NAME of the muscle!
    
    Return ONLY a JSON in this exact format:
    {
        "detections": [
            {"muscle_name": "Name of Muscle 1", "box_2d": [ymin, xmin, ymax, xmax]},
            {"muscle_name": "Name of Muscle 2", "box_2d": [ymin, xmin, ymax, xmax]},
            ...
        ]
    }
    """
    
    try:
        # Chama a API Gemini
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[meu_arquivo, prompt],
            #tempertura=0.1
            #temperature=0.1
        )
        
        # Extrai dados JSON da resposta
        resultado = extrair_json_da_resposta(response.text)
        
        if resultado and "detections" in resultado:
            # Processa cada detecção para gerar coordenadas em pixels
            deteccoes_processadas = []
            nomes_musculos = []
            
            for deteccao in resultado["detections"]:
                nome = deteccao["muscle_name"]
                coords_norm = deteccao["box_2d"]
                
                # Converte coordenadas normalizadas para pixels
                ymin = int((coords_norm[0] / 1000) * altura_img)
                xmin = int((coords_norm[1] / 1000) * largura_img)
                ymax = int((coords_norm[2] / 1000) * altura_img)
                xmax = int((coords_norm[3] / 1000) * largura_img)
                
                deteccoes_processadas.append({
                    "nome": nome,
                    "coordenadas_norm": coords_norm,
                    "coordenadas_pixels": [ymin, xmin, ymax, xmax]
                })
                nomes_musculos.append(nome)
            
            return nomes_musculos, deteccoes_processadas
        else:
            print(f"Erro ao processar resposta da API para {nome_arquivo}.")
            if resultado:
                print(f"Formato recebido diferente do esperado. Chaves disponíveis: {list(resultado.keys())}")
            else:
                print(f"Não foi possível extrair JSON da resposta.")
            print(f"Resposta completa: {response.text}")
            return [], []
            
    except Exception as e:
        print(f"Erro ao processar imagem {nome_arquivo}: {str(e)}")
        return [], []

def extrair_json_da_resposta(texto_resposta):
    """
    Extrai dados JSON da resposta da API Gemini
    
    Args:
        texto_resposta: Texto da resposta da API
        
    Returns:
        dict: Dados JSON extraídos ou None se falhar
    """
    # Procura por estrutura JSON na resposta
    try:
        # Limpa a resposta para melhor processamento
        texto_limpo = texto_resposta.strip()
        
        # Procura por um objeto JSON entre chaves {}
        match = re.search(r'\{.*\}', texto_limpo, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        
        # Se não encontrou JSON com regex, tenta extrair como último recurso
        if "{" in texto_limpo and "}" in texto_limpo:
            inicio = texto_limpo.find("{")
            fim = texto_limpo.rfind("}") + 1
            json_str = texto_limpo[inicio:fim]
            return json.loads(json_str)
            
        print("Não foi possível encontrar dados JSON na resposta:")
        print(texto_resposta)
        return None
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON na resposta: {e}")
        print(f"Texto da resposta: {texto_resposta}")
        return None

def ocultar_nomes_musculos(caminho_imagem, deteccoes, pasta_saida):
    """
    Gera uma nova imagem com retângulos brancos de borda vermelha cobrindo os nomes dos músculos.
    
    Args:
        caminho_imagem: Caminho da imagem original
        deteccoes: Lista com as coordenadas dos músculos detectados
        pasta_saida: Pasta onde a imagem processada será salva
        
    Returns:
        str: Caminho da nova imagem gerada
    """
    # Carrega a imagem original
    imagem = cv2.imread(caminho_imagem)
    
    if imagem is None:
        print(f"Erro ao carregar imagem {caminho_imagem}")
        return None
    
    # Para cada detecção, desenha um retângulo branco com borda vermelha
    for deteccao in deteccoes:
        coords = deteccao["coordenadas_pixels"]
        ymin, xmin, ymax, xmax = coords
        
        # Adiciona um pequeno buffer às coordenadas para garantir cobertura completa
        buffer = 2  # pixels
        ymin = max(0, ymin - buffer)
        xmin = max(0, xmin - buffer)
        ymax = min(imagem.shape[0], ymax + buffer)
        xmax = min(imagem.shape[1], xmax + buffer)
        
        # Desenha retângulo branco (preenchimento)
        cv2.rectangle(imagem, (xmin, ymin), (xmax, ymax), (255, 255, 255), -1)
        
        # Desenha borda vermelha (2px)
        cv2.rectangle(imagem, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
    
    # Obtém nome do arquivo original
    nome_arquivo = os.path.basename(caminho_imagem)
    
    # Cria nome para arquivo processado
    nome_processado = f"processed_{nome_arquivo}"
    caminho_saida = os.path.join(pasta_saida, nome_processado)
    
    # Salva a imagem processada
    cv2.imwrite(caminho_saida, imagem)
    
    return caminho_saida

def criar_pasta_resultados():
    """
    Cria uma pasta para salvar os resultados com timestamp
    
    Returns:
        str: Caminho da pasta criada
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_resultados = f"resultados_musculos_{timestamp}"
    
    # Cria a pasta se não existir
    if not os.path.exists(pasta_resultados):
        os.makedirs(pasta_resultados)
        
    return pasta_resultados

def main():
    # É melhor usar variáveis de ambiente para chaves de API
    # Se não estiver definida, solicita ao usuário
    api_key = os.environ.get('AIzaSyD8Pi0WP3XxWQi00Eovh-V3d7UAjeVUN_4')
    if not api_key:
        api_key = input('Digite sua chave API do Google (ou configure GOOGLE_API_KEY como variável de ambiente):\n')
    
    # Inicializa o cliente Gemini
    try:
        client = genai.Client(api_key=api_key)
        print("Cliente Gemini inicializado com sucesso.\n")
    except Exception as e:
        print(f"Erro ao inicializar o cliente Gemini: {str(e)}")
        return
    
    # Solicita o caminho da pasta com as imagens
    while True:
        caminho_pasta_da_imagem = input('Qual o caminho da pasta com as imagens?\n')
        
        if os.path.isdir(caminho_pasta_da_imagem):
            print('O caminho da pasta foi colocado corretamente.\n')
            break
        else:
            print('Coloque o caminho correto da pasta.\n')
    
    # Cria pasta para resultados
    pasta_resultados = criar_pasta_resultados()
    print(f"Resultados serão salvos em: {pasta_resultados}")
    
    # Extensões de imagem que serão processadas
    extensoes_imagem = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
    
    # Lista todos os arquivos na pasta e filtra os que têm extensões de imagem
    imagens = [arquivo for arquivo in os.listdir(caminho_pasta_da_imagem)
               if os.path.isfile(os.path.join(caminho_pasta_da_imagem, arquivo)) and
               os.path.splitext(arquivo)[1].lower() in extensoes_imagem]
    
    if not imagens:
        print(f"Nenhuma imagem encontrada na pasta {caminho_pasta_da_imagem}")
        return
    
    print(f"Encontradas {len(imagens)} imagens para processamento.")
    
    # Dicionário para armazenar resultados
    resultados = {}
    
    # Processa cada imagem
    for i, imagem in enumerate(imagens):
        print(f"\nProcessando imagem {i+1}/{len(imagens)}: {imagem}")
        
        caminho_completo = os.path.join(caminho_pasta_da_imagem, imagem)
        
        # Processa a imagem com a API Gemini
        nomes_musculos, deteccoes = processar_imagem(client, caminho_completo, imagem)
        
        if nomes_musculos:
            print(f"Detectados {len(nomes_musculos)} músculos: {', '.join(nomes_musculos)}")
            
            # Gera imagem com nomes ocultados
            if deteccoes:
                caminho_imagem_processada = ocultar_nomes_musculos(caminho_completo, deteccoes, pasta_resultados)
                if caminho_imagem_processada:
                    print(f"Imagem processada salva em: {caminho_imagem_processada}")
            
            # Armazena resultados
            resultados[imagem] = {
                "nomes_musculos": nomes_musculos,
                "deteccoes": [{
                    "nome": d["nome"],
                    "coordenadas_norm": d["coordenadas_norm"]
                } for d in deteccoes]  # Simplifica para armazenamento
            }
        else:
            print(f"Nenhum músculo detectado na imagem {imagem}")
            resultados[imagem] = {"nomes_musculos": [], "deteccoes": []}
    
    # Salva resultados em arquivo de texto
    caminho_txt = os.path.join(pasta_resultados, "musculos_detectados.txt")
    with open(caminho_txt, "w", encoding="utf-8") as arquivo:
        arquivo.write("MÚSCULOS DETECTADOS NAS IMAGENS\n")
        arquivo.write("=" * 40 + "\n\n")
        
        for nome_img, dados in resultados.items():
            arquivo.write(f"Imagem: {nome_img}\n")
            if dados["nomes_musculos"]:
                arquivo.write("Músculos detectados:\n")
                for i, nome in enumerate(dados["nomes_musculos"]):
                    arquivo.write(f"  {i+1}. {nome}\n")
            else:
                arquivo.write("Nenhum músculo detectado.\n")
            arquivo.write("-" * 40 + "\n\n")
    
    # Salva dados detalhados em formato JSON
    caminho_json = os.path.join(pasta_resultados, "deteccoes_completas.json")
    with open(caminho_json, "w", encoding="utf-8") as arquivo:
        json.dump(resultados, arquivo, indent=4, ensure_ascii=False)
    
    print(f"\nProcessamento concluído!")
    print(f"Resultados salvos em: {pasta_resultados}")
    print(f"  - Imagens processadas com os nomes ocultados")
    print(f"  - Lista de músculos: {caminho_txt}")
    print(f"  - Dados detalhados: {caminho_json}")

if __name__ == "__main__":
    main()
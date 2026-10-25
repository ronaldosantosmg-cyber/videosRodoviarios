"""Orientação determinística local; mensagens são dados, nunca código executável."""
import math

RULES=[
 (('pedestre','passarela','travessia'), 'Conferir travessia e pontos de espera', ['Mantenha a espera fora da pista e dos trilhos; use faixa cadastrada, calçada ou passarela com vão suficiente.','Confira gabarito da passarela e fase exclusiva de pedestres; a aproximação do trem mantém a travessia fechada até liberar toda a composição.']),
 (('kmz','kml','zip'), 'Arquivo geográfico não pôde ser interpretado', ['Confira se o KMZ contém um KML válido e se o arquivo abre no aplicativo de origem.','Reexporte o arquivo sem anexos desnecessários; mantenha o original para conferência.']),
 (('layer','camada','pavimento','corpo_fora','trajetória','fluxo'), 'Conferir geometria, superfície e classificação', ['Use Corrigir fluxos para localizar o defeito, recuperar partes válidas ou recortar o intervalo.','Confira as camadas Eixo, Pavimento, Bordo, Canteiro e Barreira; referências não são obstáculos físicos.']),
 (('nan','infinity','finite','nulo','vazio','inválido','validation','422'), 'Entrada ou configuração inválida', ['Confira os campos citados na mensagem e informe números finitos, unidades e valores dentro dos limites.','Corrija a configuração e salve antes de repetir o cálculo.']),
 (('errno 2','no such file','arquivo não encontrado','pasta ausente'), 'Arquivo ou pasta indisponível', ['Confira se a pasta existe e se o OneDrive concluiu a sincronização; disponibilize os arquivos localmente.','Reabra o projeto correto; não recrie nem apague o original para contornar uma falha de caminho.']),
 (('permission','permissão','acesso negado','locked','winerror 32'), 'Acesso ao arquivo bloqueado', ['Feche o vídeo ou arquivo em outros programas e aguarde a sincronização.','Confira a permissão de gravação e repita sem apagar o projeto.']),
 (('memory','memória','excessiv','grande','timeout','demora'), 'Limite de recursos ou tempo', ['Faça uma prévia de um trecho menor e reduza a resolução/duração para diagnosticar.','Verifique espaço livre e arquivos de entrada; mantenha os caches persistentes e os originais.']),
 (('geotiff','raster','imagem','gdal','ecw','mrsid'), 'Conferir imagem e georreferência', ['Confira o CRS, a georreferência e o formato suportado; prefira GeoTIFF local quando disponível.','Converta pelo painel de imagens, aguarde a conclusão e confirme a fonte de apresentação.']),
 (('ffmpeg','encoder','mp4','vídeo'), 'Conferir exportação do vídeo', ['Confira o FFmpeg e a pasta de saída; feche vídeos que estejam abertos.','Gere uma prévia curta antes de repetir a exportação e confira o relatório de processamento.']),
 (('alinhamento','alignment','resíduo','residuo'), 'Conferir alinhamento e pontos de controle', ['Confira o CRS e a correspondência dos pontos de controle nas duas fontes.','Remova pares inconsistentes e recalcule os resíduos antes de aplicar.'])]

def guidance(kind,message,point=None):
    defaults={'analyze':'Conferir camadas, eixo e pavimento antes de analisar fluxos.','preview':'Conferir imagem, enquadramento e configurações da prévia.','render':'Conferir FFmpeg, configuração do vídeo e pasta de saída.','scene3d':'Conferir geometria, memória e atualização da cena 3D.','convert_imagery':'Conferir imagem, CRS e drivers de leitura.','alignment':'Conferir alinhamento e pares de pontos de controle.'}
    kind=str(kind or 'cálculo')[:80];message=str(message or '')[:8000];text=(kind+' '+(message or defaults.get(kind,''))).casefold()
    matches=[(title,steps) for terms,title,steps in RULES if any(term in text for term in terms)]
    if not matches:matches=[('Conferir entradas e relatório do cálculo',['Confira os arquivos, as configurações e a mensagem original do processamento.','Corrija a causa indicada, salve e repita uma prévia curta; preserve o projeto e o histórico.'])]
    location=None
    if isinstance(point,(list,tuple)) and len(point)==2 and all(isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n) and abs(n)<=1e9 for n in point):location=list(point)
    return dict(method='sistema_especialista_local',kind=kind,title='Como corrigir este cálculo',causes=[t for t,_ in matches],steps=list(dict.fromkeys(s for _,steps in matches for s in steps)),point=location,
                message=message,limitations='Hipóteses e passos baseados em regras locais. Não é diagnóstico garantido, modelo treinado ou certificação; a localização só aparece quando informada pelo cálculo.')

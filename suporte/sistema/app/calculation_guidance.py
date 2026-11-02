"""Orientação determinística local; mensagens são dados, nunca código executável."""
import math

RULES=[
 (('not defined','referenceerror','syntaxerror','rodoviadesktopworkspace'), 'Comando da interface indisponível', ['Preserve as alterações e confira se a atualização instalou todos os módulos da mesma revisão.','Após salvar ou descartar conscientemente a edição, reabra a interface; se persistir, exporte o log com a versão e o comando acionado.']),
 (('config.json','corromp','historico','histórico','.estado','jsondecode'), 'Conferir integridade e recuperação do projeto', ['Abra Proteção e recuperação para inspecionar a configuração e as cópias válidas antes de restaurar.','Não inicialize um projeto vazio sobre a pasta original; localize os arquivos ausentes ou um backup conferido.']),
 (('409','revisão','revision','obsoleto','outro projeto'), 'Resultado ou configuração de outra revisão', ['Confira o projeto ativo e preserve as alterações locais antes de reabrir resultados.','Atualize o diagnóstico na revisão atual; não aplique propostas antigas nem sobrescreva o arquivo externo.']),
 (('barreira','colisão','contramão','sinal vermelho','interdição'), 'Impedimento físico ou operacional do tráfego', ['Localize o ponto amarelo e confira faixa, nível, sentido e interferência física.','Use uma proposta de correção validada ou edite o trecho; mantenha a proteção contra colisões, barreiras, interdições e sinal vermelho.']),
 (('seção','secao','terceira faixa','acostamento'), 'Conferir seção operacional e afastamento do eixo', ['Confira início, fim, sentido, larguras e faixas ativas da seção típica.','Acostamentos e bordos não criam faixas de circulação; ajuste a faixa dentro do pavimento real e revalide.']),
 (('textura','material','hachura','oae'), 'Conferir classificação e material de apresentação', ['Confira a classe do elemento e o material aplicado, preservando os mapeamentos manuais.','Valide uma amostra na prévia e uma exportação curta; não esconda falhas de material para concluir o vídeo.']),
 (('webgl','context lost','contexto perdido','shader'), 'Conferir visualização gráfica', ['Retorne à vista 2D e preserve o projeto antes de reconstruir a cena 3D.','Confira aceleração gráfica e memória; reúna o log se o contexto continuar sendo perdido.']),
 (('enospc','no space','espaço insuficiente','disco cheio'), 'Espaço insuficiente para gravar', ['Confira o espaço na unidade do projeto e da saída de vídeo.','Use Manutenção para revisar caches regeneráveis; não apague projetos, vídeos ou imagens originais.']),
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
    actions=[]
    def action(code,label):
        if code not in [a['id'] for a in actions]:actions.append({'id':code,'label':label})
    if any(t in text for t in ('config.json','corromp','historico','histórico','.estado','errno 2','no such file','pasta ausente')):action('protection','Conferir proteção e recuperação')
    if any(t in text for t in ('fluxo','trajetória','barreira','colisão','contramão','interdição','esterco','ziguezague')):action('flow','Abrir correção assistida dos fluxos')
    if any(t in text for t in ('seção','secao','faixa','acostamento')):action('sections','Escolher eixo e conferir seção')
    if any(t in text for t in ('textura','material','hachura','oae')):action('materials','Conferir materiais')
    if any(t in text for t in ('ffmpeg','encoder','mp4','vídeo','render')):action('video','Conferir configuração de vídeo')
    if any(t in text for t in ('enospc','no space','espaço insuficiente','disco cheio','memory','memória')):action('maintenance','Revisar manutenção e recursos')
    action('logs','Reabrir diagnóstico dos logs')
    location=None
    if isinstance(point,(list,tuple)) and len(point)==2 and all(isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n) and abs(n)<=1e9 for n in point):location=list(point)
    return dict(method='sistema_especialista_local',kind=kind,title='Como corrigir este cálculo',causes=[t for t,_ in matches],steps=list(dict.fromkeys(s for _,steps in matches for s in steps)),actions=actions,point=location,
                message=message,limitations='Hipóteses e passos baseados em regras locais. Não é diagnóstico garantido, modelo treinado ou certificação; a localização só aparece quando informada pelo cálculo.')

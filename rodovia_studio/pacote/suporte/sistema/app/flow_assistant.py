"""Sistema especialista local: orientações rastreáveis, sem envio de dados ou LLM."""

def guidance(status,reasons,*,disabled=False,length=0.,minimum=50.,points=()):
    steps=[]
    def add(text,why,action=None):steps.append(dict(instruction=text,why=why,action=action))
    if disabled:
        title='Fluxo desligado pelo usuário'
        add('Confira por que o fluxo foi desativado antes de decidir reativá-lo.','Uma correção automática não deve desfazer sua decisão.')
    elif length<minimum:
        title='Rota abaixo do limite do projeto'
        add(f'Mantenha esta rota fora da análise e da seleção de eixos enquanto tiver menos de {minimum:g} m.','Nós internos de um eixo longo não são rotas independentes.')
        add('Se for uma ligação necessária, crie ou selecione uma rota contínua válida e confira seu sentido.','Não reduzir o limite global para liberar um fragmento isolado.')
    elif status=='adjustment':
        title='Revisar o aviso sem desligar a circulação validada'
        add('Localize o ponto e confira quais partes ou ligações foram excluídas.','Amarelo permite circulação nas trajetórias aprovadas; não significa que toda a rota esteja contínua.','locate')
        add('Se precisar conectar os trechos, tente a reconstrução validada; mantenha barreiras e sentidos.','Uma ligação recusada não deve invalidar outro itinerário seguro.')
        add('Edite manualmente a seção ou os pontos quando a correção segura não for possível.','Não reativar um desligamento manual nem atravessar um obstáculo para remover o aviso.')
        if 'corpo_fora_da_pista' in reasons:
            add('Em Camadas, confira pavimento, bordo, canteiro e barreira no ponto excluído.','Preserve os obstáculos reais e as trajetórias já aprovadas.','layers')
    elif 'corpo_fora_da_pista' in reasons:
        title='Conferir a pista no ponto do bloqueio'
        add('Localize o ponto indicado e confira onde cabem a frente, a traseira e as laterais do veículo.','O eixo pode parecer correto e o corpo ultrapassar a área disponível.','locate')
        add('Em Camadas, confira os papéis Eixo, Bordo, Pavimento, Canteiro e Barreira.','Uma linha de bordo não é barreira; não reclassifique um obstáculo real só para liberar carros.','layers')
        add('Corrija a hachura/classificação se faltar pavimento real, ou mova a faixa para dentro da pista.','Não criar atalhos sobre lacunas, canteiros ou áreas bloqueadas.')
    elif any(r in reasons for r in ('esterco_excessivo','mudanca_brusca','ziguezague','auto_intersecao','frente_traseira_degeneradas')):
        title='Corrigir a geometria do traçado'
        add('Localize o ponto indicado e examine os vértices antes e depois dele.','Nós quase coincidentes são simplificados na derivação; dobras maiores exigem ajuste.','locate')
        add('Ajuste os pontos de controle para uma curva gradual dentro do pavimento, sem cruzar o próprio eixo.','A correção precisa permitir a passagem do corpo inteiro do veículo.')
        add('Use Recuperar fluxo principal se quiser conservar apenas os intervalos que passam na validação.','Recuperação não restabelece passagem pelas partes excluídas.')
    elif status=='ok':
        title='Fluxo validado'
        add('Mantenha o fluxo; recalcule após editar geometria, sentido ou superfície.','O resultado vale para a configuração analisada.')
    else:
        title='Conferir continuidade e sentido'
        add('Confira as pontas, o nível e o sentido do eixo e das ligações.','Não unir vias em níveis diferentes nem movimentos de contramão.')
        add('Use Rota de veículos → Seleção contínua para definir explicitamente um caminho necessário.','A junção automática só resolve encontros pequenos e inequívocos.')
    if not disabled and length>=minimum and status!='ok':
        add('Calcule e atualize os fluxos; confira se o trecho ficou verde e se há veículos na prévia.','Só considerar resolvido depois de uma nova validação.','recalculate')
    return dict(method='sistema_especialista_local',title=title,steps=steps,
                limitations='Orientação baseada nos dados e regras do motor; não é um modelo de linguagem treinado nem certificação normativa.',
                point=next((p['point'] for p in points if p.get('point')),None))

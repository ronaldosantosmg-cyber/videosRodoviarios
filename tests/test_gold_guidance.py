from app.calculation_guidance import guidance


def test_convoy_message_is_not_misdiagnosed_as_pedestrians_or_ffmpeg():
    r=guidance('render','Regra de ouro: comboio sem semáforo, pedestre ou preferência de rotatória no percurso 4. Instante 0.0 s; causa lider; folga 10.604 m. Vídeo bloqueado.')
    assert r['causes']==['Conferir espaçamento e retenção da frota']
    assert any('distribuição inicial' in s for s in r['steps'])
    assert [a['id'] for a in r['actions']]==['flow','logs']


def test_motor_configuration_has_specific_guidance():
    for message in ('A regra de ouro exige o modelo de tráfego simulado para exportar veículos.','A regra de ouro exige microssimulação validada; o modo clássico não pode ser exportado com veículos.'):
        r=guidance('render',message)
        assert r['causes']==['Conferir o motor protegido de tráfego']


def test_real_pedestrian_and_encoder_errors_keep_their_guidance():
    assert 'Conferir travessia e pontos de espera' in guidance('preview','Passarela sem vão para pedestres')['causes']
    assert 'Conferir exportação do vídeo' in guidance('render','FFmpeg encoder MP4 falhou')['causes']

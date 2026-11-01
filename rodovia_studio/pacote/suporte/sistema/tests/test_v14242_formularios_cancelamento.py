"""1.42.42: Aplicar nos formulários (opt-in) e 'Cancelamento solicitado' até o servidor confirmar."""
from test_v14234_nodes_ui_video import live,gl_page


def _open(p):
    p.evaluate("""()=>{window.saves=0;window.failNext=false;window.d1=RodoviaModelDialog.open({id:'tApply',title:'Teste',html:'<input id="tin" value="a">',applyable:true,
      save:async()=>{window.saves++;await new Promise(r=>setTimeout(r,150));if(window.failNext){window.failNext=false;throw Error('Falha controlada')}}})}""")
    return p.locator('#tApply')


def test_aplicar_mantem_aberta_confirma_uma_vez_e_cancelar_nao_pergunta(gl_page):
    p=gl_page;d=_open(p);d.wait_for()
    p.locator('#tin').fill('b');b=d.get_by_role('button',name='Aplicar',exact=True)
    b.dblclick()                                    # clique duplo: executa uma só vez
    p.wait_for_timeout(500)
    assert p.evaluate('saves')==1 and d.is_visible() and 'Valores aplicados' in d.locator('[data-error]').inner_text()
    d.get_by_role('button',name='Cancelar',exact=True).click();d.wait_for(state='detached')     # nada pendente: fecha direto
    assert p.evaluate('saves')==1


def test_aplicar_com_falha_mantem_dados_e_alteracao_pendente_pergunta(gl_page):
    p=gl_page;d=_open(p);d.wait_for();p.evaluate('failNext=true');p.locator('#tin').fill('rascunho')
    d.get_by_role('button',name='Aplicar',exact=True).click();p.wait_for_timeout(500)
    assert 'Falha controlada' in d.locator('[data-error]').inner_text() and p.locator('#tin').input_value()=='rascunho'
    d.get_by_role('button',name='Cancelar',exact=True).click()
    p.get_by_role('button',name='Descartar',exact=True).click();d.wait_for(state='detached')


def test_dialogo_sem_applyable_nao_tem_aplicar(gl_page):
    p=gl_page;p.evaluate("()=>RodoviaModelDialog.open({id:'tNo',title:'X',html:'<p>x</p>',save:async()=>true})")
    d=p.locator('#tNo');d.wait_for();assert d.get_by_role('button',name='Aplicar',exact=True).count()==0
    d.get_by_role('button',name='Cancelar',exact=True).click();d.wait_for(state='detached')


def test_cancelamento_mostra_solicitado_e_so_conclui_com_o_servidor(gl_page):
    p=gl_page
    p.evaluate("""()=>{window.calls=[];window.oldApi=api;api=async(u,o)=>{calls.push(u);return {}};task='job-x';$('cancel').disabled=false}""")
    try:
        p.evaluate("$('cancel').click()");p.wait_for_timeout(200)
        assert p.evaluate('calls')==['/api/jobs/job-x/cancel'] and p.evaluate("$('cancel').disabled")
        assert 'Cancelamento solicitado' in p.locator('#message').inner_text()
        p.evaluate("()=>{$('cancel').disabled=false;$('cancel').click()}");p.wait_for_timeout(100)
        assert p.evaluate('calls')==['/api/jobs/job-x/cancel']              # segunda solicitação ignorada
    finally:
        p.evaluate("()=>{api=oldApi;task='';cancelAsked='';$('cancel').disabled=true}")


def _same(p,tol=1e-5):
    a=p.evaluate('v0');b=p.evaluate('[view.s,view.ox,view.oy]');return all(abs(x-y)<tol*max(1,abs(x)) for x,y in zip(a,b))


def test_vista_preservada_ao_salvar_aplicar_e_receber_resultados(gl_page):
    p=gl_page
    p.evaluate("()=>{view.s*=1.7;view.ox+=37;view.oy-=21;draw();window.v0=[view.s,view.ox,view.oy]}")
    p.evaluate("async()=>{await save()}");assert _same(p)
    p.evaluate("async()=>{await load(pid,{resultsOnly:true})}");assert _same(p)
    d=_open(p);d.wait_for();d.get_by_role('button',name='Aplicar',exact=True).click();p.wait_for_timeout(400);assert _same(p)
    d.get_by_role('button',name='Cancelar',exact=True).click();d.wait_for(state='detached');assert _same(p)


def _painel(p):
    return p.evaluate("()=>[document.body.classList.contains('pnAberto'),document.body.classList.contains('rsPanelOpen'),document.querySelectorAll('dialog[open]').length,document.body.className]")


def test_resultado_nao_abre_nem_fecha_paineis(gl_page):
    p=gl_page;antes=_painel(p)
    p.evaluate("async()=>{await load(pid,{resultsOnly:true,syncConfig:true})}");assert _painel(p)==antes
    p.evaluate("()=>window.dispatchEvent(new CustomEvent('rodovia:job',{detail:{id:'zz',kind:'analyze',state:'done',project:pid,progress:1,message:'ok',created:'2026-01-01 00:00:00'}}))")
    p.wait_for_timeout(200);assert _painel(p)==antes


def test_botao_desabilitado_nao_usa_cursor_de_espera(gl_page):
    p=gl_page
    c=p.evaluate("()=>{const b=document.createElement('button');b.disabled=true;b.textContent='x';document.body.append(b);const v=getComputedStyle(b).cursor;b.remove();return v}")
    assert c=='not-allowed'
    c=p.evaluate("()=>{const d=document.createElement('div');d.setAttribute('aria-busy','true');const b=document.createElement('button');b.disabled=true;d.append(b);document.body.append(d);const v=getComputedStyle(b).cursor;d.remove();return v}")
    assert c=='progress'

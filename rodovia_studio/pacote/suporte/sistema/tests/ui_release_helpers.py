"""Acesso por aba/expansão reais; mantém os comandos e handlers existentes."""
def ribbon_control(page,identity,kind='tool'):
    if kind=='tool' and identity=='pan':return page.locator('#rsQuickNavigation [data-rs-tool=pan]')
    tab='Cena' if identity in {'IMAGEMCONTORNOS','oae','gantry'} else 'Editar' if identity in {'MOVER','GIRAR','COPIAR','move','insertcontrol','DIST','CALCULARFLUXOS','inspect','chain','align'} else 'Tráfego'
    page.get_by_role('tab',name=tab,exact=True).click()
    panel=page.locator('[data-activity="'+tab+'"]')
    panel.locator('details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')
    return panel.locator('[data-rs-'+kind+'="'+identity+'"]').first


def show_calculation_guide(page):
    page.get_by_role('tab',name='Projeto',exact=True).click()
    page.locator('[data-activity="Projeto"] details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')


def presentation_options(page):
    page.get_by_role('tab',name='Projeto',exact=True).click()
    page.locator('[data-activity="Projeto"] details').evaluate_all('(items)=>items.forEach(d=>d.open=true)')

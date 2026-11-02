/* 2.38 — Glossário ÚNICO do sentido do fluxo. Todo rótulo, opção e texto de sentido vem daqui (mesmos textos de direction_policy.ROTULO no servidor).
   Nenhuma tela escreve “Crescente/Decrescente/Automático/Sem veículos” por conta própria. */
window.RodoviaGlossario=Object.freeze({
 sentido:Object.freeze({forward:'Crescente (km)',reverse:'Decrescente (km)',off:'Sem veículos',auto:'Automático'}),
 faixa:Object.freeze({f:'sentido do desenho',r:'sentido oposto'}),
 opcoes(){const s=this.sentido;return [['auto',s.auto],['forward',s.forward],['reverse',s.reverse],['off',s.off]]},
 rotulo(v){return this.sentido[v]||String(v)},
 /* sentido PRÓPRIO da rota cadastrada: relativo à ordem do desenho dela (nós de entrada/saída). Não confundir com Crescente (km), que é do eixo. */
 rota:Object.freeze({auto:'Automático (pelos nós e pelo eixo)',crescente:'Sentido do desenho',decrescente:'Sentido oposto ao desenho'})
});

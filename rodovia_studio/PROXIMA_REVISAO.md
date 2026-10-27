# Próxima revisão após a 1.42.34

Solicitações do usuário em 27/10/2026, posteriores ao escopo da 1.42.34:

1. Impedir a formação de fluxos sem eixo-base cadastrado. Exigir origem identificável e associação explícita; não basta encontrar uma linha cujo nome parece Eixo. Integrar com Escolher eixo/Configurar faixas e com os nós, sem cadastro paralelo independente ou reativação de desligamentos. Tratar projetos antigos com orientação clara e preservação das fontes. A regra deve valer também para o modo clássico, sem uma exceção silenciosa.
2. Investigar “sujeira de layer” ao abrir projeto novo, ausente no CAD. Foi perguntado se aparece na lista, no desenho ou em ambos e qual nome, aguardando resposta. Não presumir a causa. Conferir troca de projeto, respostas atrasadas, catálogo da fonte, camadas declaradas vazias, sobreposições e caches técnicos. Limpar somente dados derivados comprovadamente obsoletos; preservar fontes e elementos reais cadastrados. Identificar a origem do que aparece (CAD, KMZ, imagem/contexto, gerado, edição manual).

Critérios: projeto sem eixo cadastrado não produz itinerários e orienta o cadastro; eixo associado produz fluxo; remoção/desligamento não cria nova fonte; troca A→B→projeto novo não deixa objetos de A ou B; resultado atrasado não se aplica ao contexto novo; lista de camadas corresponde à fonte/proveniência; testes dirigidos funcionais e visuais antes do ZIP.

Não incluído no pacote 1.42.34. Main permanece protegida; continuar somente na branch de desenvolvimento.

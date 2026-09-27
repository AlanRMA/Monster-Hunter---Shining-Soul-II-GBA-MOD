# Próximas etapas — Mod Monster Hunter em Shining Soul II

Atualizado em: 26/09/2026.

Registro principal: [Modding-Shining-Soul-II.md](./Modding-Shining-Soul-II.md).

Ordem de trabalho: **entender o mapa/arena primeiro; investigar itens em seguida**.

## 1. Preservar o contexto

- [ ] Guardar um save state separado dentro da arena, sem sobrescrever o único estado disponível.
- [ ] Identificar nome do boss e da fase.
- [ ] Registrar hash/revisão da ROM e nome dos arquivos de save usados.
- [ ] Conferir watchpoints com `listw`; último registro: #5 mudança e #6 leitura de `0200B480`.
- [ ] Atualizar o registro principal a cada confirmação, preservando a distinção entre hipótese e teste concluído.

## 2. Mapa e arena — prioridade atual

### Descobertas concluídas

- [x] Identificar BG0 como interface e BG1–BG3 como cenário.
- [x] Registrar os mapas gráficos em VRAM: `0600E000`, `0600E800`, `0600F000`, `0600F800`.
- [x] Observar atualização do quadro de 256 × 256 conforme a câmera se desloca.
- [x] Rastrear um trecho: `0200B480 → 0202C460 → 0600F800`.
- [x] Identificar origem do BG3 em `0200B440`.
- [x] Identificar estruturas de camadas: `03003290 + índice × 24`.
- [x] Confirmar passo/largura do BG3 de 60 tiles, equivalente a 480 pixels.
- [x] Ler candidato a altura: 40 tiles; interpretação ainda pendente.

### Próximo passo imediato

- [x] Executar a leitura abaixo com o debugger parado e registrar os quatro blocos:

```text
x/4 $03003290 24
```

### Entender e extrair os gráficos

- [x] Identificar os ponteiros de origem de BG1 e BG2 e comparar seus campos com BG3: BG1 `0200D9C0`, BG2 `0200C700`, BG3 `0200B440`; todos com campos 60 e 40. Intervalos de 4800 bytes sustentam mapas de 60 × 40 entradas de 2 bytes.
- [x] Continuar a leitura com `disassemble/t $0800918C 64`: revelou campos de controle em `0300331C` e `03003320`, ainda sem confirmar altura.
- [x] Ler `r/2 $0300331C` e `r/2 $03003320`: valores 1 e 7; semântica ainda não confirmada.
- [x] Retomar código em `disassemble/t $08009214 64`: campos +0 e +2 participam dos cálculos de deslocamento em tiles; não confirmou altura.
- [ ] Examinar o final da função com `disassemble/t $0800946A 40` para confirmar referências de câmera e atualização do deslocamento.
- [ ] Confirmar no código o significado do campo +18 antes de assumir altura de 40 tiles.
- [ ] Validar extensão dos dados de cada camada e se representam a sala inteira.
- [ ] Identificar formato das entradas gráficas, profundidade de cor, tiles e paletas usados.
- [ ] Extrair cópias dos dados de origem, tiles e paletas sem alterar o estado do jogo.
- [ ] Reconstruir a camada completa fora do quadro de rolagem e comparar com o jogo.
- [ ] Combinar BG1–BG3 na ordem apropriada para obter uma referência visual da arena.

### Encontrar origem e comportamento da arena

- [ ] Rastrear quem preenche a estrutura e o bloco `0200B440`; localizar origem na ROM e eventual descompressão.
- [ ] Se o carregamento só ocorrer na entrada, obter um estado anterior ao boss ou investigar o carregador pelo código; não depender de sair e reentrar na sala atual.
- [ ] Identificar ID da sala, ponto de entrada, câmera e limites.
- [x] Comparar campos candidatos na arena e na entrada: `0300331C/03003320` = `1/7` e `1/0`, respectivamente.
- [ ] Repetir as leituras na próxima sala, no castelo e em outra fase; confirmar nome da fase da entrada antes de fechar a interpretação fase/sala.
- [x] Ler `03003320` na área seguinte à entrada: mudou de 0 para 1.
- [ ] Reler `0300331C` nessa área seguinte; o valor ainda não foi informado.
- [x] Observar próxima sala: `03003320 = 2`, completando sequência natural 0 → 1 → 2.
- [x] Registrar tentativa de escrever 7 em `03003320`: não trocou para a arena; persistência da escrita não verificada.
- [x] Capturar atualização natural com `watch/c $03003320`: watchpoint #7 registrou 2 → 3, Thumb, r15 `08009524`.
- [x] Analisar a escrita: função Thumb `080094CC`; primeiro argumento gravado em `0300331C` por `0800951C`, segundo em `03003320` por `08009520`; também prepara estrutura `03003550`.
- [x] Seguir `0800962C`: tabela calculada por `0848553C + contexto*0x74 + 0x10 + sala*4`; entrada passa por `08006E34`; cálculo de bloco usa cabeçalho de 16 bytes + produto dos dois campos iniciais *6.
- [x] Ler entradas 0–7: códigos `00020006` a `0002000D`; arena = `0002000D` em `084855DC`.
- [x] Inspecionar `08006E34`: chama `08006A5C` com código em r0 e base `0856F954` em r1.
- [ ] Ler `disassemble/t $08006A5C 64` para descobrir resolução do recurso da arena; significado dos campos alto/baixo ainda pendente.
- [ ] Antes de ler ponteiros globais como dados da sala nova, deixar o carregamento concluir ou parar após as atribuições; o watchpoint do índice ocorreu antes delas.
- [ ] Verificar uso do ponteiro `0800A535` guardado em `0300355C`; possível função Thumb de processamento em `0800A534`, ainda sem confirmar papel.
- [ ] Só investigar `0854654C` e `08546564` como descritores se seu uso aparecer no código; podem ser valores residuais nos registradores.
- [ ] Localizar colisão e diferenciar paredes visuais de barreiras reais.
- [ ] Localizar posição de aparecimento do boss e condições de início/fim da luta.
- [ ] Investigar abertura de saídas e recompensas após a vitória, preservando o estado anterior.
- [ ] Fazer uma alteração visual pequena e reversível; testar rolagem e recarregamento antes de ampliar.
- [ ] Planejar reutilização da sala como arena e validar um patch em cópia da ROM.

## 3. Itens — depois do mapa

- [ ] Registrar um inventário de referência e guardar save state.
- [ ] Localizar quantidade de um item por busca antes/depois de usar ou obter uma unidade.
- [ ] Descobrir início, tamanho e espaçamento dos slots de inventário.
- [ ] Identificar ID do item, quantidade e campos adicionais sem assumir que todo valor próximo pertence ao mesmo item.
- [ ] Trocar um item entre slots e comparar a estrutura.
- [ ] Relacionar IDs a nomes, ícones, categoria e efeitos.
- [ ] Separar dados do item no inventário das definições de item na ROM.
- [ ] Investigar armas, armaduras, requisitos e bônus; documentar campos realmente presentes.
- [ ] Localizar drops do boss e recompensas para o ciclo de caça do mod.
- [ ] Testar persistência ao salvar/carregar e comportamento com inventário cheio.

## 4. Validações complementares — após as prioridades atuais

- [ ] Confirmar individualmente Sword, Spear, Armor Up, Efficacy, Counter e Tactics.
- [ ] Determinar tamanho real dos campos de habilidade e significado dos bytes restantes nos slots de 4 bytes.
- [ ] Testar o mapa de posições de habilidade em outra classe.
- [ ] Verificar estabilidade dos endereços de status entre personagens e reinicializações.
- [ ] Confirmar tamanho completo e persistência da XP.
- [ ] Confirmar origem do HP atual; os dois endereços encontrados continuam candidatos.

## Critério de conclusão de cada descoberta

Registrar endereço, tamanho, significado, teste reproduzível, efeito no jogo e limitações. Uma leitura coincidente ou uma mudança visual isolada não confirma persistência, colisão ou efeito mecânico.

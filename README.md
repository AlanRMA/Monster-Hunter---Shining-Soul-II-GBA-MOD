# Shining Soul II — Registro de modding

Atualizado em: 27/09/2026.

Objetivo central: transformar os modos Single Player e Multiplayer em um mod de arenas inspirado em Monster Hunter, substituindo o fluxo da campanha original. O MVP implementa primeiro a arena em Single Player; Multiplayer será adaptado depois sobre a mesma proposta.

## Ponto de parada — 27/09/2026

- A ROM de desenvolvimento conserva o novo título `Monster Hunter Souls Arena`, o menu original funcional e o redirecionamento após a criação/carregamento do personagem para o contexto `1`, sala `7` (arena do chefe do Forte dos Goblins).
- O fluxo de criação preserva o nome e a cor escolhidos para Eric. A restrição da seleção apenas a Eric ainda é uma tarefa pendente.
- Solução temporária aceita para a primeira cutscene: o livro começa a aparecer e um `Start` automático o pula. O jogador não precisa apertar o botão. O livro ainda pode ser visto brevemente; por decisão de projeto, mantemos esse comportamento por enquanto.
- O patch foi validado na ROM isolada `Shining Soul II - Book Ready Skip Test.gba` e aplicado à ROM de desenvolvimento por `tools/apply_book_ready_skip.py`. O backup anterior é `Shining Soul II - Monster Hunter Mod Dev.before-book-ready-skip.gba`. Os arquivos `.gba` e `.sav` ficam locais e não entram no Git.
- SHA-256 da base anterior: `58ba15896e9decf7575fd70c70a14279a349884a5d4542ffd2a27ffc79db5025`. SHA-256 da ROM de desenvolvimento com o skip: `10b66522c3ba89f1830b437c3e8ef5b8bedae12fbe50623ed6a0d773caa2e8e3`.
- A ponte `bridge.lua` usa `json.lua` na mesma pasta e atende o MCP do mGBA em `127.0.0.1:8765`. No mGBA 0.10.5 desta máquina, leitura/escrita de memória, botões, screenshots e save states funcionam; `pause`, `unpause` e `frameAdvance` não estão disponíveis.

### O que o skip confirmou

- A rotina de confirmação do personagem chega à cutscene com os endereços `0300296C = 08002CF9` e `030029B8 = 030065A0` quando a cena está inicializada. O patch combina os dois marcadores no manipulador de entrada em `0800077C` e injeta `Start` somente nessa situação.
- Usar só o callback `03000010 = 08006225` ou o estado `0300135C` atingia também a seleção do personagem. Simular `Start` antes de a cena estar pronta causou tela branca ou livro corrompido. Alterar `0300001C` como contador também corrompeu a imagem.
- Pular diretamente da preparação inicial para a saída da cutscene voltou ao título. Um salto posterior, antes da espera em `08002CF4`, alcançou o diálogo do chefe sem mostrar o livro, mas deixou os gráficos da arena corrompidos. Portanto, não usar esses saltos na ROM de desenvolvimento: a espera original executa uma preparação necessária.
- Nos checkpoints, o livro ficou visível aproximadamente entre os quadros `2795` e `2925`; o `Start` automático já era enviado, mas o jogo só concluía o skip após sua própria animação. Essa é a razão de ainda aparecer brevemente.

### Próximos passos

1. Em uma partida nova e em um save existente, confirmar o caminho `Single Player -> Eric (nome/cor) -> livro breve -> arena 1/7`, com câmera, colisão, entidades, sprite do chefe e save corretos. Não tratar a simples chegada ao diálogo como validação completa do combate.
2. Restringir a escolha de classe ao Eric sem perder edição de nome e cores.
3. Identificar e entregar as três armas iniciais, três ervas de cura e a erva no atalho `R`.
4. Remover o diálogo do chefe quando o fluxo de combate estiver estável. Investigar depois um bypass real da cutscene que preserve a preparação gráfica; o skip artificial atual é o ponto de retorno seguro.
5. Substituir sprite, retrato e animações do chefe por um monstro do mod. Manter `STR = 500` e restaurar HP para `45` durante testes; balancear os atributos de Eric por último.

## MVP — fluxo central

O MVP deve funcionar como uma experiência curta e completa:

```text
Menu -> SINGLE PLAYER MODE -> Eric preparado -> boss da fase 1 -> combate
```

Critérios do MVP:

- Manter `SINGLE PLAYER MODE` e `MULTIPLAYER MODE` como os dois modos principais do mod, sem preservar o acesso normal à campanha original.
- No primeiro MVP, ao selecionar Single Player, permitir escolher/criar um arquivo de save e iniciar o fluxo de arena com Eric.
- Limitar a seleção de personagem ao Eric, inicialmente sem disponibilizar as outras classes.
- Preservar a seleção de cores do Eric e permitir que o jogador altere o nome.
- Colocar as três armas iniciais no inventário de Eric. Os itens e IDs exatos ainda precisam ser confirmados antes do patch definitivo.
- Colocar três ervas de cura no inventário e configurar a erva no atalho do botão R.
- Ir diretamente para a tela/sala do boss da fase 1, sem percorrer a campanha.
- Preferencialmente pular o texto introdutório do chefe para chegar imediatamente ao combate. Isso é desejável, mas não deve bloquear a primeira versão jogável se exigir uma alteração separada.
- Solução temporária atual: injetar `Start` pela rotina de entrada somente quando a cena do livro atinge os dois marcadores confirmados. Isso funciona, mas o livro aparece por um instante antes do skip.
- Experimento isolado `Intro Skip Test`: iniciar a máquina da abertura diretamente no estado `7` não pula para o fim; esse estado abre o fluxo de dados suspensos (`Continue from suspend data` / `Restart dungeon`). Não aplicar esse byte à ROM principal.
- Experimento isolado `Ready Intro Skip Test`: combinar a rotina `08006225` com o valor observado em `0300135C` também dispara durante a seleção do personagem e impede selecionar Eric. Esses marcadores, usados sozinhos, não identificam exclusivamente o livro.
- Definir os atributos e demais números de Eric somente no final, após o fluxo estar estável, para ajustar a dificuldade por testes de combate.

Ordem de implementação recomendada:

1. Confirmar e reproduzir com segurança o carregamento da sala do boss da fase 1.
2. Preservar seleção/criação de save e limitar a criação de personagem ao Eric, mantendo nome e cores.
3. Redirecionar a confirmação final do personagem para o novo fluxo de arena.
4. Inicializar Eric, as três armas, as três ervas e o atalho R.
5. Remover ou contornar a introdução da campanha e o texto do chefe.
6. Balancear os atributos de Eric e a dificuldade.

Destino confirmado para o MVP: contexto/fase interna `1`, sala `7`, correspondente à arena do boss do Forte dos Goblins. O fluxo final não deve carregar a entrada nem percorrer as salas normais da fase 1. Após a confirmação final de Eric (save existente ou criação com nome/cor), o jogo deve chamar diretamente o carregamento de `(1, 7)`.

Limitação confirmada do salto durante gameplay: forçar o carregador e o descritor de `sala 0` para `sala 7` carrega corretamente mapa, câmera e colisão da arena, mas mantém entidades/sprites da sala anterior; apareceram baús e um inimigo imóvel no lugar do boss. Portanto o patch definitivo não deve reutilizar uma transição de porta com entidades já ativas. O redirecionamento precisa ocorrer antes da criação das entidades, no fluxo de confirmação/carregamento do personagem, ou chamar explicitamente a inicialização completa da sala.

Fora do MVP inicial: implementação funcional do Multiplayer de arena, múltiplos bosses, progressão longa, crafting, seleção ampla de equipamentos e balanceamento definitivo de classes.

Direção visual posterior ao MVP: substituir o chefe provisório por um monstro inspirado em Monster Hunter. A troca deve abranger o sprite de combate, o retrato/profile picture usado no diálogo e o spritesheet completo de animações, preservando primeiro a lógica funcional do chefe original.

## Tela de título — arte definida

- Background oficial escolhido: arte `Monster Hunter — Souls Arena`, com ruínas verdes, o caçador, dois monstros e o pequeno companheiro.
- Prévia reduzida em resolução GBA: `title-preview.png`. A imagem `Theme.jpeg` exibida no topo do README é uma arte de referência separada.
- A arte deve substituir o background original da tela de título, preservando as opções `SINGLE PLAYER MODE` e `MULTIPLAYER MODE` do jogo.
- Foi preparada uma versão simplificada em pixel art e duas prévias em resolução nativa do GBA (`240x160`), com 256 e 64 cores. A versão de 64 cores manteve boa legibilidade e é a candidata inicial para conversão.
- Antes de aplicar o patch, ainda é necessário extrair a tela de título original para confirmar sua organização em camadas, tiles, tilemap e paletas. A integração definitiva deve reservar contraste suficiente para o menu existente.
- Os arquivos de trabalho estão em `outputs/title-background-source.png`, `outputs/title-background-simplified-master.png`, `outputs/title-background-gba-256-colors.png` e `outputs/title-background-gba-64-colors.png` no workspace desta exploração.
- Estrutura confirmada no visualizador de mapas do mGBA: imagem no `Background 1`, tilemap em `0600E800`, tiles em `06000000`, mapa lógico `256x256` e área visível `240x160`.
- Foi gerada também `outputs/title-background-original-palette-4bpp.png`, usando somente a paleta original e limitando cada tile de `8x8` a um único banco de 16 cores. Esta é a primeira prévia compatível com a estrutura gráfica observada; ainda falta convertê-la em tiles/tilemap e localizar o pacote comprimido correspondente na ROM.
- Patch da tela de título aplicado e validado na ROM de desenvolvimento. Tiles 4bpp: offset de arquivo `005E4B9C`, 19.232 bytes usados de uma área observada de 20.480 bytes. Tilemap LZ77: offset `00589784`, 1.593 bytes usados antes do próximo recurso em `00589F50`.
- SHA-256 da ROM de desenvolvimento após o patch do título: `f6968d2adc9020b864b54c9ad8b1adf21296b1b64c277b4529da701bc61d5b6b`.
- Backup limpo anterior ao patch: `Shining Soul II - Monster Hunter Mod Dev.before-title.gba`, com o mesmo SHA-256 da ROM original.
- Validação no mGBA: background, logotipo, `PRESS START`, cursor e as opções `SINGLE PLAYER MODE` / `MULTIPLAYER MODE` funcionam. O menu permanece legível, embora sobreponha o caçador central; reposicionamento fica como acabamento opcional.
- A arte nova também foi aplicada às ROMs experimentais `Force Room 7 Test` e `Force Room 7 Full Test`, preservando os patches de código específicos de cada uma.

## Ambiente e critérios de confirmação

- Jogo: Shining Soul II (USA).
- Emulador observado: mGBA 0.10.5, macOS.
- ROM original: `Shining Soul II (USA).gba`; SHA-256 `b31c19d2d25683a0941d5d501912b5f21d4590cd7071fa01882e62aa5227a7c9`.
- ROM de desenvolvimento: `Shining Soul II - Monster Hunter Mod Dev.gba`; criada como cópia byte a byte com o mesmo hash inicial.
- Regra de trabalho: não modificar a ROM original. Todo patch permanente deve ser aplicado primeiro à ROM de desenvolvimento, mantendo backup ou script reproduzível.
- Os endereços abaixo foram observados nesta sessão. Sua estabilidade após reiniciar, carregar outro personagem ou trocar de classe ainda precisa ser testada.
- “Confirmado” significa observado nos testes ou diretamente demonstrado pelo código lido. Hipóteses estão identificadas.
- Endereços de RAM e VRAM não são offsets de arquivo da ROM. Alterações temporárias não constituem um patch permanente.
- Durante exploração e testes de passagem, manter `STR = 500` em `02003C2C` para reduzir o tempo de combate. Esse valor não pertence ao balanceamento final.

## Status — base de trabalho: 500

**STR** - 2 bytes - 02003C2C

**DEX** - 2 bytes - 02003C2E

**INT** - 2 bytes - 02003C30

**VIT** - 2 bytes - 02003C32

Os quatro atributos foram exibidos em 500 após as alterações. HP e SP máximos apareceram como 999.

Distinção importante: 500 é o limite normal relatado para STR, DEX e INT. Para VIT, o limite normal relatado é 333; a edição direta permitiu exibir 500. Isso não confirma benefício adicional acima de 333 nem o limite interno do campo.

Fonte sobre limites normais: [guia de Shining Soul II](https://gamefaqs.gamespot.com/gba/589485-shining-soul-ii/faqs/30780).

Exemplo de escrita, seguido de `c` em uma entrada separada:

```text
w/2 $02003C2C 500
```

### Cópias temporárias dos atributos

- `020327C0` e `02032800` acompanharam STR = 19, mas as alterações foram sobrescritas.
- A rotina próxima de `0801B830` copiou o valor original para uma área temporária.
- `02003C2C` foi identificado como origem da STR nessa cópia; alterar essa origem resolveu o teste.

## Eric Skills — Master = nível 7

Base de endereços solicitada pelo usuário:

**Sword** - 2 bytes* - 02003C50

**Axe** - 2 bytes* - 02003C54

**Spear** - 2 bytes* - 02003C58

**Shield** - 2 bytes* - 02003C5C

**Armor Up** - 2 bytes* - 02003C60

**Efficacy** - 2 bytes* - 02003C64

**Counter** - 2 bytes* - 02003C68

**Tactics** - 2 bytes* - 02003C6C

\* “2 bytes” preserva a base solicitada, mas não é um tamanho de campo confirmado. Shield respondeu inicialmente a uma escrita de 2 bytes; Axe foi confirmado em níveis 1 e 7 usando escrita de 1 byte. O espaçamento entre os endereços é 4 bytes, o que também não prova que o campo de nível ocupe 4 bytes. Para os próximos testes, usar `w/1` no byte identificado até entender os bytes vizinhos.

- Confirmados individualmente: Axe e Shield; Shield exibiu Lv 7 / MASTER.
- Sword, Spear, Armor Up, Efficacy, Counter e Tactics seguem o padrão observado, mas ainda não tiveram confirmação individual explícita no registro.
- A hipótese anterior de espaçamento de 2 bytes foi descartada após comportamento visual incorreto. Não usar aquela tabela antiga.
- Outra classe pode usar as mesmas posições para habilidades diferentes, ou mudar a base da estrutura. Ainda não testado.

Comandos de teste para Master; executar um por vez e conferir o menu antes de salvar:

```text
w/1 $02003C50 7
w/1 $02003C54 7
w/1 $02003C58 7
w/1 $02003C5C 7
w/1 $02003C60 7
w/1 $02003C64 7
w/1 $02003C68 7
w/1 $02003C6C 7
```

## Experiência e HP — dados secundários

- XP: `02003C38` e `03003E50` acompanharam a mudança de 264 para 312.
- Foi proposto `w/2 $02003C38 1000`; capturas posteriores mostram nível 4 e EXP 1020, mas não houve registro controlado que confirme sozinho a origem principal e a persistência.
- O tamanho total do campo de XP ainda é desconhecido. Uma busca de 2 bytes pode encontrar só a parte baixa de um campo maior.
- HP atual: `0200B260` e `03003ED0` foram confirmados como espelhos ativos no teste da sala 6. Escrever `45` nos dois campos atualizou a interface para `45/45`. Durante a exploração, restaurar ambos antes de cada transição importante; a origem principal entre os dois ainda pode depender da etapa do frame.

## Arena do boss — camadas gráficas

Nome do boss/fase: ainda não registrado. Preservar um save state da sala, pois o jogador não consegue simplesmente sair e entrar novamente.

| Camada | Map base em VRAM | Conteúdo observado | Prioridade |
|---|---|---|---:|
| BG0 | `0600E000` | Interface de HP, SP e Soul | 0 |
| BG1 | `0600E800` | Partes de paredes e vegetação | 1 |
| BG2 | `0600F000` | Outras partes de paredes e vegetação | 2 |
| BG3 | `0600F800` | Chão e base do cenário | 3 |

- Todas apresentaram Tile base `06000000` e tamanho gráfico carregado de 256 × 256 pixels.
- BG0 tinha Offset 0, 0. BG1–BG3 tinham inicialmente Offset 65, 108.
- BG3 depois mostrou 240, 33 e 89, 156, com alterações nas peças exibidas.
- O jogo atualiza o conteúdo do quadro gráfico conforme a câmera se move. Os 256 × 256 não representam necessariamente a sala inteira.
- As camadas sugerem composição de profundidade; a relação exata com sprites e colisão ainda não foi mapeada.

### Caminho de dados confirmado para um trecho do BG3

```text
0200B440 — base de origem da camada na RAM
    └─ 0200B480 — trecho observado, valor 41BB
           ↓ cópia de entradas de 2 bytes
0202C460 — área intermediária do BG3 na RAM
           ↓ cópia para VRAM
0600F800 — mapa gráfico do BG3 na memória de vídeo
```

- Os primeiros 32 bytes de `0202C460` e `0600F800` coincidiram exatamente no teste.
- Um watchpoint mostrou `0202C460` passando de `72CC` para `41BB`.
- A leitura veio de `0200B480`; depois da leitura, `r12` avançou para `0200B482`.
- `0200B480` não mudou ao percorrer a sala, mas foi lido. Isso é compatível com dados de origem estáveis; não prova que essa região seja toda a sala ou que nunca seja regravada.
- `41BB`, `72CC` etc. são valores observados nas entradas gráficas; não foram identificados como IDs de sala.

### Estruturas das camadas

A função em `08009130` calcula a estrutura como:

```text
03003290 + índice × 24 bytes
```

| Camada/índice | Estrutura | Campo +12: ponteiro de origem |
|---|---|---|
| BG0 / 0 | `03003290` | `0300329C` |
| BG1 / 1 | `030032A8` | `030032B4` |
| BG2 / 2 | `030032C0` | `030032CC` |
| BG3 / 3 | `030032D8` | `030032E4` |

Campos identificados ou candidatos:

| Offset | Tamanho lido | Significado | Evidência |
|---|---|---|---|
| +8 | 2 bytes | Deslocamento/coordenada usada no cálculo | Uso observado; semântica exata pendente |
| +10 | 2 bytes | Segundo deslocamento/coordenada | Uso observado; semântica exata pendente |
| +12 | 4 bytes | Ponteiro para origem dos dados gráficos | Confirmado pelo código e leitura |
| +16 | 2 bytes | Passo entre linhas, em entradas/tiles | Confirmado no cálculo de origem |
| +18 | 2 bytes | Provável altura em tiles | Hipótese; falta observar uso |
| +20 | 2 bytes | Índice na tabela de destinos | Confirmado |
| +22 | 2 bytes | Controle de uso das coordenadas | Testado contra zero no código; função exata pendente |

Valores lidos do BG3:

```text
r/4 $030032E4 → 0200B440
r/2 $030032E8 → 003C = 60
r/2 $030032EA → 0028 = 40
r/2 $030032EC → 0003
```

A rotina trabalha com unidades de 8 pixels. A largura gráfica é de 60 tiles = 480 pixels. A hipótese de altura é 40 tiles = 320 pixels. Ainda não confirmar “arena 480 × 320” sem validar o uso da altura e a extensão real dos dados; a área caminhável é outra informação.

Tabela de destinos em `03003580`:

```text
Índice 0: 00000000
Índice 1: 0202B440
Índice 2: 0202BC50
Índice 3: 0202C460
```

A entrada zero nesta tabela não significa ausência de BG0: a interface foi observada no visualizador e pode seguir outro caminho de atualização.

### Rotinas importantes

| Endereço | Observação |
|---|---|
| `08009130` | Seleciona estrutura de 24 bytes a partir de `03003290` |
| `080093C0` | Chama `08009068` no caminho capturado |
| `08009068` | Seleciona origem e destino; calcula trecho de linha com coordenadas em tiles |
| `08009084` | Carrega ponteiro de origem de `[r6 + 12]` |
| `080090CC` | Lê passo/largura de `[r6 + 16]` |
| `08009116` | Chama a função de cópia `080B7FE8` |
| `080B7FE8` | Executa `swi #11`; depois retorna com `bx lr` |
| `00000294` | Rotina de cópia: lê halfword e avança origem em 2 bytes |
| `00000298` | Escreve halfword e avança destino em 2 bytes |

O cálculo usa coordenadas divididas por 8, máscara de 255 pixels e divisão da linha em partes que completam 32 posições. Isso sustenta a interpretação de um quadro gráfico reutilizado durante a rolagem.

## Procedimentos no debugger

- Executar cada comando separadamente; colar `w/…` e `c` juntos produziu erros de interpretação.
- `w/1`: escreve 1 byte; `w/2`: escreve 2 bytes. Escolher tamanho pela evidência, não apenas pelo resultado da busca.
- `r/2`, `r/4`: leitura de um valor.
- `x/1`, `x/2`, `x/4`: leitura de várias unidades; o último argumento é a quantidade de unidades, não de bytes.
- `watch/w`: pausa em escrita; `watch/c`: pausa em mudança; `watch/r`: pausa em leitura.
- `delete N`: remove o watchpoint/breakpoint de número N. Os números variam ao criar novos.
- `disassemble/t`: usar explicitamente para os trechos Thumb do jogo; as rotinas de cópia capturadas em endereços baixos estavam em ARM.
- Uma pausa de watchpoint não significa travamento do jogo.
- Não transformar as hipóteses em cheats permanentes antes de confirmar campo, efeito e persistência.

Último estado conhecido: watchpoint #5 em mudança de `0200B480` e #6 em leitura de `0200B480`; #6 foi o último a disparar. Confirmar a lista com `listw` antes de remover ou adicionar outros.

## Leitura das quatro estruturas — resultado

```text
x/4 $03003290 24
```

Leitura recebida:

```text
03003290: 00000000 00000000 00000000 00000000
030032A0: 00000000 00000000 000F0007 00000000
030032B0: 00000000 0200D9C0 0028003C 00010001
030032C0: 000F0007 00000000 00000000 0200C700
030032D0: 0028003C 00010002 000F0007 00000000
030032E0: 00000000 0200B440 0028003C 00010003
```

Decodificação em little-endian, respeitando estruturas de 24 bytes (não as linhas de 16 bytes do dump):

| Camada | Origem confirmada | +16: largura | +18: altura candidata | +20: índice | +22: controle |
|---|---|---:|---:|---:|---:|
| BG0 | `00000000` | 0 | 0 | 0 | 0 |
| BG1 | `0200D9C0` | 60 | 40 | 1 | 1 |
| BG2 | `0200C700` | 60 | 40 | 2 | 1 |
| BG3 | `0200B440` | 60 | 40 | 3 | 1 |

BG1–BG3 também têm +0 = 7, +2 = 15 e +4 a +10 zerados. Os significados de +0 e +2 continuam desconhecidos; não interpretar como coordenadas sem evidência.

As diferenças `0200C700 - 0200B440` e `0200D9C0 - 0200C700` são ambas `0x12C0` = 4800 bytes, exatamente `60 × 40 × 2`. Isso reforça fortemente a hipótese de três mapas de 60 × 40 entradas de 2 bytes (480 × 320 pixels). O limite final do BG1 e o uso de +18 como altura ainda precisam ser confirmados; a área caminhável não foi identificada.

Faixas previstas, com limite final exclusivo:

- BG3: `[0200B440, 0200C700)`.
- BG2: `[0200C700, 0200D9C0)`.
- BG1: `[0200D9C0, 0200EC80)` — final calculado, não verificado.

BG0 está zerado nesta tabela, embora a interface exista em VRAM; não concluir que a interface esteja desativada.

### Continuação em 0800918C — campos de controle

Leitura realizada. O trecho ainda não mostrou o uso de +18 como altura.

- `0800918C–08009192`: se o ponteiro de origem `[r6 + 12]` for zero, desvia para `080094AC`.
- `r4` mantém a base `03003290` nesse trecho. Em `08009194–080091AA`, lê um campo de 2 bytes em `0300331C` (base + `0x8C`) e compara com 5, 8 e 10.
- Para alguns desses casos, lê outro campo de 2 bytes em `03003320` (base + `0x90`). No caso 5, compara indiretamente com 13; no caso 8, trata especialmente a camada 3 e usa valores de 2 a 14 para selecionar um destino numa tabela.
- Esses campos controlam comportamentos específicos de atualização gráfica. São candidatos para investigação de contexto de fase/sala/efeito, mas sua semântica ainda é desconhecida. Não são IDs de sala confirmados.
- `080091DC` contém o literal `080091E0`; `080091E0–08009213` é a tabela de 13 endereços indicada pelo código. O disassembler apresentou os dados como falsas instruções. Retomar a leitura de código em `08009214`.
- Novas capturas mostram BG1 e BG3 com Offset 56, 124, mantendo map bases e tile base; sustentam a rolagem conjunta já observada.

Leituras recebidas: `0300331C = 1` e `03003320 = 7`. A combinação identifica o contexto observado, mas ainda não comprova IDs de fase/sala. Como o primeiro campo é 1, o fluxo segue o caso padrão em `0800925E`, não os tratamentos especiais de 5, 8 ou 10.

### Continuação em 08009214 — deslocamento em tiles

- No caminho padrão, `0800926E–08009280` converte a primeira coordenada em unidades de 8 pixels e subtrai o halfword em `[r6 + 0]`.
- `08009286–08009292` inicia o cálculo equivalente para a segunda coordenada.
- No caso especial de controle 10, `08009236–08009254` subtrai `[r6 + 2]` da segunda coordenada em tiles e pode reescrever esse campo.
- +0 e +2, antes sem interpretação, passam a ser candidatos a coordenadas de referência da atualização em tiles; ainda falta confirmar a atualização normal no final da função. Não são dimensões do mapa.
- O trecho não acessa +18: a interpretação de 40 como altura continua apoiada pelo layout e pelos intervalos entre blocos, não confirmada por esse código.

Próxima leitura focada: `disassemble/t $0800946A 40`, para examinar a parte final da função e verificar como atualiza as referências e o deslocamento gráfico.

## Ainda não localizado

- ID da sala e rotina que a carrega.
- Dados originais da arena na ROM e eventual compressão.
- Altura confirmada, colisão, área caminhável, saídas e eventos do boss.
- Estruturas de itens, inventário, equipamentos e recompensas.
- Persistência dos endereços entre personagens, classes, carregamentos e reinicializações.

## Comparação entre áreas — campos candidatos de identificação

| Local informado | `0300331C` (2 bytes) | `03003320` (2 bytes) |
|---|---:|---:|
| Arena do boss estudada | 1 | 7 |
| Entrada da fase, após teste de transição | 1 | 0 |
| Área seguinte à entrada | Não relido | 1 |
| Sala seguinte, após a sala 1 | Não relido | 2 |

A entrada foi testada após orientar a visita à fase dos goblins; o usuário informou apenas “entrada da fase”, sem repetir o nome. Confirmar o nome antes de catalogar formalmente. O usuário esclareceu que avançou salas, não fases.

Teste de escrita: o usuário tentou mudar `03003320` para 7 e não houve a troca desejada para a arena. Não foi fornecida leitura imediatamente após a escrita; não sabemos se o valor persistiu ou foi sobrescrito. Ao passar normalmente para a próxima sala, o campo mostrou 2. A sequência natural 0 → 1 → 2, junto de 7 na arena, sustenta que o campo acompanha o índice da sala atual. Escrever nele isoladamente não demonstrou acionar o carregamento de outra sala. Próximo alvo: observar uma escrita natural nesse campo durante uma transição.

Entre arena e entrada, o primeiro campo permaneceu em 1 e o segundo passou de 7 para 0. Ao avançar uma área a partir da entrada, o usuário leu `03003320 = 1`; `0300331C` ainda não foi relido nessa área. A sequência observada 0 → 1 reforça segundo campo = sala/segmento. Falta verificar se o primeiro continua em 1 e comparar com castelo e outra fase. Não presumir que todos os números sejam sequenciais nem que esses campos possam ser escritos para teletransportar.

### Transição natural da sala 2 para 3

Watchpoint #7 em mudança de `03003320` disparou com valor antigo 2 e novo 3. Isso confirma que o campo é atualizado no percurso normal entre salas; sequência observada 0 → 1 → 2 → 3, com 7 na arena.

```text
r0: 03003320  r1: 00000000  r2: 08546564  r3: 00000018
r4: 00000003  r5: 03003290  r6: 03003550  r7: 00000001
r8: 00000001  r9: 0854654C  r10: 00000000 r11: 00000000
r12: 0000271A r13: 0202FB58 r14: 080094F5 r15: 08009524
cpsr: 0000003F [------T]
Cycle: 61701775236
```

O código está em modo Thumb, próximo de `08009524`; confirmar a instrução exata da escrita com disassembly. `r4 = 3` coincide com o novo índice; `r5` aponta para a base já conhecida das estruturas. `0854654C` e `08546564` são endereços na região de ROM e diferem em `0x18`, mas não há evidência suficiente para nomeá-los como tabela de salas ou descritores. Próxima leitura: `disassemble/t $080094C0 64`. Manter a parada até capturar o trecho.

### Função de preparação da transição — 080094CC

Confirmado pelo disassembly fornecido:

- Entrada Thumb em `080094CC`; salva argumento `r0` em `r7` e argumento `r1` em `r4`.
- `0800951C` grava o primeiro argumento, via `r7`, em `0300331C`.
- `08009520` grava o segundo argumento, via `r4`, em `03003320`. Essa é a escrita que disparou o watchpoint na transição 2 → 3.
- No teste, argumentos preservados: primeiro = 1; segundo = 3. A interpretação do segundo como índice da sala é fortemente sustentada; primeiro como fase/contexto ainda depende de comparação entre fases.
- Antes das escritas, testa o bit 0 em `0300332C` (+0x9C da base) e o retorno de uma chamada a `08000470` com `03003550` como argumento. Alguns caminhos retornam zero sem executar a preparação. Significado dos controles ainda desconhecido.
- Prepara campos na estrutura `03003550`: +12 recebe `0800A535`, +16 recebe `0300354C`, +8 recebe 80 decimal, +32 e +36 recebem zero no caminho observado. O endereço ímpar `0800A535` é compatível com ponteiro para função Thumb em `0800A534`; o uso como callback ainda precisa ser confirmado.
- Portanto, a função faz mais que escrever os índices: alterar somente `03003320` não reproduz a preparação observada. Ainda não foi demonstrado que chamar esta função isoladamente basta para trocar de sala com segurança.
- Para o primeiro argumento = 1, `08009522–08009526` desvia para `0800962C`, evitando o caso especial de valor 5.
- `080094C0–080094CB` e os literais em `08009500–08009507` são dados exibidos como instruções, não sequência executável normal.
- Os valores `0854654C` e `08546564` nos registradores da parada anterior ainda não foram usados no trecho mostrado; podem ser valores residuais. Não catalogá-los como descritores sem observar seu uso.

Próxima leitura no caminho efetivamente usado: `disassemble/t $0800962C 96`. Objetivo: acompanhar a seleção/preparação de dados para os argumentos 1 e 3, até o final próximo de `08009708`.

### Tabela de seleção de salas na ROM — 0800962C

O código calcula o endereço da entrada como:

```text
entrada = 0848553C + contexto * 0x74 + 0x10 + sala * 4
```

Aqui `contexto` é o primeiro argumento preservado em r7 (candidato a fase) e `sala` o segundo, preservado em r4. O passo de 0x74 por contexto não comprova sozinho quantas salas existem: pode haver cabeçalho e outros campos.

Para contexto 1:

- Sala 0: entrada em `084855C0`.
- Sala 3: entrada em `084855CC`.
- Arena, sala 7: entrada em `084855DC`.

Esses são endereços de entradas, não os endereços finais dos mapas. `0800963A` lê a entrada e `0800963C` chama `08006E34` para interpretá-la. O retorno é guardado em `03003340` (base +0xB0). Depois chama `08008CDC` com esse resultado e o contexto.

A entrada original tem o bit `0x40000000` testado. Dependendo dele, o código usa o retorno +0x10 diretamente ou chama `08000BC8` com retorno +0x10 e `030032F4` como argumentos. Formato da entrada, significado do bit e função de `08000BC8` ainda não confirmados; não assumir ponteiro direto nem compressão.

O resultado desse segundo caminho é guardado em `030032F0` (base +0x60). A estrutura apontada tem dois campos iniciais de 2 bytes, usados no cálculo:

```text
ponteiro seguinte = estrutura + 0x10 + campo0 * campo2 * 6
```

Isso é compatível com cabeçalho de 16 bytes e três camadas de 2 bytes por tile, dadas as evidências anteriores. O código guarda o ponteiro seguinte em +0x68 ou +0x6C conforme o resultado de `0800C6B0`; não identifica sozinho o conteúdo seguinte como colisão. No caminho de retorno zero dessa função, copia os dois campos para `03003308` e `0300330A`.

A rotina também copia esses campos para outros controles e zera estado de atualização. Portanto, escrever só o índice da sala não executa esse carregamento.

Importante: a última parada foi na escrita do índice em `08009520`, ANTES dessas operações. Enquanto permanecer nessa parada, os ponteiros e dimensões globais podem ainda corresponder à sala anterior. Não rotulá-los automaticamente como dados da sala 3.

Próximas leituras estáticas: `x/4 $084855C0 8` e `disassemble/t $08006E34 24`, para examinar as entradas 0–7 e a função que interpreta seus valores.

### Entradas de salas e resolução de recurso

Leitura das oito entradas do contexto 1:

| Sala | Endereço da entrada | Valor/código de recurso |
|---|---|---|
| 0 | `084855C0` | `00020006` |
| 1 | `084855C4` | `00020007` |
| 2 | `084855C8` | `00020008` |
| 3 | `084855CC` | `00020009` |
| 4 | `084855D0` | `0002000A` |
| 5 | `084855D4` | `0002000B` |
| 6 | `084855D8` | `0002000C` |
| 7 — arena | `084855DC` | `0002000D` |

Os valores não são ponteiros diretos para a ROM. `08006E34` preserva o argumento em r0, coloca `0856F954` em r1 e chama `08006A5C`; retorna seu resultado. Assim, `08006A5C` recebe o código e uma base para resolvê-lo. O significado da parte alta `0002` e da parte baixa ainda não foi demonstrado; hipótese de grupo/índice não confirmada.

A função `08006E34` termina em `08006E3E`; `08006E40` é o literal e `08006E44` inicia outra função. Não usar a rotina posterior como continuação do resolvedor.

Próxima leitura: `disassemble/t $08006A5C 64`. Objetivo: obter a fórmula de resolução e então ler somente as entradas de tabela necessárias para o recurso da arena `0002000D`.

### Leitura dos mapas via MCP do mGBA — 2026-09-26

O MCP `mcp-mgba` foi conectado ao mGBA 0.10.5 por `bridge.lua`, escutando em `127.0.0.1:8765`. A ROM foi identificada como `SHININGSOUL2`, código `AGB-AU2E`. Nesta versão estão disponíveis leitura/escrita de memória, entrada de botões, screenshot e save states; `pause`, `unpause` e `frameAdvance` não estão disponíveis.

Estado observado na área externa com cercas e fonte:

- A estrutura de BG3 em `030032D8` continuou contendo o ponteiro `0200B440`, largura `003C` (60), altura `0028` (40), camada `0003` e controle final `0001`.
- `BG3CNT = 1F03`: prioridade 3, char base 0, screen base 31 e tilemap físico de 32x32 em `0600F800`.
- Os 2048 bytes de `0202C460` coincidiram exatamente com os 2048 bytes enviados a `0600F800` no estado observado.
- `0202C460` é um tilemap circular de 32x32 produzido a partir do mapa maior apontado por `0200B440`.
- Após mover para cima, as 32 linhas físicas corresponderam exatamente à janela mundial `x=6..37`, `y=0..31`.
- Após mover para baixo, as 32 linhas físicas corresponderam exatamente à janela mundial `x=6..37`, `y=7..38`.
- A posição física obedece ao anel: `x_fisico = x_mundo mod 32` e `y_fisico = y_mundo mod 32`. Exemplo confirmado: na linha física 0, posições 0..5 receberam `x=32..37` e posições 6..31 receberam `x=6..31`.
- As linhas mundiais 0..38 foram verificadas contra a origem; a linha 39 ainda não entrou na janela durante este teste.
- A sequência inicial do mapa e a combinação de dimensões/cabeçalho não foram encontradas cruas na ROM. Isso sustenta que o recurso passa pelo resolvedor e por descompressão ou transformação antes de chegar a `0200B440`; ainda não identifica o formato.
- Leituras dos registradores de scroll `04000010..0400001E` pelo bridge retornaram repetidamente `30B8` para todos os BGs e não foram consideradas confiáveis. Usar comparação dos tilemaps e debugger nativo para confirmar scroll.

Checkpoint criado antes do teste de movimento: `outputs/map-baseline.ss0` na pasta desta conversa do Codex. Screenshots: `current-map.png`, `map-after-up.png` e `map-after-down.png`.

Próximo alvo recomendado: continuar o caminho do código de recurso da sala (`0002000D` para a arena) por `08006A5C`, identificar o bloco comprimido na ROM e correlacionar sua saída com o cabeçalho/dados em `0200B430`/`0200B440`.

### Recurso da arena resolvido na ROM

O resolvedor em `08006A5C` foi acompanhado estaticamente para o código `0002000D`:

```text
base do resolvedor = 0856F954
deslocamento do grupo 2 = *(0856F954 + 0x10) = 000BE448
tabela do grupo 2 = 0862DD9C
entrada do índice 000D = 0862DDD4
deslocamento da entrada = 00025DE0
recurso da arena = 08653B7C
stream LZ77 = 08653B8C
```

Formato confirmado do recurso:

- `08653B7C..08653B8B`: descritor de 16 bytes.
- `08653B8C`: stream GBA LZ77 tipo `0x10`.
- Cabeçalho LZ77 `10 10 4B 00`: saída descomprimida de `0x4B10` (19.216) bytes.
- Saída = cabeçalho de `0x10` bytes + quatro planos de `60 * 40 * 2 = 0x12C0` bytes.
- Plano 0, offset `0x0010`: RAM `0200B440`, BG3.
- Plano 1, offset `0x12D0`: RAM `0200C700`, BG2.
- Plano 2, offset `0x2590`: RAM `0200D9C0`, BG1.
- Plano 3, offset `0x3850`: RAM `0200EC80`, atributos/colisão.
- Os inícios dos quatro planos extraídos da ROM coincidiram byte por byte com a RAM.

O quarto plano tem 11 valores observados: `8100`, `9000`, `9100` e `9200..9900`. A visualização forma exatamente o contorno oval da arena: `9000` domina o piso interno, `9100` o exterior, `8100` a borda e `9200..9900` aparecem em cantos/trechos inclinados. Isso confirma uma grade de atributos/colisão, embora a semântica exata de cada valor especial ainda precise de teste controlado.

Limite para patch no lugar:

- Próximo recurso: `08654D4C`.
- Espaço total desta entrada: 4.560 bytes, incluindo o descritor de 16 bytes.
- Orçamento do stream: 4.544 bytes.
- Stream original: 4.541 bytes, apenas 3 bytes livres.
- Recompressão ótima experimental: 4.512 bytes, round-trip validado, 32 bytes livres.
- Estratégia padrão: tentar patch no lugar e validar o tamanho. Se uma edição ultrapassar 4.544 bytes, realocar o recurso para espaço livre e atualizar a entrada relativa em `0862DDD4`.

Ferramentas locais de pesquisa na pasta desta conversa: extrator LZ77, compressor LZ77 ótimo, desassemblador Thumb e renderizador da grade de atributos. Nenhuma alteração foi aplicada à ROM original.

### Menu principal — estratégia definida

O menu principal exibido tem duas opções: `SINGLE PLAYER MODE` e `MULTIPLAYER MODE`. Os textos não aparecem como ASCII simples na ROM.

- `03002958` foi confirmado como índice do cursor: `0` seleciona Single Player e `1` seleciona Multiplayer.
- A escrita temporária de `1` moveu o cursor visualmente para Multiplayer.
- A rotina em torno de `08002678` trata somente duas posições: um sentido grava `1`, o outro grava `0`.
- Após confirmação, o despacho em `080027FC` lê `03002958`: índice `0` segue por `08002818`; índice `1` segue por `0800283E`.
- Existem casos internos 2 e 3 no despacho maior, mas isso não demonstra opções visíveis adicionais no menu.

Decisão estratégica: preservar as duas opções visíveis, mas transformar ambas em modos do mod de arenas. Single Player será redirecionado primeiro e constitui o MVP. Multiplayer continuará visível e será adaptado em uma etapa posterior; a campanha original não será o destino final de nenhuma das duas opções. Não é necessário criar uma terceira linha `ARENA` no menu para o MVP.

### Save e criação do personagem — estratégia definida

- Manter a tela de seleção/criação de arquivos para que o jogador possa salvar o progresso normalmente.
- Em um arquivo novo, restringir a escolha de classe/personagem ao Eric.
- Manter a tela de seleção de cores do Eric.
- Manter a edição e confirmação do nome.
- Depois da confirmação final do nome, avançar automaticamente pela introdução da campanha e seguir para a arena. No estado atual, o livro aparece brevemente antes do skip artificial aceito.
- O teste do fluxo original confirmou a sequência: arquivo -> New Game -> personagem -> confirmação de Eric -> cor -> nome -> confirmação -> introdução do livro.
- O redirecionamento do carregador já leva ao contexto `1`, sala `7`, após a abertura. O diálogo do chefe ainda precisa ser tratado separadamente.
- Outras classes/personagens poderão ser adicionados depois do MVP.

## Atualizações futuras

Para cada descoberta, registrar data, endereço, tamanho, valor anterior/depois, comando, efeito observado e condição de teste. Manter hipóteses separadas das confirmações e anotar dependência da sala/personagem.

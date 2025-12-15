# Quick Camera Moves

Addon para Blender que cria movimentos cinematográficos de câmera com poucos cliques.

![Blender](https://img.shields.io/badge/Blender-4.0%2B-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

## Movimentos disponíveis

- **Orbit** — gira ao redor do target
- **Dolly In/Out** — aproxima ou afasta do target
- **Truck Left/Right** — movimento lateral
- **Pedestal Up/Down** — sobe ou desce a câmera
- **Crane Shot** — movimento em arco vertical
- **Dolly Zoom (Vertigo)** — efeito Hitchcock, fundo distorce enquanto subject mantém tamanho
- **Arc Shot** — arco 3D ao redor do target com variação de altura
- **Whip Pan** — rotação rápida horizontal para transições
- **Push In + Tilt** — aproxima com inclinação vertical
- **Turntable** — rotação 360° perfeita para showcase
- **Flythrough** — atravessa a cena em linha reta
- **Zoom In/Out** — zoom óptico (só FOV, sem movimento)
- **Camera Shake** — tremida de câmera na mão (handheld)
- **Follow Path** — câmera segue uma curva bezier

## Instalação

1. Baixe o arquivo `quick_camera_moves.py`
2. No Blender, vá em **Edit → Preferences → Add-ons**
3. Clique em **Install** e selecione o arquivo `.py`
4. Ative o addon marcando a checkbox

O painel aparece na sidebar do 3D Viewport (tecla **N**), na aba **Camera Moves**.

## Como usar

1. Tenha uma câmera ativa na cena
2. Escolha um objeto como **Target** (ou deixe vazio pra usar o 3D Cursor)
3. Selecione o tipo de movimento
4. Ajuste duração e parâmetros
5. Clique em **Criar Movimento**

## Requisitos

- Blender 4.0 ou superior
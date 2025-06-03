# app_bst_streamlit_sem_tabs.py

import streamlit as st
import time
import re
from graphviz import Digraph
from collections import deque

# ─────────────────────────────────────────────────────────────────────────── #
#                           Definição do nó da BST
# ─────────────────────────────────────────────────────────────────────────── #
class Node:
    def __init__(self, key: int):
        self.key = key
        self.left: "Node | None" = None
        self.right: "Node | None" = None

# ─────────────────────────────────────────────────────────────────────────── #
#              Função tradicional para inserir na BST (in-order de antes)
# ─────────────────────────────────────────────────────────────────────────── #
def bst_insert(root: Node | None, key: int) -> Node:
    if root is None:
        return Node(key)
    if key < root.key:
        root.left = bst_insert(root.left, key)
    elif key > root.key:
        root.right = bst_insert(root.right, key)
    # se igual, não insere (evita duplicados)
    return root

# ─────────────────────────────────────────────────────────────────────────── #
#            Funções geradoras dos quatro tipos de percurso (in-order etc)
# ─────────────────────────────────────────────────────────────────────────── #
def preorder_keys(root: Node | None):
    if root is None:
        return
    yield root.key
    yield from preorder_keys(root.left)
    yield from preorder_keys(root.right)

def inorder_keys(root: Node | None):
    if root is None:
        return
    yield from inorder_keys(root.left)
    yield root.key
    yield from inorder_keys(root.right)

def postorder_keys(root: Node | None):
    if root is None:
        return
    yield from postorder_keys(root.left)
    yield from postorder_keys(root.right)
    yield root.key

def breadth_first_keys(root: Node | None):
    if root is None:
        return
    queue = deque([root])
    while queue:
        node = queue.popleft()
        yield node.key
        if node.left:
            queue.append(node.left)
        if node.right:
            queue.append(node.right)

# ─────────────────────────────────────────────────────────────────────────── #
#      Função para transformar texto DOT (Graphviz) em estrutura de BST
# ─────────────────────────────────────────────────────────────────────────── #
def parse_dot_to_bst(dot_text: str) -> Node | None:
    """
    Recebe o texto DOT (Graphviz) e constrói os nós com as arestas "esq" e "dir".
    Retorna a raiz da BST encontrada (nó cuja chave não aparece como filho).
    """
    # 1) Extrair todos os IDs numéricos definidos como nós: node<numero>[...]
    node_defs = re.findall(r'\bnode(\d+)\s*\[', dot_text)
    all_keys = set(int(k) for k in node_defs)

    # 2) Criar instâncias Node para cada chave
    nodes: dict[int, Node] = {k: Node(k) for k in all_keys}

    # 3) Encontrar todas as linhas de aresta no padrão:
    #    "node5":esq -> "node4"   ou   node5:esq->node4
    edge_pattern = re.compile(r'"?node(\d+)"?\s*:(\w+)\s*->\s*"?node(\d+)"?')
    child_keys = set()

    for match in edge_pattern.finditer(dot_text):
        parent_key = int(match.group(1))
        port_name = match.group(2).lower()
        child_key = int(match.group(3))

        if parent_key not in nodes or child_key not in nodes:
            continue

        parent_node = nodes[parent_key]
        child_node = nodes[child_key]

        if port_name == "esq":
            parent_node.left = child_node
        elif port_name == "dir":
            parent_node.right = child_node

        child_keys.add(child_key)

    # 4) Identificar raiz: chave que não aparece em child_keys
    root_candidates = [k for k in all_keys if k not in child_keys]
    if not root_candidates:
        return None
    root_key = root_candidates[0]
    return nodes[root_key]

# ─────────────────────────────────────────────────────────────────────────── #
#       Função que percorre a árvore buscando uma chave e retorna:
#       1) o nó encontrado (ou None)
#       2) a lista de chaves visitadas, em ordem
# ─────────────────────────────────────────────────────────────────────────── #
def search_node_ref(root: Node | None, key: int) -> tuple[Node | None, list[int]]:
    """
    Percorre a BST iterativamente, acumulando cada nó visitado em uma lista.
    Se encontrar 'key', retorna (nó_encontrado, caminho_lista). Caso contrário,
    retorna (None, caminho_lista) após esgotar a busca.
    """
    visited_list: list[int] = []
    current = root
    while current is not None:
        visited_list.append(current.key)
        if key == current.key:
            return current, visited_list
        elif key < current.key:
            current = current.left
        else:  # key > current.key
            current = current.right
    return None, visited_list

# ─────────────────────────────────────────────────────────────────────────── #
#   Função para construir o grafo Graphviz colorindo nós visitados e,
#   opcionalmente, o nó encontrado em outra cor (por ex. lightgreen).
# ─────────────────────────────────────────────────────────────────────────── #
def build_dot(root: Node | None, visited_set: set[int], found_key: int | None = None) -> Digraph:
    """
    - visited_set: conjunto de chaves de nós que já foram visitados (coloridos de lightblue)
    - found_key: se não for None, o nó com chave == found_key será colorido de lightgreen.
    """
    dot = Digraph(format="png")
    dot.attr("node", shape="circle", style="filled", color="black")

    def add_nodes_edges(node: Node | None):
        if node is None:
            return

        if found_key is not None and node.key == found_key:
            fill = "lightgreen"
        elif node.key in visited_set:
            fill = "lightblue"
        else:
            fill = "white"

        dot.node(str(node.key), fillcolor=fill)

        if node.left:
            dot.edge(str(node.key), str(node.left.key))
            add_nodes_edges(node.left)
        if node.right:
            dot.edge(str(node.key), str(node.right.key))
            add_nodes_edges(node.right)

    add_nodes_edges(root)
    return dot

# ─────────────────────────────────────────────────────────────────────────── #
#                         Inicialização do Streamlit
# ─────────────────────────────────────────────────────────────────────────── #
st.set_page_config(layout="centered")
st.title("📊 Árvore Binária de Busca")

# ─────────────────────────────────────────────────────────────────────────── #
#               Inicializa chaves em session_state, se não existirem
# ─────────────────────────────────────────────────────────────────────────── #
if "root" not in st.session_state:
    st.session_state["root"] = None

# Estado geral da aplicação:
# - operation: "idle" | "search" | "traversal"
# - sequence: lista de chaves na ordem a ser visitada
# - current_index: índice atual na sequência (começa em -1, antes do primeiro)
# - auto_run: True | False (se deve avançar automaticamente)
# - target_key: inteiro buscado (para highlight em search), ou None
for key in ["operation", "sequence", "current_index", "auto_run", "target_key"]:
    if key not in st.session_state:
        st.session_state[key] = None if key in ["target_key"] else []

# Garante valores padrão
if st.session_state["operation"] is None:
    st.session_state["operation"] = "idle"
if st.session_state["sequence"] == []:
    st.session_state["sequence"] = []
if st.session_state["current_index"] is None:
    st.session_state["current_index"] = -1
if st.session_state["auto_run"] is None:
    st.session_state["auto_run"] = False
if st.session_state["target_key"] is None:
    st.session_state["target_key"] = None

# ─────────────────────────────────────────────────────────────────────────── #
#                         SIDEBAR: Construção da Árvore
# ─────────────────────────────────────────────────────────────────────────── #
st.sidebar.write("# 1) Construir Árvore")

## 1.1) Modo Valores
st.sidebar.subheader("A) A partir de VALORES")
valores_txt = st.sidebar.text_input(
    "🔢 Valores (ex: 50,30,70,20)",
    value="50,30,70,20,40,60,80,10,25,35,45"
)
if st.sidebar.button("🛠️ Construir (Valores)"):
    try:
        lista_valores = [int(x.strip()) for x in valores_txt.split(",") if x.strip() != ""]
    except ValueError:
        st.sidebar.error("❌ Use apenas números inteiros separados por vírgula.")
        st.stop()
    if not lista_valores:
        st.sidebar.error("❌ A lista não pode ficar vazia.")
        st.stop()
    root = None
    for v in lista_valores:
        root = bst_insert(root, v)
    st.session_state["root"] = root
    # Ao reconstruir a árvore, resetar qualquer operação em curso
    st.session_state["operation"] = "idle"
    st.session_state["sequence"] = []
    st.session_state["current_index"] = -1
    st.session_state["auto_run"] = False
    st.session_state["target_key"] = None
    st.sidebar.success("✅ Árvore (Valores) criada!")

st.sidebar.markdown("---")

## 1.2) Modo DOT
st.sidebar.subheader("B) A partir de TEXTO DOT")
dot_default = """digraph g { 
  node [shape = record,height=.1];

  node4[label = "<esq> | 4 | <dir> "]
  node5[label = "<esq> | 5 | <dir> "]
  node6[label = "<esq> | 6 | <dir> "]
  node15[label = "<esq> | 15 | <dir> "]
  node19[label = "<esq> | 19 | <dir> "]
  node25[label = "<esq> | 25 | <dir> "]
  node29[label = "<esq> | 29 | <dir> "]
  node30[label = "<esq> | 30 | <dir> "]

  "node5":esq -> "node4" 
  "node5":dir -> "node6" 
  "node15":esq -> "node5" 
  "node25":esq -> "node19" 
  "node29":dir -> "node30" 
  "node25":dir -> "node29" 
  "node15":dir -> "node25" 
}"""
dot_text = st.sidebar.text_area("📄 Cole o grafo DOT aqui:", value=dot_default, height=200)
if st.sidebar.button("🛠️ Construir (DOT)"):
    if not dot_text.strip():
        st.sidebar.error("❌ O texto DOT não pode ficar vazio.")
        st.stop()
    root_dot = parse_dot_to_bst(dot_text)
    if root_dot is None:
        st.sidebar.error("❌ Não foi possível analisar o DOT. Verifique o formato.")
        st.stop()
    st.session_state["root"] = root_dot
    # Resetar operações ao reconstruir
    st.session_state["operation"] = "idle"
    st.session_state["sequence"] = []
    st.session_state["current_index"] = -1
    st.session_state["auto_run"] = False
    st.session_state["target_key"] = None
    st.sidebar.success("✅ Árvore (DOT) criada!")

st.sidebar.markdown("---")

# ─────────────────────────────────────────────────────────────────────────── #
#                        SIDEBAR: Função de Busca (search_node_ref)
# ─────────────────────────────────────────────────────────────────────────── #
st.sidebar.subheader("2) Buscar um elemento na BST")
busca_txt = st.sidebar.text_input("🔎 Digite a chave a buscar:", value="")
if st.sidebar.button("🔍 Iniciar Busca"):
    if st.session_state["root"] is None:
        st.sidebar.error("❌ Construa a árvore antes de buscar.")
        st.stop()
    try:
        chave_busca = int(busca_txt.strip())
    except ValueError:
        st.sidebar.error("❌ Use apenas números inteiros para buscar.")
        st.stop()

    # Executa a busca e monta a lista de nós visitados na ordem
    found_node, caminho = search_node_ref(st.session_state["root"], chave_busca)
    # Prepara sequência e estado de operação
    st.session_state["operation"] = "search"
    st.session_state["sequence"] = caminho[:]            # cópia da lista de inteiros
    st.session_state["current_index"] = -1               # antes do primeiro passo
    st.session_state["auto_run"] = False                 # não começar rodando automaticamente
    st.session_state["target_key"] = chave_busca         # a chave procurada

    if found_node is not None:
        st.sidebar.success(f"✅ Chave {chave_busca} encontrada (preparada para passo a passo).")
    else:
        st.sidebar.info(f"⚠️ Chave {chave_busca} NÃO encontrada (será exibido caminho visitado).")

st.sidebar.markdown("---")

# ─────────────────────────────────────────────────────────────────────────── #
#                        SIDEBAR: Caminhamentos (tratamento por passo)
# ─────────────────────────────────────────────────────────────────────────── #
st.sidebar.subheader("3) Caminhamentos (por passo)")
caminhamentos = ['Pré-ordem', 'Central', 'Pós-ordem', 'Largura']
sel_caminhamento = st.sidebar.selectbox("Escolha o tipo de caminhamento:", caminhamentos)
if st.sidebar.button("▶️ Preparar Caminhamento"):
    if st.session_state["root"] is None:
        st.sidebar.error("❌ Construa a árvore antes de percorrer.")
        st.stop()

    # Gera sequência de chaves conforme o tipo de caminhamento
    if sel_caminhamento == 'Pré-ordem':
        seq = list(preorder_keys(st.session_state["root"]))
    elif sel_caminhamento == 'Central':
        seq = list(inorder_keys(st.session_state["root"]))
    elif sel_caminhamento == 'Pós-ordem':
        seq = list(postorder_keys(st.session_state["root"]))
    else:  # 'Largura'
        seq = list(breadth_first_keys(st.session_state["root"]))

    st.session_state["operation"] = "traversal"
    st.session_state["sequence"] = seq[:]
    st.session_state["current_index"] = -1      # antes do primeiro passo
    st.session_state["auto_run"] = False
    st.session_state["target_key"] = None       # não é uma busca
    st.sidebar.success(f"✅ Sequência de {sel_caminhamento} preparada ({len(seq)} nós).")

st.sidebar.markdown("---")

# ─────────────────────────────────────────────────────────────────────────── #
#                        SIDEBAR: Controles Gerais
# ─────────────────────────────────────────────────────────────────────────── #
# Este espaço pode ser deixado para adicionar outra funcionalidade, se necessário.
# Por enquanto, não usamos nada aqui.

# ─────────────────────────────────────────────────────────────────────────── #
#                         TELA PRINCIPAL: Exibição e Controles
# ─────────────────────────────────────────────────────────────────────────── #

st.write("## Visualização da Árvore e Controles de Passo")

# placeholders para gráfico e texto abaixo
placeholder_tree = st.empty()
placeholder_info = st.empty()

root = st.session_state["root"]

# Função auxiliar para desenhar o estado atual (search ou traversal)
def render_current_step():
    seq = st.session_state["sequence"]
    idx = st.session_state["current_index"]
    # Se estamos antes do primeiro passo, visited_set = vazio
    if idx < 0:
        visited = set()
    else:
        visited = set(seq[: idx + 1])
    # Em busca, destaca-se target_key se idx alcançar o nó alvo
    target = None
    if st.session_state["operation"] == "search" and idx >= 0:
        passo_chave = seq[idx]
        if passo_chave == st.session_state["target_key"]:
            target = passo_chave

    dot = build_dot(root, visited_set=visited, found_key=target)
    placeholder_tree.graphviz_chart(dot)

    # Informação de texto
    if st.session_state["operation"] == "search":
        if idx < 0:
            placeholder_info.info("🔎 Busca não iniciada.")
        else:
            texto = ", ".join(str(x) for x in seq[: idx + 1])
            if idx < len(seq) and seq[idx] == st.session_state["target_key"]:
                placeholder_info.success(f"Passo {idx+1}/{len(seq)}: {texto}\n🟩 Nó {st.session_state['target_key']} encontrado!")
            else:
                if idx == len(seq) - 1 and seq[-1] != st.session_state["target_key"]:
                    placeholder_info.warning(f"Passo final ({idx+1}/{len(seq)}): {texto}\n❌ Não encontrado.")
                else:
                    placeholder_info.write(f"Passo {idx+1}/{len(seq)}: {texto}")

    elif st.session_state["operation"] == "traversal":
        if idx < 0:
            placeholder_info.info("▶️ Caminhamento não iniciado.")
        else:
            texto = ", ".join(str(x) for x in seq[: idx + 1])
            if idx == len(seq) - 1:
                placeholder_info.success(f"Passo final ({idx+1}/{len(seq)}): {texto}")
            else:
                placeholder_info.write(f"Passo {idx+1}/{len(seq)}: {texto}")

    else:  # idle
        placeholder_info.warning("🛈 Construa a árvore e inicie busca ou caminhamento para usar os controles de passo.")

# Renderização inicial (ou de acordo com estado)
if root is None:
    placeholder_tree.empty()
    placeholder_info.warning("🛈 Construa a árvore pela sidebar primeiro.")
else:
    render_current_step()

# ─────────────────────────────────────────────────────────────────────────── #
#                       CONTROLES DE PASSO: Voltar / Avançar / Run / Pause
# ─────────────────────────────────────────────────────────────────────────── #

def step_back():
    if st.session_state["current_index"] > -1:
        st.session_state["current_index"] -= 1

def step_forward():
    seq = st.session_state["sequence"]
    if st.session_state["current_index"] < len(seq) - 1:
        st.session_state["current_index"] += 1

def start_run_all():
    st.session_state["auto_run"] = True

def pause_run():
    st.session_state["auto_run"] = False

# Apenas mostrar controles se estivermos em busca ou caminhamento
if st.session_state["operation"] in ["search", "traversal"]:
    cols = st.columns([1, 1, 1, 1])
    with cols[0]:
        if st.button("⏮️ Voltar 1x"):
            step_back()
    with cols[1]:
        if st.button("⏭️ Avançar 1x"):
            step_forward()
    with cols[2]:
        if st.button("▶️ Rodar Tudo"):
            start_run_all()
    with cols[3]:
        if st.button("⏸️ Pausar"):
            pause_run()

    # Se auto_run está ativado, avançar automaticamente até o final (com pequeno delay)
    if st.session_state["auto_run"]:
        seq = st.session_state["sequence"]
        idx = st.session_state["current_index"]

        # Se ainda há passos a executar
        if idx < len(seq) - 1:
            # Avança um passo
            st.session_state["current_index"] = idx + 1
            render_current_step()
            time.sleep(0.8)
            st.rerun()
        else:
            # Se alcançou o fim, para o auto_run
            st.session_state["auto_run"] = False

# ─────────────────────────────────────────────────────────────────────────── #
#                            Visualização Final
# ─────────────────────────────────────────────────────────────────────────── #
st.markdown("---")
st.write("### Estado Atual (para debug) ")
st.write(f"- Operação: `{st.session_state['operation']}`")
st.write(f"- Índice atual: `{st.session_state['current_index']}`")
if st.session_state["sequence"]:
    st.write(f"- Sequência total: {st.session_state['sequence']}")
else:
    st.write(f"- Sequência total: []")
if st.session_state["target_key"] is not None:
    st.write(f"- Chave alvo (buscar): `{st.session_state['target_key']}`")
st.write(f"- Auto-run: `{st.session_state['auto_run']}`")

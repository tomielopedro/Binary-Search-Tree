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
#                    Função tradicional para inserir na BST
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
#                    Funções geradoras dos quatro tipos de percurso
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
#      Função para construir o grafo Graphviz colorindo nós visitados
# ─────────────────────────────────────────────────────────────────────────── #
def build_dot(root: Node | None, visited_set: set[int]) -> Digraph:
    dot = Digraph(format="png")
    dot.attr("node", shape="circle", style="filled", color="black")

    def add_nodes_edges(node: Node | None):
        if node is None:
            return
        fill = "lightblue" if node.key in visited_set else "white"
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
#                         Início do App Streamlit
# ─────────────────────────────────────────────────────────────────────────── #
st.set_page_config(layout="centered")
st.title("📊 Caminhamento BST — Valores ou DOT")

# ─────────────────────────────────────────────────────────────────────────── #
#                         SIDEBAR: Entradas e Botões
# ─────────────────────────────────────────────────────────────────────────── #
st.sidebar.write("# Construir Árvore")

## 1) Modo Valores
st.sidebar.subheader("1) A partir de VALORES")
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
    st.session_state["modo"] = "valores"
    if "dot_text" in st.session_state:
        del st.session_state["dot_text"]
    st.sidebar.success("✅ Árvore (Valores) criada!")

st.sidebar.markdown("---")

## 2) Modo DOT
st.sidebar.subheader("2) A partir de TEXTO DOT")
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
    st.session_state["modo"] = "dot"
    st.session_state["dot_text"] = dot_text
    if "lista_valores" in st.session_state:
        del st.session_state["lista_valores"]
    st.sidebar.success("✅ Árvore (DOT) criada!")

st.sidebar.markdown("---")

## 3) Botões de percurso
st.sidebar.subheader("3) Caminhamentos")
caminhamentos = ['Pré-ordem', 'Pós-ordem', 'Central', 'Largura']
caminhamento_buttons = st.sidebar.pills('Selecione um tipo de caminhamento: ',caminhamentos)



# ─────────────────────────────────────────────────────────────────────────── #
#                         TELA PRINCIPAL: Explicações e Árvore
# ─────────────────────────────────────────────────────────────────────────── #

with st.expander('Mode de uso', expanded=False):
    st.write('Na :orange[sidebar], escolha:')
    st.write('1) A partir de :green[VALORES]: Digite inteiros separados por vírgula e clique em :blue[Construir (Valores)]')
    st.write('2) A partir de :green[TEXTO DOT]: Cole o grafo DOT completo e clique em :blue[Construir (DOT)]')

with st.expander('Tipos de Caminhamento', expanded=False):

    st.write('Após a árvore ser construída (por qualquer modo), use os botões de percurso na :orange[sidebar]')
    st.write(':blue[Pré-ordem]: (raiz → esquerda → direita)')
    st.write(':blue[Pós-ordem]: (esquerda → direita → raiz)')
    st.write(':blue[Central]: (esquerda → raiz → direita)')
    st.write(':blue[Largura]: (nível a nível)')




# Placeholder para árvore e lista de visitas
placeholder_tree = st.empty()
placeholder_list = st.empty()

# Se existe árvore em session_state, renderiza
if "root" in st.session_state:
    root = st.session_state["root"]
    # Renderização inicial (sem nenhum nó colorido)
    dot_inicial = build_dot(root, visited_set=set())
    placeholder_tree.graphviz_chart(dot_inicial)
    placeholder_list.empty()
else:
    placeholder_tree.empty()
    placeholder_list.warning("🛈 Construa a árvore pela sidebar primeiro.")

# ─────────────────────────────────────────────────────────────────────────── #
#                     LÓGICA DE ANIMAÇÃO DOS PERCURSOS
# ─────────────────────────────────────────────────────────────────────────── #
if "root" in st.session_state:
    root = st.session_state["root"]

    def animate_traversal(generator):
        visited_set: set[int] = set()
        visited_list: list[int] = []
        for chave in generator:
            visited_set.add(chave)
            visited_list.append(chave)
            dot_passo = build_dot(root, visited_set)
            placeholder_tree.graphviz_chart(dot_passo)
            texto = ", ".join(str(x) for x in visited_list)
            placeholder_list.write(f"## Elementos:  {texto}")
            time.sleep(0.8)


    if caminhamento_buttons == 'Pré-ordem':
        animate_traversal(preorder_keys(root))
        st.sidebar.success("✅ Pré-ordem concluído!")

    if caminhamento_buttons == 'Central':
        animate_traversal(inorder_keys(root))
        st.sidebar.success("✅ I'Central concluído!")

    if caminhamento_buttons == 'Largura':
        animate_traversal(breadth_first_keys(root))
        st.sidebar.success("✅ Largura concluído!")

    if caminhamento_buttons == 'Pós-ordem':
        animate_traversal(postorder_keys(root))
        st.sidebar.success("✅ Pós-ordem concluído!")

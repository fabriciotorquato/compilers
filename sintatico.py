import json
from collections import defaultdict


# Regras de produção resumidas
# Validando apenas a chamada de função completa
productions = [
    {"programa": ["funcao", "programa"]},
    {"programa": ["@"]},
    {"funcao": ["identificador", "dois-pontos", "tipo-funcao",
                "funcao-parametros", "retorno", "::", "abre-chaves", "corpo", "fecha-chaves"]},
    {"funcao-parametros": ["abre-parenteses", "list", "fecha-parenteses"]},
    {"list": ["identificador", "dois-pontos", "tipo", "list-linha"]},
    {"list-linha": ["virgula", "list"]},
    {"list-linha": ["@"]},
    {"tipo": ["Logica"]},
    {"tipo": ["Texto"]},
    {"tipo": ["Numero"]},
    {"retorno": ["dois-pontos", "tipo"]},
    {"tipo-funcao": ["Funcao"]}
]

# Tabela LL
parsingTable = {
    "programa": {
        "identificador":  ["funcao", "programa"],
        "$": ["@"]
    },
    "funcao": {
        "identificador": ["identificador", "dois-pontos", "tipo-funcao",
                          "funcao-parametros", "retorno", "atribuicao", "abre-chaves", "corpo", "fecha-chaves"],
    },
    "funcao-parametros": {"abre-parenteses": ["abre-parenteses", "parametro-item", "fecha-parenteses"]},
    "parametro-item": {"identificador":  ["identificador", "dois-pontos", "tipo", "parametro-item-linha"]},
    "parametro-item-linha": {"virgula": ["virgula", "parametro-item"], "fecha-parenteses": ["@"]},
    "tipo": {"Logica": ["Logica"], "Texto": ["Texto"], "Numero": ["Numero"]},
    "retorno": {"dois-pontos": ["dois-pontos", "tipo"]},
    "corpo": {"fecha-chaves": ["@"]},
    "tipo-funcao": {"Funcao": ["Funcao"]}
}

# Terminais aceitos pela linguagem
terminal = ["identificador", "abre-parenteses", "fecha-parenteses", "dois-pontos", "atribuicao",
            "virgula", "abre-chaves", "fecha-chaves", "Logica", "Texto", "Numero", "Funcao", "corpo", "$"]


class Text:
    """Classe referente ao valor do token."""

    def __init__(self, text):
        self.text = text


class Group:
    """Classe referente ao grupo do token."""

    def __init__(self, group):
        self.group = group


class Locale:
    """Classe referente a localização do token."""

    def __init__(self, index, line):
        self.index = index
        self.line = line


class TokenVariables:
    """Classe os tokens que são variaveis da gramatica """

    def __init__(self, group):
        self.group = Group(group)


class Error:
    """Classe referente ao token de erro."""

    def __init__(self, erro_type):
        self.text = Text(erro_type)

    def getFormmated(self):
        """Metodo utilizado para formatada o modelo do json."""
        return {"texto": self.text.text}


class Grammar:
    """Classe que representa a gramatica """

    def __init__(self, productions, initial_variables):
        self.productions = productions
        self.initial_variables = TokenVariables(initial_variables)
        self.terminal = terminal

    def isTokenValid(self, token):
        return self.isTerminalValid(token.group.group)

    def isTerminalValid(self, text):
        return text in self.terminal


class Table:
    """Classe a tabela LL1 """

    def __init__(self, productions):
        self.productions = self.__getRules(productions)
        self.parsingTable = self.__getFirstFollowSets()

    def __getRules(self, productions):
        """Metodo utilizado para representação das regras em formato de Array de Array """

        data_dict = defaultdict(list)
        for key, value in enumerate(productions):
            data_dict[key].append(value)

        return data_dict

    def __getFirstFollowSets(self):
        """Metodo que seria responsavel pela criação da Tabela LL1"""

        return parsingTable


class Tree:
    """Classe da arvore de tokens"""

    def __init__(self):
        self.root = [
            {"tipo": "regra",
             "grupo": "programa",
                      "ramo": []
             }
        ]

    def inlude(self, parent, child):
        """metodo utilizado para inclusão de tokens que podem gerar filhos"""

        node_children = {}
        node_children = {"tipo": "regra",
                         "grupo": child,
                         "ramo": []
                         }
        parent["ramo"].append(node_children)
        return node_children

    def createLeaf(self, parent):
        """metodo utilizado para criar tokens folhas"""
        node_children = {
            "tipo": "token",
            "folha": ""
        }
        parent["ramo"].append(node_children)
        return node_children

    def includeLeaf(self, parent, child):
        """metodo utilizado para inclusão de tokens folhas"""
        if(child.group.group == "Funcao" or child.group.group == "Logica"):
            child.group.group = "reservado"

        parent["folha"] = child.getFormmated()


class ErrorTree:
    """Classe referente a arvores de erros."""

    def __init__(self):
        self.root = teste["erros"]

    def include(self, erro_type):
        error = Error(erro_type)
        self.root.append(error.getFormmated())


class Token:
    """Classe referente ao token."""

    def __init__(self, dict_token):
        self.__converterToken(dict_token)

    def __converterToken(self, dict_token):
        """Metodo responsavel pela captura do token em formato de JSON e transforma ele em uma classe"""

        if(dict_token["grupo"] == "reservado"):
            self.group = Group(dict_token["texto"])
        else:
            self.group = Group(dict_token["grupo"])

        self.text = Text(dict_token["texto"])
        self.locale = Locale(
            dict_token["local"]["indice"], dict_token["local"]["linha"])

    def getFormmated(self):
        """Metodo utilizado para formatada o modelo do json."""
        return {"grupo": self.group.group, "texto": self.text.text, "local": {"linha": self.locale.line, "indice": self.locale.index}}


class LL:
    """Classe responsavel por fazer a LL1"""

    def __init__(self, tokens):
        self.table = None

        # Criação da gramatica com as regras de produção do enumciado e variavel inicial igual a 'programa'
        self.grammar = Grammar(productions, "programa")

        # Conversão dos tokens de entrada
        self.tokens = self.__getTokens(tokens)

    def __inizialization(self):
        self.table = Table(self.grammar.productions)
        self.tree = Tree()
        self.error_tree = ErrorTree()
        self.arvore = []

    def __getTokens(self, tokens):
        """Metodo repsosnavel conversão dos tokens de entrada"""

        list_tokens = []

        for token in tokens:
            list_tokens.append(Token(token))

        list_tokens.append(self.__createEndCode(
            (int(tokens[-1]["local"]["linha"]) + 1)))

        return list_tokens

    def __createEndCode(self, line):
        """Metodo responsavel pela criação do token final '$' """

        dict_token = {
            "grupo": "$", "texto": "$",
            "local": {"linha": line, "indice": 0}
        }

        return Token(dict_token)

    def __getNextToken(self, index):
        """Meotdo responsavel por pegar proximo token valido """

        while(index < len(self.tokens)):

            # chamada do validador
            if(self.grammar.isTokenValid(self.tokens[index])):
                return self.tokens[index], index

            index += 1

        # Se retornar NONE, singifica que não existe proximo token valido
        return None, -1

    def parse(self):
        """Metodo responsavel pela criação da arvore LL"""

        self.__inizialization()
        accepted = True
        stack = []
        index = 0

        # Adição dos primeiros token na pilha
        stack.append((self.tokens[-1].group.group, None))
        stack.append(
            (self.grammar.initial_variables.group.group, self.tree.root[0]))

        while len(stack) > 0:

            # pegando elemento no topo da pilha
            top, node = stack[len(stack)-1]

            # Proximo token valido
            current_token, index = self.__getNextToken(index)

            # Index -1 singinfica não existe token valido para processar, logo erro de sintaxe
            if index == -1:
                accepted = False
                break

            # Verifica se é o mesmo token de entrada
            if top == current_token.group.group:
                if(top != "$"):
                    self.tree.includeLeaf(node, current_token)
                stack.pop()
                index = index + 1
            else:
                # Procurando valor da chave na tabela LL
                key = top, current_token.group.group

                # Verificar se terminal do topo da pilha não é aceito
                if key[0] not in self.table.parsingTable or key[1] not in self.table.parsingTable[key[0]]:
                    accepted = False
                    break

                # Pega valor da tabela LL
                value = self.table.parsingTable[key[0]][key[1]]

                # Verificar se palavra Vazia
                if "@" not in value:

                    # Adicinando elemento a arvore
                    list_node = []
                    for element in value:
                        node_children = None
                        if(self.grammar.isTerminalValid(element)):
                            if(top != "$"):
                                node_children = self.tree.createLeaf(node)
                        else:
                            node_children = self.tree.inlude(node, element)
                        list_node.append(node_children)

                    list_node = list_node[::-1]
                    value = value[::-1]

                    # remover topo da pilha
                    stack.pop()

                    # colocar token na pilha
                    for i in range(len(value)):
                        stack.append((value[i], list_node[i]))
                else:
                    stack.pop()

        if not accepted:
            """Caso ocorra um erro de sintaxe, será incluido o erro na lista"""
            self.error_tree.include("Erro de sintaxe")

        return {"arvore": self.tree.root, "erros": self.error_tree.root}


def analisadorSintatico(tokens):
    ll1Table = LL(tokens["tokens"])

    return ll1Table.parse()

# ALERTA: Nao modificar o codigo fonte apos esse aviso


def testaAnalisadorSintatico(tokens, teste):
    # Caso o resultado nao seja igual ao teste
    # ambos sao mostrados e a execucao termina
    resultado = json.dumps(analisadorSintatico(tokens), indent=2)
    teste = json.dumps(teste, indent=2)
    if resultado != teste:
        # Mostra o teste e o resultado lado a lado
        resultadoLinhas = resultado.split('\n')
        testeLinhas = teste.split('\n')
        if len(resultadoLinhas) > len(testeLinhas):
            testeLinhas.extend(
                [' '] * (len(resultadoLinhas)-len(testeLinhas))
            )
        elif len(resultadoLinhas) < len(testeLinhas):
            resultadoLinhas.extend(
                [' '] * (len(testeLinhas)-len(resultadoLinhas))
            )
        linhasEmPares = enumerate(zip(testeLinhas, resultadoLinhas))
        maiorTextoNaLista = str(len(max(testeLinhas, key=len)))
        maiorIndice = str(len(str(len(testeLinhas))))
        titule = '{:<'+maiorIndice+'} + {:<'+maiorTextoNaLista+'} + {}'
        objeto = '{:<'+maiorIndice+'} | {:<'+maiorTextoNaLista+'} | {}'
        print(titule.format('', 'teste', 'resultado'))
        print(objeto.format('', '', ''))
        for indice, (esquerda, direita) in linhasEmPares:
            print(objeto.format(indice, esquerda, direita))
        # Termina a execucao
        print("\n): falha :(")
        quit()


# Tokens que passados para a funcao analisadorSintatico
tokens = {
    "tokens": [
        # Comentario
        {
            "grupo": "comentario", "texto": "-- funcao inicial",
            "local": {"linha": 1, "indice": 0}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 1, "indice": 17}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 2, "indice": 0}
        },
        # Funcao inicio
        {
            "grupo": "identificador", "texto": "inicio",
            "local": {"linha": 3, "indice": 0}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 3, "indice": 6}
        },
        {
            "grupo": "reservado", "texto": "Funcao",
            "local": {"linha": 3, "indice": 7}
        },
        {
            "grupo": "abre-parenteses", "texto": "(",
            "local": {"linha": 3, "indice": 13}
        },
        {
            "grupo": "identificador", "texto": "valor",
            "local": {"linha": 3, "indice": 14}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 3, "indice": 19}
        },
        {
            "grupo": "reservado", "texto": "Logica",
            "local": {"linha": 3, "indice": 20}
        },
        {
            "grupo": "virgula", "texto": ",",
            "local": {"linha": 3, "indice": 26}
        },
        {
            "grupo": "identificador", "texto": "item",
            "local": {"linha": 3, "indice": 27}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 3, "indice": 31}
        },
        {
            "grupo": "reservado", "texto": "Texto",
            "local": {"linha": 3, "indice": 32}
        },
        {
            "grupo": "fecha-parenteses", "texto": ")",
            "local": {"linha": 3, "indice": 37}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 3, "indice": 38}
        },
        {
            "grupo": "reservado", "texto": "Numero",
            "local": {"linha": 3, "indice": 39}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 3, "indice": 45}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 3, "indice": 47}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 3, "indice": 48}
        },
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 4, "indice": 0}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 4, "indice": 1}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 5, "indice": 0}
        },
        # # Funcao tiposDeVariaveis
        # {
        #     "grupo": "identificador", "texto": "tiposDeVariaveis",
        #     "local": {"linha": 6, "indice": 0}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 6, "indice": 16}
        # },
        # {
        #     "grupo": "reservado", "texto": "Funcao",
        #     "local": {"linha": 6, "indice": 17}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 6, "indice": 23}
        # },
        # {
        #     "grupo": "abre-chaves", "texto": "{",
        #     "local": {"linha": 6, "indice": 25}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 6, "indice": 26}
        # },
        # # textoVar:Texto::'#'exemplo##'
        # {
        #     "grupo": "identificador", "texto": "textoVar",
        #     "local": {"linha": 7, "indice": 2}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 7, "indice": 10}
        # },
        # {
        #     "grupo": "reservado", "texto": "Texto",
        #     "local": {"linha": 7, "indice": 11}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 7, "indice": 16}
        # },
        # {
        #     "grupo": "texto", "texto": "'#'exemplo##'",
        #     "local": {"linha": 7, "indice": 18}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 7, "indice": 31}
        # },
        # # numeroVar:Numero::1234
        # {
        #     "grupo": "identificador", "texto": "numeroVar",
        #     "local": {"linha": 8, "indice": 2}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 8, "indice": 11}
        # },
        # {
        #     "grupo": "reservado", "texto": "Numero",
        #     "local": {"linha": 8, "indice": 12}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 8, "indice": 18}
        # },
        # {
        #     "grupo": "numero", "texto": "1234",
        #     "local": {"linha": 8, "indice": 20}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 8, "indice": 24}
        # },
        # # logicoVar:Logico::Sim
        # {
        #     "grupo": "identificador", "texto": "logicoVar",
        #     "local": {"linha": 9, "indice": 2}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 9, "indice": 11}
        # },
        # {
        #     "grupo": "reservado", "texto": "Logico",
        #     "local": {"linha": 9, "indice": 12}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 9, "indice": 18}
        # },
        # {
        #     "grupo": "logico", "texto": "Sim",
        #     "local": {"linha": 9, "indice": 20}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 9, "indice": 23}
        # },
        # # Fecha Funcao
        # {
        #     "grupo": "fecha-chaves", "texto": "}",
        #     "local": {"linha": 10, "indice": 0}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 10, "indice": 1}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 11, "indice": 0}
        # },
        # # Funcao tiposDeFluxoDeControle
        # {
        #     "grupo": "identificador", "texto": "tiposDeFluxoDeControle",
        #     "local": {"linha": 12, "indice": 0}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 12, "indice": 22}
        # },
        # {
        #     "grupo": "reservado", "texto": "Funcao",
        #     "local": {"linha": 12, "indice": 23}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 12, "indice": 29}
        # },
        # {
        #     "grupo": "reservado", "texto": "Logico",
        #     "local": {"linha": 12, "indice": 30}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 12, "indice": 36}
        # },
        # {
        #     "grupo": "abre-chaves", "texto": "{",
        #     "local": {"linha": 12, "indice": 38}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 12, "indice": 39}
        # },
        # # resultado:Logico::Nao
        # {
        #     "grupo": "identificador", "texto": "resultado",
        #     "local": {"linha": 13, "indice": 2}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 13, "indice": 11}
        # },
        # {
        #     "grupo": "reservado", "texto": "Logico",
        #     "local": {"linha": 13, "indice": 12}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 13, "indice": 18}
        # },
        # {
        #     "grupo": "logico", "texto": "Nao",
        #     "local": {"linha": 13, "indice": 20}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 13, "indice": 23}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 14, "indice": 0}
        # },
        # # contador:Numero::0
        # {
        #     "grupo": "identificador", "texto": "contador",
        #     "local": {"linha": 23, "indice": 2}
        # },
        # {
        #     "grupo": "dois-pontos", "texto": ":",
        #     "local": {"linha": 23, "indice": 10}
        # },
        # {
        #     "grupo": "reservado", "texto": "Numero",
        #     "local": {"linha": 23, "indice": 11}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 23, "indice": 17}
        # },
        # {
        #     "grupo": "numero", "texto": "0",
        #     "local": {"linha": 23, "indice": 19}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 23, "indice": 20}
        # },
        # # enquanto(contador < 10){
        # {
        #     "grupo": "reservado", "texto": "enquanto",
        #     "local": {"linha": 24, "indice": 2}
        # },
        # {
        #     "grupo": "abre-parenteses", "texto": "(",
        #     "local": {"linha": 24, "indice": 10}
        # },
        # {
        #     "grupo": "identificador", "texto": "contador",
        #     "local": {"linha": 24, "indice": 11}
        # },
        # {
        #     "grupo": "operador-menor", "texto": "<",
        #     "local": {"linha": 24, "indice": 20}
        # },
        # {
        #     "grupo": "numero", "texto": "10",
        #     "local": {"linha": 24, "indice": 22}
        # },
        # {
        #     "grupo": "fecha-parenteses", "texto": ")",
        #     "local": {"linha": 24, "indice": 24}
        # },
        # {
        #     "grupo": "abre-chaves", "texto": "{",
        #     "local": {"linha": 24, "indice": 25}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 24, "indice": 26}
        # },
        # {
        #     "grupo": "identificador", "texto": "contador",
        #     "local": {"linha": 25, "indice": 4}
        # },
        # {
        #     "grupo": "atribuicao", "texto": "::",
        #     "local": {"linha": 25, "indice": 12}
        # },
        # {
        #     "grupo": "identificador", "texto": "contador",
        #     "local": {"linha": 25, "indice": 14}
        # },
        # {
        #     "grupo": "operador-mais", "texto": "+",
        #     "local": {"linha": 25, "indice": 23}
        # },
        # {
        #     "grupo": "texto", "texto": "'a'",
        #     "local": {"linha": 25, "indice": 25}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 25, "indice": 28}
        # },
        # {
        #     "grupo": "fecha-chaves", "texto": "}",
        #     "local": {"linha": 26, "indice": 2}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 26, "indice": 3}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 27, "indice": 0}
        # },
        # # Fecha Funcao
        # {
        #     "grupo": "reservado", "texto": "retorna",
        #     "local": {"linha": 28, "indice": 2}
        # },
        # {
        #     "grupo": "identificador", "texto": "resultado",
        #     "local": {"linha": 28, "indice": 10}
        # },
        # {
        #     "grupo": "quebra-linha", "texto": "\n",
        #     "local": {"linha": 28, "indice": 19}
        # },
        # {
        #     "grupo": "fecha-chaves", "texto": "}",
        #     "local": {"linha": 29, "indice": 0}
        # }
    ], "erros": []
}

# Resultado esperado da execucao da funcao analisadorSintatico
teste = {
    "arvore": [
        {
            "tipo": "regra",
            "grupo": "programa",
            "ramo": [
                {
                    "tipo": "regra",
                    "grupo": "funcao",
                    "ramo": [
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "identificador", "texto": "inicio",
                                "local": {"linha": 3, "indice": 0}
                            }
                        },
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "dois-pontos", "texto": ":",
                                "local": {"linha": 3, "indice": 6}
                            }
                        },
                        {
                            "tipo": "regra",
                            "grupo": "tipo-funcao",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "reservado", "texto": "Funcao",
                                        "local": {"linha": 3, "indice": 7}
                                    }
                                }
                            ]
                        },
                        {
                            "tipo": "regra",
                            "grupo": "funcao-parametros",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "abre-parenteses", "texto": "(",
                                        "local": {"linha": 3, "indice": 13}
                                    }
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "parametro-item",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "valor",
                                                "local": {"linha": 3, "indice": 14}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 3, "indice": 19}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Logica",
                                                        "local": {"linha": 3, "indice": 20}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "virgula", "texto": ",",
                                        "local": {"linha": 3, "indice": 26}
                                    }
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "parametro-item",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "item",
                                                "local": {"linha": 3, "indice": 27}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 3, "indice": 31}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Texto",
                                                        "local": {"linha": 3, "indice": 32}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "fecha-parenteses", "texto": ")",
                                        "local": {"linha": 3, "indice": 37}
                                    }
                                }
                            ]
                        },
                        {
                            "tipo": "regra",
                            "grupo": "funcao-retorno",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "dois-pontos", "texto": ":",
                                        "local": {"linha": 3, "indice": 38}
                                    }
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "tipo",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "reservado", "texto": "Numero",
                                                "local": {"linha": 3, "indice": 39}
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "atribuicao", "texto": "::",
                                "local": {"linha": 3, "indice": 45}
                            }
                        },
                        {
                            "tipo": "regra",
                            "grupo": "funcao-corpo",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "abre-chaves", "texto": "{",
                                        "local": {"linha": 3, "indice": 47}
                                    }
                                },
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "fecha-chaves", "texto": "}",
                                        "local": {"linha": 4, "indice": 0}
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "tipo": "regra",
                    "grupo": "funcao",
                    "ramo": [
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "identificador", "texto": "tiposDeVariaveis",
                                "local": {"linha": 6, "indice": 0}
                            }
                        },
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "dois-pontos", "texto": ":",
                                "local": {"linha": 6, "indice": 16}
                            }
                        },
                        {
                            "tipo": "regra",
                            "grupo": "tipo-funcao",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "reservado", "texto": "Funcao",
                                        "local": {"linha": 6, "indice": 17}
                                    }
                                }
                            ]
                        },
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "atribuicao", "texto": "::",
                                "local": {"linha": 6, "indice": 23}
                            }
                        },
                        {
                            "tipo": "regra",
                            "grupo": "funcao-corpo",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "abre-chaves", "texto": "{",
                                        "local": {"linha": 6, "indice": 25}
                                    }
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "variavel",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "textoVar",
                                                "local": {"linha": 7, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 7, "indice": 10}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Texto",
                                                        "local": {"linha": 7, "indice": 11}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "atribuicao", "texto": "::",
                                                "local": {"linha": 7, "indice": 16}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "expressao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "texto", "texto": "'#'exemplo##'",
                                                        "local": {"linha": 7, "indice": 18}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "variavel",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "numeroVar",
                                                "local": {"linha": 8, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 8, "indice": 11}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Numero",
                                                        "local": {"linha": 8, "indice": 12}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "atribuicao", "texto": "::",
                                                "local": {"linha": 8, "indice": 18}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "expressao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "numero", "texto": "1234",
                                                        "local": {"linha": 8, "indice": 20}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "variavel",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "logicoVar",
                                                "local": {"linha": 9, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 9, "indice": 11}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Logico",
                                                        "local": {"linha": 9, "indice": 12}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "atribuicao", "texto": "::",
                                                "local": {"linha": 9, "indice": 18}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "expressao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "logico", "texto": "Sim",
                                                        "local": {"linha": 9, "indice": 20}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "fecha-chaves", "texto": "}",
                                        "local": {"linha": 10, "indice": 0}
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "tipo": "regra",
                    "grupo": "funcao",
                    "ramo": [
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "identificador", "texto": "tiposDeFluxoDeControle",
                                "local": {"linha": 12, "indice": 0}
                            }
                        },
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "dois-pontos", "texto": ":",
                                "local": {"linha": 12, "indice": 22}
                            }
                        },
                        {
                            "tipo": "regra",
                            "grupo": "tipo-funcao",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "reservado", "texto": "Funcao",
                                        "local": {"linha": 12, "indice": 23}
                                    }
                                }
                            ]
                        },
                        {
                            "tipo": "regra",
                            "grupo": "funcao-retorno",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "dois-pontos", "texto": ":",
                                        "local": {"linha": 12, "indice": 29}
                                    }
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "tipo",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "reservado", "texto": "Logico",
                                                "local": {"linha": 12, "indice": 30}
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "tipo": "token",
                            "folha": {
                                "grupo": "atribuicao", "texto": "::",
                                "local": {"linha": 12, "indice": 36}
                            }
                        },
                        {
                            "tipo": "regra",
                            "grupo": "funcao-corpo",
                            "ramo": [
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "abre-chaves", "texto": "{",
                                        "local": {"linha": 12, "indice": 38}
                                    }
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "variavel",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "resultado",
                                                "local": {"linha": 13, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 13, "indice": 11}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Logico",
                                                        "local": {"linha": 13, "indice": 12}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "atribuicao", "texto": "::",
                                                "local": {"linha": 13, "indice": 18}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "expressao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "logico", "texto": "Nao",
                                                        "local": {"linha": 13, "indice": 20}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "variavel",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "identificador", "texto": "contador",
                                                "local": {"linha": 23, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "dois-pontos", "texto": ":",
                                                "local": {"linha": 23, "indice": 10}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "tipo",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "reservado", "texto": "Numero",
                                                        "local": {"linha": 23, "indice": 11}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "atribuicao", "texto": "::",
                                                "local": {"linha": 23, "indice": 17}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "expressao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "numero", "texto": "0",
                                                        "local": {"linha": 23, "indice": 19}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "repeticao",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "reservado", "texto": "enquanto",
                                                "local": {"linha": 24, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "condicao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "abre-parenteses", "texto": "(",
                                                        "local": {"linha": 24, "indice": 10}
                                                    }
                                                },
                                                {
                                                    "tipo": "regra",
                                                    "grupo": "expressao",
                                                    "ramo": [
                                                        {
                                                            "tipo": "token",
                                                            "folha": {
                                                                "grupo": "identificador", "texto": "contador",
                                                                "local": {"linha": 24, "indice": 11}
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "operador-menor", "texto": "<",
                                                        "local": {"linha": 24, "indice": 20}
                                                    }
                                                },
                                                {
                                                    "tipo": "regra",
                                                    "grupo": "expressao",
                                                    "ramo": [
                                                        {
                                                            "tipo": "token",
                                                            "folha": {
                                                                "grupo": "numero", "texto": "10",
                                                                "local": {"linha": 24, "indice": 22}
                                                            }
                                                        }
                                                    ]
                                                },
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "fecha-parenteses", "texto": ")",
                                                        "local": {"linha": 24, "indice": 24}
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "repeticao-corpo",
                                            "ramo": [
                                                {
                                                    "tipo": "regra",
                                                    "grupo": "atribuicao",
                                                    "ramo": [
                                                        {
                                                            "tipo": "token",
                                                            "folha": {
                                                                "grupo": "identificador", "texto": "contador",
                                                                "local": {"linha": 25, "indice": 4}
                                                            }
                                                        },
                                                        {
                                                            "tipo": "token",
                                                            "folha": {
                                                                "grupo": "atribuicao", "texto": "::",
                                                                "local": {"linha": 25, "indice": 12}
                                                            }
                                                        },
                                                        {
                                                            "tipo": "regra",
                                                            "grupo": "expressao",
                                                            "ramo": [
                                                                {
                                                                    "tipo": "token",
                                                                    "folha": {
                                                                        "grupo": "identificador", "texto": "contador",
                                                                        "local": {"linha": 25, "indice": 14}
                                                                    }
                                                                },
                                                                {
                                                                    "tipo": "token",
                                                                    "folha": {
                                                                        "grupo": "operador-mais", "texto": "+",
                                                                        "local": {"linha": 25, "indice": 23}
                                                                    }
                                                                },
                                                                {
                                                                    "tipo": "token",
                                                                    "folha": {
                                                                        "grupo": "texto", "texto": "'a'",
                                                                        "local": {"linha": 25, "indice": 25}
                                                                    }
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "regra",
                                    "grupo": "retorno",
                                    "ramo": [
                                        {
                                            "tipo": "token",
                                            "folha": {
                                                "grupo": "reservado", "texto": "retorna",
                                                "local": {"linha": 28, "indice": 2}
                                            }
                                        },
                                        {
                                            "tipo": "regra",
                                            "grupo": "expressao",
                                            "ramo": [
                                                {
                                                    "tipo": "token",
                                                    "folha": {
                                                        "grupo": "identificador", "texto": "resultado",
                                                        "local": {"linha": 28, "indice": 10}
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                {
                                    "tipo": "token",
                                    "folha": {
                                        "grupo": "fecha-chaves", "texto": "}",
                                        "local": {"linha": 29, "indice": 0}
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ],
    "erros": []
}

# Execucao do teste que valida a funcao testaAnalisadorSintatico
testaAnalisadorSintatico(tokens, teste)
# print(analisadorSintatico(tokens))
print("(: sucesso :)")

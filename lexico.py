import json


class Text:
    """Classe referente ao valor do token."""

    def __init__(self, text):
        self.text = text


class Group:
    """Classe referente ao grupo do token."""

    def __init__(self, gruop):
        self.gruop = gruop


class Locale:
    """Classe referente a localização do token."""

    def __init__(self, index, line):
        self.index = index
        self.line = line


class Token:
    """Classe referente ao token."""

    def __init__(self, gruop, text):
        self.gruop = Group(gruop)
        self.text = Text(text)

    def setLocale(self, index, line):
        self.locale = Locale(index, line)

    def getFormmated(self):
        """Metodo utilizado para formatada o modelo do json."""
        return {"grupo": self.gruop.gruop, "texto": self.text.text, "local": {"linha": self.locale.line, "indice": self.locale.index}}


class ErrorToken:
    """Classe referente ao token de erro."""

    def __init__(self, text):
        self.text = Text(text)

    def setLocale(self, index, line):
        self.locale = Locale(index, line)

    def getFormmated(self):
        """Metodo utilizado para formatada o modelo do json."""
        return {"texto": self.text.text, "local": {"linha": self.locale.line, "indice": self.locale.index}}


class Tokenizer:
    """Classe central para gerenciamento da criação do token."""

    def __init__(self, program):
        self.program = program
        self.__resetAttributes()

    def __resetAttributes(self):
        """Metodo utilizado para resetar os atributos utilizados durante o token central para gerenciamento da criação do token """
        self.tokens = []
        self.erros = []
        self.pilha = []
        self.index_buffer_string = 0
        self.is_comentario = False
        self.line = 1
        self.index = 0
        self.if_operadores = False
        self.is_texto = False
        self.is_escape = False

    def __toJson(self, array_token):
        """Metodo responsavel pela converção do array para o json formatada."""
        return [elem.getFormmated() for elem in array_token]

    def __removeIdentacao(self):
        """Metodo responsavel pela remoção do espaço adicionado na identação dentro dos '{' '}' """
        if(len(self.pilha) > 1 and self.pilha[-2] == "{" and self.pilha[-1] == " "):
            self.pilha = self.pilha[:-1]
            self.index -= 1

    def __validedEscape(self, char):
        """Metodo responsavel pela validação se o caracter é um escape."""
        return char == "#" and not self.is_escape

    def __isValidedCaracteres(self, char):
        """Metodo responsavel pela validação de caracteres desconhecidos pela linguagem."""
        if(char in "@"):
            return self.__getDesconhecido(char)

    def __isOperadores(self, char):
        """Metodo responsavel pela validação se o caracter é um operadores de atribuição da linguagem."""
        return len(self.pilha) > 0 and self.pilha[-1] == ":" and char == ":"

    def __isDelimitadores(self, char):
        """Metodo responsavel pela validação se o caracter é um delimitador da linguagem."""
        return char in r"(){},"

    def __isDelimitadoresTexto(self, char):
        """Metodo responsavel pela validação se o caracter é um delimitador de texto da linguagem."""
        return char in r"'"

    def __isIfOperadores(self, char):
        """Metodo responsavel pela checagem se o operador é de atirbuição ou delimitador da linguagem."""
        return char == ":"

    def __isOperadoresMatematicos(self, char):
        """Metodo responsavel pela validação se o caracter é um operador matematico da linguagem."""
        return char in "<>+="

    def __isQuebraLinha(self, char):
        """Metodo responsavel pela validação se o caracter é uma quebra de linha da linguagem."""
        return char == r'\n'

    def __isSpace(self, char):
        """Metodo responsavel pela validação se o caracter é um espaço em branco não utilizado por texto ou comentario."""
        return char == " " and not self.is_comentario and not self.is_texto

    def __isComentario(self, char):
        """Metodo responsavel pela validação se um inicio de comentario."""
        return len(self.pilha) > 0 and self.pilha[-1] == '-' and char == '-'

    def __getTokenDesconhecido(self, char):
        """Metodo responsavel pela criação do token de desconhecido."""
        return Token("desconhecido", char)

    def __getQuebraLinha(self, char):
        """Metodo responsavel pela criação do token de quebra de linha."""
        return Token("quebra-linha", char)

    def __getOperadores(self, char):
        """Metodo responsavel pela criação dos tokens de atribuição."""
        if(char == ':'):
            return Token('atribuicao', '::')

    def __getOperadoresMatematicos(self, char):
        """Metodo responsavel pela criação dos tokens de operadores matematicos."""
        if(char == '<'):
            return Token('operador-menor', char)
        elif(char == '>'):
            return Token('operador-maior', char)
        elif(char == '+'):
            return Token('operador-mais', char)
        elif(char == '='):
            return Token('operador-igual', char)

    def __getTiposPalavra(self, text):
        """Metodo responsavel pela sub-divisão entre as palvaras reservadas, numero e identificadores."""
        if(text.isnumeric()):
            return Token('numero', text)
        elif(text == "Sim" or text == "Nao"):
            return Token('logico', text)
        elif(text[0].isupper() or text == "se" or text == "enquanto" or text == "retorna"):
            return Token("reservado", text)
        return Token("identificador", text)

    def __getDesconhecido(self, char):
        """Metodo responsavel pela criação do token de erro."""
        return ErrorToken("simbolo, {}, desconhecido".format(char))

    def __unionIdentificadores(self):
        """Metodo responsavel pela possiveis uniones de mais mais de um token, dependedo da regra."""
        new_tokens = []
        cont_pass = 0
        if(len(self.tokens) > 3):
            for index, _ in enumerate(self.tokens[:-1]):
                if((index+2) < len(self.tokens) and self.tokens[index].text.text == "se" and self.tokens[index+1].text.text == "nao"):
                    """ Validação utiliza uma comparaão se existe a ordem dos tokens SE, NAO e SE, se existir, 
                    ele ira criar um novo utilizando o 'se nao se' """
                    if(self.tokens[index+2].text.text == "se"):
                        """Comparação utilizada na regra do 'SE NAO SE'."""
                        token_old = self.tokens[index]
                        token = Token("reservado", "se nao se")
                        token.locale = token_old.locale
                        new_tokens.append(token)
                        cont_pass += 2
                    else:
                        """Comparação utilizada na regra do 'SE NAO'."""
                        token_old = self.tokens[index]
                        token = Token("reservado", "se nao")
                        token.locale = token_old.locale
                        new_tokens.append(token)
                        cont_pass += 1
                elif((index+2) < len(self.tokens) and self.tokens[index].text.text == "!" and self.tokens[index+1].text.text == "="):
                    """Comparação utilizada na regra do '!='."""
                    token_old = self.tokens[index]
                    token = Token("operador-diferente", "!=")
                    token.locale = token_old.locale
                    new_tokens.append(token)
                    cont_pass += 1
                elif(cont_pass == 0):
                    new_tokens.append(self.tokens[index])
                else:
                    cont_pass -= 1
        return new_tokens

    def __getDelimitadores(self, char):
        """Metodo responsavel pela crição dos token delimitadores da linguagem."""
        if(char == '('):
            return Token("abre-parenteses", char)
        elif(char == ')'):
            return Token("fecha-parenteses", char)
        elif(char == ':'):
            return Token("dois-pontos", char)
        elif(char == '{'):
            return Token("abre-chaves", char)
        elif(char == '}'):
            return Token("fecha-chaves", char)
        elif(char == ','):
            return Token("virgula", char)

    def __getTexto(self):
        """Metodo responsavel pela crição do token de texto."""
        jail = self.pilha[self.index_buffer_string:]
        jail = "".join(jail)
        self.pilha = self.pilha[:-len(jail)]
        return Token("texto", jail)

    def __getCadeiaCaracteresComentario(self):
        """Metodo responsavel pela crição do token de comentario."""
        jail = []
        pilha_reverse = self.pilha[::-1]

        """ Metodo utiliza uma busca na pilha procurando o 
        caracter de inicio de comentario, a pilha necessitou ser invertida apenas para facilitar o desenvolvimento """
        for index, char in enumerate(pilha_reverse[:-1]):
            if(pilha_reverse[index] == "-" and pilha_reverse[index+1] == "-"):
                jail.append(pilha_reverse[index])
                jail.append(pilha_reverse[index+1])
                break
            else:
                jail.append(char)

        jail = "".join(jail[::-1])
        self.pilha = self.pilha[:-len(jail)]
        return Token("comentario", jail)

    def __getCadeiaCaracteres(self):
        """Metodo responsavel pela crição do token de cadeia de caracteres, sendo diferenciado 
        pelo retorno do metodo de Palvras."""
        jail = []

        """ Metodo utiliza atraves da busca na pilha por caracteres delimitadores,
         espaco ou operadores de atribuição, para representar o inicio de umTEXTO"""
        for char in self.pilha[::-1]:

            if(self.__isDelimitadores(char) or char == " " or char == ":"):
                break
            else:
                jail.append(char)

        jail = "".join(jail[::-1])

        if(len(jail) == 0):
            return None
        else:
            self.pilha = self.pilha[:-len(jail)]
            return self.__getTiposPalavra(jail)

    def __generateCadeiaCaracteres(self):
        """Metodo responsavel pela geração dos tipos de cadeias de caracteres 
        (Comentario | Texto | Identificadores | Reservados)."""
        if(self.is_comentario):
            self.is_comentario = False
            token = self.__getCadeiaCaracteresComentario()
        else:
            token = self.__getCadeiaCaracteres()
        if(token is not None):
            token.setLocale(self.index-len(token.text.text), self.line)
            self.tokens.append(token)

    def __generateDelimitadores(self, char):
        """Metodo responsavel pela geração dos delimitadores"""
        token = self.__getDelimitadores(char)
        token.setLocale(self.index, self.line)
        self.tokens.append(token)

    def __generateOperadores(self, char):
        """Metodo responsavel pela geração dos operadores de atribuição"""
        token = self.__getOperadores(char)
        token.setLocale(self.index, self.line)
        self.tokens.append(token)
        self.pilha = self.pilha[:-1]

    def __generateOperadoresMatematicos(self, char):
        """Metodo responsavel pela geração dos operadores matematicos"""
        token = self.__getOperadoresMatematicos(char)
        token.setLocale(self.index, self.line)
        self.tokens.append(token)
        self.pilha = self.pilha[:-1]

    def __generateCadeiaCaracteresComDelimitadores(self, char):
        """Metodo responsavel pela geração da cadeia de caracteres que está seguida de um delimitador"""
        self.__generateCadeiaCaracteres()
        self.__generateDelimitadores(char)

    def __generateCadeiaCaracteresComOperadores(self, char):
        """Metodo responsavel pela geração da cadeia de caracteres que está seguida de um operador de atribuição"""
        self.__generateCadeiaCaracteres()
        self.__generateOperadores(char)

    def __generateCadeiaCaracteresComOperadoresMatematicos(self, char):
        """Metodo responsavel pela geração da cadeia de caracteres que está seguida de um operador matematico"""
        self.__generateCadeiaCaracteres()
        self.__generateOperadoresMatematicos(char)

    def __generateCadeiaCaracteresTexto(self, char):
        """Metodo responsavel pela geração da cadeia de carcteres"""
        token = self.__getTexto()
        if(token is not None):
            token.setLocale(self.index-len(str(token.text.text))+1, self.line)
            self.tokens.append(token)

    def __generateQuebraLinha(self):
        """Metodo responsavel pela geração da quebra de linhas"""
        self.__generateCadeiaCaracteres()
        token = self.__getQuebraLinha("\n")
        token.setLocale(self.index, self.line)
        self.tokens.append(token)

    def getTokens(self):
        """Metodo central responsavel pelo fluxo da Tokenizer"""

        self.__resetAttributes()

        for char_lines in self.program.splitlines():
            for char in char_lines:

                """Primeira Validação se caracter é valido"""
                erro_token = self.__isValidedCaracteres(char)
                if(erro_token is not None):
                    token = self.__getTokenDesconhecido(char)
                    token.setLocale(self.index, self.line)
                    self.tokens.append(token)
                    erro_token.setLocale(self.index, self.line)
                    self.erros.append(erro_token)
                else:

                    if(self.__validedEscape(char)):
                        """Segunda Validação se caracter é de escape"""
                        self.is_escape = True
                        self.pilha.append(char)
                    elif(self.is_escape):
                        self.is_escape = False
                        self.pilha.append(char)
                    else:

                        if(self.__isComentario(char)):
                            """Terceira Validação se caracter é de inicio de comentario"""
                            self.is_comentario = True

                        if(not self.is_comentario and not self.is_texto and self.__isDelimitadoresTexto(char)):
                            """Quarta Validação se caracter é de inicio de Texto"""
                            self.is_texto = True
                            self.index_buffer_string = len(self.pilha)
                            self.pilha.append(char)
                        elif(self.is_texto and self.__isDelimitadoresTexto(char)):
                            self.pilha.append(char)
                            self.__generateCadeiaCaracteresTexto(char)
                            self.is_texto = False
                        elif(self.is_texto):
                            self.pilha.append(char)
                        else:

                            if(self.__isIfOperadores(char)):
                                """Quinta Validação se caracter é um possivel operador de atribuição"""

                                if(self.if_operadores):
                                    self.if_operadores = False

                                    if(self.__isOperadores(char)):
                                        """Se for de operador de atribuição utilizar fluxo de ::"""
                                        pilha_antiga = self.pilha.pop()
                                        self.pilha = self.pilha[:-1]
                                        self.index -= 1
                                        self.__generateCadeiaCaracteresComOperadores(
                                            pilha_antiga)
                                        self.index += 1
                                    else:
                                        """Se não utilizar fluxo delimitadores"""
                                        pilha_antiga = self.pilha.pop()
                                        self.pilha = self.pilha[:-1]
                                        self.__generateCadeiaCaracteresComDelimitadores(
                                            pilha_antiga)

                                else:
                                    self.pilha.append(char)
                                    self.if_operadores = True

                            elif(self.if_operadores):
                                """Sexta Validação se caracter é um demilitador"""
                                pilha_antiga = self.pilha.pop()
                                self.pilha = self.pilha[:-1]
                                self.index -= 1
                                self.__generateCadeiaCaracteresComDelimitadores(
                                    pilha_antiga)
                                self.index += 1
                                self.if_operadores = False

                            """ Se caracter não se encaixar na validação que necessitam validar 
                            junto com a pilha, ele será validado novamente como um dos TIPOS abaixo """

                            if(self.__isDelimitadores(char)):
                                """Primeira Validação se caracter é um demilitador"""
                                self.__generateCadeiaCaracteresComDelimitadores(
                                    char)
                            elif(self.__isOperadoresMatematicos(char)):
                                """Segunda Validação se caracter é um operador matematico"""
                                self.__generateCadeiaCaracteresComOperadoresMatematicos(
                                    char)
                            elif(self.__isSpace(char)):
                                """Terceira Validação se caracter é um espaço não utilizado em Texto ou comentario"""
                                self.__generateCadeiaCaracteres()
                            else:
                                self.pilha.append(char)

                """Remove Identação dos '{' '}'"""
                self.__removeIdentacao()
                self.index += 1

            """Gerar quebra de linha """
            self.__generateQuebraLinha()

            self.line += 1
            self.index = 0

        self.tokens = self.__unionIdentificadores()
        return {"tokens": self.__toJson(self.tokens), "erros": self.__toJson(self.erros)}


def analisadorLexico(programa):
    tokenizer = Tokenizer(programa)
    return tokenizer.getTokens()
# ALERTA: Nao modificar o codigo fonte apos esse aviso


def testaAnalisadorLexico(programa, teste):
    # Caso o resultado nao seja igual ao teste
    # ambos sao mostrados e a execucao termina
    resultado = json.dumps(analisadorLexico(programa), indent=2)
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


# Programa que passdo para a funcao analisadorLexico
programa = """-- funcao inicial

inicio:Funcao(valor:Logica,item:Texto):Numero::{
}

tiposDeVariaveis:Funcao::{
  textoVar:Texto::'#'exemplo##'
  numeroVar:Numero::1234
  logicoVar:Logico::Sim
}

tiposDeFluxoDeControle:Funcao:Logico::{
  resultado:Logico::Nao

  se(1 = 2){
    resultado::Nao
  } se nao se('a' != 'a'){
    resultado::Nao
  } se nao @ {
    resultado::Sim
  }

  contador:Numero::0
  enquanto(contador < 10){
    contador::contador + 'a'
  }

  retorna resultado
}"""

# Resultado esperado da execucao da funcao analisadorLexico
# passando paea ela o programa anterior
teste = {
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
        # Funcao tiposDeVariaveis
        {
            "grupo": "identificador", "texto": "tiposDeVariaveis",
            "local": {"linha": 6, "indice": 0}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 6, "indice": 16}
        },
        {
            "grupo": "reservado", "texto": "Funcao",
            "local": {"linha": 6, "indice": 17}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 6, "indice": 23}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 6, "indice": 25}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 6, "indice": 26}
        },
        # textoVar:Texto::'#'exemplo##'
        {
            "grupo": "identificador", "texto": "textoVar",
            "local": {"linha": 7, "indice": 2}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 7, "indice": 10}
        },
        {
            "grupo": "reservado", "texto": "Texto",
            "local": {"linha": 7, "indice": 11}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 7, "indice": 16}
        },
        {
            "grupo": "texto", "texto": "'#'exemplo##'",
            "local": {"linha": 7, "indice": 18}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 7, "indice": 31}
        },
        # numeroVar:Numero::1234
        {
            "grupo": "identificador", "texto": "numeroVar",
            "local": {"linha": 8, "indice": 2}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 8, "indice": 11}
        },
        {
            "grupo": "reservado", "texto": "Numero",
            "local": {"linha": 8, "indice": 12}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 8, "indice": 18}
        },
        {
            "grupo": "numero", "texto": "1234",
            "local": {"linha": 8, "indice": 20}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 8, "indice": 24}
        },
        # logicoVar:Logico::Sim
        {
            "grupo": "identificador", "texto": "logicoVar",
            "local": {"linha": 9, "indice": 2}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 9, "indice": 11}
        },
        {
            "grupo": "reservado", "texto": "Logico",
            "local": {"linha": 9, "indice": 12}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 9, "indice": 18}
        },
        {
            "grupo": "logico", "texto": "Sim",
            "local": {"linha": 9, "indice": 20}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 9, "indice": 23}
        },
        # Fecha Funcao
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 10, "indice": 0}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 10, "indice": 1}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 11, "indice": 0}
        },
        # Funcao tiposDeFluxoDeControle
        {
            "grupo": "identificador", "texto": "tiposDeFluxoDeControle",
            "local": {"linha": 12, "indice": 0}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 12, "indice": 22}
        },
        {
            "grupo": "reservado", "texto": "Funcao",
            "local": {"linha": 12, "indice": 23}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 12, "indice": 29}
        },
        {
            "grupo": "reservado", "texto": "Logico",
            "local": {"linha": 12, "indice": 30}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 12, "indice": 36}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 12, "indice": 38}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 12, "indice": 39}
        },
        # resultado:Logico::Nao
        {
            "grupo": "identificador", "texto": "resultado",
            "local": {"linha": 13, "indice": 2}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 13, "indice": 11}
        },
        {
            "grupo": "reservado", "texto": "Logico",
            "local": {"linha": 13, "indice": 12}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 13, "indice": 18}
        },
        {
            "grupo": "logico", "texto": "Nao",
            "local": {"linha": 13, "indice": 20}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 13, "indice": 23}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 14, "indice": 0}
        },
        # se(1 = 2){
        {
            "grupo": "reservado", "texto": "se",
            "local": {"linha": 15, "indice": 2}
        },
        {
            "grupo": "abre-parenteses", "texto": "(",
            "local": {"linha": 15, "indice": 4}
        },
        {
            "grupo": "numero", "texto": "1",
            "local": {"linha": 15, "indice": 5}
        },
        {
            "grupo": "operador-igual", "texto": "=",
            "local": {"linha": 15, "indice": 7}
        },
        {
            "grupo": "numero", "texto": "2",
            "local": {"linha": 15, "indice": 9}
        },
        {
            "grupo": "fecha-parenteses", "texto": ")",
            "local": {"linha": 15, "indice": 10}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 15, "indice": 11}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 15, "indice": 12}
        },
        {
            "grupo": "identificador", "texto": "resultado",
            "local": {"linha": 16, "indice": 4}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 16, "indice": 13}
        },
        {
            "grupo": "logico", "texto": "Nao",
            "local": {"linha": 16, "indice": 15}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 16, "indice": 18}
        },
        # } se nao se('a' != 'a'){
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 17, "indice": 2}
        },
        {
            "grupo": "reservado", "texto": "se nao se",
            "local": {"linha": 17, "indice": 4}
        },
        {
            "grupo": "abre-parenteses", "texto": "(",
            "local": {"linha": 17, "indice": 13}
        },
        {
            "grupo": "texto", "texto": "'a'",
            "local": {"linha": 17, "indice": 14}
        },
        {
            "grupo": "operador-diferente", "texto": "!=",
            "local": {"linha": 17, "indice": 18}
        },
        {
            "grupo": "texto", "texto": "'a'",
            "local": {"linha": 17, "indice": 21}
        },
        {
            "grupo": "fecha-parenteses", "texto": ")",
            "local": {"linha": 17, "indice": 24}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 17, "indice": 25}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 17, "indice": 26}
        },
        {
            "grupo": "identificador", "texto": "resultado",
            "local": {"linha": 18, "indice": 4}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 18, "indice": 13}
        },
        {
            "grupo": "logico", "texto": "Nao",
            "local": {"linha": 18, "indice": 15}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 18, "indice": 18}
        },
        # } se nao @ {
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 19, "indice": 2}
        },
        {
            "grupo": "reservado", "texto": "se nao",
            "local": {"linha": 19, "indice": 4}
        },
        {
            "grupo": "desconhecido", "texto": "@",
            "local": {"linha": 19, "indice": 11}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 19, "indice": 13}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 19, "indice": 14}
        },
        {
            "grupo": "identificador", "texto": "resultado",
            "local": {"linha": 20, "indice": 4}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 20, "indice": 13}
        },
        {
            "grupo": "logico", "texto": "Sim",
            "local": {"linha": 20, "indice": 15}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 20, "indice": 18}
        },
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 21, "indice": 2}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 21, "indice": 3}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 22, "indice": 0}
        },
        # contador:Numero::0
        {
            "grupo": "identificador", "texto": "contador",
            "local": {"linha": 23, "indice": 2}
        },
        {
            "grupo": "dois-pontos", "texto": ":",
            "local": {"linha": 23, "indice": 10}
        },
        {
            "grupo": "reservado", "texto": "Numero",
            "local": {"linha": 23, "indice": 11}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 23, "indice": 17}
        },
        {
            "grupo": "numero", "texto": "0",
            "local": {"linha": 23, "indice": 19}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 23, "indice": 20}
        },
        # enquanto(contador < 10){
        {
            "grupo": "reservado", "texto": "enquanto",
            "local": {"linha": 24, "indice": 2}
        },
        {
            "grupo": "abre-parenteses", "texto": "(",
            "local": {"linha": 24, "indice": 10}
        },
        {
            "grupo": "identificador", "texto": "contador",
            "local": {"linha": 24, "indice": 11}
        },
        {
            "grupo": "operador-menor", "texto": "<",
            "local": {"linha": 24, "indice": 20}
        },
        {
            "grupo": "numero", "texto": "10",
            "local": {"linha": 24, "indice": 22}
        },
        {
            "grupo": "fecha-parenteses", "texto": ")",
            "local": {"linha": 24, "indice": 24}
        },
        {
            "grupo": "abre-chaves", "texto": "{",
            "local": {"linha": 24, "indice": 25}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 24, "indice": 26}
        },
        {
            "grupo": "identificador", "texto": "contador",
            "local": {"linha": 25, "indice": 4}
        },
        {
            "grupo": "atribuicao", "texto": "::",
            "local": {"linha": 25, "indice": 12}
        },
        {
            "grupo": "identificador", "texto": "contador",
            "local": {"linha": 25, "indice": 14}
        },
        {
            "grupo": "operador-mais", "texto": "+",
            "local": {"linha": 25, "indice": 23}
        },
        {
            "grupo": "texto", "texto": "'a'",
            "local": {"linha": 25, "indice": 25}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 25, "indice": 28}
        },
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 26, "indice": 2}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 26, "indice": 3}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 27, "indice": 0}
        },
        # Fecha Funcao
        {
            "grupo": "reservado", "texto": "retorna",
            "local": {"linha": 28, "indice": 2}
        },
        {
            "grupo": "identificador", "texto": "resultado",
            "local": {"linha": 28, "indice": 10}
        },
        {
            "grupo": "quebra-linha", "texto": "\n",
            "local": {"linha": 28, "indice": 19}
        },
        {
            "grupo": "fecha-chaves", "texto": "}",
            "local": {"linha": 29, "indice": 0}
        }
    ], "erros": [
        {
            "texto": "simbolo, @, desconhecido",
            "local": {"linha": 19, "indice": 11}
        }
    ]
}

# Execucao do teste que valida a funcao analisadorLexico
testaAnalisadorLexico(programa, teste)

print("(: sucesso :)")

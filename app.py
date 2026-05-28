import os
import json
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "segredo_super_forte"


# PERGUNTAS

def carregar_perguntas():
    base = "static/data/"
    arquivos = {
        "SOCIEDADE E CULTURA": "sociedade_cultura.json",
        "PERIODIZAÇÃO SOCIO-HISTÓRICA E PARADIGMAS CIVILIZACIONAIS": "periodizacao.json",
        "INDIVÍDUO, COMUNIDADE E SOCIEDADE": "individuo_comunidade.json",
        "O TEMPO E O ESPAÇO NA CONSTRUÇÃO SOCIAL DA REALIDADE": "tempo_espaco.json",
        "GEOPOLÍTICA, SEGURANÇA E SOCIEDADE DO RISCO": "geopolitica.json",
        "A ALTERIDADE DOS INDIVÍDUOS E DAS ORGANIZAÇÕES MODERNAS": "alteridade.json",
        "CONTEMPORANEIDADE CULTURAL E DESAFIOS DE CIVILIZAÇÃO": "contemporaneidade.json"
    }

    perguntas = {}
    for categoria, ficheiro in arquivos.items():
        caminho = os.path.join(base, ficheiro)
        with open(caminho, "r", encoding="utf-8") as f:
            data = json.load(f)
            perguntas[categoria] = data["perguntas"]

    return perguntas

perguntas_por_tema = carregar_perguntas()


# CORES DOS QUEIJOS

cores_queijo = {
    "SOCIEDADE E CULTURA": "#FFD700",
    "PERIODIZAÇÃO SOCIO-HISTÓRICA E PARADIGMAS CIVILIZACIONAIS": "#1E90FF",
    "INDIVÍDUO, COMUNIDADE E SOCIEDADE": "#32CD32",
    "O TEMPO E O ESPAÇO NA CONSTRUÇÃO SOCIAL DA REALIDADE": "#FF4500",
    "GEOPOLÍTICA, SEGURANÇA E SOCIEDADE DO RISCO": "#8A2BE2",
    "A ALTERIDADE DOS INDIVÍDUOS E DAS ORGANIZAÇÕES MODERNAS": "#FF1493",
    "CONTEMPORANEIDADE CULTURAL E DESAFIOS DE CIVILIZAÇÃO": "#FFA500"
}


# CATEGORIAS DA RODA

categorias_roda = [
    "SOCIEDADE E CULTURA",
    "PERIODIZAÇÃO SOCIO-HISTÓRICA E PARADIGMAS CIVILIZACIONAIS",
    "INDIVÍDUO, COMUNIDADE E SOCIEDADE",
    "O TEMPO E O ESPAÇO NA CONSTRUÇÃO SOCIAL DA REALIDADE",
    "GEOPOLÍTICA, SEGURANÇA E SOCIEDADE DO RISCO",
    "A ALTERIDADE DOS INDIVÍDUOS E DAS ORGANIZAÇÕES MODERNAS",
    "CONTEMPORANEIDADE CULTURAL E DESAFIOS DE CIVILIZAÇÃO",
    "PERDER QUEIJO",
    "PERDER A VEZ"
]


# IMAGEM 

def imagem_aleatoria():
    return "img/ia/Futuro-Innovador-de-la-Inteligencia-Artificial.png"


# INDEX

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session.clear()
        session["num_jogadores"] = int(request.form["num_jogadores"])
        return redirect(url_for("players"))
    return render_template("index.html")


# PLAYERS

@app.route("/players", methods=["GET", "POST"])
def players():
    num = session.get("num_jogadores", 1)

    if request.method == "POST":
        jogadores = []
        for i in range(num):
            nome = request.form.get(f"nome{i}")
            avatar = request.form.get(f"avatar{i}")
            jogadores.append({
                "nome": nome,
                "avatar": avatar,
                "score": 0,
                "queijos": [],
                "erros": []
            })
        session["jogadores"] = jogadores
        session["jogador_atual"] = 0
        return redirect(url_for("roda"))

    return render_template("players.html", num_jogadores=num)


# RODA

@app.route("/roda")
def roda():
    jogadores = session.get("jogadores", [])
    if not jogadores:
        return redirect(url_for("index"))

    j_idx = session.get("jogador_atual", 0)
    jogador_atual = jogadores[j_idx]

    # Filtrar categorias que o jogador já tem
    categorias_validas = [
        c for c in categorias_roda
        if c not in jogador_atual["queijos"]
        or c in ["PERDER QUEIJO", "PERDER A VEZ"]
    ]

    return render_template(
        "roda.html",
        jogador_atual=jogador_atual,
        categorias=categorias_validas,
        cores_queijo=cores_queijo
    )



# QUIZ_TEMA

@app.route("/quiz_tema")
def quiz_tema():
    tema = request.args.get("tema")

    jogadores = session.get("jogadores", [])
    j_idx = session.get("jogador_atual", 0)
    jogador = jogadores[j_idx]

    # PERDER A VEZ
    if tema == "PERDER A VEZ":
        session["jogador_atual"] = (j_idx + 1) % len(jogadores)
        return redirect(url_for("roda"))

    if tema == "PERDER QUEIJO":
        j_idx = session["jogador_atual"]
        jogador = session["jogadores"][j_idx]

        if jogador["queijos"]:
            perdido = random.choice(jogador["queijos"])
            jogador["queijos"].remove(perdido)

            session["queijo_perdido"] = perdido
            session["cor_queijo_perdido"] = cores_queijo.get(perdido, "#FFFFFF")
            session["evento"] = "PERDER_QUEIJO"
        else:
            session["evento"] = "SEM_QUEIJO"

        session["jogadores"][j_idx] = jogador
        session["jogador_atual"] = (j_idx + 1) % len(session["jogadores"])

        return redirect(url_for("evento"))



    # PERGUNTA NORMAL
    perguntas = perguntas_por_tema[tema]
    pergunta = random.choice(perguntas)
    pergunta["imagem"] = imagem_aleatoria()

    # Baralhar opções mantendo a correta
    opcoes = pergunta["opcoes"]
    indice_correto = pergunta["correta"]

    # Criar lista de pares (opcao, é_correta)
    opcoes_marcadas = [
        (opcao, i == indice_correto)
        for i, opcao in enumerate(opcoes)
    ]

    # Baralhar
    random.shuffle(opcoes_marcadas)

    # Reconstruir lista de opções e novo índice correto
    novas_opcoes = [op[0] for op in opcoes_marcadas]
    novo_indice_correto = [i for i, op in enumerate(opcoes_marcadas) if op[1]][0]

    # Atualizar pergunta
    pergunta["opcoes"] = novas_opcoes
    pergunta["correta"] = novo_indice_correto


    session["tema_atual"] = tema
    session["pergunta_atual"] = pergunta

    return render_template("curiosidade.html", pergunta=pergunta, tema=tema)


@app.route("/pergunta")
def pergunta():
    pergunta = session.get("pergunta_atual")
    if not pergunta:
        return redirect(url_for("roda"))

    j_idx = session["jogador_atual"]
    jogadores = session["jogadores"]

    return render_template(
        "quiz.html",
        pergunta=pergunta,
        jogadores=jogadores,
        jogador=j_idx + 1,
        numero_pergunta=1,
        total_perguntas=1,
        tema=session.get("tema_atual"),
        cores_queijo=cores_queijo
    )


# QUIZ_(RESPOSTA)

@app.route("/quiz", methods=["POST"])
def quiz():
    jogadores = session["jogadores"]
    j_idx = session["jogador_atual"]

    pergunta = session.get("pergunta_atual")
    resposta = int(request.form["resposta"])
    correta = int(request.form["correta"])
    tema = session.get("tema_atual")

    acertou = (resposta == correta)

    if acertou:
        jogadores[j_idx]["score"] += 1

        if tema not in jogadores[j_idx]["queijos"]:
            jogadores[j_idx]["queijos"].append(tema)
            session["queijo_ganho"] = tema
        else:
            session["queijo_ganho"] = None

        session["queijo_perdido"] = None

    else:
        session["queijo_ganho"] = None
        session["queijo_perdido"] = tema
        jogadores[j_idx]["erros"].append(tema)

    # Verificar vitória
    if len(jogadores[j_idx]["queijos"]) == 7:
        return redirect(url_for("result"))

    # Salvar alterações
    session["jogadores"] = jogadores

    # 🔥 PASSAR PARA O PRÓXIMO JOGADOR SEMPRE
    session["jogador_atual"] = (j_idx + 1) % len(jogadores)

    return render_template(
        "feedback.html",
        acertou=acertou,
        tema=tema,
        pergunta=pergunta,
        resposta_certa=pergunta["opcoes"][correta],
        explicacao=pergunta["explicacao"],
        jogador=jogadores[j_idx],
        cores_queijo=cores_queijo
    )

@app.route("/evento")
def evento():
    evento = session.get("evento")
    queijo = session.get("queijo_perdido")
    cor = session.get("cor_queijo_perdido")
    jogador = session["jogadores"][session["jogador_atual"]]

    return render_template(
        "feedback_evento.html",
        evento=evento,
        queijo=queijo,
        cor=cor,
        jogador=jogador
    )



# RESULTADOS

@app.route("/result")
def result():
    jogadores = session.get("jogadores", [])

    # Ordenar por número de queijos (descendente)
    jogadores_ordenados = sorted(
        jogadores,
        key=lambda j: len(j["queijos"]),
        reverse=True
    )

    return render_template(
        "podio.html",
        jogadores=jogadores_ordenados,
        cores_queijo=cores_queijo
    )



# RUN

if __name__ == "__main__":
    app.run(debug=True)

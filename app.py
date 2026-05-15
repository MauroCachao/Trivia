import os
import json
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "segredo_super_forte"

# -----------------------------
# CARREGAR PERGUNTAS
# -----------------------------
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

# -----------------------------
# CORES DOS QUEIJOS
# -----------------------------
cores_queijo = {
    "SOCIEDADE E CULTURA": "#FFD700",
    "PERIODIZAÇÃO SOCIO-HISTÓRICA E PARADIGMAS CIVILIZACIONAIS": "#1E90FF",
    "INDIVÍDUO, COMUNIDADE E SOCIEDADE": "#32CD32",
    "O TEMPO E O ESPAÇO NA CONSTRUÇÃO SOCIAL DA REALIDADE": "#FF4500",
    "GEOPOLÍTICA, SEGURANÇA E SOCIEDADE DO RISCO": "#8A2BE2",
    "A ALTERIDADE DOS INDIVÍDUOS E DAS ORGANIZAÇÕES MODERNAS": "#FF1493",
    "CONTEMPORANEIDADE CULTURAL E DESAFIOS DE CIVILIZAÇÃO": "#FFA500"
}

# -----------------------------
# CATEGORIAS DA RODA
# -----------------------------
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

# -----------------------------
# IMAGEM ALEATÓRIA
# -----------------------------
def imagem_aleatoria():
    return "img/ia/Futuro-Innovador-de-la-Inteligencia-Artificial.png"

# -----------------------------
# INDEX
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        session.clear()
        session["num_jogadores"] = int(request.form["num_jogadores"])
        return redirect(url_for("players"))
    return render_template("index.html")

# -----------------------------
# PLAYERS
# -----------------------------
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

# -----------------------------
# RODA
# -----------------------------
@app.route("/roda")
def roda():
    jogadores = session.get("jogadores", [])
    if not jogadores:
        return redirect(url_for("index"))

    session["queijo_ganho"] = None
    session["queijo_perdido"] = None

    j_idx = session.get("jogador_atual", 0)
    jogador_atual = jogadores[j_idx]

    return render_template(
        "roda.html",
        jogador_atual=jogador_atual,
        categorias=categorias_roda,
        cores_queijo=cores_queijo
    )

# -----------------------------
# QUIZ_TEMA
# -----------------------------
@app.route("/quiz_tema")
def quiz_tema():
    tema = request.args.get("tema")

    # PERDER A VEZ
    if tema == "PERDER A VEZ":
        session["jogador_atual"] = (session["jogador_atual"] + 1) % len(session["jogadores"])
        return redirect(url_for("roda"))

    # PERDER QUEIJO
    if tema == "PERDER QUEIJO":
        j_idx = session["jogador_atual"]
        jogador = session["jogadores"][j_idx]

        if jogador["queijos"]:
            perdido = random.choice(jogador["queijos"])
            jogador["queijos"].remove(perdido)
            session["queijo_perdido"] = perdido

        session["jogadores"][j_idx] = jogador
        session["jogador_atual"] = (j_idx + 1) % len(session["jogadores"])
        return redirect(url_for("roda"))

    # TEMA NORMAL
    perguntas = perguntas_por_tema[tema]
    pergunta = random.choice(perguntas)
    pergunta["imagem"] = imagem_aleatoria()

    session["tema_atual"] = tema
    session["pergunta_atual"] = pergunta

    return render_template("curiosidade.html", pergunta=pergunta, tema=tema)

# -----------------------------
# PERGUNTA
# -----------------------------
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

# -----------------------------
# QUIZ (RESPOSTA)
# -----------------------------
@app.route("/quiz", methods=["POST"])
def quiz():
    jogadores = session["jogadores"]
    j_idx = session["jogador_atual"]

    pergunta = session.get("pergunta_atual")
    resposta = int(request.form["resposta"])
    correta = int(request.form["correta"])
    tema = session.get("tema_atual")

    acertou = (resposta == correta)

    # ACERTOU
    if acertou:
        jogadores[j_idx]["score"] += 1

        if tema not in jogadores[j_idx]["queijos"]:
            jogadores[j_idx]["queijos"].append(tema)
            session["queijo_ganho"] = tema
        else:
            session["queijo_ganho"] = None

        session["queijo_perdido"] = None

    # ERROU
    else:
        resposta_certa = pergunta["opcoes"][correta]
        session["queijo_ganho"] = None
        session["queijo_perdido"] = tema
        jogadores[j_idx]["erros"].append(tema)

    # VERIFICAR SE COMPLETOU OS 7 QUEIJOS
    if len(jogadores[j_idx]["queijos"]) == 7:
        return redirect(url_for("result"))

    session["jogadores"] = jogadores

    # MOSTRAR FEEDBACK IMEDIATO
    return render_template(
        "feedback.html",
        acertou=acertou,
        tema=tema,
        pergunta=pergunta,
        resposta_certa=pergunta["opcoes"][correta],
        jogador=jogadores[j_idx],
        cores_queijo=cores_queijo
    )

# -----------------------------
# RESULTADOS
# -----------------------------
@app.route("/result")
def result():
    return render_template("result.html", jogadores=session["jogadores"], cores_queijo=cores_queijo)

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

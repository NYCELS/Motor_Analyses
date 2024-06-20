from flask import Flask, request, render_template, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plot', methods=['POST'])
def plot():
    # Obtendo os parâmetros do formulário
    rs = float(request.form['rs'])
    xs = float(request.form['xs'])
    rr = float(request.form['rr'])
    xr = float(request.form['xr'])
    xm = float(request.form['xm'])
    V = float(request.form['V'])
    P = int(request.form['P'])
    f = float(request.form['f'])
    P_out = float(request.form['P_out']) * 0.7355 * 1000  # Convertendo CV para Watts

    # Velocidade síncrona
    ns = 120 * f / P

    # Range de escorregamento
    s = np.linspace(0, 1, 20)

    # Cálculos
    ws = 2 * np.pi * ns / 60  # Velocidade síncrona em rad/s
    w_r = (1 - s) * ws  # Velocidade do rotor em rad/s

    # Circuito equivalente
    z_m = 1j * xm
    z_r = rr / s + 1j * xr
    z_eq = rs + 1j * xs + (z_m * z_r) / (z_m + z_r)

    # Corrente de estator
    I_s = V / z_eq

    # Potência convertida
    P_conv = 3 * (abs(I_s) ** 2) * (rr / s)

    # Potência mecânica
    P_mech = P_conv * (1 - s)

    # Torque eletromagnético
    T = P_mech / w_r

    # Preparando os dados para passar como contexto
    graph_data = {
        's': s.tolist(),  # Escorregamento para o gráfico e tabela
        'T': T.tolist()   # Torque para o gráfico e tabela
    }

    # Preparando dados para a tabela de escorregamento e torque
    table_data = list(zip(s.tolist(), T.tolist()))

    # Gerar imagem do gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(s, T, label='Torque')
    ax.set_title('Curvas de Torque em Função do Escorregamento')
    ax.set_xlabel('Escorregamento (s)')
    ax.set_ylabel('Torque (Nm)')
    ax.legend()

    # Salvando a imagem em um arquivo temporário e convertendo para base64
    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_str = base64.b64encode(img_stream.getvalue()).decode('utf-8')

    # Encerrando a figura
    plt.close(fig)

    # URL da nova página onde o gráfico será exibido
    return render_template('graph_page.html', img_str=img_str, table_data=table_data)

if __name__ == '__main__':
    app.run(debug=True)

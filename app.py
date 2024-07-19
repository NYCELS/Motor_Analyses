from flask import Flask, request, render_template, jsonify, send_file
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64

app = Flask(__name__, static_folder='motor_analysis')

# Dados iniciais para exibição na primeira carga da página
@app.route('/')
def index():
    return render_template('index.html')

# Rota para plotar o gráfico e gerar a tabela inicial
@app.route('/plot', methods=['POST'])
def plot():
    # Obter parâmetros do formulário
    rs = float(request.form['rs'])
    xs = float(request.form['xs'])
    rr = float(request.form['rr'])
    xr = float(request.form['xr'])
    V = float(request.form['V'])
    P = int(request.form['P'])
    I = int(request.form['I'])
    f = float(request.form['f'])
    polos = int(request.form['polos'])
    rend = float(request.form['rend'])
    conexao = request.form['conexao']

    # Ajustar a corrente I com base no tipo de ligação
    if conexao == 'triangulo':
        V /= np.sqrt(3)
    elif conexao == 'estrela':
        V = V

    # XMG
    xm = I * 0.35

    # Converter CV para Watts
    P_out = P * 0.7355

    # Par de polos
    pp = polos / 2
    
    # Velocidade síncrona
    ns = 120 * f / pp

    # Range de escorregamento
    s = np.linspace(0, 1, 100)

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

    # Inverter o eixo x e ordenar a tabela do maior para o menor escorregamento
    s_invertido = np.flip(s)
    T_invertido = np.flip(T)
    sorted_table_data = sorted(zip(s_invertido.tolist(), T_invertido.tolist()), key=lambda x: x[0], reverse=True)

    # Preparar dados adicionais para a tabela
    Rsth = rs / (xs + xr)
    Xsth = xs + xm
    x_r = xr * s
    r_r0 = rr / s
    k1 = xm / xs
    r_r = rr * s
    k2 = xm / xr

    if conexao == 'triangulo':
        Vth = V / np.sqrt(3)
    elif conexao == 'estrela':
        Vth = V

    w = ws
    Xe2 = (xm * xm) / (xs + xm)

    # Preparar dados para a tabela
    table_data = []
    for i, (s_val, T_val) in enumerate(sorted_table_data):
        row = {
            's': s_val,
            'T': T_val,
            'Rsth': Rsth,
            'Xsth': Xsth,
            'x_r': x_r[i],
            'r_r0': r_r0[i],
            'k1': k1,
            'r_r': r_r[i],
            'k2': k2,
            'Vth': Vth,
            'w': w,
            'Xe2': Xe2
        }
        table_data.append(row)

    # Gerar imagem do gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(s_invertido, T_invertido, label='Torque')
    ax.set_title('Curvas de Torque em Função do Escorregamento')
    ax.set_xlabel('Escorregamento (s)')
    ax.set_ylabel('Torque (Nm)')
    ax.set_xlim([1, 0])  # Definir limite do eixo x de 1 a 0, invertido
    ax.grid(True)  # Adicionar linhas de grade ao gráfico
    ax.legend()

    # Salvar a imagem em um arquivo temporário e converter para base64
    img_stream = io.BytesIO()
    plt.savefig(img_stream, format='png')
    img_stream.seek(0)
    img_str = base64.b64encode(img_stream.getvalue()).decode('utf-8')

    # Encerrar a figura para liberar memória
    plt.close(fig)

    # Retornar para a página HTML com o gráfico e tabela invertidos
    return render_template('graph_page.html', img_str=img_str, table_data=table_data, k1=k1, k2=k2, f=f)

# Rota para atualizar os dados com novos valores de K1, K2 e f via AJAX
@app.route('/update', methods=['POST'])
def update():
    # Obter parâmetros dos inputs
    data = request.get_json()
    k1 = float(data.get('k1', 1.0))
    k2 = float(data.get('k2', 1.0))
    f = float(data.get('f', 60.0))
    
    # Recalcular os dados com os novos valores de K1, K2 e f
    # Velocidade síncrona
    polos = 4  # Exemplo fixo de número de polos
    ns = 120 * f / (polos / 2)

    # Range de escorregamento
    s = np.linspace(0, 1, 100)

    # Cálculos
    ws = 2 * np.pi * ns / 60  # Velocidade síncrona em rad/s
    w_r = (1 - s) * ws  # Velocidade do rotor em rad/s

    # Torque eletromagnético ajustado com K1 e K2
    T = (k1 * (1 - s) * ws) / (k2 + s)

    # Inverter o eixo x e ordenar a tabela do maior para o menor escorregamento
    s_invertido = np.flip(s)
    T_invertido = np.flip(T)
    sorted_table_data = sorted(zip(s_invertido.tolist(), T_invertido.tolist()), key=lambda x: x[0], reverse=True)

    # Preparar dados adicionais para a tabela
    Rsth = 0.1
    Xsth = 0.2
    x_r = 0.3 * s
    r_r0 = 0.4 / s
    r_r = 0.5 * s
    Vth = 220.0 * f
    w = ws
    Xe2 = 0.6

    # Preparar dados para a tabela
    table_data = []
    for i, (s_val, T_val) in enumerate(sorted_table_data):
        row = {
            's': s_val,
            'T': T_val,
            'Rsth': Rsth,
            'Xsth': Xsth,
            'x_r': x_r[i],
            'r_r0': r_r0[i],
            'k1': k1,
            'r_r': r_r[i],
            'k2': k2,
            'Vth': Vth,
            'w': w,
            'Xe2': Xe2
        }
        table_data.append(row)

    # Retornar os dados em formato JSON
    return jsonify(img_str=img_str, table_data=table_data)

# Rota para exportar os dados da tabela para Excel
@app.route('/export_excel', methods=['POST'])
def export_excel():
    # Dados da tabela para exportar
    data = request.get_json()
    df = pd.DataFrame(data['table_data'])

    # Criar um buffer para o arquivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Table Data')
    writer.save()
    output.seek(0)

    # Retornar o arquivo Excel como um download
    return send_file(output, attachment_filename='table_data.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

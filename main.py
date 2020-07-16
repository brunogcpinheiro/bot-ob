from iqoptionapi.stable_api import IQ_Option
import time
import json
from datetime import datetime
from dateutil import tz
import sys


def stop(lucro, gain, loss):
    if lucro <= float('-' + str(abs(loss))):
        print('Stop Loss batido!')
        sys.exit()

    if lucro >= float(abs(gain)):
        print('Stop Gain Batido!')
        sys.exit()


def Martingale(valor, payout):
    lucro_esperado = valor * payout
    perda = float(valor)

    while True:
        if round(valor * payout, 2) > round(abs(perda) + lucro_esperado, 2):
            return round(valor, 2)
            break
        valor += 0.01


def Payout(par):
    API.subscribe_strike_list(par, 1)
    while True:
        d = API.get_digital_current_profit(par, 1)
        if d != False:
            d = round(int(d) / 100, 2)
            break
        time.sleep(1)
    API.unsubscribe_strike_list(par, 1)

    return d


API = IQ_Option('brunogcpinheiro@gmail.com',
                'bgcp2087')  # Entrar Login e Senha
API.connect()
API.change_balance('PRACTICE')  # Real ou Practice

while True:
    if API.check_connect() == False:
        print('Erro ao conectar')
        API.connect
    else:
        print('Conectado com Sucesso')
        break
    time.sleep(3)


def timestamp_converter(x):  # Função para converter timestamp
    hora = datetime.strptime(datetime.utcfromtimestamp(
        x).strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    hora = hora.replace(tzinfo=tz.gettz('GMT'))

    return hora


def banca():
    return API.get_balance()


par = input(
    'Qual par você deseja operar? Obs.: Se OTC acrescente -OTC no fim. => ').upper()
porcentagem_de_entrada = int(input(
    'Qual o percentual da banca será utilizado para entradas? => ')) / 100
valor_entrada = float(int(banca()) * porcentagem_de_entrada)
valor_entrada_b = float(valor_entrada)

martingale_pergunta = input('Quantos martin gales serão utilizados? => ')
martingale = int(martingale_pergunta)
martingale += 1

porcentagem_de_stop_loss = int(
    input('Qual o percentual para o stop loss? => ')) / 100
porcentagem_de_stop_gain = int(
    input('Qual o percentual para o stop gain? => ')) / 100
stop_loss = float(int(banca()) * porcentagem_de_stop_loss)
print('Banca:', banca())
print('Stop Loss:', stop_loss)
stop_gain = float(int(banca()) * porcentagem_de_stop_gain)
print('Stop Gain:', stop_gain)
print('************************')
print('Aguarde...')

lucro = 0
valor = 0
payout = Payout(par)

while True:
    teste = timestamp_converter(API.get_server_timestamp())
    minutos = float((teste.strftime('%M.%S'))[1:])
    entrar = True if (minutos >= 4.57 and minutos <=
                      5) or minutos >= 9.57 else False

    if entrar:
        print('\n\nIniciando Trade!', '\nData:', str(teste)[:-6])

        if valor > 0:

            valor_entrada = float(
                int(banca()) * porcentagem_de_entrada) + round(valor * porcentagem_de_entrada, 2)

        else:
            valor_entrada = float(int(banca()) * porcentagem_de_entrada)

        print('Entrada:', valor_entrada)
        dir = False
        print('Verificando cores..')

        velas = API.get_candles(par, 60, 3, API.get_server_timestamp())

        velas[0] = 'verde' if velas[0]['open'] < velas[0]['close'] else 'vermelho' if velas[0]['open'] > velas[0]['close'] else 'doji'
        velas[1] = 'verde' if velas[1]['open'] < velas[1]['close'] else 'vermelho' if velas[1]['open'] > velas[1]['close'] else 'doji'
        velas[2] = 'verde' if velas[2]['open'] < velas[2]['close'] else 'vermelho' if velas[2]['open'] > velas[2]['close'] else 'doji'

        cores = velas[0] + ' ' + velas[1] + ' ' + velas[2]

        if cores.count('verde') > cores.count('vermelho') and cores.count('doji') == 0:
            dir = 'put'

        if cores.count('vermelho') > cores.count('verde') and cores.count('doji') == 0:
            dir = 'call'

        print('Últimas velas do quadrante:', cores, '\nOperação:', dir)

        if dir:
            for i in range(martingale):

                status, id = API.buy_digital_spot(par, valor_entrada, dir, 1)

                if status:
                    while True:
                        status, valor = API.check_win_digital_v2(id)

                        if status:
                            valor = valor if valor > 0 else float(
                                '-' + str(abs(valor_entrada)))
                            lucro += round(valor, 2)

                            print('Resultado: ', end='')
                            print('WIN /' if valor > 0 else 'LOSS /', round(valor, 2), '/ Acumulado: ',
                                  round(lucro, 2), ('/ '+str(i) + ' GALE' if i > 0 else ''))

                            valor_entrada = Martingale(
                                (valor_entrada_b +
                                 (valor_entrada * (100 % - payout))), payout)

                            stop(lucro, stop_gain, stop_loss)

                            break

                    if valor > 0:
                        break

                else:
                    print('\nERRO AO REALIZAR ORDEM\n\n')

        else:
            print(
                'Analise Inconclusiva, foram encontrados candles neutros')
            time.sleep(5)
            entrar = False

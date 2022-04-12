import requests
from bs4 import BeautifulSoup
from time import sleep
from threading import Thread
import js2py


stop = False
gambling_headers = {
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="100", "Google Chrome";v="100"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-dest': 'iframe',
    'referer': 'https://vsa2.gambling-malta.com/',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}
# BetanoBR: Premiere | betanolatam: Liga America
operators = ['BetanoBR', 'betanolatam']
historic = []
def getLastGame(operator):
    url = f'https://vsa2.gambling-malta.com/vr-media-schedule/MediaViewer?sportType=FOOTBALL_MATCH&operator={operator}'
    result = requests.get(url=url, headers=gambling_headers)
    bs = BeautifulSoup(result.text, 'html.parser')
    return bs.find('iframe').attrs['src'].split('eventId')[-1].replace('=', '')

def getResult(eventId, operator : str):
    try:
        finished = [game['eventId'] for game in historic]
        if eventId not in finished:
            result_url = f'https://vsmv.gambling-malta.com/media/viewer/vanilla/vanilla-viewer.php?userId=1&operator={operator}&eventId={eventId}'
            result = requests.get(url=result_url, headers=gambling_headers)
            bs = BeautifulSoup(result.text, 'html.parser')
            homeTeamName = bs.find('div', {'id' : 'homeTeamName'}).text
            awayTeamName = bs.find('div', {'id' : 'awayTeamName'}).text
            homeTeamScore = bs.find('div', {'class' : 'homeTeamScore'}).attrs['id'].replace('homeTeamScore', '')
            awayTeamScore = bs.find('div', {'class' : 'awayTeamScore'}).attrs['id'].replace('awayTeamScore', '')
            js_code = bs.find_all('script')[-1].string
            for index_of_document, line in enumerate(js_code.split('\n')):
                if 'var timeArray' in line:
                    break
            js_reformed = "\n".join(js_code.split('\n')[:index_of_document])
            eventTime = js2py.eval_js(js_reformed + '\nhrs + ":" + mins')
            league = 'Premiere' if operator == operators[0] else 'América'
            historic.append({
                'liga': league,
                'inicio': eventTime,
                'eventId': eventId,
                'timeDaCasa': homeTeamName,
                'timeDeFora': awayTeamName,
                'scoreDeCasa': homeTeamScore,
                'scoreDeFora': awayTeamScore
            })
            print(f'[{league}] Adicionado {homeTeamName} {homeTeamScore} x {awayTeamScore} {awayTeamName}')
    except Exception as e:
        # print(e)
        pass

def premiereGamesTask():
    while not stop:
        getResult(getLastGame(operators[0]), operators[0])
        sleep(2)

def americaGamesTask():
    while not stop:
        getResult(getLastGame(operators[1]), operators[1])
        sleep(2)

def commandLine():
    global stop
    help_message = (
        "help           Mostra essa mensagem\n"
        "exit           Finaliza o programa\n"
        "show           Mostra os jogos capturados\n"
        "show score     Mostra os jogos pelo placar Ex.: show score 2 1\n"
        "show anyscores Mostra os jogos que algum time marcou a quantidade de gols Ex.: show anyscores 3"
    )
    print(help_message)
    while not stop:
        cmd = input()
        cmd = cmd.lower()
        error = False
        if cmd == 'help': print(help_message)
        if cmd.startswith('show'):
            target_list = historic.copy()
            params = cmd.split(' ')[1:]
            if len(params) >= 1:
                if 'america' in params and 'premiere' in params:
                    print('Você deve escolher entre america e premiere.')
                else:
                    if 'america' in params:
                        target_list = list(filter(lambda n : n['liga'] == 'América', target_list))
                    if 'premiere' in params:
                        target_list = list(filter(lambda n : n['liga'] == 'Premiere', target_list))
                    if 'score' in params:
                        score_index = params.index('score')
                        try:            
                            if params[score_index + 1].isdigit() and params[score_index + 2].isdigit():
                                valid = []
                                for game in target_list:
                                    if params[score_index + 1] == game['scoreDeCasa']:
                                        if params[score_index + 2] == game['scoreDeFora']:
                                            valid.append(game['eventId'])
                                    if params[score_index + 1] == game['scoreDeFora']:
                                        if params[score_index + 2] == game['scoreDeCasa']:
                                            valid.append(game['eventId'])

                                
                                target_list = list(
                                    filter(
                                        lambda n: n['eventId'] in valid,
                                        target_list
                                    )
                                )
                        except:
                            print('Use: show score PLACAR_1 PLACAR_2')

                    if 'anyscores' in params:
                        anyscores_index = params.index('anyscores')
                        try:            
                            if params[anyscores_index + 1].isdigit():
                                valid = []
                                for game in target_list:
                                    if params[score_index + 1] == game['scoreDeCasa'] or params[score_index + 1] == game['scoreDeFora']:
                                            valid.append(game['eventId'])

                                
                                target_list = list(
                                    filter(
                                        lambda n: n['eventId'] in valid,
                                        target_list
                                    )
                                )
                        except:
                            print('Use: show anyscores PLACAR_1')

            for game in target_list:
                print(f'[{game["liga"]}][{game["inicio"]}] {game["timeDaCasa"]} {game["scoreDeCasa"]} x {game["scoreDeFora"]} {game["timeDeFora"]}')
            target_list.clear()
        if cmd == 'exit':
            print("Encerrando...")
            stop = True
def main():
    t1 = Thread(target=premiereGamesTask)
    t2 = Thread(target=americaGamesTask)
    t3 = Thread(target=commandLine)
    t1.start()
    t2.start()
    t3.start()

main()
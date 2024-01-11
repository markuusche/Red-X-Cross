from src.modules import *
from src.helpers import *

count = 0

# this is where the table looping happens
def play(driver, game, bet, allin=False):
    global count
    waitElement(driver, 'in-game', 'botnav')
    wait_If_Clickable(driver, 'category', game)
    elements = findElements(driver, 'lobby', game)
    for i in range(len(elements)):
        gameName = elements[i]
        if game == 'dragontiger' and 'DT' not in gameName.text:
            continue

        elif game == 'baccarat' and i == 0:
            continue

        elif game == 'three-cards' and 'Three' not in gameName.text:
            continue

        elif game == 'sedie' and 'Sedie' not in gameName.text:
            continue
            
        if allin:
            elements = reset_coins(driver, game)

        x = elements[i]

        # javascript code to prevent full screen when
        # entering tables
        driver.execute_script(executeJS('exitScreen')) 
        driver.execute_script("arguments[0].scrollIntoView();", x)
        
        x.click()
        waitElement(driver, 'in-game', 'game')
        playGame(driver, game, bet, allin)

        if game == 'baccarat' and bet == 'All':
            allin = False

        wait_If_Clickable(driver, 'in-game', 'back')
        waitElement(driver, 'lobby', 'main')
        elements = findElements(driver, 'lobby', game)
        count += 1

# this is where the betting process for single bet
def playGame(driver, game, bet, allin=False):
    bet_areas = list(data(game))
    if bet == 'All':
        for i in range(0, len(bet_areas)):
            betOn(driver, game, bet_areas[i])
            if i == len(bet_areas) -1:
                break
    else:
        betOn(driver, game, bet, allin)

def betOn(driver, bet, betArea, allin=False):
    '''
    this function:
    assert coins and player balance matched,
    asserts the balance is deducted by betting,
    asserts the remaining balance after betting,
    asserts the the added and lose amount after game results,
    asserts No more bets to be made,
    waits for Successful Bet,
    waits for Betting is open,
    logs the the overall results,
    logs table and dealer name,
    '''

    balance = []
    table = findElement(driver, 'in-game','tableNumber')
    dealer = findElement(driver, 'in-game','dealer')

    while True:
        money = findElement(driver, 'in-game','balance')
        balance.append(money.text)
        checkPlayerBalance(driver)
        waitElement(driver, 'in-game', 'timer')
        timer = findElement(driver, 'in-game', 'timer')
        
        if timer.text == 'CLOSED':
            waitPresence(driver, 'in-game', 'toast', text='Please Place Your Bet!')
            captureDigitalMessage(driver, 'Please Place Your Bet', table.text, allin)
        else:
            intTimer = int(timer.text)
            if intTimer <= 5:
                waitPresence(driver, 'in-game', 'toast', text='Please Place Your Bet!')
                if intTimer == 3:
                    captureDigitalMessage(driver, 'Please Place Your Bet', table.text, allin)
            else:
                if intTimer >= 8:
                    if allin:
                        if bet == 'baccarat':
                            coins_allin(driver, bet, allin)

                        elif bet == 'dragontiger':
                            coins_allin(driver, bet, allin)

                        elif bet == 'three-cards':
                            coins_allin(driver, bet, allin)

                        elif bet == 'sedie':
                            coins_allin(driver, bet, allin)

                        else:
                            ...
                    else:
                        wait_If_Clickable(driver, bet, betArea)
                        waitElementInvis(driver, 'in-game', 'toast')
                        findElement(driver, 'action', 'confirm', click=True)

                    waitPresence(driver, 'in-game','toast', text='Bet Successful!')
                    captureDigitalMessage(driver, 'Bet Sucessful', table.text, allin)
                    waitPresence(driver, 'in-game','toast', text='No More Bets!')
                    remainingMoney = findElement(driver, 'in-game', 'balance')
                    preBalance = float(remainingMoney.text.replace(',',''))

                    captureDigitalMessage(driver, 'No More Bets', table.text, allin)
                    assertionCheck(driver)
                    waitElementInvis(driver, 'in-game', 'toast')
                    waitElement(driver, 'in-game', 'toast')
                    winner = findElement(driver, 'in-game', 'toast')
                    captureDigitalMessage(driver, winner.text, table.text, allin)
                    
                    # =================================================
                    # get game result text from digital message
                    board = findElements(driver, 'in-game', 'board-result')
                    lucky_odds = dict(data('lucky'))
                    lucky_result = 0.00
                    for i in board:
                        board_result = i.text.split(' – ')[0]

                        if board_result in lucky_odds:
                            value = lucky_odds[board_result]
                            lucky_result = float(value)

                    # =================================================

                    bets = findElement(driver, 'in-game', 'bets')
                    getBets = float(bets.text.replace(',',''))
                    oldBalance = float(balance[0].replace(',',''))

                    # get balance after bet
                    wl = LoseOrWin(driver)
                    #assertionCheck(driver, check=True)
                    balance = float(remainingMoney.text.replace(',',''))
                    total = 0
                    back = 0

                    # =================================================
                    # calculates the expected lose and win
                    if 'Lose: ' in wl:
                        loseAmount = float(wl.replace('Lose: ',''))
                        calcAmount = float(f'{preBalance:.2f}') + float(f'{getBets:.2f}') - float(f'{loseAmount:.2f}')

                        if allin:
                            screenshot(driver, 'Lose Balance', table.text)
                        
                        assert f'{calcAmount:.2f}' == f'{balance:.2f}'
                    else:
                        resultBal = float(wl.replace('Win: ',''))
                        total = float(f'{preBalance:.2f}') + float(f'{resultBal:.2f}') + float(f'{getBets:.2f}')
                        placeBets = findElement(driver, 'in-game', 'bets')
                        cFloat = float(placeBets.text.replace(',',''))

                    # =================================================

                        # ====================================================
                        # calculate the odds player will receive after winning 
                        getOdds = findElement(driver, bet, betArea)
                        match = re.search(r'\b(\d+:\d+(\.\d+)?)\b', getOdds.text)

                        # special case for Three-cards odds
                        if allin == False:
                            if bet == 'three-cards' and betArea == 'Lucky':
                                calc_odds = lucky_result * cFloat
                                assert calc_odds == resultBal
                            else:
                                if match:
                                    val = match.group(1)
                                    odds = float(val.split(':', 1)[1])
                                    winOdds = cFloat * odds
                                    if resultBal != 0.00:
                                        assert winOdds == resultBal, 'Odds did not match'
                                else:
                                    print("Odds not found")
                        # ====================================================
                                
                        if allin:
                            screenshot(driver, 'Win Balance', table.text)

                        assert f'{total:.2f}' == f'{balance:.2f}'
                    
                    if allin:
                        waitPresence(driver, 'in-game','toast', text='You have NOT bet for 3 times, 2 more and you\'ll be redirected to lobby!')
                        captureDigitalMessage(driver, 'You have NOT bet for 3 times', table.text, allin)

                    with open('logs.txt', 'a') as logs:
                        logs.write(f'===============================\nIndex: {count}\n{table.text} {dealer.text} - BET on: {betArea}\nCurrent Balance: {oldBalance:.2f}\nBet: {getBets:.2f}\nPre-Balance: {preBalance:.2f}\n{wl}\nCash back: {back}\nFinal Balance: {balance:.2f}\n===============================\n' + '\n')
                    break

# check if the player balance from top left panel icon
# and in the middle panel matches.
def checkPlayerBalance(driver):
    coins = findElement(driver, 'in-game', 'balance')
    playerBalance = findElement(driver, 'in-game', 'playerBalance')
    assert coins.text == playerBalance.text

# gets Lose or Win message with the values
def LoseOrWin(driver):
    waitElement(driver, 'in-game', 'resultToast')
    result = findElement(driver, 'in-game', 'winloss')
    if '-' in result.text:
        getText = float(result.text.replace('W/L', '').replace('-','').replace(' ','').replace(':',''))
        return f'Lose: {getText:.2f}'
    else:
        getText = float(result.text.replace('W/L', '').replace('+','').replace(' ','').replace(':',''))
        return f'Win: {getText:.2f}'

# All-in bet
def coins_allin(driver, game, allin=False):
    bet_areas = list(data(game))
    coins = findElement(driver, 'in-game','balance')
    table = findElement(driver, 'in-game','tableNumber')

    for _ in range(0, 30):
        index = random.choice(range(len(bet_areas)))
        wait_If_Clickable(driver, game, bet_areas[index])
        insufficient = driver.execute_script(executeJS('getDigital'))

        if insufficient == True:
            captureDigitalMessage(driver, 'Insufficient', table.text, allin)
            wait_If_Clickable(driver, 'action', 'confirm')
            waitPresence(driver, 'in-game','balance', text='0.00')
            assert coins.text == '0.00'
            break

def assertionCheck(driver, check=False):
    preResult = findElements(driver, 'in-game', 'board-result')
    for i in preResult:
        result = int(i.text)
        
        if check:
            assert result > 0
        else:
            assert result == 0

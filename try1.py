import random
choices = {'1': 'rock', '2': 'paper', '3': 'scissors'}
beats = { 'rock':'paper' , 'paper':'scissors' , 'scissors':'rock'}
memory = {
    'rock':     {'rock': 0, 'paper': 0, 'scissors': 0},
    'paper':    {'rock': 0, 'paper': 0, 'scissors': 0},
    'scissors': {'rock': 0, 'paper': 0, 'scissors': 0},
}
last_move = None
def remember(player_move):
    global last_move
    if last_move is not None:
        memory[last_move][player_move] += 1
    last_move = player_move
def smart_computer_choice():
    if last_move is None:
        return random.choice(list(choices.values()))   # first round: no data yet

    counts = memory[last_move]                    # what the player did after their last move
    prediction = max(counts, key=counts.get)      # the move with the highest count

    if counts[prediction] == 0:
        return random.choice(list(choices.values()))   # no pattern learned yet

    return beats[prediction]                      # play what beats the prediction

def get_decisions():
    player_input= input("1 for rock , 2 for paper , 3 for scissors: ").strip()
    while player_input not in choices:
        player_input= input("Invalid input. Choose 1 for rock , 2 for paper , 3 for scissors: ").strip()


    player_choice = choices[player_input]
    #computer_choice  = random.choice(list(choices.values())) # my old one without prediction
    computer_choice = smart_computer_choice()
    remember(player_choice)


    return player_choice , computer_choice

def get_winner(player , computer):
    if player == computer:
        print(f"It's a tie, computer also chose {computer}")
        return 'tie'

    elif player == 'rock' :
        if computer == 'paper':
            print("you lost , computer chose paper")
            return 'computer'
        else :
            print("you won , computer chose scissors")
            return 'player'
    elif player == 'paper':
        if computer == 'scissors':
            print("you lost , computer chose scissors")
            return 'computer'
        else :
            print("you won , computer chose rock")
            return 'player'
    elif player == 'scissors':
        if computer == 'rock':
            print("you lost , computer chose rock")
            return 'computer'
        else :
            print("you won , computer chose paper")
            return 'player'

if __name__ == "__main__":
    print("welcome to the rock paper scissors game")
    player_score = 0
    computer_score = 0

    for round_number in range(1, 6):
        print(f"\n--- Round {round_number} of 5 ---")
        player, computer = get_decisions()
        result = get_winner(player, computer)
        if result == 'player':
            player_score += 1
        elif result == 'computer':
            computer_score += 1
        print(f"Score ==> You: {player_score}  Computer: {computer_score}")

    print("\n=== Final result ===")
    print(f"You: {player_score}  Computer: {computer_score}")
    if player_score > computer_score:
        print("You won the game!")
    elif computer_score > player_score:
        print("Computer won the game!")
    else:
        print("The game is a draw!")

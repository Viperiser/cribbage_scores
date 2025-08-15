# This script analyses the data and estimates skill scores.

# Imports
import pandas as pd
import json

# Global variables
PARTICIPATION_FILE = "20250809-costa_rica_cribbage_participation.csv"
SCORE_FILE = "20250809-costa_rica_cribbage_results.csv"
OUTPUT_NAME = "20250815-costa_rica_cribbage_analysis"
SIG_FIG_TOLERANCE = 4  # Controls size of update to be considered significant


# Helper functions
def get_data(file_path):
    """Ingests data and returns a .csv file."""
    df = pd.read_csv(file_path)
    return df


def get_actual_scores(data):
    """Returns the actual scores as a dict from the dataframe."""
    actual_scores = {}
    for i in data.columns:
        actual_scores[i] = sum(data[i])
    return actual_scores


def calculate_expected_scores(skills, participation_data, results_data):
    """Calculates expected scores based on participation data and skills."""
    names = participation_data.columns
    number_of_games = len(participation_data)
    expected_scores = {}
    for i in names:
        expected_scores[i] = 0
    for game_number in range(number_of_games):
        number_of_players = sum(participation_data.iloc[game_number])
        if number_of_players == 4:
            for player in names:  # we are calculating their expected score
                result = results_data.iloc[game_number][player]
                teamskill = 0
                for potential_partner in names:
                    if results_data.iloc[game_number][potential_partner] == result:
                        teamskill += skills[potential_partner]
                total_skills = sum(skills[p] for p in names)
                expected_scores[player] += teamskill / total_skills
        else:
            for player in names:
                if participation_data.iloc[game_number][player] == 1:
                    total_skills = sum(
                        skills[p]
                        for p in names
                        if participation_data.iloc[game_number][p] == 1
                    )
                    expected_scores[player] += skills[player] / total_skills
    return expected_scores


def update_skills(skills, participation_data, results_data):
    """Updates the skills based on expected and actual scores."""
    new_skills = {}
    expected_scores = calculate_expected_scores(
        skills, participation_data, results_data
    )
    actual_scores = get_actual_scores(results_data)
    player_names = participation_data.columns
    for player in player_names:
        new_skills[player] = (
            skills[player] * actual_scores[player] / expected_scores[player]
        )
    # find earliest player in alphabetical order
    reference_player = min(player_names)
    new_skills[reference_player] = 1  # Set reference player's skill to 1

    return new_skills


def get_skills(participation_data, results_data):
    """Returns the skills of players based on participation and results data."""
    # Initialise skills
    skills = {}
    for i in participation_data.columns:
        skills[i] = 1  # Initial skill set to 1 for all players
    new_skills = update_skills(skills, participation_data, results_data)
    # Check if the skills have converged
    while any(
        abs(new_skills[player] - skills[player]) > 10 ** (-SIG_FIG_TOLERANCE)
        for player in new_skills
    ):
        skills = new_skills.copy()
        new_skills = update_skills(skills, participation_data, results_data)

    return new_skills


def generate_matchups(names):
    """Generates a list of matchups in cribbage from the list of names."""
    matchnum = 0
    matchnumbers = []
    players = []
    # Four-player matchups
    for i in range(1, len(names)):
        opponents = names.copy()
        opponents.remove(names[0])
        opponents.remove(names[i])
        matchnumbers.append(matchnum)
        players.append(", ".join(sorted((names[0], names[i]))))
        matchnumbers.append(matchnum)
        players.append(", ".join(sorted((opponents[0], opponents[1]))))
        matchnum += 1
    # Three-player matchups
    for i in range(len(names)):  # The one who isn't playing
        opponents = names.copy()
        opponents.remove(names[i])
        players.extend(opponents)
        matchnumbers.extend([matchnum] * 3)
        matchnum += 1
    # Two-player matchups
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            matchnumbers.extend([matchnum] * 2)
            players.append(names[i])
            players.append(names[j])
            matchnum += 1
    matchlist = pd.DataFrame({"match_number": matchnumbers, "players": players})
    return matchlist


def generate_actuals_table(participation_data, results_data):
    # Generate list of matchups
    names = participation_data.columns.tolist()
    matchups = generate_matchups(names)
    games_played = [0] * len(matchups)
    games_won = [0] * len(matchups)
    # Find all actuals
    for matchup in range(len(matchups)):
        # For each matchup, go through every game to find games that correspond to it
        for game_number in range(len(participation_data)):
            if sum(participation_data.iloc[game_number]) == 4:
                # This game is 4 player, so needs handling differently
                t1_1 = names[0]
                t2_1 = names[1]  # Placeholder that will be replaced
                result_1 = results_data.iloc[game_number][0]
                for i in range(1, 4):
                    if results_data.iloc[game_number][i] == result_1:
                        t2_1 = names[i]
                other_team = names.copy()
                other_team.remove(t1_1)
                other_team.remove(t2_1)
                team_1 = ", ".join(sorted((t1_1, t2_1)))
                team_2 = ", ".join(sorted(other_team))
                if matchups.iloc[matchup]["players"] == team_1:
                    games_played[matchup] += 1
                    games_won[matchup] += result_1
                if matchups.iloc[matchup]["players"] == team_2:
                    games_played[matchup] += 1
                    games_won[matchup] += 1 - result_1

            else:  # This game is 2 or 3 players
                # Find the players in the matchup
                matchup_number = matchups.iloc[matchup]["match_number"]
                players = set(
                    matchups[matchups["match_number"] == matchup_number][
                        "players"
                    ].tolist()
                )
                # Find the players in the game we are checking
                game_players = set(
                    [
                        name
                        for name in names
                        if participation_data.at[game_number, name] == 1
                    ]
                )
                # Find the winner in the game we are checking
                winner = [
                    name for name in names if results_data.at[game_number, name] == 1
                ][0]
                if players == game_players:
                    games_played[matchup] += 1
                    if matchups.iloc[matchup]["players"] == winner:
                        games_won[matchup] += 1

    matchups["games_played"] = games_played
    matchups["games_won"] = games_won
    return matchups


def predict_scores(skills, actuals_table):
    number_of_matches = max(actuals_table["match_number"]) + 1
    expected_scores = []
    for matchup in range(number_of_matches):
        raw_players = [
            name
            for name in actuals_table[actuals_table["match_number"] == matchup][
                "players"
            ].tolist()
        ]
        players = []
        for player in raw_players:
            players.extend(player.split(", "))
        total_skill = sum(skills[player] for player in players)

        raw_teams = actuals_table[actuals_table["match_number"] == matchup][
            "players"
        ].tolist()
        for player in raw_teams:
            team = []
            team.extend(player.split(", "))
            team_skill = sum(skills[player] for player in team)
            expected_scores.append(team_skill / total_skill)
    actuals_table["expected_score"] = expected_scores
    return actuals_table


def transform_data(final_actuals_table):
    # Turn it into a json of matchups
    number_of_entries = max(final_actuals_table["match_number"]) + 1
    entries = []
    for entry in range(number_of_entries):
        entry_data = final_actuals_table[final_actuals_table["match_number"] == entry]
        players = entry_data["players"].tolist()
        games_played = entry_data["games_played"].tolist()
        games_won = entry_data["games_won"].tolist()
        if sum(games_played) == 0:
            games_won = None
        expected_scores = entry_data["expected_score"].tolist()
        entries.append(
            {
                "players": players,
                "actual_wins": games_won,
                "predicted_win_rates": expected_scores,
            }
        )
    return entries


# Main function
def main():
    """Main function to run the analysis."""
    participation_data = get_data(PARTICIPATION_FILE)
    results_data = get_data(SCORE_FILE)
    skills = get_skills(participation_data, results_data)
    print("Final estimated skills:", skills)
    print(
        "Expected scores:",
        calculate_expected_scores(skills, participation_data, results_data),
    )
    played = get_actual_scores(participation_data)
    print("Games played:", played)
    scores = get_actual_scores(results_data)
    print("Actual scores:", scores)

    actuals_table = generate_actuals_table(participation_data, results_data)
    predicted_scores = predict_scores(skills, actuals_table)
    print("Actual and predicted scores:", predicted_scores)

    transformed_data = transform_data(predicted_scores)
    print("Transformed data:", transformed_data)

    final_data = {}
    final_data["played"] = played
    final_data["wins"] = scores
    final_data["skills"] = skills
    final_data["matches"] = transformed_data

    with open(f"{OUTPUT_NAME}.json", "w") as f:
        json.dump(final_data, f)

    return


main()

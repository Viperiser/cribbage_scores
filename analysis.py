# This script analyses the data and estimates skill scores.

# Imports
import pandas as pd

# Global variables
PARTICIPATION_FILE = "20250809-costa_rica_cribbage_participation.csv"
SCORE_FILE = "20250809-costa_rica_cribbage_results.csv"
SIG_FIG_TOLERANCE = 2  # Controls size of update to be considered significant


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
        new_skills[player] = actual_scores[player] / expected_scores[player]
    # find earliest player in alphabetical order
    reference_player = min(player_names)
    reference_skill = new_skills[reference_player]
    # normalize scores based on the reference player
    for player in player_names:
        new_skills[player] = new_skills[player] / reference_skill
    return new_skills


# Main function
def main():
    """Main function to run the analysis."""
    participation_data = get_data(PARTICIPATION_FILE)
    results_data = get_data(SCORE_FILE)
    skills = {}
    for i in participation_data.columns:
        skills[i] = 1  # Initial skill set to 1 for all players
    print(calculate_expected_scores(skills, participation_data, results_data))
    print(get_actual_scores(results_data))
    print(update_skills(skills, participation_data, results_data))
    return


main()

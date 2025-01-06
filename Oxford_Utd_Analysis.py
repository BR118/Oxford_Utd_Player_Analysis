import sqlite3
import pandas as pd

# Database Helper Functions
def fetch_table_data(conn, table_name):
    """Function to fetch data from a database table.
    
    Args:
    conn (sqlite3.Connection): Connection to the database.
    table_name (str): Name of the table to fetch data from.

    Returns:
    pd.DataFrame: DataFrame containing the data from the specified table.
    """
    return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

def save_table_to_db(df, table_name, conn):
    """Function to save a DataFrame to a database table.
    
    Args:
    df (pd.DataFrame): DataFrame to save to the database.
    table_name (str): Name of the table to save the data to.
    conn (sqlite3.Connection): Connection to the database.
    """
    df.to_sql(table_name, conn, if_exists='replace', index=False)

# Helper Functions
def stat_value(row, stat, default=0):
    """Function to get the value of a stat from a row, with a default value of 0 if the stat is NaN.
    
    Args:
    row (pd.Series): Row containing the data.
    stat (str): Name of the stat to get the value of.
    default (int, optional): Default value to return if the stat is NaN. Defaults to 0.

    Returns:
    int: Value of the stat from the row.
    """
    return row[stat] if pd.notna(row[stat]) else default

def get_stat_contribution(stat, row, position, role, weights, stat_ranges_by_role):
    """Function to calculate the contribution of a given stat to a player's rating.
    
    Args:
    stat (str): Name of the stat to calculate the contribution of.
    row (pd.Series): Row containing the player's data.
    position (str): Position of the player.
    role (str): Role of the player.
    weights (dict): Dictionary containing the weights for each stat for each position.
    stat_ranges_by_role (dict): Dictionary containing the ranges for each stat for each role.

    Returns:
    float: Contribution of the stat to the player's rating.
    """
    weight = weights.get(position, {}).get(stat, 0)
    value = stat_value(row, stat)
    max_value = stat_ranges_by_role[role].get(stat, 1)
    normalised_value = value / max_value if max_value > 0 else 0
    return weight * normalised_value

# Calculation Functions
def calculate_scores_and_ratings(df, position_stats, weights, stat_ranges_by_role):
    """
    Function to calculate the raw scores and normalised ratings for each player in the dataset.

    Args:
    df (pd.DataFrame): DataFrame containing the player data.
    position_stats (dict): Dictionary containing the stats for each position.
    weights (dict): Dictionary containing the weights for each stat for each position.
    stat_ranges_by_role (dict): Dictionary containing the ranges for each stat for each role.

    Returns:
    Tuple[List[float], List[float]]: Tuple containing the raw scores and normalised ratings for each
    player in the dataset.
    """
    raw_scores = [] # List to store raw scores for each player
    normalised_scores = []  # List to store normalised ratings for each player
    for _, row in df.iterrows():    # Iterate over each row in DataFrame
        position = row['Position']  # Get position of the player
        role = row['Role']  # Get role of the player
        if position not in position_stats or role not in stat_ranges_by_role:   # Check if position is in position_stats dictionary
            raw_scores.append(None) # Append None to the raw_scores list if the position is not in the dictionary
            normalised_scores.append(None)  # Append None to the normalised_scores list if the position is not in the dictionary
            continue

        stats = position_stats[position]    # Get stats for player's position
        raw_score = sum(    # Calculate raw score for the player
            get_stat_contribution(stat, row, position, role, weights, stat_ranges_by_role)  
            for stat in stats
        )
        raw_scores.append(raw_score)    # Append raw score to the raw_scores list

    min_raw = min(filter(None, raw_scores), default=0)  # Get minimum raw score
    max_raw = max(filter(None, raw_scores), default=1)  # Get maximum raw score
    normalised_scores = [   # Calculate normalised rating for each player
        1 + 9 * (score - min_raw) / (max_raw - min_raw) if max_raw != min_raw else 1
        for score in raw_scores
    ]
    return raw_scores, normalised_scores

def debug_player_rating(player_name, df, position_stats, weights, stat_ranges_by_role):
    """
    Function to debug the rating calculation for a specific player and observe how each stat contributes to their rating.

    Args:
    player_name (str): Name of the player to debug.
    df (pd.DataFrame): DataFrame containing the player data.
    position_stats (dict): Dictionary containing the stats for each position.
    weights (dict): Dictionary containing the weights for each stat for each position.
    stat_ranges_by_role (dict): Dictionary containing the ranges for each stat for each
    role.
    """
    player_row = df[df['Name'] == player_name]  # Get the row for the player
    if player_row.empty:    # Check if player is not found
        print(f"No player found with name: {player_name}")
        return

    player_row = player_row.iloc[0] # Get the player's row
    position = player_row['Position']   # Get the player's position
    role = player_row['Role']   # Get the player's role
    if position not in position_stats or role not in stat_ranges_by_role:   # Check if position is in position_stats dictionary
        print(f"Position {position} not in position_stats.")
        return

    print(f"Debugging for Player: {player_name}, Position: {position}, Role: {role}")
    print("-" * 50) # Print a line of dashes to separate the output
    raw_score = 0   # Initialise the player's raw score

    for stat in position_stats[position]:   # Iterate over each stat for the player's position
        contribution = get_stat_contribution(stat, player_row, position, role, weights, stat_ranges_by_role)    # Calculate the contribution of the stat
        raw_score += contribution   # Add the contribution of the stat to the player's raw score
        print(f"Stat: {stat}, Contribution: {contribution:.2f}")

    print("-" * 50)
    print(f"Raw Score: {raw_score}")

    min_raw_score_dataset = df['raw_score'].min()   # Get minimum raw score in the dataset
    max_raw_score_dataset = df['raw_score'].max()   # Get maximum raw score in the dataset
    if min_raw_score_dataset != max_raw_score_dataset:  # Check if minimum and maximum raw scores are not equal
        normalised_score = 1 + (9 * (raw_score - min_raw_score_dataset) / (max_raw_score_dataset - min_raw_score_dataset))  # Calculate normalised rating
    else:
        normalised_score = 1    # Set normalised rating to 1 if minimum and maximum raw scores are equal

    print(f"Normalised Rating for {player_name}: {normalised_score}")
    print("-" * 50)

# Main Function
def main():
    conn = sqlite3.connect('Oxford_Utd_Stats.db')  # Connect to database

    df = fetch_table_data(conn, "player_stats")   # Fetch data from player_stats table

    # Define positions to roles to obtain suffcient data for comparisons
    position_roles = {
        'CF': 'Attackers', 'LW': 'Attackers', 'RW': 'Attackers',
        'AM': 'Midfielders', 'CM': 'Midfielders', 'DM': 'Midfielders',
        'CB': 'Defenders', 'LB': 'Defenders', 'RB': 'Defenders',
        'GK': 'Goalkeepers'
    }
    df['Role'] = df['Position'].map(position_roles)

    # Position-specific stats that will contribute to how they are rated
    position_stats = {
        'CF': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
            'accuratePasses', 'inaccuratePasses', 'keyPasses', 'successfulDribbles',
            'interceptions', 'yellowCards', 'redCards', 'totalShots', 'shotsOnTarget', 'totalDuelsWon',
            'penaltyWon', 'penaltyConceded', 'goalsFromInsideTheBox', 'goalsFromOutsideTheBox', 'dispossessed',
            'possessionLost', 'possessionWonAttThird', 'touches', 'wasFouled', 'fouls', 'ownGoals', 'offsides',
            'passToAssist', 'tacklesWon', 'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'LW': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
                'accuratePasses', 'inaccuratePasses', 'keyPasses', 'successfulDribbles', 'tackles',
                'interceptions', 'yellowCards', 'redCards', 'accurateCrosses', 'totalShots', 'shotsOnTarget',
                'totalDuelsWon', 'penaltyWon', 'penaltyConceded', 'accurateLongBalls', 'errorLeadToGoal',
                'dispossessed', 'possessionLost', 'possessionWonAttThird', 'touches', 'wasFouled', 'fouls',
                'ownGoals', 'dribbledPast', 'offsides', 'passToAssist', 'duelLost', 'tacklesWon', 
                'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
    'RW': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
                'accuratePasses', 'inaccuratePasses', 'keyPasses', 'successfulDribbles', 'tackles',
                'interceptions', 'yellowCards', 'redCards', 'accurateCrosses', 'totalShots', 'shotsOnTarget',
                'totalDuelsWon', 'penaltyWon', 'penaltyConceded', 'accurateLongBalls', 'errorLeadToGoal',
                'dispossessed', 'possessionLost', 'possessionWonAttThird', 'touches', 'wasFouled', 'fouls',
                'ownGoals', 'dribbledPast', 'offsides', 'passToAssist', 'duelLost', 'tacklesWon', 
                'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'AM': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
            'accuratePasses', 'inaccuratePasses', 'accurateOppositionHalfPasses', 'accurateFinalThirdPasses',
            'keyPasses', 'successfulDribbles', 'tackles', 'interceptions', 'yellowCards', 'redCards',
            'totalShots', 'shotsOnTarget', 'totalDuelsWon', 'penaltyWon', 'accurateLongBalls', 'errorLeadToGoal',
            'dispossessed', 'possessionLost', 'possessionWonAttThird', 'touches', 'wasFouled', 'fouls',
            'ownGoals', 'dribbledPast', 'offsides', 'passToAssist', 'duelLost', 'tacklesWon', 'totwAppearances',
            'expectedGoals', 'ballRecovery', 'appearances'],
        'CM': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
            'accuratePasses', 'inaccuratePasses', 'accurateOwnHalfPasses', 'accurateOppositionHalfPasses',
            'accurateFinalThirdPasses', 'keyPasses', 'successfulDribbles', 'tackles', 'interceptions',
            'yellowCards', 'redCards', 'totalShots', 'shotsOnTarget', 'totalDuelsWon', 'penaltyWon',
            'penaltyConceded', 'accurateLongBalls', 'clearances', 'errorLeadToGoal', 'errorLeadToShot',
            'dispossessed', 'possessionLost', 'possessionWonAttThird', 'touches', 'wasFouled', 'fouls',
            'ownGoals', 'dribbledPast', 'offsides', 'blockedShots', 'passToAssist', 'cleanSheet', 'duelLost',
            'goalsConceded', 'tacklesWon', 'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'DM': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
            'accuratePasses', 'inaccuratePasses', 'accurateOwnHalfPasses', 'accurateOppositionHalfPasses',
            'accurateFinalThirdPasses', 'keyPasses', 'successfulDribbles', 'tackles', 'interceptions',
            'yellowCards', 'redCards', 'totalShots', 'shotsOnTarget', 'totalDuelsWon', 'penaltyWon',
            'accurateLongBalls', 'clearances', 'errorLeadToGoal', 'errorLeadToShot', 'dispossessed',
            'possessionLost', 'possessionWonAttThird', 'touches', 'wasFouled', 'fouls', 'ownGoals',
            'dribbledPast', 'offsides', 'blockedShots', 'passToAssist', 'cleanSheet', 'duelLost', 
            'goalsConceded', 'tacklesWon', 'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'RB': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
                'accuratePasses', 'inaccuratePasses', 'accurateOwnHalfPasses', 'accurateOppositionHalfPasses',
                'accurateFinalThirdPasses', 'keyPasses', 'successfulDribbles', 'tackles', 'interceptions',
                'yellowCards', 'redCards', 'accurateCrosses', 'totalShots', 'shotsOnTarget', 'groundDuelsWon',
                'aerialDuelsWon', 'penaltyWon', 'penaltyConceded', 'accurateLongBalls', 'clearances',
                'errorLeadToGoal', 'errorLeadToShot', 'dispossessed', 'possessionLost', 'possessionWonAttThird',
                'touches', 'wasFouled', 'fouls', 'ownGoals', 'dribbledPast', 'offsides', 'blockedShots',
                'passToAssist', 'cleanSheet', 'duelLost', 'aerialLost', 'goalsConceded', 'tacklesWon',
                'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'LB': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
                'accuratePasses', 'inaccuratePasses', 'accurateOwnHalfPasses', 'accurateOppositionHalfPasses',
                'accurateFinalThirdPasses', 'keyPasses', 'successfulDribbles', 'tackles', 'interceptions',
                'yellowCards', 'redCards', 'accurateCrosses', 'totalShots', 'shotsOnTarget', 'groundDuelsWon',
                'aerialDuelsWon', 'penaltyWon', 'penaltyConceded', 'accurateLongBalls', 'clearances',
                'errorLeadToGoal', 'errorLeadToShot', 'dispossessed', 'possessionLost', 'possessionWonAttThird',
                'touches', 'wasFouled', 'fouls', 'ownGoals', 'dribbledPast', 'offsides', 'blockedShots',
                'passToAssist', 'cleanSheet', 'duelLost', 'aerialLost', 'goalsConceded', 'tacklesWon',
                'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'CB': ['rating', 'goals', 'bigChancesCreated', 'bigChancesMissed', 'assists', 'expectedAssists',
            'accuratePasses', 'inaccuratePasses', 'accurateOwnHalfPasses', 'accurateOppositionHalfPasses',
            'keyPasses', 'tackles', 'interceptions', 'yellowCards', 'redCards', 'groundDuelsWon',
            'aerialDuelsWon', 'penaltyConceded', 'accurateLongBalls', 'clearances', 'errorLeadToGoal',
            'errorLeadToShot', 'dispossessed', 'possessionLost', 'wasFouled', 'fouls', 'ownGoals',
            'dribbledPast', 'blockedShots', 'passToAssist', 'cleanSheet', 'duelLost', 'aerialLost',
            'goalsConceded', 'tacklesWon', 'totwAppearances', 'expectedGoals', 'ballRecovery', 'appearances'],
        'GK': ['rating', 'accuratePasses', 'inaccuratePasses', 'yellowCards', 'redCards', 'groundDuelsWon',
            'aerialDuelsWon', 'penaltyConceded', 'accurateLongBalls', 'clearances', 'errorLeadToGoal',
            'errorLeadToShot', 'dispossessed', 'possessionLost', 'wasFouled', 'fouls', 'ownGoals',
            'dribbledPast', 'saves', 'cleanSheet', 'penaltySave', 'savedShotsFromInsideTheBox',
            'savedShotsFromOutsideTheBox', 'goalsConcededInsideTheBox', 'goalsConcededOutsideTheBox',
            'punches', 'successfulRunsOut', 'highClaims', 'crossesNotClaimed', 'duelLost', 'aerialLost',
            'goalsConceded', 'totwAppearances', 'ballRecovery', 'appearances']
    }

    # Weighted stats for each position based on their importance (IMO)
    weights = {
        'CF':   {
            'rating': 1.0, 'goals': 2.0, 'bigChancesCreated': 1.5, 'bigChancesMissed': -1.0,
            'assists': 1.5, 'expectedAssists': 1.2, 'accuratePasses': 0.5, 'inaccuratePasses': -0.3,
            'keyPasses': 1.0, 'successfulDribbles': 1.2, 'interceptions': 0.5,
            'yellowCards': -1.0, 'redCards': -2.0, 'totalShots': 1.0, 'shotsOnTarget': 1.5,
            'totalDuelsWon': 0.8, 'penaltyWon': 1.0, 'penaltyConceded': -1.5, 'goalsFromInsideTheBox': 1.5,
            'goalsFromOutsideTheBox': 2.0, 'dispossessed': -0.5, 'possessionLost': -0.3, 'possessionWonAttThird': 1.0,
            'touches': 0.3, 'wasFouled': 0.5, 'fouls': -0.2, 'ownGoals': -3.0, 'offsides': -0.5,
            'passToAssist': 1.0, 'tacklesWon': 0.5, 'totwAppearances': 1.0, 'expectedGoals': 2.0,
            'ballRecovery': 0.5, 'appearances': 0.3
        },
        'LW':   {
            'rating': 1.0, 'goals': 2.5, 'bigChancesCreated': 2.0, 'bigChancesMissed': -1.2,
            'assists': 2.0, 'expectedAssists': 1.5, 'accuratePasses': 0.7, 'inaccuratePasses': -0.3,
            'keyPasses': 1.8, 'successfulDribbles': 1.5, 'tackles': 0.6, 'interceptions': 0.6,
            'yellowCards': -1.0, 'redCards': -2.0, 'accurateCrosses': 1.5, 'totalShots': 1.5,
            'shotsOnTarget': 1.8, 'totalDuelsWon': 0.9, 'penaltyWon': 1.0, 'penaltyConceded': -1.5,
            'accurateLongBalls': 0.5, 'errorLeadToGoal': -2.0, 'dispossessed': -0.8, 'possessionLost': -0.5,
            'possessionWonAttThird': 1.2, 'touches': 0.4, 'wasFouled': 0.6, 'fouls': -0.3,
            'ownGoals': -3.0, 'dribbledPast': -1.0, 'offsides': -0.5, 'passToAssist': 1.5,
            'duelLost': -0.3, 'tacklesWon': 0.7, 'totwAppearances': 1.2, 'expectedGoals': 2.8,
            'ballRecovery': 0.5, 'appearances': 0.3
        },
        'RW':   {
            'rating': 1.0, 'goals': 2.5, 'bigChancesCreated': 2.0, 'bigChancesMissed': -1.2,
            'assists': 2.0, 'expectedAssists': 1.5, 'accuratePasses': 0.7, 'inaccuratePasses': -0.3,
            'keyPasses': 1.8, 'successfulDribbles': 1.5, 'tackles': 0.6, 'interceptions': 0.6,
            'yellowCards': -1.0, 'redCards': -2.0, 'accurateCrosses': 1.5, 'totalShots': 1.5,
            'shotsOnTarget': 1.8, 'totalDuelsWon': 0.9, 'penaltyWon': 1.0, 'penaltyConceded': -1.5,
            'accurateLongBalls': 0.5, 'errorLeadToGoal': -2.0, 'dispossessed': -0.8, 'possessionLost': -0.5,
            'possessionWonAttThird': 1.2, 'touches': 0.4, 'wasFouled': 0.6, 'fouls': -0.3,
            'ownGoals': -3.0, 'dribbledPast': -1.0, 'offsides': -0.5, 'passToAssist': 1.5,
            'duelLost': -0.3, 'tacklesWon': 0.7, 'totwAppearances': 1.2, 'expectedGoals': 2.8,
            'ballRecovery': 0.5, 'appearances': 0.3
        },
        'AM':   {
            'rating': 1.0, 'goals': 2.0, 'bigChancesCreated': 2.5, 'bigChancesMissed': -1.0,
            'assists': 2.5, 'expectedAssists': 2.0, 'accuratePasses': 1.0, 'inaccuratePasses': -0.4,
            'accurateOppositionHalfPasses': 1.2, 'accurateFinalThirdPasses': 1.5, 'keyPasses': 2.5,
            'successfulDribbles': 1.8, 'tackles': 0.8, 'interceptions': 0.7, 'yellowCards': -1.0,
            'redCards': -2.0, 'totalShots': 1.2, 'shotsOnTarget': 1.5, 'totalDuelsWon': 1.0,
            'penaltyWon': 1.0, 'accurateLongBalls': 0.7, 'errorLeadToGoal': -2.0, 'dispossessed': -0.6,
            'possessionLost': -0.4, 'possessionWonAttThird': 1.5, 'touches': 0.5, 'wasFouled': 0.6,
            'fouls': -0.3, 'ownGoals': -3.0, 'dribbledPast': -1.0, 'offsides': -0.5, 'passToAssist': 2.0,
            'duelLost': -0.3, 'tacklesWon': 0.8, 'totwAppearances': 1.5, 'expectedGoals': 2.5,
            'ballRecovery': 0.5, 'appearances': 0.3
        },
        'CM':   {
            'rating': 1.0, 'goals': 1.5, 'bigChancesCreated': 2.0, 'bigChancesMissed': -0.8,
            'assists': 2.0, 'expectedAssists': 1.8, 'accuratePasses': 1.2, 'inaccuratePasses': -0.3,
            'accurateOwnHalfPasses': 1.2, 'accurateOppositionHalfPasses': 1.5, 'accurateFinalThirdPasses': 1.8,
            'keyPasses': 2.0, 'successfulDribbles': 1.0, 'tackles': 1.5, 'interceptions': 1.5,
            'yellowCards': -1.0, 'redCards': -2.0, 'totalShots': 0.8, 'shotsOnTarget': 1.0,
            'totalDuelsWon': 1.2, 'penaltyWon': 1.0, 'penaltyConceded': -1.5, 'accurateLongBalls': 1.2,
            'clearances': 1.0, 'errorLeadToGoal': -2.0, 'errorLeadToShot': -1.5, 'dispossessed': -0.5,
            'possessionLost': -0.3, 'possessionWonAttThird': 1.2, 'touches': 0.5, 'wasFouled': 0.7,
            'fouls': -0.3, 'ownGoals': -3.0, 'dribbledPast': -1.0, 'offsides': -0.5, 'blockedShots': 0.5,
            'passToAssist': 1.5, 'cleanSheet': 0.5, 'duelLost': -0.3, 'goalsConceded': -1.5,
            'tacklesWon': 1.2, 'totwAppearances': 1.2, 'expectedGoals': 1.8, 'ballRecovery': 1.2,
            'appearances': 0.3
        },
        'DM':   {
            'rating': 1.0, 'goals': 1.2, 'bigChancesCreated': 1.8, 'bigChancesMissed': -0.8,
            'assists': 1.5, 'expectedAssists': 1.5, 'accuratePasses': 1.5, 'inaccuratePasses': -0.5,
            'accurateOwnHalfPasses': 1.5, 'accurateOppositionHalfPasses': 1.2, 'accurateFinalThirdPasses': 1.0,
            'keyPasses': 1.8, 'successfulDribbles': 0.8, 'tackles': 2.0, 'interceptions': 2.0,
            'yellowCards': -1.0, 'redCards': -2.0, 'totalShots': 0.6, 'shotsOnTarget': 0.8,
            'totalDuelsWon': 1.5, 'penaltyWon': 0.5, 'accurateLongBalls': 1.2, 'clearances': 1.5,
            'errorLeadToGoal': -2.5, 'errorLeadToShot': -1.8, 'dispossessed': -0.5, 'possessionLost': -0.5,
            'possessionWonAttThird': 1.2, 'touches': 0.6, 'wasFouled': 0.6, 'fouls': -0.5,
            'ownGoals': -3.0, 'dribbledPast': -1, 'offsides': -0.2, 'blockedShots': 0.7,
            'passToAssist': 1.0, 'cleanSheet': 1.0, 'duelLost': -0.5, 'goalsConceded': -1.5,
            'tacklesWon': 2.0, 'totwAppearances': 1.5, 'expectedGoals': 1.2, 'ballRecovery': 2.0,
            'appearances': 0.3
        },
        'RB':   {
            'rating': 1.0, 'goals': 0.8, 'bigChancesCreated': 1.5, 'bigChancesMissed': -0.5,
            'assists': 1.8, 'expectedAssists': 1.5, 'accuratePasses': 1.2, 'inaccuratePasses': -0.3,
            'accurateOwnHalfPasses': 1.5, 'accurateOppositionHalfPasses': 1.2, 'accurateFinalThirdPasses': 1.5,
            'keyPasses': 1.8, 'successfulDribbles': 1.0, 'tackles': 2.0, 'interceptions': 1.8,
            'yellowCards': -1.0, 'redCards': -2.0, 'accurateCrosses': 1.5, 'totalShots': 0.8,
            'shotsOnTarget': 0.8, 'groundDuelsWon': 1.5, 'aerialDuelsWon': 1.0, 'penaltyWon': 0.5,
            'penaltyConceded': -1.5, 'accurateLongBalls': 1.0, 'clearances': 1.5, 'errorLeadToGoal': -2.5,
            'errorLeadToShot': -1.8, 'dispossessed': -0.5, 'possessionLost': -0.3, 'possessionWonAttThird': 1.2,
            'touches': 0.6, 'wasFouled': 0.6, 'fouls': -0.5, 'ownGoals': -3.0, 'dribbledPast': -1.5,
            'offsides': -0.2, 'blockedShots': 1.0, 'passToAssist': 1.2, 'cleanSheet': 1.5,
            'duelLost': -0.5, 'aerialLost': -0.3, 'goalsConceded': -1.5, 'tacklesWon': 2.0,
            'totwAppearances': 1.5, 'expectedGoals': 0.8, 'ballRecovery': 1.8, 'appearances': 0.3
        },
        'LB':   {
            'rating': 1.0, 'goals': 0.8, 'bigChancesCreated': 1.5, 'bigChancesMissed': -0.5,
            'assists': 1.8, 'expectedAssists': 1.5, 'accuratePasses': 1.2, 'inaccuratePasses': -0.3,
            'accurateOwnHalfPasses': 1.5, 'accurateOppositionHalfPasses': 1.2, 'accurateFinalThirdPasses': 1.5,
            'keyPasses': 1.8, 'successfulDribbles': 1.0, 'tackles': 2.0, 'interceptions': 1.8,
            'yellowCards': -1.0, 'redCards': -2.0, 'accurateCrosses': 1.5, 'totalShots': 0.8,
            'shotsOnTarget': 0.8, 'groundDuelsWon': 1.5, 'aerialDuelsWon': 1.0, 'penaltyWon': 0.5,
            'penaltyConceded': -1.5, 'accurateLongBalls': 1.0, 'clearances': 1.5, 'errorLeadToGoal': -2.5,
            'errorLeadToShot': -1.8, 'dispossessed': -0.5, 'possessionLost': -0.3, 'possessionWonAttThird': 1.2,
            'touches': 0.6, 'wasFouled': 0.6, 'fouls': -0.5, 'ownGoals': -3.0, 'dribbledPast': -1.5,
            'offsides': -0.2, 'blockedShots': 1.0, 'passToAssist': 1.2, 'cleanSheet': 1.5,
            'duelLost': -0.5, 'aerialLost': -0.3, 'goalsConceded': -1.5, 'tacklesWon': 2.0,
            'totwAppearances': 1.5, 'expectedGoals': 0.8, 'ballRecovery': 1.8, 'appearances': 0.3
        },
        'CB':   {
            'rating': 1.0, 'goals': 0.5, 'bigChancesCreated': 0.5, 'bigChancesMissed': -0.2,
            'assists': 0.8, 'expectedAssists': 0.8, 'accuratePasses': 1.5, 'inaccuratePasses': -0.3,
            'accurateOwnHalfPasses': 2.0, 'accurateOppositionHalfPasses': 1.0, 'keyPasses': 0.5,
            'tackles': 2.5, 'interceptions': 2.5, 'yellowCards': -1.0, 'redCards': -2.0,
            'groundDuelsWon': 2.0, 'aerialDuelsWon': 2.5, 'penaltyConceded': -2.0, 'accurateLongBalls': 1.5,
            'clearances': 2.5, 'errorLeadToGoal': -3.0, 'errorLeadToShot': -2.0, 'dispossessed': -0.5,
            'possessionLost': -0.3, 'wasFouled': 0.5, 'fouls': -0.5, 'ownGoals': -3.5, 'dribbledPast': -2.0,
            'blockedShots': 1.5, 'passToAssist': 0.8, 'cleanSheet': 2.5, 'duelLost': -0.5,
            'aerialLost': -0.5, 'goalsConceded': -2.0, 'tacklesWon': 2.5, 'totwAppearances': 1.5,
            'expectedGoals': 0.5, 'ballRecovery': 2.5, 'appearances': 0.3
        },
        'GK':   {
            'rating': 3.0, 'accuratePasses': 1.0, 'inaccuratePasses': -0.3, 'yellowCards': -1.0,
            'redCards': -2.0, 'groundDuelsWon': 1.0, 'aerialDuelsWon': 1.5, 'penaltyConceded': -2.0,
            'accurateLongBalls': 1.0, 'clearances': 1.5, 'errorLeadToGoal': -3.0, 'errorLeadToShot': -1.5,
            'dispossessed': -0.5, 'possessionLost': -0.2, 'wasFouled': 0.5, 'fouls': -0.5,
            'ownGoals': -3.5, 'dribbledPast': -0.25, 'saves': 3.0, 'cleanSheet': 3.0,
            'penaltySave': 2.5, 'savedShotsFromInsideTheBox': 2.0, 'savedShotsFromOutsideTheBox': 1.5,
            'goalsConcededInsideTheBox': -1.2, 'goalsConcededOutsideTheBox': -1.5, 'punches': 1.0,
            'successfulRunsOut': 1.2, 'highClaims': 1.5, 'crossesNotClaimed': -0.5, 'duelLost': -0.2,
            'aerialLost': -0.2, 'goalsConceded': -1.5, 'totwAppearances': 1.5, 'ballRecovery': 1.5,
            'appearances': 0.3
        }
    }

    stat_ranges_by_role = {}    # Dictionary to store the maximum values for each stat for each role
    for role, group in df.groupby('Role'):  # Iterate over each role in the dataset and group by role
        max_values = {stat: group[stat].max(skipna=True) for position in position_stats for stat in position_stats[position]}   # Get the maximum value for each stat in the group
        stat_ranges_by_role[role] = max_values  # Add the maximum values to the dictionary

    df['raw_score'], df['normalised_rating'] = calculate_scores_and_ratings(df, position_stats, weights, stat_ranges_by_role)   # Calculate raw scores and normalised ratings

    calculated_df = df[['Name', 'Position', 'raw_score', 'normalised_rating']]
    save_table_to_db(calculated_df, "calculations", conn)   # Save the calculated ratings to the database

    print("Raw scores and normalised ratings have been successfully saved to the 'calculations' table.")

    debug_player_rating("Will Vaulks", df, position_stats, weights, stat_ranges_by_role)    # Debug the rating for a specific player (e.g. Will Vaulks)

    conn.close()    # Close database connection

if __name__ == "__main__":
    main()  # Call the main function

# Oxford_Utd_Player_Analysis

This project is a comprehensive analysis of Oxford United players' performance using data-driven insights. It involves calculating normalised player ratings, visualising key statistics, and generating interactive charts to better understand player contributions and positional trends.

##Features:
Player Ratings: Calculate raw and normalised ratings based on various weighted stats per position.
Interactive Visualisations:
Donut Chart: Shows the average contribution by position.
Line Graph: Displays each player's normalised rating.
Heatmap: Highlights average key stats (e.g., goals, assists, tackles) for each position.
Database Integration: Reads player stats from a SQLite database (Oxford_Utd_Stats.db) and writes calculated scores back for further use.

##Why SQLite Instead of an API?
Initially, I would have preferred to use a live API for fetching player statistics to ensure the most up-to-date and extensive data (as well as making the code more tidy). However, due to API access limitations (from sofascore), the project relies on pre-stored data in a local SQLite database. If API access becomes feasible in the future, the project can be extended to integrate live data fetching.

##Statistics
All statistics were obtained from sofascore - by inspecting each player's statistic page on sofascore and heading to network and viewing the response all stats were stored as JSON and implemented into my python code. Below is a screenshot of where stats are founded from.

<img width="1435" alt="Screenshot 2025-01-06 at 14 20 49" src="https://github.com/user-attachments/assets/17bd9c0d-aacf-4a5b-8cc1-f5a2f0f74796" />

##Requirements
Python: Version 3.8 or above.
Libraries:
pandas
sqlite3
plotly
numpy

Install dependencies using:
pip install pandas plotly numpy

##Data Description
Database: The project uses a SQLite database (Oxford_Utd_Stats.db) with a table named player_stats.
Key Columns:
Name: Player name.
Position: Player's position (e.g., CF, CB, GK).
Various Stats: Metrics like goals, assists, tackles, successful dribbles, etc.

##How to Run:
###Step 1: Set Up the Database
Run the following script to set up the SQLite database (Oxford_Utd_Stats.db) and populate it with player stats:
python Oxford_Utd_Database_Setup.py

###Step 2: Calculate Ratings
Execute the script to calculate raw scores and normalised ratings for each player:
python Oxford_Utd_Analysis.py
This will create a new table, calculations, in the Oxford_Utd_Stats.db database containing the calculated ratings.

###Step 3: Visualise the Data
Open the Jupyter Notebook for interactive visualisations:
jupyter notebook Oxford_Utd_Analysis_Visualisations.ipynb
This notebook generates:
Donut chart showing average contribution by position.
Line graph of player ratings.
Heatmap of average key stats by position.



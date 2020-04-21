# -*- coding: utf-8 -*-
from datetime import datetime,timedelta
import cassiopeia as cass
from cassiopeia.core import Summoner, Match, MatchHistory, common
from cassiopeia.data import Season, Queue, Region
from collections import Counter
import arrow
import os
import pandas as pd 


class Matchup:
    def __init__(self, participant, match_duration):
        self.campione = participant.champion
        self.kills = participant.stats.kills
        self.deaths = participant.stats.deaths
        self.assists = participant.stats.assists
        self.wins = participant.stats.win
        self.games = 1
        self.cs = participant.stats.neutral_minions_killed + participant.stats.total_minions_killed
        self.time = match_duration.seconds / 60

    def update(self, participant, match_duration):
        self.kills += participant.stats.kills
        self.deaths += participant.stats.deaths
        self.assists += participant.stats.assists
        self.games += 1
        self.wins += participant.stats.win
        self.cs += participant.stats.neutral_minions_killed + participant.stats.total_minions_killed
        self.time += match_duration.seconds / 60

    def to_dict(self):
        return {"champion": self.campione.name,
                "kills": round(self.kills / self.games, 2),
                "deaths": round(self.deaths / self.games, 2),
                "assists": round(self.assists / self.games, 2),
                "cs/min": round(self.cs / self.time, 2), 
                "winrate": str(round(self.wins / self.games, 2) * 100) + '%',
                "games": self.games,
                "kda": round((self.kills + self.assists) / max(self.deaths, 1), 3)
                }

# cassiopeia setup
cass.set_riot_api_key('INSERT_API_KEY')
cass.set_default_region("EUW")        

# dates to be considered
begin_data = datetime.strptime("08/01/20 00:00", "%d/%m/%y %H:%M")
end_data= datetime.now()

players = {
           "faker": ["Hide on Bush"], 
           # short_name: exact summoner name, list for more than one
           }
for player_name in players.keys():
    matchups = {}
    if isinstance(players[player_name], str):
        player = [players[player_name]]
    else:
        player = players[player_name]
    if os.path.isfile(f'{player_name}.csv'):
            continue
    for account in player:
        summoner = cass.get_summoner(name=account, region=Region.europe_west)
        match_history = MatchHistory(summoner=summoner, begin_time=arrow.get(begin_data.timestamp()), end_time=arrow.get(end_data.timestamp()), queues={Queue.ranked_solo_fives, Queue.ranked_flex_fives})
        for match in match_history:
            participant = match.participants[account]
            if participant.champion.name in matchups.keys():
                matchups[participant.champion.name].update(participant, match.duration)
            else:
                matchups[participant.champion.name] = Matchup(participant, match.duration)
    df = pd.DataFrame([matchups[m].to_dict() for m in matchups.keys()]).sort_values('games', ascending=False)
    df.to_csv(f'{player_name}.csv', index=False)
